# ArtifactLayout: 실험 출력 폴더의 schema 관리자

작성일: 2026-04-29

관련 파일:

- `src/routix/io/artifact_layout.py` — `ArtifactLayout` base class
- `src/routix/io/_default_artifact_layout.yaml` — 기본 schema
- `src/routix/io/path.py` — `init_run_root`, `RunRoot`
- `src/routix/runner/*.py` — runner 클래스의 `layout` 파라미터
- `src/routix/subroutine_controller.py` — `set_artifact_layout`
- `src/routix/logging.py` — file handler lifecycle + prefix/level filter

## 1. 배경 / 동기

routix-기반 실험 코드는 layer별 로그(run / scenario / instance)와 다양한
artifact(manifest, solution, step log, 시각화 산출 등)를 동일한 출력 폴더에
떨군다. 이 폴더 구조를 코드 곳곳에서 ad-hoc하게 조립하면 다음 문제가 생긴다.

- 파일 경로 결정 로직이 호출 지점마다 흩어진다 (runner 내부의
  `working_dir / f"{ins_name}_..."` 같은 ad-hoc 조립, reporter 내부의 별도
  규약 등).
- 같은 좌표(run / scenario / instance)에서 여러 종류의 artifact가 산출되는데,
  좌표 자체와 파일명 규약이 코드 곳곳에 박힌다.
- POST_PROCESS_ONLY 모드의 reporter가 "이 instance의 manifest는 어디 있어?"를
  알아내려면 동일 규칙을 두 곳(runner, reporter)에서 hard-code해야 한다.
- 사용자(또는 외부 분석 스크립트)가 출력 디렉터리를 열어 무엇이 어디 있는지
  파악하려면 코드를 직접 읽어야 한다 — 디렉토리 구조의 single source of truth가
  없다.

`ArtifactLayout`은 위 문제를 풀기 위한 "출력 폴더의 schema 관리자"로 routix에
도입된다.

## 2. 디렉터리 구조 — 세 개의 zone

instance 디렉터리는 **세 개의 zone**으로 나뉜다:

| zone        | 위치                            | 의미                                                        |
| ----------- | ------------------------------- | ----------------------------------------------------------- |
| `final`     | instance 디렉터리 바로 아래     | 한 instance의 **최종 결과**. 다른 도구가 의존해도 되는 면.  |
| `progress/` | instance 디렉터리 / `progress/` | 실행 **과정 기록**. step log, 중간 phase 산출 등.           |
| `report/`   | instance 디렉터리 / `report/`   | **사후 생성** artifact. 시각화 등 reporter가 만든 것.       |

```plaintext
output/
└── <base_output_dir_name>/                  # 예: 20260427_smoke
    └── <run_id>/                            # 예: 20260429T114816_361693 (timestamp)
        ├── <run_id>_main.log                # host project main의 root logger 출력
        ├── <run_id>_MultiScenarioRunner.log
        ├── <experiment_config>.yaml         # 입력 yaml 사본
        ├── <run_id>_summary.csv             # cross-scenario 요약 (project overlay)
        └── <scenario_name>/
            ├── <run_id>_MultiInstanceRunner.log
            ├── <scenario_name>_benchmark.log
            ├── <scenario_name>_statistics.yaml
            └── <instance_name>/
                │
                │ ── final zone ──
                ├── <run_id>_SingleInstanceRunner.log
                ├── <run_id>_SubroutineController.log
                ├── <ins>_instance_result.yaml   # manifest (마지막에 atomic write)
                ├── <ins>_obj_log.yaml           # objective trajectory
                ├── <ins>_solution.json          # 유일한 solution serialization
                │
                │ ── progress zone ──
                ├── progress/
                │   └── <ins>_<step_idx>-<method>_step_log.yaml
                │
                │ ── report zone ──
                └── report/
                    └── ...   # project overlay가 추가하는 시각화 등
```

핵심 규칙:

- log 파일은 자기 layer가 "soak through"되는 가장 안쪽 디렉터리에서 생성된다
  (instance log는 instance final zone, scenario log는 scenario 디렉터리, run log는
  run 디렉터리).
- log 파일명 prefix는 `<run_id>` (run-root의 디렉터리 이름과 동일).
  scenario / instance 단위로 자기 timestamp을 만들지 않는다 — 모두 같은 run에
  속한다는 사실을 파일명만 봐도 알 수 있도록.
