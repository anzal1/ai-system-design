"""A complete RAG pipeline from scratch, composed from the sibling modules.

Stages, all built in this repo:

  documents -> chunker (recursive, structure-aware)
            -> BM25 index            -> ranked list A
            -> hashed-ngram vectors  -> ranked list B
            -> reciprocal rank fusion of A and B
            -> context assembly under a token budget
            -> stub "model": deterministic extractive answerer with citations

The model is a template, on purpose. The point is the system around it:
if retrieval, fusion, budgeting, and citation plumbing are right, any
real model drops into the last step. If they are wrong, no model saves
you.

Stdlib only. Deterministic. Offline. Run: python3 rag_pipeline.py
"""

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for sibling in ("chunker", "bm25", "vector-index"):
    sys.path.insert(0, os.path.join(_HERE, "..", sibling))

from chunker import chunk_recursive          # noqa: E402
from bm25 import BM25Index, tokenize         # noqa: E402
from vector_index import embed, cosine       # noqa: E402

# ---------------------------------------------------------------------------
# Corpus: three internal docs. Deliberately contains an exact error code
# (lexical search territory) and morphological variants like
# "authentication" vs "authenticating" (where token-exact BM25 misses
# and the character n-gram vectors still match).
# ---------------------------------------------------------------------------

DOCUMENTS = {
    "auth-guide": """\
# Service Authentication Guide

## Token Based User Authentication

The platform authenticates users with short lived bearer tokens. The
token issuer signs a token valid for fifteen minutes. Clients must
refresh before expiry. Tokens are validated locally against the cached
public key, so validation adds no network hop.

## Service To Service Auth

Service to service traffic uses mutual TLS. Certificate rotation
happens every 24 hours through the mesh controller. Never pin a
leaf cert.
""",
    "error-codes": """\
# Gateway Error Code Reference

## ERR-4302

ERR-4302 means the upstream returned a response larger than the 8 MB
gateway buffer. Fix it by enabling response streaming on the route or
raising the buffer limit for that route class.

## ERR-5108

ERR-5108 is emitted when the retry budget for a route is exhausted.
It usually indicates a downstream outage, not a gateway problem.
""",
    "deploy-notes": """\
# Deploy Pipeline Notes

## Rollout Strategy

Deploys roll one zone at a time with automated metric gates between
zones. A gate failure freezes the rollout and pages the release owner.
Manual promotion is available for emergency patches but requires two
approvals.

## Database Migrations

Migrations run before the code deploy and must be backward compatible
for one release. Destructive migrations wait one full release cycle
after the code that stopped using the old schema.
""",
}

RRF_K = 60          # standard damping constant for reciprocal rank fusion
TOKEN_BUDGET = 220  # context budget for the stub model, in estimated tokens


