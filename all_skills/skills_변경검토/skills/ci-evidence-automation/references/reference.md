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
# MANUAL_PENDING: 수동 지표 확인 대기. 해소 시 결과·일시·출처를 함께 기록하고
#                 results/<지표id>.txt 증적을 생성한다 (eval-runner '수동 지표 수명주기' 참조)
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
- **Evidence freshness (2026-07-27)**: evidence_pack 최신 run의 `commit_sha` ≠ HEAD이고 src/include/tests에 diff가 있으면 해당 evidence는 **STALE** — 재실행 전까지 판정 근거로 인용 금지
- **CI 스위트 열거 (2026-07-27)**: 스위트 목록은 파일시스템에서 파생한다(glob, 예: `tests/test_*.cpp`). 하드코딩할 경우 파일 집합과의 대조 가드를 필수로 둔다 — 신규 테스트의 조용한 누락 방지
- Include reproduction commands in regression reports
- Acceptable regression range: `(current - baseline) / baseline <= threshold%`

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
