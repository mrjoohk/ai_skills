---
name: agent-orchestration
description: "Designs multi-agent workflows by generating structured role description files (agents/*.md) that agent-executor can use to spawn real subagents. Use when the user wants to break a complex task into parallel agent roles, define handoffs, or prepare an orchestration plan. Trigger when the user mentions 'multi-agent', 'agent 분배', '역할 나눠서', or before running agent-executor."
user-invocable: true
allowed-tools: Read, Write
---

# Agent Orchestration — Role Design & Documentation Generation Skill

Decompose complex tasks into agent-specific roles and generate
**structured role description files** that `agent-executor` can spawn.

> This skill handles **documentation generation only**.
> Actual subagent execution is handled by `/agent-executor`.

---

## When to Use
- When a task is complex or benefits from parallel processing
- When you want to execute multiple stages (1~8) simultaneously
- When you need role design preparation before running `/agent-executor`

---

## Execution Steps

### Step 1 — Task Analysis and Agent Count Determination
Read input documents (design documents, UF lists, WBS, etc.) and:
- Identify independent work units that can run in parallel
- Arrange dependent tasks sequentially
- Use the standard 3-agent structure, adjusting as needed for task scale

### Step 2 — Generate Agent Role Files
Create agent-specific .md files in the `agents/` directory.
Must follow the **Agent Role File Template** below.

### Step 3 — Generate Orchestration Plan File
Create `agents/orchestration_plan.md`.
agent-executor reads this file to determine execution order.

---

## Agent Role File Template

> Save as `agents/agent-<N>-<role>.md`

```markdown
# Agent-<N>: <Role Name>

## role
One-line role summary

## objective
Concrete objective this agent must achieve

## task_prompt
Prompt to be passed directly to the subagent by agent-executor
Write concretely and actionably, including file paths and output locations

## inputs
- <Input file path or previous agent output>
- ...

## outputs
- <File path to be generated>
- <File path to be generated>

## dependencies
- <Agent number that must complete first, or none>

## acceptance_criteria
- <Completion judgment criteria — numeric or file existence>
- ...

## skills_to_use
- <Skill name for subagent to use, or none>
```

---

## Orchestration Plan Template

> Save to `agents/orchestration_plan.md`

```markdown
# Orchestration Plan

## Task Overview
One-line summary of overall task

## Agent List

| Agent | Role | File | Parallel Execution | Dependencies |
|:---:|---|---|:---:|---|
| Agent-1 | Architect | agents/agent-1-architect.md | ✅ | none |
| Agent-2 | Builder    | agents/agent-2-builder.md   | ❌ | After Agent-1 |
| Agent-3 | Verifier   | agents/agent-3-verifier.md  | ❌ | After Agent-2 |

## Execution Groups (agent-executor executes in this order)
- Group 1 (parallel): Agent-1
- Group 2 (parallel): Agent-2
- Group 3 (parallel): Agent-3

## Final Report Storage Location
reports/orchestration_report_<timestamp>.md
```

---

## Standard 3-Agent Roles

| Agent | Role | Responsible Stages |
|:---:|---|---|
| Agent-1 (Architect) | Requirements·Design·UF/IF completion | Stage 1~7 |
| Agent-2 (Builder) | Minimal diff implementation | Implementation |
| Agent-3 (Verifier) | Validation·Testing·Evidence Pack·CI | Stage 8 |

See `reference.md` for Handoff templates and `examples.md` for example prompts.
