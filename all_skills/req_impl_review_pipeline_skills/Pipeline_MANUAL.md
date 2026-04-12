# Req → Impl → Review Pipeline Skills — 스킬 연동 사용 매뉴얼

> **디렉토리 목적:** Claude와 Cursor를 연결하는 AI 협업 개발 파이프라인.
> 요구사항 정의부터 설계, Cursor 구현 지시, 코드 리뷰, 수정까지 6단계로 개발 주기를 자동화한다.

---

## 포함 스킬 목록

| 스킬 | 단계 | 역할 |
|------|------|------|
| `context-engineering` | 프로젝트 시작 | 에이전트 설정 파일 생성 (CLAUDE.md / AGENTS.md / GEMINI.md) |
| `req-elicitor` | 1 | 자연어 문제 → 요구사항 아티팩트 |
| `if-designer` | 1 | 요구사항 → IF 경계·분해 설계 |
| `uf-designer` | 2 | IF 분해 → UF 블록 명세 |
| `repo-doc-writer` | 3 | 설계 아티팩트 → Cursor용 /docs/ai 문서화 |
| `cursor-task-formatter` | 4·6 | UF 블록 or 리뷰 결과 → Cursor 프롬프트 |
| `code-reviewer` | 5 | Cursor 구현 결과 코드 리뷰 |
| `uf-chain-validator` | 검증 | UF 체인 무결성 + I/O 계약 검증 |
| `uf-if-debug-mapper` | 디버깅 | UF/IF 이슈 → 코드 위치 맵 + 디버깅 플랜 |
| `project-summarizer` | 완료 | 전 과정 요약 문서 생성/갱신 |

---

## 전체 파이프라인 흐름

```
[자연어 문제 기술]
        ↓
① Claude: req-elicitor ─────────────────────────────────
          requirements.md, if_list.md
        ↓
② Claude: uf-designer ──────────────────────────────────
          uf.md (태스크 분해)
        ↓
   [도메인 특화 감사 투입 시점 — specific_skills 참조] ★
        ↓
③ Claude: repo-doc-writer ──────────────────────────────
          /docs/ai/overview.md, /docs/ai/tasks/*.md
        ↓
④ Claude: cursor-task-formatter (Mode A: 구현 프롬프트) ─
          Cursor Composer 붙여넣기용 프롬프트
        ↓
   ════════════════════════════════
   [Cursor Composer에서 구현]
   ════════════════════════════════
        ↓
⑤ Claude: code-reviewer ───────────────────────────────
          review_report.md (CRITICAL / WARN / SUGGEST)
        ↓
⑥ Claude: cursor-task-formatter (Mode B: fix 프롬프트) ─
          Cursor Composer 수정용 프롬프트
        ↓
   ════════════════════════════════
   [Cursor Composer에서 수정]
   ════════════════════════════════
        ↓
   (⑤→⑥ 사이클: 리뷰 통과까지 반복)
        ↓
⑦ Claude: uf-chain-validator ──────────────────────────
          최종 UF 체인 검증
        ↓
⑧ Claude: project-summarizer ──────────────────────────
          project_summary.md
```

---

## 단계별 사용 방법

### Step 1 — Requirements + Architecture (req-elicitor → if-designer)

**목적:** 자연어 문제 설명을 기계가 읽을 수 있는 설계 아티팩트로 변환.

**트리거 예시:**
- "요구사항 뽑아줘", "설계 시작해줘", "REQ 써줘"
- 기능 설명 후 "IF 설계해줘"

**실행 순서:**
```
req-elicitor → (명확화 Q&A 완료) → requirements.md 확정
    ↓
if-designer → if_list.md + if_decomposition.md
```

**산출물:**
- `requirements.md` (REQ 블록)
- `if_list.md` (IF 경계 + I/O 계약)
- `if_decomposition.md` (UF 후보 트리 + 각 리프 노드의 `Verification Owner` 선언)

