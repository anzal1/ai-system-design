"""BM25 from scratch.

Everything a lexical search engine needs, in one file:

- tokenizer (lowercase, alphanumeric, tiny stopword list)
- inverted index (term -> postings list of (doc_id, term_frequency))
- IDF with the BM25 smoothing that keeps common terms non-negative
- the full BM25 scoring formula with k1 and b
- top-k search over a small inline corpus

The demo searches the corpus, then reruns one query under different
k1 and b settings to show how the parameters change rankings.

Stdlib only. Deterministic. Run: python3 bm25.py
"""

import math
import re
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Corpus: short docs from a fictional internal knowledge base. Doc 7 is
# deliberately long and repetitive to make length normalization visible.
# ---------------------------------------------------------------------------

CORPUS = {
    "doc0": "How to rotate API keys for the billing service. Keys expire "
            "every 90 days and rotation is zero downtime.",
    "doc1": "Postgres connection pool tuning guide. Set pool size based on "
            "core count, not request rate.",
    "doc2": "Incident review: billing outage caused by expired API keys. "
            "Rotation alert was misconfigured.",
    "doc3": "Kubernetes pod eviction and memory limits explained. Evictions "
            "happen before the OOM killer runs.",
    "doc4": "Onboarding checklist for new engineers. Covers laptop setup, "
            "VPN access, and repository permissions.",
    "doc5": "API gateway rate limiting design. Token bucket per client key, "
            "with burst allowance and retry headers.",
    "doc6": "Billing service architecture overview. Invoicing, proration, "
            "and payment retries with exponential backoff.",
    "doc7": "Billing billing billing. The billing team owns billing. For "
            "billing questions ask billing support. Billing invoices, "
            "billing disputes, billing exports, billing dashboards, billing "
            "reports, and billing escalations all go through the billing "
            "queue. Billing on-call handles billing pages about billing.",
}

STOPWORDS = {"a", "an", "and", "the", "is", "to", "of", "for", "on", "in",
             "with", "how", "all", "go", "not", "was", "by", "before",
             "every", "new", "ask", "about"}

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


# ---------------------------------------------------------------------------
# The index.
# ---------------------------------------------------------------------------


class BM25Index:
    """Inverted index with BM25 scoring.

    score(q, d) = sum over query terms t of:
        IDF(t) * tf(t,d) * (k1 + 1)
                 -----------------------------------------
                 tf(t,d) + k1 * (1 - b + b * |d| / avgdl)

    k1 controls term-frequency saturation: how quickly repeated
    occurrences of a term stop adding score. b controls length
    normalization: how much long documents are penalized.
    """

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.postings = defaultdict(list)  # term -> [(doc_id, tf), ...]
        self.doc_len = {}                  # doc_id -> token count
        self.n_docs = 0
        self.avgdl = 0.0

    def add(self, doc_id, text):
        tokens = tokenize(text)
        self.doc_len[doc_id] = len(tokens)
        for term, tf in sorted(Counter(tokens).items()):
            self.postings[term].append((doc_id, tf))
        self.n_docs += 1
        self.avgdl = sum(self.doc_len.values()) / self.n_docs

    def idf(self, term):
        """BM25 IDF with +0.5 smoothing and +1 inside the log so terms
        that appear in most documents score near zero instead of
        negative (the Lucene variant)."""
        df = len(self.postings.get(term, ()))
        return math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    def search(self, query, k=5, k1=None, b=None):
        k1 = self.k1 if k1 is None else k1
        b = self.b if b is None else b
        scores = defaultdict(float)
        for term in tokenize(query):
            idf = self.idf(term)
            for doc_id, tf in self.postings.get(term, ()):
                norm = 1 - b + b * self.doc_len[doc_id] / self.avgdl
                scores[doc_id] += idf * tf * (k1 + 1) / (tf + k1 * norm)
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked[:k]