def estimate_tokens(text):
    """Rough token count: about 4 characters per token for English.
    A real system uses the target model's own tokenizer."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Ingestion: chunk every document, index every chunk twice.
# ---------------------------------------------------------------------------


def _has_body(chunk):
    """Ingestion filter: a chunk that is only heading lines carries no
    evidence and pollutes both indexes (tiny chunks score high under
    BM25 length normalization on any shared title word)."""
    return any(
        line.strip() and not line.lstrip().startswith("#")
        for line in chunk.split("\n")
    )


class HybridRetriever:
    def __init__(self, documents, chunk_size=350):
        self.chunks = {}   # chunk_id -> text
        self.bm25 = BM25Index(k1=1.5, b=0.75)
        self.vectors = {}  # chunk_id -> unit vector
        for doc_id, text in documents.items():
            body_chunks = [
                c for c in chunk_recursive(text, size=chunk_size) if _has_body(c)
            ]
            for i, chunk in enumerate(body_chunks):
                cid = f"{doc_id}#{i}"
                self.chunks[cid] = chunk
                self.bm25.add(cid, chunk)
                self.vectors[cid] = embed(chunk)

    def bm25_ranking(self, query, k=10):
        return [cid for cid, _ in self.bm25.search(query, k=k)]

    def vector_ranking(self, query, k=10):
        qv = embed(query)
        scored = sorted(
            ((cosine(qv, v), cid) for cid, v in self.vectors.items()),
            key=lambda x: (-x[0], x[1]),
        )
        return [cid for _, cid in scored[:k]]

    def fuse(self, rankings, k=10):
        """Reciprocal rank fusion: score(d) = sum over lists of
        1 / (RRF_K + rank). Rank-based, so BM25 scores and cosine
        similarities never need to share a scale."""
        scores = {}
        for ranking in rankings:
            for rank, cid in enumerate(ranking, start=1):
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
        fused = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return fused[:k]

    def retrieve(self, query, k=10):
        return self.fuse(
            [self.bm25_ranking(query, k), self.vector_ranking(query, k)], k
        )


# ---------------------------------------------------------------------------
# Context assembly: greedy packing under a token budget.
# ---------------------------------------------------------------------------


def assemble_context(retriever, fused, budget=TOKEN_BUDGET):
    """Take fused candidates in order, keep each chunk that still fits
    the budget, stop when the budget is spent. Returns a list of
    (citation_number, chunk_id, text) plus the tokens used."""
    context = []
    used = 0
    for cid, _score in fused:
        cost = estimate_tokens(retriever.chunks[cid])
        if used + cost > budget:
            continue  # skip and try the next, smaller candidate
        context.append((len(context) + 1, cid, retriever.chunks[cid]))
        used += cost
    return context, used


# ---------------------------------------------------------------------------
# Stub model: deterministic extractive answering with citations.
# ---------------------------------------------------------------------------

_SENT = re.compile(r"(?<=[.!?])\s+")


def _norm(token):
    """Suffix-stripping lite, so 'means' matches 'mean' and
    'authenticating' matches 'authenticate'. A real system does not
    need this: the actual model reads the context directly. The stub
    needs it because it matches surface tokens."""
    for suffix in ("ing", "ion", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[: -len(suffix)]
            break
    if token.endswith("e") and len(token) > 4:
        token = token[:-1]
    return token


def stub_model(query, context):
    """Stands in for the LLM. Picks the context sentences with the most
    query-term overlap, emits them with citation markers, and refuses
    when no sentence overlaps enough. Deterministic and dumb, which is
    the point: it can only answer from the context it was handed, so
    every quality problem visible here is a retrieval or assembly
    problem, not a model problem."""
    q_terms = {_norm(t) for t in tokenize(query)}
    scored = []
    for n, cid, text in context:
        # Drop heading lines; they title the evidence, they are not it.
        body = "\n".join(
            line for line in text.split("\n") if not line.lstrip().startswith("#")
        )
        flat = " ".join(body.split())
        for sent in _SENT.split(flat):
            terms = {_norm(t) for t in tokenize(sent)}
            overlap = len(q_terms & terms)
            if overlap >= 2:
                scored.append((-overlap, n, sent))
    if not scored:
        return "I cannot answer this from the provided context.", []
    scored.sort()
    picked = scored[:2]
    answer = " ".join(f"{sent} [{n}]" for _, n, sent in picked)
    cited = sorted({n for _, n, _ in picked})
    return answer, cited


# ---------------------------------------------------------------------------
# Pipeline runner and demo.
# ---------------------------------------------------------------------------


def answer(retriever, query, verbose=True):
    fused = retriever.retrieve(query)
    context, used = assemble_context(retriever, fused)
    text, cited = stub_model(query, context)
    if verbose:
        print(f"\nQ: {query}")
        print(f"  fused top 3: {[cid for cid, _ in fused[:3]]}")
        print(f"  context: {len(context)} chunks, ~{used}/{TOKEN_BUDGET} tokens")
        print(f"  A: {text}")
        if cited:
            for n, cid, _ in context:
                if n in cited:
                    print(f"     [{n}] {cid}")
    return fused, context, text, cited


def rank_of(cid, ranking):
    return ranking.index(cid) + 1 if cid in ranking else None


def find_chunk(retriever, substring):
    """Locate the gold chunk by content, not by guessed index."""
    hits = [cid for cid, text in retriever.chunks.items() if substring in text]
    assert len(hits) == 1, f"expected one chunk containing {substring!r}: {hits}"
    return hits[0]


def main():
    retriever = HybridRetriever(DOCUMENTS)
    print("=" * 72)
    print(f"RAG pipeline: {len(DOCUMENTS)} docs -> {len(retriever.chunks)} "
          f"chunks, BM25 + hashed-ngram vectors, RRF, "
          f"{TOKEN_BUDGET}-token context")
    print("=" * 72)

    # ----- Query 1: exact identifier. Lexical territory. -----------------
    q1 = "what does error ERR-4302 mean"
    gold1 = find_chunk(retriever, "gateway buffer")
    bm_r1 = retriever.bm25_ranking(q1)
    vec_r1 = retriever.vector_ranking(q1)
    print(f"\n[1] exact-identifier query: {q1!r}")
    print(f"  gold chunk {gold1}: rank  bm25={rank_of(gold1, bm_r1)}  "
          f"vector={rank_of(gold1, vec_r1)}")
    fused1, ctx1, a1, c1 = answer(retriever, q1)

    # ----- Query 2: morphological variants. Vector territory. ------------
    # The doc says "Certificate rotation"; the query says "rotating
    # certificates". Exact-token BM25 matches none of the query's word
    # forms, but character n-grams overlap heavily.
    q2 = "rotating certificates for internal services"
    gold2 = find_chunk(retriever, "Certificate rotation")
    bm_r2 = retriever.bm25_ranking(q2)
    vec_r2 = retriever.vector_ranking(q2)
    print(f"\n[2] morphological-variant query: {q2!r}")
    print(f"  gold chunk {gold2}: rank  bm25={rank_of(gold2, bm_r2)}  "
          f"vector={rank_of(gold2, vec_r2)}")
    fused2, ctx2, a2, c2 = answer(retriever, q2)

    # ----- Query 3: no evidence in corpus. Must refuse. -------------------
    q3 = "what is the parental leave policy"
    fused3, ctx3, a3, c3 = answer(retriever, q3)

    # ----- Correctness asserts --------------------------------------------
    # 1. Exact identifier: BM25 puts the gold chunk first; fusion keeps it
    #    on top; the answer cites a chunk that actually contains the code.
    assert rank_of(gold1, bm_r1) == 1
    assert fused1[0][0] == gold1
    assert c1, "query 1 should be answerable"
    cited_texts1 = [t for n, _, t in ctx1 if n in c1]
    assert any("ERR-4302" in t for t in cited_texts1), \
        "citation must point at the chunk containing the error code"
    assert "streaming" in a1 or "buffer" in a1, f"answer misses the fix: {a1}"

    # 2. Morphological variant: the vector ranking beats BM25 for the gold
    #    chunk, and fusion still surfaces it at the top.
    r_bm = rank_of(gold2, bm_r2) or len(retriever.chunks) + 1
    r_vec = rank_of(gold2, vec_r2)
    assert r_vec is not None and r_vec < r_bm, \
        f"vector rank {r_vec} should beat bm25 rank {r_bm}"
    assert fused2[0][0] == gold2
    assert c2, "query 2 should be answerable"

    # 3. Token budget is enforced for every query.
    for ctx in (ctx1, ctx2, ctx3):
        assert sum(estimate_tokens(t) for _, _, t in ctx) <= TOKEN_BUDGET

    # 4. Citation integrity: every cited number maps to a context chunk.
    for cited, ctx in ((c1, ctx1), (c2, ctx2), (c3, ctx3)):
        nums = {n for n, _, _ in ctx}
        assert all(n in nums for n in cited), "dangling citation"

    # 5. No evidence means refusal, not a confident guess.
    assert not c3 and "cannot answer" in a3, f"expected refusal, got: {a3}"

    print("\nAll asserts passed.")
    print("Takeaway: the stub model never hallucinates because it can only")
    print("quote its context. Every wrong answer in this pipeline would be")
    print("a retrieval, fusion, or budgeting bug. That is the property to")
    print("preserve when a real model replaces the stub.")


if __name__ == "__main__":
    main()
