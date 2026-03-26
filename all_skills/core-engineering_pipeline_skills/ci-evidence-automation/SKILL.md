---
name: ci-evidence-automation
description: "Automates CI checks, coverage gates, evidence packs, and regression reporting."
user-invocable: true
allowed-tools: Read, Write
---

# CI Evidence Automation

Automates CI and evidence pack practices:
- coverage gates
- evidence pack generation (runs, metrics, environment, commit)
- regression detection and reporting
- artifact storage conventions

## When to Use
- When introducing new UF modules
- When CI becomes noisy or lacks diagnostics
- When you need consistent evidence artifacts for experiments (Exp-01..)

## Inputs
- CI config (`.github/workflows/*`)
- test command(s)
- evidence schema (`evidence_pack/*`)

## Output
- recommended CI workflow steps (lint/test/coverage/artifacts)
- evidence pack schema + sample files
- regression thresholds and alert templates

## MCP Integration
- `mcp.shell`: run CI steps locally, generate coverage reports
- `mcp.filesystem`: write workflow yml and evidence templates
- `mcp.webhook`: send success/failure/regression notifications

## Token Saving
- Post concise CI summaries; attach full logs as artifacts.
- Use diff patches for workflow changes.

See `references/reference.md` and `references/examples.md`.
