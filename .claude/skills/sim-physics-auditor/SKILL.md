    ---
    name: sim-physics-auditor
    description: "Audits physics consistency (units, Nyquist, PRF, Doppler, dynamics) and assumptions."
    user-invocable: true
    allowed-tools: Read, Write
---

# Sim Physics Auditor

Audits physics and simulation consistency for SAR and UAV dynamics:
- units and dimensions
- coordinate frames
- Nyquist, PRF vs Doppler bandwidth
- bandwidth/resolution relations
- stability checks for control loops

## When to Use
- Before trusting numeric results
- When changing radar/platform parameters
- When porting equations between languages (C/Fortran/Python/C#)

## Inputs
- Equations + assumptions
- Parameter ranges (fc, B, v, altitude, look angle, PRF)
- Expected outputs (resolution, swath, SNR proxy, stability margins)

## Output
- checklist PASS/WARN/FAIL
- suspected inconsistent equations
- recommended validation experiments
- acceptance thresholds and plots to generate

## MCP Integration
- `mcp.shell`: run parameter sweeps, generate plots, compute metrics
- `mcp.filesystem`: store sweep configs + results
- optional `mcp.github`: open issues for physics inconsistencies

## Token Saving
- Use short symbolic representations and point to files for full derivations.
- Store plots and raw results under `reports/physics/`.

See `reference.md` and `examples.md`.
