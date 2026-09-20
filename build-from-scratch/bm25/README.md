# BM25 From Scratch

## Problem

Vector search misses exact terms. Error codes, ticket IDs, product names, acronyms, and policy numbers are exactly the tokens an embedding model compresses away, and they are exactly what enterprise queries contain. Every serious retrieval stack keeps a lexical retriever next to the vector index, and the lexical retriever is almost always BM25 or a close variant.

Most engineers use BM25 through Elasticsearch or OpenSearch without knowing what k1 and b do, which makes tuning a guessing game. The whole algorithm fits in a page of Python.

## What You Build

One file, `bm25.py`, containing:

- A tokenizer: lowercase, alphanumeric tokens, small stopword list.
- An inverted index: term to postings list of `(doc_id, term_frequency)`.
- BM25 IDF with the Lucene-style smoothing that keeps common terms non-negative.
- The full BM25 scoring function with tunable k1 and b.
- Top-k search over an inline eight-document corpus, including one deliberately spammy long document that makes the parameters visible.

The demo runs three searches, then reruns the query `billing` under different k1 and b settings and shows the ranking change.

## How It Works

Indexing walks each document once, counts term frequencies, and appends `(doc_id, tf)` to each term's postings list. Search only touches postings lists for query terms, which is the entire reason inverted indexes exist: scoring cost scales with the number of documents containing the query terms, not corpus size.

The score for a document is a sum over query terms of `IDF(t) * saturation(tf, |d|)`:

- **IDF** rewards rare terms. `log(1 + (N - df + 0.5) / (df + 0.5))`. A term in one of eight docs gets weight 1.79; a term in half the corpus gets 0.69. The +0.5 smoothing and the +1 inside the log are the variant Lucene ships, chosen so a term appearing in most documents scores near zero rather than negative.
- **k1** controls term-frequency saturation. The term-frequency factor is `tf * (k1 + 1) / (tf + k1 * norm)`, which is a curve that rises steeply at tf=1 and flattens. At k1=0.2, the fourteenth occurrence of "billing" is worth almost nothing; at k1=5.0, repetition keeps paying. The demo shows the spammy document's lead over normal documents growing from 1.19x to 4.6x as k1 rises.
- **b** controls length normalization. The denominator's `norm = 1 - b + b * |d| / avgdl` inflates for long documents when b is high, deflating their per-term scores. At b=0, document length is ignored. At b=1, scores are fully normalized by relative length, and the demo shows short focused documents climbing the ranking.

## Design Decisions

- **Lucene IDF variant over the classic Robertson-Sparck Jones formula.** The classic formula goes negative when a term appears in more than half the corpus, which lets a matching document score below a non-matching one. The smoothed variant is what production engines actually run.
- **Stopword removal in the tokenizer.** BM25's IDF already downweights common terms, so stopwords are not strictly needed for ranking quality; they are removed here to keep postings lists and demo output readable. Production engines often keep them and rely on IDF.
- **Scores computed with a document-at-a-time accumulator dict.** Simple and correct. Real engines use block-max WAND or similar algorithms to skip documents that cannot reach the current top-k, because they cannot afford to score every candidate.
- **k1 and b overridable per query.** This exists purely so the demo can show parameter effects side by side; production systems fix them per index after offline tuning.

## Failure Modes

- **Vocabulary mismatch.** BM25 scores zero for any paraphrase. "Restart the container" will never match a document that only says "reboot the pod". This is the structural failure that motivates hybrid retrieval, and no parameter tuning fixes it.
- **k1 too high** rewards keyword-stuffed documents; the demo's doc7 is the canonical victim profile. **k1 too low** makes BM25 nearly binary (term present or not), losing the signal that a document about billing mentions billing more than once.
- **b too high** buries long documents that are legitimately comprehensive, a common problem for reference pages and runbooks. **b too low** lets long documents win by containing everything.
- **Tiny corpora make IDF noisy.** With eight documents, one added document visibly moves every IDF. Parameter studies on small corpora do not transfer to large ones.
- **Tokenization decides everything upstream.** Splitting `error-code-503` into three tokens versus one changes what queries can match. Most "BM25 is bad on our data" complaints are tokenizer complaints.

## What Production Systems Do Differently

- Block-max WAND and impact-ordered postings to skip non-competitive documents, plus compressed postings (delta encoding, variable-byte or SIMD codecs).
- Language-aware analysis chains: stemming or lemmatization, synonym expansion, per-field tokenizers, character filters for identifiers.
- Field-weighted scoring (BM25F) so a title match outranks a body match.
- Distributed sharding with per-shard scoring and global merge, where per-shard IDF can subtly diverge from global IDF.
- Parameter tuning against labeled relevance judgments, not defaults; though k1 between 1.2 and 2.0 with b at 0.75 is a robust starting point that decades of TREC experiments keep confirming.

Why lexical search still matters next to vectors: embeddings are trained to preserve meaning, and they trade away surface form to do it. An embedding of "invoice INV-2024-88191 was double charged" and one of "invoice INV-2024-88190 was double charged" are nearly identical vectors, but only one document answers the query. BM25 is the component that treats those two strings as completely different, because lexically they are. Hybrid systems win because the failure modes are complementary: BM25 cannot see paraphrase, vectors cannot see identity.

## Run It

```bash
cd build-from-scratch/bm25
python3 bm25.py
```

Runs in under a second. Prints IDF values, three ranked searches, and the k1 and b studies. Asserts validate IDF ordering, expected top results for each query, that high k1 lets repetition win, that low k1 flattens the repetition advantage, and that length normalization shrinks the long document's lead.

## Exercises

1. Remove the stopword list and rerun. Which rankings change, and why does IDF absorb most but not all of the damage?
2. Add a `remove(doc_id)` method. Decide how to handle `avgdl` and postings cleanup, and state the cost of your approach at 10 million documents.
3. Implement BM25F: give each document a `title` and `body` field with separate per-field length normalization and a title boost. Show a query where field weighting flips the top result.
4. Implement a WAND-style upper-bound skip: precompute each term's maximum possible score contribution and stop scoring documents that cannot beat the current k-th score. Count scored documents with and without it.
5. Tune k1 and b by grid search against a handmade set of 10 queries with graded relevance labels, optimizing NDCG@3. Report how flat or sharp the optimum is.

## Further Reading

- [Robertson and Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond" (2009)](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf) - the definitive survey by BM25's principal author, including where k1 and b come from.
- [Lucene BM25Similarity source](https://github.com/apache/lucene/blob/main/lucene/core/src/java/org/apache/lucene/search/similarities/BM25Similarity.java) - the exact scoring code the industry runs, including the smoothed IDF this module copies.
- [Elasticsearch: Practical BM25](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables) - a production vendor's plain-language walkthrough of k1 and b effects.
- [Ding and Suel, "Faster Top-k Document Retrieval Using Block-Max Indexes" (2011)](https://dl.acm.org/doi/10.1145/2009916.2009935) - the skipping technique that makes exhaustive scoring unnecessary at scale.
