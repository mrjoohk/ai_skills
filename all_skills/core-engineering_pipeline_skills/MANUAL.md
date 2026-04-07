# Core Engineering Pipeline Skills — 스킬 연동 사용 매뉴얼

> **디렉토리 목적:** 자연어 문제 기술에서 검증된 코드 산출물까지, 소프트웨어 엔지니어링 전 주기를
> 구조화된 아티팩트(문서 + 코드 + 증거)로 연결하는 파이프라인 스킬 묶음.

---

## 포함 스킬 목록

| 스킬 | Stage | 역할 |
|------|-------|------|
| `core-engineering` | 전체 | 파이프라인 전체 규칙 정의 (마스터 레퍼런스) |
| `req-elicitor` | 1–4 | 문제 정의 → 요구사항 도출 |
| `if-designer` | 5–6 | IF 경계 설계 → UF 후보 분해 |
| `uf-designer` | 7 | UF 블록 명세 정의 |
| `uf-implementor` | 구현 | UF 블록 → 프로덕션 코드 + 유닛 테스트 |
| `if-integrator` | 통합 | UF → IF 수준 통합 모듈 조립 |
| `uf-chain-validator` | 검증 | UF 체인 무결성 + I/O 계약 검증 |
| `uf-if-debug-mapper` | 디버깅 | UF/IF 이슈 → 코드 위치 매핑 + 디버깅 플랜 |
| `eval-planner` | 8 | 평가 지표 · 임계값 · 벤치마크 계획 설계 |
| `eval-runner` | 8 | 평가 계획 실행 + 실험 결과 보고서 생성 |
| `ci-evidence-automation` | CI | CI 게이트 · 증거 팩 · 회귀 감지 자동화 |
| `project-summarizer` | 완료 | 프로젝트 진행 전 과정 요약 문서 생성/갱신 |

> `core-engineering` 스킬은 직접 실행하는 스킬이 아니라, 나머지 모든 스킬이 참조하는
> **설계 원칙 문서** 역할을 한다. 파이프라인 시작 전 읽어두는 것을 권장한다.

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
   evaluation_plan.md
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

---

### ③ uf-designer — UF 블록 명세 정의

**언제:** `if_decomposition.md` 완성 직후.

**트리거 예시:**
- "UF 설계해줘", "UF 블록 만들어줘", "uf.md 작성"

**입력 → 출력:**
```
if_decomposition.md
  → uf.md (전체 UF 블록: 알고리즘 요약 + 엣지케이스 + 검증 계획)
```

**중요:** UF 설계 완료 후 `uf-chain-validator`를 1차 실행해 UF→IF 커버리지를 확인한 뒤 구현으로 진행.

---

### ★ 도메인 특화 감사 투입 시점 (specific_skills)

> uf.md가 완성되고 uf-implementor 실행 전후, 또는 if-integrator 단계에서
> 프로젝트 도메인에 따라 `specific_skills` 디렉토리의 감사 스킬을 선택 투입한다.
> **이 스킬들은 파이프라인 구성 스킬이 아니라 선택 투입 감사 스킬이다.**
>
> | 투입 조건 | 권장 스킬 |
> |-----------|-----------|
> | GPU/HPC 연산 포함 UF가 있는 경우 | `gpu-hpc-guard` |
> | 물리 시뮬레이션 방정식이 포함된 경우 | `sim-physics-auditor` |
> | RAG 파이프라인 또는 임베딩 데이터를 다루는 경우 | `rag-data-quality` |
>
> 자세한 사용법은 `specific_skills/MANUAL.md` 참조.

---

### ④ uf-implementor — UF 코드 구현

**언제:** `uf.md` + UF→IF 커버리지 검토 완료 후.

**트리거 예시:**
- "UF 구현해줘", "코드 써줘", "implement UF"

**입력 → 출력:**
```
uf.md (+ uf_if_coverage_review.md 권장)
  → src/uf/*.py (프로덕션 코드 + 독스트링)
  → tests/unit/test_uf_*.py (유닛 테스트)
  → reports/impl/uf_impl_report_*.md
```

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

**트리거 예시:**
- "UF 검증해줘", "체인 검사해줘", "validation 돌려줘"

**입력 → 출력:**
```
uf.md + src/ + tests/ + evidence_pack/
  → validation_report.md (PASS/FAIL + 누락 링크 목록)
```

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

**언제:** 새 UF 모듈 도입 시, CI 구성 정비가 필요할 때.

**트리거 예시:**
- "CI 설정해줘", "evidence pack 만들어줘", "coverage gate 잡아줘"

**입력 → 출력:**
```
.github/workflows/ + test commands + evidence_pack/
  → CI 워크플로우 권장 구성
  → evidence pack 스키마 + 샘플
  → 회귀 임계값 + 알림 템플릿
```

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

---

## 빠른 시작 — 새 프로젝트 체크리스트

```
□ 1. 문제를 자연어로 설명한다
□ 2. req-elicitor 실행 → 명확화 질문 답변
□ 3. if-designer 실행
□ 4. uf-designer 실행 → uf-chain-validator로 커버리지 확인
□ 5. (도메인 해당 시) specific_skills 감사 스킬 투입
□ 6. uf-implementor 실행
□ 7. if-integrator 실행
□ 8. uf-chain-validator 최종 검증
□ 9. eval-planner → eval-runner 실행
□ 10. ci-evidence-automation 구성
□ 11. project-summarizer로 완료 문서 생성
```
