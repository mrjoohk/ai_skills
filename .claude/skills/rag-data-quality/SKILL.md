    ---
    name: rag-data-quality
    description: "Assesses RAG corpus quality: chunking, metadata, dedup, coverage, recall/rerank eval."
    user-invocable: true
    allowed-tools: Read, Write
---

# RAG Data Quality

Ensures RAG corpus quality and evaluability:
- metadata completeness and schema consistency
- chunking rules + overlap
- deduplication and near-dup detection
- coverage analysis against FAQs
- recall@k + rerank effectiveness, grounded answer checks

## When to Use
- Before/after ingesting new documents
- When recall or answer grounding drops
- When expanding fields (air/weapon/ground/sensor/comm)

## Inputs
- corpus path(s) or index stats
- chunking config
- evaluation set template (Q/A + citations)

## Output
- quality report (coverage, duplication, missing metadata)
- suggested targeted acquisition plan (avoid random-only)
- evaluation protocol with metrics and thresholds

## MCP Integration
- `mcp.filesystem`: scan corpus and metadata
- `mcp.shell`: run eval scripts, compute recall@k, generate reports
- optional `mcp.chroma`: query index stats (if available)

## Token Saving
- Summarize with tables. Store full report as `reports/rag_quality.md`.

See `reference.md` and `examples.md`.
