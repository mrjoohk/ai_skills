# Core Engineering Pipeline Skills — 스킬 연동 사용 매뉴얼

> 저장소 위치: 스킬 정본은 [`skills/`](../../skills/), 전체 목록은 [스킬 목록](../skill-catalog.md), 새 프로젝트 규칙·도구는 [프로젝트 템플릿](../../templates/project/)을 참조합니다. 이 문서의 분류명은 폴더 사본이 아닌 사용 흐름을 뜻합니다.

> **디렉토리 목적:** 자연어 문제 기술에서 검증된 코드 산출물까지, 소프트웨어 엔지니어링 전 주기를
> 구조화된 아티팩트(문서 + 코드 + 증거)로 연결하는 파이프라인 스킬 묶음.

요청에 필요한 단계만 선택한다. 짧은 작업은 main이 직접 처리하고, 독립적으로 나눌 이점이 있는 작업만
런타임의 가용 slot 안에서 worker에게 맡긴다. main은 의존성·쓰기 범위·필수 수락 기준을 정하고 결과를 통합·검증한다.
사용자가 지정한 출력과 기존 정본 위치가 우선이며, 아래 `rd/`, `reports/` 경로는 새 프로젝트의 선택 기본값이다.
공통 운영은 [GLOBAL_RULES](../../templates/project/GLOBAL_RULES.md)의 lightweight 모드를 기본으로 한다.
[TRACEABILITY](../../templates/project/policies/TRACEABILITY.md)는 명시적으로 tracked를 선택했거나 기존 프로젝트의 필수 추적 규약이 있을 때 적용한다.

---

## 포함 스킬 목록

| 스킬 | Stage | 역할 |
|------|-------|------|
| `core-engineering` | 전체 | 파이프라인 전체 규칙 정의 (마스터 레퍼런스) |
| `context-engineering` | 프로젝트 시작 | 에이전트 설정 파일 생성 (CLAUDE.md / AGENTS.md / GEMINI.md) |
| `req-elicitor` | 1–4 | 문제 정의 → 요구사항 도출 |
| `if-designer` | 5–6 | IF 경계 설계 → UF 후보 분해 |
| `uf-designer` | 7 | UF 블록 명세 정의 |
| `uf-implementor` | 구현 | UF 블록 → 프로덕션 코드 + 유닛 테스트 (TDD) |
| `if-integrator` | 통합 | UF → IF 수준 통합 모듈 조립 |
| `uf-chain-validator` | 검증 | UF 체인 무결성 + I/O 계약 검증 |
| `uf-if-debug-mapper` | 디버깅 | UF/IF 이슈 → 코드 위치 매핑 + 디버깅 플랜 |
| `eval-planner` | 8 | 평가 지표 · 임계값 · 벤치마크 계획 설계 |
| `exp-runner` | 8 | 평가 계획 실행: 시드·환경 고정, 실험 실행, provenance 기록 |
| `eval-runner` | 8 | 실험 결과 지표 계산 + 비교 보고서 생성 |
| `ci-evidence-automation` | CI | CI 게이트 · 증거 팩 · 회귀 감지 자동화 |
| `project-summarizer` | 완료 | 프로젝트 진행 전 과정 요약 문서 생성/갱신 |

> `core-engineering` 스킬은 직접 실행하는 스킬이 아니라, 나머지 모든 스킬이 참조하는
> **설계 원칙 문서** 역할을 한다. 파이프라인 시작 전 읽어두는 것을 권장한다.
> 설계 갈림길에서는 요청 범위를 먼저 확인하고, 결과에 영향을 주는 후보는 대표 입력으로 비교한다.
> 후보 시제품은 서로 독립이고 출력 경로를 분리할 수 있을 때 가용 slot 안에서 병렬로 맡길 수 있다.

---

## 전체 파이프라인 흐름

