---
name: ag-orchestration
description: "ag(antigravity) 플랫폼 전용 멀티에이전트 오케스트레이션 스킬. ag는 서브에이전트 스폰을 지원하지 않으므로, 파일 기반 메시지 패싱으로 에이전트 간 협업을 수행한다. 오케스트레이션 세션에서만 사용. '오케스트레이션 세션', 'ag 오케스트레이션', '에이전트 역할 파일 생성', 'agent 핸드오프 처리', '결과 수집', 'final report' 등의 맥락에서 반드시 이 스킬을 사용한다."
allowed-tools: Read, Write
---

# ag-Orchestration Skill (오케스트레이션 세션 전용)

ag 플랫폼에서는 서브에이전트 스폰이 불가능하다.
이 스킬은 **파일 기반 메시지 패싱(File-based Message Passing)** 을 통해
오케스트레이션 세션이 여러 에이전트 세션을 조율하는 방법을 정의한다.

> **이 스킬은 오케스트레이션 세션에서만 사용한다.**
> 각 에이전트 세션은 `/ag-agent-executor` 스킬을 사용한다.

---

## 핵심 아키텍처

```
[사용자가 직접 세션 전환]

오케스트레이션 세션           에이전트 세션 (1/2/3)
        │                           │
        │  ① role 파일 생성          │
        │  ② task 파일 작성 ────────►│
        │                           │  ③ 역할 수행
        │◄──── ④ handoff 파일 ───────│
        │  ⑤ 라우팅 판단              │
        │  ⑥ 다음 task 작성 ─────────►│
        │                           │  ⑦ 역할 수행
        │◄──── ⑧ result 파일 ────────│
        │  ⑨ 결과 수집 → Final Report │
```

**핸드오프 경로**: AgentN → orchestration → AgentM
**상태 공유**: `ag-workspace/` 폴더를 모든 세션이 공유

---

## 공유 워크스페이스 구조

```
ag-workspace/
├── roles/                         # 에이전트 역할 정의 (orchestration이 생성)
│   ├── agent1-role.md
│   ├── agent2-role.md
│   └── agent3-role.md
├── tasks/                         # orchestration → agent 작업 지시
│   └── agent{N}-task-{seq:03d}.md
├── handoffs/                      # agent → orchestration 핸드오프
│   └── agent{N}-handoff-{seq:03d}.md
├── results/                       # 에이전트 완료 결과물
│   └── agent{N}-result-{seq:03d}.md
└── reports/
    └── final-report.md
```

---

## Execution Steps

### Phase 1 — 역할 파일 생성 (최초 1회)

`agents/orchestration_plan.md` 또는 사용자 요청을 분석하여:

