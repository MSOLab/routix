# ccdeJava 검토 — laadi 계획 대조

작성일: 2026-07-03
상태: 조사 완료 — `docs/20260702_laadi_plan.md`의 보조 문서 (계획 반영 제안 포함, §10 미해결질문에는 답하지 않음)

대상: `/home/hjt/code/ccdeJava` — POSCO SCM cast 편성(연주 편성) 문제. Java+CPLEX,
Maven 멀티모듈 + 별도 uv 프로젝트 `python_scripts/`.
사용자 맥락: **알고리즘 정의 ↔ 실험 실행 분리**의 또 다른 선행 사례이며, **실험 실행 ↔
분석 분리**도 Java(실행)/Python(분석) 언어 경계로 "어쩔 수 없이" 이루어진 사례.
단 실행→분석이 한 번에 이어지지 않는 불편이 있었음.

방법: opus 서브에이전트 2개가 2026-07-03에 코드를 직접 읽고 수집 (① `c7b01b-local-runner`
중심 Java 측, ② `python_scripts/` 측 + Java 대응물 grep 교차확인). 아래 file:line 근거는
그 조사 결과이며 경로는 ccdeJava 저장소 기준.

---

## 0. 요약

- ccdeJava는 laadi가 지향하는 경계의 **원시형**이다. 알고리즘(`c7b01b-feature`) ↔
  실행(`c7b01b-local-runner`)은 단방향 모듈 의존으로, 실행(Java) ↔ 분석(Python)은
  **디스크 CSV만이 경계**로 분리되어 있다. P1("파일만이 경계")의 *위치*는 옳게 잡았다.
- 실패한 것은 경계의 **계약**이다. 경로·파일명·컬럼명·셀 특수값이 전부 언어별 코드
  상수/날 리터럴로 2~4중 유지되고 기계가 읽는 SSOT가 없다. 그 결과 (a) **drift가 실제로
  발생**했고(§3.1 — 지금 분석이 도는 건 "쓰는 항목이 마침 안 갈린" 운), (b) 실행→분석
  연결이 "사람이 timestamp를 눈으로 보고 소스에 붙여넣는" 수동 단계로 단절되며,
  (c) 분석 산출은 콘솔/클립보드로 증발한다. **laadi 계획의 P1~P4와 §5.8~5.10을 통째로
  실증하는 표본.**
- 계획서에 새로 넣을 것 8건(§4 표): 검증형 analyzer의 표준 verdict+위반 아티팩트(P-3),
  외부(수동/AsIs) 해 수입 경로(P-4), per-instance 설정 동결 불변식(P-2), 인코딩 계약
  조항(P-5), 값 어휘(enum)의 계약 포함 명시(P-6), 기계 키/표시명 분리(P-8, §10-5 연계),
  per-instance override 선례 각주(P-7, §10-2 원자료), 출처 목록 추가(P-1).

---

## 1. ccdeJava가 시도한 분리 — 구조

```txt
┌── c7b01b-feature (알고리즘 정의 ≈ laadi 2a) ──┐   ┌── c7b01b-local-runner (실험 실행 ≈ 2b) ──┐
│ SingleCastDesigner(2,000+줄 MIP 파이프라인)   │   │ SingleCastMaker / MultiCastMaker /        │
│ MultiCastDesigner(2,800+줄, cast마다          │◄──│ JobCastMaker / BenchmarkSingleCastRunner  │
│   SingleCastDesigner 재생성 = 재귀 구성)       │의존│ + CsvBatchAnalyzer,                       │
│ alg/model(CPLEX), handler/, io/dflib(~29      │   │   *IntegrityChecker (각자 별도 main)      │
│   테이블), option/, param/(컬럼 상수)          │   └───────────────────────────────────────────┘
└───────────────────────────────────────────────┘        (c7b01b-store: 로거 등 공통 유틸)
   경계 API = BaseCastDesignOption(~30 setter) + `DataFrame makeSingleCast(SummaryHandler)`
              — 컴파일타임 Java 타입 계약. 스키마 아님.

 실행 산출: bin/castDesign/<runner>/outputdata/<worksCode>_<jikbun>_<ts>/<runTimestamp>/
            _result1..9_*.csv + <runTimestamp>_SingleSummary.csv + .log
        │
        ▼  ═══ 자동 연결 전무: 사람이 timestamp를 눈으로 확인해 .py 소스에 붙여넣음 ═══
 python_scripts/ (분석 ≈ laadi 3, 별도 uv 프로젝트, orchestrator 없음 — main.py는 스텁)
   cast_painter.py(1,992줄 도식 PNG) · summary_generator.py(집계→클립보드/콘솔) ·
   manual_cast_feasibility.py(수동 편성 검증 CLI) · split_by_plan_cast_no.py
   ← param/ 컬럼·특수값 상수를 Java param/과 **각각 손으로 이중 유지**
```

