"""Semantic response caching from scratch.

A prefix cache reuses computation and never changes the answer. A semantic
cache reuses ANSWERS: if a new query looks similar enough to an old one, serve
the old response and skip the model entirely. That makes it the only cache in
this track that can be wrong. Similarity is not equivalence, and the failure
mode is not a slow response, it is a confident incorrect one.

This file builds the whole mechanism with stdlib only:

  - embeddings via hashed character n-grams (the hashing trick)
  - cosine threshold matching over the cached entries
  - staleness windows (age limits per entry)
  - a correctness-risk gate: rule-based detection of time-sensitive and
    user-specific queries that must never be served from cache

and then demonstrates the failure case: a poisoned cache serving the wrong
answer when the threshold is set greedily.

Pure stdlib. Deterministic. Simulated time. Run: python3 semantic_cache.py
"""

import hashlib
import math
import re

# ---------------------------------------------------------------------------
# Embeddings: hashed character n-grams. Each 3..5-gram of the normalized text
# is hashed into one of DIM buckets (the hashing trick), the vector is then
# L2-normalized. No vocabulary, no training, no numpy. Crude, but it captures
# surface similarity well enough to expose every property that matters for a
# cache: paraphrases land close, unrelated queries land far, and, crucially,
# some non-equivalent queries also land close. That last property is the bug.
# ---------------------------------------------------------------------------

DIM = 256


def normalize(text):
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def embed(text):
    text = " " + normalize(text) + " "
    vec = [0.0] * DIM
    for n in (3, 4, 5):
        for i in range(len(text) - n + 1):
            gram = text[i:i + n]
            h = hashlib.md5(gram.encode()).digest()
            bucket = int.from_bytes(h[:4], "big") % DIM
            sign = 1.0 if h[4] % 2 == 0 else -1.0  # signed hashing trick
            vec[bucket] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# Correctness-risk gate. Rule-based and deliberately conservative: any query
# that mentions time, freshness, or the requesting user must go to the model.
# A cached answer to "what is MY current balance" is wrong for almost every
# user who could hit it. This gate runs BEFORE lookup and before store, so
# risky answers are never even written.
# ---------------------------------------------------------------------------

TIME_SENSITIVE = re.compile(
    r"\b(today|tonight|tomorrow|yesterday|now|current(ly)?|latest|recent|"
    r"this (week|month|year)|weather|news|stock|price of|score|schedule)\b")
# Note the precision trade-off: bare "my" would also flag generic FAQ text
# like "reset my password", so the rules name the possessives that actually
# bind an answer to one user's state. Rule gates buy predictability at the
# price of recall; anything the rules miss goes to the cache.
USER_SPECIFIC = re.compile(
    r"\bmy (account|orders?|balance|subscription|invoices?|bill|plan|"
    r"packages?|delivery|refund)\b|\border\s*#?\d+\b|\bi am\b|\bi'm\b")


def risk_flags(query):
    q = normalize(query)
    flags = []
    if TIME_SENSITIVE.search(q):
        flags.append("time-sensitive")
    if USER_SPECIFIC.search(q):
        flags.append("user-specific")
    return flags


# ---------------------------------------------------------------------------
# The cache. Linear scan over entries: fine at this scale, and honest about
# what a real system replaces with an ANN index, not with different logic.
# ---------------------------------------------------------------------------

class SemanticCache:
    def __init__(self, threshold=0.88, staleness_window=3600.0):
        self.threshold = threshold
        self.staleness = staleness_window
        self.entries = []  # (vector, query, response, stored_at)
        self.stats = {"hit": 0, "miss": 0, "near_miss": 0,
                      "gated": 0, "expired": 0}

    def get(self, query, now):
        """Returns (response or None, reason)."""
        if risk_flags(query):
            self.stats["gated"] += 1
            return None, "gated:" + ",".join(risk_flags(query))
        v = embed(query)
        best_sim, best = -1.0, None
        for entry in self.entries:
            sim = cosine(v, entry[0])
            if sim > best_sim:
                best_sim, best = sim, entry
        if best is None:
            self.stats["miss"] += 1
            return None, "miss:empty"
        if best_sim < self.threshold:
            # Near miss: similar but not similar enough. This bucket is where
            # correctness lives; a greedy threshold moves these into hits.
            if best_sim >= self.threshold - 0.15:
                self.stats["near_miss"] += 1
                return None, f"near_miss:{best_sim:.3f}"
            self.stats["miss"] += 1
            return None, f"miss:{best_sim:.3f}"
        if now - best[3] > self.staleness:
            self.stats["expired"] += 1
            return None, f"expired:age={now - best[3]:.0f}s"
        self.stats["hit"] += 1
        return best[2], f"hit:{best_sim:.3f}"

    def put(self, query, response, now):
        if risk_flags(query):
            return False  # risky answers are never cached in the first place
        self.entries.append((embed(query), query, response, now))
        return True


# ---------------------------------------------------------------------------
# Demo scenarios.
# ---------------------------------------------------------------------------

MODEL_COST = 0.01  # USD per model call, flat for the demo


def scenario_true_hits(cache):
    """Paraphrases of a cached FAQ answer should hit."""
    now = 0.0
    cache.put("how do I reset my password on the web app",
              "Go to Settings, then Security, then Reset Password.", now)
    cache.put("how do I upgrade my workspace from the free plan to the team plan",
              "Open Billing and choose Team under Change Plan.", now)
    paraphrases = [
        "how do i reset my password in the web app",
        "how do I reset my password on the web application",
        "how do I upgrade a workspace from the free plan to the team plan",
        "how can I upgrade my workspace from the free plan to the team plan",
    ]
    results = []
    for q in paraphrases:
        resp, reason = cache.get(q, now + 10)
        results.append((q, resp is not None, reason))
    return results


