---
name: code-reviewer
description: >
  Layered, independent code review against UF/IF contracts, requirements, and coding
  standards. Produces a structured finding report that cursor-task-formatter can turn
  into Cursor fix prompts. Supports three review layers: `uf_layer` (for UF implementation
  files produced by uf-implementor), `if_layer` (for IF integration modules produced by
  if-integrator), and `generic` (for arbitrary code with no linked spec). Must run as an
  independent sub-agent and inherits the common critic contract. Trigger after Cursor
  or uf-implementor / if-integrator has finished producing code. Users may say
  "코드 리뷰해줘", "리뷰 해줘", "구현 검토해줘", "코드 확인해줘", "review this code",
  "PR 리뷰", "버그 찾아줘", "개선점 찾아줘", "UF 구현 리뷰", "IF 통합 리뷰". Also
  trigger automatically in the orchestrator after builder/uf-implementor or
  builder/if-integrator completes.
allowed-tools: Read, Write

pipeline:
  role: verifier
  stage: "review"

  review_layers:
    - id: uf_layer
      role: verifier-critic
      critic_of: uf-implementor
      inputs:
        required:
          - path: src/uf/**/*.py
            producer: uf-implementor
          - path: uf.md
            producer: uf-designer
        optional:
          - path: tests/unit/**
          - path: docs/ai/tasks/*.md
        forbidden:
          - path: .pipeline/handoffs/*uf-implementor*.json
            reason: "Producer's self-claim of correctness — §2.2 of critic_contract."
          - path: reports/impl/uf_impl_report_*.md
            reason: "Producer-emitted self-report; reading it primes the critic with the producer's status claims."
      fanout:
        strategy: per-file
        scope_key: file_path
        max_parallel: 6
      reference: references/review_criteria_uf.md

    - id: if_layer
      role: verifier-critic
      critic_of: if-integrator
      inputs:
        required:
          - path: src/if/**/*.py
            producer: if-integrator
          - path: if_list.md
            producer: if-designer
        optional:
          - path: tests/integration/**
          - path: uf.md
          - path: requirements.md
        forbidden:
          - path: .pipeline/handoffs/*if-integrator*.json
            reason: "Producer self-claim — §2.2."
          - path: reports/impl/if_integration_report_*.md
            reason: "Producer-emitted self-report."
      fanout:
        strategy: per-if
        scope_key: parent_if
        max_parallel: 4
      reference: references/review_criteria_if.md

    - id: generic
      role: verifier
      critic_of: null
      inputs:
        required:
          - path: <caller-specified source paths>
        optional:
          - path: docs/
      forbidden: []
      fanout:
        strategy: per-file
        max_parallel: 6
      reference: references/review_criteria_generic.md

  outputs:
    files:
      - path: "reports/review/<layer>_<timestamp>_review.md"
        kind: report
    status_enum: [COMPLETE, BLOCKED]

  human_in_loop:
    required: false

  validator:
    script: "<skill_dir>/scripts/validate_review.py"
    json_output: true

  downstream:
    - next: builder/cursor-task-formatter
      when: "layer == uf_layer && findings.length > 0 && verdict != BLOCK"
    - next: builder/cursor-task-formatter
      when: "layer == if_layer && findings.length > 0 && verdict != BLOCK"
    - next: orchestrator_advance
      when: "verdict == APPROVE"
    - next: user_escalation
      when: "verdict == BLOCK"

critic_contract:
  inherits: ../_shared/critic_contract.md
  contract_version: "1.0"
  applies_to_layers: [uf_layer, if_layer]
  independence: spawn_in_fresh_subagent
  require_alternatives: false        # fact-based review; code has no "alternative designs"
  require_statistical_rigor: false
  verdict_enum: [APPROVE, REQUEST_CHANGES, BLOCK]
  iteration_limit: 2
---

# Code-Reviewer — Three Review Layers

Reviews code with layer-appropriate criteria and produces a finding report that feeds
directly into `cursor-task-formatter` for automated fix-prompt generation.

The three layers differ in **what the code is checked against**:

| Layer | Contract source | What the critic asks |
|---|---|---|
| `uf_layer` | `uf.md` UF Block for the reviewed function | Does this function satisfy its UF spec — signature, I/O, edge cases, verification plan? |
| `if_layer` | `if_list.md` IF Block + UF call graph | Does this module orchestrate UFs correctly and satisfy the IF's I/O contract and acceptance criteria? |
| `generic` | External coding standards only | Is this code correct, readable, and safe, given no formal spec? |

> **Read `../_shared/critic_contract.md` first** for layers `uf_layer` and `if_layer`.
> Generic layer is Verifier, not Critic — it does not inherit the contract's §2.3
> (alternatives mandate) but does follow §2.1 (independence) and §2.2 (input whitelist).
>
> **Read `references/review_criteria_<layer>.md`** before starting.
> **Use `assets/review_report_template.md`** as output skeleton.

---

## Bundled Resources

| File | When to use |
|---|---|
| `../_shared/critic_contract.md` | Common critic contract for `uf_layer` and `if_layer` |
| `references/review_criteria_uf.md` | UF-layer checklists (contract, logic, quality, tests) |
| `references/review_criteria_if.md` | IF-layer checklists (orchestration, contract satisfaction, integration tests) |
| `references/review_criteria_generic.md` | Generic checklist (legacy — no spec linkage) |
| `assets/review_report_template.md` | Fill-in template for the finding report |
| `scripts/validate_review.py` | Self-validator: confirms report has all mandatory sections + JSON handoff |

---

## Layer Selection

The orchestrator selects the layer. If invoked without a layer argument:

1. If the target path matches `src/uf/**` → default to `uf_layer`.
2. If the target path matches `src/if/**` → default to `if_layer`.
3. If neither matches → default to `generic` and log `layer_auto_selected=generic` in handoff JSON.

Users may override with `--layer uf_layer | if_layer | generic`. Mixing layers in a single
invocation is disallowed — spawn separate instances per layer.

---

## Review Lenses (apply to all layers; criteria files differ per layer)

### Lens 1 — Contract Compliance

Applies only to `uf_layer` and `if_layer`. Checks each reviewed function against its spec
(UF Block or IF Block).

- [ ] Signature matches spec (param names, types, return type).
- [ ] All inputs validated against spec constraints (type / unit / range / shape).
- [ ] Output shape/type matches spec exactly — no silent reshape or downcast.
- [ ] Every documented edge case handled with the behavior stated in the spec.
- [ ] No undocumented side effects (writes to globals, emits logs outside spec).

For `if_layer` additionally:
- [ ] IF entry-point function exposes only the spec's I/O; internal UF signatures do not leak.
- [ ] UF call sequence matches dependency graph in `if_decomposition.md` as *implied* by call order (do not read the decomposition file directly — §2.2 of contract).
- [ ] Postcondition checks present for every IF acceptance criterion.

**Severity:** Contract violation (wrong output type, missing mandated edge case, leaked internal) → **CRITICAL**.

### Lens 2 — Logic Correctness

Applies to all layers.

- [ ] Off-by-one: loop bounds, slice indices, range ends.
- [ ] Null / None / undefined: all nullable inputs guarded.
- [ ] Type coercion: no implicit conversions that could lose data.
- [ ] Branching completeness: every logical state handled.
- [ ] Error propagation: exceptions caught at the appropriate level (not swallowed, not over-broad).
- [ ] Mutation safety: shared state not mutated across call boundaries.
- [ ] Async/await: promises/awaitables not dropped.
- [ ] Resource lifecycle: files/sockets/locks released on all paths (including exceptions).

**Severity:** Logic error producing wrong results on known inputs → **CRITICAL**. Unhandled exception path that crashes in production → **CRITICAL**. Silent error-swallow → **WARN**.

### Lens 3 — Code Quality

Applies to all layers.

- [ ] Names represent what, not how.
- [ ] Single responsibility per function.
- [ ] No copy-pasted logic ≥ 5 lines.
- [ ] Magic numbers/strings extracted to named constants.
- [ ] Comments on non-obvious logic; no commented-out dead code.
- [ ] Public API documented (types, raises, returns).

**Severity:** Duplication < 5 lines / style inconsistency → **SUGGEST**. Missing docstring on public function → **WARN**.

### Lens 4 — Test Coverage

Applies to all layers when tests are available.

- [ ] Each acceptance criterion has at least one asserting test.
- [ ] Tests assert specific outputs with numeric tolerance, not just "no exception".
- [ ] Negative tests exist for declared edge cases.
- [ ] Fixtures are deterministic (seeded) where randomness is involved.

For `if_layer` additionally:
- [ ] Integration tests exercise the full UF chain through the IF entry point, not just direct-call unit tests.

**Severity:** Missing test for spec-covered criterion → **WARN**. Flaky / nondeterministic test → **WARN**. Assertions that always pass (e.g., `assert result is not None` only) → **CRITICAL**.

### Lens 5 — Security (all layers, only when applicable)

- [ ] No raw SQL or command injection.
- [ ] No secrets hardcoded.
- [ ] External inputs sanitized before use.
- [ ] File-path inputs restricted to allowed directories.

**Severity:** Injection risk / hardcoded secret → **CRITICAL**. Missing sanitization on external input → **WARN**.

---

## Execution Flow

### Phase A — Integrity Check (uf_layer, if_layer)

1. Verify none of the layer's forbidden inputs are in scope. If any present: `BLOCK` with `forbidden_input_exposure`.
2. Verify required spec file (`uf.md` for uf_layer, `if_list.md` for if_layer) is readable. If not: `BLOCK` with `missing_spec_reference`.
3. SHA-256 hash required artifacts for handoff.

For `generic` layer, skip integrity check (no spec, no forbidden list).

### Phase B — Scope Resolution

- `uf_layer`: iterate over files under `src/uf/`; for each function, resolve its UF-ID by
  filename pattern (`if_XX_<name>.py` → UF-XX-*) and locate the UF Block in `uf.md`.
- `if_layer`: iterate over files under `src/if/`; for each entry-point function, locate
  the IF Block in `if_list.md`.
- `generic`: iterate over paths specified by the caller.

### Phase C — Lens Application

Apply lenses in order. For each finding use the format in `../_shared/critic_contract.md` §3.

Example:
```
[CRITICAL] FIND-UF-01-03-01: Output dtype mismatch
  What:      uf_01_03_resize() returns float64 but UF-01-03 spec says float32
  Why:       Downstream UF-01-04 expects float32; silent upcast costs 2× memory
  Fix:       Cast result to np.float32 before return
  Affected:  src/uf/if_01_resize.py:47
```

For `if_layer`, every finding ID uses `FIND-IF-<IF-ID>-<N>`.
For `uf_layer`, every finding ID uses `FIND-UF-<UF-ID>-<N>`.
For `generic`, every finding ID uses `FIND-GEN-<file-slug>-<N>`.

### Phase D — Verdict

| Condition | Verdict |
|---|---|
| Any CRITICAL finding | `BLOCK` |
| `forbidden_input_exposure` or `missing_spec_reference` | `BLOCK` |
| WARN ≥ 3 across the scope | `REQUEST_CHANGES` |
| WARN = 1 or 2 | `REQUEST_CHANGES` when scope is a single file/IF; otherwise `APPROVE` with findings |
| Only SUGGEST or none | `APPROVE` |

### Phase E — Report Emission

1. Write `reports/review/<layer>_<timestamp>_review.md` using `assets/review_report_template.md`.
2. Emit handoff JSON (§4.2 of common contract).
3. Run `scripts/validate_review.py`.
4. If any WARN or CRITICAL remain, include the instruction at the report end:
   > "Run `cursor-task-formatter --mode fix` on this report to generate Cursor fix prompts."

### Phase F — Fan-Out Merge (orchestrator responsibility)

When fan-out is active (per-file for uf_layer/generic, per-if for if_layer):

- Each instance emits its own report.
- Orchestrator merges: concatenate Findings sections preserving per-instance ID namespaces
  (no re-numbering); compute overall verdict as `max(verdicts)` in severity order
  (BLOCK > REQUEST_CHANGES > APPROVE).
- Emit a single aggregate report `reports/review/<layer>_<timestamp>_review_merged.md`
  and aggregate handoff JSON.

---

## Rules

### Common (all layers)
1. Be specific: cite file, line number, and exact variable/function names.
2. Every finding includes a "Fix:" line stating correct behavior — not exact code.
3. Do not invent requirements. Behavior not in the spec is at most `SUGGEST` (except for
   security/safety issues, which are always `CRITICAL`).
4. Review only changed lines when reviewing a PR, unless changes break existing contracts.

### Layer-specific
5. **`uf_layer` critics** must read the UF Block in `uf.md` before writing findings. Not the producer's impl report, not the handoff JSON.
6. **`if_layer` critics** must cross-check the IF entry-point against the IF Block's acceptance criteria. Postcondition asserts missing → CRITICAL.
7. **`generic` layer** does not apply Lens 1 (no contract to check); uses only Lenses 2–5.
8. **Do not propose refactors that span beyond the changed scope** unless the scope itself is broken. Critic scope is the reviewed code; larger rewrites belong in follow-up tickets.

---

## Known Limits

- Critics cannot execute code. Static analysis only. Run-time defects (race conditions,
  memory pressure under load, gradient instability) are flagged as hypotheses with WARN
  severity; eval-result-critic and gpu-hpc-guard catch runtime effects.
- `uf_layer` cannot cross-check against UF-to-UF chain continuity beyond the reviewed
  file. That's `uf-chain-validator --mode mechanical`'s job.
- `if_layer` cannot verify REQ satisfaction end-to-end; that's `eval-result-critic`.
- `generic` layer lacks spec linkage and produces the weakest findings. Prefer `uf_layer`
  or `if_layer` whenever a spec exists.
