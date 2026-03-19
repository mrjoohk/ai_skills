# ag-Orchestration Examples

## 예시 시나리오: SAR 시뮬레이션 파이프라인 구축

전체 목표: SAR 신호 처리 파이프라인의 요구사항 분석 → 구현 → 검증

---

### Phase 1: 오케스트레이션 세션에서 역할 파일 생성

**사용자 프롬프트 예시:**
```
SAR 시뮬레이션 파이프라인 구현 태스크를 ag 멀티에이전트로 분배해줘.
agent-orchestration 에서 만든 orchestration_plan.md 파고 ag-orchestration 스킬로 시작해.
```

**오케스트레이션이 생성하는 파일:**

`ag-workspace/roles/agent1-role.md`:
```markdown
# Agent-1: Architect

## role
요구사항 분석 및 UF/IF 설계 (Stage 1~7)

## context
SAR 시뮬레이션 파이프라인 구축 프로젝트. 전체 목표는 GPU 기반 SAR 신호처리
파이프라인의 요구사항 도출 및 구조 설계.

## objective
- requirements.md 도출 (REQ-001 ~ REQ-010)
- if_list.md 작성 (IF-01 ~ IF-05)
- uf.md 작성 (UF-01 ~ UF-15)

## inputs
- docs/problem_statement.md
- docs/constraints.md

## expected_outputs
- ag-workspace/artifacts/requirements.md
- ag-workspace/artifacts/if_list.md
- ag-workspace/artifacts/uf.md

## acceptance_criteria
- REQ 블록 10개 이상
- 모든 IF에 Input/Output Contract 정의
- 모든 UF에 Parent IF 연결

## skills_to_use
- core-engineering

## handoff_instruction
작업 완료 후 ag-workspace/handoffs/agent1-handoff-001.md 작성.
```

`ag-workspace/tasks/agent1-task-001.md`:
```markdown
# Task for Agent-1 | seq: 001

## FROM
orchestration

## SEQ
001

## OBJECTIVE
docs/ 의 문서를 기반으로 SAR 파이프라인의 요구사항, IF, UF를 도출하라.

## INPUTS
- docs/problem_statement.md
- docs/constraints.md

## OUTPUTS_EXPECTED
- ag-workspace/artifacts/requirements.md
- ag-workspace/artifacts/if_list.md
- ag-workspace/artifacts/uf.md

## ACCEPTANCE_CRITERIA
- REQ 블록 10개 이상 (REQ-001~REQ-010)
- IF 블록 5개 이상, 각 IF에 Contract 완비
- UF 블록 15개 이상, 각 UF에 Parent IF 연결

## CONTEXT
프로젝트 시작 단계. 아직 이전 에이전트 산출물 없음.
core-engineering 스킬을 활성화하여 GLOBAL_RULES.md 의 8단계 프로세스 따를 것.

## DEADLINE_HINT
none
```

**사용자 안내:**
```
## 🚀 ag 오케스트레이션 준비 완료

ag에서 세션 4개를 생성해주세요:
- 오케스트레이션 세션: 현재 이 세션 유지
- Agent-1 세션: ag-workspace/roles/agent1-role.md 로드
- Agent-2 세션: ag-workspace/roles/agent2-role.md 로드
- Agent-3 세션: ag-workspace/roles/agent3-role.md 로드

각 에이전트 세션에서는 /ag-agent-executor 스킬을 사용합니다.
지금 Agent-1 세션으로 이동하여 task를 실행하세요.
```

---

### Phase 2: Agent-1 세션에서 작업 수행

**Agent-1 세션 시작 프롬프트:**
```
/ag-agent-executor
ag-workspace/roles/agent1-role.md 읽고 task 실행해줘.
```

**Agent-1이 작업 완료 후 작성하는 핸드오프:**

