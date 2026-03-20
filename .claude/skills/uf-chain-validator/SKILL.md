---
name: uf-chain-validator
description: "Validates UF-chain integrity, I/O contracts, tests, and evidence linkage."
user-invocable: true
allowed-tools: Read, Write
---

# UF Chain Validator

Validates UF-chain consistency:
- UF IDs are complete and ordered
- Each UF has an explicit I/O contract
- Tests exist and meet coverage gates
- Evidence pack references exist and are consistent

## When to Use
- Before merging a feature branch
- After adding or refactoring UF modules
- When coverage or evidence gates fail in CI

## Inputs
- Path(s) to UF definition files (e.g., `docs/uf/*.md`, `uf_chain.yaml`)
- Project source paths (e.g., `src/`)
- Test paths (e.g., `tests/`)
- Evidence pack root (e.g., `evidence_pack/`)

## Output
A validation report in Markdown:
- PASS/FAIL summary
- Missing UF blocks or broken links
- Missing tests or weak assertions
- Proposed fixes (minimal diffs)

## MCP Integration
- `mcp.filesystem`: scan UF docs and evidence directories
- `mcp.shell`: run `pytest -q`, `pytest --cov`, `ruff`, `mypy` (as applicable)
- `mcp.github`: comment on PRs with the report

## Token Saving
- Reference failing files + exact sections; avoid pasting whole documents.
- Provide patches/diffs for fixes.
- Summarize errors with paths and line numbers.

See `reference.md` for report format and `examples.md` for test prompts.
