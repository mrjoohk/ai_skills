# Examples: Agent Executor

## End-to-End Flow Example (agent-orchestration → agent-executor)

### Step 1: Role Design (agent-orchestration)
```
/agent-orchestration Allocate W100000~W400000 design to 3 agents.
Agent-1 performs Stage 4~7 (REQ·UF refinement),
Agent-2 runs eval-planner,
Agent-3 handles CI design with ci-evidence-automation.
Generate role files and orchestration_plan.md in agents/ directory.
```

**Generated Result:**
```
agents/
  orchestration_plan.md
  agent-1-architect.md
  agent-2-eval-planner.md
  agent-3-ci-designer.md
```

---

### Step 2: Actual Execution (agent-executor)
```
/agent-executor Read agents/orchestration_plan.md and
spawn subagents to execute the work.
```

**Execution Flow:**
```
Orchestrator (current session)
  │
  ├─ Group 1 [parallel spawn]
  │    └─ Spawn Agent-1: "Perform Stage 4~7, generate uf.md..."
  │
  ├─ Group 1 completion check → verify uf.md, requirements.md exist
  │
  ├─ Group 2 [spawn]
  │    └─ Spawn Agent-2: "Establish evaluation plan with eval-planner..."
  │
  ├─ Group 3 [spawn]
  │    └─ Spawn Agent-3: "Design CI with ci-evidence-automation..."
  │
  └─ Generate integrated report: reports/orchestration_report_<timestamp>.md
```

---

## Test Prompt 1: Basic Execution
```
/agent-executor Read agents/orchestration_plan.md and execute.
```

**Expected Outputs:**
- Output files from each agent
- `reports/orchestration_report_<timestamp>.md`

---

## Test Prompt 2: Re-run Specific Agent Only
```
/agent-executor Re-run Agent-2 only.
Agent-1 output (uf.md) already exists.
```

---

## Test Prompt 3: Regenerate Report After Completion
```
/agent-executor All agent work is complete.
Read agents/ files and generated outputs,
then regenerate orchestration_report.md only.
```
