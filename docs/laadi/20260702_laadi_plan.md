# Laadi 패키지 정의 계획

작성일: 2026-07-02
갱신: 2026-07-03 — frame(액자) 모델·analyzer 1급 시민 추가 (§1.2, §5.9–5.10)
갱신: 2026-07-06 — §10 미해결질문 결정 반영 (§0.1; 8번만 잔존), routix 검증 버그
수정 완료 (§3.1, §10-6)
갱신: 2026-07-09 — 계산 실험 안정성 추가 (§5.12: step checkpoint·graceful
shutdown·원자적 쓰기 — `ffc_cmax` checkpoint 관행 조사 기반; §2.5·§5.4·§8·§9 연동);
RESUME 두 용례(crash recovery / prefix 분기)와 `ffc_dw_wET` c2657e0b 검증본 반영
(§5.12, §9)
갱신: 2026-07-11 — composite subalgorithm(정의로서의 시퀀스) 추가 (§5.3.1;
§2.3·§2.4·§5.5·§5.9·§6.1·§6.2 연동). 실전 선례 = `../ffc_dw_wET_2026`의
`coarsen_solve_reconstruct`/`solve_flow`(조사로 검증, IMPLEMENTED 2026-07-11)
상태: 초안 — laadi 저장소 생성 전 참조 문서 (routix 저장소 docs/laadi/에 참조용으로
커밋됨; 작업 상태 정본은 docs/laadi/AGENTS.md)

> **Laadi** = **L**ibrary for **A**lgorithm **A**nalysis & **D**esign **I**nfrastructure.
> routix의 의도를 계승하고 aladia의 설계 자산을 참조하되, **greenfield로 재작성**하는
> 새 패키지의 정의 계획.

관련 자료 (검증된 출처):

- routix: `src/routix/**`, `docs/20260429_artifact_manager.md`, `docs/20260528_resource_monitor.md`
- aladia (요구사항 기록): `../aladia/docs/01_routix_know_how.md`, `../aladia/docs/02_contracts.md`,
  `../aladia/contracts/**`, `../aladia/AGENTS.md`
- 실전 사용처: `../ffc_dw_wET_2026` (routix 단독 — 의도에 가장 부합),
  `../fm_prmu_sumTj_2026`, `../ffc_cmax_2026` (routix+mbls+schore)
- 경계 참조: `../mbls` (solver adapter의 예), `../schore` (domain 패키지의 예)

---

## 0. 확정된 결정 (2026-07-02)

| 항목 | 결정 |
| --- | --- |
| aladia와의 관계 | **greenfield 재작성**. aladia의 문서·계약은 참조 자료로만 쓰고 코드는 계승하지 않음 |
| LLM 가이드 형태 | **CLI 상태기계** (`laadi init/status/validate/add`) + **AGENTS.md/템플릿 scaffold** 병행 |
| v1 검증 | **toy 예제를 LLM이 처음부터 구축**하는 시나리오로 acceptance, `ffc_dw_wET_2026` 마이그레이션은 v1.x |
| 이름 | `laadi` — PyPI 미등록 확인 (2026-07-02 기준 404; `aladia`도 실제로는 미공개였음) |
| routix | 그대로 유지. laadi는 drop-in 대체가 아님 |

### 0.1 추가 확정 (2026-07-06 — §10 답변)

| 항목 | 결정 |
| --- | --- |
| subalgorithm 실행 모델 (§5.3, §10-1) | **context-callable** 확정. 판단 기준 = "Sonnet 4.5급 LLM이 작성하기 좋은 형태" — 근거는 §10-1. 사용감 스파이크 불요 |
| stopping criteria (§10-2) | per-instance timelimit **표현식(`"5nc"`류)을 표준 필드로 — 필수 기능** |
| 분석 v1 절단선 (§10-3) | 제안대로 확정: core = aggregate_row+statistics+analyzer 실행기 / `[report]` extra = RPDf·차트 / gantt류 도메인 렌더러 = 도메인 모듈 소관 |
| 이름·PyPI (§10-4) | `laadi` 유지, **PyPI 선점하지 않음** — 공개 시점에 선점돼 있으면 개명 |
| 문서 언어 (§10-5) | **전부 영어** (한국어 질의에는 LLM이 한국어로 응답하므로 사용성 손실 없음) |
| routix 병행 유지보수 (§10-6) | §3.1 검증 버그 3건 routix에서 수정 **완료** (2026-07-06) |
| frame 크기 정책 (§10-7) | 제안대로: v1 무제한 + 크기 관측(frame_record에 bytes), 상한/샘플링/압축은 데이터 축적 후 |
| frame ↔ (2a) 접점 (§10-8) | **미해결 유지** — 유일한 잔여 질문 |

별도 결정 대기: ccdeJava 검토(`20260703_laadi_ccdeJava_review.md`)의 제안 P-1~P-8.

---

## 1. 배경 — 계보와 문제의식

```txt
routix (2026-)                      실전 3개 저장소 운영으로 노하우 축적
  └→ aladia (2026-06)               계약 우선(greenfield) 1차 시도. 문서·계약 설계는 성숙,
  │                                  구현은 (a)↔(b) 미배선 등 갭 존재 (§3.2)
  └→ Laadi (본 계획)                 aladia의 요구사항 + 실전 통증 + 신규 요구(LLM 가이드)를
                                     합쳐 다시 greenfield
```

routix의 근본 문제 (사용자 정의): 세 관심사가 분리되지 않음.

1. **실험 결과를 저장하는 폴더 구조 정의**
2. **알고리즘 정의 및 실험 실행**
3. **분석 양식 정의 및 실험 분석**

궁극 목표: (2)가 programming language-agnostic해지고, (1)과 (3)을 각각 다른 언어로
구현할 수 있는 상태 (예: (1)을 C/Java로, (3)을 Python/JS로). 단, **v1은 세 관심사
모두 Python**. 언어 교체는 계약(contract)이 경계를 지키는지 검증된 뒤의 일 (§9).

추가 관찰 (사용자): (2) 안에서도 **알고리즘 정의/실행**과 **실험 orchestration**은
다른 언어가 어울릴 수 있다. `docs/20260528_resource_monitor.md` 같은 관측 인프라는
C로 만들 엄두가 안 나지만 Python이면 자연스럽다. → §4의 관심사 모델에서 (2)를
(2a)/(2b)로 내부 분할해 이 seam을 예약한다.

### 1.1 즉시 요구사항 (v1의 존재 이유)

> `uv add laadi` 후 LLM에게 "실험을 위한 코드베이스 작성해"라고 시키면,
> **무엇을 어떤 순서로 해야 하는지 LLM이 알고 step-by-step으로 진행**할 수 있어야 한다.
> (input data 준비 → input data class 생성 → 규약에 맞춘 subalgorithm 작성 →
> orchestration → 분석)

현재는 이 스토리를 지원하는 것이 **어디에도 없다**: routix에는 scaffold/템플릿/가이드가
전무하고, aladia의 AGENTS.md는 좋은 플레이북이지만 aladia 저장소 안에만 있어서
`uv add`로 설치한 소비 저장소에는 전달되지 않으며, 뒷받침하는 CLI/validator도 없다.

### 1.2 추가 요구 (2026-07-03): subalgorithm 단위 기록·분석 = 필수 기능

> subalgorithm별 분석은 거의 언제나 필요하다 (예: `ffc_dw_wET`의
> `calc_mcf_lb_and_derive_full_sch`를 위한 전용 분석 파일 다수). 현재는 파일이
> 여기저기 쌓여서 좋은 practice가 아니지만 더 나은 방법을 못 찾은 상태.
> **subalgorithm 단위의 분석 파일 생성은 알고리즘 분석·디자인의 필수 기능이다.**
>
> subalgorithm도 algorithm이다 — 즉 **액자식(재귀) 구성**이고, 액자 단위로 결과
> 기록과 분석이 되어야 한다. 핵심은 실험 수행 시 필요한 데이터를 **전부 어떻게든
> 텍스트로 기록**해 두는 것. 그림·HTML 생성은 분석 때의 일이며, 실행은 분석에
> 필요한 데이터를 유연하게 보관할 수 있으면 된다.

→ §5.9(frame 모델: 기록 측), §5.10(analyzer + study: 분석 측)로 설계에 반영.

---

## 2. 요구사항 복원 — aladia에 부어졌던 것

aladia의 `docs/01_routix_know_how.md`(KEEP/FIX 목록)와 `docs/02_contracts.md`,
`contracts/` 스키마 10종에서 복원한 요구사항. **Laadi가 전부 계승한다.**

### 2.1 원칙 (Prime directives)

- **P1. 세 관심사는 오직 디스크 위 아티팩트로만 소통한다.** 모든 경계(폴더 layout,
  실험 config, 아티팩트 내용)는 기계가 읽는 계약 — JSON Schema 2020-12 — 이 SSOT.
- **P2. Postel 원칙**: 정의 계약(layout, run_config, spec류)은 strict
  (`additionalProperties: false` — 오타 즉시 검출), 데이터 아티팩트(manifest,
  solution, trajectory 등)는 lenient (생산자가 필드를 추가해도 구 reader가 안 깨짐).
- **P3. self-describing**: 모든 데이터 아티팩트는 `laadi_schema: {kind, version}`
  헤더와 run/scenario/instance 좌표를 문서 안에 지님. 버전은 깨는 변경에만 증가.
