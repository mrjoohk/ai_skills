    ---
    name: agent-orchestration
    description: "Defines multi-agent roles, handoffs, and MCP-driven workflow orchestration."
    user-invocable: true
    allowed-tools: Read, Write
---

# Agent Orchestration

Defines a 3-agent workflow with consistent handoffs and MCP execution hooks.

## Roles
- **Agent-1 (Architect):** clarify requirements, UF decomposition, acceptance criteria
- **Agent-2 (Builder):** implement minimal diffs, keep code cohesive
- **Agent-3 (Verifier):** tests, benchmarks, evidence pack, CI gates

## When to Use
- Multi-module changes (SAR pipeline + tests + CI)
- RAG ingest + evaluation + index updates
- Any change requiring evidence packs and regressions tracking

## Handoff Template
Use the exact format below for token-efficient transfers:
- From Agent:
- To Agent:
- Objective:
- Context Links: (paths, issues, PRs)
- Deliverables:
- Constraints:
- Acceptance Tests:
- Evidence Outputs:

## MCP Integration Patterns
- `mcp.github`: create issues/PRs, post status comments
- `mcp.shell`: run build/test/bench
- `mcp.filesystem`: create `reports/`, `evidence_pack/`, `configs/`
- `mcp.webhook`: optional status notifications

## Token Saving
- Agent-2 should work from a minimal file set (list paths).
- Agent-3 should summarize failures with commands + key excerpts, then store full logs in artifacts.

See `reference.md` and `examples.md`.
