---
name: uf-chain-validator
description: >
  Two-mode validator for UF design and UF-chain integrity. Mode `mechanical` performs
  structural checks (UF-ID continuity, I/O contract presence, test mapping, evidence
  linkage, IF→UF coverage) and produces uf_if_coverage_review.md. Mode `critique`
  performs independent adversarial review of UF design quality (algorithm choice,
  edge-case representativeness, I/O precision, verification plan realism) and produces
  reports/critique/uf_design_<timestamp>_critique.md. Critique mode inherits the
  common critic contract and must run in a fresh sub-agent. Trigger mechanical mode
  before merging feature branches, after adding UF modules, or when coverage/evidence
  gates fail. Trigger critique mode after uf-designer produces uf.md and before
  uf-implementor starts. Users can invoke both modes with keywords like "UF 검증",
  "UF chain 점검", "UF 설계 비판", "UF design critique", "커버리지 체크",
  "UF 체인 유효성", "uf_if_coverage_review", "UF 7.5 검토".
allowed-tools: Read, Write

pipeline:
  role: verifier
  stage: "7.5"

  modes:
    - id: mechanical
      role: verifier
      stage: "7.5-mechanical"
      inputs:
        required:
          - path: uf.md
            producer: uf-designer
          - path: if_list.md
            producer: if-designer
        optional:
          - path: src/uf/
            producer: uf-implementor
          - path: tests/
            producer: uf-implementor
          - path: evidence_pack/
            producer: ci-evidence-automation
      outputs:
        files:
          - path: uf_if_coverage_review.md
            kind: report
        status_enum: [COMPLETE, PARTIAL, BLOCKED]
      human_in_loop:
        required: false
      fanout:
        strategy: none
      gate: true
      downstream:
        - next: builder/uf-implementor
          when: "passed && no UNCOVERED"
        - next: architect/uf-designer
          when: "has UNCOVERED"
        - next: architect/if-designer
          when: "has REDUNDANT_IF"

    - id: critique
      role: verifier-critic
      stage: "7-review"
      critic_of: uf-designer
      inputs:
        required:
          - path: uf.md
            producer: uf-designer
          - path: if_list.md
            producer: if-designer
        optional:
          - path: requirements.md
        forbidden:
          - path: if_decomposition.md
            reason: "Producer's decomposition rationale — reading it causes the critic to inherit producer's design path (§2.2 of critic_contract)."
          - path: .pipeline/handoffs/*uf-designer*.json
            reason: "Producer's self-claim of correctness."
      outputs:
        files:
          - path: "reports/critique/uf_design_<timestamp>_critique.md"
            kind: report
        status_enum: [COMPLETE, BLOCKED]
      human_in_loop:
        required: false
      fanout:
        strategy: per-if
        scope_key: parent_if
        max_parallel: 4
      validator:
        script: "<skill_dir>/scripts/validate_critique.py"
        json_output: true
      downstream:
        - next: builder/uf-implementor
          when: "verdict == APPROVE"
        - next: architect/uf-designer
          when: "verdict == REQUEST_CHANGES && iteration < 2"
        - next: user_escalation
          when: "verdict == BLOCK || iteration >= 2"

critic_contract:
  inherits: ../_shared/critic_contract.md
  contract_version: "1.0"
  applies_to_modes: [critique]
  independence: spawn_in_fresh_subagent
  require_alternatives: true
  require_statistical_rigor: false
  verdict_enum: [APPROVE, REQUEST_CHANGES, BLOCK]
  iteration_limit: 2
---

# UF Chain Validator — Mechanical Checks + Independent Critique

Two distinct operating modes on the same inputs. The orchestrator selects which mode to
invoke; both modes can be run on the same `uf.md` but must be invoked separately with
`--mode mechanical` or `--mode critique`.

| Mode | What it checks | Produces | Gate semantics |
|---|---|---|---|
| `mechanical` | UF-ID continuity, I/O contract presence, test/evidence linkage, IF→UF coverage, chain continuity | `uf_if_coverage_review.md` | Blocks on UNCOVERED or REDUNDANT_IF |
| `critique`   | Algorithm appropriateness, edge-case representativeness, I/O precision, verification plan realism | `reports/critique/uf_design_<timestamp>_critique.md` | Blocks on CRITICAL verdict; loops on REQUEST_CHANGES |

> **For critique mode only:** read `../_shared/critic_contract.md` **before** doing anything
> else. All rules in the common critic contract apply. If the orchestrator invoked this
> skill without mode selection, default to `mechanical` and note the ambiguity.

---

## Bundled Resources

| File | When to use |
|---|---|
| `../_shared/critic_contract.md` | Common contract for critique mode (independence, verdict, iteration) |
| `references/reference.md` | Legacy mechanical-mode report format (existing) |
| `references/examples.md` | Example mechanical reports (existing) |
| `references/critique_criteria.md` | **New.** Critique-mode lens checklists and severity tables |
| `references/README_kr.md` | Korean README (existing) |
| `assets/mechanical_report_template.md` | Fill-in template for `uf_if_coverage_review.md` |
| `assets/uf_critique_template.md` | Fill-in template for critique-mode output |
| `scripts/validate_chain.py` | Mechanical mode self-validator |
| `scripts/validate_critique.py` | Critique mode self-validator |

---

## Mode: `mechanical`

This preserves the skill's original behavior. Use when you need a structural pass/fail
gate — not a design review.

### Inputs
- Required: `uf.md`, `if_list.md`
- Optional: `src/uf/`, `tests/`, `evidence_pack/`

### Check Items (mirrors legacy `references/reference.md`)

| # | Check | PASS criterion |
|---|---|---|
| 1 | UF-ID continuity and uniqueness | No duplicate or missing numbers in `UF-[parent_IF]-[seq]` scheme |
| 2 | I/O contract present per UF | Type + unit + shape + range on every input/output |
| 3 | Test mapping | Unit test path declared for each UF |
| 4 | Acceptance criteria non-trivial | Not just smoke tests; numeric thresholds present |
| 5 | Evidence-pack reference | Path and schema declared for UF producing artifacts |
| 6 | CI gate matches local expectations | Coverage thresholds consistent |
| 7 | IF→UF coverage | Every IF acceptance criterion covered by ≥ 1 UF |
| 8 | UF→IF attribution | Every UF has a parent IF and appears in `if_decomposition.md` |
| 9 | I/O chain continuity | Output type/shape of UF-N matches input of consumer UF-M |

### Output Format

Use `assets/mechanical_report_template.md`. The schema is the same as `references/reference.md`:

```
# UF Chain Validation Report
- Project / Commit / Date / Validator Version / UF Scope / IF Scope

## Summary
- PASS count / WARN count / FAIL count / Overall coverage / Priority fixes

## Findings Table
| UF-ID | Status | Issue Type | Location | Evidence | Fix Proposal |
```

### Verdict (mechanical)

- `PASS` — all checks green; orchestrator advances to `builder/uf-implementor`.
- `WARN` — non-blocking issues (e.g., weak acceptance assertion); proceed with notes.
- `FAIL` — at least one `UNCOVERED` or `REDUNDANT_IF` or chain break; route back to `uf-designer` or `if-designer`.

Mechanical mode does **not** use the critic verdict enum. Its output is a PASS/WARN/FAIL
summary, not an APPROVE/REQUEST_CHANGES/BLOCK judgement.

---

## Mode: `critique`

Independent adversarial review of UF design quality. Catches semantic defects that
mechanical checks cannot see.

### Independence Requirements

- **Must** spawn in a fresh sub-agent. If the orchestrator invokes this mode in the same
  context as `uf-designer`, refuse with `BLOCK: shared_context_violation`.
- **Must** read `../_shared/critic_contract.md` before proceeding.
- **Must not** read `if_decomposition.md` or any producer handoff log. These capture the
  producer's decomposition reasoning and are explicitly forbidden (§2.2 of contract).

### Inputs (strict)

| Status | Path | Purpose |
|---|---|---|
| required | `uf.md` | Primary artifact under review |
| required | `if_list.md` | Upstream contract — parent IF I/O to cross-check |
| optional | `requirements.md` | Origin REQ for deepest traceability |
| **forbidden** | `if_decomposition.md` | Producer's tree/rationale. Do not open. |
| **forbidden** | `.pipeline/handoffs/*uf-designer*.json` | Producer's own claim. Do not open. |

### Review Lenses (per UF Block)

**Lens C-1 — Algorithm Appropriateness.**
- Is the named algorithm the right choice for the task class?
- What are 2+ alternative algorithms? What trade-off axis separates them (accuracy vs compute, memory vs latency, generality vs domain-fit)?
- Is a known-failure-mode of the chosen algorithm unaddressed? (e.g., "letterbox resize" + "non-multiple-of-32 input" → padding artifact if not handled)

Checklist in `references/critique_criteria.md` §Lens-C1.

**Lens C-2 — Edge-Case Representativeness.**
- Are the stated edge cases the 3+ **most likely** to fail in production, or just the easy-to-write ones?
- Domain-specific must-haves: NaN/Inf for numeric, empty/None for optional, oversized input, shape mismatches between UFs, resource exhaustion, concurrency (if UF is reentrant).
- Score coverage: {has_all, has_most, has_only_easy}. `has_only_easy` → WARN.

Checklist in `references/critique_criteria.md` §Lens-C2.

**Lens C-3 — I/O Contract Precision.**
- Type + unit/shape + range declared for every input and output?
- Coordinate system declared for spatial data (pixel / normalized / world)?
- Implicit type conversions between UF-N and UF-(N+1) flagged?
- Does the UF's output actually satisfy the parent IF's input contract (cross-check via `if_list.md`)?

Checklist in `references/critique_criteria.md` §Lens-C3.

**Lens C-4 — Verification Plan Realism.**
- Named test function paths: do they follow the repo's test layout?
- Named fixtures: can they actually be constructed? (e.g., "a 4-channel 48 kHz recording with known SNR" — is such a fixture generatable?)
- Coverage target (default `>= 90%`): justified, or rubber-stamp?
- Performance/memory benchmarks declared if UF is performance-critical?

Checklist in `references/critique_criteria.md` §Lens-C4.

### Execution Flow (critique mode)

#### Phase A — Integrity Check
1. Verify forbidden inputs are not in scope. If any present: `BLOCK` with `forbidden_input_exposure`.
2. Verify required inputs readable. If not: `BLOCK` with `missing_required_input`.
3. SHA-256 hash required artifacts for handoff.

#### Phase B — Enumerate UFs
- Parse `uf.md` into UF Blocks.
- If `fanout: per-if` is engaged by the orchestrator, the critic instance is scoped to UFs under one parent IF only; otherwise review all UFs.

#### Phase C — Apply Lenses
- For each in-scope UF, apply C-1 through C-4.
- Record findings in the format from `../_shared/critic_contract.md` §3.

#### Phase D — Alternatives Analysis
Pick top-3 most impactful UFs in scope (by: (a) Primary-metric relevance, (b) cross-IF boundary position, (c) algorithmic complexity). For each:
- Propose ≥ 2 alternative algorithms or decompositions.
- State trade-off axis.
- Declare defensibility of current choice given parent IF's I/O contract.

#### Phase E — Verdict

```
BLOCK              if (CRITICAL ≥ 1)
                  OR (any UF has no Edge Cases at all)
                  OR (any UF output type ≠ parent IF input type without explicit conversion)
                  OR (forbidden_input_exposure)
                  OR (missing_required_input)

REQUEST_CHANGES    if (WARN ≥ 2 within a single parent IF scope)
                  OR (WARN = 1 AND Lens-C1 algorithm unjustified)

APPROVE            otherwise
```

#### Phase F — Report Emission
- Write `reports/critique/uf_design_<timestamp>_critique.md` using `assets/uf_critique_template.md`.
- Emit handoff JSON block per `../_shared/critic_contract.md` §4.2.
- Run `scripts/validate_critique.py` on the emitted report.

### Fan-Out Protocol

When orchestrator spawns one critique instance per parent IF:
- Each instance's `--scope IF-<id>` argument limits review to UFs with matching `Parent IF`.
- Each instance emits its own report; orchestrator merges by concatenating Findings sections
  and computing the overall verdict as `max(verdicts, severity_order)`.
- Merge rule: if any IF-scoped instance returns `BLOCK`, overall verdict is `BLOCK`.
  Otherwise if any returns `REQUEST_CHANGES`, overall is `REQUEST_CHANGES`.

---

## Rules Specific to This Skill

### Mechanical mode
1. Do not interpret design quality; report what is or is not present.
2. Use path + symbol references; do not paste large code blocks.
3. Provide minimal-diff fix proposals where possible.

### Critique mode (in addition to common critic contract)
1. **Never open `if_decomposition.md`.** If it appears in context, record the exposure in the report and emit `BLOCK` with `forbidden_input_exposure`.
2. **Alternatives are mandatory even on APPROVE.** An APPROVE verdict without the top-3 alternatives section is invalid.
3. **Do not propose specific UF rewrites.** Fix fields state what the block *should specify*, not exact algorithm code.
4. **Cross-check against `if_list.md`.** Every leaf UF's output type must satisfy its parent IF's expected input, verified mechanically within this mode.
5. **Fan-out instances are independent.** Do not share findings across IF-scoped instances except through the orchestrator's merge step.

---

## Mode Selection Heuristic (for the orchestrator, informational)

| Situation | Mode to invoke |
|---|---|
| `uf-designer` just emitted `uf.md` | `critique` first, then on APPROVE → `mechanical` before `uf-implementor` |
| `uf-implementor` just completed | `mechanical` only (chain continuity, test linkage) |
| CI gate failed | `mechanical` only |
| Pre-merge gate | `mechanical` only |
| User says "check UF design quality" | `critique` |
| User says "validate coverage" | `mechanical` |

If ambiguous and the orchestrator cannot decide, default to `mechanical` and log
`ambiguous_mode_selection` in the handoff JSON. Users can re-run with explicit mode.

---

## Known Limits

### Mechanical mode
- Does not detect semantic defects — an algorithmically wrong UF with a correct I/O signature will pass.
- Chain-continuity check is type-level; value-range compatibility is not verified.

### Critique mode
- Algorithm appropriateness judgement depends on the critic's domain knowledge and the completeness of `references/critique_criteria.md` reference tables. Domains not covered in the reference tables produce weaker critiques.
- Fan-out per IF may miss cross-IF design issues (e.g., two IFs duplicating the same UF under different names). These are caught by mechanical mode's coverage check.
- Verification plan realism (Lens C-4) cannot confirm that a named test fixture actually exists in the repo — only that the spec names one. Pair with `mechanical` mode for repo-side existence checks.
