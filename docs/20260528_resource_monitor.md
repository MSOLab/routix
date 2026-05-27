# ResourceMonitor: 실행 중 system resource 관측 + time limit overrun 진단

작성일: 2026-05-28

관련 파일 (예상):

- `src/routix/resource_monitor.py` — `ResourceMonitor` 본체 (신설 예정)
- `src/routix/subroutine_controller.py` — controller 진입/종료 hook에서 monitor 시작/정지
- `src/routix/metric_time_series/` — RSS / swap / CPU 시계열 저장 (기존 인프라 재사용)
- `src/routix/report/` — peak RSS / swap_in event를 statistics에 surface
- `src/routix/elapsed_timer.py` — 본 doc에서 다루는 "wall-clock의 신뢰성" 문제와 직결

## 1. 배경 — wall-clock time limit이 깨지는 case

routix-기반 host project(flowshop-tardiness 등)는 instance 단위로 wall-clock
time limit을 정한 뒤 algorithm 내부 solver(예: OR-Tools CP-SAT)에 그대로 넘긴다.
solver는 보통 자기 wall-clock으로 limit을 본다는 가정 아래 동작한다.

이 가정이 **system이 swap을 사용하기 시작하면 깨진다**는 사실을 한 batch에서
명확하게 관측했다.

### 1.1 관측 조건

- host project: flowshop-tardiness, branch `20260527_results_for_defence`
- batch: `Outputs_scenarios/20260528T002147_783988/20260527_ablation_c1/`
- 입력: VRM benchmark instances `537`, `538`, `539`, `540`
  (각 350 jobs × 50 machines, `resources/vrm/{537,538,539,540}.txt`)
- runner: `MultiInstanceConcurrentRunner`, 12 worker
- subroutine flow: `set_random_seed → initialize_by_nehms →
  compute_preemptive_last_stage_lb → set_cp_model_as_base_cp_model →
  solve_base_cp_model`
- stopping criterion: `timelimit_n_by_m_multiplier: 0.045`
  → `350 × 50 × 0.045 = 787.5 sec` per instance
- 4개 instance가 동일 process pool 안에서 거의 동시에 시작 (`00:21:47`)
- 실행 중 시스템이 swap을 일부 사용

### 1.2 관측 결과

instance 별 `solve_base_cp_model` log entry 기준:

| ins  | solver start (s) | solver elapsed (s) | total (s) | 초과 (s)        |
| ---- | ---------------: | -----------------: | --------: | --------------: |
| 538  |            80.23 |             719.30 |    799.53 |       **+12**   |
| 539  |            80.69 |             922.28 |   1002.97 |      **+215**   |
| 540  |            78.00 |            1182.17 |   1260.17 |      **+473**   |
| 537  |          (32.52) | (solver 미완료)    |    >1200s | 미완료 (응답無) |

(전부 동일 timelimit 787.5 sec)

raw evidence:

```text
# 538/subroutine_controller.log (line 15)
2026-05-28 00:35:07,355 - INFO - {'method': 'solve_base_cp_model', ...,
                                  'start_sec': 80.23, 'elapsed_sec': 719.30}

# 539/subroutine_controller.log (line 15)
2026-05-28 00:38:30,798 - INFO - {'method': 'solve_base_cp_model', ...,
                                  'start_sec': 80.69, 'elapsed_sec': 922.28}

# 540/subroutine_controller.log (line 15)
2026-05-28 00:42:48,002 - INFO - {'method': 'solve_base_cp_model', ...,
                                  'start_sec': 78.00, 'elapsed_sec': 1182.17}

# 537/subroutine_controller.log (line 12, 마지막 활동)
2026-05-28 00:25:06,668 - INFO - Elapsed: 198.84 sec, ObjValue: 1686658.0, ...
# 이후 응답 없음
```

핵심 패턴:

- 모두 같은 batch / 같은 stopping criterion / 같은 algorithm.
- 538은 거의 정확히 제 시간에 종료 — solver가 wall-clock을 honor.
- 539 / 540 / 537은 같은 환경인데도 각각 +215s / +473s / 미완료로 점점 더
  심하게 미끄러짐.
- 미끄러진 정도가 system이 swap에 점점 의존하는 양과 단조 관계로 보임 (정량
  자료는 본 batch엔 없음 — 그래서 ResourceMonitor가 필요).

### 1.3 가설

OR-Tools CP-SAT(혹은 일반적인 wall-clock 기반 solver)는 자체 worker thread에서
주기적으로 deadline을 본다. system이 swap-thrash 상태에 들어가면:

1. 해당 process 전체가 OS에 의해 길게 descheduled 된다 (수십~수백 ms 단위로).
2. solver의 deadline check 루프가 같이 멈춘다 — wall-clock으로는 시간이
   흐르지만, 측정 자체가 안 됨.