- **P4. agent-legibility**: 모양(schema)과 자리(layout)가 명시적 SSOT이면, LLM 작업은
  "정해진 모양을 정해진 자리에 추가"가 되고 기계가 검증할 수 있다.

### 2.2 계승하는 데이터 모델 (routix의 크라운 주얼)

- **scope × zone 2축 모델**: scope = `run → scenario → instance`,
  zone(instance 한정) = `final`(안정 산출물, 덮어쓰기 금기) / `progress`(감사·디버그
  흔적) / `report`(재생성 가능한 2차 가공물). `final+progress` = 실행(2)의 영역,
  `report` = 분석(3)의 영역 — zone 분류가 곧 (2)/(3) 분리의 의미론적 기반.
- **zone fail-fast 규칙**: scope=instance면 zone **필수**, run/scenario면 **금지**.
  (미지정이 가장 보호받는 final로 조용히 떨어졌던 실제 사고의 재발 방지.
  aladia는 이를 JSON Schema if/then/else로 인코딩 — 그 방식 그대로 계승.)
- **layout 계약**: (scope, kind, zone) → path 해석을 스키마 데이터로 선언.
  `register_kind`식 프로젝트 overlay, `stamp()`로 사용된 스키마를 run 디렉터리에 박제,
  reader의 해석 우선순위 = 박제본 > 명시 제공 > 기본값. 경로 하드코딩 전면 금지.
- **RunMode seam**: `FULL_RUN / RESUME / POST_PROCESS_ONLY`. POST_PROCESS_ONLY가
  (2)/(3) 분리가 이미 동작함을 증명하는 축 — 계승하되 §5의 실패 계약과 함께 완성.
- **SRP bottom-up 러너 파이프라인**: controller → single-instance → multi-instance
  (+concurrent) → multi-scenario. 층간 데이터는 메모리가 아니라 **디스크의 계약
  아티팩트**로 흐른다 (POST_PROCESS_ONLY와 외부 도구가 같은 면을 씀).

### 2.3 계승하는 계약 인벤토리 (aladia `contracts/core/` 기준)

| kind | 성격 | 요지 |
| --- | --- | --- |
| `layout` | 정의·strict | scopes/zones/logs/artifacts 선언, zone 규칙 인코딩 |
| `run_config` | 정의·strict | 실험 세팅: output_dir, instance_selection, worker 수, scenarios[] |
| `subalgorithm_spec` | 정의·strict | input–mechanism–output 3요소 + `emits_trajectory`. mechanism = **`code_ref`(atomic 또는 래핑형) 또는 `steps` sub-flow(선언형 composite — §5.3.1)**, 상호배타·strict. 래핑형은 `code_ref`에 flow-typed param을 **추가** 선언 — 이 param은 code_ref의 대안이 아니라 그 위에 얹히는 직교 축(§5.3.1 form B, CSR가 정본) |
| `problem_spec` | 정의·strict | parameters/variables/objective/constraints + backends(mip/cp) |
| `instance_manifest` | 데이터·lenient | per-instance 결과의 정본. status enum, first/best obj, **artifacts 색인(kind→상대경로)** — reader가 glob하지 않게 하는 열쇠. **atomic write, 맨 마지막에** |
| `solution` | 데이터·lenient | `{obj_value, obj_bound, payload_kind, payload}` 봉투. tuple-key YAML 폐기, JSON |
| `trajectory` | 데이터·lenient | 시간축 표준 출력. JSONL 1줄 = `{series, t, value, note?}` (append-friendly, crash-resilient, 타 언어 writer 친화). 읽기 뷰는 grouped 형태 |
| `step_record` | 데이터·lenient | step당 1레코드: method, call_context, start/elapsed, params, obj, error? — Laadi에서는 **frame_record로 일반화** (§5.9: 임의 깊이의 액자 트리) |
| `aggregate_row` | 데이터 | (3)이 생산하는 집계 행. 추가 컬럼은 스칼라로 제한(CSV/타 언어 안전) |
| domain 모듈 (예: `scheduling/schedule`) | opt-in | core는 도메인 무지. payload_kind로 디스패치 |

### 2.4 계약으로 승격하는 실행 불변식

routix 호스트들의 AGENTS.md에만 존재하던 관례를 **기계가 강제**한다:

- **I1. step당 register 최대 1회.** (위반 시 obj_log 집계가 조용히 오염 — 현재는
  아무도 검출 못함) composite subalgorithm(§5.3.1) 하에서는 **leaf 단위**로 성립하고
  composite 부모는 자식 outcome을 집계해 1회 register.
- **I2. elapsed_time은 step 진입~register 사이 monotonic 측정, register 직전 캡처
  이후 추가 작업 금지.**
- I3. zone 규율 (final에 파생물 금지).
- I4. 시계열은 trajectory 계약으로만 방출 (ad-hoc 파일 금지).
- I5. 경로는 layout으로만 해석.
- I6. 변경 후 validator 실행으로 루프를 닫는다.

composite subalgorithm 도입 시 flow/spec의 재귀 검증(child 존재·params 정합·**cycle
없음**, §5.3.1)은 이 I-목록의 **편입 후보** — "선언한 불변식은 기계가 강제"(§3.3 원칙 2).

### 2.5 3개 실험 저장소에서 추가로 추출된 요구

- **RESUME 공통화**: 세 저장소가 각각 ~350 LOC를 재발명 (해/obj-trace 복원, 가상
  타이머, flow prefix 검증, 파일 존재성 정책). 프레임워크가 소유해야 함.
- **step checkpoint 공통화**: `ffc_cmax`는 최상위 flow 스텝이 성공적으로 끝날 때마다
  incumbent schedule 전체(start/end time map)+obj log+summary를 resume 입력과 동일한
  파일 모양으로 `checkpoints/<step>-<method>/<instance>/results/`에 기록
  (`hybridflowshop/controller/controller_core.py` `_try_save_step_checkpoint`).
  checkpoint를 가리키는 resume metadata YAML 82개가 실전 소비를 증명. 단 앱 레벨
  구현이라 갭 존재 — 비원자적 쓰기, signal 무방비, 첫 feasible 이전 무기록, 예외
  스텝 미기록. 프레임워크가 소유해야 함 (§5.12).
- **step 템플릿 흡수**: `ffc_dw_wET`의 controller.py는 동일한 ~30줄 템플릿
  (monotonic 시작 → Option 조립 → 실행 → None-safe obj 추출 → report → register)을
  ~30회 복붙. TODOS.md가 데코레이터화를 명시적으로 미룸 — Laadi가 흡수.
- **cross-run 분석/provenance**: run 비교가 손으로 유지하는 RUNS 테이블과
  'run setting' commit 관행에 의존. run manifest(계약)로 구조화 필요.
- **baseline/BKS 조인**: 세 저장소 모두 외부 BKS CSV를 조인해 RPDf를 계산하는데
  컬럼명('Instance' vs 'insName')·파일 위치가 전부 암묵 규약 — 계약 필요.
- **분석이 로그를 regex 파싱**: `fm_prmu`의 `scripts/process_logs.py`는 method
  timing을 복원하려고 log 텍스트에 `ast.literal_eval`을 돌림. 기계가 소비할 데이터가
  로그로만 존재했기 때문 — trajectory/step_record 계약이 근본 해법.
- **solver 오버런의 사후 보정**: CP-SAT wall-clock 초과(+473s 관측)를 분석층이
  잘라내는(`apply_timelimit_trim`) 구조. 실행층 관측(ResourceMonitor)과 timelimit
  정책이 프레임워크 관심사임을 보여줌 (§9 로드맵).
- **god-controller 문제**: flow step이 "controller의 메서드"여야만 해서
  `ffc_cmax`의 컨트롤러가 17,358줄로 비대해짐. 알고리즘 단위의 더 작은 계약 필요 (§5.3).

---

## 3. 반복하지 말아야 할 것 — 검증된 결함 목록

### 3.1 routix에서 (조사로 검증됨)

| 결함 | 위치 | Laadi 대응 |
| --- | --- | --- |
| controller 예외를 `finally: return post_run_process()`가 전부 삼킴 | `runner/single_instance_runner.py:99-105` | 실패 계약 §5.4 |
| concurrent runner에 per-instance 예외 격리 없음 (`future.result()`가 시나리오 전체를 죽임) | `runner/multi_instance_concurrent_runner.py` | 실패 계약 §5.4 |
| pyyaml을 import하면서 runtime 의존성 미선언 (`dependencies=[]`) — 깨끗한 설치에서 import 실패 | `pyproject.toml` | 의존성 명시 + 설치 스모크 테스트 |
| layout이 실행에 미배선: runner들이 `layout` 파라미터를 받고 안 씀, RESUME 경로는 스키마에 없는 제3의 규약(`results/`, `*_solution.yaml`) 하드코딩 — **레이아웃 지식이 3곳에서 3가지 답** | `multi_instance_runner.py:129-206` 등 | layout이 유일한 경로 권위 §5.1 |
| 문서 drift: 삭제된 API(SubroutineReportRecorder)·미구현 API(discover_*)를 README가 안내 | README, runner/README.md | 문서는 코드에서 생성하거나 contract 테스트로 검증 |
| 암묵 계약 무더기: `instance.name`, `output_metadata`/`shared_param_dict` 문자열 키, camelCase CSV 컬럼 | 전반 | 전부 스키마化 |

