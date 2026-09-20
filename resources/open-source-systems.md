# Open-Source Systems Worth Reading

Last reviewed: 2026-09-21

Curated, capped at 15 entries. These are real production systems whose source code teaches more than most writeups. Read them to steal designs, not just to use them.

## Inference And Serving

- [vLLM](https://github.com/vllm-project/vllm): the reference implementation of PagedAttention and continuous batching; informs every self-hosted serving decision and is the codebase to read to understand KV cache management.
- [SGLang](https://github.com/sgl-project/sglang): serving engine built around RadixAttention prefix caching; informs how much shared-prefix traffic changes serving economics.
- [llama.cpp](https://github.com/ggml-org/llama.cpp): CPU-first inference with the most practical quantization implementations anywhere; informs quantization format choices and what edge deployment really requires.
- [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM): NVIDIA's compiled inference stack; informs what peak GPU performance costs in build complexity versus vLLM's flexibility.
- [Ollama](https://github.com/ollama/ollama): local model runtime with a clean model-packaging design; informs how to make self-hosted models operable by people who are not infrastructure engineers.

## Routing And Gateways

- [LiteLLM](https://github.com/BerriAI/litellm): a proxy normalizing 100+ provider APIs with routing, fallbacks, and spend tracking; informs multi-provider portability design and is a catalog of how provider APIs actually differ.

## Orchestration And Agents

- [LangGraph](https://github.com/langchain-ai/langgraph): graph-based agent orchestration with checkpointing and human-in-the-loop interrupts; informs how to make agent state durable and resumable.
- [LlamaIndex](https://github.com/run-llama/llama_index): the broadest collection of retrieval and indexing strategies in one codebase; informs chunking and index-structure choices by letting you read dozens of implementations side by side.
- [DSPy](https://github.com/stanfordnlp/dspy): programs, not prompts, with optimizers that tune prompts against metrics; informs whether prompt engineering in your pipeline can become a compilation step.

## Evaluation And Observability

- [Ragas](https://github.com/explodinggradients/ragas): reference implementations of RAG metrics like faithfulness and context precision; informs what to measure in retrieval pipelines and how judge-based metrics are actually computed.
- [promptfoo](https://github.com/promptfoo/promptfoo): config-driven eval harness with CI integration and red-teaming plugins; informs how to wire regression gates into a deploy pipeline.
- [Langfuse](https://github.com/langfuse/langfuse): open-source LLM tracing and evaluation platform; informs trace schema design, and self-hosting it answers the observability data-residency question.

## Retrieval Infrastructure

- [pgvector](https://github.com/pgvector/pgvector): vector search inside Postgres; informs the vector-DB-versus-existing-database decision, and its HNSW implementation is compact enough to actually read.
- [Qdrant](https://github.com/qdrant/qdrant): a dedicated vector database in Rust with filtered search done properly; informs what a purpose-built vector store buys over a bolted-on index.

## Guardrails

- [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails): programmable input, output, and dialog rails; informs where policy enforcement can sit in the request path and what rail latency costs.
