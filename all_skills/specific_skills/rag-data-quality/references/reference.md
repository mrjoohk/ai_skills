# Reference: RAG Quality Report

## Metadata Schema (Minimum Required)
```yaml
# Document Level
doc_id:      <Unique identifier>
source:      <Original file path or URL>
domain:      <Domain hint — e.g., technical doc, legal, medical, product manual>
title:       <Document title>
date:        <Creation/modification date (ISO 8601)>
version:     <Version (if applicable)>
author_org:  <Author or organization (if known)>

# Chunk Level
chunk_id:    <Unique chunk identifier within document>
chunk_index: <Sequence number within document>
token_count: <Token count of chunk>
```

---

## Chunking Rules Guide

| Rule | Description |
|---|---|
| **Chunk size** | Target token count N (e.g., 256~512 tokens) |
| **Overlap** | Overlapping tokens between consecutive chunks M (e.g., 32~64 tokens) |
| **Table preservation** | Do not split in the middle of tables |
| **Title linking** | Keep section titles with their body content |
| **Code blocks** | Do not split code blocks |
| **Split criteria** | Paragraph boundary first, sentence boundary second |

---

## Quality Metrics

| Metric | Definition | Target Threshold |
|---|---|---|
| **Coverage** | Proportion of evaluation queries answerable from corpus | >= X% |
| **Duplication Rate** | Proportion of near-duplicate chunks | <= Y% |
| **Missing Metadata** | Proportion of chunks missing required metadata | 0% |
| **Recall@k** | Proportion of queries with correct chunk in top-k | >= Z% |
| **Rerank Lift** | Difference in top-1 accuracy before/after reranking | >= Δ% |
| **Grounded Answer Rate** | Proportion of answers with citations | >= W% |

---

## Targeted Acquisition Plan
- Do not use random acquisition as the only strategy
- Identify low-coverage clusters from evaluation query set
- Specifically propose document types to address gaps

---

## Result Storage Paths
- `reports/rag_quality.md` — full quality report
- `configs/chunking.yaml` — chunking configuration
- `reports/recall_eval_<timestamp>.csv` — Recall@k evaluation results
