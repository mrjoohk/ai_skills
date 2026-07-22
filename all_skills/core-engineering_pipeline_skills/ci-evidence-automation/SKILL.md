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

## When to Use (objective triggers)
- `eval-runner` has produced `evidence_pack/metrics.yaml` for the first time (wire it into CI now)
- A new UF/IF module landed and has no coverage gate in CI
- `evidence_pack/` schema is being extended (new run/metric fields)
- A regression threshold from `rd/evaluation_plan.md` needs enforcement on every push

## Inputs
- CI config (`.github/workflows/*`)
- test command(s)
- `evidence_pack/metrics.yaml` (from eval-runner) + `evidence_pack/runs.yaml`, `env.yaml` (from exp-runner)
- Regression thresholds from `rd/evaluation_plan.md`

**Gate G4 (entry check):** validate `evidence_pack/metrics.yaml` against the schema in
`references/reference.md` before wiring CI. Reject entries produced in
`Mode: UNPLANNED` runs unless the user explicitly promotes them. Report
`Gate G4: PASS | BLOCKED (schema/provenance issues)`.

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
