# Req → Impl → Review Pipeline Skills — 스킬 연동 사용 매뉴얼

> **디렉토리 목적:** Claude와 Cursor를 연결하는 AI 협업 개발 파이프라인.
> 요구사항 정의부터 설계, Cursor 구현 지시, 코드 리뷰, 수정까지 6단계로 개발 주기를 자동화한다.

---

## 포함 스킬 목록

| 스킬 | 단계 | 역할 |
|------|------|------|
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
- `if_decomposition.md` (UF 후보 트리)

---

### Step 2 — Task Breakdown (uf-designer)

**목적:** IF 분해 트리의 각 리프 노드를 구현 가능한 UF 명세로 정형화.

**트리거 예시:**
- "UF 설계해줘", "UF 블록 만들어줘", "태스크 분해해줘"

**산출물:**
- `uf.md` (UF 블록 전체: 알고리즘 요약 + I/O 계약 + 엣지케이스 + 검증 계획)

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
uf.md + src/ + tests/ + evidence_pack/
  → validation_report.md (PASS/FAIL + 누락 링크 목록)
```

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

---

## 빠른 시작 체크리스트

```
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
