---
name: uf-if-debug-mapper
description: "Maps UF/IF issues to code locations and generates a human-in-the-loop debugging plan."
user-invocable: true
allowed-tools: Read, Write
---

# UF/IF Debug Mapper

This skill generates a **human-in-the-loop** Markdown document that helps you quickly answer:

- *Given a UF (Unit Function) or IF (Integration Function / Interface Function) and a suspected problem,*  
  **which code should I debug** and **how**?

It is designed for workflows where you (the human) will directly intervene to patch code, while agents help with:
- anticipating failure modes,
- mapping them to concrete files/functions,
- proposing minimal, testable fixes,
- and capturing evidence.

## When to Use
- You have a UF-chain or IF-layer design and want a debugging guide *before implementation*.
- A CI failure/regression happened and you want a fast "where to look" map.
- A runtime symptom appears (OOM, wrong units, unstable loop, bad networking) and you need a reproducible triage plan.

## Inputs (what you should provide)
- UF list (e.g., UF-01..UF-27) and/or IF list (IF-01..)
- Module layout (top-level directories)
- Known error logs / stack traces (optional but helpful)
- Runtime constraints (e.g., 120 Hz loop, peak VRAM <= 18GB)

## Output
Creates a single Markdown guide, recommended location:
- `docs/uf_if_debug_map.md`

The guide includes:
1. **UF→Code Mapping**
2. **IF→Code Mapping**
3. **Symptom→Likely Root Cause Table**
4. **Debug Playbooks** (commands, breakpoints, logs)
5. **Minimal-Fix Patterns** (small diffs)
6. **Evidence Outputs** (reports, logs, plots)

## MCP Integration (Optional Hooks)
- `mcp.filesystem`: scan repo structure and generate the mapping doc
- `mcp.shell`: run repro commands, tests, minimal benchmarks
- `mcp.github`: open issues, comment with the generated map, link evidence
- `mcp.webhook`: notify on regression (optional)

## Token Saving Rules
- Prefer producing **path+symbol** references (e.g., `src/sar/bp.py::backproject()`).
- Do not paste entire files; store full logs under `reports/`.
- Provide diffs for suggested fixes.

## Agent Orchestration Link
- **Agent-1 (Architect):** generate/refresh the mapping doc from UF/IF specs and repo tree
- **Agent-2 (Builder):** implement minimal fixes in mapped locations
- **Agent-3 (Verifier):** add tests and evidence artifacts; validate in CI

See `reference.md` for the exact document template and `examples.md` for test prompts.
