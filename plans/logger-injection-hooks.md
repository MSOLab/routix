# routix — `self.logger` injection hooks

## Context

하위 프로젝트 `ffc_ddw_sum_et` 가 scope별(run → scenario → instance) log 파일을 분리 저장하려 한다. 현재 routix 의 base 클래스들은 module-level `logging.info/error/exception` 을 직접 호출하기 때문에, 하위에서 scope 별 FileHandler 를 부착해도 routix 내부 로그는 root logger 로 흘러 섞인다.

본 변경의 목적은 routix 의 각 base 클래스가 **`self.logger` 인스턴스를 보유** 하고, 하위 프로젝트에서 해당 logger 를 교체/override 할 수 있게 하여 scope별 파일 분리를 가능하게 하는 것. 기본 동작(별도 주입 없을 때)은 기존과 실질적으로 동일하게 유지한다.

## Design

### Logger 기본값: hierarchical name

각 클래스 `__init__` 에서 다음을 기본값으로 할당.

```python
self.logger = logger if logger is not None else logging.getLogger(
    f"routix.{self.__class__.__name__}"
)
```

Hierarchical name (`routix.*`) 을 쓰는 이유:
- 사용자가 `logging.getLogger("routix").setLevel(...)` / `.addHandler(...)` 로 routix 전체 로그를 일괄 제어 가능
- 서브클래스가 default 를 그대로 써도 `routix.FFcSubroutineController` 등으로 routix 네임스페이스에 붙어 그룹 제어가 유지됨
- 클래스 이름 네임스페이스 (`"SubroutineController"` 등) 를 점유하지 않아 하위 프로젝트의 동명 클래스와 충돌 위험 없음

### Logger 주입 범위: 모든 base 클래스

하위 프로젝트가 scope별 logger 를 주입할 수 있도록 **다음 7개 클래스의 `__init__` 에 `logger: logging.Logger | None = None` 파라미터 추가**:

- `SubroutineController`
- `SolutionManager`
- `SubroutineFlowValidator`
- `SingleInstanceRunner`
- `MultiInstanceRunner`
- `MultiInstanceConcurrentRunner`
- `MultiScenarioRunner`

생성자 파라미터로 받는 이유 (서브클래스 override 만으로 부족한 케이스):

- `MultiInstanceRunner.__init__` 내부에서 RESUME 모드 시 `_load_resume_data()` 실패하면 L67 에서 로그가 찍힘
- `MultiScenarioRunner.__init__` → `_init_multi_instance_runners` 안에서 scenario config 누락 시 L83 에서 warning 찍힘
- 서브클래스가 `super().__init__()` *이후* 에 `self.logger` 를 재할당하는 구조라면, super init 중 발생한 이 로그들은 default logger 로 샘 → scope 파일에 안 들어감
- 따라서 생성자 파라미터로 받아 base init 진입 직전에 꽂는 경로가 필요

### Scope 전파 정책 (routix 쪽 책임 경계)

- routix 는 **생성자 훅만 제공**. 각 레벨의 logger 가 자식에게 어떻게 파생/전파되는지는 하위 프로젝트의 override 책임.
- 기본 동작 (logger 미주입) 에서는 각 자식 클래스가 자신의 hierarchical default (`routix.<ChildClassName>`) 를 씀.
- SubroutineController 생성 책임은 `SingleInstanceRunner.get_controller()` 에 있음 (추상 메서드). 하위 프로젝트가 override 에서 `SubroutineController(..., logger=self.logger)` 로 instance-scope logger 를 controller 에 전달.
- Runner 체인에서는 하위 프로젝트가 `_init_multi_instance_runners` / `_init_single_instance_runners` 를 override 해서 scope 별 logger 를 하위 runner 에 주입.

## Changes

### 1. `src/routix/subroutine_controller.py`

```python
def __init__(
    self,
    name: str,
    subroutine_flow: Sequence[DynamicDataObject] | DynamicDataObject,
    stopping_criteria: StoppingCriteriaT,
    start_dt: datetime | None = None,
    logger: logging.Logger | None = None,   # NEW
):
    ...
    self.logger = logger if logger is not None else logging.getLogger(
        f"routix.{self.__class__.__name__}"
    )
```

치환:
- L183: `logging.error(str(log_entry))` → `self.logger.error(str(log_entry))`
- L189: `logging.info(str(log_entry))` → `self.logger.info(str(log_entry))`
- L259: `logging.info(f"[Repeat] Stopping condition met at iteration {i + 1}/{n_repeats}.")` → `self.logger.info(...)`
- L263: `logging.info(f"[Repeat] Starting repeat {i + 1}/{n_repeats}")` → `self.logger.info(...)`

### 2. `src/routix/solution_manager.py`

`SolutionManager.__init__` 에 `logger` 파라미터 추가:

