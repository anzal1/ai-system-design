# Build a KV-Cache Simulator From Scratch

## Problem

Transformer decoding is autoregressive: token n+1 requires attention over tokens 1 through n. Done naively, every decode step re-derives the keys and values for the entire history, so the tenth token costs ten times the first and the total cost of a response grows with the square of its length. The KV cache is the single optimization that makes LLM serving economically viable, and its behavior explains most of what operators observe: why long conversations get slow and expensive, why providers sell prompt caching, and why context length is really a memory budget.

## What You Build

`kv_cache.py` decodes 48 tokens through single-head attention two ways and counts every multiply-accumulate:

- **No cache:** each step recomputes K and V for all previous tokens, which is what a stateless forward pass per token actually costs
- **With cache:** each step computes K and V once for the new token and appends them
- An assert that both paths produce bit-identical outputs, proving the cache is an optimization and not an approximation
- Measured per-token and cumulative MAC tables, asserted exactly against the closed forms `(2t+1)D^2 + 2tD` and `3D^2 + 2tD`
- A prompt-caching model: a 5-turn conversation over a 200-token system prompt, showing fresh prefill of the full history each turn costs 3.4x more than prefix reuse

At 48 tokens the uncached path already costs 11.4x more in total, and the gap widens linearly with length.

## How It Works

At decode step t, attention needs the query for the newest token and the keys and values for all t tokens. The query genuinely depends only on the new token. The keys and values for tokens 1 through t-1 were fully determined the moment those tokens were processed, so recomputing them is pure waste. The cache stores each k and v vector the first time it is computed.

The arithmetic follows directly. Without a cache, step t performs 2t+1 projection matvecs (K and V for everything, Q for the new token) at D squared multiplies each, so per-token cost grows linearly and the total is quadratic. With the cache, every step performs exactly 3 projections. The attention itself, one score per cached position plus the weighted sum, still costs 2tD per step and remains irreducibly quadratic in total, but its constant is D rather than D squared, so it stays a minor term at these scales.

The script counts real operations inside `dot` rather than trusting the formulas, then asserts the measured counts equal the formulas exactly. The growth-shape asserts check that doubling the sequence multiplies uncached total cost by roughly 4 and cached total cost by roughly 2.

The prompt-caching section applies the identical logic across requests instead of across steps. Turn n of a conversation must prefill the whole history unless the serving stack still holds the KV entries for the shared prefix. With prefix reuse, every token is prefilled exactly once, ever, and the script asserts the reused total equals one fresh prefill of the final conversation.

## Design Decisions

**Count operations, do not time them.** Wall-clock timing of pure Python measures the interpreter, not the algorithm. MAC counts are exact, deterministic, and map directly onto the FLOP budgets used in real capacity planning. The tradeoff is that counts ignore memory traffic, and in production decode is memory-bandwidth bound, not compute bound; the What Production Systems Do Differently section addresses that gap.

**Softmax omitted from the simulated attention.** Softmax adds exps and divides that do not change which terms are quadratic, and omitting it keeps the two decode paths trivially bit-comparable. The cost model loses nothing that matters at this altitude.

**Single head, single layer, D=32.** The per-layer, per-head costs simply multiply by layer and head counts, so the smallest configuration that shows the asymptotics is the right one. 48 steps is enough for an 11x cumulative gap while keeping the uncached path fast in pure Python.

**Bit-identical output as the correctness bar.** Recomputing k_i performs the same multiplies in the same order as computing it once, so exact float equality holds here and makes a sharp assert. On GPUs, reduction-order differences make this bar unachievable; simulators get to be stricter than the systems they model.

## Failure Modes

