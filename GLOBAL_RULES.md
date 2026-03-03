# GLOBAL_RULES.md (Claude Code Skills Pack)

These global rules apply to all skills in this pack.

## Non-negotiables
1. **Be unambiguous.** Every requirement must be testable and measurable.
2. **Define contracts.** For any function/module: Inputs, Outputs, Constraints, Failure modes.
3. **Evidence-first.** Every significant claim must have an associated artifact: tests, logs, plots, benchmarks, or run metadata.
4. **Minimize token usage.** Prefer references to file paths and concise diffs over dumping large code blobs.
5. **Safe-by-default.** Avoid generating sensitive/regulated content. Keep defense-domain work at a high-level engineering focus unless explicitly scoped and authorized.

## Standard Output Formats
### Requirement Block
- **ID:** (REQ-###)
- **Context:**
- **Inputs:**
- **Outputs:**
- **Constraints:**
- **Acceptance Criteria:** (Given/When/Then + numeric thresholds)
- **Tests:** (unit/integration/e2e)
- **Evidence:** (paths to artifacts)

### UF Block
- **UF-ID:** (UF-##)
- **Goal:**
- **I/O Contract:**
- **Algorithm Summary:**
- **Edge Cases:**
- **Verification Plan:**
- **Evidence Pack Fields:** scenario_id, run_id, metrics, environment, commit_sha

## Token-Saving Rules (Do This)
- Refer to code using **paths and symbols** (e.g., `src/sar/bp.py::backproject()`).
- Ask for **minimal context**: file tree, specific functions, error logs.
- Prefer **patches/diffs** over full files.
- Split large changes into staged commits: (1) refactor, (2) behavior change, (3) tests/bench.

## Agent Orchestration Conventions
- **Agent-1 (Architect):** requirement/spec decomposition + design
- **Agent-2 (Builder):** implementation with minimal diffs
- **Agent-3 (Verifier):** tests, benchmarks, evidence pack, CI gates

Handoff format:
- **From Agent:** (1/2/3)
- **To Agent:** (1/2/3)
- **Objective:**
- **Context Links:** (file paths, issue IDs)
- **Deliverables:**
- **Constraints:**
- **Acceptance Tests:**