- (2a)↔(2b) 경계의 실체: 러너가 Option 객체를 조립해 Designer를 호출하고
  SummaryHandler로 결과 행을 수집 (`SingleCastMaker.java:138-211`). 단방향 의존
  (runner→feature), 알고리즘은 러너를 모름 — **모듈 경계 자체는 건강**.
- 실제 데이터 교환(입력 13+기준 11 CSV, 출력 result1~9 CSV, 컬럼명)은 Option의 경로
  문자열 + `AutoCastDesignInfo` 파일명 상수 + `*ColLabel` 컬럼 상수라는 **암묵 규약**으로
  매개. JSON Schema류 SSOT 없음.
- (2)↔(3) 경계: Java·shell 어디에도 python 호출 없음(grep 확인). 분석 스크립트는 경로를
  소스에 하드코딩 (`cast_painter.py:23` — prefix·timestamp까지 통째로;
  `summary_generator.py:9-14` — `D:/data/...` Windows 절대경로 + 변수 재대입 토글).

한 줄 평가: **경계의 위치는 laadi와 동형, 경계의 계약이 부재** — laadi가 "계약을 기계가
읽는 SSOT로" 만들려는 이유가 이 저장소의 통증 전부와 1:1 대응한다.

---

## 2. laadi에 가져갈 좋은 점

각 항목: 무엇(근거) → 계획 현황 → 제안.

### 2.1 실패를 1급 레코드로 — finally에서 반드시 Summary 행 append

`SingleCastDesigner`는 실패해도 `runSummary`에 `완료=false`+`ErrMsg`를 담아 **finally에서
반드시 Summary CSV에 한 행을 append**한다 (`SingleCastDesigner.java:213,468-486`). 하류
집계는 `완료=="O"` 필터로 성공만 취한다 (`CsvBatchAnalyzer.java:120`). 실패가 "파일 부재"가
아니라 상태 컬럼이 있는 행으로 남는다.

→ 계획 §5.4의 "manifest는 모든 경로에서 반드시 쓰인다"·`status: error/stopped`와 정확히
같은 사상. **변경 불요, 실증 근거로 추가.** (atomic-last manifest의 Java 선례)

### 2.2 검증 위반을 조사 가능한 산출물로 — pass/fail이 아니라 "무엇이 왜"

`CastResultIntegrityChecker`는 중량/폭 범위 위반 시 콘솔 ❌뿐 아니라 **위반 행 자체를
`<name>_VslabsViolatingWeightRange.csv`로 저장**한다 (`CastResultIntegrityChecker.java:198-246`).
검사 항목도 실질적: cast 내 유일성, chSeq 연속성, 용강 혼합 가능성, strand 대칭, 범위.

→ 계획 §6.2 `laadi validate`는 계약(스키마) 검증이고, 이런 **도메인 무결성(해의 실행가능성)
검증**은 §5.7(objective 재계산)에 인접하나 더 넓다. ccdeJava에는 이 검증기가 **3벌 중복**
(Java 인스턴스/배치 checker + Python `manual_cast_feasibility.py`) — 반복 발생하는 실수요라는
증거. **제안 P-3**: §5.10에 "검증형 analyzer" 관례 추가 — analyzer가 ① 기계판독 verdict
(JSON + 종료코드) ② 위반 레코드 아티팩트를 report/study zone에 남기는 표준 형태. 도메인
검사 로직은 도메인 모듈 소관, laadi는 verdict 봉투·자리만 규정. (BatchResultIntegrityChecker가
검사 on/off를 `static final boolean`으로 게이팅하는 것(`:19-22`)의 교정 = analyzer
config/diagnostic level.)

