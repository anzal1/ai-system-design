# Build a BPE Tokenizer From Scratch

## Problem

Every language model system meters its inputs and outputs in tokens. Billing is per token, rate limits are per token, context windows are per token, and decode latency is roughly one step per output token. Yet most engineers treat the tokenizer as a black box, which makes it impossible to reason about cost, latency, or why a prompt cache stopped hitting.

Byte-pair encoding is the algorithm behind nearly every production tokenizer. It is small enough to build in an afternoon and understanding it pays off every time you look at a bill or a latency trace.

## What You Build

`bpe.py` is a complete byte-level BPE tokenizer in about 200 lines of stdlib Python:

- Pre-tokenization that splits text into word-like pieces, GPT-2 style, with the leading space attached to the word
- A training loop that learns 200 merges from a small inline corpus by repeatedly merging the most frequent adjacent pair
- An encoder that applies merges by training rank and a decoder that maps token ids back to bytes
- A vocab growth table showing compression improving from 1.00 to 3.21 bytes per token as merges accumulate
- A demonstration that `" tokenizer"` and `"tokenizer"` produce entirely different token ids, which is the mechanism behind most prompt-cache misses

## How It Works

Training starts with a vocabulary of 256 tokens, one per byte value. Any byte sequence is representable from step zero, so there is no out-of-vocabulary problem, even for emoji and text in scripts the corpus never contained.

Each training step counts every adjacent token pair across the corpus, picks the most frequent pair, assigns it a new token id, and rewrites the corpus with the merge applied. Ties break deterministically toward the smallest pair so every run produces identical merges. Each merge removes exactly one token per occurrence of the pair, which is why the script can track corpus token count during training without re-encoding, and why the final assert checks that the tracked count matches a fresh encode.

Encoding replays training in miniature: for each pre-token, find the pair with the lowest training rank present in the current token sequence, merge it, and repeat until no learned pair remains. Decoding is trivial by construction, since every token id maps to a fixed byte string and concatenation restores the input exactly.

Pre-tokenization matters more than it looks. Merges never cross the pieces it produces, so `" the"` (with space) and `"the"` (without) are learned as unrelated tokens. This is faithful to production tokenizers and it is the root cause of the boundary effects discussed below.

## Design Decisions

**Byte-level base vocabulary, not characters.** Character-level BPE needs an unknown-token fallback for unseen characters. Byte-level BPE covers all of Unicode with 256 base tokens. The tradeoff is that multi-byte UTF-8 characters start as several tokens, so non-Latin scripts compress worse until merges cover them, which is also true of production tokenizers and is why the same sentence costs more tokens in Hindi than in English.

**Greedy rank-based encoding, not optimal segmentation.** Applying merges in training order is what GPT-2 class tokenizers do. An optimal segmenter could sometimes produce fewer tokens, but encoding must exactly match what training produced or the vocabulary statistics the model learned no longer hold.

**Space attached to the following word.** Attaching whitespace to the next word halves the token count for normal prose compared to emitting spaces as separate tokens. The cost is boundary sensitivity: the first word of a string tokenizes differently from the same word mid-sentence.

**A tiny corpus and 200 merges.** Real tokenizers train on terabytes and learn 50k to 200k merges. The algorithm is identical; only the scale differs. Keeping it small makes the vocab growth table readable and training instant.

## Failure Modes

- **Prompt-cache invalidation from unstable assembly.** Caches match on exact token prefixes. Trimming a trailing space, normalizing a newline, or injecting a timestamp near the front of a prompt changes every token after it and turns cache hits into full-price prefill.
- **Token counts diverging between systems.** Counting tokens with the wrong tokenizer (or estimating by characters divided by four) produces budgets that overflow the context window or leave money on the table. Multilingual text makes the error worse.
- **Truncation mid-token-boundary.** Cutting text by characters and re-encoding can produce a different token sequence than the original prefix, which corrupts few-shot prompts and breaks continuation tasks.
- **Unnormalized Unicode.** Two visually identical strings with different normalization forms (NFC vs NFD) tokenize differently, defeating deduplication, caching, and exact-match evals.
- **Digit and code fragmentation.** Numbers and rare identifiers split into many tokens, so arithmetic-heavy or code-heavy prompts cost more than their character count suggests and models see numbers as arbitrary fragments.

## What Production Systems Do Differently

- Vocabularies of 50k to 200k tokens trained on massive corpora, with regex pre-tokenizers tuned per model family (contractions, digit runs, code punctuation)
- Special tokens for chat structure, tool calls, and document boundaries that are inserted by id, never by encoding their string form, since user text that happens to contain the string must not become the token
- Trie-based or precomputed merge tables so encoding runs in microseconds; this reference implementation is quadratic per word, which is fine at word length but not at scale
- Careful handling of invalid UTF-8 and byte fallback so arbitrary binary-ish input cannot crash the encoder
- Some model families use SentencePiece or Unigram tokenization instead of BPE; the boundary and cost implications are the same

## Run It

```bash
python3 bpe.py
```

Runs in well under a second, prints the first merges, the vocab growth table, round-trip checks, and the boundary sensitivity demo. Inline asserts validate lossless round trips on seen and unseen text, compression above 1.5 bytes per token, and consistency between training bookkeeping and the encoder.

## Exercises

1. Add a `count_tokens(text)` helper and compare token counts for the same paragraph in English and in a language your corpus never saw. Explain the difference in one sentence.
2. Change `NUM_MERGES` to 50, 400, and 1000. Plot (or tabulate) bytes per token against vocabulary size and find where returns diminish for this corpus.
3. Make encoding fast: replace the rank-scan loop in `encode_word` with a priority queue keyed by rank. Verify identical output on the corpus before and after.
4. Simulate a cache-miss incident: build a 500-byte prompt, encode it, then prepend a single character and measure how many token positions survive unchanged. Write the postmortem line you would file.
5. Implement special tokens: reserve ids for `<|system|>` and `<|user|>`, insert them by id during prompt assembly, and add an assert proving that a user string containing the literal text `<|system|>` does not encode to the reserved id.

## Further Reading

- [Neural Machine Translation of Rare Words with Subword Units (Sennrich et al., 2016)](https://arxiv.org/abs/1508.07909), the paper that introduced BPE for NLP; the training loop here is its Algorithm 1.
- [Language Models are Unsupervised Multitask Learners (Radford et al., 2019)](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf), Section 2.2 explains why GPT-2 moved BPE to the byte level and added regex pre-tokenization.
- [tiktoken](https://github.com/openai/tiktoken), a production BPE implementation worth reading to see how the rank-based encoder here becomes fast.
- [Anthropic prompt caching documentation](https://docs.claude.com/en/docs/build-with-claude/prompt-caching), the official statement of exact-prefix matching, which is the production consequence of the boundary demo in this module.
