"""Prefix caching from scratch.

Prompt caches are prefix caches. The provider stores the model's computed
state (KV cache) for a token prefix, and a later request that starts with the
exact same tokens skips recomputing it. Two consequences fall out of "exact
same tokens" and decide the entire economics:

  1. Ordering matters. One volatile token early in the prompt invalidates
     everything after it. Stable content first, volatile content last.
  2. Hits are exact-prefix hits. The natural data structure is a trie keyed
     on token prefixes, which is what this file builds, with TTL and LRU
     eviction and a cache-write vs cache-read cost model.

Pure stdlib. Deterministic. Simulated time. Run: python3 prompt_cache.py
"""

import random

# ---------------------------------------------------------------------------
# Tokenizer: a toy word-level tokenizer. Real tokenizers are subword, but the
# caching math only needs stable ids for stable text, which this provides.
# ---------------------------------------------------------------------------

class Tokenizer:
    def __init__(self):
        self.vocab = {}

    def encode(self, text):
        ids = []
        for w in text.split():
            if w not in self.vocab:
                self.vocab[w] = len(self.vocab)
            ids.append(self.vocab[w])
        return ids


# ---------------------------------------------------------------------------
# Cost model, USD per million tokens. The ratios mirror how providers price
# caching: writing a prefix costs a premium over plain input, reading it back
# costs a small fraction. Caching pays off when a written prefix is read back
# enough times to cover its write premium.
# ---------------------------------------------------------------------------

PRICE_INPUT = 3.00        # uncached input tokens
PRICE_CACHE_WRITE = 3.75  # 1.25x input: storing the prefix costs extra
PRICE_CACHE_READ = 0.30   # 0.1x input: reading a cached prefix is cheap

CACHE_TTL = 300.0         # seconds a cached prefix lives without a hit
MAX_CACHED_TOKENS = 50000  # total token budget across all cached prefixes


# ---------------------------------------------------------------------------
# The trie. Each node is one token id. A node marked as a breakpoint means
# "the prefix ending here is cached" and carries TTL and LRU bookkeeping.
# Lookup walks the request's tokens down the trie and remembers the deepest
# live breakpoint it passed: that is the longest cached prefix.
# ---------------------------------------------------------------------------

class TrieNode:
    __slots__ = ("children", "cached_at", "last_used", "depth", "path")

    def __init__(self, depth):
        self.children = {}
        self.cached_at = None   # None means not a cache breakpoint
        self.last_used = None
        self.depth = depth      # tokens from root, i.e. prefix length
        self.path = ()          # token ids from root to this node


class PrefixCache:
    def __init__(self, ttl=CACHE_TTL, max_tokens=MAX_CACHED_TOKENS):
        self.root = TrieNode(0)
        self.ttl = ttl
        self.max_tokens = max_tokens
        self.cached_tokens = 0
        self.breakpoints = set()  # live breakpoint nodes, for eviction scans
        self.evictions_ttl = 0
        self.evictions_lru = 0

    def _expire(self, node, now):
        if node.cached_at is not None and now - node.last_used > self.ttl:
            self._uncache(node)
            self.evictions_ttl += 1

    def _uncache(self, node):
        # Only the deepest breakpoint on a path holds "new" tokens beyond the
        # previous breakpoint, but accounting per-breakpoint by full depth
        # would double count. We charge each breakpoint only its marginal
        # tokens at insert time, stored implicitly: charge = depth minus the
        # nearest cached ancestor's depth at the time of caching. To keep the
        # implementation honest and simple, we recompute marginal size here.
        self.cached_tokens -= self._marginal_tokens(node)
        node.cached_at = None
        node.last_used = None
        self.breakpoints.discard(node)

    def _marginal_tokens(self, node):
        """Tokens this breakpoint holds beyond its nearest cached ancestor."""
        ancestor_depth = 0
        for bp in self.breakpoints:
            if bp is node:
                continue
            if bp.cached_at is not None and bp.depth < node.depth \
                    and self._is_ancestor(bp, node):
                ancestor_depth = max(ancestor_depth, bp.depth)
        return node.depth - ancestor_depth

    def _is_ancestor(self, a, b):
        """True if breakpoint a lies on the path from root to b."""
        # The trie has no parent pointers; walk from root toward b's tokens is
        # not available either, so we store paths instead. See lookup(): we
        # tag nodes with their path tuple lazily. For clarity over speed.
        return b.path[:len(a.path)] == a.path

    def lookup(self, tokens, now):
        """Walk the trie. Returns (cached_prefix_len, deepest_live_node)."""
        node = self.root
        best = 0
        path = []
        for tok in tokens:
            if tok not in node.children:
                break
            node = node.children[tok]
            path.append(tok)
            self._expire(node, now)
            if node.cached_at is not None:
                node.last_used = now
                best = node.depth
        return best

    def insert(self, tokens, now):
        """Mark the full token sequence as a cache breakpoint."""
        node = self.root
        path = []
        for tok in tokens:
            path.append(tok)
            if tok not in node.children:
                node.children[tok] = TrieNode(node.depth + 1)
                node.children[tok].path = tuple(path)
            node = node.children[tok]
        node.path = tuple(path)
        if node.cached_at is not None:
            node.last_used = now
            return
        node.cached_at = now
        node.last_used = now
        self.breakpoints.add(node)
        self.cached_tokens += self._marginal_tokens(node)
        # LRU eviction: drop the least recently used breakpoint until the
        # token budget holds. Never evict what we just inserted.
        while self.cached_tokens > self.max_tokens and len(self.breakpoints) > 1:
            victim = min((bp for bp in self.breakpoints if bp is not node),
                         key=lambda bp: bp.last_used)
            self._uncache(victim)
            self.evictions_lru += 1