# ---------------------------------------------------------------------------
# Demo.
# ---------------------------------------------------------------------------


def show(index, query, k=3, **params):
    results = index.search(query, k=k, **params)
    label = ", ".join(f"{n}={v}" for n, v in params.items()) or \
            f"k1={index.k1}, b={index.b}"
    print(f"\n  query: {query!r}  ({label})")
    for doc_id, score in results:
        preview = CORPUS[doc_id][:58]
        print(f"    {score:6.3f}  {doc_id}  {preview}...")
    return results


def main():
    index = BM25Index(k1=1.5, b=0.75)
    for doc_id, text in CORPUS.items():
        index.add(doc_id, text)

    print("=" * 72)
    print(f"BM25 over {index.n_docs} docs, avgdl={index.avgdl:.1f} tokens")
    print("=" * 72)

    print("\nIDF sanity check (rarer term, higher weight):")
    for term in ("billing", "keys", "eviction"):
        df = len(index.postings[term])
        print(f"  idf({term!r:12}) = {index.idf(term):.3f}  (df={df})")

    # Basic searches.
    r1 = show(index, "expired API keys billing outage")
    r2 = show(index, "postgres pool size")
    r3 = show(index, "rate limiting token bucket")

    # ----- Parameter study: k1 (term-frequency saturation) --------------
    print("\n" + "-" * 72)
    print("k1 study: query 'billing'. doc7 says 'billing' 14 times.")
    print("Low k1 saturates tf fast, so spam repetition stops paying.")
    low_k1 = show(index, "billing", k=3, k1=0.2, b=0.0)
    high_k1 = show(index, "billing", k=3, k1=5.0, b=0.0)

    # ----- Parameter study: b (length normalization) ---------------------
    print("\n" + "-" * 72)
    print("b study: same query. doc7 is also the longest doc, so length")
    print("normalization (b=1) is a second, independent way to demote it.")
    no_norm = show(index, "billing", k=3, k1=1.5, b=0.0)
    full_norm = show(index, "billing", k=3, k1=1.5, b=1.0)

    # ----- Correctness asserts ------------------------------------------
    # IDF ordering: term in 4 docs < term in 2 docs < term in 1 doc.
    assert index.idf("billing") < index.idf("keys") < index.idf("eviction")

    # The incident doc must win the incident query: it is the only doc
    # containing 'expired', 'outage', plus 'api', 'keys', 'billing'.
    assert r1[0][0] == "doc2", f"expected doc2 first, got {r1}"
    assert r2[0][0] == "doc1", f"expected doc1 first, got {r2}"
    assert r3[0][0] == "doc5", f"expected doc5 first, got {r3}"

    # k1 effect: with high k1, raw repetition dominates and the spammy
    # doc7 wins. With low k1, tf saturates and doc7's 14 repetitions are
    # worth barely more than one occurrence.
    assert high_k1[0][0] == "doc7", "high k1 should reward repetition"
    top_score_low = dict(low_k1)["doc7"]
    single_occurrence = [s for d, s in low_k1 if d != "doc7"]
    assert single_occurrence, "expected other billing docs in results"
    assert top_score_low < 1.30 * max(single_occurrence), \
        "low k1 should nearly flatten repetition advantage"

    # b effect: with b=0 doc7 wins on repetition; with b=1 its length
    # penalty cancels most of that advantage.
    assert no_norm[0][0] == "doc7"
    gap_no_norm = no_norm[0][1] - no_norm[1][1]
    gap_full = dict(full_norm)["doc7"] - max(
        s for d, s in full_norm if d != "doc7")
    assert gap_full < gap_no_norm, \
        "length normalization should shrink the long doc's lead"

    print("\nAll asserts passed.")
    print("Takeaway: k1 caps what repetition can buy, b charges rent for")
    print("length. Defaults (k1=1.2..2.0, b=0.75) exist because most")
    print("corpora contain a doc7.")


if __name__ == "__main__":
    main()
