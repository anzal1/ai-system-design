# Build a Tiny Transformer From Scratch

## Problem

Most engineers operating LLM systems have never traced a single token through a transformer. That gap shows up in production reasoning: why doubling context more than doubles prefill cost, why time-to-first-token and time-per-output-token behave differently, why long-context pricing is tiered. All of these fall out of about 150 lines of arithmetic, and once you have written that arithmetic yourself the cost model stops being folklore.

## What You Build

`transformer.py` is one complete transformer block in pure Python, lists of floats, no numpy:

- Token plus positional embedding lookup over an 8-word toy vocabulary
- Single-head scaled dot-product attention with a causal mask, printed as a readable weight matrix
- A two-layer ReLU MLP, pre-norm residual wiring, and layernorm
- Logits via weight-tied unembedding and greedy decoding of 5 tokens
- A multiply-accumulate counter inside every dot product, producing a measured cost table for sequence lengths 2 to 16 that is asserted against the closed-form model `4nD^2 + n(n+1)D`

Weights are fixed by `random.seed(5)`, so the model is untrained and its output is arbitrary, but every run is identical and every intermediate value can be printed and inspected.

## How It Works

Each input token becomes a vector: its embedding row plus a positional embedding row. Attention then lets each position build a weighted average of every earlier position. For position i, a query vector is compared against the keys of positions 0 through i by dot product, scaled by 1 divided by sqrt(d) so score magnitude does not grow with width, and passed through softmax to get weights that sum to 1. Those weights mix the value vectors. The printed matrix makes the causal mask visible: everything above the diagonal is zero because a token may not read the future.

The MLP then transforms each position independently. Residual connections add each sublayer's output back to its input, and layernorm keeps activations in a stable range. Logits are dot products between the final hidden state and each embedding row; greedy decode takes the argmax, appends it, and runs the whole forward pass again.

The cost table is the point. Q, K, V, and output projections cost `4nD^2`, linear in sequence length. Score computation and value mixing cost `n(n+1)D`, quadratic, because position i does i+1 comparisons. At tiny n the linear term dominates, which the table shows honestly: growth per doubling is 2.11x, then 2.22x, then 2.39x, trending toward 4x as the quadratic term takes over. In production models with contexts of 100k+ tokens, the quadratic term is the bill.

## Design Decisions

**Pure Python lists, no numpy.** Every multiply is visible and countable, and the module runs anywhere. The tradeoff is speed: this code is thousands of times slower per operation than a BLAS call, which is fine at d_model 8 and fatal at d_model 8192. The gap itself is instructive, since production inference is dominated by how well these exact loops map onto matrix hardware.

**Untrained random weights.** Training even a toy model would triple the code and bury the forward pass. The output sequence is meaningless, and honestly so. The asserts therefore check structural properties (softmax rows sum to 1, the causal mask holds, layernorm has zero mean and unit variance, determinism holds) rather than output quality.

**Single head, single block, pre-norm.** Multi-head attention is h copies of this head on slices of the vector, and depth is this block repeated. Neither changes the shape of the cost model, so both are left as exercises. Pre-norm is used because it is what modern models ship.

**Weight-tied unembedding.** Reusing the embedding matrix for logits saves a parameter matrix and matches common practice (GPT-2 and many descendants). The tradeoff, irrelevant at this scale, is a mild constraint coupling input and output spaces.

**Greedy decode that reruns the full forward pass.** This is deliberately wasteful: every new token recomputes attention for the entire sequence. It makes the redundancy the KV cache removes concrete. The kv-cache module in this track measures exactly what that waste costs.

## Failure Modes

- **Softmax overflow.** Naive `exp(score)` overflows for large scores. The implementation subtracts the row max first, and an assert feeds it scores of 1000 to prove it. Real serving stacks hit this with long contexts and low-precision arithmetic.
- **Causal mask bugs.** If any weight above the diagonal is nonzero, the model reads the future, training metrics look great, and generation is garbage. The assert here checks the mask on every row.
- **Scale factor omitted.** Dropping the 1/sqrt(d) scaling pushes softmax into saturation, where attention becomes a hard argmax and gradients vanish. Easy to miss because the code still runs.
- **Position table exhaustion.** Learned positional embeddings hard-cap sequence length at MAX_LEN; an input one token longer is an index error here and silent quality collapse in systems that extrapolate poorly.
- **Nondeterminism assumed away.** This module asserts bit-identical repeated forwards. Production GPU inference does not guarantee that, since parallel reduction order varies, which matters for caching, evals, and debugging.

## What Production Systems Do Differently

- Dozens of blocks, dozens of heads, d_model in the thousands, and grouped-query or multi-query attention to shrink the KV footprint
- Rotary or other relative position encodings instead of a learned absolute table, which is much of why long-context extrapolation works at all
- FlashAttention-style kernels that keep the O(n^2) arithmetic but never materialize the n by n matrix, making attention memory-linear
- Prefill and decode treated as different workloads: prefill processes the whole prompt in parallel and is compute bound, decode emits one token at a time and is memory-bandwidth bound. This is why time-to-first-token scales with prompt length while time-per-output-token is roughly flat, and why serving stacks batch and schedule the two phases separately.
- Sampling with temperature, top-p, and penalties instead of pure greedy argmax, plus speculative decoding to amortize the per-token cost

## Run It

```bash
python3 transformer.py
```

Runs in under a second. Prints the causal attention matrix for a 3-token prompt, ranked next-token logits, a greedy 5-token continuation, and the measured attention MAC table. Inline asserts validate softmax, the causal mask, layernorm statistics, determinism, and the exact cost model.

## Exercises

1. Print the attention matrix for the full 8-token generated sequence and identify which earlier token each new token attends to most.
2. Remove the 1/sqrt(d) scaling and rerun. Compare the attention matrices and explain the change in one sentence.
3. Extend the cost table to n = 32, 64, 128 (raise MAX_LEN) and find the sequence length where the quadratic term overtakes the projections for this D_MODEL. Derive the crossover formula and check it.
4. Implement multi-head attention: split the 8-dim space into 2 heads of 4, run attention per head, concatenate, and keep every existing assert passing.
5. Add a KV cache to `greedy_decode` so each step computes K and V only for the new token, and assert the generated sequence is unchanged. Then compare your MAC counts with the kv-cache module's.

## Further Reading

- [Attention Is All You Need (Vaswani et al., 2017)](https://arxiv.org/abs/1706.03762), the original architecture; Section 3.2 defines exactly the scaled dot-product attention implemented here.
- [Efficiently Scaling Transformer Inference (Pope et al., 2022)](https://arxiv.org/abs/2211.05102), the clearest published treatment of why prefill is compute bound and decode is memory bound, with the arithmetic to prove it.
- [nanoGPT](https://github.com/karpathy/nanoGPT), the smallest serious trained implementation; diff it against this module to see what training adds.
- [FlashAttention (Dao et al., 2022)](https://arxiv.org/abs/2205.14135), how production kernels keep O(n^2) compute while cutting memory traffic, which reframes where the real cost lives.