`ag-workspace/handoffs/agent1-handoff-001.md`:
```markdown
# Handoff from Agent-1

## FROM_AGENT
agent1

## SEQ
001

## STATUS
PASS

## SUMMARY
SAR 파이프라인 요구사항 분석 완료. REQ-001~REQ-012 도출,
IF-01~IF-06 정의, UF-01~UF-18 작성. GPU 처리 제약 조건이
IF-03에 반영됨.

## OUTPUTS
- ag-workspace/artifacts/requirements.md
- ag-workspace/artifacts/if_list.md
- ag-workspace/artifacts/uf.md

## ACCEPTANCE_CRITERIA_MET
- [x] REQ 블록 10개 이상 (12개 달성)
- [x] 모든 IF에 Input/Output Contract 정의 (6개)
- [x] 모든 UF에 Parent IF 연결 (18개)

## NEXT_AGENT
agent2

## NEXT_OBJECTIVE
UF 목록 기반으로 최소 diff 구현. GPU 처리 제약(IF-03) 우선 구현.

## ISSUES
none

## CONTEXT_FOR_NEXT
- UF-07, UF-08이 GPU 연산 핵심. IF-03의 Input Contract 엄격히 준수 필요.
- requirements.md의 REQ-005 (레이턴시 < 50ms) 가 구현 시 주요 제약.
- uf.md 의 모든 UF에 Verification Plan 포함됨, Agent-3 참고.
```

**사용자 안내 (Agent-1 출력):**
```
## ✅ Agent-1 작업 완료

상태: PASS
산출물:
- ag-workspace/artifacts/requirements.md
- ag-workspace/artifacts/if_list.md
- ag-workspace/artifacts/uf.md

핸드오프 파일 작성 완료:
ag-workspace/handoffs/agent1-handoff-001.md

👉 오케스트레이션 세션으로 이동하여 핸드오프를 처리해주세요.
```

---

### Phase 3: 오케스트레이션 세션에서 핸드오프 처리

**사용자가 오케스트레이션 세션으로 돌아와서:**
```
agent1 핸드오프 들어왔어. 처리해줘.
```

**오케스트레이션이 수행하는 동작:**

1. `ag-workspace/handoffs/agent1-handoff-001.md` 읽기
2. STATUS: PASS, NEXT_AGENT: agent2 확인
3. `ag-workspace/tasks/agent2-task-001.md` 생성:

```markdown
# Task for Agent-2 | seq: 001

## FROM
orchestration

## SEQ
001

## OBJECTIVE
Agent-1이 도출한 UF 목록 기반으로 SAR 파이프라인 최소 diff 구현.
GPU 처리 제약(IF-03)을 우선 구현하라.

## INPUTS
- ag-workspace/artifacts/requirements.md
- ag-workspace/artifacts/if_list.md
- ag-workspace/artifacts/uf.md

## OUTPUTS_EXPECTED
- src/sar_pipeline/processor.py
- src/sar_pipeline/gpu_handler.py
- src/sar_pipeline/tests/test_processor.py

## ACCEPTANCE_CRITERIA
- UF-01~UF-18 모두 구현 (stub 포함)
- IF-03 GPU Contract 준수 (dtype, shape 검증 포함)
- 단위 테스트 파일 존재

## CONTEXT
Agent-1 완료. 요구사항/IF/UF 모두 준비됨.
핵심 제약: REQ-005 (레이턴시 < 50ms), IF-03 GPU Contract.
UF-07, UF-08이 GPU 연산 핵심이니 우선 구현.

## DEADLINE_HINT
none
```

**사용자 안내:**
```
## ✅ 핸드오프 처리 완료

FROM: Agent-1 → TO: Agent-2
이유: Architect 단계 완료. Builder 단계 시작.

→ Agent-2 세션으로 이동해서 task를 실행해주세요.
새 task: ag-workspace/tasks/agent2-task-001.md
```

---

### Phase 4: 최종 리포트 생성

모든 에이전트 완료 후 오케스트레이션 세션에서:

```
모든 에이전트 완료됐어. final report 생성해줘.
```

오케스트레이션이 `ag-workspace/reports/final-report.md` 생성 (reference.md 의 템플릿 참고).

---

## 실패 처리 예시

Agent-2가 STATUS: FAIL 로 핸드오프를 보낸 경우:

```markdown
## STATUS
FAIL

## ISSUES
GPU 메모리 부족으로 UF-07 구현 실패. torch.cuda.OutOfMemoryError.
IF-03의 batch_size 파라미터 상한 재정의 필요.

## NEXT_AGENT
agent1
```

**오케스트레이션 대응:**
- NEXT_AGENT: agent1 → Architect에게 IF-03 재정의 요청
- 새 task: `agent1-task-002.md` 에 ISSUES 내용 포함

또는 오케스트레이션이 자체 판단하여 Agent-2에게 수정 task 재발행:
- `agent2-task-002.md`: batch_size 조정하여 재시도 지시
