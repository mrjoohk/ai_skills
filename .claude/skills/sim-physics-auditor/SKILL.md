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

## MCP Integration
- `mcp.shell`: run parameter sweeps, generate plots, calculate metrics
- `mcp.filesystem`: store sweep configuration and results in `reports/physics/`
- `mcp.github` (optional): open physics mismatch issues

---

## Token Saving
- Use brief symbol notation; store full derivations as file references.
- Store plots and raw results in `reports/physics/`.

See `reference.md` and `examples.md`.
