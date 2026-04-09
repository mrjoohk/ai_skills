# Examples: RAG Data Quality

## Test Prompt 1: Metadata Audit
```
"Scan data/corpus/ and validate which required metadata fields
 (doc_id, source, domain, title, date, chunk_id, token_count)
 are missing from each document. Organize missing fields by domain
 and output results to reports/rag_quality.md."
```

**Expected output:**
- List of missing fields (grouped by domain)
- Total document count and complete metadata ratio

---

## Test Prompt 2: Chunking Strategy Evaluation and Improvement
```
"Evaluate the current chunking configuration (size=512, overlap=32).
 Verify whether table and section title handling rules are correct
 and propose improved chunking rules in configs/chunking.yaml.
 Estimate impact on Recall@5."
```

**Expected output:**
- List of current chunking issues
- Improved `configs/chunking.yaml`
- Recall@5 impact estimation

---

## Test Prompt 3: Low-Coverage Gap Analysis and Targeted Acquisition Plan
```
"For 20 evaluation queries, identify low-coverage clusters.
 For each gap, propose specific document types to address it.
 Establish a gap-based acquisition plan instead of random collection."
```

**Expected output:**
- List of low-coverage query clusters
- Target document types per cluster
- Expected coverage improvement after acquisition

---

## Test Prompt 4: Run Recall@k Evaluation
```
"Calculate Recall@3, Recall@5, and Recall@10 for the evaluation
 query set (eval/queries.json). Measure top-1 accuracy difference
 before and after reranking (Rerank Lift). Store results in
 reports/recall_eval_<timestamp>.csv."
```

**Expected output:**
- `reports/recall_eval_<timestamp>.csv` (includes Recall@k and Rerank Lift)
- Summary of improvement recommendations