# ---------------------------------------------------------------------------
# The metered client: wraps the cache with the provider cost model.
# ---------------------------------------------------------------------------

class MeteredClient:
    def __init__(self, cache):
        self.cache = cache
        self.hits = 0
        self.misses = 0
        self.tokens_read_from_cache = 0
        self.cost_with_cache = 0.0
        self.cost_without_cache = 0.0

    def send(self, tokens, now):
        n = len(tokens)
        self.cost_without_cache += n * PRICE_INPUT / 1e6
        hit_len = self.cache.lookup(tokens, now)
        new_tokens = n - hit_len
        if hit_len > 0:
            self.hits += 1
            self.tokens_read_from_cache += hit_len
        else:
            self.misses += 1
        # Read the cached prefix cheap, write the extension at a premium.
        self.cost_with_cache += hit_len * PRICE_CACHE_READ / 1e6
        self.cost_with_cache += new_tokens * PRICE_CACHE_WRITE / 1e6
        self.cache.insert(tokens, now)
        return hit_len


# ---------------------------------------------------------------------------
# Workload: a chat product. Every session shares one long system prompt and
# tool definitions, then diverges per user, and each turn extends the
# session's own prefix. This is the shape prompt caching was built for.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = " ".join(f"sys{i}" for i in range(1200))  # 1200 stable tokens
TOOL_DEFS = " ".join(f"tool{i}" for i in range(600))      # 600 stable tokens


def run_chat_workload(client, rng, sessions=40, turns=6):
    now = 0.0
    tok = Tokenizer()
    base = tok.encode(SYSTEM_PROMPT + " " + TOOL_DEFS)
    for s in range(sessions):
        history = list(base)
        for t in range(turns):
            user_msg = " ".join(
                f"u{s}t{t}w{i}" for i in range(rng.randint(20, 80)))
            history = history + tok.encode(user_msg)
            client.send(list(history), now)
            # Simulated assistant reply extends the prefix for the next turn.
            reply = " ".join(f"a{s}t{t}w{i}" for i in range(rng.randint(30, 120)))
            history = history + tok.encode(reply)
            now += rng.uniform(2.0, 20.0)  # think time between turns
    return now


