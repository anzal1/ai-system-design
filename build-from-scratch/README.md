# Build From Scratch

Reading about a system teaches you its vocabulary. Building it teaches you its tradeoffs. This track implements every core component of a production AI system in pure Python standard library, no frameworks, no API keys, no network. Every module runs with a single command and validates itself with asserts.

These are pedagogical implementations, not production code. Each README ends with a section on what production systems do differently, so you know exactly which corners were cut and why real systems cannot cut them.

## Rules Of The Track

- Pure Python 3, standard library only. If you can read Python, you can read all of it.
- Every module runs offline and deterministically: `python3 <module>.py`.
- Every module prints a demo that makes the core tradeoff visible, not just a green checkmark.
- Every module maps back to a pattern page or decision guide in the main course.

## The Path

Build them in order. Each layer sits on the one below it.

### Layer 1: The Model Substrate

Why models cost what they cost and why context length hurts.

1. [Tokenizer](./tokenizer/README.md): byte-pair encoding, the unit of cost and latency.
2. [Transformer](./transformer/README.md): a forward pass with attention, small enough to trace by hand.
3. [KV Cache](./kv-cache/README.md): why decode without a cache is quadratic and what caching buys.

### Layer 2: The Retrieval Stack

The machinery under every RAG system.

4. [Chunker](./chunker/README.md): three chunking strategies and how boundaries decide retrieval quality.
5. [BM25](./bm25/README.md): lexical search with an inverted index, still half of every good retrieval system.
6. [Vector Index](./vector-index/README.md): embeddings via the hashing trick, brute-force cosine search, then an HNSW-lite graph index with a real recall-versus-speed benchmark.
7. [RAG Pipeline](./rag-pipeline/README.md): hybrid retrieval with reciprocal rank fusion, token-budgeted context assembly, and citation-grounded answers.

### Layer 3: The Serving Layer

What sits between your users and the model.

8. [Model Router](./model-router/README.md): complexity scoring, cost-aware selection, fallback chains, and a budget governor.
9. [Rate Limiter](./rate-limiter/README.md): token-aware token buckets, per-tenant fairness, and why request-count limits fail for LLM traffic.
10. [Prompt Cache](./prompt-cache/README.md): a prefix trie with TTL and eviction, and the cost model that makes stable prefixes worth designing for.
11. [Semantic Cache](./semantic-cache/README.md): similarity-matched response caching and the correctness gates that keep it from becoming a bug.

### Layer 4: The Control Plane

The parts that make an AI system trustworthy.

12. [Agent Loop](./agent-loop/README.md): a tool-use loop with schema validation, a policy gate, budget limits, and loop detection.
13. [Eval Harness](./eval-harness/README.md): datasets, graders, baselines, and a regression gate that actually fires.
14. [Guardrails](./guardrails/README.md): injection heuristics, PII detection, and a hand-written structured-output validator with repair.

## How To Use This Track

- Pair each module with its course page: the module shows the mechanism, the page shows the production design space around it.
- Do the exercises. They escalate from tweaking parameters to changing the design, and the later ones are interview-grade.
- When you finish a layer, try the corresponding design review in [design-reviews](../design-reviews) with your new mental model.
