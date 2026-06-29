# Source Map

Last reviewed: 2026-05-11

This is a curated source map for AI system design. It is not an "awesome links" list.

Add a source only when it supports a concrete design decision, tradeoff, failure mode, evaluation method, or production architecture.

## Source Types

- **Official:** provider docs, standards, reference architectures, model/system cards
- **Research:** papers, benchmarks, conference material
- **Implementation:** open-source repos, examples, SDKs, eval harnesses
- **Engineering:** production writeups, postmortems, architecture blogs
- **Practitioner:** high-signal field reports with concrete evidence

## Evaluation

| Source | Type | Why it matters |
| --- | --- | --- |
| [OpenAI evaluation best practices](https://platform.openai.com/docs/guides/evaluation-best-practices) | Official | Defines practical eval design, continuous evaluation, and production-oriented test thinking for LLM apps. |
| [Anthropic evaluation tool](https://docs.claude.com/en/docs/test-and-evaluate/eval-tool) | Official | Shows how prompt and model behavior can be tested against scenario datasets. |
| [Arize Phoenix LLM evals](https://arize.com/docs/phoenix/evaluation/llm-evals) | Implementation | Useful for understanding evaluator types, LLM-as-judge patterns, and observability integration. |
| [LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) | Implementation | Helpful for dataset-driven evaluation, experiments, and application-level testing. |

## RAG

| Source | Type | Why it matters |
| --- | --- | --- |
| [Google Cloud RAG reference architectures](https://docs.cloud.google.com/architecture/rag-reference-architectures) | Official | Provides cloud reference architectures for retrieval-augmented generation systems. |
| [LlamaIndex RAG documentation](https://docs.llamaindex.ai/en/stable/understanding/rag/) | Implementation | Useful for understanding indexing, retrieval, and query workflows. |
| [ARES: Automated Evaluation Framework for RAG Systems](https://arxiv.org/abs/2311.09476) | Research | Frames RAG evaluation around context relevance, answer faithfulness, and answer relevance. |

## Agents And Tool Use

| Source | Type | Why it matters |
| --- | --- | --- |
| [Anthropic tool use](https://docs.claude.com/en/docs/tool-use) | Official | Shows the model-tool interaction loop and the need to implement tools client-side. |
| [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Engineering | Clearly separates workflows from agents and argues for adding agentic complexity only when it improves outcomes. |
| [OpenAI Agents SDK](https://platform.openai.com/docs/guides/agents-sdk/) | Official | Useful for understanding agent orchestration, tracing, and tool integration patterns. |
| [OpenAI Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/) | Implementation | Shows where input and output guardrails fit in agent design. |
| [LangGraph documentation](https://docs.langchain.com/langgraph) | Implementation | Useful for durable execution, streaming, human-in-the-loop, and agent orchestration concepts. |

## Tool Integration

| Source | Type | Why it matters |
| --- | --- | --- |
| [Model Context Protocol documentation](https://modelcontextprotocol.io/docs/getting-started/intro) | Standard | MCP is an open protocol for connecting AI applications to external data, tools, and workflows. |
| [OpenTelemetry GenAI semantic conventions repository](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai) | Standard | Tracks emerging telemetry conventions for model calls, agents, MCP, metrics, spans, and events. |

## Security

| Source | Type | Why it matters |
| --- | --- | --- |
| [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications) | Standard | Baseline threat model for LLM application security, including prompt injection and data leakage. |
| [OWASP Top 10 for LLM Applications 2025 PDF](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf) | Standard | Useful as a stable reference artifact for security discussions and review. |
| [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) | Standard | Provides a broad risk-management framework for trustworthy AI systems and links to the Generative AI Profile. |

## Observability

| Source | Type | Why it matters |
| --- | --- | --- |
| [Arize Phoenix documentation](https://arize.com/docs/phoenix) | Implementation | Covers AI observability, traces, datasets, and eval workflows. |
| [OpenAI evaluation best practices](https://platform.openai.com/docs/guides/evaluation-best-practices) | Official | Connects eval growth with production monitoring and continuous evaluation. |
| [OpenTelemetry GenAI semantic conventions repository](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai) | Standard | Provides a shared vocabulary for GenAI spans, metrics, events, model providers, agents, and MCP. |

## Adding Sources

Use this format:

```text
Title:
URL:
Source type:
Topic:
Why it matters:
Production implication:
Claim this supports:
```
