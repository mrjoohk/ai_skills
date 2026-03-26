# AI 개발 파이프라인 매뉴얼

> Claude + Cursor를 연결하는 6단계 자동화 파이프라인

---

## 파이프라인 전체 구조

```
1️⃣ Claude (req-elicitor + if-designer)
   "요구사항 뽑아줘" → requirements.md, if_list.md
         ↓
2️⃣ Claude (uf-designer)
   "UF 설계해줘" → uf.md (태스크 분해)
         ↓
3️⃣ Claude (repo-doc-writer)  ← 신규
   "docs 써줘" → /docs/ai/overview.md, /docs/ai/tasks/*.md
         ↓
4️⃣ Claude (cursor-task-formatter)  ← 신규
   "Cursor 프롬프트 만들어줘" → 붙여넣기용 Cursor 프롬프트
         ↓
   [Cursor Composer에서 구현]
         ↓
5️⃣ Claude (code-reviewer)  ← 신규
   "코드 리뷰해줘" → review_report.md (CRITICAL / WARN / SUGGEST)
         ↓
6️⃣ Claude (cursor-task-formatter, Mode B)
   "fix 프롬프트 만들어줘" → Cursor 수정 프롬프트
         ↓
   [Cursor Composer에서 수정]
         ↓
   ✅ 완료
```

---

## 사용 스킬 목록

| 단계 | 스킬 | 트리거 예시 |
|---|---|---|
| 1️⃣ Requirements | `req-elicitor` | "요구사항 뽑아줘", "REQ 써줘" |
| 1️⃣ Architecture | `if-designer` | "IF 설계해줘", "시스템 경계 잡아줘" |
| 2️⃣ Task Breakdown | `uf-designer` | "UF 설계해줘", "UF 블록 만들어줘" |
| 3️⃣ Repo Docs | **`repo-doc-writer`** | "docs 써줘", "Cursor용 문서 만들어줘" |
| 4️⃣ Cursor Prompts | **`cursor-task-formatter`** | "Cursor 프롬프트 만들어줘", "구현 지시서 써줘" |
| 5️⃣ Code Review | **`code-reviewer`** | "코드 리뷰해줘", "구현 검토해줘" |
| 6️⃣ Fix Prompts | **`cursor-task-formatter`** | "fix 프롬프트 만들어줘" |

굵은 글씨 3개가 이번에 새로 추가된 스킬이다.

---

## 단계별 상세 사용법

---

### Step 1️⃣ — Requirements + Architecture

**목적:** 자연어 문제 설명을 기계가 읽을 수 있는 설계 아티팩트로 변환

**사용 스킬:** `req-elicitor` → `if-designer`

**대화 예시:**
```
나: 우리 앱에 실시간 알림 시스템을 추가하고 싶어. 설계 시작해줘.

Claude: [req-elicitor 실행]
       → problem_statement.md 작성
       → 명확화 질문 4-6개 제시

나: (질문 답변)

Claude: → requirements.md 완성 (REQ 블록)

나: IF 설계해줘.

Claude: [if-designer 실행]
       → if_list.md (IF 경계 정의)
       → if_decomposition.md (UF 후보 트리)
```

**산출물:**
- `requirements.md` — REQ 블록 + 인수 기준
- `if_list.md` — IF 목록 + I/O 계약
- `if_decomposition.md` — IF→UF 분해 트리

---

### Step 2️⃣ — Task Breakdown

**목적:** IF를 Cursor가 구현할 수 있는 단위 함수(UF)로 분해

**사용 스킬:** `uf-designer`

**대화 예시:**
```
나: UF 설계해줘.

Claude: [uf-designer 실행]
       → uf.md 생성
         (각 UF마다: 시그니처, I/O 계약, 엣지 케이스, 검증 기준)
```

**산출물:**
- `uf.md` — UF 블록 전체 (구현 전 최종 스펙)

---

### Step 3️⃣ — Repo Docs  🆕

**목적:** 설계 아티팩트를 Cursor가 바로 읽을 수 있는 `/docs/ai/` 구조로 변환

**사용 스킬:** `repo-doc-writer`

**대화 예시:**
```
나: docs 써줘. Cursor가 읽을 수 있게 레포에 저장해줘.

Claude: [repo-doc-writer 실행]
       → 아티팩트 스캔 (requirements.md, if_list.md, uf.md)
       → docs/ai/overview.md 작성
       → docs/ai/architecture.md 작성 (mermaid 다이어그램)
       → docs/ai/tasks/UF-01.md 작성
       → docs/ai/tasks/UF-02.md 작성
       → ...
       → validate_docs.sh 실행 → ✓ 검증 통과
```

**산출물:**
```
docs/ai/
├── overview.md        ← 시스템 목적 + IF 목록
├── architecture.md    ← 의존성 다이어그램
└── tasks/
    ├── UF-01.md       ← Cursor 태스크 파일
    ├── UF-02.md
    └── ...
```

**Cursor에서 사용법:**
Cursor Composer의 Context에 `docs/ai/` 폴더 전체를 추가한다.

---

### Step 4️⃣ — Cursor Composer 구현  🆕

**목적:** UF 스펙을 Cursor에 붙여넣을 수 있는 프롬프트로 변환

**사용 스킬:** `cursor-task-formatter`