2026-07-06: 위 중 3건 — 예외 삼킴, concurrent 격리 부재, pyyaml 미선언 — 은 routix에서
직접 수정 완료 (§10-6, `tests/test_runner_failure.py`·`tests/test_packaging.py` 동반).
layout 미배선·문서 drift·암묵 계약은 설계 수준 문제라 laadi가 해소.

### 3.2 aladia에서 ("v1 완성" 주장 대비 실제 갭)

- **(a)→(b) 미배선**: `run_config` 스키마는 있으나 그것을 로드해 러너를 구동하는
  코드가 없음. 필드명 drift(`stopping_criteria` vs 코드의 `stopping`)가 **round-trip
  테스트 부재의 증거**.
- **contracts 패키징 미해결**: repo-root `contracts/`가 wheel에 실리지 않아 설치 후
  `contracts_dir()`가 `FileNotFoundError` — `uv add` 스토리의 직접적 blocker.
- **선언한 불변식 미강제**: I1/I2 런타임 체크 없음, spec↔code↔flow 정합 validator
  미구현, flow 정적 검증도 없음(routix에는 있었음).
- RESUME enum-only, 예외 격리 없음, 시나리오 중복 가드 없음, error manifest를 쓰는
  경로 없음, scaffolder/validator CLI 미착수.

### 3.3 Laadi의 작동 원칙 (위 실패의 일반화)

1. **소비자 없는 계약은 넣지 않는다.** 모든 계약은 그것을 쓰는(write) 코드와
   읽는(read) 코드, 그리고 **config→실행→읽기 round-trip 테스트**와 함께 착지한다.
2. **선언한 불변식은 기계가 강제한다.** 문서에만 있는 규칙은 규칙이 아니다.
3. **설치 상태에서 검증한다.** `uv add laadi` 직후의 스모크 테스트(임시 venv에서
   import + `laadi init` + toy run)가 CI에 포함된다.
4. **로그는 사람용이다.** 기계가 소비할 데이터는 반드시 계약 아티팩트로 나온다.

---

## 4. 관심사 모델 — 경계 다이어그램

사용자의 세 관심사에 (2)의 내부 seam을 더한 모델:

```txt
┌─────────────────── Define (언어중립 선언 · 전 관심사가 공유) ───────────────────┐
│  layout        run_config        subalgorithm_spec / problem_spec               │
│  "결과가 어디에 놓이나"   "무엇을 실행하나"      "빌딩블록의 모양"                    │
└──────┬──────────────────┬──────────────────────┬────────────────────────────────┘
       │                  ▼                      │
       │   ┌───────── (2) Execute ────────────┐  │
       │   │ (2b) orchestration  ← Python 유지 │  │
       │   │   runners·process pool·logging·  │  │
       │   │   RunMode·ResourceMonitor(후속)   │  │
       │   │      │ executor seam (§9, v2에    │  │
       │   │      ▼  process 계약으로 승격)     │  │
       │   │ (2a) algorithm 정의·실행           │◄─┘  spec의 code_ref가 여기를 가리킴
       │   │   subalgorithm 구현·solver adapter │      (장기: C/C++ 등으로 교체 가능)
       │   └──────────────┬───────────────────┘
       │                  │ 산출: final/·progress/ (manifest, solution,
       │                  ▼        trajectory.jsonl, step_record.jsonl)
       │       ═══════ 파일만이 경계 (계약 준수, self-describing) ═══════
       │                  │
       ▼                  ▼
┌───────────────── (3) Analyze (장기: Python/JS 등 교체 가능) ────────────────────┐
│  open_run reader → aggregate_row / statistics / RPDf / 시각화 → report/ zone     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

관심사 소속 정리 (aladia에서 모호했던 부분의 확정):

- **(1) = layout 계약 + 그 해석기.** 사용자의 "(1) 폴더 구조"가 이것.
- **run_config, subalgorithm_spec, problem_spec은 "Define" 층**으로, 특정 관심사의
  소유물이 아니라 **모든 관심사가 공유하는 언어중립 선언**이다. (aladia의 (a)가
  layout과 config를 뭉뚱그렸던 것을 명시적으로 분리.)
- **(2a)/(2b) seam**: v1에서는 둘 다 Python이고 seam은 in-process Protocol이지만,
  계약(flow, spec, 아티팩트)에 Python 전용 가정이 스미지 않도록 설계한다.
  `code_ref`는 v1에서 `module:callable` 형식이되, spec 스키마상 "executor가 해석하는
  불투명 문자열"로 정의해 언어 교체 여지를 남긴다.
- **mbls/schore의 위치**: mbls류(solver adapter)는 (2a)에 **꽂히는 플러그인**,
  schore류(domain 데이터)는 laadi 밖의 도메인 패키지. Laadi는 이들을 흡수하지 않고
  **프로토콜 seam만 제공** — instance 데이터 클래스에 요구하는 것은
  `name: str` + `from_<format>(stream)` 파서 + JSON-safe 직렬화뿐 (np.int64 캐스팅
  같은 직렬화 관심사는 domain이 아니라 Laadi의 직렬화 경계가 흡수).

---

## 5. 핵심 설계 결정 (aladia 대비 변경·보강)

### 5.1 layout이 유일한 경로 권위

routix의 실패(레이아웃 지식 3곳 분산)를 원천 차단: **base 러너·controller·reader가
전부 layout API만으로 경로를 얻는다.** working_dir 문자열 조립 경로는 처음부터
존재하지 않는다. RESUME의 파일 존재성 검사도 layout의 kind 질의로만 수행.

### 5.2 trajectory에 attribution을 내장

aladia의 array-of-records JSONL을 계승하되 두 가지를 더한다:

- **`context` 필드**: 각 레코드에 계층적 call context(`"3-pw_cp"` 등)를 필수 부여.
  → 호스트들이 로그 regex 파싱과 mbls의 'N-method' note 관행으로 하던 per-method
  attribution이 계약 데이터가 된다 (thesis phase-breakdown 파이프라인의 요구를 흡수).
- **time basis 명시**: instance-scope 아티팩트(trajectory, step_record)의 `t`는
  **instance 실행 시작 기준 monotonic elapsed sec**. solver 내부의 solve-상대 시각은
  **방출하는 adapter가 shift할 책임** (mbls에서 host가 손으로 하던 것을 계약 문구로).
  wall-clock 정렬은 manifest의 `started_at/finished_at`(ISO-8601)으로.
- 기록 정책은 aladia의 결정 유지: **모든 register 값을 기록**하고 개선 필터링은
  read-time에 direction+`improved` 플래그로. (routix의 write-time 필터링은 폐기.)

### 5.3 subalgorithm 실행 모델 — step 템플릿과 god-controller의 동시 해소

방향 (**확정** 2026-07-06 — §10-1, 기준: LLM 사용성):

- subalgorithm = **`SubalgorithmContext`를 받아 `StepOutcome`을 반환하는 callable**
  (Protocol). controller 메서드일 필요가 없다. `subalgorithm_spec.code_ref`가 이
  callable을 가리키고, 이름으로 flow에서 참조된다.
- context가 제공: instance, params, incumbent 접근, `register()`, trajectory 방출,
  logger, stop_predicate, (읽기 전용) layout 좌표.
- **step 러너(프레임워크)가 템플릿을 소유**: monotonic 타이밍, I1/I2 불변식 강제
  (register 2회 → 즉시 에러; register 후 반환까지의 시간 감시), step_record 기록,
  예외 포획. → 호스트의 ~30줄×30회 복붙과 17k줄 컨트롤러가 함께 사라진다.
- `ffc_dw_wET`의 `AlgSpec → Algorithm.run → AlgRecord` (routix-free 알고리즘층,
  `docs/algorithm-principles.md` 18규칙 — 명시적으로 "ALADIN-style runtime" 대비)가
  이 모델의 실전 검증본이다. 그 18규칙을 context/outcome 설계의 입력으로 쓴다.
- flow의 정적 검증(routix SubroutineFlowValidator에 있었고 aladia가 누락한 것)을
  복원: flow의 method가 등록된 subalgorithm인지, params가 spec과 정합한지.

### 5.3.1 composite subalgorithm — 정의로서의 시퀀스 (2026-07-11 추가)

§1.2의 "subalgorithm도 algorithm — 액자식(재귀)"을 **정의 측**에서 실현한다. §5.3의
atomic subalgorithm(= `code_ref`가 가리키는 단일 callable)과 대비되는
**composite subalgorithm** = mechanism이 다른 subalgorithm들의 **순서 있는 시퀀스**
(= 이름 있는 재사용 sub-flow)인 subalgorithm. 지금까지 시퀀스 구성은 run_config의
flow(§5.5)에만 있었고 §5.9는 그 결과를 *기록*만 했다 — composite는 그 시퀀스를
**이름 붙은 정의**로 승격해 flow 밖에서도 재사용·검증되게 한다.

**실전 선례 (조사로 검증, 2026-07-11)**: `../ffc_dw_wET_2026`의
`coarsen_solve_reconstruct`(CSR)가 이미 구현·운용 중 — subalgorithm이 다른
subalgorithm들의 시퀀스로 정의되는 이 코드베이스의 정본 예다
(`plans/20260711/csr_solve_flow.md`, Status IMPLEMENTED). CSR 스텝은 inline
`solve_flow`(top-level flow와 **동일 schema**의 step 리스트)를 받아, coarsen된
instance 위에서 **같은 클래스의 자식 컨트롤러**로 그 시퀀스를 실행한다
(`orchestration/controller.py:2640` `coarsen_solve_reconstruct(..., solve_flow)`;
`:2816` `_coarsen_solve_reconstruct_via_flow`).

**정의 형태 두 가지 — 문법·실행·기록은 하나**:

| 형태 | mechanism | 자식 결과 집계 | 실전 선례 |
| --- | --- | --- | --- |
| (A) 선언형 composite | subalgorithm_spec의 `steps`(= sub-flow 자체), `code_ref` 없음 | 프레임워크(마지막 leaf outcome = 부모 outcome) | — (신규 재사용 블록) |
| (B) 래핑형 composite | `code_ref` + **flow-typed param**(inner flow), 코드가 전처리·후집계 | 사용자 코드(부모가 명시 register) | CSR `solve_flow`(집계·register 정본). routix `repeat`/`routine_data`는 flow-as-param **구조** 선례일 뿐 — 집계도 register도 없음(leaf가 자기 등록, §5.5), 형태 (B)의 후집계·명시 register 의미론은 CSR만이 예시 |

둘 다 (i) flow 정규형 문법 하나(§5.5)를 공유하고, (ii) step 러너가 여는 **자식 frame
subtree** 하나(§5.9)로 실행되며, (iii) frame 트리 하나로 기록된다. 차이는 자식들의
결과를 프레임워크가 집계하느냐(A) 사용자 코드가 집계하느냐(B)뿐이다.

**parameter passing** — 자식 시퀀스로 값이 흐르는 규약:

- inner step은 각자 params를 inline으로 실어 자식 subalgorithm에 전달 (routix
  `_call_method(**kwargs)` 계승 — CSR `solve_flow`의 각 step이 이 방식).
- 래핑형에서 composite **자신의** params(CSR `factor`, `timelimit`)는 wrapper 소관.
  자식에 넘어가는 것은 composite가 **명시적으로 구성**한 (instance, budget, scale) —
  CSR: coarsen된 instance + `child_timelimit = min(composite budget, remaining)`
  strict-min + `time_factor` scale bridge(coarse 완료시각을 원척으로 환산). 프레임워크는
  timelimit 표현식(§10-2 `"5nc"`류) 평가·budget strict-min·frame 좌표만 제공하고,
  instance 변환·scale은 composite 코드가 소유.
- timelimit 표현식은 **자식이 도는 instance 기준**으로 평가 (CSR: coarsen이 `p`만
  바꾸고 `n,c`는 불변이라 초 단위 값은 원 instance와 동일 — `csr_subalg.yaml` 주석).

**nesting depth — 무제한 + cycle 금지 (v1 채택)**: composite의 자식이 또 composite여도
같은 기계의 재귀(§5.9 frame 재귀 = §1.2 액자식)로 처리된다. **명시적 depth guard는
두지 않는다**; 실질 상한은 (a) 공유 시간 예산(자식 budget = `min(composite budget,
remaining)`, 매 step 전 stop_predicate 검사)과 (b) 정적 검증의 cycle 금지(아래).
CSR v1은 1단계만 쓰지만 기계는 재귀를 구조적으로 지원 — ffc 문서가 재귀 시
`time_factor`가 단계마다 곱해짐을 명시. depth 상한/샘플링은 §10-7(frame 크기 정책)과
동형으로 데이터 축적 후 결정.

**validation implications** — §5.3의 flow 정적 검증을 **재귀화**:

1. composite의 모든 child ref가 **등록된 subalgorithm**인지.
2. child params가 각 child의 spec과 **정합**인지.
3. **cycle 없음** — composite가 자신을 직·간접 참조하지 않는 DAG (신규 검사;
   재귀 검증의 종료 보장).
4. 래핑형의 flow-typed param은 **비어있지 않은** step dict 시퀀스이고 각 step이
   `method` 키를 가지는지 — CSR가 child 실행 전에 step마다 `parse_step`로 검증하고 빈
   리스트를 `ValueError`로 거부하는 관행의 계약화 (`controller.py:2840` 부근).

S5(§6.1) 완료 판정은 atomic의 "code_ref import + 시그니처 적합"을 선언형에서는
이 재귀 검증으로 대체, 래핑형에서는 둘 다 요구한다.

**execution·reporting implications**:

- composite 부모는 자식 frame subtree를 열고, **leaf subalgorithm만 register**한다.
  I1(step당 register ≤1, §2.4)은 **leaf 단위**로 성립. composite 부모의 register도
  정확히 1회 — 선언형은 마지막 leaf outcome이 곧 부모 outcome, 래핑형은 부모가
  자식들의 outcome을 **집계**해 명시 register.
- CSR의 집계가 래핑형의 정본 예: 자식의 모든 등록(`child.solution_manager.history`)을
  후보로 수집 → 구조적 dedup → 원척 복원·feasibility 검증 → 원척 objective argmin
  1건만 부모 register(`obj_bound=None` — coarse 해는 원척 하한이 아니므로).
- 기록은 §5.9 그대로: 자식 frame이 트리에 자동으로 남아, 분석층이 "어느 composite가
  어느 자식 frame을 낳았는가"를 로그 파싱 없이 복원.

**§10-8과의 관계**: `context`가 자식 sub-flow를 돌리는 면(가칭 `context.run_subflow`)은
§10-8(frame 핸들을 (2a) 심층까지 전달)의 **프레임워크 주도형** 특수해다 — composite는
런너가 *선언된 step 시퀀스*를 몰기 때문에 opaque 알고리즘 내부까지 파고들 필요가 없다.
§10-8은 여전히 opaque (2a) 내부 단계를 frame으로 잡는 별도 문제로 남는다.

**concrete example — CSR `solve_flow`**
(`../ffc_dw_wET_2026/metadata/20260711/csr_subalg.yaml`, 축약):

```yaml
subroutine_flow:
  - method: coarsen_solve_reconstruct          # 래핑형 composite subalgorithm
    factor: 50
    timelimit: "0.09nc"                          # composite 자신의 예산 (wrapper 소관)
    solve_flow:                                  # flow-typed param — top-level flow와 동일 schema
      - method: calc_mcf_lb_and_derive_full_sch
        adjust_p: true
      - method: run_flip_makespan_cp_from_incumbent
        cp_tl: "0.009nc"                          # coarse instance 기준 평가 (n,c 불변)
      - method: neh_cp
        job_priority: "weight-due-pos"
      - method: incremental_sw_cp
        non_time_fixed_op_time_limit_multiplier: 0.005
      - method: solve_base_model_cpsat
