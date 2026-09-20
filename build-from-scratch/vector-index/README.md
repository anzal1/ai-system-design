# Vector Index From Scratch

## Problem

Vector search has two halves that are usually learned as black boxes: the embedding (how text becomes a vector) and the index (how a nearest-neighbor query avoids touching every vector). Brute-force cosine search is exact but scales linearly with corpus size. Every production vector database replaces it with an approximate nearest neighbor (ANN) index, and every ANN index makes the same trade: it gives up guaranteed correctness to answer in sublinear time. Engineers who have never seen that trade measured tend to treat recall as either free or unknowable. It is neither.

## What You Build

One file, `vector_index.py`, in two parts:

**Part A: an embedding with no ML.** Character trigrams hashed into a 256-dimensional vector with signed feature hashing, then L2 normalized. It captures surface similarity only, but it produces genuine cosine-similarity behavior: related texts score around 0.4, unrelated texts near 0.1, which is enough to drive and honestly evaluate the search machinery.

**Part B: two indexes and a benchmark.**

- Brute-force cosine search: score everything, sort, return top-k. The exactness baseline.
- HNSW-lite: a simplified but faithful Hierarchical Navigable Small World graph. Exponentially distributed layer assignment, greedy descent through upper layers, best-first beam search with an `ef` parameter at layer 0, bidirectional links capped at M per node, and the paper's neighbor-selection heuristic.

The benchmark indexes 3000 clustered synthetic vectors and reports, for several `ef` values, recall@10 against brute-force ground truth and distance comparisons per query. Typical output: recall 0.90 at 5 percent of brute-force comparisons, recall 0.996 at 8 percent.

## How It Works

**Feature hashing.** Each character trigram is hashed with crc32; one part of the hash picks a bucket, one bit picks a sign. Collisions are inevitable at 256 dimensions, but signed hashing makes colliding features cancel on average instead of always adding, so the dot product remains an unbiased estimate of n-gram overlap. This is the same trick production systems use for high-cardinality categorical features.

**HNSW.** The index is a stack of graphs. Every vector lives in layer 0; each higher layer keeps an exponentially thinning random sample. A query starts at the single entry point in the top layer and greedily walks to the nearest node, layer by layer. The upper layers act like an express lane: they cross the space in a few hops and drop the search into the right neighborhood of layer 0. There, a best-first beam search expands the closest unexpanded candidate, maintaining the `ef` best results, and stops when no candidate can improve the worst of them. `ef` is the recall dial: a wider beam escapes more local minima and finds more true neighbors, at the cost of more distance computations.

**The neighbor-selection heuristic is the part people skip, and it is load-bearing.** The naive policy links each new node to its M closest candidates. On clustered data (all real embedding data is clustered), the closest candidates are all in the same cluster, the graph fragments into islands, and greedy search cannot cross between them. The first version of this module did exactly that and scored recall@10 of 0.26, barely improving with beam width. The paper's heuristic keeps a candidate only if it is closer to the new node than to any already-selected neighbor, which forces links to spread across directions and clusters. Same code otherwise, recall 0.996.

## Design Decisions

- **Squared Euclidean distance inside the graph, cosine outside.** On unit vectors the two produce identical rankings (|a-b|^2 = 2 - 2cos), and squared Euclidean skips a sqrt per comparison. Normalizing at ingestion and forgetting about cosine is standard production practice.
- **Comparisons counted, not just wall-clock time.** Pure-Python distance loops are hundreds of times slower than SIMD, so timing this code says little about production latency. Distance comparisons per query is implementation-independent and transfers: 8 percent of brute-force comparisons is 8 percent whether the loop is Python or AVX-512.
- **Clustered synthetic data instead of uniform random.** Uniform vectors on a sphere are the easiest possible case for ANN and never occur in practice. Clustered data is what embeddings look like and is what makes the neighbor-selection heuristic matter.
- **Queries drawn from the same distribution as the corpus.** Real queries resemble the documents they search. Adversarially off-distribution queries are a real concern but a different experiment.
- **No deletions.** HNSW deletions are genuinely hard (removing a node can disconnect the graph) and every production system handles them with tombstones and periodic rebuilds. Modeling that adds code without adding insight here.

