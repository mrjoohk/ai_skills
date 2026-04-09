# Examples: Eval Planner

## Test Prompt 1: Design Document → Evaluation Plan
```
/eval-planner Read W400000_Downstream_Validation_Design.md and
define evaluation metrics, thresholds (Baseline·Target·Stretch), and benchmark datasets
for each downstream task (source separation / ASR / speaker diarization / localization).
Write evaluation_plan.md
```

**Expected outputs:**
- `evaluation_plan.md` (metric tables per task + acceptance criteria + REQ mapping)

---

## Test Prompt 2: REQ Blocks → Evaluation Plan
```
/eval-planner Analyze REQ-001 to REQ-010 in requirements.md and
design evaluation metrics and acceptance criteria for each requirement.
Specify 1 Primary metric and 2–3 Secondary metrics.
Set thresholds using SOTA from Papers with Code as Baseline.
```

**Expected outputs:**
- `evaluation_plan.md` (with per-REQ metric mapping)

---

## Test Prompt 3: UF Blocks → Unit Evaluation Plan
```
/eval-planner From uf.md (UF-01 to UF-15), identify directly measurable UFs and
define metrics and thresholds to link to each UF's Verification Plan.
The model is in NLP domain and the task is translation.
```

**Expected outputs:**
- `evaluation_plan.md` (per-UF metrics + calculation methods)
- Next step guidance: `Use /eval-runner to generate calculation functions`