```

시퀀스는 coarsen된 instance 위에서 **같은 클래스의 자식 컨트롤러**로 실행되고
(`controller.py:2886`), 자식의 매 등록이 후보가 된다:

```python
coarse_instance = FFcDDWParameters.coarsen_processing_times(instance, factor)
child = FFcDDWSubroutineController(
    instance=coarse_instance,
    subroutine_flow=solve_flow_list,             # solve_flow == 하나의 subroutine_flow
    stopping_criteria={"timelimit": child_timelimit},
    time_factor=factor,                           # coarse→원척 scale bridge
)
child.run()                                       # routix 일반 디스패치 (_run_flow → _call_method)
```

### 5.4 실패·상태 계약 (신규 설계)

routix의 예외 삼킴/전파 비일관을 실패 매트릭스로 대체:

| 실패 지점 | 동작 |
| --- | --- |
| step 내부 예외 | step_record에 `error` 기록 → controller 중단 → **manifest `status: error`로 반드시 기록** (atomic, 마지막) |
| instance 수준 실패 | 시나리오는 계속. 시나리오 통계에 실패 수 집계, 시나리오 로그에 traceback surface |
| worker/pickling 실패 | 해당 instance error 처리 + 명시 로그. pool은 유지 |
| stopping 도달 | `status: stopped` (error와 구분) |
| SIGTERM/SIGINT 1회 | cooperative stop (§5.12) — 다음 안전 지점에서 checkpoint·manifest `status: interrupted` 기록 후 종료. 2회째 신호는 즉시 종료 |
| post-process 예외 | 실행 결과를 오염시키지 않음 — report zone 산출만 포기하고 보고 |

manifest는 **모든 경로에서 반드시 쓰인다**. "manifest 존재 = 그 instance의 다른
final 아티팩트 존재"라는 `ffc_dw_wET`의 atomic-last 관행을 계약 문구로 승격.

### 5.5 flow 표기 정규형

현실(3개 저장소 전부 flat kwargs)과 스키마(strict는 nested만 가능)의 모순 해소:

- **정규형(계약) = nested `params:`** — strict 검증 가능.
- **저작 편의 = flat 허용**: loader가 flat을 nested로 정규화한 뒤 검증. 문서와
  scaffold 템플릿은 flat을 보여줌 (사람과 LLM이 쓰기 쉬운 쪽).
- **composite와 문법 공유**: composite subalgorithm(§5.3.1)의 sub-flow와 래핑형의
  flow-typed param(CSR `solve_flow`)은 **이 정규형 문법을 그대로 재사용**한다 — nesting
  표기를 둘로 가르지 않는다. routix `repeat`/`routine_data`(`subroutine_flow_data.md`)가
  flow가 자기 자신을 param으로 품는 내장 선례.

### 5.6 contracts 패키징

- 스키마 SSOT는 **`src/laadi/contracts/` (package data)** — wheel에 반드시 실림
  (`importlib.resources`로 접근). 설치 스모크 테스트가 이를 검증.
- 타 언어 도구를 위해 **`laadi contracts export <dir>`** CLI로 스키마 사본을 내보냄
  (+ 저장소에도 편의상 export본을 둘 수 있으나 SSOT는 패키지 내부).

### 5.7 objective 무결성

routix `SolutionManager.register`의 "보고값 vs 재계산값 불일치 → ValueError" 검사
(aladia가 누락)를 계승하되 위치를 조정: problem 정의가 objective evaluator를
제공하면(`problem_spec`에 선택 필드 `objective_ref`) register 시점에 재계산 검증.
미제공 시 신뢰 모드. `ffc_dw_wET`의 persist-time "SSOT recompute" 관행의 일반화.

### 5.8 provenance & 신규 계약 2종

- **`run_manifest`** (run scope, 신규): config 사본 경로/해시, laadi·플러그인 버전,
  git commit, hostname, 시작·종료 시각. → 'run setting' commit·손으로 만든 RUNS
  테이블 관행 제거, cross-run 분석의 발견 메커니즘 제공.
- **`baseline_table`** (신규): instance id ↔ BKS/LB/참조값 매핑의 표준 스키마
  (RPDf 계산의 전제). 세 저장소의 암묵 CSV 규약을 흡수.

### 5.9 Frame(액자) 모델 — subalgorithm 단위 기록 (2026-07-03 추가)

§1.2의 요구를 구조화한 것. **"subalgorithm도 algorithm"** 이므로 실행을 재귀 트리로
모델링하고, 트리의 모든 노드(=액자=frame)에서 동일한 기록·분석 기계가 작동하게 한다.

**현재 관행 (조사로 검증)** — 액자식 구조를 프레임워크 없이 손으로 재발명 중:

| 현재 (ffc_dw_wET 등) | 증거 |
| --- | --- |
| 진단 하나에 공유 파일 3곳+ 수정 (layout YAML kind 등록 + controller `_emit_*` + reporting.py `_write_*` 가족) | `calc_mcf_lb` 하나에 kind 5개 수동 등록; reporting.py 2,256줄로 비대 |
| glob 충돌을 서브디렉토리 수동 중첩으로 방어 | overlay YAML 주석: `mcf_lb_phase_schedule`/`csr`/`flip_makespan_cp` 전부 "greedy glob이 cross-match하지 않도록 subdir에 격리" |
| call_context 접두사를 파일명에 수동 부착, 분석이 문자열 prefix 매칭으로 복원 | `6-run_reactive_loop_report.csv`; flow 순서 바꾸면 전 다운스트림 파손 |
| 분석에 필요한 값 미보존 → 재실행/로그 스크래핑 | CSR coarse obj 미기록 → 1,440 인스턴스 결정론적 재실행 (`dump_csr_coarse_obj.py`); 3개 스크립트가 로그를 regex+`ast.literal_eval`로 긁음 |
| 진단 방출 게이트가 step별 ad-hoc boolean | `emit_phase_schedules`, `draw_pmtn_sch_heatmap` |

**설계**:

- **frame 트리**: 실행 = frame의 트리. root frame = instance 실행 전체, subalgorithm
  호출 = 자식 frame, composite subalgorithm(§5.3.1)의 내부 단계(round, phase)도 frame
  — 재귀. composite가 정의로 **선언한 자식 시퀀스**는 이 자식 frame들에 결정론적으로
  대응한다 — 정의 측(§5.3.1)과 기록 측(여기)이 한 트리를 공유(정의 대칭 = 기록 대칭).
  frame 주소 = call context 경로 (`3-calc_mcf_lb.r1` 식). routix
  MethodContextManager가 로그 접두사로만 쓰던 것을 **기록·발견·분석의 1급 좌표**로 승격.
- **frame_record** (step_record의 일반화, JSONL): frame이 닫힐 때 1줄 — 주소, parent,
  method, params, start/elapsed, obj 변화, `metrics`(자유 스칼라 dict), error.
  트리 전체가 텍스트로 직렬화되어 분석층이 실행 구조를 **로그 파싱 없이** 복원한다.
- **frame 방출 API** — 실행층의 유일한 기록 면:
  - `frame.emit(label, data, level=...)` → layout이
    `progress/<frame주소>/<seq>_<label>.json`에 자동 배치하고 **manifest의 artifacts
    색인에 등록**. kind 수동 등록·서브디렉토리 수동 중첩이 사라지고, 발견이 색인
    질의가 되므로 greedy glob 문제가 구조적으로 소멸.
  - `frame.metric(key, value, note?)` → 단발 스칼라는 frame_record.metrics로, 시계열은
    trajectory(context=frame주소)로. **free-text 로그 스크래핑 클래스 전체 제거.**
  - "의심되면 기록한다"를 싸게: 방출물은 lenient 봉투(어느 frame이, 언제, 무슨
    label로)+자유 payload. 특정 payload가 안정되면 domain 계약으로 승격 (예: schedule
    snapshot).
- **diagnostic level**: step별 ad-hoc boolean을 대체하는 표준 knob.
  run_config/scenario/step 수준에서 지정하고 `frame.emit`의 `level`이 게이트.
  "분석 입력을 만들기 위한 debug run config"가 1급 개념이 된다.
- **텍스트 전용 계약**: 실행층 산출 포맷 whitelist = JSON/JSONL/CSV(+YAML).
  renderable(PNG/SVG/HTML)은 report zone 전용 = **분석층만 생산**. 이 조항은 (2a)
  언어 교체성의 전제이기도 하다 — C++ executor가 matplotlib 없이 완전한 기록을
  남길 수 있어야 한다.

계승할 좋은 관행: `ffc_dw_wET`의 step별 진단 dataclass(단일 작성자, validity
predicate 포함 — `algorithm/mcf_lb/diagnostic.py`)는 frame.emit의 payload 소스로
그대로 유효. scenario/run 집계 CSV를 dataclass 스키마에서 자동 유도하는 것이 목표
(지금은 subalgorithm마다 reporter 메서드를 손으로 씀).

### 5.10 Analyzer 1급 시민 + study scope — frame의 분석 대칭 (2026-07-03 추가)

**현재 관행 (조사로 검증)**: 분석 스크립트 23개(ffc_dw_wET `scripts/`)가 flat하게
쌓이고 lifecycle 구분은 파일명 관례(밑줄 접두사=일회성, 날짜 접미사)뿐. ffc_cmax는
analyzer들이 아예 repo root에 있음. 산출물의 자리는 4갈래로 무정부 상태 —
① run 트리 안으로 역주입 (`process_logs.py`가 instance dir에 CSV/PNG 주입 — 실행
기록의 불변성 훼손), ② gitignore된 `analysis/` (기본 증발; 보존 가치가 생기면
`git add -f`가 사실상의 publish 메커니즘), ③ 커밋된 `analysis_outputs/` (150개
파일 중 재생성 가능한 것은 p1_algo_explainer뿐 — 생성기가 함께 없음), ④ CWD/repo
root (`dispatched_totals_by_instance.csv` 등 — "왕창"의 실체). run 위치는 전부
하드코딩 상수(frozen dataclass, DEFAULT_RUNS dict, 심지어 regex 안의 timestamp)라
대부분의 스크립트가 이미 inert. in-run과 standalone이 같은 분석의 두 코드 경로로
존재해 drift (`write_cp_gap_artifacts` vs `build_cp_gap_report.py`).

**설계**:

- **`analyzer_spec` 계약** (subalgorithm_spec의 분석 대칭 — 신규 kind):
  `name`, `attaches_to`(subalgorithm 이름 | root | artifact kind), `consumes`
  (kinds + scope: frame/instance/scenario/run/study), `produces`(report-zone/study
  산출 kinds), `code_ref`, `lifecycle`({in_run, standalone, study}).
- **한 정의, 모든 lifecycle**: in-run post-process와 `laadi analyze <run>`(사후
  재실행)이 **같은 함수**를 호출한다 — POST_PROCESS_ONLY는 이 성질의 특수형.
  일회성 조사 → 상시 분석으로의 graduation이 재작성이 아니라 spec 필드 변경이 된다
  (현재는 scripts/ → package 승격 시 재작성: `process_logs.py` → `log_processor.py`).
- **frame 질의 reader**: `run.frames(method="calc_mcf_lb...")` — instance/scenario
  경계를 넘어 해당 frame들과 그 emit 산출물·metrics를 순회. **root frame 분석
  (알고리즘 전체)과 subalgorithm 분석이 같은 기계** — 액자식의 이득.
- **산출물의 자리** (왕창 문제의 정면 해소):
  - run 트리 안 산출은 대응 scope의 **report zone에만**. final/progress로의 역주입
    금지를 계약 문구로 — run 트리는 실행의 불변 기록이다.
  - run 트리 밖 = **study scope 신설** (run/scenario/instance에 이은 실행-밖 좌표):
    `analyses/<ts>_<label>/`을 layout이 관리하고 **`study_manifest`**(생성 analyzer
    code_ref, 소비한 run_id들, 명령, laadi 버전)를 자동 스탬프. "생성기 없는 커밋
    산출물"과 "gitignore 강제-add publish" 문제 해소. 보존은 명시적 promote 단계로
    (기본: 대용량 데이터 ignore, manifest+writeup 추적).
  - run 참조는 경로 하드코딩 대신 run_manifest/registry 질의(§5.8) — study의 입력이
    재현 가능한 질의로 기록된다.
- **stdout-only 금지**: analyzer 결과는 항상 study/report 산출물로 남긴다 (현재
  cross-run 조사 3종이 터미널 스크롤백으로 증발).
- ffc_cmax의 **p1_algo_explainer 패턴** (demo instance에 subalgorithm을 직접 구동해
  단계 스냅샷 → 재생성 가능한 그림 빌드)은 study의 한 종류로 자연 수용 — frame
  기록이 남으므로 demo run 하나가 곧 설명 자료의 소스가 된다.

### 5.11 의존성·배포 정책

- core 런타임 의존성 최소: `jsonschema`, `referencing`, `pyyaml` 수준.
- **분석 시각화·pandas류는 `laadi[report]` optional extra** — `fm_prmu`가 subprocess
  테스트로 지키던 "solver-free zone"을 패키지 구조로 강제 (mbls가 matplotlib을 hard
  dep으로 가진 반례의 교훈). solver는 당연히 의존성에 없음 (adapter 플러그인 소관).
- Python ≥ 3.11, `py.typed` 동봉.

### 5.12 계산 실험 안정성 — step checkpoint·graceful shutdown (2026-07-09 추가)

장시간 계산이 비정상 종료(예외, SIGTERM preempt, SIGKILL/정전)되어도 **그때까지의
중간 schedule과 기록을 잃지 않는다.** 스텝 내 손실은 수용한다(긴 스텝은 알고리즘의
성질 — `incremental_pw_cp`류) — 목표는 granularity를 높이는 것이 아니라 **같은
granularity에서 확실히 잃지 않는 것**.

**현재 관행 (`ffc_cmax`, 조사로 검증 2026-07-09)** — 스텝 단위 checkpoint를 앱
레벨로 구현해 실전 운용 중:

| 있는 것 | 갭 |
| --- | --- |
| 최상위 flow 스텝 완료마다 incumbent schedule 전체 직렬화 (`_try_save_step_checkpoint`) | solution→obj_log→summary→metadata **비원자적 순차 기록** — 기록 도중 크래시 시 찢긴 checkpoint |
| checkpoint 파일 모양 = 최종 산출물과 동일 → checkpoint가 곧 resume 입력 (metadata 82개가 실전 소비) | **signal handler/atexit 전무** — SIGTERM(클러스터 preempt)에도 진행 중 스텝 전량 손실 |
| resume 시 `ResumeValidator`가 feasibility·obj 재검증 후 주입 | 첫 feasible incumbent 이전엔 **아무것도 안 남음** |
| `scripts/checkpoint_inventory.py`로 스텝별 best obj 조망 → resume 지점 선정 | 스텝이 예외로 죽으면 그 스텝 checkpoint 미기록; resume은 사람이 metadata를 작성하는 수동 절차 |

**설계** — 기록 측(1–5)과 복원 측(RESUME)을 분리한다:

1. **checkpoint = frame 경계의 자동 산출물**: root 직속 frame(=최상위 flow 스텝)이
   닫힐 때 step 러너가 현재 incumbent solution + `checkpoint_manifest`를 기록.
   solution은 기존 계약 kind 재사용(모양이 final과 동일 → checkpoint가 곧 resume·
   분석 입력 — `ffc_cmax` 관행의 승격), 경로는 **layout의 checkpoint scope/kind로만
   해석** (routix RESUME가 스키마 밖 "제3의 규약"을 하드코딩했던 결함의 재발 방지,
   §5.1). run_config에서 on/off·유지 개수(최신 N개) 지정.
2. **원자적 쓰기 규약 (전 아티팩트 공통)**: 데이터 아티팩트 writer는 temp 파일 +
   `os.replace`. checkpoint는 구성 파일을 다 쓴 뒤 **`checkpoint_manifest`를 맨
   마지막에** — manifest 없는 checkpoint 디렉터리는 reader가 없는 것으로 취급
   (§5.4 atomic-last 관행의 일반화). 찢긴 checkpoint가 구조적으로 소멸.
3. **trajectory의 crash-resilience를 계약 문구로**: JSONL writer는 레코드 단위
   append+flush. 스텝 중간에 SIGKILL이 와도 obj 궤적·frame_record는 마지막
   레코드까지 생존 — schedule 스냅샷은 스텝 granularity지만 "무슨 일이 있었는지"는
   레코드 단위로 남는다.
4. **graceful shutdown**: (2b)가 SIGTERM/SIGINT 핸들러를 설치 → stop_predicate가
   True를 반환하는 cooperative stop → subalgorithm이 다음 안전 지점에서 반환 →
   정상 종료 경로로 수렴해 checkpoint + manifest `status: interrupted` 기록. 2회째
   신호는 즉시 종료(escape hatch). 클러스터 preempt(SIGTERM 후 유예)가 "손실"이
   아니라 "짧은 stopping"이 된다. §5.4 실패 매트릭스에 반영.
5. **solution이 없어도 기록은 남는다**: manifest·frame_record·trajectory는 incumbent
   유무와 무관하게 모든 경로에서 기록 (§5.4) — "첫 feasible 이전 크래시 = 무기록"
   갭 해소. "solution 없음"과 "기록 없음"이 구분된다.
6. **checkpoint inventory는 analyzer로**: checkpoint 스캔 → 스텝별 best obj/bound
   표는 §5.10 analyzer_spec의 표준 동봉 analyzer로 제공 (`ffc_cmax`
   `checkpoint_inventory.py`의 흡수). resume 지점 선정·중간 경과 조망이 표준 기능이
   된다.

**RESUME과의 관계**: 복원 메커니즘(checkpoint 로드 → 상태 재구성 → flow prefix
검증)은 여전히 v1.x(§8)이나, **v1의 checkpoint가 resume의 유일한 입력이 되도록
모양을 v1에서 고정**한다. resume의 용례는 둘이며, 같은 메커니즘의 두 소비자다:

- ① **crash recovery** — 중단된 run의 마지막 checkpoint에서 복구 (`ffc_cmax` 관행).
- ② **prefix 분기** — **완주한** base run의 비싼 공통 prefix를 1회만 계산하고 여러
  tail 설정으로 fan-out (`ffc_dw_wET` c2657e0b 관행 — 공통 prefix가 시나리오 예산의
  ~40%라 7개 시나리오의 중복 계산을 제거). checkpoint 모양 설계는 두 용례를 모두
  지탱해야 한다.

검증 로직은 §5.7 objective evaluator를 재사용(로드 시 재계산 검증 —
`ResumeValidator` 관행의 승격. `ffc_dw_wET`가 manifest 스칼라를 무검증 신뢰한 것은
반면교사). 스텝보다 촘촘한 스냅샷(예: incumbent 갱신 시, diagnostic level 게이트)은
후속 검토 — 기본은 스텝 granularity.

---

## 6. 즉시 요구 구현: LLM step-by-step 가이드

### 6.1 캐노니컬 빌드 순서 (상태기계의 상태들)

`ffc_dw_wET`(20단계)·`fm_prmu`(14)·`ffc_cmax`(11)의 실제 구축 순서를 하나로 정규화:

| 단계 | 이름 | 산출물 | 완료 판정 (기계 검증) |
| --- | --- | --- | --- |
| S0 | scaffold | `laadi init`이 생성: 디렉터리 뼈대, AGENTS.md, 템플릿, config stub | init 마커 + 구조 존재 |
| S1 | problem 정의 | `docs/problems/<name>.md` + `specs/<name>.problem.json` | spec 스키마 통과, md 섹션 존재 |
| S2 | input data 준비 | `benchmarks/<family>/` 원시 파일 + `FORMAT.md` (+ instance 목록/메타 CSV) | 디렉터리·FORMAT.md 존재, run_config의 instance_selection이 해석 가능 |
| S3 | input data class | instance 프로토콜(`name`, `from_<format>(stream)`, JSON-safe) 구현 + 로더 | 프로토콜 적합성 검사 + 샘플 1개 파싱 테스트 |
| S4 | solution·objective | solution payload 표현 + objective evaluator (SSOT) | `objective_ref` 로드 가능, 왕복 직렬화 테스트 |
| S5 | subalgorithm | `docs/subalgorithms/<name>.md` + `specs/<name>.subalgorithm.json` + `code_ref` 구현(atomic) 또는 sub-flow 선언(composite, §5.3.1) | atomic: spec 통과 + code_ref import 가능 + 시그니처 적합 / composite: spec 통과 + child ref 전부 등록 + params 정합 + cycle 없음 |
| S6 | 실험 세팅 | `configs/<name>.yaml` (run_config) | strict 검증 + flow의 method가 전부 등록된 spec과 정합 |
| S7 | 스모크 실행 | 소수 instance로 `laadi run --smoke` | run 디렉터리가 계약 검증 통과 (manifest·trajectory 등) |
| S8 | 본 실행 + 분석 | full run → `open_run` / `laadi report` | aggregate_row 산출, report zone 생성 |

### 6.2 CLI 상태기계

- **`laadi init`** — S0 수행. 소비 저장소에 구조 + **AGENTS.md**(§6.3) + 템플릿 +
  config stub을 생성. 이미 있는 파일은 건드리지 않음(idempotent).
- **`laadi status`** — 저장소를 검사해 단계별 체크리스트와 **다음에 할 일**을 출력.
  각 단계의 완료 판정은 §6.1의 기계 검증 규칙. 출력은 사람도 LLM도 읽기 좋은
  체크리스트 형식 (+ `--json`).
- **`laadi validate`** — 존재하는 모든 정의(specs, configs, layout overlay)와
  선택적으로 run 디렉터리를 계약 검증. 실패 메시지는 "무엇을 어떻게 고치라"까지.
- **`laadi add subalgorithm|problem|experiment|analyzer <name>`** — 해당 단계의
  템플릿 쌍(md + spec stub)을 생성하고 다음 행동을 안내. `add analyzer <name>
  --for <subalgorithm>`은 analyzer_spec(§5.10) stub과 code_ref 골격을 생성.
  `add subalgorithm <name> --of a,b,c`는 선언형 composite(§5.3.1) spec stub
  (`steps: [a,b,c]`, code_ref 없음)을 생성 — 새 callable 없이 재사용 시퀀스를 정의.
- **`laadi analyze <run_dir|study질의> [--analyzer name]`** — 등록된 analyzer를
  기존 run(또는 study)에 실행. in-run post-process와 같은 코드 경로 (§5.10).

`status`가 상태기계의 심장이다: **상태는 별도 상태 파일이 아니라 저장소의 실제
내용물에서 유도**한다 (파일이 곧 상태 — 중간에 사람이 손대도 어긋나지 않음).

S1–S8은 최초 구축의 선형 경로이고, S5(subalgorithm)·S6(실험 세팅)·analyzer 추가는
이후 반복되는 **상시 작업 4종** — aladia AGENTS.md의 작업 3종에 "(4) analyzer 추가"가
더해진 것. AGENTS.md와 `laadi add`가 네 작업 모두를 커버한다.

### 6.3 scaffold되는 AGENTS.md

aladia AGENTS.md의 계승·확장판. 포함 내용:

- 세 관심사와 저장소 모양(§6.1의 디렉터리 규약), 불변식 I1–I6.
- S1–S8 각 단계의 레시피: 무엇을 만들고, 어떤 템플릿을 쓰고, 어떤 명령으로 검증하는지.
- "막히면 `laadi status`" — CLI와 문서가 같은 상태기계를 가리킴.
- 외부 저장소 결과 가져오기 (`open_run`) 사용법.

문서(AGENTS.md)와 CLI(status)는 **같은 단계 정의를 한 소스에서 공유**한다
(단계 정의를 laadi 패키지 내 데이터로 두고 둘 다 그것을 렌더).

### 6.4 v1 acceptance 시나리오 (확정된 검증 방식)

> 빈 저장소에서: `uv add laadi` → `laadi init` → LLM에게 toy 문제 서술과 함께
> "실험 코드베이스를 작성해"라고만 지시 → LLM이 AGENTS.md + `laadi status`만으로
> S1→S8을 완주 → 산출 run 디렉터리가 `laadi validate`를 통과하고, **다른 저장소에서**
> `open_run`으로 읽혀 aggregate가 나온다.

toy 문제 (제안): **단일 기계 총 가중 지연 (1‖ΣwjTj)** 또는 소형 순열 flowshop.
solver 의존성 없이 순수 Python으로 EDD/SPT constructive + pairwise-swap local
search 2~3개 subalgorithm이 나오는 크기. 인스턴스는 생성 스크립트로.
이 toy는 laadi 저장소의 `examples/`에 참조 구현으로도 동봉한다 (LLM이 만든 결과와
비교하는 기준선 + 문서 역할).

---

## 7. 패키지 구조 (v1)

```txt
laadi/
├── pyproject.toml            # deps: jsonschema, referencing, pyyaml / extra: [report]
│                             # [project.scripts] laadi = "laadi.cli:main"
├── AGENTS.md                 # laadi 저장소 자체 개발용 (소비 저장소용은 scaffold 데이터)
├── docs/                     # 설계 문서 (본 계획의 후속들)
├── src/laadi/
│   ├── contracts/            # JSON Schema SSOT (package data) + examples/
│   ├── schema.py             # kind 레지스트리, $ref 해석, validate/example
│   ├── layout.py             # 관심사 (1): layout 해석기, stamp/restore, 발견 API
│   ├── define/               # Define 층: run_config·spec 로더 (strict 검증 포함)
│   ├── run/                  # 관심사 (2): frame 트리·방출 API(emit/metric),
│   │                         #   step 러너(불변식 강제), runner 계층, RunMode,
│   │                         #   trajectory/frame_record writer
│   ├── analyze/              # 관심사 (3): open_run/RunReader, frames() 질의,
│   │                         #   analyzer registry·실행, study scope,
│   │                         #   aggregate, (extra) baseline join·RPDf·차트
│   ├── cli/                  # init/status/validate/add/run/report/contracts-export
│   └── scaffold/             # 소비 저장소에 심을 AGENTS.md·템플릿·단계 정의 데이터
├── examples/toy_smtwt/       # §6.4 toy 참조 구현
└── tests/                    # 계약 예제 왕복 + round-trip(config→run→read) +
                              #   설치 스모크 + 불변식 강제 테스트
