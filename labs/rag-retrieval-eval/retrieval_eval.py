#!/usr/bin/env python3
"""Tiny retrieval eval for RAG system design.

This intentionally uses only the Python standard library. The goal is to teach
retrieval evaluation mechanics before adding embeddings, rerankers, or LLMs.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOCUMENTS_PATH = ROOT / "data" / "documents.jsonl"
QUERIES_PATH = ROOT / "data" / "queries.jsonl"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def term_frequency(tokens: list[str]) -> Counter:
    return Counter(tokens)


def inverse_document_frequency(documents: list[dict]) -> dict[str, float]:
    doc_count = len(documents)
    document_frequency: Counter[str] = Counter()

    for document in documents:
        terms = set(tokenize(document["text"]))
        document_frequency.update(terms)

    return {
        term: math.log((doc_count + 1) / (count + 1)) + 1
        for term, count in document_frequency.items()
    }


def score(query: str, document: dict, idf: dict[str, float]) -> float:
    query_terms = term_frequency(tokenize(query))
    document_terms = term_frequency(tokenize(document["text"]))

    total = 0.0
    for term, query_count in query_terms.items():
        if term not in document_terms:
            continue
        total += query_count * document_terms[term] * idf.get(term, 1.0)

    # Small title boost because titles often preserve useful document intent.
    title_terms = set(tokenize(document["title"]))
    total += sum(0.5 for term in query_terms if term in title_terms)
    return total


def retrieve(query: str, documents: list[dict], idf: dict[str, float], top_k: int) -> list[tuple[dict, float]]:
    scored = [(document, score(query, document, idf)) for document in documents]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def main() -> None:
    documents = load_jsonl(DOCUMENTS_PATH)
    queries = load_jsonl(QUERIES_PATH)
    idf = inverse_document_frequency(documents)

    top_1_hits = 0
    top_3_hits = 0

    for query in queries:
        results = retrieve(query["query"], documents, idf, top_k=3)
        returned_ids = [document["id"] for document, _score in results]
        expected_id = query["expected_document_id"]

        top_1_hit = returned_ids[:1] == [expected_id]
        top_3_hit = expected_id in returned_ids

        top_1_hits += int(top_1_hit)
        top_3_hits += int(top_3_hit)

        print("=" * 80)
        print(f"Query: {query['query']}")
        print(f"Expected: {expected_id}")
        print(f"Top-1 hit: {top_1_hit}")
        print(f"Top-3 hit: {top_3_hit}")
        print()

        for rank, (document, document_score) in enumerate(results, start=1):
            print(f"{rank}. {document['id']} | score={document_score:.2f} | {document['title']}")
        print()

    total = len(queries)
    print("=" * 80)
    print("Aggregate")
    print(f"Queries: {total}")
    print(f"Recall@1: {top_1_hits / total:.2f}")
    print(f"Recall@3: {top_3_hits / total:.2f}")
    print()
    print("Failure analysis")
    print("- Did failures come from missing terms, ambiguous wording, or weak ranking?")
    print("- Would metadata filters, query rewriting, hybrid search, or reranking help?")
    print("- Which failures would still break answer generation even with a stronger model?")


if __name__ == "__main__":
    main()
