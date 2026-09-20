# Build A Semantic Cache From Scratch

One file, pure Python stdlib. You build a semantic response cache: hashed n-gram embeddings, cosine threshold matching, staleness windows, and a rule-based correctness-risk gate, then you watch it serve a confidently wrong answer, on purpose.

## Problem

A prefix cache reuses computation and never changes the answer. A semantic cache reuses answers: if a new query is similar enough to an old one, serve the stored response and skip the model. On FAQ-shaped traffic this can eliminate a large share of model calls.

It is also the only cache in this track that can be wrong. Similarity is not equivalence. "Token limit on the basic plan" and "token limit on the pro plan" are one word apart, score 0.83 cosine with these embeddings, and require different answers. A prefix cache miss costs latency; a semantic cache false hit costs correctness, and the user gets a fast, fluent, wrong response with no error anywhere in the logs. Before treating semantic caching as an optimization, treat it as a correctness feature that must be argued safe.

## What You Build

- Embeddings from hashed character n-grams: every 3, 4, and 5-gram of the normalized query is hashed into one of 256 signed buckets (the hashing trick), then L2-normalized. No vocabulary, no training, no dependencies.
- Cosine threshold matching by linear scan over cached entries, with three outcome bands: hit, near miss (close but below threshold), and miss.
- Staleness windows: entries past an age limit are never served, even on an exact match.
- A correctness-risk gate: rule-based detection of time-sensitive queries (today, latest, weather, news, prices) and user-specific queries (my account, my order, order numbers). Gated queries are never served from cache and never stored, so a risky answer cannot enter the cache in the first place.
- Five scripted scenarios: true hits on paraphrases, a near-miss rejection, the risk gate, staleness expiry, and a poisoned-cache failure where a greedy threshold serves the wrong plan's answer.

## How It Works

1. The gate runs before everything. If a query matches a time-sensitive or user-specific rule, the lookup is refused and so is the store. Order matters: gating only reads would still let risky answers poison the cache for later queries.
2. Ungated queries are embedded and compared against every entry. The best match above the threshold and inside the staleness window is served.
3. Matches that fall within 0.15 below the threshold are counted as near misses. This band is the observability surface: it is where the next false hit is hiding, and production systems sample it for human review.
4. The poisoned-cache scenario runs the same query pair at two thresholds. At 0.88 the pro-plan question is a near miss and goes to the model. At 0.75 it hits the basic-plan answer and the cache returns a wrong number with a healthy-looking log line.

## Design Decisions

- **The gate is rules, not a model.** A gate that exists to bound worst-case behavior should be predictable and auditable. Rules have known false negatives (the demo's own comments admit bare "my" was too broad to use), but they never drift, and every gating decision can be explained by pointing at a regex.
- **Never store gated queries, not just never serve them.** Storing "what is my account balance" under any answer creates a poisoned entry that a differently phrased but similar query could hit later. Write-side gating removes the class of bug.
- **A conservative default threshold.** With these embeddings, real paraphrases score 0.89 to 0.95 and one-word substitutions score 0.81 to 0.86, so 0.88 separates them for the demo corpus. The overlap between those two bands is the fundamental problem, and no threshold removes it; it only chooses which error you make more often.
- **Near misses are a first-class outcome.** The gap between "hit" and "miss" is where correctness decisions happen. Counting it separately is what makes threshold tuning an evidence-based activity instead of a vibe.
- **Linear scan, honestly.** Real systems use an ANN index for speed. The logic above the index (threshold, staleness, gate) is identical, and this module keeps it legible.

## Failure Modes

- The false hit: two queries above threshold that need different answers. This is not an edge case, it is a property of every similarity measure, and character n-grams make it vivid because surface-similar strings with opposite meanings score high. Dense embeddings reduce the rate; nothing makes it zero.
- Silent staleness: the cached answer was right when stored and wrong now (a plan's limits changed). The staleness window bounds the exposure but the window is a guess.
- Gate recall failures: "what do I owe" is user-specific and matches no rule here. Every rule list is incomplete; the question is whether misses fail toward the model (safe, this design) or toward the cache.
- Cross-user leakage: without per-user or per-tenant partitioning, one user's cached answer can serve another user's query. The gate blocks the obvious cases; partitioning is the real fix.
- Metric seduction: hit rate is the dashboard number, and every false hit increments it. A team optimizing hit rate without a wrong-answer eval is optimizing the failure mode.

## What Production Systems Do Differently

- Dense embeddings from a trained model replace hashed n-grams, moving similarity from surface form toward meaning. Paraphrases with no shared words can hit; lexically close opposites score lower. The false-hit problem shrinks and does not disappear.
- An ANN index (HNSW, IVF) replaces the linear scan so lookup stays fast at millions of entries.
- Verification layers sit above the threshold: a cheap model asked "does this cached answer correctly answer this query" before serving, trading back some latency for a correctness check.
- Caches are partitioned per tenant and often per user, with invalidation hooks wired to the systems whose data the answers describe (pricing tables, plan limits, docs).
- Thresholds are tuned offline against labeled query pairs, reported as a precision-recall trade-off, and re-evaluated when the embedding model or the traffic changes.
- Many teams conclude the risk is not worth it for open-ended queries and restrict semantic caching to closed FAQ corpora where the answer set is enumerable and reviewed.

## Run It

```bash
python3 semantic_cache.py
```

Runs in under a second. Prints the five scenarios with per-lookup reasons (hit with score, near miss, gated with the flag, expired with age), then aggregate stats and model calls avoided. Inline asserts validate embedding sanity, gate rules, all four paraphrase hits, the near-miss rejection, gate behavior on reads and writes, staleness expiry, and both sides of the poisoned-cache threshold experiment.

## Exercises

1. Find a query pair the gate misses: user-specific meaning, none of the listed possessives. Confirm the cache will happily serve one user's answer to the other, then extend the rules to catch your pair without gating the FAQ corpus.
2. Add per-entry categories with different staleness windows (pricing: 1 hour, how-to: 30 days) and route each `put` through a rule-based classifier. Show one query where the category rule, not the similarity, decides correctness.
3. Build the threshold curve: create 20 labeled query pairs (10 equivalent, 10 trap pairs), sweep the threshold from 0.5 to 0.99, and print false-hit rate against true-hit rate at each step. Find the threshold you would defend in a review.
4. Add a verification stub: when similarity lands between 0.83 and 0.93, call a `verify(query, cached_query)` function (simulate it with a rule that compares the non-overlapping words) before serving. Measure how many false hits it removes and how many true hits it costs.
5. Implement cross-user poisoning end to end: user A's gated-rule-missing query stores a personal answer, user B's paraphrase retrieves it. Then fix it with per-user cache partitions and show the fix also destroyed most of your hit rate. Write three sentences on when that trade is worth it.

## Further Reading

- [GPTCache (Bang et al., 2023)](https://arxiv.org/abs/2310.02238) describes the best-known open-source semantic cache: embeddings, vector store, eviction, and reported hit rates, useful as the production-shaped version of this module.
- [Weinberger et al. (2009): Feature Hashing for Large Scale Multitask Learning](https://arxiv.org/abs/0902.2206) is the paper behind the signed hashing trick this module uses for embeddings.
- [Malkov and Yashunin (2016): HNSW](https://arxiv.org/abs/1603.09320) is the ANN index that replaces this module's linear scan at scale.
- [../../patterns/prompt-caching.md](../../patterns/prompt-caching.md) covers the safe sibling: prefix caching that reuses computation instead of answers, worth reading side by side to internalize why one needs a correctness argument and the other does not.
