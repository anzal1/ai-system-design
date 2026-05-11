# AI System Design

A practical, open-source guide to designing production AI systems.

Most system design resources teach databases, caches, queues, APIs, replication, sharding, and scaling. Those still matter. But AI-native products add new failure modes and design decisions:

- Probabilistic model behavior
- Hallucinations and unverifiable answers
- Retrieval quality and stale knowledge
- Prompt and model version drift
- Tool misuse and agentic failure loops
- Evaluation pipelines and regression testing
- Latency budgets shaped by model calls and token volume
- Cost controls across prompts, retrieval, reranking, and inference
- Security risks such as prompt injection, data leakage, and unsafe tool execution

This repo exists to map those problems clearly.

## What This Is

AI System Design is a field guide for engineers designing real AI products. It focuses on architecture, tradeoffs, failure modes, evaluation, observability, security, and production constraints.

The goal is not to collect AI news. The goal is to explain how to make system design decisions when the core component is a model whose output is useful but not guaranteed.

## Who This Is For

- Backend engineers moving into AI products
- ML engineers who need product and infrastructure architecture context
- Founders building AI-native SaaS products
- Senior engineers preparing for AI system design interviews
- Devtool and platform engineers building internal AI infrastructure

## What This Is Not

- Not an AI news feed
- Not a prompt-hack collection
- Not vendor marketing
- Not a generic ML theory course
- Not an "awesome links" repository
- Not a place for unsourced claims or shallow summaries

## Start Here

1. [What Is AI System Design?](./foundations/what-is-ai-system-design.md)
2. [RAG System Design](./patterns/rag.md)
3. [Agent Tool-Use System Design](./patterns/agent-tool-use.md)
4. [Evaluation Pipeline Pattern](./patterns/eval-pipeline.md)
5. [RAG vs Fine-Tuning](./decision-guides/rag-vs-finetuning.md)

## Repo Map

```text
ai-system-design/
├── foundations/             # Core concepts and mental models
├── patterns/                # Reusable architecture patterns
├── decision-guides/         # Tradeoff-driven engineering decisions
├── case-studies/            # Realistic system design walkthroughs
├── evals-observability/     # Testing, tracing, monitoring, and feedback loops
├── security/                # AI-specific threat models and mitigations
├── reference-architectures/ # Production-ready blueprints
├── frontier-notes/          # Cutting-edge changes translated into production impact
└── resources/               # Curated source map, not a dumping ground
```

## Content Standard

Every serious page should answer:

- What problem does this solve?
- When should you use it?
- What is the architecture?
- What are the core components?
- What are the tradeoffs?
- What fails in production?
- How do you evaluate it?
- What should you observe?
- What are the cost and latency implications?
- What are the security risks?
- What sources support the claims?

See [CONTENT_STANDARD.md](./CONTENT_STANDARD.md).

## Contributing

This repo should be useful because it is selective. Contributions are welcome, but the bar is intentionally high.

Good contributions include:

- Production architecture patterns
- Clear decision guides
- Case studies with concrete tradeoffs
- Failure modes from real systems
- Evaluation and observability methods
- Primary-source-backed frontier notes

Start with [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

Content is licensed under [CC BY 4.0](./LICENSE.md) unless otherwise noted.
