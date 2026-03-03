# Examples: UF Chain Validator

## Test Prompt 1: Chain Integrity
"Validate UF-01..UF-18 in `docs/uf/` and produce a report. Flag missing I/O contracts, missing tests, and missing evidence references."

## Test Prompt 2: Pre-merge Gate
"Run the UF validation on this branch and output a concise PASS/FAIL summary suitable for a PR comment. Provide minimal diffs for any doc fixes."

## Test Prompt 3: Coverage Failure Triage
"CI reports coverage 71% (<85%). Identify which UF modules lack tests and propose the smallest set of tests to reach 85%."

## Expected Artifacts
- `reports/uf_validation.md`
- Optional: patches for missing UF blocks
