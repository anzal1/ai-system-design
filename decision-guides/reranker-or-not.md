# Should You Add A Reranker?

Last reviewed: 2026-06-29

## Problem

Rerankers can improve RAG quality, but they add latency, cost, and another model-like component to operate.

The question is not whether rerankers are good. The question is whether your retrieval failures are ranking failures.

## Short Answer

Add a reranker when the right evidence appears in the candidate pool but is ranked too low to reach the final context.

Do not add a reranker when the right evidence is missing entirely.

## Decision Table

| Situation | Add reranker? |
| --- | --- |
| Required source appears in top 50 but not top 5 | Yes |
| Required source never appears | No |
| Many near-duplicate chunks compete | Maybe |
| Query needs exact ID match | Usually no |
| Latency budget is strict | Only if quality gain is large |
| No retrieval eval set exists | Not yet |

## What Rerankers Fix

Rerankers can fix:

- Poor ordering
- Semantic subtlety
- Similar documents
- First-stage score noise

Rerankers do not fix:

- Missing documents
- Bad chunking
- Broken permissions
- Stale indexes
- Unsupported answers

## Evaluation Strategy

Before adding a reranker:

1. Build a retrieval eval set.
2. Measure recall@50.
3. Measure recall@5.
4. Inspect failures.

If recall@50 is high but recall@5 is low, a reranker is likely useful.

After adding a reranker:

- Measure recall@5
- Measure final-context inclusion
- Measure answer faithfulness
- Measure p95 latency
- Measure cost per successful answer

## Failure Modes

- Reranker improves benchmark but not product quality
- Reranker sees sensitive chunks before permission filtering
- Reranker favors well-written but unsupported chunks
- Added latency breaks user experience
- Teams stop improving chunking and metadata

## Practical Rule

Reranking is a second-stage optimization. Do retrieval evals first. Fix ingestion, chunking, metadata, and permissions before adding another model.

## Further Reading

- [Hybrid RAG And Reranking](../patterns/hybrid-rag-reranking.md)
