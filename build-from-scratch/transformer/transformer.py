"""A tiny transformer forward pass in pure Python.

One transformer block, single-head causal attention, lists of floats, no
numpy. Weights are fixed by a seeded RNG so every run is identical. The goal
is to make the mechanics legible: what attention actually computes, and why
its cost grows with the square of the sequence length.

Run: python3 transformer.py
"""

import math
import random

# ---------------------------------------------------------------------------
# Configuration. Deliberately tiny so intermediate values are printable.
# ---------------------------------------------------------------------------

VOCAB = ["<bos>", "the", "cat", "sat", "on", "mat", "ran", "."]
D_MODEL = 8    # embedding width
D_FF = 16      # MLP hidden width
MAX_LEN = 16   # positional embedding table size

random.seed(5)

# Operation counters. Every dot product reports its length so we can measure
# where multiply-accumulate work goes without instrumenting inner loops.
OPS = {"attn": 0, "other": 0}


def dot(a, b, bucket="other"):
    assert len(a) == len(b)
    OPS[bucket] += len(a)
    return sum(x * y for x, y in zip(a, b))


def matvec(mat, vec, bucket="other"):
    """mat is a list of rows; returns mat[r] . vec for each output r."""
    return [dot(row, vec, bucket) for row in mat]


def rand_matrix(rows, cols, scale=0.4):
    return [[random.uniform(-scale, scale) for _ in range(cols)] for _ in range(rows)]


# ---------------------------------------------------------------------------
# Fixed weights. In a real model these come from training. Here they are just
# deterministic numbers, because the lesson is the wiring, not the knowledge.
# ---------------------------------------------------------------------------

W_EMB = rand_matrix(len(VOCAB), D_MODEL)   # token embeddings
W_POS = rand_matrix(MAX_LEN, D_MODEL)      # positional embeddings
W_Q = rand_matrix(D_MODEL, D_MODEL)
W_K = rand_matrix(D_MODEL, D_MODEL)
W_V = rand_matrix(D_MODEL, D_MODEL)
W_O = rand_matrix(D_MODEL, D_MODEL)
W_FF1 = rand_matrix(D_FF, D_MODEL)
B_FF1 = [random.uniform(-0.1, 0.1) for _ in range(D_FF)]
W_FF2 = rand_matrix(D_MODEL, D_FF)
B_FF2 = [random.uniform(-0.1, 0.1) for _ in range(D_MODEL)]
# The unembedding reuses W_EMB (weight tying), a common production choice.


# ---------------------------------------------------------------------------
# Building blocks.
# ---------------------------------------------------------------------------

def layernorm(vec, eps=1e-5):
    mean = sum(vec) / len(vec)
    var = sum((x - mean) ** 2 for x in vec) / len(vec)
    return [(x - mean) / math.sqrt(var + eps) for x in vec]