### 2.3 `manual_cast_feasibility.py` — 분석 스크립트의 모범형

유일하게 argparse CLI(`:190-199`), 파일 상단 docstring이 검사 항목·**입력별 인코딩**·사용법·
종료코드를 계약처럼 명시(`:1-23`), 판정을 **종료코드 0/1**로 기계에 노출(`:205`), 소비 컬럼을
상단 상수로 격리(`:34-48`). 나머지 스크립트(하드코딩·콘솔 증발)와 질적으로 다르다.

→ **analyzer_spec(§5.10)의 실전 원형.** 계획이 이미 포괄하나 두 요소를 명시적으로 흡수:
① verdict의 종료코드 노출(P-3에 포함), ② 입력 인코딩의 계약화(P-5).

### 2.4 변동부만 YAML로 + 로드 시 필수 키 즉시 검증 + per-instance override

`BenchmarkArguments`/`SingleCastArguments`는 SnakeYAML 로드 직후 필수 키 부재를 즉시
검증한다 (`BenchmarkArguments.java:62-88`, `SingleCastArguments.java:49-55`). 벤치마크 YAML은
`instanceIdList` + **`instanceIdToArgsMap`(인스턴스별 인자 재정의)**를 가진다.

→ run_config strict 검증(§2.3, P2)과 동일 사상 — 변경 불요. 단 **per-instance override
슬롯은 계획에 없다**: run_config는 `instance_selection`까지만. 인스턴스별 파라미터(강제
charge수, per-instance timelimit)는 ccdeJava와 세 실험 저장소(§10-2의 `"5nc"` 표현식)에서
반복되는 실수요. **제안 P-7**: 결정은 §10-2에서 하되, `instanceIdToArgsMap` 선례를 §10-2에
원자료로 각주.

### 2.5 외부(수동/AsIs) 해를 같은 검증·분석 기계에 태우기

`BatchResultIntegrityChecker`는 러너 출력이 아니라 **수동 수집한 현업(AsIs) 결과**
(`bin/castDesign/result/AsIs/...`, `:40`)를 검증하고, `manual_cast_feasibility.py`는 사람이
짠 편성안을 검증하며, `split_by_plan_cast_no.py`는 AsIs 결과를 인스턴스별로 쪼갠다. 즉
**분석·검증 대상이 laadi가 실행한 run만이 아니다** — 알고리즘 해 vs 사람/타 시스템 해
비교는 이 도메인의 상시 업무다.

→ 계획의 `baseline_table`(§5.8)은 **스칼라 참조값**(BKS/LB)만 다룬다. **제안 P-4**: 외부
해를 `solution` 계약 봉투로 **수입(import)**해 동일 analyzer·검증형 analyzer를 적용하는
경로를 v1.x 로드맵에 추가 (예: `laadi import-solution` 또는 study 입력으로 외부 아티팩트
등록). v1 범위는 불변, baseline_table 항목에 "스칼라 한정, 해 수준 비교는 v1.x" 주석만.

### 2.6 인코딩을 계약에

Summary CSV는 Excel/한글 호환을 위해 **UTF-8 BOM을 손으로 기록**하고
(`SingleCastSummaryHandler.java:68-72`, `CsvBatchAnalyzer.java:190-198`), 입력별 인코딩은
구전 지식이다 (`manual_cast_feasibility.py:14`: OrderList=utf-8-sig, VslabList·수동결과=cp949).

→ 계획에 인코딩 조항이 없다. **제안 P-5**: 계약 공통 조항으로 ① laadi 산출 아티팩트는
UTF-8 고정(JSON/JSONL), ② CSV(aggregate 등)의 utf-8-sig 여부는 1회 결정해 계약에 명시
(Excel/한글 소비자 실존 — ccdeJava·세 저장소 공통), ③ 외부 입력 데이터의 인코딩은 instance
데이터 계약/FORMAT.md의 명시 필드로.

