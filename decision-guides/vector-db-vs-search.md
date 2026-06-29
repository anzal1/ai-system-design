# Vector DB vs Search Engine vs Hybrid Search

Last reviewed: 2026-06-29

## Problem

RAG systems need retrieval, but retrieval does not always mean a vector database. Some systems need keyword search. Some need vector search. Many production systems need both.

## Short Answer

Use keyword search for exact matching.

Use vector search for semantic similarity.

Use hybrid search when users need both exact terms and semantic intent.

## Decision Table

| Requirement | Keyword search | Vector search | Hybrid |
| --- | --- | --- | --- |
| Exact IDs and names | Strong | Weak | Strong |
| Semantic paraphrases | Weak | Strong | Strong |
| Debuggability | Strong | Medium | Medium |
| Mature filtering | Strong | Depends | Strong |
| Enterprise docs | Good | Good | Usually best |
| Small corpus | Good | Often unnecessary | Maybe overkill |
| Multilingual semantic match | Weak | Strong | Strong |

## Use Keyword Search When

- Queries include exact terms
- Documents contain product names, IDs, or error codes
- Ranking needs to be explainable
- The corpus is small or structured
- Existing search infrastructure is strong

## Use Vector Search When

- Users ask semantic questions
- Documents use different wording than users
- You need similarity over text, images, audio, or code
- The system should retrieve concepts, not exact terms

## Use Hybrid Search When

- You have enterprise documents
- Exact terms and semantic meaning both matter
- You need strong baseline retrieval before reranking
- Search failures are expensive

## Failure Modes

Keyword search:

- Misses paraphrases
- Requires users to know exact vocabulary
- Struggles with conceptual queries

Vector search:

- Misses rare exact strings
- Can retrieve semantically similar but factually wrong chunks
- Harder to debug scores
- Embeddings can become stale

Hybrid search:

- More moving parts
- Ranking can become hard to explain
- Fusion weights need evals
- Latency can increase

## Evaluation Strategy

Create a retrieval eval set with expected source IDs.

Run:

- Keyword only
- Vector only
- Hybrid
- Hybrid plus reranking

Measure recall, ranking, final-context inclusion, and answer faithfulness.

## Practical Rule

For enterprise RAG, start with hybrid search unless you have strong evidence that one method is enough.

## Further Reading

- [Hybrid RAG And Reranking](../patterns/hybrid-rag-reranking.md)
- [RAG System Design](../patterns/rag.md)
