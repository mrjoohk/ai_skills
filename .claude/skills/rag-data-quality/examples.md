# Examples: RAG Data Quality

## Test Prompt 1: Metadata Audit
"Scan `data/corpus/` and validate that each document has required metadata fields. Output missing fields by field category (air/weapon/...)."

## Test Prompt 2: Chunking Evaluation
"Evaluate current chunking config (size/overlap). Propose improved rules for tables and headings and estimate impact on recall@k."

## Test Prompt 3: Targeted Collection Plan
"Given 30 FAQs per field, identify low-coverage question clusters and propose targeted doc types to collect (avoid random sampling-only)."

## Expected Output
- `reports/rag_quality.md`
- `configs/chunking.yaml` suggestions
