# Enterprise RAG Review Guide

## Strong Answer Checklist

- Uses RAG for document knowledge instead of fine-tuning
- Uses hybrid search or justifies a simpler retrieval method
- Preserves source IDs, chunk IDs, document versions, and permissions
- Enforces permissions before context assembly
- Evaluates retrieval separately from generation
- Tests citation support and refusal behavior
- Covers stale documents, deletion, and connector failures
- Treats retrieved content as untrusted
- Logs enough trace data to debug failures
- Defines latency and cost budget

## Common Weaknesses

- Says "use a vector database" without explaining chunking or metadata
- Lets the model enforce permissions
- Evaluates only final answer quality
- Omits citation validation
- Ignores document deletion and freshness
- Stores raw sensitive traces without access control

## Good Tradeoff Discussion

A strong submission should compare:

- Vector-only vs hybrid retrieval
- Pre-filter vs post-filter permissions
- Reranking vs latency
- Larger chunks vs smaller chunks
- Long context vs retrieval
- Strict refusal vs helpfulness
