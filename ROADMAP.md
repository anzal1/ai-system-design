# Roadmap

This roadmap is organized by audience value, not by content volume.

## Phase 1: Repo MVP

Goal: prove that engineers want a serious AI system design knowledge base.

- [x] Define positioning and content standard
- [x] Add initial repo structure
- [x] Publish first canonical pages
- [x] Add GitHub issue templates
- [x] Add first case study
- [x] Add source map
- [x] Add course and syllabus
- [x] Add first runnable lab
- [x] Add first assignments and design review
- [x] Add expanded pattern library
- [x] Add expanded decision guides
- [x] Add security deep dives
- [x] Add additional labs and reference architectures
- [x] Complete Module 2 LLM application architecture
- [x] Complete Module 5 observability and incident response
- [x] Add capstone and answer-key review guides
- [ ] Share for critique with engineering communities

## Phase 2: Core Coverage

Goal: cover the design decisions most teams hit while building production AI features.

- RAG with hybrid retrieval and reranking
- Agent workflows vs autonomous agents
- Model routing and fallback design
- Human-in-the-loop review queues
- Prompt and model version management
- AI observability and tracing
- Evaluation datasets and regression testing
- Prompt injection and data leakage threat models
- Cost and latency budgeting
- MCP and tool integration patterns
- GenAI OpenTelemetry conventions
- Multimodal AI system design
- Long-context architecture tradeoffs

## Phase 2.5: Depth And Breadth Expansion

Goal: make the repo both the deepest and the widest serious resource on AI system design, without becoming a link dump.

- [ ] Build From Scratch track: every core component implemented in pure Python stdlib, runnable offline
  - Layer 1, model substrate: tokenizer, transformer forward pass, KV cache
  - Layer 2, retrieval stack: chunker, BM25, vector index with HNSW-lite, full RAG pipeline
  - Layer 3, serving: model router, token-aware rate limiter, prompt cache, semantic cache
  - Layer 4, control plane: agent loop, eval harness, guardrails
- [ ] Atlas: a complete map of the field, every territory and topic, with honest coverage markers linking to existing pages or marked planned
- [ ] New depth pages: agent memory systems, multi-agent orchestration, streaming and partial results, feedback and data flywheels, fine-tuning pipeline, self-host vs API serving
- [ ] Expanded curated resources: courses and books, production postmortems, benchmarks and datasets, open-source systems worth reading
- [ ] First-hand production case studies from real projects with real numbers

Curation rule that keeps breadth from rotting: every resource entry carries one sentence on why it is worth your time, and no resource page exceeds fifteen entries.

## Phase 3: Case Studies

Goal: teach through realistic system designs.

- AI customer support agent
- Enterprise document Q&A
- Perplexity-style AI search
- Cursor-style code assistant
- Voice AI receptionist
- AI data analyst
- Internal knowledge assistant
- Agentic operations assistant
- Multimodal document processing pipeline

## Phase 4: Frontier Notes

Goal: translate new research, models, tools, and infrastructure into production design implications.

Each frontier note should explain:

- What changed
- Why it matters
- Which architecture decisions it affects
- What remains unproven
- Whether teams should adopt, watch, or ignore it

## Phase 5: Website

Only build a website after the repo shows pull through issues, discussions, PRs, and repeated external references.
