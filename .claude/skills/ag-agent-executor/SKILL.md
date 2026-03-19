---
name: ag-agent-executor
description: "ag(antigravity) 플랫폼 전용 에이전트 실행 스킬. ag는 서브에이전트 스폰을 지원하지 않으므로, 각 에이전트 세션이 독립적으로 역할을 수행하고 파일로 결과를 전달한다. 에이전트 세션(agent1/2/3)에서만 사용. 'ag 에이전트', 'agent 역할 실행', 'role 파일 읽어서', 'task 실행', '핸드오프 작성' 등의 맥락에서 반드시 이 스킬을 사용한다."
allowed-tools: Read, Write
---

# ag-Agent-Executor Skill (에이전트 세션 전용)

ag 플랫폼에서 각 에이전트 세션은 **독립적인 대화 컨텍스트**를 갖는다.
이 스킬은 에이전트가 자신의 역할 파일을 읽고, 태스크를 수행하고,
결과를 파일로 출력하여 오케스트레이션 세션과 소통하는 방법을 정의한다.

> **이 스킬은 에이전트 세션(Agent-1/2/3)에서만 사용한다.**
> 오케스트레이션 세션은 `/ag-orchestration` 스킬을 사용한다.

---

## 에이전트 세션 시작 절차

### Step 1 — 역할 파일 로드
세션 시작 시 오케스트레이션이 안내한 역할 파일을 읽는다:

```
ag-workspace/roles/agent{N}-role.md
```

역할 파일에서 다음을 파악한다:
- `role` / `objective`: 이 세션의 목적
- `inputs`: 읽어야 할 파일들
- `expected_outputs`: 생성해야 할 파일들
- `acceptance_criteria`: 완료 기준
- `skills_to_use`: 사용할 스킬

### Step 2 — 최신 Task 파일 확인
역할 파일 로드 후, 자신에게 할당된 task 파일을 확인한다:

```
ag-workspace/tasks/agent{N}-task-*.md
```

가장 최신 seq 번호의 task 파일을 읽어 현재 수행할 작업을 파악한다.
(task 파일이 없으면 역할 파일의 objective에 따라 첫 번째 작업을 수행한다.)

### Step 3 — 작업 수행
task의 `objective` 와 `acceptance_criteria` 를 기준으로 작업을 수행한다.

- `inputs` 에 명시된 파일들을 읽어 컨텍스트 확보
- `skills_to_use` 에 명시된 스킬이 있으면 해당 스킬 활성화
- `expected_outputs` 경로에 결과물 저장

### Step 4 — 핸드오프 파일 작성
작업 완료 후 **핸드오프 파일**을 작성한다:

저장 위치: `ag-workspace/handoffs/agent{N}-handoff-{seq:03d}.md`

**핸드오프 파일 템플릿:**
```markdown
# Handoff from Agent-{N}

## FROM_AGENT
agent{N}

## SEQ
{task의 seq와 동일}

## STATUS
PASS | FAIL

## SUMMARY
{이번 작업에서 달성한 것 — 1~3 문장}

## OUTPUTS
- {생성한 파일 경로}
- {생성한 파일 경로}

## ACCEPTANCE_CRITERIA_MET
- [x] {달성한 기준}
- [ ] {미달성 기준 (STATUS==FAIL 시)}

## NEXT_AGENT
{다음에 실행되어야 할 에이전트 번호, 없으면 "none"}

## NEXT_OBJECTIVE
{다음 에이전트가 수행해야 할 작업 — 오케스트레이션에게 제안}

## ISSUES
{문제가 있으면 기술, 없으면 "none"}

## CONTEXT_FOR_NEXT
{다음 에이전트가 알아야 할 핵심 컨텍스트 또는 주요 결과 요약}
```

### Step 5 — 결과 파일 작성 (최종 단계인 경우)
자신이 마지막 에이전트이거나 `NEXT_AGENT: none` 인 경우:

저장 위치: `ag-workspace/results/agent{N}-result-{seq:03d}.md`

**결과 파일 템플릿:**
```markdown
# Result: Agent-{N}

## STATUS
PASS | FAIL

## DELIVERABLES
- {최종 산출물 파일 경로 및 설명}

## SUMMARY
{전체 작업 완료 요약}

## EVIDENCE
- {테스트 통과 여부, 벤치마크, 로그 경로 등}
```

### Step 6 — 사용자에게 안내

작업 완료 후 사용자에게 다음 형식으로 안내한다:

```
## ✅ Agent-{N} 작업 완료

**상태:** PASS / FAIL
**산출물:** {파일 경로 목록}

핸드오프 파일을 작성했습니다:
ag-workspace/handoffs/agent{N}-handoff-{seq:03d}.md

---
👉 **오케스트레이션 세션으로 이동하여 핸드오프를 처리해주세요.**
```

---

## 다음 Task 수신 절차

오케스트레이션이 새 task 파일을 작성한 후 사용자가 이 세션으로 돌아오면:

1. `ag-workspace/tasks/agent{N}-task-*.md` 에서 새 task 확인
2. 이전 seq보다 높은 seq의 task 파일을 읽는다
3. Step 3 ~ Step 6 반복 수행

---

## 주의사항

- **컨텍스트 독립성**: 각 세션은 독립된 컨텍스트를 갖는다. 이전 세션에서 한 작업은 파일을 통해서만 접근 가능하다.
- **파일 경로 준수**: `ag-workspace/` 하위 경로를 정확히 지켜야 오케스트레이션이 파일을 찾을 수 있다.
- **핸드오프 형식 준수**: 오케스트레이션은 핸드오프 파일의 마크다운 헤더(`## FROM_AGENT` 등)를 파싱하므로 형식을 정확히 따른다.
- **작업 중단 시**: 작업 도중 실패하면 STATUS: FAIL 로 핸드오프를 작성하고 ISSUES 에 상세 내용을 기입한다.

---

자세한 핸드오프 파일 스펙은 `ag-workspace/roles/` 의 역할 파일과
오케스트레이션이 제공하는 task 파일을 참고하라.