```python
def __init__(self, logger: logging.Logger | None = None) -> None:
    self.history: list[SolutionRecord[...]] = []
    self.incumbent_solution: SolutionT | None = None
    self.best_obj_value: float | None = None
    self.best_obj_bound: float | None = None
    self.logger = logger if logger is not None else logging.getLogger(
        f"routix.{self.__class__.__name__}"
    )
```

치환:
- L124: `logging.info(f"Incumbent solution updated with objective: {self.best_obj_value}")` → `self.logger.info(...)`
- L130: `logging.info(f"Incumbent solution updated (equal objective): {self.best_obj_value}")` → `self.logger.info(...)`

Note: L109 의 주석 처리된 `# logging.info(...)` 는 그대로 둠 (dead code, 본 작업 범위 밖).

### 3. `src/routix/subroutine_flow_validator.py`

현재 `normalize()` 내부에서 `logger = logging.getLogger(__name__)` 을 매 호출마다 재생성하는 패턴인데, 일관성 위해 `__init__` 에서 `self.logger` 로 통일:

```python
def __init__(
    self,
    controller_class: type,
    logger: logging.Logger | None = None,   # NEW
):
    self.controller_class = controller_class
    self.logger = logger if logger is not None else logging.getLogger(
        f"routix.{self.__class__.__name__}"
    )
```

치환:
- L169: `logger = logging.getLogger(__name__)` 제거
- L181: `logger.exception("DynamicDataObject.to_obj() failed for %r", x)` → `self.logger.exception(...)`
- `normalize()` 내부 중첩 함수 `recursively_normalize` 도 closure 로 `self.logger` 참조 (별도 변수 전달 불필요)

### 4. `src/routix/runner/single_instance_runner.py`

```python
def __init__(
    self,
    instance: ParametersT,
    shared_param_dict: dict,
    subroutine_flow: Any,
    stopping_criteria: Any,
    output_dir: Path,
    output_metadata: dict[str, Any],
    mode: RunMode = RunMode.FULL_RUN,
    logger: logging.Logger | None = None,   # NEW
):
    self.logger = logger if logger is not None else logging.getLogger(
        f"routix.{self.__class__.__name__}"
    )
    self.e_timer = ElapsedTimer()
    ...
```

현재 이 파일에는 `logging.*` 호출이 없지만, 하위 프로젝트가 `get_controller()` override 에서 `SubroutineController(..., logger=self.logger)` 로 controller 에 instance-scope logger 를 넘길 수 있도록 하는 훅.

### 5. `src/routix/runner/multi_instance_runner.py`

```python
def __init__(
    self,
    s_i_runner_class: type[SingleInstanceRunnerT],
    instances: Sequence[ParametersT],
    shared_param_dict: dict,
    subroutine_flow: Any,
    stopping_criteria: Any,
    output_dir: Path,
    output_metadata: dict[str, Any],
    mode: RunMode = RunMode.FULL_RUN,
    logger: logging.Logger | None = None,   # NEW
    **kwargs: Any,
) -> None:
    self.logger = logger if logger is not None else logging.getLogger(
        f"routix.{self.__class__.__name__}"
    )
    self.e_timer = ElapsedTimer()
    ...
```

`self.logger` 할당은 **첫 줄에** 배치 (L62-67 RESUME 실패 시 `self.logger.exception` 호출이 base init 안에서 발생하므로, 그 이전에 반드시 세팅돼야 함).

치환:
- L67: `logging.exception(f"Loading resume data failed: {e}")` → `self.logger.exception(...)`
- L197: `logging.info(f"Setting flow_resume_idx to {flow_resume_idx}")` → `self.logger.info(...)`
- L207: `logging.error(f"Error in instance {runner.ins_name}: {e}")` → `self.logger.error(...)`
- L208: `traceback.print_exc()` → `self.logger.exception("Instance %s failed", runner.ins_name)` (traceback 이 파일에 보존되도록 교체). `import traceback` 은 남은 사용처 없으면 제거.

### 6. `src/routix/runner/multi_instance_concurrent_runner.py`

`MultiInstanceConcurrentRunner.__init__` 에 `logger` 파라미터 추가하고 super 에 전달:

```python
def __init__(
    self,
    s_i_runner_class: type[SingleInstanceRunnerT],
    instances: Sequence[ParametersT],
    shared_param_dict: dict,
    subroutine_flow: Any,
    stopping_criteria: Any,
    output_dir: Path,
    output_metadata: dict[str, Any],
    mode: RunMode = RunMode.FULL_RUN,
    instance_worker_cnt: int = 2,
    logger: logging.Logger | None = None,   # NEW
    **kwargs: Any,
) -> None:
    super().__init__(
        s_i_runner_class,
        instances,
        shared_param_dict,
        subroutine_flow,
        stopping_criteria,
        output_dir,
        output_metadata,
        mode,
        logger=logger,
    )
    self.set_instance_worker_cnt(instance_worker_cnt)
```

(부모 init 에서 `self.logger` 가 세팅되므로 여기서 중복 할당 불필요.)

