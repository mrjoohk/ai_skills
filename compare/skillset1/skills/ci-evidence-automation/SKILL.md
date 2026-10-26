---
name: ci-evidence-automation
description: "Automates CI checks, coverage gates, evidence packs, and regression reporting."
user-invocable: true
allowed-tools: Read, Write, Bash
---

# CI Evidence Automation

Automates CI and evidence pack practices:
- coverage gates
- evidence pack generation (runs, metrics, environment, commit)
- regression detection and reporting
- artifact storage conventions
- mutation (negative-control) runs — `scripts/mutation_runner.py`

## When to Use (objective triggers)
- `eval-runner` has produced `evidence_pack/metrics.yaml` for the first time (wire it into CI now)
- A new UF/IF module landed and has no coverage gate in CI
- `evidence_pack/` schema is being extended (new run/metric fields)
- A regression threshold from `rd/evaluation_plan.md` needs enforcement on every push
- A change needs negative-control evidence (GLOBAL Rule 12) — mutants that the tests must catch

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

## Mutation / Evidence Runner (`scripts/mutation_runner.py`)

Each mutant = text edits applied to a fresh temporary copy of the code; the tests must then fail. The working tree is
never touched. Spec format, CLI and results file: `references/mutation_runner.md`. Commands below are one line
(Windows cmd and POSIX shells alike); `R` = `.claude/skills/ci-evidence-automation/scripts/mutation_runner.py`.

| When | Command |
|---|---|
| After any code change — do the patterns still apply? (seconds, no tests) | `python R SPEC --root . --check` |
| While iterating — mutants of changed functions only | `python R SPEC --root . --changed SNAPSHOT --jobs 2 --out RES.json` |
| One area | `python R SPEC --root . --only R0*,F05 --jobs 2` |
| Final evidence — every mutant once | `python R SPEC --root . --jobs <cores> --out logs/<P>_evidence/mutation.json` |
| Host with a per-call time limit | `python R SPEC --root . --out RES.json --budget 100 --timeout 60` — repeat while exit code = 3 |
| Final gate from the merged file | `python R SPEC --root . --out RES.json --summary --strict` |

1. **Iterate small, finish once.** `--check` after every edit, `--changed`/`--only` while iterating; the full set runs
   **once**, at the end, with `--jobs` = core count (2 cores ≈ 2×). Tests that drive a single-instance application
   (COM, Hangul) keep `--jobs 1`.
2. **Time limits everywhere.** `--timeout` per mutant (the whole process tree is killed; on POSIX a supervisor also
   ends a hung test, busy or blocked, whose runner was killed). Keep the timeout ≥ 1.5 × the slowest mutant (the runner warns).
   A code path that can hang gets a subprocess + timeout *inside its test*, so the test fails fast.
3. **Host per-call limits** (e.g., a remote shell with 180 s per call and no background processes): `--budget`
   ≈ limit − timeout − 20 s, plus `--out`; the same command resumes where it stopped (exit 3 = run it again). Run the
   calls **one after another** on one host — concurrent heavy calls contend and time out.
4. **Anchor patterns to a function** (`"func": "name"` or `"Class.method"`), so a pattern stays unique as the file grows.
   A `pattern` result is a broken mutant, not a pass — fix the spec before reading any other number.
5. **Gate.** survived / pattern / invalid / error always fail; `--strict` (final gate) also fails timeout, stale
   (code or mutant changed after the result), not-run and unverified (no baseline for this code). Exit codes:
   0 pass · 1 fail · 2 setup error · 3 incomplete. An `error` is not retried by `--resume`: fix it, rerun with `--only`.
6. **Negative control of the setup.** Before the mutants, every distinct test command (global and per-mutant) must pass
   on the unmutated copy and actually run tests — otherwise every mutant would look "killed". One runner per results
   file (one host at a time); keep `--out` and `--tmp` outside the `--copy` paths.
7. **No git?** `--snapshot DIR` after the full run; use DIR as the `--changed` baseline.

Precedent: drmHWP P-041 re-ran all 106 mutants sequentially 10+ times (5–9 min each) and lost ~15–20 min to host
limits; P-043 ran the same 106 with `--jobs 2` (about 2× faster, identical results) and on the 180 s host in
`--budget` calls without manual chunks.

## MCP Integration
- `mcp.shell`: run CI steps locally, generate coverage reports
- `mcp.filesystem`: write workflow yml and evidence templates
- `mcp.webhook`: send success/failure/regression notifications

## Token Saving
- Post concise CI summaries; attach full logs as artifacts.
- Use diff patches for workflow changes.

See `references/reference.md`, `references/examples.md` and `references/mutation_runner.md`.