3. resume 직후 deadline check가 fire되어 solver는 "끝난다"고 결정하지만, 이미
   wall-clock 기준으로는 한참 지난 상태.
4. 종료 처리(callback, post-solve, hint 회수 등)에도 swap이 끼면 다시 길게
   걸려 추가 overrun을 만든다.

또 다른 가능성: solver가 CPU-time 기준으로 limit을 보면 swap I/O wait 동안
CPU-time이 거의 안 늘어나서 wall-clock 한참 뒤에 deadline에 도달.

본 doc은 어느 가설이 맞는지 확정하지 않는다 — 어느 쪽이든 routix 입장에서는
**관측 데이터 없이는 사후 진단 불가능하다**는 사실이 중요하다.

## 2. routix가 해야 할 일

routix는 host project가 "왜 time limit이 안 지켜졌나"를 사후에 답할 수 있도록
다음 두 가지를 제공해야 한다.

1. **실행 중 system resource 시계열을 수동(passive)으로 수집** — 이것이 본
   doc의 핵심 제안 `ResourceMonitor`.
2. (장기) **wall-clock의 비신뢰성을 노출하는 helper** — 본 doc은 §5에서
   질문으로만 남김. routix가 자체적으로 limit을 enforce하는 것이 옳은지,
   solver에 위임할지의 정책 결정이 따로 필요.

§2의 (1)은 (2)와 독립적으로 가치가 있다 — limit이 깨지지 않는 run에서도
performance regression 분석 / OOM 진단 / cgroup 튜닝에 쓰임.

## 3. `ResourceMonitor` 설계 스케치

### 3.1 책임

- 자기 process(+선택적으로 자식들)의 다음 값들을 주기적으로 sampling:
  - RSS (Resident Set Size)
  - VMS (Virtual Memory Size)
  - swap usage (per-process, `/proc/<pid>/status: VmSwap`)
  - system-wide swap in/out rate (`/proc/vmstat: pswpin/pswpout`)
  - CPU% (process 기준, optional)
  - load average (system 기준, optional)
- 값을 `MetricTimeSeries`에 적재 (timestamp은 `ElapsedTimer` 기준 elapsed_sec).
- threshold 초과 event를 `WARNING`으로 자기 logger에 emit
  (예: `swap_in_rate > 0`이 처음 발생한 시점, `RSS > 0.9 * cgroup_memory_max`).
- `SubroutineReport`에 peak/aggregate 통계를 push (peak RSS, peak swap, swap이
  처음 발동된 시각 등).

### 3.2 인터페이스 스케치

```python
# routix/src/routix/resource_monitor.py

from dataclasses import dataclass
from pathlib import Path

from .elapsed_timer import ElapsedTimer
from .metric_time_series import MetricTimeSeries


@dataclass(frozen=True)
class ResourceSample:
    elapsed_sec: float
    rss_bytes: int
    vms_bytes: int
    swap_bytes: int           # per-process VmSwap
    sys_swap_in_pages: int    # cumulative since boot
    sys_swap_out_pages: int   # cumulative since boot
    cpu_percent: float | None


class ResourceMonitor:
    """배경 thread에서 일정 주기로 system resource를 sampling.

    threading 기반(GIL 영향 최소화 위해 sleep 사이에만 측정). multiprocessing
    worker 안에서 쓰일 수 있도록 picklable한 config + 시작은 worker init에서.
    """

    def __init__(
        self,
        *,
        e_timer: ElapsedTimer,
        sample_interval_sec: float = 1.0,
        swap_warn_threshold_bytes: int = 0,   # 0 = "swap 처음 쓰는 순간 경고"
        rss_warn_threshold_bytes: int | None = None,
        pid: int | None = None,               # None = 현재 process
    ) -> None: ...

    def start(self) -> None: ...
    def stop(self) -> None: ...

    # ---- time series 접근 ----
    @property
    def rss_series(self) -> MetricTimeSeries[int]: ...
    @property
    def swap_series(self) -> MetricTimeSeries[int]: ...
    @property
    def sys_swap_in_rate_series(self) -> MetricTimeSeries[float]: ...
    # ...

    # ---- 사후 통계 ----
    def peak_rss_bytes(self) -> int: ...
    def first_swap_in_elapsed_sec(self) -> float | None:
        """system swap_in이 0에서 양수로 처음 바뀐 시각. 없으면 None."""

    def dump_yaml(self, path: Path) -> None: ...
```

### 3.3 `SubroutineController` 통합

`SubroutineController.run` 진입에서 monitor를 attach, 종료(or 예외)에서 detach.
`ArtifactLayout`이 결정한 instance progress zone에 `_resource_monitor.yaml` 같은
이름으로 시계열을 dump (zone 이름은 별도 합의 필요 — [[20260429_artifact_manager]]
참조).