def main():
    rng = random.Random(11)

    # --- unit checks: trie mechanics -----------------------------------------
    c = PrefixCache(ttl=100.0, max_tokens=1000)
    tk = Tokenizer()
    a = tk.encode("s s s alpha")
    b = tk.encode("s s s beta")
    assert c.lookup(a, 0.0) == 0, "cold cache misses"
    c.insert(a, 0.0)
    assert c.lookup(a, 1.0) == 4, "exact repeat hits the full prefix"
    assert c.lookup(b, 1.0) == 0, \
        "shared words are not a hit: only a cached breakpoint counts"
    c.insert(b, 1.0)
    assert c.lookup(b, 2.0) == 4

    # TTL: a breakpoint unused past its TTL is dead.
    assert c.lookup(a, 300.0) == 0, "TTL evicts stale prefixes"
    assert c.evictions_ttl >= 1

    # One changed token at the front kills everything after it.
    c2 = PrefixCache()
    stable = tk.encode("system system system question")
    volatile = tk.encode("time=1730000000 system system system question")
    c2.insert(stable, 0.0)
    assert c2.lookup(stable, 1.0) == len(stable)
    assert c2.lookup(volatile, 1.0) == 0, \
        "a volatile token at position 0 invalidates the whole prefix"

    # LRU: tiny budget forces eviction of the least recently used prefix.
    c3 = PrefixCache(ttl=1e9, max_tokens=10)
    p1 = tk.encode("x1 x2 x3 x4 x5 x6")
    p2 = tk.encode("y1 y2 y3 y4 y5 y6")
    c3.insert(p1, 0.0)
    c3.insert(p2, 5.0)  # 12 tokens > 10 budget, p1 is older, p1 dies
    assert c3.lookup(p1, 6.0) == 0 and c3.lookup(p2, 6.0) == 6
    assert c3.evictions_lru == 1

    # --- the chat workload ----------------------------------------------------
    cache = PrefixCache()
    client = MeteredClient(cache)
    sim_end = run_chat_workload(client, rng)

    total = client.hits + client.misses
    hit_rate = client.hits / total
    saved = client.cost_without_cache - client.cost_with_cache
    print("PREFIX CACHE DEMO (chat workload: shared system prompt, divergent turns)")
    print(f"  requests: {total} across 40 sessions x 6 turns, "
          f"simulated {sim_end:.0f}s")
    print(f"  hit rate: {hit_rate:.1%}  ({client.hits} hits, {client.misses} misses)")
    print(f"  tokens read from cache: {client.tokens_read_from_cache}")
    print(f"  cost without cache: ${client.cost_without_cache:.4f}")
    print(f"  cost with cache:    ${client.cost_with_cache:.4f}")
    print(f"  saved:              ${saved:.4f} "
          f"({100 * saved / client.cost_without_cache:.0f}%)")
    print(f"  evictions: {cache.evictions_ttl} ttl, {cache.evictions_lru} lru")

    # --- the ordering experiment: same content, volatile token first ---------
    cache_bad = PrefixCache()
    client_bad = MeteredClient(cache_bad)
    rng2 = random.Random(11)
    now = 0.0
    tok2 = Tokenizer()
    base_text = SYSTEM_PROMPT + " " + TOOL_DEFS
    for s in range(40):
        history = []
        for t in range(6):
            # A per-request timestamp placed BEFORE the system prompt. Every
            # request now has a unique first token.
            stamp = f"ts={s * 1000 + t}"
            user_msg = " ".join(
                f"u{s}t{t}w{i}" for i in range(rng2.randint(20, 80)))
            history = history + tok2.encode(user_msg)
            full = tok2.encode(stamp + " " + base_text) + history
            client_bad.send(full, now)
            reply = " ".join(
                f"a{s}t{t}w{i}" for i in range(rng2.randint(30, 120)))
            history = history + tok2.encode(reply)
            now += rng2.uniform(2.0, 20.0)

    bad_total = client_bad.hits + client_bad.misses
    bad_hit_rate = client_bad.hits / bad_total
    print(f"\n  same workload, timestamp prepended before the system prompt:")
    print(f"  hit rate: {bad_hit_rate:.1%}   "
          f"cost: ${client_bad.cost_with_cache:.4f} "
          f"(vs ${client_bad.cost_without_cache:.4f} uncached: caching now "
          f"LOSES money, every request pays the write premium)")

    # --- behavioral asserts ----------------------------------------------------
    assert hit_rate > 0.8, "stable-prefix chat workload should hit often"
    assert saved > 0, "caching saved money on the stable-prefix workload"
    assert bad_hit_rate == 0.0, "one volatile leading token kills every hit"
    assert client_bad.cost_with_cache > client_bad.cost_without_cache, \
        "with zero hits, the write premium makes caching strictly worse"
    assert client.cost_with_cache < client_bad.cost_with_cache, \
        "prompt ordering alone separates profit from loss"
    print("\n  all asserts passed")


if __name__ == "__main__":
    main()
