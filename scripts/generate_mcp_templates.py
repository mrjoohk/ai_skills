#!/usr/bin/env python3
"""generate_mcp_templates.py

Generates project-local MCP mapping templates and orchestration stubs for this skills pack.

Usage:
  python scripts/generate_mcp_templates.py --project-root .

Outputs:
  - configs/mcp/mcp_map.yaml
  - configs/mcp/webhook_payloads.json
  - docs/agent_handoffs.md
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from datetime import datetime

DEFAULT_MCP_MAP = {
  "servers": [
    {"name": "shell", "purpose": "Run build/test/bench commands"},
    {"name": "filesystem", "purpose": "Read/write project files and reports"},
    {"name": "github", "purpose": "Issues/PRs/status comments"},
    {"name": "webhook", "purpose": "Send status notifications (optional)"},
    {"name": "chroma", "purpose": "Vector store queries (optional)"},
  ],
  "skill_to_server_hooks": {
    "core-engineering": ["filesystem"],
    "uf-chain-validator": ["filesystem", "shell", "github"],
    "gpu-hpc-guard": ["shell", "filesystem"],
    "agent-orchestration": ["github", "shell", "filesystem", "webhook"],
    "sim-physics-auditor": ["shell", "filesystem"],
    "rag-data-quality": ["filesystem", "shell", "chroma"],
    "ci-evidence-automation": ["shell", "filesystem", "github", "webhook"],
    "uf-if-debug-mapper": ["filesystem", "shell", "github"],
  },
  "commands": {
    "run_tests": "pytest -q",
    "run_coverage": "pytest --cov --cov-report=xml",
    "lint": "ruff check .",
    "typecheck": "mypy .",
    "bench": "python -m benchmarks.run",
  }
}

DEFAULT_WEBHOOK_PAYLOADS = {
  "SUCCESS": {
    "event": "success",
    "task": "<TASK_NAME>",
    "commit": "<COMMIT_SHA>",
    "summary": "<ONE_LINE_SUMMARY>",
    "artifacts": ["<PATH1>", "<PATH2>"]
  },
  "FAILURE": {
    "event": "failure",
    "task": "<TASK_NAME>",
    "commit": "<COMMIT_SHA>",
    "error_summary": "<SHORT_ERROR>",
    "failing_commands": ["<CMD>"],
    "logs_path": "<PATH>"
  },
  "COVERAGE_LOW": {
    "event": "coverage_low",
    "task": "<TASK_NAME>",
    "current": "<PCT>",
    "required": "<PCT>",
    "missing_modules": ["<MODULE>"]
  },
  "REGRESSION": {
    "event": "regression",
    "metric": "<METRIC>",
    "before": "<VALUE>",
    "after": "<VALUE>",
    "threshold": "<THRESHOLD>",
    "repro": "<COMMAND>"
  }
}

HANDOFF_DOC = """# Agent Handoffs (Template)

Use this template to connect Agent-1/2/3 work with MCP steps.

## Handoff Block
From Agent:
To Agent:
Objective:
Context Links:
Deliverables:
Constraints:
Acceptance Tests:
Evidence Outputs:

## Example: Agent-1 -> Agent-2
From Agent: Agent-1 (Architect)
To Agent: Agent-2 (Builder)
Objective: Implement UF-19 (Range gating) with minimal diffs
Context Links:
- docs/uf/UF-19.md
- src/sar/gating.py
Deliverables:
- src/sar/gating.py (new)
- tests/test_gating.py (new)
Constraints:
- peak VRAM <= 18GB
- runtime <= 60s for reference scenario
Acceptance Tests:
- pytest -q
- unit tests include edge cases
Evidence Outputs:
- reports/bench/gating.md
- evidence_pack/metrics.yaml

"""

def write_file(path: Path, content: str, executable: bool=False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | 0o111)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".", help="Path to project root")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    ts = datetime.utcnow().isoformat() + "Z"

    mcp_map_path = root / "configs" / "mcp" / "mcp_map.yaml"
    payloads_path = root / "configs" / "mcp" / "webhook_payloads.json"
    handoffs_path = root / "docs" / "agent_handoffs.md"

    # Simple YAML emitter (keeps dependencies minimal)
    lines = []
    lines.append(f"# Auto-generated at {ts}")
    lines.append("servers:")
    for s in DEFAULT_MCP_MAP["servers"]:
        lines.append(f"  - name: {s['name']}")
        lines.append(f"    purpose: {json.dumps(s['purpose'])}")
    lines.append("skill_to_server_hooks:")
    for k, v in DEFAULT_MCP_MAP["skill_to_server_hooks"].items():
        lines.append(f"  {k}: {v}")
    lines.append("commands:")
    for k, v in DEFAULT_MCP_MAP["commands"].items():
        lines.append(f"  {k}: {json.dumps(v)}")
    yaml_text = "\n".join(lines) + "\n"

    write_file(mcp_map_path, yaml_text)
    write_file(payloads_path, json.dumps(DEFAULT_WEBHOOK_PAYLOADS, indent=2) + "\n")
    write_file(handoffs_path, HANDOFF_DOC)

    print(f"Wrote: {mcp_map_path}")
    print(f"Wrote: {payloads_path}")
    print(f"Wrote: {handoffs_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
