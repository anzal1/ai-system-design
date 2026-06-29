# Course

AI System Design is a practical course for engineers who already understand software systems and want to design production-grade AI systems.

The course is built around one idea: AI products are systems, not prompts. A useful AI feature needs architecture, evaluation, observability, security, cost control, and operational discipline.

## Learning Outcomes

By the end, you should be able to:

- Design an AI feature from requirements to production rollout
- Choose between prompting, RAG, fine-tuning, tools, workflows, and agents
- Build retrieval systems with measurable quality
- Design eval pipelines that catch regressions
- Debug AI behavior with traces and observability
- Threat-model prompt injection, data leakage, and unsafe tool use
- Budget latency and cost across model calls, retrieval, reranking, and tools
- Review AI system architectures like a senior engineer

## Prerequisites

You should be comfortable with:

- APIs and backend services
- Databases and search basics
- Queues, caches, and rate limits
- Basic machine learning concepts
- Reading engineering design docs

You do not need to be a deep learning researcher.

## How To Use This Course

Use the course in three passes.

### Pass 1: Concepts

Read the core guides and understand the vocabulary.

### Pass 2: Systems

Work through the labs and design assignments. The goal is not to memorize patterns. The goal is to practice making tradeoffs.

### Pass 3: Reviews

Read and write design reviews. This is where the real learning happens: constraints, failure modes, eval plans, security boundaries, and cost budgets.

## Module 1: AI System Design Fundamentals

Start here if you are coming from traditional backend or system design.

Read:

- [What Is AI System Design?](./foundations/what-is-ai-system-design.md)

Practice:

- Write a one-page design for a simple AI assistant.
- Identify where correctness depends on model behavior instead of deterministic code.

You should be able to explain:

- Why AI systems need evals
- Why context is a design surface
- Why model output is not the same as product behavior

## Module 2: LLM Application Architecture

Learn the common shape of production LLM applications: orchestration, prompts, structured outputs, retries, fallbacks, logging, and safety boundaries.

Read:

- [Evaluation Pipeline Pattern](./patterns/eval-pipeline.md)

Practice:

- Add a trace schema for an AI request.
- Define fallback behavior for a failed model call.

You should be able to explain:

- What belongs in the orchestration layer
- What to log for reproducibility
- Where deterministic validation should sit

## Module 3: RAG Systems

Learn how to connect models to external knowledge through retrieval.

Read:

- [RAG System Design](./patterns/rag.md)
- [RAG vs Fine-Tuning](./decision-guides/rag-vs-finetuning.md)

Lab:

- [RAG Retrieval Eval Lab](./labs/rag-retrieval-eval/README.md)

Assignment:

- [Design Enterprise RAG](./assignments/design-enterprise-rag.md)

You should be able to explain:

- How chunking affects quality
- When hybrid retrieval is better than vector search alone
- How to evaluate retrieval separately from generation
- Why citations are not automatically trustworthy

## Module 4: Evaluation Systems

Learn to treat AI quality as an engineering loop.

Read:

- [Evaluation Pipeline Pattern](./patterns/eval-pipeline.md)

Practice:

- Build an eval set from expected behavior, edge cases, and known failures.
- Define release gates for a model or prompt change.

You should be able to explain:

- Why offline and online evals serve different purposes
- When deterministic checks beat LLM judges
- How production failures become regression tests

## Module 5: Observability And Debugging

Learn what must be traced to debug AI behavior.

Practice:

- Design a trace record for a RAG answer.
- Identify which fields require redaction or access control.

You should be able to explain:

- Why normal API logs are not enough
- How to debug retrieval failures
- How to compare prompt/model versions

## Module 6: Agents And Workflows

Learn the difference between deterministic workflows and agentic systems.

Read:

- [Agent Tool-Use System Design](./patterns/agent-tool-use.md)

Assignment:

- [Design Agent Workflow](./assignments/design-agent-workflow.md)

You should be able to explain:

- When an agent is justified
- How to design tool permission boundaries
- Why write tools need approval and auditability
- How to limit loops, cost, and side effects

## Module 7: Security And Safety

Learn the security model of AI applications.

Read:

- [Prompt Injection Threat Model](./security/prompt-injection.md)

Practice:

- Add adversarial cases to an eval set.
- Threat-model a RAG or agent architecture.

You should be able to explain:

- Direct vs indirect prompt injection
- Why retrieved content is untrusted data
- Why tool authorization must live outside the model

## Module 8: Cost, Latency, And Scaling

Learn to budget the full request path, not just the final model call.

Practice:

- Create a latency budget for a support agent.
- Decide which steps can use small models, caching, batching, or async work.

You should be able to explain:

- How retrieval, reranking, tools, and generation contribute to latency
- How model routing can reduce cost
- When streaming improves perceived latency but not total latency

## Module 9: Production Case Studies

Learn by reviewing complete systems.

Read:

- [AI Customer Support Agent](./case-studies/ai-support-agent.md)
- [Enterprise Document Q&A Design Review](./design-reviews/enterprise-doc-qa/README.md)

You should be able to explain:

- How requirements shape architecture
- How eval, observability, and security fit into the system
- Which constraints force tradeoffs

## Module 10: Frontier To Production

Learn how to evaluate new models, papers, tools, and standards without chasing hype.

Read:

- [Frontier Notes Guide](./frontier-notes/README.md)

Practice:

- Pick a new paper, model release, or framework feature.
- Write what changed, what it affects, what remains unproven, and whether teams should adopt, watch, or ignore it.

You should be able to explain:

- The difference between novelty and production value
- How to translate research into architecture implications
- How to keep content current without becoming a news feed

## Recommended Path

If you want the shortest serious path:

1. Read [What Is AI System Design?](./foundations/what-is-ai-system-design.md)
2. Read [RAG System Design](./patterns/rag.md)
3. Run [RAG Retrieval Eval Lab](./labs/rag-retrieval-eval/README.md)
4. Read [Evaluation Pipeline Pattern](./patterns/eval-pipeline.md)
5. Read [Agent Tool-Use System Design](./patterns/agent-tool-use.md)
6. Read [Prompt Injection Threat Model](./security/prompt-injection.md)
7. Complete [Design Enterprise RAG](./assignments/design-enterprise-rag.md)
8. Review [Enterprise Document Q&A](./design-reviews/enterprise-doc-qa/README.md)