```python
# pseudo, controller.run() 내부
mon = ResourceMonitor(e_timer=self.e_timer, sample_interval_sec=1.0)
try:
    mon.start()
    self._run_steps(...)
finally:
    mon.stop()
    self.report.attach_resource_monitor(mon)   # report에 peak/event 노출
    if self._artifact_layout is not None:
        mon.dump_yaml(self._artifact_layout.artifact_path(
            "resource_monitor_timeseries",
            scenario_name=..., instance_name=...,
        ))
```

### 3.4 `SubroutineReportStatistics`에 surface할 항목

- `peak_rss_mib`
- `peak_swap_mib`
- `first_swap_in_elapsed_sec` (`null`이면 swap 없이 끝남)
- `swap_active_duration_sec` (cumulative)
- `wall_clock_vs_solver_drift_sec` (선택 — host project가 측정해서 attach.
  본 batch에서는 538은 +12s, 540은 +473s. routix가 자동 계산하기는 어렵고
  host project가 `solver-reported elapsed` vs `wall-clock elapsed`를 비교해
  넣는 형태가 자연스러움.)

## 4. routix에서의 위치

- `routix.resource_monitor` 신설 (top-level module, package화는 불필요).
- `routix.__init__`에서 export.
- `metric_time_series`는 그대로 dependency로 사용.
- 의존성: 표준 library만으로 `/proc/<pid>/status`, `/proc/vmstat`을 읽어
  Linux는 무의존성 처리 가능. macOS/Windows는 차후. `psutil`은 optional dep로
  두고, 없으면 `/proc` fallback이라는 두-단 구조가 routix 철학에 맞음.
- `pyproject.toml`에 `psutil`은 `[project.optional-dependencies] monitor = ["psutil"]`.

## 5. 미해결 질문

### 5.1 routix가 wall-clock limit을 enforce해야 하나

본 doc은 "관측"까지만 다룬다. solver가 limit을 못 지킬 때 routix가 강제로
중단시키는 것이 옳은지는 별도 문제:

- 강제 중단: `multiprocessing` 자식 process에 `SIGALRM` / `terminate()`. 그러나
  partial result를 잃을 위험.
- soft hint: solver에 더 짧은 limit을 넘기는 식의 host project 책임으로 남김.
- routix는 `ResourceMonitor`로 "솔버가 제 시간에 못 끝낼 신호"를 미리 surface
  하는 정도가 minimal.

본 batch의 538(거의 on-time)과 540(+473s) 사이 차이는 정확히 swap 강도였을
가능성이 높다 — 강제 중단보다는 swap을 피하도록 host에 신호를 일찍 주는
방향이 우선이라고 본다.

### 5.2 multiprocessing worker에서의 sampling

`MultiInstanceConcurrentRunner`의 child process 각각이 자기 monitor를 띄울
경우, parent가 종합 view를 갖기 어렵다. 옵션:

- 각 worker가 자기 monitor를 띄우고 결과를 instance 디렉터리에 dump → 사후
  취합. (현재 안)
- parent에 통합 monitor를 두고 worker pid를 등록. simpler but cross-worker
  attribution이 모호.

기본은 (1). parent monitor는 후속 작업.

### 5.3 측정 자체의 overhead

`sample_interval_sec=1.0`이면 무시 가능한 수준 (한 sample 당 `/proc` read 몇 번).
0.1초 이하로 내리면 thrashing 분석은 가능해지나, 정작 swap이 활성화된 순간엔
monitor thread도 같이 미끄러져서 sampling이 늦게 일어날 수 있다. 측정 자체가
관측 대상에 흔들리는 문제 — 사후 보정은 timestamp을 sample 시점이 아니라
`time.monotonic()`으로 stamp해서 monitor 자신의 stall을 후처리에서 인식하게
한다.

### 5.4 다른 system metric

NUMA balancing, page fault rate, CPU governor 등도 overrun과 상관 있을 수
있으나 본 doc 범위에서는 RSS + swap에 집중. 추가는 metric을 enum으로 두고
plug-in 형태로 확장.

## 6. 작업 단위 (예정)

- [ ] `src/routix/resource_monitor.py` 신설 — `ResourceMonitor` + Linux
      `/proc` reader.
- [ ] `tests/test_resource_monitor.py` — 백그라운드 thread 시작/정지,
      sample interval 정확도, swap event detection (모킹).
- [ ] `SubroutineController`에 lifecycle hook 통합 (default ON / off-switch).
- [ ] `SubroutineReportStatistics`에 peak RSS / first_swap_in_elapsed_sec 추가.
- [ ] `ArtifactLayout`에 `resource_monitor_timeseries` kind 등록
      (zone=progress).
- [ ] host project (flowshop-tardiness) 측에서 본 batch를 monitor를 단 채로
      재실행해 가설(§1.3)을 검증 — routix 변경의 acceptance test 역할도 겸함.