1. **태스크 분해**: 전체 작업을 독립적/순차적 단위로 분리
2. **에이전트 역할 할당**: 기본 3-agent 구조 (Architect / Builder / Verifier)
3. **ag-workspace/roles/** 에 role 파일 생성 → **Role File Template** 참고
4. **ag-workspace/tasks/** 에 최초 task 파일 생성 → **Task File Template** 참고
5. 사용자에게 세션 생성 및 시작 방법 안내

**사용자에게 전달할 안내 메시지 형식:**
```
## 🚀 ag 오케스트레이션 준비 완료

세션 4개를 ag에서 생성해주세요:
- 오케스트레이션 세션 (현재): 계속 이 세션 사용
- Agent-1 세션: ag-workspace/roles/agent1-role.md 로드 후 시작
- Agent-2 세션: ag-workspace/roles/agent2-role.md 로드 후 시작
- Agent-3 세션: ag-workspace/roles/agent3-role.md 로드 후 시작

각 에이전트는 `/ag-agent-executor` 스킬로 시작합니다.
Agent-1부터 시작하세요. 완료 시 이 세션으로 돌아오세요.
```

---

### Phase 2 — 핸드오프 처리 (반복)

에이전트가 작업 완료 후 사용자가 이 세션으로 돌아올 때마다:

1. **새 핸드오프 파일 확인**
   ```
   ag-workspace/handoffs/ 에서 미처리 파일 목록 확인
   (처리된 파일: 해당 task 파일이 이미 존재하는 것)
   ```

2. **핸드오프 내용 파싱** → `handoff-protocol.md` 참고
   - `FROM_AGENT`, `STATUS`, `OUTPUTS`, `NEXT_AGENT`, `NEXT_OBJECTIVE` 추출

3. **라우팅 판단**
   - STATUS == PASS → 다음 에이전트로 task 생성
   - STATUS == FAIL → 오류 분석 후 동일 에이전트에 재시도 task 또는 사용자에게 보고
   - 모든 에이전트 완료 → Phase 3으로

4. **Task 파일 생성** (`ag-workspace/tasks/agent{M}-task-{seq:03d}.md`)
   - 이전 핸드오프의 outputs를 inputs로 연결
   - 명확한 objective와 acceptance_criteria 포함

5. **사용자 안내**
   ```
   ## ✅ 핸드오프 처리 완료

   FROM: Agent-{N} → TO: Agent-{M}
   이유: {라우팅 근거}

   → Agent-{M} 세션으로 이동해서 task를 실행해주세요.
   새 task 파일: ag-workspace/tasks/agent{M}-task-{seq:03d}.md
   ```

---

### Phase 3 — 최종 리포트 생성

모든 에이전트의 result 파일이 존재할 때:

1. `ag-workspace/results/` 에서 모든 result 파일 읽기
2. 전체 실행 흐름 재구성 (task → handoff → result 시퀀스)
3. `ag-workspace/reports/final-report.md` 생성 → `report-template.md` 참고

---

## Role File Template

> 저장 위치: `ag-workspace/roles/agent{N}-role.md`

```markdown
# Agent-{N}: {역할명}

## role
{한 줄 역할 요약}

## context
{이 에이전트가 알아야 할 프로젝트 배경 및 전체 목표}

## objective
{이 에이전트가 달성해야 할 구체적인 목표}

## inputs
- {입력 파일 경로 또는 선행 에이전트 출력물}

## expected_outputs
- {생성해야 할 파일 경로}

## acceptance_criteria
- {완료 판단 기준 (숫자 또는 파일 존재 여부)}

## skills_to_use
- {사용해야 할 스킬명, 없으면 none}

## handoff_instruction
작업 완료 후 `ag-workspace/handoffs/agent{N}-handoff-001.md` 를
handoff-protocol 형식에 맞게 작성하고 사용자에게 오케스트레이션 세션으로
돌아가도록 요청하세요.
```

---

## Task File Template

> 저장 위치: `ag-workspace/tasks/agent{N}-task-{seq:03d}.md`

```markdown
# Task for Agent-{N} | seq: {seq}

## from
orchestration

## seq
{seq}

## objective
{이번 태스크의 구체적 목표}

## inputs
- {이전 에이전트 outputs 경로 또는 기타 입력}

## outputs_expected
- {생성해야 할 결과물 경로}

## acceptance_criteria
- {완료 기준}

## context
{이전 에이전트 결과 요약 또는 현재 상태}

## instruction
1. 이 task 파일을 읽었으면 `/ag-agent-executor` 스킬 지시에 따라 실행하세요.
2. 완료 시 `ag-workspace/handoffs/agent{N}-handoff-{seq:03d}.md` 를 작성하세요.
3. 작업 완료 후 사용자에게 "오케스트레이션 세션으로 돌아가세요" 라고 안내하세요.
```

---

## 상태 추적

오케스트레이션은 다음 기준으로 현재 상태를 파악한다:

| 조건 | 상태 |
|---|---|
| `ag-workspace/roles/` 만 존재 | 에이전트 세션 시작 대기 |
| `tasks/agent{N}-task-001.md` 존재 | Agent-N 작업 진행 중 |
| `handoffs/agent{N}-handoff-{seq}.md` 존재 & 대응 task 없음 | 핸드오프 처리 필요 |
| 모든 `results/agent{N}-result-*.md` 존재 | Final Report 생성 가능 |

---

자세한 핸드오프 파일 스펙은 `reference.md` 를 참고하라.
예시 실행 시나리오는 `examples.md` 를 참고하라.
