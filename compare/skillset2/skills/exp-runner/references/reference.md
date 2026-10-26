# exp-runner — Reference

## 1. runs.yaml Full Schema

```yaml
# evidence_pack/runs.yaml — one list entry per run
- run_id: Exp-01            # unique, never reused; rerun → Exp-01b
  scenario_id: speech_sep    # task name from rd/evaluation_plan.md
  experiment: baseline       # baseline | proposed | ablation-<name>
  command: "python src/if/pipeline.py --cfg cfg/base.yaml --seed 42"
  seed: 42
  dataset: WSJ0-2mix
  split: test
  status: COMPLETED          # COMPLETED | FAILED | SKIPPED
  started: "2026-07-21T10:30:00+09:00"
  duration_s: 812.4
  outputs: results/Exp-01/   # predictions, checkpoints, traces, log.txt
  commit_sha: abc1234
  dirty: false               # true if working tree had uncommitted changes
  env_ref: evidence_pack/env.yaml
  error_tail: null           # last ~10 lines of stderr when FAILED
```

## 2. env.yaml Schema

```yaml
captured: "2026-07-21T10:29:00+09:00"
python: "3.11.6"
packages:            # relevant subset only, not full freeze
  torch: "2.3.1+cu121"
  numpy: "1.26.4"
cuda: "12.1"  driver: "550.54"
hardware:
  gpu: "RTX 4090 24GB x1"
  cpu: "Ryzen 9 7950X"  ram_gb: 64
os: "Ubuntu 22.04"
```

## 3. Run Matrix Patterns

| Pattern | Runs | When |
|---|---|---|
| Pairwise compare | {baseline, proposed} × seeds{42,43,44} | default model comparison |
| Ablation | proposed ± component × 1 seed (then 3 seeds for finalists) | component attribution |
| Sweep | proposed × param grid × 1 seed | threshold/param selection (mark `experiment: sweep-<param>` — excluded from headline metrics) |

## 4. Seed Policy

- Default 3 seeds; report mean ± std downstream (eval-runner handles aggregation).
- Simulation domains (deterministic solvers): 1 seed acceptable — record `seed: null` + note determinism source.
- Never compare runs with mismatched seed sets; exp-runner refuses and reports.

## 5. Failure Handling Decision Table

| Symptom | Action |
|---|---|
| OOM | record FAILED, suggest gpu-hpc-guard audit, halve batch → `Exp-##b` |
| NaN loss / divergence | record FAILED, suggest sim-physics-auditor (numerical stability) |
| Missing dataset path | stop the whole matrix — plan error, not a run error |
| Flaky (passes on rerun) | keep both entries; flag `WARN: nondeterminism` |
