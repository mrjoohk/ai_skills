# GLOBAL_RULES.md (Claude Code Skills Pack)

These global rules apply to all skills in this pack.

## Non-negotiables
1. **Be unambiguous.** Every requirement must be testable and measurable.
2. **Define contracts.** For any function/module: Inputs, Outputs, Constraints, Failure modes.
3. **Evidence-first.** Every significant claim must have an associated artifact: tests, logs, plots, benchmarks, or run metadata.
4. **Minimize token usage.** Prefer references to file paths and concise diffs over dumping large code blobs.
5. **Safe-by-default.** Avoid generating sensitive/regulated content. Keep domain-specific work at a high-level engineering focus unless explicitly scoped and authorized.

---

## Design Process (core-engineering)

All design work follows this 8-stage process:

```
Stage 1  Problem Definition              →  problem_statement.md
Stage 2  Problem Review and Clarification →  clarification_log.md
Stage 3  Problem Elaboration             →  assumptions_and_constraints.md
Stage 4  Requirements Derivation         →  requirements.md  (REQ blocks)
Stage 5  Integration Function (IF) Derivation   →  if_list.md
Stage 6  Integration Function Decomposition    →  if_decomposition.md
Stage 7  Unit Function (UF) Derivation         →  uf.md  (UF blocks)
Stage 8  Verification & Evidence Planning      →  verification_plan.md, evidence_pack/
```

---

## Standard Output Formats

### Requirement Block (REQ-###)
- **ID:** (REQ-###)
- **Context:**
- **Inputs:**
- **Outputs:**
- **Constraints:**
- **Acceptance Criteria:** (Given/When/Then + numeric thresholds)
- **Tests:** (unit/integration/e2e)
- **Evidence:** (paths to artifacts)

### IF Block (IF-##)
- **IF-ID:** (IF-##)
- **Description:**
- **Producer:**
- **Consumer:**
- **Input Contract:** (type, unit/shape, range)
- **Output Contract:** (type, unit/shape, range)
- **Constraints:** (timing, protocol, serialization)
- **Failure Modes:**
- **Linked REQs:** (REQ-###)

### UF Block (UF-##)
- **UF-ID:** (UF-##)
- **Parent IF:** (IF-##)
- **Goal:**
- **I/O Contract:**
- **Algorithm Summary:**
- **Edge Cases:**
- **Verification Plan:**
- **Evidence Pack Fields:** scenario_id, run_id, metrics, environment, commit_sha

---

## Token-Saving Rules (Do This)
- Refer to code using **paths and symbols** (e.g., `src/pipeline/processor.py::process()`).
- Ask for **minimal context**: file tree, specific functions, error logs.
- Prefer **patches/diffs** over full files.
- Split large changes into staged commits: (1) refactor, (2) behavior change, (3) tests/bench.

---

## Agent Orchestration Conventions
- **Agent-1 (Architect):** Design process Stage 1~7 — requirement/spec decomposition, IF/UF definition
- **Agent-2 (Builder):** Implementation with minimal diffs
- **Agent-3 (Verifier):** Stage 8 — tests, benchmarks, evidence pack, CI gates

Handoff format:
- **From Agent:** (1/2/3)
- **To Agent:** (1/2/3)
- **Objective:**
- **Context Links:** (file paths, issue IDs)
- **Deliverables:**
- **Constraints:**
- **Acceptance Tests:**
- **Evidence Outputs:**
