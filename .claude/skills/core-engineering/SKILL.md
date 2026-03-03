    ---
    name: core-engineering
    description: "Global rules for requirements, verification, and integration across projects."
    user-invocable: false
    allowed-tools: Read, Write
---

# Core Engineering

This skill defines **global engineering rules** for requirement clarity, verification, and integration.
It is designed as a foundation for all other skills in this pack.

## When to Use
- You need to convert a vague goal into testable requirements.
- You are about to start a UF-chain decomposition.
- You want a consistent acceptance criteria / evidence structure across modules.

## Execution Rules
1. Always produce **testable** acceptance criteria.
2. Always specify **I/O contracts** (types, units, coordinate frames, shapes).
3. Prefer minimal diffs and file references to save tokens.
4. Define evidence artifacts for each claim.

## Standard Deliverables
- `requirements.md` with REQ blocks
- `uf.md` with UF blocks
- `verification_plan.md` (unit + integration + e2e)
- `evidence_pack/` structure proposal

## MCP Hooks (Optional)
- `mcp.shell`: run lint/tests/bench commands
- `mcp.filesystem`: create/update requirements and test plans
- `mcp.github`: open issues, link PRs, attach evidence artifacts

## Output Templates
See: `reference.md`.