```

모듈 경계가 관심사 경계와 일치한다: `analyze`는 `run`을 import하지 않고, 오직
`schema`/`layout`과 디스크만 본다 (import 방향을 테스트로 고정).

---

## 8. v1 범위

### 포함

- 계약 전체 세트 (§2.3 + run_manifest, baseline_table, **frame_record,
  analyzer_spec, study_manifest**) — 각각 예제·왕복 테스트·소비 코드 동반 (§3.3 원칙 1).
- 관심사 3개의 Python 구현: layout 해석기 / **frame 트리·방출 API(emit/metric,
  diagnostic level, 텍스트 전용 계약)**·step 러너·러너 계층(FULL_RUN,
  POST_PROCESS_ONLY, 실패 계약, 시나리오 중복 가드, per-instance 격리) /
  open_run·`frames()` 질의·aggregate·**analyzer 실행(`laadi analyze`, 단일 run)**.
- study scope 최소형: `analyses/<ts>_<label>/` 생성 + study_manifest 자동 스탬프.
  (registry 질의 기반 run 선택 고도화는 v1.x)
- **계산 실험 안정성의 기록 측 (§5.12)**: step checkpoint 자동 기록
  (+checkpoint_manifest), 원자적 쓰기 규약, trajectory 레코드 단위 flush,
  SIGTERM/SIGINT graceful shutdown, 동봉 checkpoint inventory analyzer.
  복원(RESUME) 없이도 "죽어도 잃지 않는다"는 가치가 독립 성립.
- 불변식 I1–I6의 기계 강제.
- CLI 상태기계 + scaffold (§6) 전체.
- toy 예제와 §6.4 acceptance의 자동화 가능한 부분 (계약 검증·cross-repo 읽기).
  toy에는 analyzer 1개 이상 포함 (subalgorithm 단위 분석의 참조 구현).

### 명시적 비목표 (v1)

- **RESUME 구현** — 복원 메커니즘은 v1.x (aladia처럼 "enum만 있는 상태"로 두지
  않도록, v1에서는 RunMode에서 아예 빼는 것도 검토). 단 §5.12의 checkpoint 기록이
  v1에 포함되므로 resume의 입력물은 v1 실행부터 쌓이고, checkpoint 모양이 곧 resume
  계약의 예약이다.
- C/C++/TS 등 실제 언어 교체, executor process 계약 — v2.
- ResourceMonitor — v1.x (아래 참고).
- mbls 후속(solver adapter)·schore 후속(domain 패키지) 제작 — seam만 제공.
- legacy routix 결과 트리 어댑터 — v1.x (마이그레이션과 함께).
- 컨트롤러 런타임 교체 추상화(routix의 fs_/tbb_/ga_ 복붙 문제의 일반해) — §5.3이
  상당 부분 해소하지만, 잔여 이슈는 v2.

---

## 9. 로드맵

### v1 — "uv add laadi로 LLM이 실험 코드베이스를 만든다" (본 계획)

작업 순서 (TDD 슬라이스, 각 슬라이스는 round-trip 테스트로 닫음):

1. contracts + schema.py + 패키징 (설치 스모크 포함)
2. layout (해석기·stamp·발견 API)
3. run: frame 트리·방출 API → step 러너(불변식 강제, step checkpoint §5.12) →
   single → multi(+concurrent, 실패 계약) → scenario — **run_config 로더가 처음부터
   러너를 구동** (aladia 실패의 정면 교정). 원자적 writer·graceful shutdown은 이
   슬라이스의 기반 유틸로 먼저 착지
4. analyze: open_run → frames() 질의 → aggregate → analyzer 실행·study 스탬프 →
   (extra) baseline/RPDf
5. CLI + scaffold + AGENTS.md
6. toy 예제 (analyzer 포함) → §6.4 acceptance (LLM 실주행)

### v1.x — 실전 흡수

- **`ffc_dw_wET_2026` 마이그레이션** (확정된 단계적 검증). 선행: legacy routix
  layout 어댑터 → laadi.analyze가 기존 run 트리를 읽는 것부터 (위험 최소 진입).
- RESUME (세 저장소의 ~350 LOC×3에서 복원 상태 목록 추출: incumbent, obj-trace,
  가상 타이머, flow prefix 검증). 입력은 v1의 checkpoint (§5.12). 실전 검증본 둘 —
  `ffc_cmax`의 checkpoint→ResumeValidator→주입 파이프라인(crash recovery)과
  `ffc_dw_wET` c2657e0b의 prefix-분기 resume. 후자에서 채택할 기법:
  - **시계 back-dating**: `timer.set_start_time(now − 실측 prefix elapsed)` —
    timelimit 표현식(`"5nc"`류)·정지조건 코드를 무변경 재사용. 과금은 명목 예산이
    아니라 manifest의 **실측** elapsed로 (주의: base와 다른 하드웨어면 tail 예산
    왜곡 — 계약에 명기할 것).
  - **obj-trace를 절대 timestamp 키로 병합**: resume 경계를 넘는 궤적 연속성
    (back-dating 덕에 rescaling 불필요; 세그먼트는 call index가 아니라 timestamp로).
  - **checkpoint 모양의 SSOT 분할 명시**: 스케줄 ← solution 아티팩트, 전역 LB·obj
    스칼라 ← manifest (solution의 bound는 보통 없음).
  - **prefix 안전 감사 + 재실행 훅**: "tail이 소비하는 prefix 상태 = incumbent+LB
    뿐"인지 명시 감사하고, 초과분이 있으면 재실행할 스텝을 지정하는 훅
    (`method_names_to_run_before_resume`류).
- **ResourceMonitor**: `docs/20260528_resource_monitor.md`의 설계를 laadi (2b)로
  이식. 시계열은 별도 저장소가 아니라 **trajectory 계약의 `resource/*` series로
  방출** (계약 재사용), peak 통계는 manifest에. timelimit enforce 정책 질문은 그
  문서의 §5 그대로 계승.
- solver adapter 가이드 문서 (mbls의 교훈: 타임스탬프 shift 책임, 콜백 배선,
  Protocol로 계약 명시).

### v2 — 언어 교체

- (2b)→(2a) executor process 계약: 실행 파일 invocation 규약 (인자로 run_config·
  layout·좌표 전달, 종료 코드, 아티팩트는 계약대로 기록). C/C++ toy executor PoC.
- (3) TS/JS reader PoC (contracts export 소비).
- (1) 타 언어 layout 해석기는 필요가 생길 때 (스키마가 언어중립이므로 자연히 가능).

---

## 10. 미해결 질문 — 결정 (2026-07-06)

8번을 제외하고 전부 결정됨 (요약: §0.1). 원 질문과 결정 근거를 함께 기록한다.

1. **subalgorithm 실행 모델의 최종형** (§5.3): **context-callable로 확정.**
   판단 기준(사용자 지정) = "Sonnet 4.5급 LLM이 작성하기 좋은 형태". 두 안의 비교:
   - **작업이 새 파일+새 함수로 국소화**: subclass 방식은 이미 존재하는 (커질수록
     거대한) 클래스 파일을 열어 메서드를 삽입해야 함 — 잘못된 위치 삽입, 기존 메서드
     훼손, 대형 파일의 컨텍스트 부담 등 중급 LLM의 대표 실수 클래스가 그대로 노출.
     callable 방식은 `laadi add subalgorithm`이 새 파일을 생성하는 것으로 끝나
     idempotent하고 충돌이 없음.
   - **완료 판정의 기계 검증**: Protocol 시그니처 적합성은 validator가 검사 가능
     (P4 — "정해진 모양을 정해진 자리에"). subclass의 올바름(super 호출, self 상태
     초기화 순서, 메서드 간 암묵 호출 규약)은 정적 검증이 어려워 S5 단계의 완료
     판정(§6.1)이 약해짐.
   - **암묵 상태 제거**: controller 인스턴스 변수는 어디서 초기화되고 누가 읽는지
     클래스 전체를 읽어야 알 수 있음. context의 명시적 state 슬롯은 국소적으로
     추적 가능 — 코드베이스 전체를 읽지 않고 작업하는 LLM 시나리오에서 결정적.
   - **테스트 용이**: callable은 context fake 하나로 단위 테스트. subclass는
     controller 기동이 필요해 LLM이 테스트를 생략하거나 통합 테스트로 도피하기 쉬움.
   - **(2a) 언어 교체성과의 정합**: "불투명 code_ref가 가리키는 callable"은 v2의
     비-Python executor와 자연스럽게 정합. bound method는 Python 클래스 의미론을
     경계에 새김.
   - subclass의 장점(상태 공유 인체공학, IDE 탐색성)은 사람 개발자용 이점이라 이번
     판단 기준에서는 비중이 낮음. 상태 공유는 context state 슬롯이 흡수.
   → §5.3의 스파이크 단서 해제. 잔여 스파이크 필요성은 8번에만 남음.
2. **stopping criteria 스키마 범위**: per-instance timelimit **표현식은 표준 필드로
   필수 채택** (`"5nc"`, `timelimit_n_by_m_multiplier`류). 표현식 문법과 평가 규칙의
   구체 설계는 laadi 저장소에서.
3. **분석 v1 산출물의 선**: 제안 절단선 그대로 확정 — core = aggregate_row +
   scenario statistics + analyzer 실행기 / `[report]` extra = RPDf·차트 / 렌더러는
   도메인 무관(trajectory 라인차트)만 laadi, gantt류는 도메인 모듈 소관.
4. **이름·PyPI**: `laadi` 유지. **PyPI 선점은 하지 않음** — 공개 시점에 이름이
   선점되어 있으면 그때 개명.
5. **문서 언어 정책**: **전부 영어** (계약, README, AGENTS.md, 설계 문서 포함).
   한국어로 질문하면 LLM이 한국어로 답하므로 원문이 영어여도 사용성 손실 없음.
6. **routix 병행 유지보수 범위**: 검증된 버그를 routix에서 수정 — **완료
   (2026-07-06)**: ① `SingleInstanceRunner.run`의 `finally: return` 예외 삼킴 제거
   (예외 전파, 실패 시 post_run_process 미호출; 실패 기록용 **`on_run_error` 훅 신설**
   — 기본 no-op, 훅 자체의 예외는 로그만 남기고 원 예외를 가리지 않음 — laadi §5.4
   실패 계약의 routix 축소판. sequential MultiInstanceRunner의
   기존 per-instance 격리가 이 수정으로 비로소 작동), ② `MultiInstanceConcurrentRunner`
   에 per-instance 예외 격리(실패 instance는 로그+None, pool·시나리오 유지),
   ③ pyyaml runtime 의존성 선언. 테스트 `tests/test_runner_failure.py`,
   `tests/test_packaging.py` 동반. layout 미배선·문서 drift는 laadi에서 해소.
7. **frame 방출물의 크기 정책** (§5.9): 제안대로 확정 — v1은 무제한 + 크기 관측
   (frame_record에 bytes 기록), 상한/샘플링/압축은 데이터가 쌓인 뒤 결정.
8. **frame과 (2a) 알고리즘 계약의 접점** — **미해결 (유일한 잔여 질문)**:
   routix-free 알고리즘층(AlgSpec→AlgRecord) 내부의 단계도 frame으로 잡으려면
   stop_predicate처럼 frame 핸들(또는 방출 콜백)을 AlgSpec에 주입해야 함 —
   알고리즘층의 framework-free 원칙(ffc_dw_wET algorithm-principles.md 18규칙)과의
   균형. 1번이 context-callable로 확정되어 질문은 "context가 제공하는 frame 기능을
   (2a) 심층까지 어떻게 전달하나"로 좁혀짐 — laadi 저장소에서 스파이크로 결정.

---

## 부록 A. 근거 요약 — 세 실험 저장소의 진화

| | `fm_prmu_sumTj` (초기) | `ffc_cmax` (중기) | `ffc_dw_wET` (최신·정본) |
| --- | --- | --- | --- |
| 폴더 정의 (1) | 수작업 경로 + 상수 파일 3곳 분산 | 동일 + glob 하드코딩 | **ArtifactLayout YAML overlay (35 kinds) + stamp** |
| 알고리즘 층 (2a) | controller 메서드 (러너 3벌 복붙) | **17,358줄 god-controller** | **routix-free AlgSpec→AlgRecord 계약** |
| 분석 (3) | dashboards/를 subprocess 테스트로 solver-free 강제 | 러너 메서드에 분석 ~1,400줄 유착 | report/ zone + POST_PROCESS_ONLY |
| 사용 패키지 | routix+mbls+schore | routix+mbls+schore | **routix 단독** (의도에 부합) |

## 부록 B. mbls / schore 경계 메모

- **mbls** (CP-SAT adapter): 호스트들이 실제로 소비하는 것은 CustomCpModel의 LNS
  기계(제약 롤백), 콜백 recorder, status enum, obj-trace store. 제공된 solve
  파이프라인은 양 호스트가 ~200줄씩 fork(경직성) — adapter 계약을 Protocol로 명시할
  것과 타임스탬프 기준 책임을 계약에 적을 것의 근거. painter(matplotlib)가 hard
  dep인 것은 (2)/(3) 유착의 반례.
- **schore** (domain 데이터): routix와 코드 결합 zero — 경계 모델로서 건강.
  단 np.int64→int 캐스팅 등 직렬화 관심사가 domain에 새어 들어감 → Laadi가
  직렬화 경계에서 흡수. 미래의 schore-like 패키지는 instance 프로토콜(§4)만
  맞추면 laadi에 꽂힌다.
