---
name: rag-data-quality
description: "Assesses RAG corpus quality: chunking, metadata, deduplication, coverage, and recall/rerank evaluation for any domain."
user-invocable: true
allowed-tools: Read, Write
---

# RAG Data Quality

Ensures quality and evaluability of RAG corpus:
- Metadata completeness and schema consistency validation
- Chunking rules and overlap setting verification
- Duplicate and near-duplicate detection
- Coverage analysis against domain FAQs/queries
- Recall@k, reranking effectiveness, answer grounding validation

---

## When to Use
- Before/after ingesting new documents
- When recall or answer grounding quality degrades
- When expanding corpus to new domains or topics
- When changing chunking strategy or embedding model
- For corpus audit and periodic quality checks

---

## Inputs
- Corpus path or index statistics
- Chunking configuration (chunk size, overlap, split criteria)
- Evaluation set template (Q/A + citation sources)
- Domain hints (technical docs, legal, medical, product manuals, etc.)

---

## Output
- **Quality report:** coverage, duplication rate, missing metadata
- **Targeted acquisition plan:** gap-based strategy instead of random collection
- **Evaluation protocol:** metrics (Recall@k, MRR, Precision@k) and thresholds

---

## Pipeline Insertion & Input Source
- **When:** audit an available corpus/index before its metrics are adopted by `eval-planner` (Stage 8), or run a standalone corpus audit. Recheck affected metrics after ingest, chunking, or embedding-model changes.
- **Input source:** corpus path and chunking configuration from existing project configuration; use an approved evaluation set (Q/A + citations) or the project's canonical requirements. If no set exists, report that limitation or propose one explicitly rather than silently treating generated queries as ground truth.
- **Paths:** honor user-specified outputs and existing canonical locations. `rd/requirements.md`, `rd/domain_metrics.md`, and `reports/rag/` are optional defaults for a new project, not prerequisites.

## Downstream Handoff — eval wiring
Return audit-derived metrics and proposed thresholds to main in the following form. Mark unavailable baselines as unmeasured and cite the evaluation set and run evidence for measured results.

```
| Metric | Direction | Baseline | Target | Unit | Rationale | Auditor |
|---|---|---|---|---|---|---|
| recall_at_k | ↑ | <measured> | ≥ <target> | — | coverage gap REQ-## | rag-data-quality |
| dup_rate | ↓ | <measured> | ≤ <target> | % | index bloat guard | rag-data-quality |
```

Main verifies the results and is the single writer that merges accepted metrics into the project's canonical `domain_metrics.md` for `eval-planner`. Parallel workers return messages or write only to an assigned unique fragment, for example `reports/rag/<task-id>/domain_metrics.md`; they must not append to the shared canonical file. Reuse approved thresholds and mark new proposals as proposals. If this audit is used as a required gate, dependent work waits until its required criteria pass.

## Runtime Integration
- Use available file/index tools to inspect the corpus and metadata.
- Use available execution tools for authorized evaluation scripts and metric calculations.
- Persist reports only in the assigned project/task paths when requested or needed for resumption.

---

## Token Saving
- Return concise result tables; when a full report is needed, use the project's report location and assigned unique task path.

See `references/reference.md` and `references/examples.md`.
