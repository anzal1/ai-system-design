"""Document chunking from scratch.

Three strategies over the same document, with overlap:

1. Fixed-size: cut every N characters, no respect for structure.
2. Sentence-aware: pack whole sentences into chunks up to a size budget.
3. Recursive structure-aware: split on the largest structural boundary
   (headings, then paragraphs, then sentences) until pieces fit.

The demo chunks one realistic markdown document all three ways and
prints boundary-quality metrics: how many chunks end mid-sentence and
how many split a heading away from its body text.

Stdlib only. Deterministic. Run: python3 chunker.py
"""

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Demo document: a realistic internal runbook in markdown.
# ---------------------------------------------------------------------------

DOCUMENT = """\
# Payments Service Runbook

The payments service handles card authorization, capture, and refunds
for all checkout flows. It sits behind the API gateway and talks to
the ledger service over gRPC. On-call engineers should read this
entire document before their first shift.

## Architecture Overview

The service runs as twelve pods across three availability zones. Each
pod holds an in-memory idempotency cache with a five minute TTL.
Requests carry an Idempotency-Key header. If the key is present in the
cache, the cached response is returned and no downstream call is made.
The cache is not shared between pods, so a retried request that lands
on a different pod will reach the processor again. The processor
deduplicates on its side, which makes this safe but wasteful.

## Common Alerts

### HighAuthLatency

This alert fires when p99 authorization latency exceeds 1200 ms for
five minutes. The usual cause is processor slowness, not our code.
Check the processor status page first. If the processor is healthy,
look at connection pool saturation on the ledger client. Pool
exhaustion shows up as queue time, not connection errors, so it is
easy to misdiagnose.

### RefundBacklog

Refunds are processed by a worker that drains a queue. The alert
fires at 5000 queued refunds. Refunds are not latency sensitive, so
do not page the processor team. Scale the worker deployment to eight
replicas and the backlog usually clears within an hour.

## Deployment Notes

Deploys roll one zone at a time with a 10 minute bake per zone. Never
skip the bake. The incident on 2024-03-11 was caused by a fast rollout
that hit all zones before the first bad metric appeared. Rollback is a
single command: `deployctl rollback payments --to-previous`. It takes
about four minutes to complete.

## Contact

Escalate to the payments platform team via the escalation policy in
the paging tool. Do not DM individual engineers for production issues.
"""

# ---------------------------------------------------------------------------
# Strategy 1: fixed-size chunks with character overlap.
# ---------------------------------------------------------------------------


def chunk_fixed(text, size=400, overlap=80):
    """Cut the text every `size` characters, stepping back `overlap`
    characters between chunks. Fast and simple, blind to structure."""
    assert 0 <= overlap < size
    chunks = []
    step = size - overlap
    for start in range(0, len(text), step):
        piece = text[start : start + size]
        if piece.strip():
            chunks.append(piece)
        if start + size >= len(text):
            break
    return chunks


# ---------------------------------------------------------------------------
# Strategy 2: sentence-aware packing.
# ---------------------------------------------------------------------------

# Sentence splitter: end punctuation followed by whitespace and an
# uppercase letter, digit, or markdown marker. Deliberately simple; a
# production system would use a trained segmenter or at least handle
# abbreviations.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9#`])")


def split_sentences(text):
    """Split text into sentences, keeping markdown lines like headings
    as their own units (they do not end with punctuation)."""
    units = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            units.append(block)
            continue
        flat = " ".join(block.split())
        units.extend(s for s in _SENTENCE_END.split(flat) if s)
    return units