```
[자연어 문제 기술]
        ↓
① req-elicitor ──────────────────────────────────────────
   problem_statement.md / clarification_log.md
   assumptions_and_constraints.md / requirements.md
        ↓
② if-designer ───────────────────────────────────────────
   if_list.md / if_decomposition.md
        ↓
③ uf-designer ───────────────────────────────────────────
   uf.md (UF 블록 전체 명세)
        ↓
   [도메인 특화 감사 투입 시점 — specific_skills 참조] ★
        ↓
④ uf-implementor ────────────────────────────────────────
   src/uf/*.py + 유닛 테스트
        ↓
⑤ if-integrator ─────────────────────────────────────────
   src/if/*.py + 통합 테스트
        ↓
⑥ uf-chain-validator ────────────────────────────────────
   UF 체인 검증 리포트
        ↓
⑦ eval-planner ──────────────────────────────────────────
   rd/evaluation_plan.md
        ↓
⑦.5 exp-runner ──────────────────────────────────────────
   실험 실행: evidence_pack/runs.yaml + env.yaml + results/
        ↓
⑧ eval-runner ───────────────────────────────────────────
   실험 결과 비교 보고서
        ↓
⑨ ci-evidence-automation ────────────────────────────────
   CI 워크플로우 + 증거 팩 구성
        ↓
⑩ project-summarizer ───────────────────────────────────
   project_summary.md (전 과정 회고 + 인수인계 문서)
```

---

## 단계별 사용 방법

### ① req-elicitor — 문제 정의 & 요구사항 도출

**언제:** 새 프로젝트/기능을 시작할 때. 가장 먼저 실행.

**트리거 예시:**
- "요구사항 뽑아줘", "REQ 써줘", "설계 시작해줘"
- 문제 배경 설명 후 "requirements.md 만들어줘"

**입력 → 출력:**
```
자연어 문제 설명
  → problem_statement.md
  → clarification_log.md (명확화 Q&A)
  → assumptions_and_constraints.md
  → requirements.md (REQ 블록: Given/When/Then 형식)
```

**주의:** 명확화 질문에 충분히 답변한 후 다음 단계로 진행.

---

### ② if-designer — 시스템 경계 & IF 분해 설계

**언제:** `requirements.md` 완성 직후.

**트리거 예시:**
- "IF 설계해줘", "시스템 경계 잡아줘", "if_list 만들어줘"

**입력 → 출력:**
```
requirements.md
  → if_list.md (IF 블록: I/O 계약 포함)
  → if_decomposition.md (IF → UF 후보 트리 + 의존성 그래프)
```

**v2 변경사항:** 각 리프 노드에 `Verification Owner` 선언 필수 (`UF-local` / `guard-rail+chain` / `IF-acceptance`).
모든 리프 노드가 독립 기능 테스트 대상이어야 한다는 이전 가정은 폐기. 컴포지션/어셈블리 노드는
`guard-rail+chain` 또는 `IF-acceptance`로 분류.

**v2.1 변경사항 — 계약 설계 원칙 추가:**
- **Hyrum's Law 적용:** Output Contract에 노출하는 모든 필드는 다운스트림이 암묵적으로 의존할 수 있음을 인식하고 최소 노출 원칙으로 설계
- **추가 우선 원칙:** 기존 IF 계약 수정 시 기존 필드 삭제/변경 금지 — 선택적 필드 추가로만 확장
- **에러 시맨틱 통일:** 모든 IF의 Failure Modes는 동일한 에러 표현 방식을 따름

---

### ③ uf-designer — UF 블록 명세 정의

**언제:** `if_decomposition.md` 완성 직후.

**트리거 예시:**
- "UF 설계해줘", "UF 블록 만들어줘", "uf.md 작성"

**입력 → 출력:**
```
if_decomposition.md
  → uf.md (전체 UF 블록: 알고리즘 요약 + 엣지케이스 + 검증 계획)
  → uf_split/uf_if01.md (IF-01 전용 UF 블록 뷰)
  → uf_split/uf_if02.md (IF-02 전용 UF 블록 뷰)
  → ... (IF별 1개 파일)
```

**v2 변경사항:**
- `Verification Plan`이 3개 서브 필드로 구분: `Ownership` / `Unit Verification` / `Chain Verification`
- `UF-local`: 독립 테스트 경로 + 커버리지 목표 필수
- `guard-rail+chain`: 가드레일 테스트 + IF-체인 테스트 경로 필수, 독립 기능 테스트 불필요
- `IF-acceptance`: IF-인수 테스트 경로만 필수, 독립 테스트 불필요
- `uf.md` 외 `uf_split/` 동반 파일 생성 추가

**중요:** UF 설계 완료 후 `uf-chain-validator`를 1차 실행해 Ownership 선언 완결성을 확인한 뒤 구현으로 진행.

---

### ★ 도메인 특화 감사 투입 시점 (specific_skills)

