# laadi 프로젝트 상태 — 작업 정본

**laadi** (Library for Algorithm Analysis & Design Infrastructure) = routix의
최종 후속 패키지. aladia(1차 greenfield 시도)를 대체하는 2차 greenfield 시도.

이 문서가 laadi 프로젝트의 **상태·결정·미반영 분석의 SSOT**다. laadi 관련 새 결정이나
분석이 생기면 (에이전트 메모리가 아니라) **이 파일에 기록**한다. 이전에 Claude 메모리
(`laadi-package-plan.md`)에 쌓이던 내용을 2026-07-09 전부 이관했다.

## 정본 문서 (전부 이 폴더 `docs/laadi/`)

- **계획서**: `20260702_laadi_plan.md` — branch `20260702_new_package_plans`에
  커밋됨(f3748cf; 문서 머리말의 "commit하지 않음" 문구는 구버전). 요구사항 복원
  (aladia 47개 항목), 검증된 결함 목록(routix 예외 삼킴 버그·pyyaml 미선언, aladia
  (a)↔(b) 미배선·contracts 패키징 미해결), 관심사 모델((2)를 2a 알고리즘/2b
  orchestration으로 내부 분할), 캐노니컬 빌드 순서 S0–S8, v1 범위/로드맵 포함.
- **ccdeJava 검토**: `20260703_laadi_ccdeJava_review.md` — 제안 P-1~P-8은
  **사용자 결정 대기** (아래 참조).
- **의존성·CPU 예산 메모**: `20260707_laadi_deps_and_cpu_budget.md` (아래 참조).
- **gbrain·신규 repo 구상 검토**: `20260710_gbrain_new_repo_opinion.md` —
  보정 1·2·3 동의(2026-07-10), **이름 최종 선정·착수 시점 잔여** (아래 참조).

## 존재 이유 (Why)

v1의 존재 이유는 "`uv add laadi` 후 LLM이 step-by-step으로 실험 코드베이스를
구축"하는 것. aladia의 실패 교훈 3원칙 — 소비자 없는 계약 금지(round-trip 테스트
필수), 선언한 불변식은 기계가 강제, 설치 상태에서 검증.

## 확정 결정 타임라인

### 2026-07-02 (사용자 답변)

- aladia 관계: **greenfield 재작성** — aladia 코드는 계승하지 않고 문서·계약만 참조.
- LLM 가이드: **CLI 상태기계**(`laadi init/status/validate/add`) + **AGENTS.md/템플릿
  scaffold** 병행. 상태는 상태 파일이 아니라 저장소 내용물에서 유도.
- v1 검증: **toy 예제를 LLM이 처음부터 구축**하는 acceptance → ffc_dw_wET_2026
  마이그레이션은 v1.x.
- PyPI에 `laadi`, `aladia` 둘 다 미등록 (2026-07-02 확인).

### 2026-07-03 추가 요구 (사용자)

subalgorithm 단위 분석 파일 생성은 필수 기능. subalgorithm도 algorithm = 액자식
(재귀) 구성 → 액자 단위 기록·분석. 실행 중엔 분석에 필요할 데이터를 전부 텍스트로
유연하게 보관, 그림/HTML은 분석 때만.
→ 계획서 §5.9 frame 모델(frame 트리 = call context, frame.emit/metric, diagnostic
level, 텍스트 전용 계약) + §5.10 analyzer 1급 시민(analyzer_spec, 한 정의로 in-run/
standalone 동일 경로, study scope + study_manifest)로 반영. 근거: ffc_dw_wET에서
진단 하나에 공유 파일 3곳+ 수정, CSR coarse obj 미보존→1,440 인스턴스 재실행,
분석 3종이 로그 regex 스크래핑, 산출물이 repo root/gitignored analysis/에 무정부
적재.

### 2026-07-06 §10 결정 (사용자 답변, 계획서 §0.1·§10에 반영)

