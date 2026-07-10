# gbrain 조사 + "요구사항 우선 신규 repo" 구상 검토

- 작성: 2026-07-10, Claude (opus 서브에이전트로 gbrain 저장소 실사 후 종합)
- 상태: **보정 1·2·3 사용자 동의 (2026-07-10)** — `AGENTS.md` 타임라인에 기록됨.
  잔여: 이름 최종 선정(기준 변경으로 §4 갱신 — 아래 참조) + repo 생성 착수 시점.
- 검토 대상 구상 (사용자 제안, 2026-07-10):
  1. 새 repo를 만들어 **gbrain 중심으로 requirement를 전부 먼저 수집**
  2. 그 다음 Python/Java/C++ 등 자유 언어로 구현체 제작
  3. 실험 실행기/결과 수집기를 언어마다 2개씩 vs 언어마다 1개(내부 분할) —
     프로토타입은 Python 단일 패키지로
  4. requirements repo를 구현체 repo들과 **분리** 관리 (SSOT 극대화)
  5. 기존 후보(routix·aladia·laadi)가 아닌 **새 이름** 필요

## 0. 요약 (TL;DR)

**구상 전체에 찬성. 단 세 가지 보정을 제안한다.**

1. **gbrain은 SSOT가 아니라 SSOT 위의 인덱스·합성 레이어로 쓸 것.** gbrain 자체가
   그렇게 설계되어 있다 — 시스템 오브 레코드는 git markdown repo이고 DB는 파생물.
   따라서 "gbrain 중심"은 "gbrain **파일 규약**(markdown+frontmatter+typed link)
   중심으로 쓰되, gbrain이 사라져도 requirements corpus는 온전"으로 해석해야 안전.
2. **"다 먼저 모은 다음에"는 기존 자산 이관·통합의 타임박스로 한정할 것.**
   요구사항은 이미 대부분 수집돼 있다(§3). 새로 모으는 게 아니라 **재배치+색인**이다.
   이관 후에는 전체 waterfall이 아니라 경계별 contract-first로 진행 — aladia 교훈
   1원칙("소비자 없는 계약 금지")이 spec repo에도 그대로 적용된다.
