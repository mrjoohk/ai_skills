# Orchestration Plan

## Task Overview
<!-- One-line summary of the overall task being orchestrated -->
<overall_task_description>

## Agent List

| Agent | Role | File | Parallel OK | Dependencies |
|:---:|---|---|:---:|---|
| Agent-1 | <role_name> | agents/agent-1-<role>.md | ✅ | none |
| Agent-2 | <role_name> | agents/agent-2-<role>.md | ❌ | After Agent-1 |
| Agent-3 | <role_name> | agents/agent-3-<role>.md | ❌ | After Agent-2 |

## Execution Groups
<!-- agent-executor runs groups sequentially; agents within a group run in parallel -->

**Group 1 (parallel):** Agent-1
→ Produces: <list of key output files>

**Group 2 (parallel):** Agent-2
→ Depends on: Agent-1 outputs
→ Produces: <list of key output files>

**Group 3 (parallel):** Agent-3
→ Depends on: Agent-2 outputs
→ Produces: <list of key output files>

## Standard 3-Agent Template (adapt as needed)

| Agent | Role | Responsible Areas | Key Outputs |
|:---:|---|---|---|
| Agent-1 (Architect) | Requirements · Design · UF/IF completion | Stages 1–7 | uf.md, requirements.md, if_list.md |
| Agent-2 (Builder)   | Minimal-diff implementation | Implementation | src/, tests/ |
| Agent-3 (Verifier)  | Validation · Evidence Pack · CI | Stage 8 | reports/, evidence_pack/ |

## Final Report
`reports/orchestration_report_<timestamp>.md`

## Notes
<!-- Any task-specific constraints, ordering rules, or special considerations -->
