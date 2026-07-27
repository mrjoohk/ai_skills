# Reference: CI + Evidence Pack

## CI Pipeline Stages (Recommended Order)

| Stage | Purpose | Tool Examples | Failure Condition |
|:---:|---|---|---|
| 1 | Lint | ruff, clang-format, eslint | Warning count > 0 (strict mode) |
| 2 | Type Check | mypy, pyright (optional) | Type errors exist |
| 3 | Unit Tests | pytest, jest, gtest | Test failure |
| 4 | Coverage Gate | coverage.py, lcov | Coverage < threshold |
| 5 | Integration Tests | Scenario-based | Scenario failure |
| 6 | Benchmark (optional) | pytest-benchmark, hyperfine | Regression > threshold |
| 7 | Artifact Upload | CI artifact storage | Upload failure |

---

## Evidence Pack Directory Structure
```
evidence_pack/
  runs.yaml         # Execution metadata: timestamp, commit, params
  metrics.yaml      # Numeric results + thresholds + pass/fail
  env.yaml          # Environment info: OS, language version, library version, GPU
  scenarios.yaml    # Scenario definitions and input parameters
  artifacts/
    logs/           # Execution logs (by stage)
    plots/          # Result graphs
    profiles/       # Performance profiling results
    coverage/       # Coverage reports (coverage.xml, etc.)
```

---

## runs.yaml Minimal Schema
```yaml
run_id:     <unique run ID>
timestamp:  <ISO 8601>
commit_sha: <git commit hash>
branch:     <branch name>
trigger:    <push | pull_request | schedule>
params:     <execution parameter key-value pairs>
status:     <PASS | FAIL | MANUAL_PENDING>
# MANUAL_PENDING: awaiting manual-metric confirmation. On resolution, record the
#                 result + timestamp + source, and create the results/<metric_id>.txt
#                 evidence file (see eval-runner "Manual Metric Lifecycle")
```

---

## metrics.yaml Minimal Schema
```yaml
- metric_id:  <metric name>
  value:      <measured value>
  threshold:  <threshold value>
  comparison: <lte | gte | eq>
  status:     <PASS | FAIL | WARN | MANUAL_PENDING>
  unit:       <unit>
```

---

## Regression Policy
- Define core metrics and thresholds, storing baseline values
- Fail CI when regressions exceed thresholds
- Include reproduction commands in regression reports
- Acceptable regression range: `(current - baseline) / baseline <= threshold%`
- **Evidence freshness (commit-based)**: if the latest run's `commit_sha` ≠ HEAD and
  source/test paths have a diff between them, that evidence is **STALE** — never cite
  it as a verdict basis until re-run (staleness is defined by code change, not elapsed time)
- **CI suite enumeration**: derive the suite list from the filesystem
  (glob, e.g. `tests/test_*.py` / `tests/test_*.cpp`). If a list must be hardcoded,
  add a mandatory cross-check guard against the actual file set — otherwise newly
  added tests are silently skipped by CI

---

## Webhook Notification Payloads
```json
// SUCCESS
{ "status": "SUCCESS", "task": "", "commit": "", "summary": "", "artifacts": [] }

// FAILURE
{ "status": "FAILURE", "task": "", "commit": "", "error_summary": "", "failing_commands": [], "logs_path": "" }

// COVERAGE_LOW
{ "status": "COVERAGE_LOW", "task": "", "current": 0, "required": 0, "missing_modules": [] }

// REGRESSION
{ "status": "REGRESSION", "metric": "", "before": 0, "after": 0, "threshold": 0, "reproduction_steps": "" }
```
