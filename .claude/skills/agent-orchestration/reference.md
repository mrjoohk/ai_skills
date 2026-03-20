# Reference: Agent Orchestration Templates

## Design Process and Agent Role Mapping

| Stage (core-engineering) | Responsible Agent | Key Activities |
|---|:---:|---|
| Stage 1~3: Problem Definition·Clarification·Detailing | Agent-1 | Problem analysis, stakeholder inquiry, assumption specification |
| Stage 4~5: Requirements·IF Derivation | Agent-1 | REQ blocks, IF list, system boundaries |
| Stage 6~7: IF Decomposition·UF Derivation | Agent-1 | IF decomposition tree, UF blocks, I/O contracts |
| Implementation | Agent-2 | Minimal diff implementation |
| Stage 8: Validation·Evidence Planning | Agent-3 | Testing, benchmarking, evidence pack, CI gates |

---

## Standard 3-Agent Roles

**Agent-1 (Architect)**
- Execute design process (Stage 1~7)
- Write REQ·IF·UF documents
- Define acceptance criteria

**Agent-2 (Builder)**
- Implement minimal diff based on UF blocks
- Keep refactoring and behavior changes in separate commits
- Implement in testable units

**Agent-3 (Verifier)**
- Run unit/integration/E2E tests
- Check benchmarking and coverage gates
- Generate evidence pack and configure CI gates

---

## Handoff Message Template
```
From Agent:       (1 / 2 / 3)
To Agent:         (1 / 2 / 3)
Objective:        One-line handoff objective summary
Context Links:    File paths, issue IDs, REQ/UF/IF scope
Deliverables:     Expected output list
Constraints:      Performance, memory, schedule constraints
Acceptance Tests: Acceptance criteria — including numeric thresholds
Evidence Outputs: Evidence artifact paths
```

---

## Status Webhook Payload Templates

**SUCCESS**
```json
{
  "status": "SUCCESS",
  "task": "<UF/IF scope or task name>",
  "commit": "<commit_sha>",
  "summary": "<One-line achievement summary>",
  "artifacts": ["<path1>", "<path2>"]
}
```

**FAILURE**
```json
{
  "status": "FAILURE",
  "task": "<task name>",
  "commit": "<commit_sha>",
  "error_summary": "<error details>",
  "failing_commands": ["<command>"],
  "logs_path": "<log path>"
}
```

**COVERAGE_LOW**
```json
{
  "status": "COVERAGE_LOW",
  "task": "<task name>",
  "current": <current coverage %>,
  "required": <target coverage %>,
  "missing_modules": ["<module1>", "<module2>"]
}
```

**REGRESSION**
```json
{
  "status": "REGRESSION",
  "metric": "<metric name>",
  "before": <previous value>,
  "after": <current value>,
  "threshold": <acceptable threshold>,
  "reproduction_steps": "<reproduction command>"
}
```