**대화 예시:**
```
나: Cursor 프롬프트 만들어줘. UF-01부터 UF-03까지.

Claude: [cursor-task-formatter 실행, Mode A]
       → Cursor Composer 프롬프트 3개 생성

       ```cursor-prompt
       Working on notification-system. Implement UF-01 (parse_event)
       in `src/notifications/parser.py`.
       ...
       Verify by: pytest tests/test_parser.py
       ```

       ```cursor-prompt
       Working on notification-system. Implement UF-02 (route_event)
       ...
       ```

       ## Handoff Checklist
       - [ ] docs/ai/tasks/ 파일 최신 상태 확인
       - [ ] 프롬프트 순서대로 하나씩 실행
       - [ ] 각 구현 후 Verify 스텝 실행
       - [ ] 전체 완료 후 code-reviewer 실행
```

**Cursor에서 실행:**
1. 프롬프트를 하나씩 복사해서 Cursor Composer에 붙여넣기
2. 각 태스크 완료 후 "Verify by:" 스텝 확인
3. 다음 프롬프트로 이동

---

### Step 5️⃣ — Code Review  🆕

**목적:** Cursor가 구현한 코드를 UF 계약 + 로직 정확성 + 코드 품질로 검토

**사용 스킬:** `code-reviewer`

**대화 예시:**
```
나: src/notifications/ 코드 리뷰해줘. uf.md 기준으로.

Claude: [code-reviewer 실행]
       → 계약 준수 검토 (시그니처, I/O, 엣지 케이스)
       → 로직 정확성 검토
       → 코드 품질 검토

       # Code Review Report

       ### [CRITICAL] FINDING-1: route_event가 None 입력 처리 안 함
       - File: `src/notifications/router.py`, Line: 23-31
       - Issue: event=None일 때 AttributeError 발생
       - Fix: 함수 진입 시 `if event is None: raise ValueError(...)` 추가

       ### [WARN] FINDING-2: 테스트에 빈 payload 케이스 누락
       ...

       Summary: 1 critical, 2 warnings, 1 suggestion — NEEDS WORK
```

**산출물:**
- `review_report.md` — 우선순위별 개선 사항

---

### Step 6️⃣ — Cursor Fix / Refactor  🆕

**목적:** 리뷰 결과를 Cursor 수정 프롬프트로 변환

**사용 스킬:** `cursor-task-formatter` (Mode B)

**대화 예시:**
```
나: 리뷰 결과로 Cursor fix 프롬프트 만들어줘.

Claude: [cursor-task-formatter 실행, Mode B]

       ```cursor-prompt
       Fix the following issue in `src/notifications/router.py` (lines 23-31).

       Issue: event=None 입력 시 AttributeError 발생
       Current behavior: None.type 접근으로 크래시
       Expected behavior: ValueError 발생 with 메시지 "event must not be None"

       Do not change the route_event signature.

       Verify by: pytest tests/test_router.py::test_none_event
       ```
```

**Cursor에서 실행:**
- CRITICAL → WARN 순으로 fix 프롬프트 순차 실행
- 각 수정 후 verify 스텝 확인
- 완료 후 Step 5로 돌아가 재검토 (PASS 나올 때까지)

---

## 전체 흐름 요약 (체크리스트)

```
□ 1. "설계 시작해줘" → req-elicitor → if-designer
□ 2. "UF 설계해줘" → uf-designer
□ 3. "docs 써줘" → repo-doc-writer → docs/ai/ 생성
□ 4. "Cursor 프롬프트 만들어줘" → cursor-task-formatter
□ 5. Cursor Composer에서 태스크 순차 실행
□ 6. "코드 리뷰해줘" → code-reviewer
□ 7. "fix 프롬프트 만들어줘" → cursor-task-formatter (Mode B)
□ 8. Cursor Composer에서 수정 순차 실행
□ 9. 리뷰 재실행 → "Summary: 0 critical" 확인
□ 10. PR / 머지
```

---

## 스킬 설치

아래 `.skill` 파일 3개를 Claude 앱에 설치한다:

1. `repo-doc-writer.skill`
2. `cursor-task-formatter.skill`
3. `code-reviewer.skill`

설치 방법: Claude 앱 → Settings → Skills → Install from file

---

## FAQ

**Q. Step 3을 꼭 해야 하나요? uf.md 있으면 바로 Step 4 가면 안 되나요?**
A. 가능하다. 단, repo-doc-writer를 거치면 Cursor가 `/docs/ai/tasks/` 파일을 Context로 추가할 수 있어 구현 정확도가 높아진다. 특히 UF가 5개 이상일 때 효과가 크다.

**Q. Cursor 프롬프트는 몇 개씩 실행해야 하나요?**
A. 반드시 하나씩 순차 실행한다. 같은 파일을 수정하는 UF들은 앞 것이 완료된 후 다음 것을 실행해야 충돌이 없다.

**Q. code-reviewer가 CRITICAL을 못 찾으면 어떻게 하나요?**
A. `uf.md`를 함께 제공하면 계약 기반 리뷰가 가능해져 누락이 줄어든다. "코드 리뷰해줘. uf.md 기준으로." 라고 명시적으로 요청한다.

**Q. 기존 스킬들(uf-chain-validator, uf-if-debug-mapper)은 언제 쓰나요?**
A. uf-chain-validator는 Step 2 직후 UF 설계 자체의 정합성 검증용이다. code-reviewer는 구현 코드 리뷰용이므로 역할이 다르다. uf-if-debug-mapper는 Step 6에서 수정 후에도 버그가 반복될 때 사용한다.
