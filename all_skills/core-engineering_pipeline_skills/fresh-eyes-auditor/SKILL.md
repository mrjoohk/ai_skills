---
name: fresh-eyes-auditor
description: >
  Spawns a NEW context-free verification agent to audit the work done so far for
  ambiguity (모호함), forced logic (억지), errors (오류), and hallucination (환각) —
  then triages the fresh agent's findings by verifying every citation before accepting.
  The session agent that produced the work never reviews it directly (confirmation-bias
  guard); it only assembles the file manifest, spawns the clean agent, and triages.
  MANDATORY TRIGGERS: "모호함, 억지, 오류, 환각 없는지 검토해줘", "지금까지 설계 검토해줘",
  "지금까지 구현 검토해줘", "새 에이전트로 검토", "독립 검증해줘", "무맥락 검토",
  "신선한 눈으로 봐줘", "fresh eyes review", "제3자 시각으로 검토", "환각 없는지 확인",
  "억지 논리 없는지 봐줘". Boundary: mechanical contract/test validation is
  uf-chain-validator; code-quality 3-lens review is code-reviewer; THIS skill is the
  epistemic audit (ambiguity/forced-logic/error/hallucination) run by a context-free agent.
user-invocable: true
allowed-tools: Read, Write, Agent, WebSearch, WebFetch
---

# Fresh-Eyes Auditor — 무맥락 에이전트 기반 인식론적 감사

작업을 만든 세션 에이전트는 자기 작업 검증에 확증 편향을 가진다. 이 스킬은
**대화 맥락이 없는 새 에이전트**를 스폰하여 산출물을 파일만으로 감사하게 하고,
본 에이전트는 그 발견을 **인용 검증(트리아지)** 한 뒤에만 채택한다.

```
본 에이전트: [Step 0 범위 확정] → [Step 1 무맥락 에이전트 스폰] → [Step 2 트리아지] → [Step 3 자문 리포트]
                                        ↑ 오염 방지: 파일 경로+루브릭+출력 형식만 전달
fresh agent: 파일만 읽고 4축(모호함·억지·오류·환각) 감사 → file:line 인용 발견 반환
```

**성격: 자문(advisory) 전용.** 파이프라인을 차단(BLOCKED)하지 않는다. CRITICAL이
채택되면 "후속 단계 전 해소 권고"만 발령한다.

> **Read `references/reference.md`** — 스폰 프롬프트 템플릿(그대로 사용), 4축 루브릭,
> 트리아지 결정표, 리포트 템플릿.

---

## Step 0 — 범위 확정 (Scope Resolution)

"지금까지"는 대화가 아니라 **파일 집합**으로 정의한다:

| 상황 | 검토 모드 |
|---|---|
| 사용자가 파일/폴더 지정 | 지정된 것만 |
| 설계 문서 존재 (`rd/*.md` 또는 legacy 루트의 requirements.md/uf.md/eq.md 등) | **Mode A**: ① 설계 문서 자체 감사 + ② (코드 있으면) 설계↔코드 비교 감사 |
| 설계 문서 없음 | **Mode B**: 소스 코드(src/, tests/)만 감사 |

- 매니페스트는 **경로 목록**으로만 구성한다. 파일 내용 요약·해설을 덧붙이지 않는다.
- 파일 수가 많으면(>40) 사용자에게 우선순위 하위집합을 확인한다.

## Step 1 — 무맥락 에이전트 스폰

**Agent 도구**(범용 서브에이전트)로 새 에이전트를 생성하고,
`references/reference.md`의 스폰 프롬프트 템플릿을 **그대로** 사용한다.

**오염 방지 규칙 (이 스킬의 핵심 — 위반 시 감사 무효):**
1. 스폰 프롬프트에 넣을 수 있는 것: 파일 경로 매니페스트, 4축 루브릭, 출력 형식,
   웹 검증 정책, 검토 모드(A/B).
2. 넣을 수 없는 것: 본 세션의 요약·결론·의도 설명·"우리가 무엇을 했는지"·기대 결과·
   과거 검토 결과. 파일에 기록된 판단 근거는 파일로서 전달된다(경로만).
