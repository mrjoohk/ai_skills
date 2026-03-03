# Claude Code Skills Pack (Engineering + Simulation + RAG)

This pack provides 7 reusable skills tailored for:
- Simulation engineering (SAR/UAV), GPU/HPC constraints, physics consistency
- UF-chain (unit-function) decomposition and validation
- RAG data quality and evaluation
- CI + evidence pack automation
- Multi-agent orchestration with MCP templates

## Install
Copy the `.claude/skills` directory into your repo:

```
cp -r .claude/skills <your-project>/.claude/
```

## Token-saving usage
- Invoke a skill only when needed.
- Reference paths instead of pasting big files.
- Use the provided prompts in each skill’s `examples.md`.

## MCP integration
This pack assumes you have one or more MCP servers configured (names are placeholders):
- `shell` (run commands)
- `filesystem` (read/write files)
- `github` (issues/PRs)
- `chroma` or vector store (optional)
- custom servers: `webhook`, `ci`, `eval`, etc.

Use `scripts/generate_mcp_templates.py` to generate a project-specific MCP mapping stub.

## Contents
- `.claude/skills/<skill>/SKILL.md`
- `.claude/skills/<skill>/reference.md`
- `.claude/skills/<skill>/examples.md`
- `GLOBAL_RULES.md`
- `scripts/generate_mcp_templates.py`

- `.claude/skills/uf-if-debug-mapper/` (maps UF/IF issues to concrete debug targets)