### 2.7 아티팩트 파일명 중앙 상수화 — 그리고 그 한계

Java는 산출 파일 suffix를 `AutoCastDesignInfo` 한 곳에 상수화했다 (`:156-181` —
`_result9_CastResult.csv` 등). 방향은 옳았으나 **Java 상수는 언어 경계를 못 넘는다**:
Python `cast_painter.py`는 같은 토큰을 독립 리터럴로 match하고(`:120-186`) 관련 파일을
`str.replace("8_CastDesignData","9_CastResult")` 체인으로 유도한다(`:141-144`). suffix가
바뀌면 예외 없이 "Skipping file..."로 **조용히 그림만 안 나온다**(`:189`).

→ layout 계약(§5.1)이 정확히 이것의 해답 — 언어중립 스키마 데이터 + manifest artifacts
색인(§2.3, reader가 glob·문자열 유도를 하지 않게). **변경 불요, P1의 최상급 실증 근거.**

---

## 3. laadi 계획 결정을 실증하는 통증 (근거 보강, 계획 변경 불요)

### 3.1 SSOT 부재 → drift는 가설이 아니라 실측

계약 어휘가 언어별로 손 유지되다 **이미 갈라졌다**:

| 항목 | Python (`python_scripts/param/`) | Java (`feature/.../param/`) |
| --- | --- | --- |
| 초/말/±1 주편 flag | `"초주편"/"말주편"/"초+1주편"/"말-1주편"` (special_row_value.py:17-20) | `"C"/"D"/"G"/"H"` (SpecialRowValue.java:50-56) |
| not_check / in·not-in | `"Not Check"`, `"In"/"Not In"` | `"NOT_CHECK"`, `"IN"/"NOT_IN"` |
| true 값 집합 | `{"1","TRUE"}` | `{"1","TRUE","Y"}` |
| 구간 연산자 | `"<  a <"` (공백 2개) | `"< A <"` |
| 폭 계열 컬럼 | 옛 이름 `standardWthMinByInputs` (extra_col_label.py:31) | 개명된 `baseHrWthMinByInputs` (ExtraColLabel.java:72) |

cast_painter가 실제 소비하는 부분집합(`johap_str="1A"`, `mixed_str="1D"`, `"*"`,
`tight*` 계열)만 우연히 일치해 지금 그림이 나온다. **강제 동기화 메커니즘 zero.**
Summary 컬럼은 더 심함: `"SD_주편사용제한여재중량(ton)"` 같은 한글 리터럴이 Java 산출부
(`CastDesignHandler.java:2374`) + Java 헤더 정의(`SingleCastSummaryHandler.java:42`, 57컬럼
positional) + Java 집계기(`CsvBatchAnalyzer.java:19-34`) + Python 소비부
(`summary_generator.py:44-93`)의 **3~4곳에 복제**, `param/`에도 없음. `Map` put 키 오타는
조용히 빈 셀이 된다. → P1·P4, 계약 인벤토리(§2.3)의 직접 실증.

### 3.2 통증 → 계획 조항 대응표

