# Assignment: Design Enterprise RAG

## Scenario

You are designing an internal AI assistant for a 5,000-person company. Employees should be able to ask questions about company policies, engineering docs, HR documents, security procedures, and customer-facing playbooks.

The system must answer from approved internal documents and cite sources. It must respect document permissions.

## Requirements

- Support natural-language questions over internal documents
- Return answers with citations
- Respect user, team, and document-level permissions
- Detect when there is not enough evidence to answer
- Support document updates within 24 hours
- Provide traces for debugging bad answers
- Support at least 1,000 daily active users in the first phase

## Non-Goals

- Replacing enterprise search completely
- Answering from arbitrary internet sources
- Automatically taking actions in internal systems
- Training a model on all internal documents in phase one

## Constraints

- Some documents contain sensitive customer or employee information
- Source systems include Google Drive, Notion, Confluence, GitHub, and PDFs
- Documents change frequently
- Users should receive answers in less than 5 seconds for common queries
- Security needs audit logs for sensitive document access

## Deliverable

Write a design doc that includes:

1. Architecture diagram
2. Ingestion pipeline
3. Chunking strategy
4. Retrieval strategy
5. Metadata and permission model
6. Citation strategy
7. Evaluation plan
8. Observability plan
9. Security review
10. Cost and latency budget
11. Rollout plan

## Design Questions

Answer these explicitly:

- Where are permissions enforced?
- How do you prevent stale documents from being used?
- How do you evaluate retrieval quality?
- How do you evaluate answer faithfulness?
- What should happen when sources conflict?
- What should happen when no source supports an answer?
- When would you add reranking?
- When would you add query rewriting?
- What traces are needed to debug a bad answer?
- How do you prevent prompt injection inside retrieved docs?

## Expected Tradeoffs

You should discuss:

- Vector search vs hybrid search
- Small chunks vs large chunks
- Pre-filtering vs post-filtering permissions
- Reranking quality vs latency
- Citation strictness vs answer usefulness
- Freshness vs ingestion cost
- Centralized index vs per-source connectors

## Evaluation Rubric

| Dimension | Strong answer |
| --- | --- |
| Retrieval | Separates first-stage retrieval, filtering, reranking, and context building |
| Permissions | Enforces access outside the model before context assembly |
| Evals | Includes retrieval, generation, citation, refusal, and security evals |
| Observability | Logs query, retrieved chunks, scores, context, output, citations, and feedback |
| Security | Treats retrieved content as untrusted and covers indirect prompt injection |
| Operations | Handles document freshness, deletion, source failures, and index rebuilds |
| Latency | Budgets embedding, search, reranking, model generation, and tracing |

## Stretch Goals

- Add support for tables and code snippets
- Add per-team indexes
- Add human feedback workflow
- Add source conflict handling
- Add answer confidence labels
