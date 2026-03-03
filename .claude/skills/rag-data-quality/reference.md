# Reference: RAG Quality Report

## Metadata Schema (minimum)
- doc_id, source, field (air/weapon/ground/sensor/comm)
- title, date, version, author/org (if known)
- security/handling tags (if applicable)
- chunk_id, chunk_index, token_count

## Chunking Rules
- chunk size target: N tokens
- overlap: M tokens
- do not split tables mid-row
- keep headings with their paragraphs

## Metrics
- Coverage per field/topic
- Duplication rate
- Recall@k for query set
- Rerank lift (Δ in top-1 accuracy)
- Grounded answer rate (answers with citations)

## Targeted Acquisition
- Identify low-coverage questions and propose document types to collect
- Avoid pure random sampling as the only strategy