치환:
- L70: `logging.warning(f"Given instance_worker_cnt {instance_worker_cnt} ...")` → `self.logger.warning(...)`
- L76: `logging.info(f"Setting instance_worker_cnt to {instance_worker_cnt}")` → `self.logger.info(...)`

### 7. `src/routix/runner/multi_scenario_runner.py`

```python
def __init__(
    self,
    m_i_runner_class: type[MultiInstanceRunnerT],
    s_i_runner_class: type[SingleInstanceRunnerT],
    instances: Sequence[ParametersT],
    shared_param_dict: dict,
    scenario_configs: Sequence[dict[str, Any]],
    output_dir: Path,
    base_output_metadata: dict[str, Any],
    mode: RunMode = RunMode.FULL_RUN,
    logger: logging.Logger | None = None,   # NEW
    **kwargs: Any,
) -> None:
    self.logger = logger if logger is not None else logging.getLogger(
        f"routix.{self.__class__.__name__}"
    )
    self.e_timer = ElapsedTimer()
    ...
```

`self.logger` 할당은 **첫 줄에** 배치 (L74-86 `_init_multi_instance_runners` 안에서 scenario config 누락 시 warning 이 base init 중 발생).

치환:
- L83: `logging.warning(f"Skipping scenario {i + 1} ...")` → `self.logger.warning(...)`
- L122: `logging.info(f"--- Starting Scenario {i + 1}/{runner_cnt} ---")` → `self.logger.info(...)`
- L123: `logging.info(f"Scenario Config: {self.scenario_configs[i]}")` → `self.logger.info(...)`
- L129: `logging.error(f"Error in scenario {i + 1}: {e}", exc_info=True)` → `self.logger.error(..., exc_info=True)`
- L132: `logging.info(f"--- Finished Scenario {i + 1}/{runner_cnt} ---")` → `self.logger.info(...)`

### 8. `pyproject.toml`

버전을 `0.0.15` → `0.0.16` 으로 bump (logger 주입 경로가 생긴 API 확장).

## Backward compatibility

- 기존 사용자 입장에서 `logger` 인자 없이 객체를 만들면 여전히 child logger 로 propagate 되어 root 로 출력됨 (출력 동작 동일)
- 단, logger name 이 `"root"` → `"routix.SubroutineController"` / `"routix.MultiScenarioRunner"` / 등으로 바뀜. logger name 으로 필터링하던 사용자는 영향 받을 수 있음 → README / CHANGELOG 에 명시
- `logging.basicConfig()` 으로 root 에 StreamHandler 를 붙이고 쓰던 기존 사용자는 `propagate=True` (기본) 이므로 출력은 그대로 나옴

## Tests

`tests/test_subroutine_controller.py`:
- `SubroutineController(..., logger=custom_logger)` 로 주입 시 `self.logger is custom_logger` 확인
- 주입 없을 때 `self.logger.name == f"routix.{SubroutineController.__name__}"` 확인
- `_call_method` 실행 시 `caplog.records` 에서 logger name 이 `"routix.SubroutineController"` 로 기록되는지 확인

`tests/test_concurrent.py` 및 runner 관련 테스트:
- 각 runner 클래스 (`SingleInstanceRunner`, `MultiInstanceRunner`, `MultiInstanceConcurrentRunner`, `MultiScenarioRunner`) 의 `self.logger` 속성 존재 및 기본 이름 (`routix.<ClassName>`) 확인
- `logger=` 주입 시 해당 logger 가 그대로 세팅되는지 확인
- `caplog` 로 runner 레벨 로그가 `self.logger.name` 으로 기록되는지 확인

`tests/test_subroutine_flow_validator.py`:
- `SubroutineFlowValidator(..., logger=custom_logger)` 주입 확인
- 주입 없을 때 `self.logger.name == "routix.SubroutineFlowValidator"` 확인

`SolutionManager` 는 추상 클래스이므로 기존 테스트 패턴 (구체 서브클래스) 에 맞춰 `self.logger` 속성 및 logger name 확인 케이스만 추가.

## Verification

1. `uv run pytest` — 모든 기존 테스트 통과 + 신규 테스트 통과
2. `ffc_ddw_sum_et` 저장소에서 이 routix 버전을 editable install / 버전 bump 후 `uv run python main.py` 실행 → 각 scope log 파일이 정상 생성되는지 연동 확인 (이 검증은 ffc 측 plan `plans/20260421/logging-overhaul.md` 의 verification 단계에서 수행)

## Out of scope

- 구조화 로깅(JSON / key-value) 도입 — 별도 제안
- `logging.config.dictConfig` 기반 설정 도입 — 별도 제안
- `ProcessPoolExecutor` 자식 프로세스의 logger 초기화 hook — 하위 프로젝트 `SingleInstanceRunner.__init__` 에서 처리하는 것으로 합의됨 (routix 측 변경 불필요). 주입된 `logger` 가 worker process 로 pickle 되지 않는 경우의 재생성 책임도 ffc 측에 있음.