- 비-log artifact의 prefix는 그 artifact를 가장 잘 식별하는 좌표를 쓴다
  (instance 단위는 `<instance_name>`, scenario 단위는 `<scenario_name>`,
  run 단위는 `<run_id>`).
- **instance final zone에는 최종 결과만 둔다**. 중간 산출은 `progress/`,
  사후 시각화는 `report/`.
- **project-specific subclass / overlay의 책임 범위는 단 하나**: 각 artifact
  `kind`가 `final` / `progress` / `report` 중 어느 zone으로 가는지, 그리고
  zone 안에서의 파일명 template을 선언. 실제 path 조립은 base class가 처리.

## 3. `ArtifactLayout` 추상화

DB schema 관리자 비유:

| DB schema 관리자                     | ArtifactLayout                                |
| ------------------------------------ | --------------------------------------------- |
| 테이블 정의 (DDL)                    | 디렉터리/파일 layout 정의 (yaml)              |
| 컬럼 → 물리 위치 매핑                | (run_id, scenario, instance, kind) → Path     |
| migration tool                       | 빈 디렉터리 ensure / 기존 디렉터리 detect     |
| ORM의 query helper                   | reporter가 쓰는 `find_*` / `iter_*` API       |
| schema version                       | `_schema_version` (manifest에 박힘)           |

### 3.1 schema 데이터 (language-independent)

routix는 기본 schema yaml `src/routix/io/_default_artifact_layout.yaml`을
들고 있다. 대략의 구조는 다음과 같다.

```yaml
schema_version: 1
scopes:
  - name: run
    parent: null
    dir_template: "{base_output_dir}/{run_id}"
  - name: scenario
    parent: run
    dir_template: "{run_dir}/{scenario_name}"
  - name: instance
    parent: scenario
    dir_template: "{scenario_dir}/{instance_name}"

logs:
  - scope: run
    role: main
    file_template: "{run_id}_main.log"
  - scope: run
    role: multi_scenario_runner
    file_template: "{run_id}_MultiScenarioRunner.log"
  - scope: scenario
    role: multi_instance_runner
    file_template: "{run_id}_MultiInstanceRunner.log"
  - scope: instance
    role: single_instance_runner
    file_template: "{run_id}_SingleInstanceRunner.log"
  - scope: instance
    role: subroutine_controller
    file_template: "{run_id}_SubroutineController.log"
  - scope: instance
    role: algorithm           # 의도적으로 SubroutineController와 동일 파일
    file_template: "{run_id}_SubroutineController.log"

# zone 규칙 (validation 필수, fail-fast):
#   - scope=instance: `zone` 필드 **필수**. {final|progress|report} 중 하나.
#                     누락 → ValueError. default 없음.
#   - scope=run / scenario: `zone` 필드 **금지**. 들어오면 ValueError.
#
# Rationale: zone은 SSOT 보호 contract의 핵심 분류이므로 작성자가 매 entry마다
# 명시적으로 결정하도록 강제한다. default=final로 두면 새 kind 추가 시 zone을
# 빠뜨린 entry가 자동으로 final(가장 보호되어야 할 zone)에 들어가는 사고가
# 일어나기 쉽다.

artifacts:
  # ---- instance / final ----
  - scope: instance
    zone: final
    kind: instance_result_manifest
    file_template: "{instance_name}_instance_result.yaml"
  - scope: instance
    zone: final
    kind: solution_json
    file_template: "{instance_name}_solution.json"
  - scope: instance
    zone: final
    kind: obj_log
    file_template: "{instance_name}_obj_log.yaml"

  # ---- instance / progress ----
  - scope: instance
    zone: progress
    kind: step_log
    file_template: "{instance_name}_{step_idx}-{method}_step_log.yaml"

  # ---- scenario ----
  - scope: scenario
    kind: benchmark_log
    file_template: "{scenario_name}_benchmark.log"
  - scope: scenario
    kind: scenario_statistics
    file_template: "{scenario_name}_statistics.yaml"

  # ---- run ----
  - scope: run
    kind: summary_csv
    file_template: "{run_id}_summary.csv"
```

