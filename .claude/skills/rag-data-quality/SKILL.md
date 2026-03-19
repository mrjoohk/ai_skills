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

## MCP Integration
- `mcp.filesystem`: scan corpus and metadata
- `mcp.shell`: run evaluation scripts, calculate Recall@k, generate reports
- `mcp.chroma` (optional): query index statistics

---

## Token Saving
- Summarize results as tables and store full report in `reports/rag_quality.md`.

See `reference.md` and `examples.md`.
