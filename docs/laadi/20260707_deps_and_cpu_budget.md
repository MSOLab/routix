# Laadi 보강 메모 — 의존성 정책 · CPU core 예산 사전 검사

작성일: 2026-07-07
상태: 메모 — `20260702_laadi_plan.md`의 보강. 서로 다른 두 주제를 기록 목적으로 한
문서에 담음. laadi 저장소 생성 시 §1은 계획서 §5.11(의존성·배포 정책)의 보강으로,
§2는 신규 요구사항으로 각각 분배한다.

---

## 1. 의존성 정책 — pydantic·loguru 미채택 (2026-07-07 결정)

계획서 §5.11(core 런타임 의존성 최소)의 구체화. 판단 기준은 "최신 패키지냐"가
아니라 다음 세 질문:

1. **계약 SSOT(P1)를 보강하는가, 경쟁하는가?** — jsonschema/referencing은 SSOT를
   집행하는 쪽이라 core에 있음. SSOT 자리를 두고 경쟁하면 탈락.
2. **seam으로 새는가?** — 도메인 instance 프로토콜(`name` + `from_<format>` +
   JSON-safe 직렬화만 요구, §4)이나 subalgorithm callable에 의존성이 강제되면 탈락.
3. **core가 아니어도 된다면 extra로 가능한가?** — pandas/matplotlib이 `[report]`로
   간 것과 같은 경로.

### 1.1 pydantic — 미채택

| 논점 | 내용 |
| --- | --- |
| SSOT 역전 | 도입하면 현실적으로 Python 모델이 정본이 되고 JSON Schema는 `model_json_schema()` 파생물이 됨 — P1(JSON Schema 2020-12 = SSOT, contract-first) 위반. v2 언어 교체(§9)의 전제가 흔들림 |
| 생성 스키마 drift | pydantic이 뽑는 스키마는 pydantic 버전에 따라 출력이 변함(`$defs` 구조, nullable 표현 등). 손으로 쓴 스키마는 리뷰 가능한 diff — "계약 변경은 breaking change급 리뷰" 원칙과 정합 |
| seam 오염 | core에 있으면 `BaseModel` 상속이 도메인 instance로 스며듦 — schore가 routix와 결합 zero였던 건강함(부록 B)을 잃음 |
| 에러 메시지 | pydantic의 장점이나, `laadi validate`가 어차피 "무엇을 어떻게 고치라"까지 감싸므로(§6.2) jsonschema 원본 에러를 노출할 일 없음 |

단, **표현력은 결정 사유가 아님**을 기록해 둔다: zone fail-fast 규칙(§2.2)은
pydantic v2로도 discriminated union(`Field(discriminator="scope")`) → `oneOf` +
분기별 `const` 태그 형태로 언어중립 표현이 가능하다. 그럼에도 aladia의
`if/then/else` 인코딩을 그대로 계승하는 쪽이 위 세 논점에서 우선한다.

부수 결정:

- 검증 후 in-memory 표현은 **frozen dataclass**로 충분 — 검증은 스키마가 이미
  했으므로 이중 검증 체계는 DRY 위반.
- **dev-time 코드젠은 허용**: 스키마→dataclass 스텁 생성(datamodel-code-generator류)은
  SSOT 방향(스키마→코드)을 지키면서 손 타이핑만 줄이므로 원칙과 충돌 없음.
  단 v1은 계약 수가 감당 가능한 규모라 필요해질 때만 도입 (YAGNI).

### 1.2 loguru — 미채택

- §3.3 원칙 4 — **"로그는 사람용, 기계가 소비할 데이터는 계약 아티팩트로"** — 가
  구조화 로깅의 수요 자체를 제거한다. 로그에서 데이터를 복원할 일이 없도록 설계한
  것이 frame_record/trajectory인데, 로깅을 고급화할 이유가 없음.
- loguru는 **전역 싱글턴 sink 모델**이라 라이브러리에 부적합. laadi는 호스트
  저장소에 설치되는 프레임워크 — 호스트의 로깅 구성과 충돌하거나 인터셉트 배선을
  강요하게 됨. 정석대로 **stdlib `logging.getLogger(__name__)`로 방출만** 하고
  핸들러 구성은 호스트 몫으로.
- frame 주소 접두사류 컨텍스트는 stdlib `LoggerAdapter`/`contextvars`로, concurrent
  runner의 멀티프로세스 로깅은 `QueueHandler`로 충분.

---

## 2. CPU core 예산 사전 검사 (신규 요구, 2026-07-07)

### 2.1 요구

