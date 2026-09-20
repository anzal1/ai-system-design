# RAG Pipeline From Scratch

## Problem

RAG demos usually hide the system inside a framework and a hosted model, so when quality is bad nobody can say which stage failed. Was the chunk boundary wrong, did lexical search miss a word form, did fusion bury the right candidate, did the budget squeeze out the evidence, or did the model ignore its context? This module builds the whole pipeline from parts you can read, with a deliberately dumb deterministic model at the end, so every failure is attributable to a specific stage.

## What You Build

One file, `rag_pipeline.py`, that imports the three sibling modules (`chunker`, `bm25`, `vector-index`) and composes them:

1. **Ingestion**: recursive structure-aware chunking of three markdown docs, with an ingestion filter that drops heading-only chunks.
2. **Hybrid retrieval**: every chunk indexed twice, in a BM25 inverted index and as a hashed n-gram vector. Queries produce two ranked lists.
3. **Reciprocal rank fusion**: `score(d) = sum of 1/(60 + rank)` across lists. Rank-based, so BM25 scores and cosine similarities never need to share a scale.
4. **Context assembly**: greedy packing of fused candidates under a token budget (estimated at 4 characters per token).
5. **Stub model**: a deterministic extractive answerer. It selects the context sentences with the most query-term overlap (after light suffix stripping), emits them with `[n]` citation markers mapped to chunk IDs, and refuses when nothing overlaps enough.

The demo runs three queries: an exact error code where BM25 wins, a morphological-variant query (`rotating certificates` versus the doc's `Certificate rotation`) where BM25 scores zero and the vector side carries retrieval, and an unanswerable query that must produce a refusal.

## How It Works

The pipeline is a data flow with two parallel branches that reunite. At ingestion, each document is chunked once and each chunk gets a stable ID (`doc#i`); that ID travels through both indexes, through fusion, into the context, and out through the citations, which is what makes answers auditable end to end.

At query time both retrievers rank all chunks. RRF converts each ranked list into reciprocal-rank scores and sums them. The constant 60 damps the difference between rank 1 and rank 2 so that one retriever's strong opinion does not automatically override the other's; a document ranked 3rd and 4th by the two retrievers beats a document ranked 1st by one and absent from the other only when the lists are long. Fusion needs no score normalization, which is the practical reason production systems reach for RRF before anything cleverer.

The context assembler walks the fused list in order and keeps any chunk that still fits the remaining budget. The stub model then does the only thing a model should be allowed to do in this architecture: select and quote from the supplied context. Because it is extractive and deterministic, it cannot hallucinate. Its refusal path (no sentence overlaps the query enough) is a feature under test, not an error.

## Design Decisions

- **A stub model instead of a real one.** The point is the system, not the model. Every component that determines whether the right evidence reaches the context is fully exercised offline, deterministically, in one process. Swapping in a real model changes one function and leaves every assert about retrieval, budgeting, and citation integrity intact.
- **RRF over weighted score fusion.** Weighted fusion requires normalizing BM25 scores (unbounded) against cosine similarities (bounded) and tuning the weight per corpus. RRF uses only ranks, has one insensitive constant, and is what the pattern page in this repo recommends as a starting point.
- **Heading-only chunks filtered at ingestion.** The chunker legitimately emits a bare title when a document opens with a heading and no body. Left in the index, these tiny chunks score deceptively high under BM25 length normalization on any shared title word, and during development one of them outranked the true answer chunk after fusion. Filtering at ingestion fixed a fusion-level symptom at its actual source, which is the recurring shape of RAG debugging.
- **Greedy skip-and-continue budgeting.** When the next candidate does not fit, it is skipped and smaller later candidates may still enter. The alternative (stop at first overflow) wastes remaining budget; the cost is that ordering in the context no longer strictly matches fused rank.
- **Suffix stripping lives in the stub, not the retriever.** BM25 is left unstemmed on purpose so the demo can show what exact-token matching misses. A real model needs no stemming to read context; only the stub's surface matcher does.

## Failure Modes

- **Both retrievers miss**: no fusion can recover a chunk that neither branch ranked. The morphological query shows the near-miss version, where BM25 contributes nothing and the whole outcome rides on one branch.
- **Fusion buries the answer**: RRF rewards agreement, so a chunk both retrievers rank mid-list can outrank the true answer that only one retriever found. Larger candidate pools (the k passed to each retriever) reduce this at the cost of noisier context.
- **Budget starvation**: a large but essential chunk is skipped because two mediocre smaller chunks already spent the budget. Visible here because the demo prints tokens used per query.
- **Citation drift**: any renumbering between assembly and answering breaks the citation-to-chunk mapping silently. The asserts check every cited number resolves to a context chunk and that the cited chunk actually contains the claimed evidence.
- **Missing refusal**: the most dangerous failure in production RAG is a confident answer with no supporting evidence. The stub makes the refusal path explicit and testable; a real model needs prompting plus evaluation to approximate the same guarantee.

## What Production Systems Do Differently

- A real embedding model and a real generator, with the retrieval stack otherwise shaped like this one.
- A reranker between fusion and context assembly, spending extra compute on the top 20 to 100 candidates (see `patterns/hybrid-rag-reranking.md`).
- Permission and metadata filtering before any model-visible step.
- Real tokenizer-based budgeting, source deduplication, and diversity constraints in context assembly.
- Faithfulness and citation-support evaluation on labeled sets, plus tracing of every score and filtering decision per query.
- Query rewriting, multi-query expansion, and caching in front of retrieval.

## Run It

```bash
cd build-from-scratch/rag-pipeline
python3 rag_pipeline.py
```

Runs in about a second. Prints per-query retriever rankings, fused top candidates, context size against budget, and the cited answer. Asserts validate that BM25 ranks the exact-identifier chunk first, that the vector branch beats BM25 on the morphological query, that fusion puts the gold chunk on top in both cases, that the token budget holds for every query, that every citation resolves to a real context chunk containing the evidence, and that the out-of-corpus query is refused.

## Exercises

1. Remove the `_has_body` ingestion filter and rerun. Find which query breaks, then explain the failure chain from chunk size through BM25 length normalization to RRF.
2. Sweep `RRF_K` over {1, 10, 60, 1000} and record the fused top-3 for each query. Explain what very small and very large constants each converge to.
3. Replace greedy skip-and-continue budgeting with strict in-order packing (stop at first chunk that does not fit). Construct a query where the strict version produces a worse answer.
4. Add a second answerable query whose evidence spans two chunks and extend the stub to require citations from two distinct sources. What does this force the context assembler to guarantee?
5. Swap the stub for a real model call behind the same `stub_model(query, context)` signature, keeping every retrieval and citation assert. Then add one new eval the stub could never fail but a real model can: answer text contradicting its cited chunk.

## Further Reading

- [Cormack, Clarke, Buettcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (2009)](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) - the three-page paper behind the fusion step, including the k=60 constant.
- [Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (2020)](https://arxiv.org/abs/2005.11401) - the paper that named the pattern; useful for seeing how much of modern RAG is systems engineering added since.
- [patterns/hybrid-rag-reranking.md](../../patterns/hybrid-rag-reranking.md) - this repo's production pattern page; this module is its minimal runnable skeleton, minus the reranker.
- [Es et al., "RAGAS: Automated Evaluation of Retrieval Augmented Generation" (2023)](https://arxiv.org/abs/2309.15217) - faithfulness and citation-support metrics for when the stub is replaced with a model that can actually hallucinate.