## Failure Modes

- **Recall failures are silent.** A fragmented or under-connected graph returns plausible neighbors that are simply not the nearest ones. Nothing errors. Without a brute-force ground-truth comparison you will not know. This module's initial 0.26-recall bug looked completely healthy in its output.
- **Off-distribution queries** land far from every cluster the graph was built around, and greedy descent commits to the wrong basin. Recall measured on in-distribution queries overstates production recall if query traffic drifts.
- **Low ef gets stuck in local minima**; the demo shows recall 0.90 at ef=10 versus 1.0 at ef=64 on the same graph.
- **Insertion order matters.** The graph is built incrementally, so early points shape the express lanes. Inserting one cluster at a time produces worse graphs than shuffled insertion.
- **Hashed embeddings have zero semantics.** "Reboot" and "restart" share no trigrams and score near zero. Part A is a stand-in for a learned model, not a substitute; its collisions also add noise floor to every similarity.

The tradeoff every ANN index makes: exact search costs O(N) comparisons per query, always. An ANN index answers with a small, roughly logarithmic number of comparisons by consulting a precomputed structure, and the structure is sometimes wrong. Recall versus comparisons is the entire product. The benchmark table in the demo output is the honest way to state it: pick the recall your application needs, read off the cost. Everything a vector database vendor tunes (M, ef_construction, ef_search, quantization) moves you along or shifts that curve.

## What Production Systems Do Differently

- SIMD-vectorized distance kernels and cache-aware memory layout; distance computation is the inner loop and is never interpreted Python.
- Quantization (scalar, product, or binary) to shrink vectors 4x to 32x, trading a further slice of recall for memory and bandwidth.
- Real embedding models, with the index parameters retuned whenever the model changes, because cluster geometry changes.
- Deletions via tombstones plus background rebuild or repair; concurrent inserts with fine-grained locking.
- Continuous recall monitoring by sampling queries and comparing against exact search on a shadow index, because recall regressions are silent.
- Alternative index families where they fit better: IVF for cheap builds over static corpora, DiskANN when vectors exceed RAM.

## Run It

```bash
cd build-from-scratch/vector-index
python3 vector_index.py
```

Runs in about 7 seconds, almost all of it the pure-Python graph build over 3000 vectors. Asserts validate the embedding's similarity ordering, recall@10 of at least 0.90 at ef=32, that HNSW-lite uses under half the brute-force comparisons, and that widening the beam monotonically buys recall on this data.

## Exercises

1. Replace `_select_neighbors` with `[n for _, n in cands[:cap]]` and rerun. Report recall at each ef and explain the mechanism of the collapse in terms of graph connectivity.
2. Sort the base vectors by cluster before inserting instead of round-robin. Measure the recall change and explain why insertion order affects the finished graph.
3. Sweep M over {4, 8, 16, 32} and plot (by table) build comparisons, per-query comparisons, and recall@10. Where does more connectivity stop paying?
4. Add a `brute_force_rescore` option: retrieve 4k candidates with ef=10, then exactly rescore them and return the top k. Compare recall and total comparisons against simply raising ef. This is the two-stage pattern most production systems use.
5. Implement IVF from scratch: k-means the base vectors into 32 lists (Lloyd's algorithm is 20 lines), search the nprobe closest lists. Benchmark it against HNSW-lite on the same data at equal recall and compare comparisons per query and build cost.

## Further Reading

- [Malkov and Yashunin, "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs" (2016)](https://arxiv.org/abs/1603.09320) - the HNSW paper; Algorithm 4 is the neighbor-selection heuristic this module shows to be load-bearing.
- [hnswlib source](https://github.com/nmslib/hnswlib) - the reference C++ implementation, small enough to read against this module line by line.
- [Weinberger et al., "Feature Hashing for Large Scale Multitask Learning" (2009)](https://arxiv.org/abs/0902.2206) - the hashing trick with the signed-hash analysis Part A relies on.
- [ann-benchmarks.com](https://ann-benchmarks.com/) - standardized recall-versus-throughput curves across ANN libraries; the same tradeoff this module measures, at production scale.