| ccdeJava 통증 (근거) | 해소하는 laadi 조항 |
| --- | --- |
| 실행 전체 파라미터가 어디에도 직렬화 안 됨 — 재현하려면 소스 하드코딩+로그 텍스트를 봐야 (MultiCastMaker.java:23-54는 아예 `static final`) | run_manifest + config 사본/해시 (§5.8) |
| 단계 타이밍(`"*** X sec for WthCandid ***"`)·재시도 사유(`targetChCnt` 감소 log.warn:440,463)가 **로그로만** 존재 | "로그는 사람용"(§3.3-4), trajectory `context`(§5.2), frame_record(§5.9) |
| `MultiCastDesigner`가 cast마다 `SingleCastDesigner` 재생성(:531,885) — 알고리즘 안의 알고리즘; retry 루프의 각 시도는 기록 좌표가 없음 | **액자(frame) 모델의 실전 선례** (§5.9) — Multi=부모 frame, cast·retry 시도=자식 frame |
| 분석 산출이 클립보드/콘솔로 증발 (`summary_generator.py:31-32` `to_clipboard()`; feasibility 판정도 print만) | stdout-only 금지, report/study zone (§5.10) |
| PNG를 소스 결과 폴더에 역주입 (`cast_painter.py:40` `output_dir=ins_dir`) | run 트리 불변·report zone 강제 (§5.10) |
| run 참조가 소스 재대입 토글 (`summary_generator.py:10-13` 이중 대입) + prefix·timestamp 하드코딩 + CWD 의존 | run_manifest/registry 질의 (§5.8, §5.10) |
| 파라미터 스윕 = 주석 토글 (BenchmarkSingleCastRunner.java:90-194, 12블록 중 11개 주석) | run_config `scenarios[]` (§2.3) |
| 러너 4종의 설정 방식 제각각(YAML 2종/하드코딩 2종), `setOptionByWorksCode` 동일 본문 3벌, JobCastMaker ≈ MultiCastMaker 90% 클론 | 프레임워크가 러너 계층·step 템플릿 소유 (§2.5, §5.3) — routix 호스트 "러너 3벌 복붙"의 Java판 |
| 라이브러리 심층 `System.exit(1)` (BaseCastDesignOption.java:212-226) | 실패 계약 (§5.4) |
| `getLogFilePath`가 result CSV를 씀; 로그 위치가 러너마다 제각각 | layout 유일 경로 권위 (§5.1) |
| 분석이 실행 미기록 데이터를 **엔진 재구현으로 복원** — `util/weight_calculator.get_charge_cnt_ub`(MST+포함배제)가 Java `ChargeCountCalculator`와 병렬 구현, 산출은 print뿐 | "의심되면 기록한다" frame.emit/metric (§5.9) — ffc_dw_wET의 "CSR obj 미기록→재실행"과 동일 병 |
| RESUME·체크포인트 전무, 매 실행 전량 재계산 | RESUME 로드맵 (§9 v1.x) — 신규 정보 없음 |
| 인스턴스 루프가 **하나의 Option 객체를 mutate 재사용**, 일부 필드 리셋 누락 (BenchmarkSingleCastRunner.java:245-267) | **계획에 명시 조항 없음 → 제안 P-2** |
| orchestrator 부재 — 어떤 분석을 어떤 순서로 돌리는지 구전 (main.py 스텁, README 빈 파일) | analyzer registry·`laadi analyze`(§5.10), CLI 상태기계(§6) |

확인 항목(변경 불요): per-instance try/catch 격리(BenchmarkSingleCastRunner.java:269-273 —
한 인스턴스 실패에도 배치 계속 = §5.4와 동일), 실행별 timestamp 격리 디렉터리
(SingleCastMaker.java:117 = layout run scope의 선례), Benchmark가 SingleCastMaker 로직을
재사용하는 층 구조(= §2.2 SRP bottom-up의 배아).

---

## 4. 계획서 반영 제안 요약

반영 = `20260702_laadi_plan.md` 편집 제안. 결정 필요 표시는 사용자 판단 대기.

