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

## Pipeline Insertion & Input Source (canonical)
- **When (single rule):** after `rd/uf.md` (or `rd/eq.md` from theory-decomposer) exists and **before `eval-planner` (Stage 8)**; always re-run after parameter/porting changes. (This supersedes conflicting timings in older manuals.)
- **Input source:** equations and assumptions from `rd/eq.md` EQ Blocks (`Equation`, `Assumptions`, `Validity Domain` fields) or `rd/uf.md` `Algorithm Summary`; parameter ranges from `rd/assumptions_and_constraints.md`; ask the user only for what these files do not carry.

## Downstream Handoff — eval wiring
Append audit-derived metrics and thresholds to **`rd/domain_metrics.md`** (create if missing):

```
| Metric | Direction | Baseline | Target | Unit | Rationale | Auditor |
|---|---|---|---|---|---|---|
| energy_drift | ↓ | <measured> | ≤ <tol> | %/s | conservation check EQ-## | sim-physics-auditor |
| timestep_margin | ↑ | <computed> | ≥ 2× | — | Nyquist/stability | sim-physics-auditor |
```

`eval-planner` reads `rd/domain_metrics.md` as a first-class input (its Inputs #3) and cites the auditor per adopted metric. Detailed audit bodies stay in `reports/physics/` (GLOBAL_RULES Rule 16).

## MCP Integration
- `mcp.shell`: run parameter sweeps, generate plots, calculate metrics
- `mcp.filesystem`: store sweep configuration and results in `reports/physics/`
- `mcp.github` (optional): open physics mismatch issues

---

## Token Saving
- Use brief symbol notation; store full derivations as file references.
- Store plots and raw results in `reports/physics/`.

See `references/reference.md` and `references/examples.md`.