> uf.md가 완성되고 uf-implementor 실행 전후, 또는 if-integrator 단계에서
> 프로젝트 도메인에 따라 [domain_audits](../../skills/domain_audits/)의 감사 스킬을 선택 투입한다.
> **이 스킬들은 파이프라인 구성 스킬이 아니라 선택 투입 감사 스킬이다.**
>
> | 투입 조건 | 권장 스킬 |
> |-----------|-----------|
> | GPU/HPC 연산 포함 UF가 있는 경우 | `gpu-hpc-guard` |
> | 물리 시뮬레이션 방정식이 포함된 경우 | `sim-physics-auditor` |
> | RAG 파이프라인 또는 임베딩 데이터를 다루는 경우 | `rag-data-quality` |
>
> 자세한 사용법은 [도메인 감사 가이드](specific_skills.md)를 참조한다. 병렬 감사 결과는 worker별 fragment 또는 메시지로 반환하고,
> main이 검증 후 `domain_metrics.md` 정본에 병합한다. 같은 파일에 여러 worker가 동시에 쓰지 않는다.

---

### ④ uf-implementor — UF 코드 구현 (TDD)

**언제:** `uf.md` + UF→IF 커버리지 검토 완료 후.

**트리거 예시:**
- "UF 구현해줘", "코드 써줘", "implement UF"

**입력 → 출력:**
```
uf.md (+ uf_if_coverage_review.md 권장)
  → tests/unit/test_uf_*.py (테스트 먼저 — RED 단계)
  → src/uf/*.py (프로덕션 코드 + 독스트링 — GREEN 단계)
  → reports/impl/uf_impl_report_*.md
```

**v2 변경사항 — TDD 사이클 적용:**
- **RED 먼저:** acceptance criteria(Given/When/Then) → pytest 함수로 변환 후 FAIL 확인
- **GREEN:** 테스트 통과하는 최소 구현 작성
- **DAMP 원칙:** 테스트는 DRY보다 DAMP — 각 테스트가 독립적으로 스펙처럼 읽혀야 함
- **Mock 최소화:** 시스템 경계(I/O, 네트워크)에서만 Mock 사용
- **Beyonce Rule:** 기존 UF 수정 시 테스트 커버리지 감소 금지

---

### ⑤ if-integrator — UF → IF 통합

**언제:** 모든 필요 UF가 `IMPLEMENTED` 상태가 된 후.

**트리거 예시:**
- "UF들 통합해줘", "IF 모듈 만들어줘", "integration code 작성"

**입력 → 출력:**
```
if_list.md + if_decomposition.md + src/uf/
  → src/if/*.py (통합 모듈 + 공개 API)
  → tests/integration/ (통합 테스트)
```

---

### ⑥ uf-chain-validator — UF 체인 무결성 검증

**언제:** 기능 브랜치 병합 전, UF 모듈 추가/리팩터 후.
         `uf-designer` 완료 직후 설계 검토용으로도 조기 실행 권장.

**트리거 예시:**
- "UF 검증해줘", "체인 검사해줘", "validation 돌려줘"

**입력 → 출력:**
```
uf.md + if_list.md + src/ + tests/ + evidence_pack/
  → validation_report.md (3개 게이트별 PASS/FAIL/WARN + 제안 수정)
```

**v2 변경사항 — 3-Gate 구조:**

| 게이트 | 검증 내용 |
|--------|-----------|
| **Gate 1** 구현/런타임 | I/O 계약 존재, 체인 연속성, 런타임 스모크 테스트 |
| **Gate 2** 문서-테스트 정합 | Ownership 선언 완결성, 소유권별 테스트 경로 존재 여부 |
| **Gate 3** 증거 팩 완결성 | 증거 항목 누락 여부, `uf_split/` 동기화 상태 |

**중요:** `guard-rail+chain` 또는 `IF-acceptance` UF에 독립 기능 테스트가 없어도 자동 FAIL 아님.
소유권이 명시적으로 선언되고 해당 소유권의 테스트 경로가 존재하면 PASS.
필수 수락 기준이나 게이트가 FAIL이면 해당 결과에 의존하는 후속 단계는 통과 전까지 실행하지 않는다.
독립적인 작업은 계속할 수 있다.

---

### ⑦ eval-planner — 평가 지표 & 임계값 설계

**언제:** 구현 완료 후, 실험 실행 전. Stage 8 진입점.

**트리거 예시:**
- "평가 기준 잡아줘", "KPI 어떻게 측정해", "evaluation plan 만들어줘"

**입력 → 출력:**
```
uf.md + requirements.md
  → evaluation_plan.md (도메인별 지표 + 임계값 + 벤치마크 계획)
```

