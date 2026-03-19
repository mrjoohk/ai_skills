---
name: eval-planner
description: "Designs domain-appropriate evaluation metrics, thresholds, and benchmark plans from REQ/UF/IF blocks or design documents. Use as the dedicated entry point for core-engineering Stage 8. Trigger when the user asks to define evaluation criteria, set acceptance thresholds, plan benchmarks, or translate requirements into measurable metrics — even if they don't explicitly mention 'Stage 8' or 'evaluation plan'. Also trigger when a design document exists and the user wants to know how to measure success."
user-invocable: true
allowed-tools: Read, Write
---

# Eval Planner

Analyzes REQ blocks, UF blocks, IF blocks, or design documents to design
**evaluation metrics, thresholds, and benchmark plans** appropriate for the domain.
Dedicated entry point for core-engineering **Stage 8** (Verification & Evidence Planning).

---

## When to Use
- At the start of Stage 8: `uf.md`, `requirements.md`, design documents are ready
- Evaluation metrics and acceptance criteria are unclear or missing
- Need to quickly derive domain-specific standard metrics and thresholds
- An evaluation plan document is needed before running `eval-runner`

---

## Inputs (in order of priority)
1. `uf.md` — UF blocks (Goal, I/O Contract, Acceptance Criteria)
2. `requirements.md` — REQ blocks
3. Design documents (WBS, design doc, etc.)
4. Domain hint (auto-inferred from documents if not provided)

---

## Execution Steps

### Step 1 — Domain Detection and Task Classification
Read the input documents and identify:
- **Domain:** ML/Deep Learning · Audio/Speech · NLP · Computer Vision · Other
- **Task Type:** Classification · Regression · Generation · Separation · Translation · Detection · etc.
- **Downstream Tasks:** If present, add a separate set of metrics

### Step 2 — Metric Selection
Select metrics that match the domain and task type.
Refer to `reference.md` for the metric list.

Selection criteria:
- **Primary metric** (1 only): Core metric that determines model selection
- **Secondary metrics** (2–4): Trade-off and quality auxiliary metrics
- **Diagnostic metrics** (optional): For debugging, included in report only

### Step 3 — Threshold Setting
Set concrete numerical thresholds for each metric:
```
- Baseline:   Based on papers / public benchmarks (cite source)
- Target:     Acceptance criteria for this research (Given/When/Then format)
- Stretch:    Excellent level when reached
```

If thresholds are unclear:
1. Present domain standard benchmark values as Baseline
2. Leave a NOTE asking the user to confirm Target

### Step 4 — Benchmark Dataset Specification
Specify the evaluation datasets for each task:
- Public standard datasets (e.g., WSJ0-2mix, LibriSpeech, GLUE, etc.)
- If internal data is available, add `[internal]` tag
- Specify split criteria (test set, held-out set)

### Step 5 — Generate evaluation_plan.md
Generate the file using the Output Template below.

---

## Output Template

```markdown
# Evaluation Plan

## Metadata
- Source: <input document path>
- Domain: <detected domain>
- Date: <creation date>

## Metrics by Task

### [Task Name] (e.g., Speech Separation)

| Category | Metric | Baseline | Target | Stretch | Unit |
|:---:|---|---:|---:|---:|---|
| Primary   | SI-SDR  | 8.9 dB | ≥ 12.0 dB | ≥ 14.0 dB | dB  |
| Secondary | PESQ    | 2.1    | ≥ 2.8     | ≥ 3.2     | MOS |
| Secondary | STOI    | 0.78   | ≥ 0.88    | ≥ 0.92    | —   |

**Acceptance Criteria (Given/When/Then):**
Given <test conditions>,
When <model inference runs>,
Then <Primary metric> >= <Target> (p < 0.05, N=<sample count>)

**Evaluation Dataset:** <dataset name> (<split>)
**Calculation Tool:** eval-runner

---

## REQ / UF Mapping

| REQ-ID / UF-ID | Linked Metric | Acceptance Criteria |
|---|---|---|
| REQ-001 | SI-SDR | >= 12.0 dB |

---

## Evidence Pack Connection
- `evidence_pack/metrics.yaml` — Metric results record
- `reports/eval/<task_name>_<timestamp>.md` — Detailed report
- Next step: `/eval-runner Generate calculation functions based on evaluation_plan.md`
```

---

## Notes
- Thresholds must **always be specified numerically**. "Higher is better" is not allowed.
- Always indicate metric direction (↑/↓) to clarify whether higher or lower is better.
- Select only 1 Primary metric — to keep the model selection criterion stable.
- Domain metric reference: `reference.md`