def chunk_sentences(text, size=400, overlap_sentences=1):
    """Pack whole sentences into chunks of at most `size` characters,
    carrying the last `overlap_sentences` sentences into the next chunk."""
    sentences = split_sentences(text)
    chunks = []
    current = []
    length = 0
    for sent in sentences:
        added = len(sent) + (1 if current else 0)
        if current and length + added > size:
            chunks.append(" ".join(current))
            carry = current[-overlap_sentences:] if overlap_sentences else []
            current = list(carry)
            length = sum(len(s) for s in current) + max(len(current) - 1, 0)
        current.append(sent)
        length += len(sent) + (1 if len(current) > 1 else 0)
    if current:
        chunks.append(" ".join(current))
    return chunks


# ---------------------------------------------------------------------------
# Strategy 3: recursive structure-aware splitting.
# ---------------------------------------------------------------------------

# Separators ordered from strongest structural boundary to weakest.
# This is the idea behind "recursive character splitting" in most RAG
# frameworks: try the biggest boundary first, recurse only when a
# piece is still too large.
_SEPARATORS = [
    re.compile(r"\n(?=## )"),   # H2 sections
    re.compile(r"\n(?=### )"),  # H3 subsections
    re.compile(r"\n\n"),        # paragraphs
    _SENTENCE_END,              # sentences
]


_HEADING_LINE = re.compile(r"^(#{1,6} [^\n]+)\n+", re.MULTILINE)


def chunk_recursive(text, size=400, overlap_sentences=1, _level=0):
    """Split on the largest boundary that produces pieces small enough.
    Pieces that fit are kept whole; oversized pieces recurse to the
    next separator level. When an oversized piece starts with a heading,
    the heading is carried onto every child chunk so no chunk loses its
    section context. At the final level, fall back to sentence packing
    so no chunk exceeds the budget."""
    text_stripped = text.strip()
    if not text_stripped:
        return []
    if len(text_stripped) <= size:
        return [text_stripped]
    if _level >= len(_SEPARATORS) - 1:
        return chunk_sentences(text, size, overlap_sentences)

    pieces = [p for p in _SEPARATORS[_level].split(text) if p.strip()]
    if len(pieces) == 1:
        return chunk_recursive(text, size, overlap_sentences, _level + 1)

    chunks = []
    for piece in pieces:
        piece = piece.strip()
        if len(piece) <= size:
            chunks.append(piece)
            continue
        # Oversized piece. If it opens with a heading, split the body and
        # propagate the heading onto each child chunk.
        m = _HEADING_LINE.match(piece)
        if m:
            heading = m.group(1)
            body = piece[m.end():]
            budget = size - len(heading) - 1
            for child in chunk_recursive(body, budget, overlap_sentences, _level + 1):
                chunks.append(heading + "\n" + child)
        else:
            chunks.extend(chunk_recursive(piece, size, overlap_sentences, _level + 1))
    return chunks


# ---------------------------------------------------------------------------
# Boundary quality metrics.
# ---------------------------------------------------------------------------


@dataclass
class Quality:
    strategy: str
    n_chunks: int = 0
    broken_sentence_ends: int = 0   # chunk ends mid-sentence
    broken_sentence_starts: int = 0  # chunk starts mid-sentence
    orphan_headings: int = 0        # heading at chunk end with no body after it
    sizes: list = field(default_factory=list)


_HEADING_AT_END = re.compile(r"(^|\n)#{1,6} [^\n]*\s*$")


def measure(strategy, chunks):
    q = Quality(strategy=strategy, n_chunks=len(chunks), sizes=[len(c) for c in chunks])
    for c in chunks:
        body = c.strip()
        if not body:
            continue
        # A clean end is terminal punctuation, a heading line, or a code fence.
        if not re.search(r"[.!?:`]$", body) and not body.split("\n")[-1].startswith("#"):
            q.broken_sentence_ends += 1
        # A clean start is a capital letter, digit, heading, or backtick.
        first = body[0]
        if not (first.isupper() or first.isdigit() or first in "#`"):
            q.broken_sentence_starts += 1
        # A heading as the last line means its body landed in another chunk.
        if _HEADING_AT_END.search(body):
            q.orphan_headings += 1
    return q


