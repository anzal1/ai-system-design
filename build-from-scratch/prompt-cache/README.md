# Build A Prefix Cache From Scratch

One file, pure Python stdlib. You build the data structure behind provider prompt caching: a trie keyed on token prefixes, with TTL and LRU eviction and the cache-write versus cache-read cost model that decides whether caching makes or loses money.

## Problem

LLM requests in most products share enormous prefixes. The system prompt, tool definitions, and output schemas are identical across every request, and in a chat, each turn repeats the whole conversation so far. Recomputing attention state over those tokens on every request is pure waste, so providers cache the computed prefix state and charge a fraction of the input price to reuse it.

The catch is in the word prefix. A hit requires the exact same tokens in the exact same positions from position zero. One volatile token near the front, a timestamp, a request id, a user name, invalidates everything after it. This makes hit rate a property of how you order your prompt, not of how the cache is implemented. The demo proves it: an identical workload goes from an 83 percent hit rate and 68 percent cost saving to a 0 percent hit rate and a net loss just by prepending one timestamp token.

## What You Build

- A toy word-level tokenizer (stable ids for stable text, which is all the cache math needs)
- A trie where each node is a token and marked nodes are cache breakpoints with TTL and LRU bookkeeping
- Longest-cached-prefix lookup: walk the request's tokens down the trie, remember the deepest live breakpoint passed
- TTL eviction (a prefix unused past its TTL is dead) and LRU eviction against a total cached-token budget
- A cost model with three prices: plain input, cache write at a premium (1.25x), cache read at a deep discount (0.1x)
- A chat workload simulation: 40 sessions sharing a 1,800-token system prompt and tool block, 6 turns each, with turn N extending turn N-1's prefix
- The same workload rerun with a per-request timestamp placed before the system prompt, to measure exactly what ordering costs

## How It Works

1. Lookup walks the request tokens down the trie from the root. Every marked node passed is a candidate; the deepest live one wins. Expiry is checked lazily during the walk, so no background sweeper is needed.
2. On every request, the full token sequence is inserted as a new breakpoint. The tokens between the previous breakpoint and the new one are the marginal write, billed at the write premium; the tokens up to the hit are billed at the read discount.
3. Accounting charges each breakpoint only its marginal tokens beyond its nearest cached ancestor, so a conversation whose every turn is a breakpoint does not count the shared system prompt once per turn.
4. When total cached tokens exceed the budget, the least recently used breakpoint is uncached until the budget holds. The newest insert is never the victim.

## Design Decisions

- **A trie, not a hash map.** Hashing the full prompt gives exact-match caching only. The trie gives longest-prefix matching, which is what makes multi-turn chat cacheable: turn 3 hits turn 2's breakpoint even though the full prompts differ.
- **Lazy expiry.** TTL is enforced during lookup walks rather than by a timer. The trade-off is visible in the demo: breakpoints on abandoned branches are never walked again, so they die by LRU pressure instead of TTL. Production caches add background sweeps for exactly this reason.
- **Write premium in the model.** Caching is not free. With a 1.25x write price and 0.1x read price, a prefix must be read back roughly once before it pays for its write. A zero-hit workload is strictly worse with caching on, and the demo's ordering experiment lands there.
- **Marginal-token accounting.** Charging each breakpoint its full depth would double count shared prefixes and evict the wrong things. Marginal accounting keeps the budget meaningful.
- **The cache stores prefix lengths, not responses.** A prefix cache saves compute on input tokens. It never changes the output. That distinction is why it is safe by default, unlike semantic response caching (see the semantic-cache module).

## Failure Modes

- A deploy edits one word of the system prompt and the fleet-wide hit rate drops to zero until the new prefix is rewritten everywhere. Cost spikes exactly when a deploy is already in flight.
- Dynamic content creeps forward: someone adds "Today is {date}" at the top of the system prompt and silently converts every cache read into a cache write at the premium price.
- Tool definitions serialized from a dict with unstable key order produce different token sequences for identical logical content. Hits require byte stability, not semantic stability.
- Session-first requests miss even when the shared base is in everyone's prompts, because a breakpoint only exists where one was explicitly written. In this implementation, each session's first turn is a guaranteed miss (40 of the 240 requests).
- Teams see cheap cached tokens and expand context freely, then a hit-rate regression restores full price on a context that is now five times larger.

## What Production Systems Do Differently

- The cached object is the transformer KV cache for the prefix, stored on or near the serving GPUs, so the cache is also a latency win (seconds of prefill skipped), not just a cost win.
- Cache breakpoints are explicit API surface (Anthropic's `cache_control` blocks) or fully automatic (OpenAI caches prefixes over 1,024 tokens on its own). Explicit control lets clients put breakpoints exactly after stable content.
- Routing is cache-aware: serving stacks like vLLM and SGLang route requests sharing a prefix to the replica that already holds its KV blocks, because a cache on replica A is useless to a request landing on replica B.
- TTLs are short (minutes, refreshed on use) because GPU-adjacent memory is scarce; eviction is by block, not whole prefix, using paged KV storage.
- Providers report cache reads and writes as separate line items in usage metadata, and mature teams alert on hit-rate drops the same way they alert on error rates.

## Run It

```bash
python3 prompt_cache.py
```

Runs in a few seconds. Prints hit rate, tokens read from cache, cost with and without caching, savings, and eviction counts for the stable-prefix workload, then the same numbers for the timestamp-first variant. Inline asserts validate exact-prefix hit semantics, TTL expiry, front-token invalidation, LRU eviction under a tiny budget, the 80 percent plus hit rate on the chat workload, and that the reordered workload strictly loses money.

## Exercises

1. Each session's first turn misses because no breakpoint exists at the shared system prompt. Insert an explicit breakpoint for the base prefix before the workload starts and measure the new hit rate and saving.
2. Add a minimum cacheable length (say 1,024 tokens, as OpenAI enforces) so short prefixes are never written. Measure how it changes total cost on this workload and explain who benefits from the rule.
3. Model latency: give cache reads 0.05 ms per token of skipped prefill and misses 0.5 ms per token. Report p50 and p95 request latency for both workload variants.
4. Implement block-level caching: breakpoints only at multiples of 64 tokens. Compare hit tokens against exact breakpoints and explain why real systems accept the loss.
5. Add a second tenant whose prompts share no tokens with the first, give both one shared token budget, and make one tenant ten times chattier. Show the quiet tenant's hit rate collapse under LRU, then fix it with per-tenant budgets.

## Further Reading

- [Anthropic: prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) documents explicit cache breakpoints, the 1.25x write and 0.1x read pricing this module's cost model mirrors, and TTL behavior.
- [OpenAI: prompt caching](https://platform.openai.com/docs/guides/prompt-caching) shows the automatic variant: prefix caching over 1,024 tokens with no client control, a useful contrast in API design.
- [SGLang: RadixAttention (Zheng et al., 2023)](https://arxiv.org/abs/2312.07104) is the paper behind serving-side prefix reuse with a radix tree over KV blocks, the production-grade version of this module's trie.
- [../../patterns/prompt-caching.md](../../patterns/prompt-caching.md) is the companion pattern page on stable prefix design, cache safety, and measuring real hit rates.