| # | 계획서 위치 | 제안 | 근거 |
| --- | --- | --- | --- |
| P-1 | 머리말 "관련 자료" + 부록 A | ccdeJava를 검증된 출처로 추가 (routix 이전의 Java 산업 사례, 계보 0번째 데이터 포인트; 본 문서 링크) | 본 문서 전체 |
| P-2 | §2.4 불변식 | **I7 신설**: "인스턴스 실행에 주어지는 설정은 진입 시점에 동결된 불변 스냅샷 — 러너의 공유 가변 설정 객체 재사용 금지" | Benchmark의 option mutate 상태 누출 (§3.2) |
| P-3 | §5.10 | **검증형 analyzer 관례**: verdict(기계판독 JSON + 종료코드) + 위반 레코드 아티팩트를 report/study zone에 남기는 표준형. 검사 on/off는 소스 플래그가 아니라 analyzer config | 무결성 검사기 3벌 중복, 위반 CSV 저장 관행 (§2.2, §2.3) |
| P-4 | §5.8 + §9 v1.x | **외부 해 수입**: 수동/AsIs/타 시스템 해를 solution 봉투로 import해 동일 analyzer 적용 (v1.x). baseline_table에 "스칼라 한정" 주석 | AsIs 검증·분할 도구 3종 (§2.5) |
| P-5 | §2.1 인근 계약 공통 조항 | **인코딩 조항**: 산출 UTF-8 고정, CSV의 utf-8-sig 여부 1회 결정·명시, 외부 입력 인코딩은 명시 필드 (**결정 필요**: -sig 채택 여부) | BOM 수동 기록, cp949 구전 (§2.6) |
| P-6 | §2.3 + §5.9 승격 문구 | 계약 요소에 **값 어휘(enum·특수값) 포함**을 명시 — payload를 domain 계약으로 승격할 때 셀 값 enum까지 스키마화 | SpecialRowValue 실측 drift (§3.1) |
| P-7 | §10-2 각주 | per-instance override 선례 `instanceIdToArgsMap` 기록 (결정은 §10-2에서) | §2.4 |
| P-8 | §10-5 인근 (신규 소질문) | **기계 키 vs 표시명 분리**: 계약 필드·컬럼 키는 안정 ASCII, 한글 표시명은 분석층 표시 사전/스키마 `title` 메타데이터로 (**결정 필요**) | 한글 컬럼 리터럴 3~4곳 복제 (§3.1) |

계획 변경 없이 **근거만 보강**되는 항목: P1·P4(§3.1), run_manifest(§3.2-1), trajectory/
frame_record(§3.2-2·3), report/study zone·stdout 금지(§3.2-4·5), registry 질의(§3.2-6),
scenarios[](§3.2-7), 러너 계층·step 템플릿(§3.2-8), 실패 계약(§3.2-9), layout(§3.2-10),
frame.emit(§3.2-11), manifest 필수 기록(§2.1).

---

## 5. 미해결질문(§10) 관련 원자료 — 답하지 않음

- **§10-2 (stopping/per-instance 표현)**: `instanceIdToArgsMap`(인스턴스별 인자 재정의)이
  Java 쪽에서도 실수요였다는 선례. per-instance 강제 charge수(`userChCnt`)를 벤치마크
  YAML로 주입했다.
- **§10-3 (분석 v1 산출물의 선)**: `cast_painter.py`(1,992줄 편성 도식)는 "gantt류 도메인
  렌더러는 도메인 모듈 소관" 안을 뒷받침하는 실례. 추가 관찰 — 렌더러는 도메인 **계산**
  (단위 환산, 무게: `util/unit_converter.py`, `weight_calculator.py`)에도 의존한다. 즉
  도메인 모듈은 (2a)뿐 아니라 (3)에도 계산을 제공하는 위치이며(§4 seam과 정합), v2 언어
  교체 시 이 계산의 이중 구현(ccdeJava에서 실제 발생)이 재발할 수 있음을 §9 v2 논의에
  기록해 둘 가치.
- **§10-5 (문서 언어 정책)**: 한글 식별자가 데이터 계약(컬럼명)에 직접 들어가면 복제·
  인코딩 비용이 커진다는 실측 사례 → P-8(기계 키/표시명 분리)과 함께 결정.

## 6. 결론

ccdeJava는 laadi의 반면교사이자 선행 실증이다: **경계를 자를 자리는 이미 옳게 알고
있었고**(모듈·언어·디스크), 그 경계 위에 기계가 읽는 계약을 놓지 않으면 어떤 비용이
발생하는지(실측 drift, 수동 핸드오프, 산출물 증발, 엔진 재구현)를 한 저장소 안에서 전부
보여준다. 계획의 방향을 바꿀 발견은 없었고, 계획을 보강할 8건(P-1~P-8)과 다수의 실증
근거를 얻었다.