def report(q):
    avg = sum(q.sizes) / len(q.sizes) if q.sizes else 0
    print(f"  {q.strategy:<28} chunks={q.n_chunks:<3} avg_len={avg:6.0f}  "
          f"broken_ends={q.broken_sentence_ends:<2} broken_starts={q.broken_sentence_starts:<2} "
          f"orphan_headings={q.orphan_headings}")


# ---------------------------------------------------------------------------
# Demo.
# ---------------------------------------------------------------------------


def main():
    size = 400

    fixed = chunk_fixed(DOCUMENT, size=size, overlap=80)
    sent = chunk_sentences(DOCUMENT, size=size, overlap_sentences=1)
    rec = chunk_recursive(DOCUMENT, size=size, overlap_sentences=1)

    print("=" * 72)
    print("Chunking one runbook three ways (budget: 400 chars per chunk)")
    print("=" * 72)

    q_fixed = measure("fixed-size (overlap=80)", fixed)
    q_sent = measure("sentence-aware (overlap=1)", sent)
    q_rec = measure("recursive structure-aware", rec)

    print("\nBoundary quality (lower is better for every count):")
    for q in (q_fixed, q_sent, q_rec):
        report(q)

    print("\nSample boundary from each strategy (last 60 chars of chunk 2,")
    print("first 60 chars of chunk 3):")
    for name, chunks in (("fixed", fixed), ("sentence", sent), ("recursive", rec)):
        a = " ".join(chunks[1].split())[-60:]
        b = " ".join(chunks[2].split())[:60]
        print(f"\n  [{name}]")
        print(f"    ...{a}")
        print(f"    {b}...")

    print("\nRecursive chunks keep sections intact. First recursive chunk:")
    print("  " + " | ".join(rec[0].split("\n")[:1]))
    print(f"  ({len(rec[0])} chars, ends with: ...{rec[0][-40:].strip()!r})")

    # ----- Correctness asserts ------------------------------------------
    # Every strategy must cover the document's content (no dropped text
    # beyond whitespace normalization). Check on a token-set basis.
    doc_tokens = set(re.findall(r"\w+", DOCUMENT.lower()))
    for name, chunks in (("fixed", fixed), ("sentence", sent), ("recursive", rec)):
        chunk_tokens = set()
        for c in chunks:
            chunk_tokens.update(re.findall(r"\w+", c.lower()))
        missing = doc_tokens - chunk_tokens
        assert not missing, f"{name} chunking dropped tokens: {missing}"

    # Size budgets are respected where the strategy promises them.
    assert all(len(c) <= size for c in fixed), "fixed chunks exceed budget"
    # Sentence and recursive chunks may exceed budget only when a single
    # sentence is longer than the budget; none are in this document.
    assert all(len(c) <= size for c in sent), "sentence chunks exceed budget"
    assert all(len(c) <= size for c in rec), "recursive chunks exceed budget"

    # Overlap is real: consecutive fixed chunks share text.
    assert fixed[0][-80:] == fixed[1][:80], "fixed overlap missing"

    # Structure-aware chunking must beat fixed-size on boundary quality.
    assert q_rec.broken_sentence_ends < q_fixed.broken_sentence_ends, \
        "recursive should break fewer sentence ends than fixed"
    assert q_rec.broken_sentence_starts < q_fixed.broken_sentence_starts, \
        "recursive should break fewer sentence starts than fixed"
    assert q_sent.broken_sentence_ends < q_fixed.broken_sentence_ends, \
        "sentence-aware should break fewer sentence ends than fixed"
    assert q_rec.orphan_headings == 0, "recursive should not orphan headings"

    print("\nAll asserts passed.")
    print("Takeaway: fixed-size is cheapest but produces the worst boundaries;")
    print("recursive splitting keeps headings with their bodies, which is what")
    print("a retriever needs to match section-level queries.")


if __name__ == "__main__":
    main()
