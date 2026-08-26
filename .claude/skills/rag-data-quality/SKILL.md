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

## Pipeline Insertion & Input Source (canonical)
- **When (single rule):** after the corpus/index exists and **before `eval-planner` (Stage 8)**; re-run on ingest, chunking, or embedding-model changes. (This supersedes conflicting timings in older manuals.)
- **Input source:** corpus path and chunking configuration from project config files where present; the evaluation set (Q/A + citations) must come from the user or `rd/requirements.md` acceptance criteria — never synthesize it silently.

## Downstream Handoff — eval wiring
Append audit-derived metrics and thresholds to **`rd/domain_metrics.md`** (create if missing):

```
| Metric | Direction | Baseline | Target | Unit | Rationale | Auditor |
|---|---|---|---|---|---|---|
| recall_at_k | ↑ | <measured> | ≥ <target> | — | coverage gap REQ-## | rag-data-quality |
| dup_rate | ↓ | <measured> | ≤ <target> | % | index bloat guard | rag-data-quality |
```

`eval-planner` reads `rd/domain_metrics.md` as a first-class input (its Inputs #3) and cites the auditor per adopted metric. Detailed audit bodies stay in `reports/rag/` (GLOBAL_RULES Rule 16).

## MCP Integration
- `mcp.filesystem`: scan corpus and metadata
- `mcp.shell`: run evaluation scripts, calculate Recall@k, generate reports
- `mcp.chroma` (optional): query index statistics

---

## Token Saving
- Summarize results as tables and store full report in `reports/rag_quality.md`.

See `references/reference.md` and `references/examples.md`.
