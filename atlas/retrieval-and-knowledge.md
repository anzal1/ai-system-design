# Atlas: Retrieval And Knowledge

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers how a system gets the right knowledge in front of the model: indexing, retrieval, ranking, and the decision of whether to retrieve at all.

## Chunking

Documents must be split into units that fit retrieval and context budgets, and the split determines what can ever be retrieved. Chunks that are too small lose the context needed to answer; chunks that are too large dilute embeddings and waste tokens. The design is decided by document structure, the granularity of the questions users ask, and whether you attach parent or neighbor context at retrieval time rather than at index time.

Coverage: [Covered](../patterns/rag.md)

## Embeddings And Vector Search

Embedding choice fixes the ceiling of semantic retrieval quality: the model, its dimensionality, and its training domain decide which queries can ever match which documents. The design is decided by domain fit measured on your own retrieval eval set, cost per million tokens embedded, latency of query-time encoding, and the operational weight of the index you put behind it.

Coverage: [Covered](../decision-guides/vector-db-vs-search.md)

## Hybrid Search

Dense retrieval misses exact identifiers, rare terms, and codes; lexical retrieval misses paraphrase. Hybrid search runs both and fuses the results, usually with reciprocal rank fusion or a learned combiner. The design is decided by how much of your query traffic is keyword-shaped, whether your corpus contains identifiers that must match exactly, and the latency cost of running two retrievers.

Coverage: [Covered](../patterns/hybrid-rag-reranking.md)

## Reranking

First-stage retrieval optimizes recall over millions of documents and gets ordering wrong; a cross-encoder reranker rescores the top candidates with full query-document attention. The design is decided by whether your failure analysis shows relevant documents retrieved but ranked below the cutoff, and whether the added latency and per-query cost buy a measurable gain in answer faithfulness.

Coverage: [Covered](../decision-guides/reranker-or-not.md)

## GraphRAG

Some questions require connecting facts scattered across documents: ownership chains, dependency graphs, multi-hop relationships that no single chunk contains. GraphRAG builds an entity and relationship graph at index time and retrieves subgraphs or community summaries instead of flat chunks. The design is decided by whether your query log actually contains multi-hop questions, the cost of LLM-driven graph extraction over the corpus, and how you keep the graph consistent as documents change.

Coverage: (planned)

## Freshness And Incremental Indexing

A retrieval index is a cache of the world, and it goes stale. Full reindexing is expensive and slow; incremental indexing must handle updates, deletions, and embedding model migrations without serving a mix of old and new vectors that silently degrades retrieval. The design is decided by how fast the source data changes, the staleness tolerance of the product, and whether you can detect and reindex only changed documents.

Coverage: (planned)

## Structured-Data RAG

When the knowledge lives in tables, retrieval means generating queries, not fetching chunks: text-to-SQL, semantic layers over warehouses, and schema-aware retrieval. The failure modes are different too, because a plausible-looking wrong query returns confident wrong numbers. The design is decided by schema complexity, whether you constrain generation to a curated semantic layer, and how you validate results before showing them.

Coverage: [Covered](../case-studies/ai-data-analyst.md)

## Long Context Vs RAG

Growing context windows make it tempting to skip retrieval and stuff everything in. That trades retrieval engineering for token cost, latency, and degraded attention over long inputs, and it removes the citation boundary that retrieval gives you. The design is decided by corpus size relative to the window, query volume against per-query token cost, freshness requirements, and whether you need to show users where an answer came from.

Coverage: [Covered](../decision-guides/long-context-vs-rag.md)