def scenario_near_miss(cache):
    """Similar surface, different meaning: must NOT hit."""
    now = 100.0
    cache.put("how do I disable notifications for mentions",
              "Settings, then Notifications, then turn off Mentions.", now)
    # One word apart, cosine 0.861 with these embeddings, and the cached
    # answer is the wrong instruction for this question.
    q = "how do I disable notifications for messages"
    resp, reason = cache.get(q, now + 10)
    return q, resp, reason


def scenario_risk_gate(cache):
    qs = [
        "what is the weather today in berlin",
        "what is my account balance",
        "latest news on the merger",
        "where is my order #48211",
    ]
    results = []
    for q in qs:
        resp, reason = cache.get(q, 200.0)
        stored = cache.put(q, "SHOULD NEVER BE CACHED", 200.0)
        results.append((q, resp, reason, stored))
    return results


def scenario_staleness(cache):
    now = 1000.0
    cache.put("what is the standard shipping time",
              "Standard shipping takes 3 to 5 business days.", now)
    fresh, r1 = cache.get("what is the standard shipping time", now + 100)
    stale, r2 = cache.get("what is the standard shipping time",
                          now + cache.staleness + 1)
    return fresh, r1, stale, r2


def scenario_poisoned(threshold):
    """The failure case. Two different questions with heavy n-gram overlap.

    At a greedy threshold the second query hits the first answer, and the
    user asking about the pro plan is told the price of the basic plan. The
    cache did exactly what it was configured to do. That is the point: the
    bug is the configuration, and nothing in the mechanism can catch it.
    """
    cache = SemanticCache(threshold=threshold)
    now = 0.0
    cache.put("what is the token limit on the basic plan",
              "The basic plan includes 500,000 tokens per month.", now)
    q = "what is the token limit on the pro plan"
    resp, reason = cache.get(q, now + 5)
    return q, resp, reason


def main():
    # --- unit checks: embedding behaves like a similarity measure ------------
    a = embed("how do I reset my password")
    b = embed("how can I reset my password")
    c = embed("recommend a good pasta recipe")
    assert cosine(a, a) > 0.999, "self-similarity is 1"
    assert cosine(a, b) > cosine(a, c), "paraphrase beats unrelated"
    assert cosine(a, c) < 0.5, "unrelated queries land far apart"

    # --- unit checks: risk gate -----------------------------------------------
    assert risk_flags("what is my account balance") == ["user-specific"]
    assert "time-sensitive" in risk_flags("weather today in berlin")
    assert risk_flags("how do I reset my password") == []

    print("SEMANTIC CACHE DEMO")
    cache = SemanticCache(threshold=0.88, staleness_window=3600.0)

    # 1. True hits
    print("\n  1. true hits (paraphrases of cached FAQ answers):")
    hits = scenario_true_hits(cache)
    for q, hit, reason in hits:
        print(f"     [{reason:<12}] {q}")
    assert all(h for _, h, _ in hits), "paraphrases should hit at 0.88"

    # 2. Near-miss rejection
    print("\n  2. near-miss rejection (similar words, different meaning):")
    q, resp, reason = scenario_near_miss(cache)
    print(f"     [{reason:<12}] {q}")
    print(f"     served: {resp!r}  (a hit would hand the MENTIONS answer "
          f"to a user asking about MESSAGES)")
    assert resp is None, "the near miss must not be served"

    # 3. Correctness-risk gate
    print("\n  3. correctness-risk gate (never served, never stored):")
    for q, resp, reason, stored in scenario_risk_gate(cache):
        print(f"     [{reason:<22}] stored={stored!s:<5} {q}")
        assert resp is None and not stored

    # 4. Staleness window
    fresh, r1, stale, r2 = scenario_staleness(cache)
    print("\n  4. staleness window (same query, one hour later):")
    print(f"     [{r1}] fresh lookup served: {fresh is not None}")
    print(f"     [{r2}] stale lookup served: {stale is not None}")
    assert fresh is not None and stale is None

    # 5. The poisoned cache
    print("\n  5. poisoned cache (threshold set greedily at 0.75):")
    q, resp, reason = scenario_poisoned(threshold=0.75)
    print(f"     [{reason:<12}] {q}")
    print(f"     served: {resp!r}")
    print("     WRONG. The user asked about the pro plan. Every similarity")
    print("     mechanism has query pairs above threshold that need different")
    print("     answers. Lowering the threshold manufactures more of them.")
    assert resp is not None and "basic plan" in resp, \
        "the greedy threshold serves the wrong plan's limit"
    q2, resp2, reason2 = scenario_poisoned(threshold=0.88)
    print(f"     [{reason2:<12}] same pair at threshold 0.88: served={resp2 is not None}")
    assert resp2 is None, "the conservative threshold refuses the same pair"

    # --- economics ------------------------------------------------------------
    s = cache.stats
    lookups = sum(s.values())
    saved = s["hit"] * MODEL_COST
    print(f"\n  stats over {lookups} lookups: {s}")
    print(f"  model calls avoided: {s['hit']}  (${saved:.2f} saved at "
          f"${MODEL_COST:.2f}/call)")
    print(f"  lookups the gate sent to the model regardless of similarity: "
          f"{s['gated']}")
    assert s["hit"] == 5 and s["gated"] == 4 and s["near_miss"] >= 1

    print("\n  all asserts passed")


if __name__ == "__main__":
    main()
