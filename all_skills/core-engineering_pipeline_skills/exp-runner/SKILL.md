---
name: exp-runner
description: >
  Executes experiments defined in rd/evaluation_plan.md and produces the raw result
  data + provenance records that eval-runner consumes. Fills the pipeline gap between
  eval-planner (plan) and eval-runner (metric computation): fixes seeds and environment,
  runs training/inference/simulation commands per scenario, and writes
  evidence_pack/runs.yaml, evidence_pack/env.yaml, and results/<exp_id>/ outputs.
  Trigger when the user says "실험 돌려줘", "실험 실행", "run experiments",
  "execute the evaluation plan", "베이스라인 돌려줘", "학습 실행하고 기록해줘",
  or when evaluation_plan.md exists but no experiment results/runs.yaml exist yet.
  Also trigger before eval-runner when the user asks to compare models but no
  result data has been produced.
user-invocable: true
allowed-tools: Read, Write, Bash
---

# Exp-Runner — Experiment Execution & Provenance

Fills the Stage 8 execution gap: `eval-planner` designs the plan, **exp-runner runs it**,
`eval-runner` computes metrics from what exp-runner recorded.

```
eval-planner            exp-runner                       eval-runner
rd/evaluation_plan.md → [실행: 시드·환경 고정, 시나리오별 실행] → evidence_pack/runs.yaml
                        results/<exp_id>/                        + results/ → metrics
```

Without this skill, "Experiment result data" (eval-runner's input) has no producer and
reproducibility rules (same dataset/split/seed) have no enforcer.

---

## Inputs

- `rd/evaluation_plan.md` — **required** (Gate: if missing, stop and run `eval-planner` first; ad-hoc runs without a plan belong to eval-runner's UNPLANNED mode, not here)
- Runnable entry points: `src/if/*.py` (if-integrator output) or user-specified train/infer scripts
- Dataset paths + split definitions (from the plan's Benchmark Dataset section; ask only if absent)
- Hardware/session constraints (optional; merge from `rd/domain_metrics.md` if present)

**Entry gate (G3 pass-through):** if `reports/impl/if_integration_report_*.md` shows
`INTERFACE_ERROR` or `PARTIAL`, stop — running experiments on a broken integration
wastes compute and produces misleading evidence. Route to `uf-if-debug-mapper`.

---

## Execution Steps

### Step 1 — Derive Run Matrix from the Plan
- Parse `rd/evaluation_plan.md`: tasks, datasets/splits, experiments to compare (Baseline / Proposed / ablations)
- Assign run IDs: `Exp-01`, `Exp-02`, … (one row per experiment × dataset × seed)
- Fix seeds explicitly (default: 3 seeds unless the plan states otherwise); identical dataset/split/seed across compared experiments is **mandatory**

### Step 2 — Freeze Environment
Record before any run into `evidence_pack/env.yaml`:
- python/library versions (`pip freeze` relevant subset), CUDA/driver if GPU
- hardware (GPU model, VRAM, CPU, RAM), OS
- `commit_sha` of the code under test (fail with a warning if the working tree is dirty — note `dirty: true`)

### Step 3 — Execute Runs
For each run in the matrix:
- Launch via `mcp.shell`/Bash with the fixed seed and config; capture stdout/stderr to `results/<exp_id>/log.txt`
- Save raw outputs (predictions, checkpoints, sim traces) under `results/<exp_id>/`
- On failure: record `status: FAILED` with the error tail — never silently drop a run
- Long runs: report progress and estimated remaining runs to the user between runs

### Step 4 — Write Provenance (`evidence_pack/runs.yaml`)

```yaml
- run_id: Exp-01
  scenario_id: <task from evaluation_plan>
  command: "<exact command line>"
  seed: 42
  dataset: <name>  split: <split>
  status: COMPLETED | FAILED
  started: <ISO8601>  duration_s: <float>
  outputs: results/Exp-01/
  commit_sha: <sha>
  env_ref: evidence_pack/env.yaml
```

### Step 5 — Handoff

```
✅ exp-runner complete.
  - evidence_pack/runs.yaml   (N runs, M failed)
  - evidence_pack/env.yaml
  - results/<exp_id>/         (raw outputs per run)

Next step → /eval-runner with rd/evaluation_plan.md + evidence_pack/runs.yaml
(FAILED runs are excluded from metric aggregation — rerun or investigate first.)
```

---

## Rules

1. No run without a plan — unplanned exploration is allowed but belongs outside evidence (`eval-runner` UNPLANNED mode).
2. Seeds, dataset, split, and command line are recorded **verbatim** for every run; a run missing any of these is invalid and must be re-executed.
3. Compared experiments must share dataset/split/seed sets — if the plan violates this, stop and flag to the user.
4. Never overwrite a previous `run_id`; append new runs (`Exp-01b` for reruns) so regressions stay traceable.
5. Failures are evidence too: keep FAILED entries in runs.yaml.

---

## Bundled Resources

| Resource | When to use |
|---|---|
| `references/reference.md` | runs.yaml/env.yaml full schema, run matrix patterns, seed policy |
| `references/README_kr.md` | 한국어 사용 가이드 |