project별로 추가하고 싶은 artifact는 **overlay yaml**로 위에 덮어쓰거나,
`register_kind` API로 sub-class에서 등록한다.

### 3.2 interpreter (Python)

`routix.io.artifact_layout.ArtifactLayout`이 yaml을 읽어 다음을 제공한다:

```python
Zone = Literal["final", "progress", "report"]

class ArtifactLayout:
    """Base class. project별 추가 kind은 subclass에서 register."""

    def __init__(self, *, run_root: Path, run_id: str, schema_path: Path | None = None): ...

    # ---- scope path ----
    def run_dir(self) -> Path: ...
    def scenario_dir(self, scenario_name: str) -> Path: ...
    def instance_dir(self, scenario_name: str, instance_name: str) -> Path: ...

    # ---- zone path (instance scope only) ----
    def zone_dir(
        self, zone: Zone, *, scenario_name: str, instance_name: str,
    ) -> Path:
        """final → instance_dir 그대로 / progress → instance_dir/progress /
        report → instance_dir/report. 첫 호출에서 mkdir."""

    # ---- log ----
    def log_path(
        self,
        role: Literal["main", "multi_scenario_runner",
                       "multi_instance_runner",
                       "single_instance_runner",
                       "subroutine_controller",
                       "algorithm"],
        *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
    ) -> Path: ...

    # ---- artifact ----
    def artifact_path(
        self, kind: str, *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
        **placeholders: str,
    ) -> Path:
        """schema entry의 zone을 따라 자동으로 final/progress/report로 라우팅."""

    # ---- POST_PROCESS_ONLY ----
    def discover_scenarios(self) -> list[str]: ...
    def discover_instances(self, scenario_name: str) -> list[str]: ...
    def find_instance_manifests(self, scenario_name: str) -> list[Path]: ...
    def find_artifacts(
        self, kind: str, *,
        scenario_name: str | None = None,
        instance_name: str | None = None,
    ) -> list[Path]:
        """zone 안에서 glob."""

    # ---- subclass extension hook ----
    def register_kind(
        self, kind: str, *,
        scope: Literal["run", "scenario", "instance"],
        zone: Zone | None = None,             # required iff scope=="instance"
        file_template: str,
    ) -> None:
        """project subclass가 추가 kind을 등록.

        zone 규칙 (yaml schema와 동일, fail-fast):
        - scope="instance": zone 필수. None이면 ValueError.
        - scope="run"/"scenario": zone 금지. None이 아니면 ValueError.
        """

    # ---- serialize ----
    def stamp(self) -> Path: ...   # writes <run_id>_artifact_layout.yaml
```

호출 측은 절대 `working_dir / f"{ins}_..."` 같은 문자열 조립을 하지 않는다.
모든 경로는 layout에게 묻는다.

**project-specific subclass 책임**은 `register_kind` 호출만으로 끝난다. base
클래스가 zone routing(`final`/`progress/`/`report/`)과 디렉터리 생성을 처리하기
때문에, subclass는 "이 kind는 어느 scope, 어느 zone, 어떤 파일명으로" 만 선언:

```python
class MyProjectLayout(ArtifactLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.register_kind(
            "phase_diagnostic",
            scope="instance", zone="progress",
            file_template="{instance_name}_phase_diagnostic.yaml",
        )
        # ... project별 추가 kind들
```

(yaml overlay 방식과 sub-classing 방식은 둘 다 가능하게 두되, 기본 권장은
yaml overlay. subclass는 yaml로 표현하기 어려운 dynamic 분기가 필요할 때만
사용.)

### 3.3 왜 yaml + interpreter로 쪼개나

- POST_PROCESS_ONLY 모드는 **다른 시점에 다른 코드 버전**으로 만든 디렉터리를
  열어 처리해야 한다. interpreter만 진화하고 schema는 stamp된 yaml을 따라가면,
  과거 run에 대해서도 동일한 "이 파일은 무슨 kind지?" 판단이 가능하다.
- 외부 도구(분석 노트북, 시각화 스크립트, 다른 언어 도구)도 yaml만 보고
  레이아웃을 알 수 있다 — language-independent.
- routix 안에서 layout 규약을 단일 source로 갖고 있고, project는 overlay만
  올린다 → DRY.

## 4. routix 구현 요약

### 4.1 `routix.io.artifact_layout`

