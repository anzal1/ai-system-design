# RAG Retrieval Eval Lab

This lab teaches a core RAG lesson:

> Before evaluating generated answers, evaluate whether retrieval finds the right evidence.

The lab uses a tiny local corpus and a standard-library Python script. It does not require API keys, embeddings, or a model provider. That is intentional. The purpose is to isolate retrieval quality.

## What You Will Learn

- How retrieval quality affects RAG systems
- Why keyword retrieval can fail on semantic queries
- Why metadata and expected source IDs matter
- How to compute simple top-K retrieval metrics
- How to turn retrieval failures into system design decisions

## Files

```text
labs/rag-retrieval-eval/
├── README.md
├── retrieval_eval.py
└── data/
    ├── documents.jsonl
    └── queries.jsonl
```

## Run

From the repo root:

```bash
python3 labs/rag-retrieval-eval/retrieval_eval.py
```

Expected output includes:

- Top retrieved documents for each query
- Whether the expected source appeared in top 1 and top 3
- Aggregate recall metrics
- Failure analysis prompts

## System Design Lesson

A RAG answer can fail for multiple reasons:

- The right document was never indexed
- The right document was indexed but chunked badly
- Retrieval returned the wrong chunk
- Retrieval found the right chunk but ranked it too low
- The model ignored the evidence
- The answer cited a document that did not support the claim

This lab isolates one layer: retrieval.

## Exercise

1. Run the lab.
2. Inspect the failures.
3. Add one new query to `data/queries.jsonl`.
4. Add one new document to `data/documents.jsonl`.
5. Re-run the eval.
6. Write down whether the failure was caused by vocabulary mismatch, missing metadata, ambiguous wording, or weak scoring.

## Questions

- Which queries fail because the words do not match?
- Which queries would benefit from synonyms or query rewriting?
- Which queries need metadata filters?
- Which queries need a reranker?
- Which failures would not be fixed by a larger language model?

## Extensions

- Add BM25 instead of the simple scorer.
- Add metadata filters such as `audience`, `source_type`, or `updated_at`.
- Add a second-stage reranker.
- Add chunk IDs and parent document IDs.
- Add a field for whether the retrieved document supports a citation.

## Production Connection

In production RAG systems, retrieval evals should run before prompt or model changes are judged. If the correct evidence is missing from the context, answer quality evals will mix retrieval failure with generation failure.
