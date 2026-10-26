---
name: sim-physics-auditor
description: "Audits physics and simulation consistency: units, dimensions, coordinate frames, numerical stability, and domain-specific invariants."
user-invocable: true
allowed-tools: Read, Write
---

# Sim Physics Auditor

Audits physics simulation consistency and numerical accuracy:
- Units and Dimensions validation
- Coordinate Frames consistency verification
- Sampling theory compliance (Nyquist, time resolution, etc.)
- Numerical stability verification (control loops, integrators, filters)
- Bandwidth·resolution relationship verification
- Equation equivalence validation for cross-language porting

---

## When to Use
- Always before trusting numerical results
- When changing simulation parameters (frequency, velocity, sample rate, step size, etc.)
- When porting physics equations to different languages/frameworks (e.g., Python → C++ → C#)
- When changing control loop or filter design
- When adding new physics domain modules (signal processing, dynamics, optics, acoustics, etc.)

---

## Inputs
- Equations, formulas and assumptions
- Parameter ranges (frequency, velocity, step size, lookup range, etc.)
- Expected outputs (resolution, error bounds, SNR proxy, stability margin, etc.)
- Domain hints (signal processing / dynamics / optics / thermal / control, etc.)

---

## Output
- **PASS / WARN / FAIL checklist**
- List of suspected equation mismatches (path·symbol references)
- Recommended verification experiment plan
- Acceptance thresholds and list of plots to generate

---

## Pipeline Insertion & Input Source
- **When:** in an engineering pipeline, audit available equations or implementation before their metrics are adopted by `eval-planner` (Stage 8). Recheck the affected equations after parameter/porting changes. Standalone audits can use supplied equations and code without creating UF/EQ documents.
- **Input source:** equations and assumptions from canonical EQ Blocks (`Equation`, `Assumptions`, `Validity Domain`), UF `Algorithm Summary`, or code; parameter ranges from existing constraints/configuration. Ask only for missing information that is necessary for the audit.
- **Paths:** honor user-specified outputs and existing canonical locations. `rd/eq.md`, `rd/uf.md`, `rd/domain_metrics.md`, and `reports/physics/` are optional defaults for a new project, not prerequisites.

## Downstream Handoff — eval wiring
Return audit-derived metrics and proposed thresholds to main in the following form. Distinguish computed estimates from measured results and cite the source evidence for measured baselines.

```
| Metric | Direction | Baseline | Target | Unit | Rationale | Auditor |
|---|---|---|---|---|---|---|
| energy_drift | ↓ | <measured> | ≤ <tol> | %/s | conservation check EQ-## | sim-physics-auditor |
| timestep_margin | ↑ | <computed> | ≥ 2× | — | Nyquist/stability | sim-physics-auditor |
```

Main verifies the results and is the single writer that merges accepted metrics into the project's canonical `domain_metrics.md` for `eval-planner`. Parallel workers return messages or write only to an assigned unique fragment, for example `reports/physics/<task-id>/domain_metrics.md`; they must not append to the shared canonical file. Reuse approved thresholds and mark new proposals as proposals. If this audit is used as a required gate, dependent work waits until its required criteria pass.

## Runtime Integration
- Use available execution/plotting tools for authorized parameter sweeps and metric calculations.
- Persist sweep configurations and results only in the assigned project/task paths when requested or needed for resumption.
- Use connected issue tools when issue creation is within the user's request.

---

## Token Saving
- Use brief symbol notation; store full derivations as file references.
- When files are needed, store plots and raw results in the project's report location and assigned unique task path.

See `references/reference.md` and `references/examples.md`.