**v2 변경사항:** `if_decomposition.md`의 각 리프 노드에 `Verification Owner` 필드 추가
(`UF-local` / `guard-rail+chain` / `IF-acceptance`). 모든 리프가 독립 테스트 가능해야 한다는
이전 가정 폐기.

**v2.1 변경사항 — 계약 설계 원칙 추가 (if-designer):**
- **Hyrum's Law 적용:** IF Output Contract 노출 필드는 다운스트림이 암묵적으로 의존할 수 있음 인식 → 최소 노출 설계
- **추가 우선 원칙:** 기존 IF 계약 수정 시 기존 필드 삭제/변경 금지, 선택적 추가만 허용
- **에러 시맨틱 통일:** 모든 IF Failure Modes는 동일한 에러 표현 방식 사용

---

### Step 2 — Task Breakdown (uf-designer)

**목적:** IF 분해 트리의 각 리프 노드를 구현 가능한 UF 명세로 정형화.

**트리거 예시:**
- "UF 설계해줘", "UF 블록 만들어줘", "태스크 분해해줘"

**산출물:**
- `uf.md` (UF 블록 전체: 알고리즘 요약 + I/O 계약 + 엣지케이스 + 검증 계획)
- `uf_split/uf_if01.md`, `uf_split/uf_if02.md`, … (IF별 UF 블록 동반 파일)

**v2 변경사항:**
- `Verification Plan` 구조 개편: `Ownership` / `Unit Verification` / `Chain Verification` 3개 서브 필드
- `UF-local`: 독립 테스트 경로 + 커버리지 목표 필수
- `guard-rail+chain`: 가드레일 테스트 + IF-체인 테스트 경로 필수, 독립 기능 테스트 불필요
- `IF-acceptance`: IF-인수 테스트 경로만 필수
- IF별 `uf_split/` 동반 파일 생성 추가

---

### ★ 도메인 특화 감사 투입 시점 (specific_skills)

> `uf.md` 완성 직후, `repo-doc-writer` 실행 전.
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

### Step 3 — Repo Documentation (repo-doc-writer)

**목적:** 설계 아티팩트를 Cursor가 구현 컨텍스트로 직접 읽을 수 있는 `/docs/ai` 문서로 변환.
         이 단계 없이 Cursor에 직접 설계 파일을 넘기면 컨텍스트 품질이 낮아진다.

**트리거 예시:**
- "docs 써줘", "Cursor용 문서 만들어줘", "/docs/ai 업데이트"
- "repo에 설계 문서 반영해줘"

**입력 → 출력:**
```
requirements.md + if_list.md + if_decomposition.md + uf.md
  → /docs/ai/overview.md
  → /docs/ai/tasks/*.md (UF별 구현 컨텍스트)
```

---

### Step 4 — Cursor Implementation Prompts (cursor-task-formatter Mode A)

**목적:** UF 블록을 Cursor Composer에 붙여넣기만 하면 구현이 시작되는 자기완결형 프롬프트로 변환.

**트리거 예시:**
- "Cursor 프롬프트 만들어줘", "구현 지시서 써줘"
- "Cursor에 넘겨줄 내용 만들어줘"

**입력 → 출력:**
```
uf.md + /docs/ai 문서
  → UF별 Cursor Composer 프롬프트 (자기완결형, 붙여넣기용)
```

---

### [Cursor 구현 단계]

Cursor Composer에 Step 4의 프롬프트를 붙여넣고 구현을 실행한다.
구현 완료 후 Claude로 돌아와 Step 5를 진행한다.

---

### Step 5 — Code Review (code-reviewer)

**목적:** Cursor가 구현한 코드를 UF/IF 계약, 로직 정확성, 코드 품질 기준으로 구조적 리뷰.

**트리거 예시:**
- "코드 리뷰해줘", "구현 검토해줘"
- "버그 찾아줘", "리뷰해줘"

