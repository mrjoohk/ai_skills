# Reference: Agent Executor

## agents/ Directory Structure

```
agents/
  orchestration_plan.md       ← Entry point for agent-executor
  agent-1-architect.md        ← Agent-1 role file
  agent-2-builder.md          ← Agent-2 role file
  agent-3-verifier.md         ← Agent-3 role file
```

---

## orchestration_plan.md Parsing Items

Core fields agent-executor must read:

| Field | Purpose |
|---|---|
| Agent List | Confirm file paths |
| Execution Groups | Determine parallel/sequential spawn |
| Final Report Storage Location | Report file path |

---

## Agent Role File Parsing Items

| Field | Purpose |
|---|---|
| `task_prompt` | Instructions to pass to subagent |
| `inputs` | File list subagent will read |
| `outputs` | File list subagent will generate |
| `dependencies` | Whether prior agent completion is required |
| `acceptance_criteria` | Completion judgment criteria |
| `skills_to_use` | Skill information to pass to subagent |

---

## Parallel Spawn Pattern

```
# Multiple Agent tool calls in single message = parallel execution
Group 1 (parallel):
  → Agent tool (task_prompt from agent-1-architect.md)
  → Agent tool (task_prompt from agent-1b-analyst.md)   ← Called simultaneously in same message

# Next group after previous group completes
Group 2 (after Group 1 completes):
  → Agent tool (task_prompt from agent-2-builder.md)
```

---

## Subagent Result Report Format

Standard format subagent must return:

```
STATUS: PASS
OUTPUTS:
  - uf.md
  - requirements.md
SUMMARY: Derived UF-01~UF-20. I/O contracts included.
ISSUES: none
```

FAIL case:
```
STATUS: FAIL
OUTPUTS:
  - uf.md (partially complete)
SUMMARY: Input file path error while writing I/O contracts after UF-15.
ISSUES: if_list.md file missing. Check agents/agent-1-architect.md inputs.
```

---

## Error Handling Policy

| Situation | Handling |
|---|---|
| Output file not generated | Record FAIL, orchestrator determines retry |
| acceptance_criteria not met | Record WARN, can proceed to next group |
| Subagent error termination | Record FAIL, halt dependent agent execution |
| Independent agent FAIL | Only that agent FAIL, others continue |