def softmax(scores):
    peak = max(scores)  # subtract the max so exp never overflows
    exps = [math.exp(s - peak) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def relu(vec):
    return [x if x > 0 else 0.0 for x in vec]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def attention(xs):
    """Single-head causal self-attention over the whole sequence.

    For every position i:
      q_i attends to k_0..k_i, never to the future.
      Output i is a probability-weighted average of v_0..v_i.
    Returns (outputs, attention_matrix).
    """
    n = len(xs)
    qs = [matvec(W_Q, x, "attn") for x in xs]
    ks = [matvec(W_K, x, "attn") for x in xs]
    vs = [matvec(W_V, x, "attn") for x in xs]

    outputs = []
    attn_matrix = []
    scale = 1.0 / math.sqrt(D_MODEL)
    for i in range(n):
        # n scores at position n-1, so scoring alone is 1+2+...+n = O(n^2).
        scores = [dot(qs[i], ks[j], "attn") * scale for j in range(i + 1)]
        weights = softmax(scores)
        attn_matrix.append(weights + [0.0] * (n - i - 1))  # causal: future is zero
        mixed = [0.0] * D_MODEL
        for j, w in enumerate(weights):
            for d in range(D_MODEL):
                mixed[d] += w * vs[j][d]
        OPS["attn"] += (i + 1) * D_MODEL
        outputs.append(matvec(W_O, mixed, "attn"))
    return outputs, attn_matrix


def mlp(x):
    hidden = relu(add(matvec(W_FF1, x), B_FF1))
    return add(matvec(W_FF2, hidden), B_FF2)


def forward(token_ids):
    """Full forward pass. Returns (logits_per_position, attention_matrix)."""
    assert len(token_ids) <= MAX_LEN
    xs = [add(W_EMB[t], W_POS[pos]) for pos, t in enumerate(token_ids)]

    # Pre-norm transformer block: x + Attn(LN(x)), then x + MLP(LN(x)).
    attn_out, attn_matrix = attention([layernorm(x) for x in xs])
    xs = [add(x, a) for x, a in zip(xs, attn_out)]
    xs = [add(x, mlp(layernorm(x))) for x in xs]

    logits = [[dot(layernorm(x), emb) for emb in W_EMB] for x in xs]
    return logits, attn_matrix


def greedy_decode(prompt_ids, num_new):
    """Re-run the full forward pass per new token. Every step recomputes
    attention for the whole sequence, which is exactly the waste a KV cache
    removes (see the kv-cache module)."""
    ids = list(prompt_ids)
    for _ in range(num_new):
        logits, _ = forward(ids)
        last = logits[-1]
        ids.append(max(range(len(VOCAB)), key=lambda t: last[t]))
    return ids


# ---------------------------------------------------------------------------
# Demo.
# ---------------------------------------------------------------------------

def main():
    print("=== Tiny transformer forward pass ===\n")
    print(f"vocab={VOCAB}")
    print(f"d_model={D_MODEL}, d_ff={D_FF}, 1 block, 1 head, weights seeded\n")

    prompt = ["<bos>", "the", "cat"]
    prompt_ids = [VOCAB.index(t) for t in prompt]
    logits, attn = forward(prompt_ids)

    print(f"Causal attention weights for prompt {prompt}:")
    print("  each row is a query position, each column a key position")
    for i, row in enumerate(attn):
        cells = " ".join(f"{w:5.2f}" for w in row)
        print(f"  {prompt[i]:>6} | {cells}")

    print("\nLogits at the last position (next-token scores):")
    last = logits[-1]
    for tok, score in sorted(zip(VOCAB, last), key=lambda p: -p[1]):
        print(f"  {tok:>6} {score:8.3f}")

    generated = greedy_decode(prompt_ids, 5)
    text = " ".join(VOCAB[i] for i in generated)
    print(f"\nGreedy decode, 5 new tokens: {text}")

    # ------------------------------------------------------------------
    # Correctness asserts.
    # ------------------------------------------------------------------
    for row in attn:
        live = [w for w in row if w > 0]
        assert abs(sum(live) - 1.0) < 1e-9, "attention rows must sum to 1"
    for i, row in enumerate(attn):
        assert all(w == 0.0 for w in row[i + 1:]), "causal mask leaked the future"

    normed = layernorm([3.0, -1.0, 4.0, 1.0, -5.0, 9.0, 2.0, -6.0])
    assert abs(sum(normed)) < 1e-9, "layernorm output must have zero mean"
    var = sum(x * x for x in normed) / len(normed)
    assert abs(var - 1.0) < 1e-3, "layernorm output must have unit variance"

    assert abs(sum(softmax([1.0, 2.0, 3.0])) - 1.0) < 1e-12
    assert softmax([1000.0, 1000.0]) == [0.5, 0.5], "softmax must not overflow"

    logits2, _ = forward(prompt_ids)
    assert logits == logits2, "forward pass must be deterministic"
    assert greedy_decode(prompt_ids, 5) == generated, "decode must be deterministic"
    assert len(last) == len(VOCAB)

    # ------------------------------------------------------------------
    # Cost measurement: attention multiply-accumulates vs sequence length.
    # QKV projections grow linearly with n. Scores and value mixing grow with
    # n^2. At small n the linear projections dominate; the quadratic term
    # takes over as context grows.
    # ------------------------------------------------------------------
    print("\nMultiply-accumulate ops in attention for one forward pass:")
    print(f"  {'seq len':>7} {'attn MACs':>10} {'growth':>7}")
    measured = []
    for n in [2, 4, 8, 16]:
        OPS["attn"] = OPS["other"] = 0
        forward([i % len(VOCAB) for i in range(n)])
        measured.append(OPS["attn"])
        ratio = f"{measured[-1] / measured[-2]:6.2f}x" if len(measured) > 1 else "      -"
        print(f"  {n:>7} {measured[-1]:>10} {ratio}")

    # Exact cost model: 4n D^2 for Q,K,V,O projections plus n(n+1)(D+D) for
    # scores and value mixing. The measured counts must match it.
    for n, got in zip([2, 4, 8, 16], measured):
        expected = 4 * n * D_MODEL ** 2 + n * (n + 1) * D_MODEL
        assert got == expected, f"cost model mismatch at n={n}: {got} != {expected}"
    # Growth must exceed 2x per doubling: the quadratic term is real.
    for a, b in zip(measured, measured[1:]):
        assert b > 2 * a, "attention cost should grow faster than linear"

    print("\n  Cost model: 4nD^2 (projections, linear in n)")
    print("            + n(n+1)D  (scores + value mixing, quadratic in n)")
    print("  Doubling the sequence more than doubles the work. This is the")
    print("  O(n^2) that makes long contexts expensive and prefill compute")
    print("  bound, while decode repeats a cheap step once per output token.")

    print("\nAll asserts passed.")


if __name__ == "__main__":
    main()