- `ArtifactLayout` 클래스 (위 § 3.2 시그니처).
- 기본 schema yaml `src/routix/io/_default_artifact_layout.yaml` —
  `main`/`multi_scenario_runner`/`multi_instance_runner`/`single_instance_runner`/`subroutine_controller`/`algorithm`
  6개 logger role 정의 + manifest, benchmark_log, scenario_statistics 등 routix
  일반 artifact 정의 포함 (project 특화 kind는 overlay).
- placeholder 치환은 `str.format`으로 충분 (sandbox 필요 없음).

### 4.2 `init_run_root`

`src/routix/io/path.py`:

- `init_run_root(...)` 함수가 `RunRoot` (`run_root: Path`, `run_id: str`,
  `e_timer: ElapsedTimer`)를 리턴.
- 기존 `init_timestamped_working_dir`는 backwards-compatible 유지 (legacy 호출
  지점용).

### 4.3 Runner 확장

`MultiScenarioRunner`, `MultiInstanceRunner`, `MultiInstanceConcurrentRunner`,
`SingleInstanceRunner`:

- 생성자에 `layout: ArtifactLayout | None = None` 추가.
- `layout`이 주어지면 scenario / instance 디렉터리 결정을 layout에 위임.
- `layout`이 None이면 현재 동작 유지 (backwards-compatible).
- `MultiScenarioRunner`는 layout이 주어지면
  `layout.log_path("multi_scenario_runner")`,
  `layout.log_path("multi_instance_runner", scenario_name=...)` 등으로 자기
  layer의 log path를 layout에 묻는다.

### 4.4 `SubroutineController` — level-filtered propagation + `set_artifact_layout`

#### 4.4.1 SC log 처리의 rationale

상위 layer(main / MultiScenarioRunner / MultiInstanceRunner /
SingleInstanceRunner)는 **swap-on-root 방식의 현재 동작을 그대로 유지**한다
(Python 기본 동작에 맡김). SubroutineController + algorithm 사이는 **격벽이
아니라 level-filtered propagation**으로 처리한다. 이유:

- SC와 algorithm은 step / batch / dispatcher 단위로 record를 쏟아낸다. 하나의
  instance solve 동안 수천~수만 줄이 자연스럽게 발생, 절대 다수가 DEBUG/INFO.
- 이 noise가 SIR.log로 그대로 propagate되면 SIR.log를 사람이 읽을 수 없게 된다
  (SIR 자신의 record는 instance 시작/종료/post-process 정도라 SC noise에 묻힌다).
- 그렇다고 완전 격벽(`propagate=False`)으로 끊으면 **SC ERROR가 SIR.log에
  surface되지 않아** instance failure 진단 시 SC.log를 따로 열어야 한다. SIR가
  자기 layer에서 "이 instance가 왜 죽었는지"를 보지 못한다는 뜻.
- 절충: SC namespace 기원 record 중 **WARNING/ERROR/CRITICAL은 그대로
  propagate, INFO/DEBUG는 drop**. SIR.log는 SC noise에서 자유롭되 instance
  failure signal은 즉시 보임.

#### 4.4.2 구현

`record.name` 기반의 표준 `logging.Filter`로 noise namespace만 상위에서 차단:

```python
# routix/src/routix/logging.py
class PrefixLevelFilter(logging.Filter):
    """주어진 prefix로 시작하는 record는 WARNING 이상만 통과시킨다.

    record는 변형하지 않으며 (level/lineno 보존), 다른 logger 기원 record는
    그대로 통과. 부모 file handler에 부착해 SIR.log를 SC noise에서 보호.
    console handler에는 부착하지 않아 사용자가 console로 SC 진행을 볼 수 있게
    한다.
    """

    def __init__(self, prefix: str):
        super().__init__()
        self._prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith(self._prefix):
            return record.levelno >= logging.WARNING
        return True
```

caller 흐름 (host project 측):

