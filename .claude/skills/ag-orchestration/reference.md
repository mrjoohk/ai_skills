# ag-Orchestration Reference

## 1. 파일 명명 규칙

모든 파일은 `ag-workspace/` 를 루트로 하며, 아래 규칙을 따른다.

| 파일 종류 | 경로 패턴 | 생성 주체 |
|---|---|---|
| 역할 파일 | `roles/agent{N}-role.md` | orchestration |
| Task 지시 | `tasks/agent{N}-task-{seq:03d}.md` | orchestration |
| 핸드오프 | `handoffs/agent{N}-handoff-{seq:03d}.md` | agent{N} |
| 결과물 | `results/agent{N}-result-{seq:03d}.md` | agent{N} (최종) |
| 최종 리포트 | `reports/final-report.md` | orchestration |

- `{N}`: 에이전트 번호 (1, 2, 3)
- `{seq:03d}`: 0-padded 3자리 순서 번호 (001, 002, …)

---

## 2. 핸드오프 파일 전체 스펙

에이전트가 오케스트레이션에 보내는 메시지 형식.

```markdown
# Handoff from Agent-{N}

## FROM_AGENT
agent{N}

## SEQ
{대응하는 task의 seq 번호}

## STATUS
PASS                          ← 성공 | FAIL (부분 실패) | BLOCKED (외부 요인)

## SUMMARY
{이번 작업에서 달성한 것 — 1~3 문장으로 간결하게}

## OUTPUTS
- path/to/output1.md
- path/to/output2.py

## ACCEPTANCE_CRITERIA_MET
- [x] {달성된 기준}
- [ ] {미달성 기준 — STATUS==FAIL 시 기입}

## NEXT_AGENT
agent2                        ← 다음 에이전트 번호. 없으면 none

## NEXT_OBJECTIVE
{오케스트레이션에게 제안하는 다음 에이전트의 목표 — 간결하게}

## ISSUES
none                          ← 문제 없으면 none, 있으면 상세 기술

## CONTEXT_FOR_NEXT
{다음 에이전트가 반드시 알아야 할 핵심 컨텍스트}
{예: 생성된 주요 파일 설명, 특이사항, 주의점}
```

### 파싱 규칙
오케스트레이션은 `## {KEY}` 패턴으로 값을 추출한다.
- 각 섹션의 내용은 다음 `##` 헤더 전까지
- `OUTPUTS` 는 `- ` 로 시작하는 줄들을 리스트로 처리
- `STATUS` 는 첫 번째 단어만 유효 (PASS / FAIL / BLOCKED)

---

## 3. Task 파일 전체 스펙

오케스트레이션이 에이전트에게 보내는 지시 형식.

```markdown
# Task for Agent-{N} | seq: {seq}

## FROM
orchestration

## SEQ
{seq}

## OBJECTIVE
{이번 태스크에서 달성해야 할 구체적 목표}

## INPUTS
- {이전 에이전트 outputs 경로}
- {기타 필요한 파일 경로}

## OUTPUTS_EXPECTED
- {생성해야 할 결과물 경로}
- {생성해야 할 결과물 경로}

## ACCEPTANCE_CRITERIA
- {완료 판단 기준 (가능하면 수치 또는 파일 존재 여부로)}

## CONTEXT
{이전 에이전트 결과 요약 및 현재 작업 상태}
{오케스트레이션이 판단한 라우팅 이유 포함}

## DEADLINE_HINT
none                          ← 시간 제약 없으면 none
```

---

## 4. 오케스트레이션 상태 머신

오케스트레이션은 `ag-workspace/` 파일 시스템 상태로 현재 단계를 판단한다.

```
INIT
  │  roles/ 파일 생성 완료
  ▼
TASKS_DISPATCHED
  │  tasks/agent{N}-task-001.md 존재
  ▼
WAITING_HANDOFF
  │  에이전트 작업 중
  ▼
HANDOFF_RECEIVED              ← handoffs/ 에 새 파일 발견
  │
  ├── STATUS==PASS & NEXT_AGENT != none  ──► 다음 에이전트 task 생성 → TASKS_DISPATCHED
  ├── STATUS==PASS & NEXT_AGENT == none  ──► result 파일 확인 → COLLECTING_RESULTS
  ├── STATUS==FAIL & 재시도 가능          ──► 동일 에이전트 재시도 task 생성
  └── STATUS==FAIL & 재시도 불가          ──► ABORTED (사용자에게 보고)

COLLECTING_RESULTS
  │  모든 agent result 파일 존재
  ▼
REPORT_GENERATED              ← reports/final-report.md 생성 완료
```

---

## 5. Final Report 템플릿

```markdown
# ag Orchestration Final Report

**Date:** {날짜}
**Task:** {전체 작업 한 줄 요약}

---

## Execution Summary

| Agent | 역할 | 상태 | 주요 산출물 |
|:---:|---|:---:|---|
| Agent-1 | Architect | ✅ PASS | uf.md, requirements.md |
| Agent-2 | Builder   | ✅ PASS | src/pipeline/... |
| Agent-3 | Verifier  | ✅ PASS | reports/validation.md |

**전체 상태:** ✅ ALL PASS / ⚠️ PARTIAL / ❌ FAIL

---

## 실행 흐름

```
orchestration → Agent-1 (task-001)
Agent-1 → orchestration (handoff-001) [PASS]
orchestration → Agent-2 (task-001)
Agent-2 → orchestration (handoff-001) [PASS]
orchestration → Agent-3 (task-001)
Agent-3 → orchestration (handoff-001) [PASS]
```

---

## 에이전트별 결과

### Agent-1: {역할명}
- **상태:** ✅ PASS
- **산출물:** {파일 경로}
- **요약:** {agent 핸드오프의 SUMMARY}
- **이슈:** none

### Agent-2: {역할명}
...

### Agent-3: {역할명}
...

---

## 최종 산출물 목록

- `{경로}` — {설명}
- `{경로}` — {설명}

---

## 다음 단계 / 권고사항

- {후속 작업 또는 리뷰 필요 항목}
```

---

## 6. 에러 처리 가이드

| 상황 | 오케스트레이션 대응 |
|---|---|
| STATUS: FAIL, 명확한 원인 | ISSUES 분석 → 동일 에이전트에 수정된 task 재발행 (seq 증가) |
| STATUS: FAIL, 원인 불명 | 사용자에게 보고 후 판단 요청 |
| STATUS: BLOCKED | 블로킹 원인 해소 후 재발행 또는 우회 경로 task 생성 |
| 핸드오프 파일 없음 (타임아웃) | 사용자에게 해당 에이전트 세션 확인 요청 |
| ACCEPTANCE_CRITERIA 미달성 | 미달성 항목을 포함한 재시도 task 생성 |