3. **언어×컴포넌트 매트릭스는 N×2가 아니다.** 경계가 파일(계획서 §4 "파일만이
   경계")이므로 결과 수집기·분석기는 runner의 언어와 무관하게 **1개(Python)로 충분**
   하다. 언어별로 만들 것은 실행기(runner)뿐. 따라서 "Python 프로토타입, 단일 패키지,
   내부 분할"이라는 본인 판단이 정확하고, 그 내부 seam을 처음부터 파일 계약으로 두면
   나중에 쪼갤 필요조차 없을 수 있다.

repo 구조 추천: **2개로 시작** — ① spec repo(요구사항 markdown + 기계가독 계약 +
conformance fixtures), ② Python 구현 repo. 언어별 추가 repo는 두 번째 언어가
실제로 생길 때(YAGNI). 이름 숏리스트(2026-07-10 기준 변경 반영): **sindbad ·
daedalus · gordius** (§4).

---

## 1. gbrain 실사 결과

### 1.1 무엇인가

> "Search gives you raw pages. GBrain gives you the answer. It's the brain layer
> your AI agent has been missing — the only one that does synthesis, graph
> traversal, and gap analysis in one box." (README 원문)

- package.json 자기서술: "Postgres-native personal knowledge brain with hybrid
  RAG search". Garry Tan(YC CEO)이 본인 AI 에이전트들의 기억층으로 만든 실사용
  제품. TypeScript+Bun, PGLite(내장 Postgres WASM) 또는 외부 Postgres+pgvector.
- **핵심 구조: brain(=DB) / source(=markdown git repo) 이원화.** markdown 파일
  (YAML frontmatter)이 지식의 단위이고 **git repo가 시스템 오브 레코드**, DB는
  검색·그래프용 파생 인덱스. wikilink/typed-link에서 LLM 호출 없이 typed edge를
  추출해 지식그래프를 자동 구축.
- **schema pack**: 페이지 타입 체계(taxonomy)를 버전 있는 YAML로 정의·교체·마이그레이션
  가능 (`api_version: gbrain-schema-pack-v1`).
- `gbrain think`: 인용 달린 답 + **gap 분석("브레인이 아직 모르는 것")**. 상시
  dream cycle이 중복 제거·인용 수정·**모순 탐지**를 자동 수행.
- CLI + **MCP 서버** 제공 — Claude Code 등에서 도구로 직접 질의 가능.

### 1.2 성숙도

production급. src/ TS 파일 751개, 테스트 파일 ~1,198개, CI 정적 가드 스크립트
~30개, 문서 방대(AGENTS.md·llms.txt 포함), CHANGELOG에 마이그레이션 40여 회.
단, **v0.42.x pre-1.0**이고 사실상 단독 메인테이너 — 변화 속도가 빠르다.

### 1.3 무엇이 아닌가

**실험 orchestration 프레임워크가 아니다.** 알고리즘 workflow, solver subroutine,
실험 config 같은 것은 정의하지 않는다. laadi가 하려는 일과 겹치지 않고, 겹치는
지점은 "지식(요구사항) 관리"뿐이다.

### 1.4 requirements 저장소 용도 적합성

잘 맞는다. 근거:

- **source = markdown git repo** 개념이 "별도 requirements repo"와 1:1 대응 —
  requirements repo를 만들고 gbrain source로 mount하면 끝.
- schema pack으로 requirements 전용 타입 체계를 정의할 수 있다. 예:
  `requirement / decision / contract / defect-lesson / open-question / prior-art`
  타입 + `supersedes / derives-from / verified-by / conflicts-with` typed link.
- `think`의 gap 분석·dream cycle의 모순 탐지는 요구사항 공학에서 실제로 유용한
  기능이다 — 지금까지 laadi 결정들이 문서 여러 곳에 흩어져 상호 모순을 사람이
  추적해온 것(예: P-1~P-8 대기 상태 관리)의 자동화 후보.
- **MCP 서버**: 구현 repo에서 작업하는 LLM 에이전트가 spec repo를 파일로 뒤지는
  대신 requirements brain에 질의 — "spec repo 분리 시 LLM이 spec을 못 본다"는
  분리의 대표 단점을 정면으로 상쇄한다. v1 존재 이유("LLM이 step-by-step으로
  구축")와 시너지가 큰 지점.

### 1.5 보너스 — laadi 설계 관점의 prior art

gbrain의 **eval 서브시스템**은 laadi가 참고할 만한 실전 패턴을 여럿 갖고 있다:

- NDJSON baseline 포맷: `_kind: 'baseline_metadata'` 판별자 헤더 행 + 데이터 행,
  `BASELINE_FILE_SCHEMA_VERSION` 명시 — self-describing 아티팩트 계약의 실례.
- **metric glossary를 코드 SSOT로** 두고 문서를 자동 생성
  (`metric-glossary.ts` → `METRIC_GLOSSARY.md`) — laadi의 계약↔문서 drift 방지에
  동일 기법 적용 가능.
- capture → baseline publish → replay → **gate**(회귀·정확도 이중 게이트) 루프 —
  acceptance 시나리오(계획서 §6.4)의 CI화 모델.
- 재현성 관행: 고정 seed, 순차 실행 기본(병렬은 opt-in), 비용 상한을 실행
  파라미터로, **결과 감사 추적을 git으로**.

### 1.6 리스크

1. **pre-1.0 churn**: 마이그레이션 40여 회 이력. requirements SSOT는 수년 살아야
   하는 자산 — §0-1의 "SSOT는 markdown, gbrain은 인덱스" 원칙을 지키면 gbrain이
   죽거나 크게 바뀌어도 corpus는 무사하다. 이 원칙이 리스크의 사실상 전부를 흡수.
2. **스택 추가**: Bun ≥1.3.10 + TS. 사용자 주력 스택(Python/Java) 밖의 런타임이
   하나 늘어난다. 소비만 하고 수정하지 않는 도구라 부담은 제한적.
3. **외부 API 유출 점검 필요**: 기본 reranker(ZeroEntropy)·embedding이 외부 API를
   쓴다. 미공개 연구 아이디어가 담긴 requirements를 넣기 전에 **로컬 전용/오프라인
   구성이 가능한지, 어떤 데이터가 어디로 나가는지 확인**해야 한다. (조사 미완 —
   도입 결정 시 첫 확인 항목.)

---

## 2. 구상 평가 — 사안별 판정

### 2.1 "새 repo에 요구사항 먼저" — 조건부 찬성

방향 자체는 이미 확정된 노선의 연장이다: 계획서 §4가 Define 층(layout·run_config·
spec)을 "언어중립 선언"으로, 경계를 "파일만"으로 이미 정의했고, §9 v2가 언어 교체를
로드맵에 올려놨다. 이번 구상은 그 방향을 **아키텍처 시점으로 앞당기는 것**이고,
aladia의 미해결 문제였던 "contracts 패키징"(계획서 §3.2)에 대한 구조적 답이기도 하다.

조건: **"다"를 기존 자산 이관으로 정의할 것.** 요구사항 수집을 완결 조건(gate)으로
두면 BDUF가 된다. aladia 실패의 일반화(계획서 §3.3)가 여기에도 적용된다 —
계약은 소비자(구현)가 있어야 검증된다. 제안: 이관·통합에 타임박스(1~2주)를 걸고,
그 후에는 spec과 Python 프로토타입을 **경계 단위로 병행**(spec 버전을 구현이 pin).

### 2.2 "gbrain 중심" — 조건부 찬성

§1.4대로 적합하다. 조건은 §0-1(SSOT는 markdown git, gbrain은 인덱스·합성 레이어)과
§1.6-3(외부 API 점검). 이 해석이면 gbrain 도입 실패조차 저비용이다 — mount 해제하면
평범한 markdown repo가 남는다.

### 2.3 언어 자유화(Python/Java/C++) — 찬성

단, 구현 언어별 repo를 미리 만들지는 말 것. v2 로드맵(executor process 계약,
C/C++ toy PoC)이 이미 이 문을 열어놨다. spec이 언어중립이면 언어 추가는 필요가
생길 때 하는 게 맞다.

### 2.4 실행기/수집기 분리 — 제3안: **N runners × 1 analyzer**

사용자가 제시한 두 안(언어마다 2개 / 언어마다 1개+내부 분할)은 둘 다 "언어마다
수집기도 다시 만든다"를 전제하는데, 그 전제가 불필요하다:

- 실행기(runner)는 사용자 알고리즘 코드가 사는 곳이므로 **언어별로 존재해야 한다**.
- 수집기·분석기는 계약을 준수한 **파일(manifest, trajectory.jsonl, solution 등)만
  읽는다**. runner가 Java든 C++이든 아티팩트가 계약에 맞으면 분석기는 하나면 된다.
  Java runner + Python analyzer 조합이 자연스럽게 성립한다.
- 따라서 언어별 작업량은 "2개"도 "1개(실행+수집)"도 아니고 **"runner 1개"**다.
  분석기는 Python 1벌을 계속 쓴다 (JS reader류는 §9 v2처럼 필요 시).

프로토타입 전략에 대한 판단: **"자신이 없으니 Python 단일 패키지로"는 겸손이 아니라
정답이다.** 계약은 첫 작성에서 완벽할 수 없고(aladia 실증), 같은 프로세스 안에서
쓰기측(runner)과 읽기측(analyzer)을 round-trip 테스트로 맞대보는 것이 계약을
단단하게 만드는 가장 싼 방법이다. 핵심은 하나: **단일 패키지라도 내부 seam을
in-memory 객체 전달이 아니라 "디스크에 쓴 파일을 다시 읽기"로 강제**할 것.
그러면 이후의 물리적 분리는 언제 해도 되고, 안 해도 된다.

### 2.5 spec repo 분리 — 찬성 (논거 정리)

정확히 하자면 SSOT는 repo 분리가 아니라 "단일 mastering 지점 + 참조 규율"에서
나온다 — monorepo의 `spec/` 디렉토리도 SSOT는 된다. 분리의 실익은 다른 데 있다:

| 실익 | 설명 |
| --- | --- |
| 버전 독립성 | spec을 태그로 릴리스, 구현들이 특정 버전을 pin — "무엇에 적합한 구현인가"가 기계가독 |
| 강제 decoupling | 구현이 spec 내부에 손을 못 댐. 계약 변경 = 별도 repo의 PR = 파괴적 변경 수준의 리뷰(사용자 전역 규칙과 일치) |
| 다언어 중립 지대 | 어떤 구현 언어의 소유물도 아닌 장소 — Java/C++ 구현이 생겨도 spec의 위치 논쟁이 없음 |
| gbrain 정합 | source = repo 단위 mount라 분리 repo가 곧 mount 단위 |

비용(솔로 개발자의 cross-repo 왕복, 구현 작업 중 spec 가시성)은 gbrain MCP(§1.4)와
spec 버전 pin으로 상쇄 가능. **단, spec repo가 산문만 담으면 aladia 재판이 된다** —
반드시 포함할 것: ① 기계가독 스키마(JSON Schema 등), ② golden fixtures(계약 준수
아티팩트의 정본 예시), ③ conformance 검사 실행기(얇게라도). "spec + conformance
suite"가 곧 표준이고, 산문 요구사항은 그 주석이다.

문서 언어: 기존 결정(§10-5, 전부 영어)을 spec repo에도 적용 권장 — LLM 소비성
극대화, 질문은 한국어로 해도 무방.

---

## 3. 기존 laadi 자산과의 관계 — 재수집이 아니라 이관

새 repo가 승인되면 다음이 씨앗 corpus다 (이미 수집 완료된 요구사항):

- `20260702_laadi_plan.md` — aladia 47항목 복원, 검증된 결함 목록, §5 설계 결정
  전체, S0–S8, v1 범위/로드맵
- `20260703_ccdeJava_review.md` — P-1~P-8 (**미결**, open-question 페이지로 이관)
- `20260707_deps_and_cpu_budget.md` — pydantic/loguru 기각 근거, CPU 예산 원칙
- `AGENTS.md` 타임라인 — 결정 이력(= decision 타입 페이지들), resume 분석의
  미기재 항목 4·6·7(ROOT gotcha, flow cache, 라운드트립+pickle)
- 잔여 미결: §10-8(frame↔(2a) 접점), P-1~P-8, physical core 검출/keyword 필드명

이 구상이 승인되면 "laadi"라는 패키지명·단일 repo 계획은 superseded되지만, **계획서
내용물은 전부 살아서 spec repo의 초기 페이지가 된다.** 버리는 것은 없다.

---

## 4. 이름 후보 (2026-07-10 기준 변경으로 갱신)

### 4.1 기준 (사용자, 2026-07-10)

원래 의중은 **aladin**(알라딘 — 한국인에게 익숙 + 세계적으로 유명)이었으나
aladdin·aladin 모두 PyPI 선점으로 포기. 새 기준 — 둘 다 필수:

1. **한국인에게 익숙한 발음/철자** (외래어 표기가 정착된 이름)
2. **세계적으로 유명함** (설화·신화·문학·과학자 등)

1차 후보였던 라틴/그리스 어원 계열(exagium 등)은 이 기준으로 superseded — 기록은
부록 B. 재생성은 사용자 지시대로 sonnet 서브에이전트가 수행(20개+ 브레인스토밍 →
전수 PyPI 확인 → 가용 19개), 상위 후보는 본 세션에서 PyPI 재검증(이중 확인).
PyPI는 2026-07-10 기준이며 §10-4 결정대로 선점하지 않으므로 공개 시점 재확인 필요.

### 4.2 숏리스트 (큐레이션)

| 순위 | 후보 | 유래 | 강점 | 약점 |
| --- | --- | --- | --- | --- |
| 1 | **sindbad** | 아라비안나이트의 뱃사람 신밧드 | **aladin과 같은 아라비안나이트 계열 — 원래 의중과의 연속성**. 반복 항해로 미지를 발견 = 반복 실험으로 해공간 탐색. GitHub 142건으로 충돌 낮음 | 표준 표기 "신밧드"의 역표기는 sinbad(선점)라 d 위치 혼동 여지. 단 sindbad는 임의 변형이 아니라 원어(Sindbād)에 충실한 정식 이형 — aladin(d 하나 뺀 변형)보다 정직한 타협 |
| 2 | **daedalus** | 그리스 신화의 장인·발명가 다이달로스 (이카루스의 아버지) | 주제 적합성 최고 — 설계자·발명가 원형 = 실험 설계 프레임워크. "다이달로스" 표기 정착 | Cardano 암호화폐 공식 지갑명과 정확히 겹침(개발자 검색 혼선). GitHub 1,781건 |
| 3 | **gordius** | "고르디우스의 매듭"의 왕 | 복잡한 문제의 해결 은유. GitHub 22건 — 전 후보 중 충돌 최소 | 구(句)로만 익숙하고 단독 이름 인지도 약함 |

### 4.3 차순위·기각 (가용하나 감점, 재검토 가능)

- **heisenberg** (하이젠베르크): 인지도 매우 높음(브레이킹 배드 포함). 단 10자이고,
  "측정이 결과를 교란한다"는 함의는 실험 프레임워크에 양날.
- **copernicus** (코페르니쿠스): EU 지구관측 프로그램 공식명과 충돌, 10자.
- **amundsen** (아문센): Lyft의 데이터 카탈로그 OSS와 동명 — 인접 분야라 실질 리스크.
- **ithaca** (이타카): DeepMind의 고대문자 복원 AI 모델명과 충돌 — ML 커뮤니티 혼선.
- **sunzi** (손자병법): 주제 적합성 최고이나 병음 철자가 조건 1 위반(보통
  suntzu를 먼저 시도, suntzu는 선점).
- **bremen** (브레멘 음악대): 주제 연결 없음.
- 기타 가용 확인됨(테마·인지도 미달로 기각): ishmael, fenrir(일본 Fenrir사),
  baldur(Baldur's Gate), tantalus·narcissus(부정적 함의), linnaeus(철자 괴리),
  oedipus(프로이트 연상), atalanta(축구클럽), guinevere(표기 불일치), vesalius(인지도).

### 4.4 선점 확인 목록 (2026-07-10, 재확인 불요)

sinbad, icarus, archimedes, eureka, atlas, prometheus, hercules, odin, darwin,
edison, curie, kepler, galileo, turing, athena, minerva, hermes, merlin, solomon,
occam, rubicon, virgil, euler, gilgamesh, sherpa, sisyphus, pygmalion, mendel,
planck (+ 1차 조사분: tactus, prova, ansatz, pacta, kanon, metron, veritor).

repo 명명 예 (sindbad 채택 시): spec repo = `sindbad-spec`, Python 구현 =
`sindbad`(PyPI 패키지명 동일), 향후 `sindbad-java` 등.

---

## 5. 승인 시 실행 순서 (제안)

1. **S-A**: 이름 결정 → spec repo 생성 → gbrain 설치·mount 전에 §1.6-3(외부 API
   데이터 경로) 확인 → requirements 전용 schema pack 초안.
2. **S-B**: 기존 docs/laadi 자산 이관(영어화 포함, §3 목록) — **타임박스 1~2주**.
   미결정 사항은 open-question 타입 페이지로.
3. **S-C**: Define 층 계약의 기계가독화(JSON Schema + golden fixtures + 얇은
   conformance 실행기) — 계획서 §4 Define 층이 초안 그 자체.
4. **S-D**: Python 구현 repo 시작 — 캐노니컬 빌드 순서 S0–S8 유지, spec 버전 pin,
   round-trip 테스트로 계약 검증. 이후 spec과 구현을 경계 단위로 병행 진화.

---

## 부록 A — 조사 방법

- gbrain: opus 서브에이전트가 저장소 shallow clone(커밋 50개, 2026-06-01~07-06
  구간) 후 README·package.json·src 구조·테스트·docs 실사. 인용문은 verbatim.
- 이름 1차(어원 계열): 본 세션에서 직접 생성·확인. 이름 2차(새 기준): sonnet
  서브에이전트가 생성·전수 확인, 상위 후보는 본 세션에서 재검증.
- 확인 도구: PyPI JSON API(HTTP 404=미등록)·GitHub repo 검색 API, 2026-07-10 실행.

## 부록 B — 1차 이름 후보 (라틴/그리스 어원 계열, superseded 2026-07-10)

새 기준(§4.1) 확정 전에 "시험·검정의 어원"을 축으로 생성했던 후보들. 전부 PyPI
미등록(2026-07-10)이었으며 기록용으로만 보존.

| 후보 | 어원·뜻 | GitHub | 비고 |
| --- | --- | --- | --- |
| exagium | 라틴어 "무게 달기·검정" — assay/essay의 공통 어원 | 0 | 당시 1순위 |
| silheom | 실험(實驗)의 로마자 표기 | 1 | 비한국어권 철자 오류 여지 |
| probanda | 라틴어 "입증되어야 할 것들" | 8 | |
| peira | 그리스어 πεῖρα "시도·시험" — empirical의 어원 | 119 | |
| empeiria | 그리스어 "경험" | 17 | |
| dokima | 그리스어 dokimē "검증됨·입증됨" | 67 | |
| experior | 라틴어 "나는 시험한다" | 40 | 동사형이라 어색 |
| saggio | 이탈리아어 "검정·시론" | 다수 | 일반 단어라 검색성 낮음 |

탈락(당시): tentamen(GitHub 391건 — 스웨덴어 "시험"이라 충돌 과다).