```python
from routix.logging import PrefixLevelFilter, attach_fh_to_logger, detach_fh_from_logger

# SIR file handler 셋업 자리에서 (process 수명 동안 한 번)
sir_file_handler.addFilter(PrefixLevelFilter(sc_logger_prefix))
# console handler에는 부착 안 함 → SC 진행이 console에는 그대로 보임

# SingleInstanceRunner가 controller 진입 직전에
sc_logger_name = f"{sc_logger_prefix}.{instance_name}"
attach_fh_to_logger(
    sc_logger_name,
    layout.log_path("subroutine_controller",
                    scenario_name=..., instance_name=...),
)
# helper가 logger.setLevel(DEBUG), DEBUG-level FileHandler 부착, defensive sweep을 처리.
# propagate는 건드리지 않음 (Python 기본 True 그대로) — 위로 흐르되 filter가 INFO/DEBUG만 drop.
```

- SC.log: SC logger 자체 file handler가 받으므로 full fidelity (DEBUG~ERROR).
- SIR.log: 상위 file handler에 attach된 filter가 SC namespace의 INFO/DEBUG만
  drop. SIR own records, MIR/MSR/main records는 영향 없음. SC의 WARNING/ERROR는
  통과 → instance failure가 SIR.log에 surface.
- console: filter 없는 stream handler가 모든 record를 사용자 -q/-v level에
  맞춰 출력 (SC INFO도 console에선 보임).
- algorithm은 `__init__(..., logger: Logger | None = None)`으로 logger를 받고,
  controller가 호출할 때 `logger=self.logger`를 명시 전달. None이면 module-level
  fallback. algorithm은 SC logger 인스턴스를 그대로 들고 쓰므로 record.name이
  SC namespace로 시작 → filter 적용 대상.

#### 4.4.3 layout 통합

- `set_working_dir` 호출자를 그대로 두되, `set_artifact_layout(layout,
  scenario_name=..., instance_name=...)`을 추가해 controller / algorithm이
  instance scope의 log/artifact 경로를 layout에 물어볼 수 있게 한다.
- `try_get_file_path_for_subroutine`은 layout 기반으로 동작 (progress zone에
  step_log 떨어뜨리도록).

#### 4.4.4 각 log 파일에 들어가는 record (요약)

| log file | 내용 | 메커니즘 |
| --- | --- | --- |
| `<run_id>_main.log` | host project main이 active 동안 emit한 propagating record | host project가 셋업 |
| `<run_id>_MultiScenarioRunner.log` | MSR active 동안의 propagating record | swap-on-root |
| `<run_id>_MultiInstanceRunner.log` | MIR active 동안의 propagating record | swap-on-root |
| `<run_id>_SingleInstanceRunner.log` | SIR own record + **SC/algorithm WARNING/ERROR/CRITICAL** (instance failure가 SIR.log에 surface) | swap-on-root + `PrefixLevelFilter` |
| `<run_id>_SubroutineController.log` | SC + algorithm record (DEBUG~ERROR full fidelity) | SC logger 직접 file handler attach + `propagate=True` + 같은 logger 객체 공유 |

console에는 SC 진행 record까지 모두 통합으로 보임 (root stream handler가
propagation으로 자동 수신, filter는 file handler에만 부착).

### 4.5 `routix.logging` 모듈

- `attach_fh_to_logger(logger_name, file_path)` /
  `detach_fh_from_logger(logger_name)` — 임의 logger에 DEBUG-level
  `FileHandler`를 부착/해제. `_MANAGED_TAG`로 자기가 부착한 handler만 추적하며
  attach/detach 진입에서 defensive sweep. `propagate`는 건드리지 않음 (Python
  기본 True 유지).
- `PrefixLevelFilter(prefix)` — `record.name`이 `prefix`로 시작하는 record 중
  INFO/DEBUG를 drop하는 표준 `logging.Filter`. 상위 file handler에 한 번
  부착하면 process 수명 동안 작동 (stateless).
- 후속 후보(미도입): `LogScope` (swap-on-root용 컨텍스트 매니저) — 일반화된
  push/replace 패턴. 실수요가 안정된 다음 promotion.

## 5. 위험 / 미해결 질문

### 5.1 SC handler 누적 문제 — 안전한 attach/detach 패턴

**문제**: instance A 실행 중 예외 발생 → logger 정리 누락 → 이후 instance
B/C/... 의 record가 A의 log 파일에 계속 누적되거나, 중복 record가 발생.

