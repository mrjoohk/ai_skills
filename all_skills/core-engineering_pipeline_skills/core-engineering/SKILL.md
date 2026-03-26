---
name: core-engineering
description: "Global rules for requirements, verification, and integration across projects. Defines the end-to-end design process from problem to unit functions."
user-invocable: true
allowed-tools: Read, Write
---

# Core Engineering

This skill defines the **global engineering design process** and rules for requirement clarity, verification, and integration.
It is the foundation for all other skills in this pack.

---

## Design Process

```
Problem Definition
  ↓
Problem Review & Clarification
  ↓
Problem Elaboration (Constraints · Boundaries · Assumptions)
  ↓
Requirements Elicitation  ──→  Write REQ Blocks
  ↓
Integration Function (IF) Identification  ──→  Define system boundaries and interfaces
  ↓
IF Decomposition  ──→  IF → Subfunctions dependency graph
  ↓
Unit Function (UF) Definition  ──→  UF Blocks · I/O Contracts · Verification Plan
  ↓
UF→IF Coverage Review  ──→  Bottom-up integration check · Gap & redundancy detection
  ↓                         (iterate back to Stage 5/7 if gaps found)
Verification & Evidence Planning
```

### Stage 1 — Problem Definition
- Describe problem background and context in 1–3 sentences
- Identify scope of impact (system, team, timeline)
- **Output:** `problem_statement.md`

### Stage 2 — Problem Review & Clarification
- List ambiguous terms and boundary conditions
- Confirm stakeholders and prepare questions list
- Identify overlapping or conflicting goals
- **Output:** `clarification_log.md` (Q&A format)

### Stage 3 — Problem Elaboration
- Constraints: time, memory, accuracy, regulations, etc.
- Boundary Conditions: input ranges, extreme values
- Assumptions: explicit recording for later validation
- **Output:** `assumptions_and_constraints.md`

### Stage 4 — Requirements Elicitation
- Write functional and non-functional requirements
- Format each requirement as a **REQ Block** (see template below)
- Express Acceptance Criteria as Given/When/Then with numeric thresholds
- **Output:** `requirements.md`

### Stage 5 — Integration Function (IF) Identification
- Create system boundary diagram
- List external interfaces (inputs/outputs, APIs, hardware interfaces)
- Specify inputs, outputs, constraints, and linked REQs for each IF
- **Output:** `if_list.md`

### Stage 6 — IF Decomposition
- Decompose each IF into subfunctions and create dependency graph
- Decomposition criteria: Single Responsibility Principle (SRP), testability
- Decomposition result becomes candidate UF list
- **Output:** `if_decomposition.md` (with tree/graph visualization)

### Stage 7 — Unit Function (UF) Definition
- Format each UF as a **UF Block** (see template below)
- I/O Contract: specify type, unit, coordinate system, tensor shape
- List edge cases and failure modes
- **Output:** `uf.md`

### Stage 7.5 — UF→IF Coverage Review
- For each IF, verify that its decomposed UFs collectively satisfy the IF's I/O contract and acceptance criteria (bottom-up integration check)
- Check for coverage gaps: any IF acceptance criterion not covered by at least one UF → flag as `UNCOVERED`
- Check for redundancy: multiple UFs with identical responsibility → flag as `REDUNDANT`
- Check I/O chain continuity: output of one UF must match input type/shape of the next in the call graph
- Iterate: if gaps or mismatches found, revise `uf.md` or `if_list.md` before proceeding
- **Output:** `uf_if_coverage_review.md` (coverage matrix: IF rows × UF columns, PASS/UNCOVERED/REDUNDANT)

### Stage 8 — Verification & Evidence Planning
- Write unit / integration / E2E test plans
- Define Evidence Pack structure
- Set regression thresholds
- **Output:** `verification_plan.md`, proposed `evidence_pack/` structure

---

## Execution Rules

1. All acceptance criteria must be **testable and measurable numerically**.
2. All I/O contracts must specify **type, unit, and shape**.
3. Token economy: prioritize file paths and symbol references. Do not paste large code blocks.
4. All claims must have **evidence artifacts** (test results, logs, plots, benchmarks).
5. Assumptions must be explicitly recorded and validated later.

---

## Output Templates

### REQ Block
```
- ID: REQ-###
- Context: (background and motivation)
- Inputs: (type, unit, range)
- Outputs: (type, unit, range)
- Constraints: (performance, memory, accuracy, etc.)
- Acceptance Criteria: Given <situation>, When <action>, Then <result> (with numeric thresholds)
- Tests: unit / integration / e2e
- Evidence: (artifact paths)
```

### UF Block
```
- UF-ID: UF-##
- Parent IF: IF-##
- Goal: (single responsibility statement)
- I/O Contract:
    Input:  <name>: <type>, <unit/shape>, <range>
    Output: <name>: <type>, <unit/shape>, <range>
- Algorithm Summary: (core algorithm in 1–3 lines)
- Edge Cases: (extreme values, null, overflow, etc.)
- Verification Plan: (test commands, coverage goals)
- Evidence Pack Fields: scenario_id, run_id, metrics, environment, commit_sha
```

---

## MCP Hooks (Optional)
- `mcp.shell`: run lint/tests/bench
- `mcp.filesystem`: create/update requirements, uf, verification_plan files
- `mcp.github`: open issues, link PRs, attach evidence artifacts

---

## Skill Integration

Use these skills to execute each stage. The pipeline runs sequentially — each skill's output is the next skill's input.

| Skill | Stages | Input → Output |
|---|---|---|
| `req-elicitor` | **1–4** (entry point) | problem description → `requirements.md` |
| `if-designer` | **5–6** | `requirements.md` → `if_list.md` + `if_decomposition.md` |
| `uf-designer` | **7** | `if_decomposition.md` → `uf.md` |
| `uf-chain-validator` | **7.5** | `uf.md` + `if_list.md` → coverage review |
| `uf-if-debug-mapper` | **6–7** (debug) | UF/IF artifacts → debug map |
| `uf-implementor` | After Stage 7.5 | `uf.md` → implemented UF code |
| `if-integrator` | After UF implementation | UF code → IF-level modules |
| `eval-planner` | **8** | REQ/UF/IF blocks → `verification_plan.md` |
| `eval-runner` | After Stage 8 | evaluation plan + results → metrics report |
| `ci-evidence-automation` | Stage 8+ | test results → evidence pack |
| `agent-orchestration` | All stages | applies agent role distribution |

See `references/reference.md` for full output templates.
