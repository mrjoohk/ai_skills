# Reference: CI + Evidence Pack

## CI Steps (typical)
1. Lint (ruff/clang-format/etc.)
2. Type check (mypy, optional)
3. Unit tests (pytest)
4. Coverage gate (fail under threshold)
5. Integration tests (scenario-based)
6. Benchmarks (optional)
7. Upload artifacts (coverage.xml, logs, reports, evidence_pack)

## Evidence Pack Layout
evidence_pack/
  runs.yaml
  metrics.yaml
  env.yaml
  scenarios.yaml
  artifacts/
    logs/
    plots/
    profiles/

## Regression Policy
- Define key metrics and thresholds
- Store baseline values
- Fail CI on regression beyond threshold
- Provide reproduction command

## Notification Payloads
- JSON payload templates for webhook posting