logger 이름이 instance마다 다르면(`controller.<instance_name>`) record
cross-contamination 자체는 자동 방지되지만, 같은 process가 instance를 순차
처리하는 (single-worker / fail-then-retry) 시나리오에서는 stale handler가 fd로
남아 누적될 수 있음. 이를 막기 위해 다음 4-단 방어:

1. **defensive sweep on attach** — attach 함수 진입 시 그 logger에 이미 붙어
   있는 `_MANAGED_TAG` handler를 모두 close + remove한 다음 새로 부착.
   이전 run이 detach를 못 했어도 이번 run 시작에서 청소됨.
2. **try/finally on caller** — `SingleInstanceRunner.run`의 try/finally 블록
   안에서 attach → controller.run → detach. 예외 경로도 detach가 무조건 실행됨.
3. **idempotent detach** — detach가 호출되지 않았거나 두 번 호출돼도 안전.
   handler가 없으면 no-op.
4. **logger 이름 per-instance** — `controller.<instance_name>` 으로 이미
   분리되어 있어, 1·2·3이 모두 실패하더라도 다른 instance의 record가 잘못된
   파일로 가는 사고는 발생하지 않음 (최악의 경우는 fd 누수만).

helper 시그니처 (`routix.logging` 실제 구현):

```python
# routix/src/routix/logging.py

_MANAGED_TAG = "_routix_managed"

_DEFAULT_FILE_FMT = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


class PrefixLevelFilter(logging.Filter):
    """주어진 prefix로 시작하는 record는 WARNING 이상만 통과; INFO/DEBUG는 drop."""

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self._prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith(self._prefix):
            return record.levelno >= logging.WARNING
        return True


def attach_fh_to_logger(logger_name: str, file_path: Path) -> logging.Logger:
    """logger에 DEBUG-level file handler 부착. propagate는 그대로 (Python 기본 True)."""
    log = logging.getLogger(logger_name)
    _sweep(log)                                     # (1) defensive sweep
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(file_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_DEFAULT_FILE_FMT)
    setattr(fh, _MANAGED_TAG, True)
    log.addHandler(fh)
    return log


def detach_fh_from_logger(logger_name: str) -> None:
    """attach_fh_to_logger가 부착한 handler들을 close+remove. idempotent."""
    _sweep(logging.getLogger(logger_name))           # (3) idempotent


def _sweep(log: logging.Logger) -> None:
    for h in list(log.handlers):
        if getattr(h, _MANAGED_TAG, False):
            try:
                h.close()
            finally:
                log.removeHandler(h)
```

caller pattern:

```python
from routix.logging import attach_fh_to_logger, detach_fh_from_logger

sc_logger_name = f"{sc_logger_prefix}.{instance_name}"
try:
    attach_fh_to_logger(
        sc_logger_name,
        layout.log_path("subroutine_controller",
                        scenario_name=..., instance_name=...),
    )
    self.ctrlr = self.get_controller()
    self.ctrlr.run()
finally:
    detach_fh_from_logger(sc_logger_name)
```

`PrefixLevelFilter`는 SIR file handler에 한 번만 부착하면 되며 (process 수명
동안 stateless), instance 단위로 attach/detach할 필요 없음. console stream
handler에는 부착하지 않으므로 SC INFO/DEBUG도 console에는 -q/-v level에 따라
보임.

**테스트로 검증할 시나리오** (`tests/test_logging.py` 에 구현됨):

- `controller.run`이 정상 종료 → attached file handler가 detach로 사라지는가.
- `controller.run`이 예외로 종료 → finally의 detach가 실행되는가, fd가 닫히는가.
- 같은 process에서 instance A → 예외 → instance B를 새 attach 호출 → A의 handler
  잔재가 남지 않는가 (defensive sweep 작동 확인).
- 같은 process에서 instance A → 정상 → instance B → A의 SC.log에 B의 record가
  들어가지 않는가 (logger 이름 분리 작동 확인).
- SC logger에서 INFO 발행 → SC.log에 기록, SIR.log에 미기록.
- SC logger에서 ERROR 발행 → SC.log + SIR.log 모두 기록 (instance failure
  surface).
- `PrefixLevelFilter` prefix 안 맞는 다른 logger의 INFO → SIR.log에 기록
  (filter는 매칭 prefix에만 적용).