**입력 → 출력:**
```
구현 코드 (src/) + uf.md + if_list.md
  → review_report.md
    - CRITICAL: 계약 위반, 로직 오류 (즉시 수정 필요)
    - WARN: 품질 문제 (수정 권장)
    - SUGGEST: 개선 아이디어 (선택)
```

---

### Step 6 — Fix Prompts (cursor-task-formatter Mode B)

**목적:** 리뷰 발견사항을 Cursor가 바로 수정할 수 있는 fix 프롬프트로 변환.

**트리거 예시:**
- "fix 프롬프트 만들어줘", "수정 지시서 써줘"

**입력 → 출력:**
```
review_report.md
  → CRITICAL/WARN 항목별 Cursor fix 프롬프트
```

> ⑤→⑥ 사이클은 CRITICAL 항목이 모두 해소될 때까지 반복한다.

---

### Step 7 — 최종 검증 (uf-chain-validator)

**목적:** 모든 수정 완료 후 UF 체인 전체 무결성 최종 확인.

**트리거 예시:**
- "최종 검증해줘", "UF 체인 확인해줘", "merge 전에 검사해줘"

**입력 → 출력:**
```
uf.md + if_list.md + src/ + tests/ + evidence_pack/
  → validation_report.md (3개 게이트별 PASS/FAIL/WARN + 제안 수정)
```

**v2 변경사항 — 3-Gate 구조:**

| 게이트 | 검증 내용 |
|--------|-----------|
| **Gate 1** 구현/런타임 | I/O 계약, 체인 연속성, 런타임 스모크 테스트 |
| **Gate 2** 문서-테스트 정합 | Ownership 선언 완결성, 소유권별 테스트 경로 존재 여부 |
| **Gate 3** 증거 팩 완결성 | 증거 항목 누락, `uf_split/` 동기화 |

**중요:** `guard-rail+chain` / `IF-acceptance` UF에 독립 기능 테스트가 없어도 자동 FAIL 아님.

**v2.1 변경사항 — 테스트 품질 체크 추가:**
- **Beyonce Rule:** 기존 UF 수정 시 테스트 커버리지 감소 → WARN
- **테스트 품질 WARN:** 비서술적 테스트명, 구현 내부 동작 검증, 단일 테스트에 여러 개념 혼합

---

### Step 8 — 완료 정리 (project-summarizer)

**목적:** 전 개발 주기 기록을 핵심 중심으로 압축. 다음 스프린트 시작 시 컨텍스트 복원에 활용.

**트리거 예시:**
- "프로젝트 정리해줘", "지금까지 한 일 요약해줘"
- "개발 과정 문서화해줘", "스프린트 회고 만들어줘"

**입력 → 출력:**
```
대화 히스토리 + 설계 산출물 + 구현 결과
  → project_summary.md (누적 갱신)
```

**v2.1 변경사항 — Key Decisions 섹션 추가:**
- **What이 아닌 Why 기록:** 결정 사항에 이유 + 기각 대안 필수 포함
- **Key Decisions 표 필수:** `결정 | 선택 | 기각 대안 | 이유` 형식
- 기록 기준: 두 가지 이상 접근법 비교, IF 경계 변경, 알고리즘 교체, 예상치 못한 제약으로 설계 변경

---

## 디버깅 발생 시 — uf-if-debug-mapper

파이프라인 어느 단계에서든 UF/IF 관련 오류가 발생하면 투입.

**트리거 예시:**
- "어디를 디버깅해야 해?", "런타임 에러 디버깅 플랜 짜줘"
- "CI 실패했어, 어디가 문제야?"

**입력 → 출력:**
```
UF/IF 목록 + 에러 로그 + 모듈 레이아웃
  → 디버깅 가이드 (코드 위치 맵 + 최소 수정 제안 + 검증 방법)
```

