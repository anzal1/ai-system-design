"""Byte-pair encoding from scratch.

Trains a byte-level BPE tokenizer on a small inline corpus, then encodes and
decodes text with it. Pure Python 3 stdlib, deterministic, no network.

Run: python3 bpe.py
"""

import re

# ---------------------------------------------------------------------------
# Corpus. Small on purpose so training is visible, with repeated vocabulary so
# merges have something to find.
# ---------------------------------------------------------------------------

CORPUS = """\
The tokenizer is the front door of every language model system.
Every request is billed in tokens, rate limited in tokens, and truncated in tokens.
The model never sees characters. The model sees token ids.
A tokenizer maps bytes to token ids and token ids back to bytes.
Byte pair encoding builds a vocabulary by merging the most frequent pair of
adjacent tokens, over and over, until the vocabulary reaches a target size.
Frequent words become single tokens. Rare words split into many tokens.
The tokenizer decides the cost of a prompt before the model runs at all.
The tokenizer decides the latency of a response, because decoding emits one
token at a time, and a response that needs more tokens takes more steps.
Prompt caching matches on exact token prefixes. Change one byte near the
front of a prompt and every cached token after it is invalidated.
The same text can tokenize differently depending on what precedes it, so
prompt assembly must be byte stable if the cache is going to hit.
"""

NUM_MERGES = 200
BASE_VOCAB = 256  # one token id per byte value

# ---------------------------------------------------------------------------
# Pre-tokenization. Real BPE tokenizers (GPT-2 and descendants) split text
# into word-like pieces first so merges never cross a word boundary. The
# leading space stays attached to the word, which is why " hello" and "hello"
# are different tokens in production tokenizers.
# ---------------------------------------------------------------------------

PRE_TOKEN = re.compile(r" ?[A-Za-z]+| ?[0-9]+| ?[^A-Za-z0-9\s]+|\s+")


def pre_tokenize(text):
    parts = PRE_TOKEN.findall(text)
    assert "".join(parts) == text, "pre-tokenization must be lossless"
    return parts


# ---------------------------------------------------------------------------
# Training.
# ---------------------------------------------------------------------------

def count_words(text):
    """Map each pre-token, as a tuple of byte values, to its corpus count."""
    counts = {}
    for part in pre_tokenize(text):
        word = tuple(part.encode("utf-8"))
        counts[word] = counts.get(word, 0) + 1
    return counts


def pair_stats(word_counts):
    stats = {}
    for word, count in word_counts.items():
        for pair in zip(word, word[1:]):
            stats[pair] = stats.get(pair, 0) + count
    return stats


def merge_word(word, pair, new_id):
    out = []
    i = 0
    while i < len(word):
        if i + 1 < len(word) and (word[i], word[i + 1]) == pair:
            out.append(new_id)
            i += 2
        else:
            out.append(word[i])
            i += 1
    return tuple(out)


def train(text, num_merges):
    """Return (merges, vocab, history).

    merges: list of ((left_id, right_id), new_id) in training order
    vocab:  token id -> bytes
    history: (merge_count, vocab_size, corpus_token_count) checkpoints
    """
    word_counts = count_words(text)
    vocab = {i: bytes([i]) for i in range(BASE_VOCAB)}
    merges = []
    total_tokens = sum(len(w) * c for w, c in word_counts.items())
    history = [(0, BASE_VOCAB, total_tokens)]

    for step in range(num_merges):
        stats = pair_stats(word_counts)
        if not stats:
            break
        # Deterministic choice: highest count, ties broken by smallest pair.
        best = max(stats, key=lambda p: (stats[p], -p[0], -p[1]))
        new_id = BASE_VOCAB + step
        merges.append((best, new_id))
        vocab[new_id] = vocab[best[0]] + vocab[best[1]]
        word_counts = {merge_word(w, best, new_id): c for w, c in word_counts.items()}
        total_tokens -= stats[best]  # each merge removes one token per occurrence
        if (step + 1) % 25 == 0:
            history.append((step + 1, BASE_VOCAB + step + 1, total_tokens))
    return merges, vocab, history


# ---------------------------------------------------------------------------
# Encoding and decoding.
# ---------------------------------------------------------------------------