3. 새 Agent 호출로 시작한다 — 기존 에이전트 SendMessage 재사용 금지(맥락 보유).

**fresh agent에게 부여되는 규칙(템플릿에 포함):**
- 모든 발견은 `file:line + 원문 인용` 필수. 인용 없는 발견은 무효.
- 정보 부족으로 판정 불가하면 추측하지 말고 `UNVERIFIABLE`로 보고.
- 웹 검증은 **출처 주장(논문·교과서 식 번호·Source 필드)과 외부 수치 주장에 한정**
  (WebSearch로 실재·값 대조). 그 외는 파일 내부 교차 검증만.
- 산출: 발견 목록 {ID, 축, 심각도(CRITICAL/WARN/INFO), file:line, 인용, 설명, 제안}.

## Step 2 — 트리아지 (본 에이전트, 검증자의 환각 방어)

fresh agent의 발견 자체가 환각일 수 있다. 발견마다 순서대로:

| 검사 | 통과 못 하면 |
|---|---|
| ① 인용 실재: file:line이 존재하고 인용문이 실제 내용과 일치하는가 | `REJECTED-MISQUOTE` (검증자 환각 — 기록) |
| ② 근거 기재: 파일 안의 판단 근거·가정 기록이 이미 해당 지적을 해명하는가 | `REJECTED-JUSTIFIED` (해명 위치 인용) |
| ③ 실질성: 지적이 수정 가능한 실제 결함인가 (스타일 취향 아님) | `REJECTED-TRIVIAL` |
| 모두 통과 | `ACCEPTED` |

- 본 에이전트의 세션 맥락 사용은 **이 단계에서만 허용**된다(②의 해명 탐색 등).
  단, 기각 사유는 반드시 **파일 인용**으로 뒷받침한다 — "내가 알기로는" 금지.
- 모든 채택/기각에 판단 근거 명시 (GLOBAL_RULES Rule 3).

## Step 3 — 자문 리포트

`review_docs/YYMMDD_HHMM_fresh_eyes_audit.md` 생성 (Rule 6; 텍스트 중심 → .md):

- 범위·모드, 발견 통계 (축×심각도)
- ACCEPTED 발견 (축별, file:line 인용, 권고 조치 포함)
- REJECTED 발견 + 기각 사유 (검증자 오탐 기록도 데이터다)
- UNVERIFIABLE 목록 (결함이 아님 — 정보 부족 항목, 사용자 확인 요청)
- 후속 라우팅 권고: 설계 결함→해당 설계 스킬(req-elicitor/if-designer/uf-designer/
  theory-decomposer), 코드 결함→uf-implementor(수정) 또는 code-reviewer, 물리·단위→
  sim-physics-auditor, 계약·테스트→uf-chain-validator
- CRITICAL ACCEPTED 존재 시: "권고: 후속 단계 진행 전 해소" (차단 아님)

Rule 4/8 로그 기록 후 사용자에게 제시.

---

## Rules

1. 스폰 프롬프트에 세션 해석을 주입하지 않는다 — 경로+루브릭+형식만.
2. 인용 없는 발견은 트리아지 진입 전 자동 기각.
3. UNVERIFIABLE은 결함으로 집계하지 않는다 (추측 금지 원칙의 정상 산출).
4. 이 스킬은 **수정하지 않는다** — 검토자와 수정자 분리, 라우팅만 제시.
5. 자문 전용: BLOCKED를 발령하지 않는다.
6. 반복 실행 시 이전 감사 리포트를 fresh agent에게 주지 않는다 (앵커링 방지).
   트리아지 단계에서만 이전 리포트와 대조해 재발/해소 여부를 표기한다.

## Fallback

Agent 도구가 없는 환경에서는 `ag-orchestration`/`ag-agent-executor`(파일 기반 메시지
전달)로 대체한다: 스폰 프롬프트를 역할 파일로 저장 → 별도 세션이 수행 → 결과 파일 회수.

---

## Bundled Resources

| Resource | When to use |
|---|---|
| `references/reference.md` | 스폰 프롬프트 템플릿(verbatim), 4축 루브릭 상세, 트리아지 결정표, 리포트 템플릿 |
| `references/README_kr.md` | 한국어 사용 가이드 |