---

### ⑧ eval-runner — 평가 실행 & 결과 리포트

**언제:** `evaluation_plan.md` 완성 후, 실험 결과 데이터가 있을 때.

**트리거 예시:**
- "지표 계산해줘", "실험 결과 비교해줘", "결과 테이블 만들어줘"

**입력 → 출력:**
```
evaluation_plan.md + 실험 결과 데이터
  → 지표 계산 함수
  → 실험 비교 보고서 (Markdown)
```

---

### ⑨ ci-evidence-automation — CI 자동화 & 증거 팩

**언제:** 새 UF 모듈 도입 시, CI 구성 정비가 필요할 때, 변경의 음성 대조(변이 시험) 증거가 필요할 때.

**트리거 예시:**
- "CI 설정해줘", "evidence pack 만들어줘", "coverage gate 잡아줘"
- "변이 시험 돌려줘", "음성 대조 증거 만들어줘"

**입력 → 출력:**
```
.github/workflows/ + test commands + evidence_pack/
  → CI 워크플로우 권장 구성
  → evidence pack 스키마 + 샘플
  → 회귀 임계값 + 알림 템플릿
변이 명세(JSON 또는 옛 .py) + 시험 명령
  → scripts/mutation_runner.py → 결과 JSON(변이별 잡힘/살아남음·잡은 시험) + 관문(종료 코드)
```

**변이 실행기 요점:** 반복 중에는 `--check`·`--changed`·`--only`, 끝에 전체 한 번 `--jobs <코어 수>`.
호출당 시간 제한이 있는 호스트는 `--budget` + `--out`(같은 명령 반복으로 이어 감), 마지막 관문은 `--summary --strict`.
자세한 것은 [변이 실행기 가이드](../../skills/engineering_pipeline/ci-evidence-automation/references/mutation_runner.md)를 참조한다.

---

### ⑩ project-summarizer — 프로젝트 완료 정리

**언제:** 프로젝트 마무리, 스프린트 회고, 인수인계 문서 필요 시.
         중간 점검 시에도 실행하여 `project_summary.md`를 누적 업데이트할 수 있다.

**트리거 예시:**
- "프로젝트 정리해줘", "지금까지 한 일 요약해줘", "project summary 만들어줘"
- "회고 문서 만들어줘", "인수인계 자료 작성"

**입력 → 출력:**
```
대화 히스토리 + 설계 산출물 (requirements.md, uf.md 등)
  → project_summary.md (문제 배경 / 설계 결정 / 구현 흐름 / 이슈 & 해결 / 개선점)
```

**특징:** 기존 `project_summary.md`가 있으면 덮어쓰지 않고 내용을 병합·갱신한다.

**v2.1 변경사항 — Key Decisions 섹션 추가:**
- **What이 아닌 Why 기록:** 결정 사항에는 이유 + 기각한 대안을 반드시 포함
- **Key Decisions 표 필수:** 중요 설계 결정은 `결정 | 선택 | 기각 대안 | 이유` 형식으로 기록
- 기록 기준: 두 가지 접근법 비교·선택, IF 경계 변경, 알고리즘 교체, 예상치 못한 제약으로 설계 변경

---

## 디버깅 발생 시 — uf-if-debug-mapper

파이프라인 어느 단계에서든 예상치 못한 오류가 발생하면 투입.

**트리거 예시:**
- "어디를 디버깅해야 해?", "CI 실패했어, 어디가 문제야?"
- "런타임 에러 났어, 디버깅 플랜 짜줘"

**입력 → 출력:**
```
UF/IF 목록 + 에러 로그 + 모듈 레이아웃
  → 디버깅 가이드 (코드 위치 맵 + 수정 제안 + 검증 방법)
```

**v2.1 변경사항 — 구조적 트리아지 추가:**
- **오류 범위 보류:** 실패한 결과에 의존하는 단계는 보류 → 증거 보존 → 5단계 트리아지. 독립 작업은 계속 가능
- **5단계 체크리스트:** Reproduce → Localize → Reduce → Fix Root Cause → Guard
- **근본 원인 수정 원칙:** 증상만 수정 금지, "왜 발생했는가?"를 원인에 도달할 때까지 반복
- **Guard 단계 의무화:** 버그 수정 후 재발 방지 테스트 추가 필수

---

## 같은 날 변경 검토 — fresh-eyes-auditor (Delta 모드)

