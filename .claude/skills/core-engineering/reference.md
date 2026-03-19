# Reference: Core Engineering Templates

## Design Process Output Summary by Stage

| Stage | Stage Name | Output |
|:---:|---|---|
| 1 | Problem Definition | `problem_statement.md` |
| 2 | Problem Review & Clarification | `clarification_log.md` |
| 3 | Problem Elaboration | `assumptions_and_constraints.md` |
| 4 | Requirements Elicitation | `requirements.md` (REQ blocks) |
| 5 | IF Identification | `if_list.md` |
| 6 | IF Decomposition | `if_decomposition.md` |
| 7 | UF Definition | `uf.md` (UF blocks) |
| 8 | Verification & Evidence Planning | `verification_plan.md`, `evidence_pack/` |

---

## Problem Statement Template
```
## Problem Background
(Context and scope of impact — 1–3 sentences)

## Scope of Impact
- System:
- Team/Stakeholders:
- Schedule Impact:

## Initial Constraints
(List known technical and non-functional constraints)
```

---

## Clarification Log Template
```
## Q&A List
| # | Question | Answer | Source | Date |
|---|----------|--------|--------|------|
| 1 | ... | ... | ... | ... |

## Resolved Ambiguities
- ...

## Unresolved Items (require further clarification)
- ...
```

---

## Assumptions & Constraints Template
```
## Constraints
- Performance: (e.g., processing time <= X ms)
- Memory: (e.g., RAM <= Y GB)
- Accuracy: (e.g., error <= Z%)
- Regulations/Compliance: ...

## Boundary Conditions
- Input minimum / maximum values
- Extreme scenarios (empty input, maximum load, etc.)

## Assumptions — to be validated later
| # | Assumption | Validation Method | Status |
|---|-----------|-------------------|--------|
| A1 | ... | ... | Unvalidated |
```

---

## REQ Block Template
```
- ID: REQ-###
- Context: (background and motivation)
- Inputs:
    <name>: <type>, <unit>, <range>
- Outputs:
    <name>: <type>, <unit>, <range>
- Constraints: (performance, memory, accuracy, determinism, etc.)
- Acceptance Criteria:
    Given <situation>, When <action>, Then <result> (with numeric thresholds)
    Example: "Then response time <= 200ms (95th percentile)"
- Tests:
    Unit: <test function name or file path>
    Integration: <scenario name>
    E2E: <end-to-end scenario>
- Evidence:
    reports/<...> (plots, logs, metrics)
    evidence_pack/<...> (runs.yaml, metrics.yaml, env.yaml)
```

---

## IF Block Template
```
- IF-ID: IF-##
- Description: (one-line summary of interface purpose)
- Producer: <module/component>
- Consumer: <module/component>
- Input Contract:
    <name>: <type>, <unit/shape>, <range>
- Output Contract:
    <name>: <type>, <unit/shape>, <range>
- Constraints: (timing, protocol, serialization format, etc.)
- Failure Modes: (e.g., schema mismatch, timeout, null input)
- Linked REQs: REQ-###, REQ-###
```

---

## UF Block Template
```
- UF-ID: UF-##
- Parent IF: IF-##
- Goal: (single responsibility statement)
- I/O Contract:
    Input:  <name>: <type>, <unit/shape>, <range>
    Output: <name>: <type>, <unit/shape>, <range>
- Algorithm Summary: (core algorithm in 1–3 lines)
- Edge Cases: (extreme values, null, overflow, empty input, etc.)
- Verification Plan:
    Unit:        pytest <path>::<test_func>
    Integration: <scenario file path>
    Coverage:    >= XX%
- Evidence Pack Fields: scenario_id, run_id, metrics, environment, commit_sha
```

---

## Evidence Pack Schema
```
evidence_pack/
  runs.yaml       # Execution metadata: timestamp, commit, params
  metrics.yaml    # Numeric results + thresholds + pass/fail
  env.yaml        # Environment: OS, Python, CUDA, GPU, package versions
  scenarios.yaml  # Scenario definitions and input parameters
  artifacts/
    logs/         # Execution logs
    plots/        # Result graphs
    profiles/     # Performance profiling results
```

---

## Minimal Diff Patch Convention
- Prioritize `git diff`-style patches over full file outputs.
- Separate refactoring-only commits from behavior-change commits.
- Organize changes by type: (1) Refactoring, (2) Behavior changes, (3) Tests/Benchmarks.
