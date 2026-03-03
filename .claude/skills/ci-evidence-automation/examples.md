# Examples: CI Evidence Automation

## Test Prompt 1: Coverage Gate
"Update `.github/workflows/ci.yml` to enforce coverage >= 85% and upload `coverage.xml` as an artifact. Provide a minimal diff."

## Test Prompt 2: Evidence Pack Generation
"Design `evidence_pack/` schema and add a CI step that writes `env.yaml` and `runs.yaml` on each run."

## Test Prompt 3: Regression Alerts
"Add a step that compares current benchmark metrics to baseline and triggers webhook alerts on regression > 5%."

## Expected Output
- workflow diffs
- evidence templates
- webhook message formats
