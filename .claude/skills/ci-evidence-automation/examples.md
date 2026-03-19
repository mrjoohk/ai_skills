# Examples: CI Evidence Automation

## Test Prompt 1: Configure Coverage Gate
```
"Update .github/workflows/ci.yml to apply a coverage >= 85% gate
 and upload coverage.xml as an artifact.
 Provide output in minimal diff format."
```

**Expected Output:**
- `.github/workflows/ci.yml` diff
- Coverage gate stage definition

---

## Test Prompt 2: Add Evidence Pack Generation CI Stage
```
"Add a stage that creates the evidence_pack/ schema on each CI run.
 Auto-generate runs.yaml and env.yaml and upload them as artifacts
 after execution."
```

**Expected Output:**
- CI workflow diff (evidence_pack generation stage)
- `runs.yaml`, `env.yaml` schema examples

---

## Test Prompt 3: Add Regression Alert Stage
```
"Add a CI stage that compares current benchmark metrics against baseline
 and triggers a webhook notification if regression exceeds 5%."
```

**Expected Output:**
- CI workflow diff (regression comparison + alert stage)
- Webhook payload example (REGRESSION)

---

## Test Prompt 4: Design Complete Evidence Pack
```
"Design the complete Evidence Pack structure for the project.
 Define schemas for runs.yaml, metrics.yaml, env.yaml, and scenarios.yaml,
 and design scripts for auto-generating each file in CI."
```

**Expected Output:**
- `evidence_pack/` directory structure + schema for each file
- Auto-generation script design (with path references)