알고리즘 실험의 병목은 I/O가 아니라 **physical core**다. 따라서 실험 시작 데이터
(run_config)를 받는 시점에 다음을 검사할 수 있어야 한다:

> 현재 실험 config가 **동시에 최대로 사용하게 되는 physical core 수**는 몇인가?

이 값이 머신의 physical core 수보다 너무 크면 **실행 전에 error를 발생**시킨다
(fail-fast — run이 시작된 뒤 oversubscription으로 전체 측정이 오염되는 것을 방지).

### 2.2 원칙 — algorithm 일반 원칙 (solver 한정 아님)

solver 사용 시에만 적용되는 규칙이 아니라 **모든 algorithm(subalgorithm)의 기본
원칙**이다:

> **별도 표기하지 않는 경우 core를 최대 하나만 사용한다.** core를 여럿 사용할 수
> 있는 algorithm은 core 수를 **정해진 optional keyword argument**로 지정받을 수
> 있으며, 그 keyword argument의 **default value는 1**이다.

- **표준 keyword는 하나.** solver adapter든 순수 Python 휴리스틱이든 동일한 예약
  필드명을 쓴다. solver별 파라미터(CP-SAT `num_workers`, CPLEX `threads`, Gurobi
  `Threads` 등)로의 번역은 adapter(2a 플러그인)의 책임 — 계약 문구로 명시.
  ("core 하나"를 "thread 하나 사용"으로 세는 관례도 있으나 같은 의미.)
- **예산 계산식**: 모든 step의 core 사용량 = keyword 값(미지정 시 default 1)로
  집계 — `max(step별 keyword 값) × instance 병렬화 수(worker)` 를 physical core
  수와 비교, 초과 시 error.
- 이 원칙은 계획서 §2.4 실행 불변식(I1–I6) 목록의 **편입 후보** — "선언한 불변식은
  기계가 강제한다"(§3.3 원칙 2)의 적용 대상.

### 2.3 계획서와의 접점 (설계 스케치)

- **검사 시점**: run_config 로드 시 — Define층 strict 검증(§5.5)과 `laadi validate`
  (§6.2), 그리고 `laadi run` 기동 직전 양쪽에서 같은 검사기를 호출. S6(실험 세팅)
  완료 판정(§6.1)에 편입 가능.
- **keyword의 자리**: flow step params의 **예약 필드** = subalgorithm callable의
  optional keyword argument (default 1). subalgorithm_spec이 multi-core 지원 여부를
  선언하면 기계 검증이 두 갈래로 가능: ① multi-core 미지원 algorithm에 keyword를
  넘기는 config를 `laadi validate`가 거부, ② 예산 검사기는 선언과 무관하게 모든
  step을 keyword 값(없으면 1)으로 집계. 구체 필드명은 laadi 저장소에서 계약 설계 시
  확정.
- **동시성 모델**: step은 instance 안에서 순차이므로
  per-instance peak = max(step별 keyword 값, 기본 1),
  전체 peak = instance worker 수 × per-instance peak.
  (시나리오 순차 실행 가정 — routix 관례 계승.)
- **ResourceMonitor와의 관계** (`20260528_resource_monitor.md`, v1.x): 본 검사는
  **정적 사전 예산 검사**, ResourceMonitor는 **동적 사후 관측** — 상보적.
  관측이 예산 초과를 발견하면 keyword 선언이 실제와 다르다는 신호 (§2.5의 CP-SAT
  wall-clock 오버런 관측과 같은 계열의 실행층 자원 관심사).

### 2.4 미해결 (laadi 저장소에서 결정)

- **physical core 수 검출 방법**: stdlib `os.cpu_count()`는 logical 수만 반환.
  후보 — ① Linux `/proc/cpuinfo`·`lscpu` 파싱(stdlib만, 플랫폼 한정),
  ② `psutil.cpu_count(logical=False)` (의존성 추가 — §5.11 최소 의존성과 절충),
  ③ run_config/머신 설정에 명시 필드 + 자동 검출은 best-effort 폴백.
- **escape hatch**: 초과 시 무조건 error가 기본이되, 의도적 oversubscription 허용
  플래그가 필요한지 (예: 짧은 스모크 런). 일단 없이 시작.
- algorithm(특히 solver나 BLAS류 내부 라이브러리)이 선언 없이 멀티스레드를 쓰거나
  keyword를 전달받고도 지키지 않는 경우 — 사전 예산 검사는 선언 기반이라 못 잡음.
  ResourceMonitor 관측으로 닫는 것이 자연스러움.
