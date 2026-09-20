"""KV-cache simulator.

Runs single-head attention decode two ways: recomputing keys and values for
the whole sequence at every step, and reusing a KV cache. Both paths produce
bit-identical outputs. The difference is the multiply-accumulate count, which
this script measures directly, not estimates.

Pure Python 3 stdlib, deterministic, no network.

Run: python3 kv_cache.py
"""

import random

D = 32          # model width
STEPS = 48      # tokens to decode
random.seed(3)

MACS = 0  # global multiply-accumulate counter


def dot(a, b):
    global MACS
    MACS += len(a)
    return sum(x * y for x, y in zip(a, b))


def matvec(mat, vec):
    return [dot(row, vec) for row in mat]


def rand_matrix(rows, cols):
    return [[random.uniform(-0.2, 0.2) for _ in range(cols)] for _ in range(rows)]


W_Q = rand_matrix(D, D)
W_K = rand_matrix(D, D)
W_V = rand_matrix(D, D)

# The token stream: one fixed embedding per position, generated once so both
# decode paths consume identical inputs.
EMBEDDINGS = [[random.uniform(-1, 1) for _ in range(D)] for _ in range(STEPS)]


def attend(q, ks, vs):
    """Raw causal attention for one query: scores against every cached key,
    then a score-weighted sum of values. Softmax is skipped because it adds
    no multiplies that change the asymptotics, only exp and divide."""
    scores = [dot(q, k) for k in ks]              # t dot products of length D
    out = [0.0] * D
    for s, v in zip(scores, vs):
        for d in range(D):
            out[d] += s * v[d]
    global MACS
    MACS += len(vs) * D                            # count the weighted sum
    return out


def decode_no_cache(steps):
    """At every step, recompute K and V for the entire sequence so far.

    This is what running a stateless forward pass per token costs. Serving
    without a KV cache really does this.
    """
    outputs, per_step = [], []
    global MACS
    for t in range(1, steps + 1):
        before = MACS
        ks = [matvec(W_K, EMBEDDINGS[i]) for i in range(t)]   # t recomputed
        vs = [matvec(W_V, EMBEDDINGS[i]) for i in range(t)]   # t recomputed
        q = matvec(W_Q, EMBEDDINGS[t - 1])
        outputs.append(attend(q, ks, vs))
        per_step.append(MACS - before)
    return outputs, per_step


def decode_with_cache(steps):
    """Compute K and V once per token and append them to the cache."""
    outputs, per_step = [], []
    k_cache, v_cache = [], []
    global MACS
    for t in range(1, steps + 1):
        before = MACS
        k_cache.append(matvec(W_K, EMBEDDINGS[t - 1]))        # 1 new key
        v_cache.append(matvec(W_V, EMBEDDINGS[t - 1]))        # 1 new value
        q = matvec(W_Q, EMBEDDINGS[t - 1])
        outputs.append(attend(q, k_cache, v_cache))
        per_step.append(MACS - before)
    return outputs, per_step