**Coupling 주의**: `PrefixLevelFilter`의 prefix는 SC logger 이름 컨벤션과
묶여 있다. routix는 특정 namespace를 hardcode하지 않고 `prefix: str` 파라미터로
caller가 주입하도록 둠. host project는 자기 SC logger 이름의 namespace를
파일 handler 셋업 자리에서 받아 `PrefixLevelFilter(prefix=...)`로 SIR file
handler에 부착.

### 5.2 scenario 이름 / 디렉터리 중복 (실험 overwrite 방지)

**문제**: scenario name이 중복된 채로 들어와 두 scenario가 같은 디렉터리를
공유하면 두 번째 scenario가 첫 번째 결과를 silently overwrite. 디스크에는 늦게
끝난 scenario만 남고 사용자는 한참 뒤에야 발견.

**대책**: `ArtifactLayout.scenario_dir(name)` 첫 호출 시 register된 이름 set을
들고 있다가 같은 이름이 다시 들어오면 `ValueError`로 fail-fast. host project
측에서는 layout 생성 직전(예: config 로딩 직후)에 동일 검증을 한 번 더 거치는
것이 권장 — 두 군데에서 검증하면 한쪽이 무너져도 다른 쪽이 잡는다.

### 5.3 그 외 위험

- **Backwards compatibility**: pre-zone, pre-layout 디렉터리는 본 layout으로
  해석하지 않음. POST_PROCESS_ONLY는 신규 run에 대해서만 보장. 기존 디렉터리는
  별도 일회성 분석 스크립트로 처리.
- **multiprocessing (layout)**: ProcessPoolExecutor worker는 layout 객체를
  pickle해 받게 된다. layout이 yaml 경로 + dict만 들고 있으면 picklable.
  logger handler attach는 worker init에서 layout으로부터 path를 다시 도출하는
  식으로 처리.
- **layout vs subroutine context name**:
  `SubroutineController.get_file_path_for_subroutine`은 method context stack
  (`reps.0.run_xxx` 같은 prefix)을 파일명에 박는다. 이건 instance scope
  artifact 안에서의 sub-naming이라 layout과 직교. layout은 디렉터리만 결정하고
  이 helper는 파일명만 결정하도록 분리 유지.
- **scope 간 경계 지점**: scenario log와 instance log를 동시에 쓰고 싶을 때
  root logger의 핸들러 chain이 문제 없는지 확인 필요. 현재 `_MANAGED_TAG`로
  자기 관리 핸들러만 교체하므로 multi-handler attach 자체는 가능.
- **kind 추가의 거버넌스**: 동일 kind을 여러 곳에서 정의하면 충돌. routix base가
  `routix.*` 네임스페이스를, project overlay가 자기 네임스페이스를 쓰는
  컨벤션 검토.

## 6. 작업 단위 요약 (routix)

- [x] `src/routix/io/_default_artifact_layout.yaml` 신설
      (final/progress/report zone 정의 포함)
- [x] `src/routix/io/artifact_layout.py` 신설 (`ArtifactLayout` base
      class + `zone_dir`, `register_kind` API)
- [x] `src/routix/io/path.py`에 `init_run_root` 추가
- [x] `MultiScenarioRunner`, `MultiInstanceRunner`, `MultiInstanceConcurrentRunner`,
      `SingleInstanceRunner`에 `layout` 파라미터 추가 (default None)
- [x] `SubroutineController.set_artifact_layout` 추가
- [x] `routix.logging` 모듈 추가
      - `attach_fh_to_logger(logger_name, file_path)` /
        `detach_fh_from_logger(logger_name)` (file handler attach/detach +
        `_MANAGED_TAG` defensive sweep, propagate는 건드리지 않음)
      - `PrefixLevelFilter(prefix)` — `record.name`이 prefix로 시작하는
        record 중 INFO/DEBUG는 drop, WARNING+는 통과시키는 `logging.Filter`
      - `tests/test_logging.py` — § 5.1 시나리오 7개 + 단위 5개 = 12 테스트
- [x] `tests/io/test_artifact_layout.py` — zone routing, subclass register,
      stamp/restore round-trip, **zone validation** (scope=instance에 zone 누락
      → ValueError / scope=run·scenario에 zone 지정 → ValueError / scenario_dir
      중복 등록 → ValueError)
- [x] `subroutine_flow_data.md`, `runner/README.md`에 layout 언급