**v2.1 변경사항 — 구조적 트리아지 추가:**
- **Stop-the-Line Rule:** 오류 발생 즉시 중단 → 증거 보존 → 5단계 트리아지 진행
- **5단계:** Reproduce → Localize (UF/IF 레이어 특정) → Reduce → Fix Root Cause → Guard
- **근본 원인 수정:** 증상 수정 금지, UF→UF 경계의 I/O 불일치까지 추적
- **Guard 단계:** 재발 방지 테스트 추가 후 uf-chain-validator 재실행

---

---

## 컨텍스트 관리 — context-engineering

새 프로젝트 또는 새 세션 시작 시 **에이전트 설정 파일 3종**을 생성하는 스킬.
Claude / Cursor / Codex / Antigravity 등 어떤 에이전트를 사용하더라도 동일하게 작동한다.

**트리거 예시:**
- "새 프로젝트 시작할게", "세션 시작", "에이전트 설정해줘"
- "CLAUDE.md 만들어줘", "AGENTS.md 만들어줘", "GEMINI.md 만들어줘"
- "venv 설정해줘", "context setup"

**호출 시점 (명확한 기준):**

| 상황 | 호출 이유 |
|------|----------|
| **프로젝트 최초 시작 (저장소 clone 직후)** | 에이전트 설정 파일이 없으면 에이전트가 규칙과 경로를 모름 |
| **기존 프로젝트에 새 에이전트 추가 시** | 새 에이전트용 설정 파일 생성 필요 |
| **설정 파일이 GLOBAL_RULES.md 최신 내용을 반영 못할 때** | 재생성으로 동기화 |

**스킬 동작:**
1. 사용자에게 venv Python 실행파일 경로 요청
2. 사용자에게 API 키 요청 (선택)
3. 수집한 정보 + GLOBAL_RULES.md 준수 지시 + 핵심 아티팩트 경로로 3개 파일 생성

**입력 → 출력:**
```
venv Python 경로 + API 키 (선택)
  → ./CLAUDE.md   (Claude용)
  → ./AGENTS.md   (Codex / Antigravity 등)
  → ./GEMINI.md   (Gemini용)
```

**주의:** context-engineering은 GLOBAL_RULES.md를 생성하지 않는다.
GLOBAL_RULES.md는 req-elicitor 또는 별도 수동 작업으로 생성한다.

**파이프라인 내 위치:**
```
프로젝트 시작 → [context-engineering: 에이전트 설정 파일 생성]
     ↓
req-elicitor → if-designer → uf-designer → repo-doc-writer
     ↓
cursor-task-formatter → Cursor 구현 → code-reviewer → ...
```

---

## 빠른 시작 체크리스트

```
□ 0. context-engineering 실행 → CLAUDE.md / AGENTS.md / GEMINI.md 생성
□    (GLOBAL_RULES.md 미존재 시 수동 작성 또는 req-elicitor 이후 작성)
□ 1. 기능을 자연어로 설명한다
□ 2. req-elicitor 실행 → 명확화 질문 답변
□ 3. if-designer 실행
□ 4. uf-designer 실행
□ 5. (도메인 해당 시) specific_skills 감사 스킬 투입
□ 6. repo-doc-writer 실행
□ 7. cursor-task-formatter (Mode A) → Cursor 구현
□ 8. code-reviewer 실행
□ 9. cursor-task-formatter (Mode B) → Cursor 수정 (CRITICAL 해소까지 반복)
□ 10. uf-chain-validator 최종 검증
□ 11. project-summarizer로 완료 문서 생성
```

---

## core-engineering_pipeline_skills와의 차이점

| 항목 | core-engineering | req_impl_review |
|------|-----------------|-----------------|
| 구현 주체 | Claude (`uf-implementor`) | Cursor Composer |
| 브리지 스킬 | 없음 | `repo-doc-writer` + `cursor-task-formatter` |
| 리뷰 방식 | `uf-chain-validator` | `code-reviewer` + `cursor-task-formatter` |
| 평가 단계 | `eval-planner` + `eval-runner` | 별도 연계 가능 |
| 적합한 상황 | 설계 중심, 문서화 강조 | 빠른 구현 + 코드 품질 검토 |