def main():
    print("=== KV-cache simulator ===\n")
    print(f"d_model={D}, single head, {STEPS} decode steps, "
          f"MACs counted inside every dot product\n")

    out_no_cache, macs_no_cache = decode_no_cache(STEPS)
    out_cache, macs_cache = decode_with_cache(STEPS)

    # The cache is an optimization, not an approximation: identical floats.
    assert out_no_cache == out_cache, "cache changed the math"

    # Measured cost must match the closed-form model exactly.
    # no cache: (2t+1) projections of D^2 each, plus 2tD for attention
    # cache:    3 projections of D^2, plus 2tD for attention
    for t in range(1, STEPS + 1):
        assert macs_no_cache[t - 1] == (2 * t + 1) * D * D + 2 * t * D
        assert macs_cache[t - 1] == 3 * D * D + 2 * t * D

    print("MACs per decoded token:")
    print(f"  {'token':>5} {'no cache':>10} {'with cache':>10} {'ratio':>7}")
    for t in [1, 2, 4, 8, 16, 32, 48]:
        a, b = macs_no_cache[t - 1], macs_cache[t - 1]
        print(f"  {t:>5} {a:>10} {b:>10} {a / b:>6.1f}x")

    cum_a = cum_b = 0
    cum_no_cache, cum_cache = [], []
    for a, b in zip(macs_no_cache, macs_cache):
        cum_a += a
        cum_b += b
        cum_no_cache.append(cum_a)
        cum_cache.append(cum_b)

    print("\nCumulative MACs to decode n tokens:")
    print(f"  {'n':>5} {'no cache':>10} {'with cache':>10} {'ratio':>7}")
    for t in [1, 2, 4, 8, 16, 32, 48]:
        a, b = cum_no_cache[t - 1], cum_cache[t - 1]
        print(f"  {t:>5} {a:>10} {b:>10} {a / b:>6.1f}x")

    # Growth-shape asserts: quadratic without cache, near linear with it.
    # Doubling n should roughly 4x the uncached total and roughly 2x the
    # cached total. Projection-vs-attention mix keeps it from being exact,
    # so bound it instead of pinning it.
    r_no = cum_no_cache[31] / cum_no_cache[15]   # n=32 vs n=16
    r_yes = cum_cache[31] / cum_cache[15]
    assert 3.0 < r_no < 4.5, f"uncached growth not quadratic: {r_no:.2f}"
    assert 1.8 < r_yes < 2.6, f"cached growth not near linear: {r_yes:.2f}"

    print(f"\n  Doubling n=16 -> n=32 multiplies total cost by "
          f"{r_no:.1f}x uncached, {r_yes:.1f}x cached.")
    print("  Without the cache, every step re-derives K and V for the whole")
    print("  history: per-token cost grows linearly, total cost quadratically.")
    print("  With the cache, per-token cost is one projection set plus one")
    print("  attention row, so the total grows almost linearly.")

    # ------------------------------------------------------------------
    # The same idea one level up: prompt caching. A conversation replays its
    # entire history every turn. Prefix reuse skips prefill work for tokens
    # whose K and V are already stored, exactly like the per-token cache
    # above but across requests.
    # ------------------------------------------------------------------
    def prefill_macs(new_tokens, existing):
        """Projections for new tokens plus attention of new against all."""
        total = 0
        for i in range(new_tokens):
            t = existing + i + 1
            total += 3 * D * D + 2 * t * D
        return total

    system_prompt = 200
    turn_tokens = 40
    turns = 5

    fresh = 0
    reused = 0
    history = 0
    print(f"\nPrompt caching: {system_prompt}-token system prompt, "
          f"{turns} turns of {turn_tokens} tokens each")
    print(f"  {'turn':>5} {'fresh prefill':>14} {'prefix reuse':>13}")
    for turn in range(1, turns + 1):
        full = system_prompt + turn * turn_tokens
        cost_fresh = prefill_macs(full, 0)              # re-prefill everything
        cost_reuse = prefill_macs(full - history, history)  # only the delta
        fresh += cost_fresh
        reused += cost_reuse
        history = full
        print(f"  {turn:>5} {cost_fresh:>14} {cost_reuse:>13}")
    print(f"  {'sum':>5} {fresh:>14} {reused:>13}  ({fresh / reused:.1f}x saved)")

    assert reused < fresh, "prefix reuse must cost less than fresh prefill"
    # With reuse, every token is prefilled exactly once, so the total equals
    # one fresh prefill of the final conversation.
    assert reused == prefill_macs(system_prompt + turns * turn_tokens, 0)

    print("\n  Without prefix reuse, turn n pays to re-prefill the whole")
    print("  conversation. Total prefill grows quadratically in turns, which")
    print("  is why long chats get slow and expensive. With reuse, each token")
    print("  is prefilled once, ever, as long as the prefix stays byte-identical.")

    print("\nAll asserts passed.")


if __name__ == "__main__":
    main()