- **KV memory exhaustion.** The cache costs 2 x layers x positions x d_model x bytes-per-element per sequence. Real numbers: a 7B model at fp16 holds roughly 0.5 MB per token, so a 32k-token conversation pins about 16 GB, a whole GPU, for one user. Serving stacks that ignore this fall over at moderate concurrency.
- **Cache invalidation by prefix edits.** Any change to earlier tokens, an edited system prompt, a re-ranked tool list, a timestamp, invalidates every cached position after it. The prompt-cache table degrades to the fresh-prefill column.
- **Fragmentation from contiguous allocation.** Reserving max-context-length cache per request wastes most of it on short requests. This one failure mode motivated PagedAttention and roughly 2 to 4x throughput gains, which is a hint about how bad the waste was.
- **Cross-request leakage.** A shared prefix cache keyed incorrectly can serve one tenant's KV state to another. Prefix caches must be keyed on the exact token sequence and scoped to a trust boundary.
- **Mistaking cached decode for free decode.** The attention term still grows linearly per token with context length, and memory bandwidth grows with cache size, so long contexts slow decode even with a perfect cache. The cache removes recomputation, not context cost.

## What Production Systems Do Differently

- **PagedAttention (vLLM):** KV cache stored in fixed-size blocks with an indirection table, like virtual memory, eliminating fragmentation and enabling copy-on-write sharing of common prefixes across requests
- **Grouped-query and multi-query attention:** many query heads share few KV heads, shrinking the cache 4 to 8x at minor quality cost, a tradeoff made mostly for serving economics
- **KV quantization:** storing cache entries at 8-bit or lower, trading a little accuracy for double the concurrent sequences per GPU
- **Prefix caching as a product:** providers persist KV state for repeated prompt prefixes across requests and price cache reads at a fraction of fresh input tokens (Anthropic charges roughly 10 percent for cache hits, with a premium on cache writes), which is the pricing expression of the tables this script prints
- **Eviction and offload policies:** caches spill from GPU to CPU or disk under pressure, so a "cache hit" has tiers with very different latencies

## Run It

```bash
python3 kv_cache.py
```

Runs in well under a second. Prints per-token and cumulative MAC tables for both decode paths, the growth ratios under doubling, and the 5-turn prompt-caching comparison. Inline asserts validate bit-identical outputs, exact agreement with the closed-form cost model, quadratic versus near-linear growth shape, and that prefix reuse equals prefilling each token exactly once.

## Exercises

1. Add a bytes column: for each n, compute the cache size in bytes at fp16 for this model and for a 32-layer, d_model 4096, 8-KV-head model. Find the context length where one sequence exceeds 24 GB.
2. Model grouped-query attention: parameterize the number of KV heads and show how cache size and projection MACs change while the score computation does not.
3. Extend the prompt-caching model with pricing: assign costs of 1.0 per fresh input token, 0.1 per cached read, and 1.25 per cache write, then find the minimum number of reuses a prefix needs before caching is profitable.
4. Simulate an edited system prompt at turn 3 (invalidate the prefix) and quantify how much of the 3.4x saving survives. Then simulate moving the edit to the end of the prompt instead.
5. Implement block-based cache accounting: allocate KV memory in blocks of 16 tokens, run 100 random-length requests (seeded), and compare peak memory against contiguous max-length allocation. You have rebuilt the motivation for PagedAttention.

## Further Reading

- [Efficient Memory Management for Large Language Model Serving with PagedAttention (Kwon et al., 2023)](https://arxiv.org/abs/2309.06180), the vLLM paper; its Section 3 measures how much KV memory naive serving wastes, continuing exactly where exercise 5 ends.
- [Efficiently Scaling Transformer Inference (Pope et al., 2022)](https://arxiv.org/abs/2211.05102), works through the memory-bandwidth arithmetic that MAC counting deliberately omits, and explains why decode is bandwidth bound.
- [Anthropic prompt caching documentation](https://docs.claude.com/en/docs/build-with-claude/prompt-caching), the production pricing and exact-prefix-matching rules that the second half of this script models.
- [GQA: Training Generalized Multi-Query Transformer Models (Ainslie et al., 2023)](https://arxiv.org/abs/2305.13245), the standard technique for shrinking the KV cache and the quality tradeoff data behind it.
