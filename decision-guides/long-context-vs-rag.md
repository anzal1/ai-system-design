# Long Context vs RAG

Last reviewed: 2026-06-29

## Problem

Large context windows make it tempting to put everything into the prompt. This can simplify early prototypes, but it does not eliminate retrieval, permissions, freshness, cost, or evaluation problems.

## Short Answer

Use long context when the working set is bounded, the user needs synthesis over many provided artifacts, and latency/cost are acceptable.

Use RAG when the knowledge base is large, dynamic, permissioned, or needs source selection.

## Decision Table

| Requirement | Long context | RAG |
| --- | --- | --- |
| User uploads a small set of files | Strong | Maybe |
| Large enterprise knowledge base | Weak | Strong |
| Strict permissions | Harder | Strong |
| Freshness and deletion | Harder | Strong |
| Source discovery | Weak | Strong |
| Multi-document synthesis | Strong | Strong |
| Low cost | Often weak | Depends |

## Long Context Strengths

- Simple architecture
- Fewer retrieval misses
- Good for bounded document sets
- Easier to preserve local document order
- Useful for codebase or contract review tasks

## Long Context Risks

- High token cost
- High latency
- Attention dilution
- Harder citation support
- Harder permission control
- Context packing becomes its own retrieval problem

## RAG Strengths

- Scales to large corpora
- Supports permissions
- Supports freshness
- Supports targeted source selection
- Easier to evaluate retrieval

## RAG Risks

- Retrieval misses
- Chunking errors
- Indexing complexity
- Reranking cost
- Citation mismatch

## Practical Rule

Long context is not a replacement for information architecture. If the system needs to choose what the model sees, you still need retrieval logic, even if the context window is large.

## Further Reading

- [RAG System Design](../patterns/rag.md)
- [Hybrid RAG And Reranking](../patterns/hybrid-rag-reranking.md)
