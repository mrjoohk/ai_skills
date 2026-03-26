# Examples: Eval Runner

## Test Prompt 1: Evaluation Plan → Calculation Functions + Report
```
/eval-runner Read evaluation_plan.md and
write SI-SDR, PESQ, STOI calculation functions for the source separation task
in scripts/eval/separation_eval.py, then output a comparison report for
the following two experiments:
  Exp-01 (baseline): pred/baseline/, ref/clean/
  Exp-02 (proposed): pred/proposed/, ref/clean/
```

**Expected outputs:**
- `scripts/eval/separation_eval.py` (calculation functions)
- `reports/eval/separation_<timestamp>.md` (comparison report)
- `evidence_pack/metrics.yaml` (numeric records)

---

## Test Prompt 2: Direct Numeric Input → Comparison Table
```
/eval-runner Organize the following experiment results into a comparison table.
Target: SI-SDR >= 12.0, WER <= 15%.
  Exp-01 Baseline:  SI-SDR=9.2, PESQ=2.3, WER=18.2%
  Exp-02 Proposed:  SI-SDR=12.8, PESQ=2.9, WER=14.1%
  Exp-03 Ablation:  SI-SDR=11.4, PESQ=2.7, WER=15.3%
Include acceptance criteria judgments (PASS/FAIL).
```

**Expected outputs:**
- `reports/eval/comparison_<timestamp>.md` (3-way comparison table + PASS/FAIL judgments)

---

## Test Prompt 3: NLP Metric Calculation Script Generation
```
/eval-runner Generate BLEU, ROUGE-L, and BERTScore calculation scripts
for evaluating a translation model.
Input: pred/translations.txt, ref/references.txt
Save results in evidence_pack/metrics.yaml and
create a form that can run directly in CI.
```

**Expected outputs:**
- `scripts/eval/translation_eval.py`
- Execution command: `python scripts/eval/translation_eval.py --pred ... --ref ...`
- `evidence_pack/metrics.yaml` schema example