① subalgorithm 실행 모델 = **context-callable** 확정(기준: "Sonnet 4.5급 LLM이
작성하기 좋은 형태" — 스파이크 불요), ② per-instance timelimit 표현식(`"5nc"`류) =
표준 필드 필수, ③ 분석 v1 절단선 제안대로, ④ `laadi` 유지·PyPI 선점 안 함(선점되면
개명), ⑤ 문서 **전부 영어**(laadi 저장소 기준), ⑥ routix 검증 버그 3건 수정 완료
(예외 삼킴 제거·concurrent per-instance 격리·pyyaml 의존성 선언 + 실패 기록용
`on_run_error` 훅 신설(C안: 기본 no-op, 훅 예외는 원 예외를 가리지 않음) +
tests/test_runner_failure.py·test_packaging.py, 버전 0.0.17 유지 — 릴리스는
/release로 별도), ⑦ frame 크기 v1 무제한+bytes 관측, ⑧ frame↔(2a) 접점만
**미해결** — "context가 제공하는 frame 기능을 (2a) 심층까지 어떻게 전달하나"로
좁혀짐 (laadi 저장소에서 스파이크로 결정).

### 2026-07-09 계산 실험 안정성 (사용자 요구, 계획서 §5.12 신설)

`ffc_cmax` checkpoint 관행 조사(최상위 flow 스텝 완료마다 incumbent schedule 전체를
`checkpoints/<step>-<method>/`에 resume 입력과 동일 모양으로 기록,
`controller_core.py` `_try_save_step_checkpoint`; resume metadata 82개가 실전 소비)
를 근거로 laadi가 프레임워크 소유. 사용자 결정: **스텝 내 손실은 수용**(긴 스텝은
알고리즘 성질) — 같은 granularity에서 확실히 잃지 않는 게 목표. 설계: ① frame 경계
자동 checkpoint(layout kind로 경로, 모양=final과 동일) ② 원자적 쓰기(temp+os.replace,
checkpoint_manifest 맨 마지막) ③ trajectory 레코드 단위 flush ④ SIGTERM/SIGINT
graceful shutdown(cooperative stop→status: interrupted, 2회째 즉시 종료; §5.4
매트릭스에 행 추가) ⑤ solution 없어도 기록은 남김 ⑥ checkpoint inventory analyzer
동봉. **기록 측은 v1 포함, 복원(RESUME)은 v1.x 유지** — checkpoint 모양이 resume
계약의 예약. §2.5·§8·§9도 연동 수정.

### 2026-07-10 신규 repo 구상 (사용자 답변)

- `20260710_gbrain_new_repo_opinion.md`의 **보정 1·2·3 모두 동의**: ① gbrain은
  SSOT(git markdown) 위 인덱스·합성 레이어로만, ② 요구사항 "선수집" = 기존 자산
  이관의 타임박스로 한정, ③ N runners × 1 Python analyzer — Python 단일 패키지
  프로토타입, 내부 seam은 "파일 재읽기"로 강제.
- **이름 기준 변경**: 원래 의중은 aladin(한국인에게 익숙 + 세계적으로 유명)이었으나
  aladdin·aladin 모두 PyPI 선점. 새 기준 = **한국인에게 익숙한 발음/철자 + 세계적
  유명함** (두 조건 모두 필수). 라틴/그리스 어원 후보(exagium 등)는 이 기준으로
  superseded. 후보 재생성은 sonnet 서브에이전트 위임 → **완료**: 가용(PyPI 미등록)
  19개 확보, 숏리스트 **sindbad·daedalus·gordius** + 차순위·선점 목록은 20260710
  문서 §4에 기록(선점 목록 재확인 불요). 최종 선정은 사용자 몫.

### 2026-07-11 composite subalgorithm (정의로서의 시퀀스, 계획서 §5.3.1 신설)

subalgorithm을 **다른 subalgorithm들의 순서 있는 시퀀스**로 정의할 수 있게 함 —
§1.2의 "subalgorithm도 algorithm = 액자식(재귀)"을 §5.9(기록 측)에 이어 **정의 측**
으로 완성. 지금까지 시퀀스 구성은 run_config의 flow에만 있고 §5.9는 결과를 *기록*만
했다. 실전 선례(조사로 검증): `../ffc_dw_wET_2026`의 `coarsen_solve_reconstruct`가
inline `solve_flow`(top-level flow와 동일 schema)를 받아 coarsen된 instance 위에서
**같은 클래스의 자식 컨트롤러**로 실행 — IMPLEMENTED 2026-07-11
(`plans/20260711/csr_solve_flow.md`, `orchestration/controller.py:2640·2816·2886`,
`metadata/20260711/csr_subalg.yaml`). 설계: ① 정의 형태 둘(A 선언형 = spec의
`steps` sub-flow·code_ref 없음 / B 래핑형 = code_ref + flow-typed param, CSR가 B의
정본)이지만 **문법(§5.5)·실행(자식 frame subtree §5.9)·기록(frame 트리)은 하나** ②
parameter passing: inner step params는 자식에 inline 전달, 래핑형 composite 자신의
params(CSR `factor`·`timelimit`)는 wrapper 소관·자식엔 명시 구성한 (instance, budget,
scale=`time_factor`) 전달 ③ **nesting 무제한 + cycle 금지**(v1; depth guard 없음,
상한은 공유 시간 예산) ④ 검증 재귀화(child 등록 확인·params 정합·cycle 없음·flow-typed
param 비어있지 않음) ⑤ I1(register ≤1)은 leaf 단위, composite 부모는 자식 outcome
집계 후 1회 register(CSR: 후보 수집→dedup→원척 복원·검증→argmin, `obj_bound=None`).
계획서 §5.3.1 신설 + §2.3(subalgorithm_spec mechanism)·§2.4(I1·cycle)·§5.5(문법
공유)·§5.9(정의↔기록 대칭)·§6.1(S5 판정)·§6.2(`add subalgorithm --of`) 연동,
`20260707` 메모 §2.2·§2.3(예산 트리 재귀) 갱신. **§10-8은 여전히 미해결** —
`context.run_subflow`류가 §10-8의 프레임워크 주도형 특수해이나 opaque (2a) 심층 frame
문제는 별개로 잔존.

## routix 병행 수정과 호스트 영향

**호스트 3개 영향 조사 (2026-07-06, opus 서브에이전트)**: 러너 실패 의미론 변경에
대해 셋 다 **즉시 변경 불요** (uv.lock이 구버전 고정: ffc_cmax=0.0.15, 나머지 0.0.17).
업그레이드 시: ffc_cmax는 3계층 전부 run() 완전 override라 무영향; fm_prmu는 single이
super().run() 위임이라 새 의미론 적용되나 집계가 디스크 .exists() 가드 기반이라 견고
(실패 인스턴스가 파일을 안 남기고 집계에서 조용히 빠지는 운영상 변화만; 선택:
on_run_error로 에러 요약행); **ffc_dw_wET는 None 방어 적용 완료(2026-07-06)** —
concurrent 격리가 워커 사망 시 None을 인스턴스 리스트에 주입하게 되는 문제. 조사 때
지목된 2곳(main.py:145, reporting.py:561) 외에 reporting.py 리포터에 미방어 소비처
~20곳이 더 있어서, 소비처별 가드 대신 **유입 단일 지점(reporting.py ScenarioResult
조립부)에서 None→error 세팅된 placeholder InstanceResult(`_worker_failure_placeholder`)
로 정규화**. 실패가 main의 에러 카운트에 잡혀 조용히 사라지지 않음. 테스트
tests/orchestration/test_multi_scenario_runner.py::test_post_run_process_normalizes_none_instance_result
추가, 508개 통과. 커밋은 사용자 몫.
메타 관찰: 세 호스트 모두 run() override로 실패 계약을 각자 재발명 — laadi §5.4의 실증.

## 보강 메모 (2026-07-07)

정본: `20260707_laadi_deps_and_cpu_budget.md`. ① **pydantic·loguru 미채택**
(SSOT 역전·스키마 drift·seam 오염 / 전역 sink는 라이브러리 부적합 — stdlib logging),
② **CPU core 예산 사전 검사 + algorithm 일반 원칙** — 병목은 physical core. 모든
algorithm은 별도 표기 없으면 core 최대 1개; multi-core 가능 algorithm은 표준
optional kwarg(default 1)로 지정 (solver 한정 아님, 불변식 I-목록 편입 후보).
run_config 로드 시점에 `max(step별 keyword) × instance worker 수`를 physical core
수와 비교, 초과면 실행 전 error. ResourceMonitor(동적 관측)와 상보. 미해결:
physical core 검출 방법(psutil?), keyword 필드명.

## 분석 기록

### ccdeJava 검토 (2026-07-03) — 제안 P-1~P-8 **사용자 결정 대기**

사용자의 또 다른 분리 선례 `../ccdeJava`(Java+CPLEX, 알고리즘=feature 모듈 ↔
실행=local-runner 모듈, 분석=python_scripts 언어 분리)를 opus 서브에이전트로 조사 →
`20260703_laadi_ccdeJava_review.md` 작성(사용자가 20260703으로 리네임 후 커밋).
결론: 경계 위치는 laadi와 동형이나 계약 부재로 실측 drift(SpecialRowValue 값 분기
등)·수동 핸드오프·산출물 증발 발생. 계획 보강 제안 **P-1~P-8**(검증형 analyzer
verdict, 외부 해 import, per-instance 설정 동결 I7, 인코딩 조항, 값 어휘 계약화,
기계 키/표시명 분리 등)은 **사용자 결정 대기 — 계획서 본문은 아직 수정하지 않음**.

### ffc_dw_wET resume 커밋 분석 (2026-07-09, c2657e0b, opus 조사) — **계획서 반영 완료**

"seed tail from base run incumbent" = crash recovery가 아니라 **완주한 base run의
공통 prefix(예산 ~40%)를 1회 계산 후 7개 tail 설정으로 분기하는 실험 fan-out** —
laadi RESUME의 두 번째 용례. 참고: 그 커밋의 계획 문서가 말하는 "hybridflowshop
참조 구현" = ffc_cmax_2026 내 패키지(동일 prior art의 이식).

신규 참조점:

1. **시계 back-dating**: `timer.set_start_time(now − 실측 prefix_elapsed)` —
   timelimit 표현식·정지조건 코드 무변경 재사용, manifest의 실측 elapsed를 과금.
2. **obj_log를 절대 timestamp로 병합**: rescaling 불필요(back-dating 덕),
   call_index가 아닌 timestamp로 세그먼트해 중복 인덱스 공존.
3. **SSOT 분할**: 스케줄←solution.json, LB/obj 스칼라←manifest (solution의
   objBound는 보통 None) — checkpoint shape 설계 시 이 이원성 명시 필요.
4. **seed 레코드 ROOT gotcha**: 복원 등록도 method context 안에서 해야 함(아니면
   step_label=ROOT로 다운스트림 obj_log 소비자 전부 파손 — 실제 발생·수정).
   복원 레코드는 native 스텝과 형태상 구분 불가해야 한다.
5. **prefix 안전 감사 + 확장 훅**: "tail이 소비하는 prefix 상태 = incumbent+LB뿐"을
   명시 감사, 그보다 크면 재실행할 스텝을 지정하는 `method_names_to_run_before_resume`.
6. **flow cache 스탬프**: 시나리오 dir별 실행 flow 자동 기록 + strict prefix
   equality 검증 (config basename 의존은 fragile로 명시적 기각).
7. **라운드트립+pickle 테스트**: solution 로더가 dump와 대칭임을 라운드트립으로,
   ProcessPool 주입 가능성을 pickle 테스트로 계약화.

약점(반면교사): manifest 무검증 신뢰(ffc_cmax ResumeValidator의 obj 재계산·교차검증
누락), resume_dir 하드코드 절대경로(run_manifest 간접참조 필요), back-dating의
하드웨어 이질성 미고려(base와 다른 머신이면 tail 예산 왜곡).

→ 2026-07-09 계획서 반영 완료 (사용자 승인): §5.12 RESUME 관계 문단에 "resume의 두
용례(crash recovery / prefix 분기)" 추가 + §9 v1.x RESUME 항목에 1·2·3·5를 실전
검증본으로 병기 (back-dating의 하드웨어 이질성 주의 포함). 4(ROOT gotcha)·6(flow
cache)·7(라운드트립+pickle 테스트)은 계획서 미기재 — laadi 저장소 구현 시 이 문서를
참조.

### gbrain 조사 + "요구사항 우선 신규 repo" 구상 검토 (2026-07-10) — **보정 동의로 종결**

사용자 제안(요구사항을 gbrain 중심 신규 repo에 먼저 수집 → 자유 언어 구현, spec
repo 분리, 새 이름)을 opus 서브에이전트의 gbrain 실사와 함께 검토 →
`20260710_gbrain_new_repo_opinion.md`. 요지: **찬성 + 보정 3건** — ① gbrain은
SSOT(git markdown)의 인덱스·합성 레이어로만(외부 API 데이터 경로 점검 필수),
② "다 먼저 수집" = 기존 docs/laadi 자산 이관의 타임박스로 한정(waterfall 금지),
③ 매트릭스는 N×2가 아니라 **N runners × 1 Python analyzer**(경계=파일 계약이므로)
— Python 단일 패키지 프로토타입이 정답이되 내부 seam을 "파일 재읽기"로 강제.
spec repo는 스키마+golden fixtures+conformance 실행기 필수(산문만이면 aladia 재판).
laadi 단일 repo 계획은 superseded되나 계획서 내용물은 spec repo의 씨앗으로 전부 이관.

→ 2026-07-10 당일 사용자 답변: 보정 1·2·3 전부 동의 (타임라인 참조). 검토 시점의
1차 이름 후보(exagium 계열)는 이름 기준 변경으로 superseded — 현행 숏리스트는
20260710 문서 §4(sindbad·daedalus·gordius), 1차 후보 기록은 같은 문서 부록 B.

## 잔여 결정·작업 규칙

- **잔여 결정**: §10-8(frame↔(2a) 접점 — laadi 저장소에서 스파이크) + ccdeJava
  P-1~P-8 + **이름 최종 선정(새 기준 후보 중) + 신규 repo 생성 착수 시점(사용자
  지시 대기)**.
- laadi 저장소 생성 시 계획서를 첫 입력으로. **아직 laadi 디렉토리 생성은 하지 말
  것** (사용자 지시 대기).
- laadi 관련 새 결정/분석은 이 파일에 기록 (에이전트 메모리 금지). 커밋은 사용자 몫.