def encode_word(word_bytes, ranks, pair_to_id):
    """Apply learned merges to one pre-token, lowest training rank first."""
    ids = list(word_bytes)
    while len(ids) >= 2:
        pairs = set(zip(ids, ids[1:]))
        candidates = [p for p in pairs if p in ranks]
        if not candidates:
            break
        best = min(candidates, key=lambda p: ranks[p])
        ids = list(merge_word(tuple(ids), best, pair_to_id[best]))
    return ids


def encode(text, ranks, pair_to_id):
    ids = []
    for part in pre_tokenize(text):
        ids.extend(encode_word(part.encode("utf-8"), ranks, pair_to_id))
    return ids


def decode(ids, vocab):
    return b"".join(vocab[i] for i in ids).decode("utf-8")


# ---------------------------------------------------------------------------
# Demo.
# ---------------------------------------------------------------------------

def main():
    merges, vocab, history = train(CORPUS, NUM_MERGES)
    ranks = {pair: rank for rank, (pair, _) in enumerate(merges)}
    pair_to_id = {pair: new_id for pair, new_id in merges}

    print("=== BPE from scratch ===\n")

    print("First 10 learned merges (most frequent pairs first):")
    for pair, new_id in merges[:10]:
        left, right = vocab[pair[0]], vocab[pair[1]]
        print(f"  {left!r:12} + {right!r:12} -> id {new_id:3} = {vocab[new_id]!r}")

    corpus_bytes = len(CORPUS.encode("utf-8"))
    print("\nVocab growth vs corpus compression:")
    print(f"  {'merges':>6} {'vocab':>6} {'corpus tokens':>13} {'bytes/token':>12}")
    for merge_count, vocab_size, tokens in history:
        print(f"  {merge_count:>6} {vocab_size:>6} {tokens:>13} {corpus_bytes / tokens:>12.2f}")

    # Round-trip on the training corpus.
    corpus_ids = encode(CORPUS, ranks, pair_to_id)
    assert decode(corpus_ids, vocab) == CORPUS, "corpus round-trip failed"

    # Round-trip on text the tokenizer never saw, including multi-byte UTF-8.
    unseen = "Tokenizers must survive café, naïve, and \U0001F680 without training on them."
    unseen_ids = encode(unseen, ranks, pair_to_id)
    assert decode(unseen_ids, vocab) == unseen, "unseen-text round-trip failed"

    # Compression: the trained tokenizer should beat one token per byte.
    ratio = corpus_bytes / len(corpus_ids)
    assert ratio > 1.5, f"expected compression above 1.5 bytes/token, got {ratio:.2f}"

    # Training bookkeeping matches a fresh encode of the corpus.
    assert len(corpus_ids) == history[-1][2], "tracked token count diverged from encoder"
    assert len(vocab) == BASE_VOCAB + len(merges)

    print(f"\nCorpus: {corpus_bytes} bytes -> {len(corpus_ids)} tokens "
          f"({ratio:.2f} bytes/token)")
    print(f"Unseen text round-trips: {len(unseen.encode('utf-8'))} bytes -> "
          f"{len(unseen_ids)} tokens")

    sample = "The tokenizer decides the cost"
    sample_ids = encode(sample, ranks, pair_to_id)
    print(f"\nToken boundaries for {sample!r}:")
    print("  " + " | ".join(decode([i], vocab) for i in sample_ids))

    # ------------------------------------------------------------------
    # Token boundary instability: the same word tokenizes differently with
    # and without a leading space. This is why prompt caches, which match on
    # exact token prefixes, break when prompt assembly is not byte stable.
    # ------------------------------------------------------------------
    with_space = encode(" tokenizer", ranks, pair_to_id)
    without_space = encode("tokenizer", ranks, pair_to_id)
    assert with_space != without_space, "expected different tokenizations"
    print("\nToken boundary sensitivity:")
    print(f"  ' tokenizer' -> {with_space}")
    print(f"  'tokenizer'  -> {without_space}")
    print("  One missing byte changes every token id that follows. A prompt")
    print("  cache keyed on token prefixes misses on all of them.")

    print("\nAll asserts passed.")


if __name__ == "__main__":
    main()