큰 변경이나 위험이 높은 변경은 diff 범위를 정해 검토한다. 알고리즘·수치 성질, API·데이터 흐름, 시험 등 필요한 관점을
선택하고, 독립 검토가 유용하면 가용 slot 안에서 worker를 배정한다. main은 인용과 증거를 대조해 지적을 채택하고,
수정 후에는 영향받은 범위만 재확인한다. 검토 범위와 회수·시간 예산을 정해 같은 전체 감사를 무한 반복하지 않는다.
긴 작업의 재개에 필요한 보고·처분 내역은 파일로 남긴다. 자세한 것은
[fresh-eyes-auditor](../../skills/engineering_pipeline/fresh-eyes-auditor/SKILL.md)의 Delta 모드를 참조한다.

---

## 컨텍스트 관리 — context-engineering

필요한 에이전트 설정 파일을 기존 환경과 규약에 맞춰 생성·병합하는 스킬.
`CLAUDE.md`, `AGENTS.md`, `GEMINI.md` 중 요청된 파일만 다루며 기존 사용자 설정을 보존한다.

**트리거 예시:**
- "새 프로젝트 시작할게", "세션 시작", "에이전트 설정해줘"
- "CLAUDE.md 만들어줘", "AGENTS.md 만들어줘", "GEMINI.md 만들어줘"
- "venv 설정해줘", "context setup"
- "맥락 관리 규칙 넣어줘", "state.md"

**호출 시점 (명확한 기준):**

| 상황 | 호출 이유 |
|------|----------|
| **프로젝트 최초 설정이 필요할 때** | 기존 규약과 실행 환경을 확인해 필요한 설정만 생성 |
| **기존 프로젝트에 새 에이전트 추가 시** | 새 에이전트용 설정 파일 생성 필요 |
| **설정 파일이 현재 규약과 어긋날 때** | 해당 절만 병합·갱신 |
| **설정 파일에 '긴 작업 규칙(맥락 관리)'이 없을 때** | 그 섹션만 추가 |

**스킬 동작:**
1. 기존 설정·프로젝트 규칙·실행 환경을 먼저 탐색한다.
2. 필요한 Python 경로를 환경에서 확인하고, 진행에 꼭 필요한 정보만 없을 때 질문한다.
3. 필요한 인증 변수 이름만 기록한다. API 키 값은 질문하거나 설정·상태 파일에 저장하지 않는다.
4. 요청된 설정 파일에 현재 규칙과 실제 정본 경로를 병합한다.

**입력 → 출력:**
```
기존 설정 + 탐색한 환경·정본 경로 + 필요한 인증 변수 이름
  → 요청된 CLAUDE.md / AGENTS.md / GEMINI.md만 생성·병합
```

**긴 작업의 맥락 관리:** 재개가 필요한 작업만 프로젝트가 정한 위치의 상태 파일에 범위·결정·남은 일·증거 경로를 남긴다.
긴 요청이라는 이유로 새 chat을 자동 생성하지 않는다. 독립적인 읽기·탐침만 worker에 맡기고,
짧은 결과는 메시지로 받을 수 있으며 장기 재개에 필요한 결과만 파일로 보존한다.

**주의:** `GLOBAL_RULES.md`가 없어도 현재 요청과 기존 규약으로 수행할 수 있는 독립 작업은 진행한다.
규칙 파일 생성은 요청 범위에 있을 때만 수행한다.

**파이프라인 내 위치:**
```
프로젝트 시작 → [context-engineering: 에이전트 설정 파일 생성]
     ↓
req-elicitor → if-designer → uf-designer → uf-implementor → ...
```

---

## 빠른 시작 — 새 프로젝트 체크리스트

```
□ 0. 필요하면 context-engineering 실행 → 요청된 설정 파일만 생성·병합
□    기존 정본·환경을 먼저 확인하고 요청에 필요한 아래 단계만 선택
□ 1. 문제를 자연어로 설명한다
□ 2. req-elicitor 실행 → 명확화 질문 답변
□ 3. if-designer 실행
□ 4. uf-designer 실행 → uf-chain-validator로 커버리지 확인
□ 5. (도메인 해당 시) specific_skills 감사 스킬 투입
□ 6. uf-implementor 실행
□ 7. if-integrator 실행
□ 8. uf-chain-validator 최종 검증
□ 9. eval-planner → exp-runner(실험 실행·기록) → eval-runner 실행
□ 10. ci-evidence-automation 구성
□ 11. project-summarizer로 완료 문서 생성
```
