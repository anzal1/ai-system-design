# Syllabus

## Course Title

AI System Design: Designing Production AI Systems

## Course Format

This is an open-source, self-paced engineering course.

Each module combines:

- Conceptual guide
- Architecture pattern
- Decision guide
- Hands-on lab or design assignment
- Evaluation and observability requirements
- Security and failure-mode review

## Target Audience

This course is for engineers and builders who can already design normal software systems but need a rigorous path into AI-native system design.

Primary audience:

- Backend engineers
- ML engineers
- Staff and senior engineers
- AI startup founders
- Platform and devtool engineers

Secondary audience:

- Engineering managers reviewing AI projects
- Interview candidates preparing for AI system design rounds
- Product-minded researchers moving toward applied systems

## What Students Will Build

Students will design and critique:

- A RAG-based document Q&A system
- An eval pipeline
- A tool-using agent workflow
- A secure support assistant
- A production observability plan
- A cost and latency budget

Students will also run at least one local retrieval evaluation lab.

## Grading Philosophy

This course does not grade by memorization.

Good work is judged by:

- Clear requirements
- Explicit assumptions
- Correct architecture boundaries
- Real tradeoffs
- Concrete failure modes
- Measurable eval strategy
- Useful observability plan
- Security controls outside the model
- Cost and latency reasoning

## Module Schedule

### Week 1: Foundations

Topics:

- AI system design vs traditional system design
- Probabilistic behavior
- Context as a design surface
- Product correctness vs model output

Deliverable:

- One-page AI feature design with assumptions and failure modes

### Week 2: LLM Application Architecture

Topics:

- Orchestration layer
- Prompt and model versioning
- Structured output validation
- Retries, fallbacks, and release gates

Deliverable:

- Trace schema for an LLM request

### Week 3: RAG Systems

Topics:

- Ingestion
- Chunking
- Embeddings
- Hybrid retrieval
- Reranking
- Citations
- Freshness and permissions

Deliverable:

- RAG retrieval lab results and failure analysis

### Week 4: Evals

Topics:

- Golden datasets
- Regression tests
- LLM-as-judge
- Human review
- Offline vs online evals

Deliverable:

- Eval plan for a RAG or agent system

### Week 5: Observability

Topics:

- Traces
- Prompt and context logging
- Token and latency accounting
- Feedback loops
- Debugging semantic failures

Deliverable:

- Observability plan with redaction rules

### Week 6: Agents And Tool Use

Topics:

- Workflow vs agent
- Tool registry
- Tool-call validation
- Human approval
- Autonomy budgets
- Side-effect safety

Deliverable:

- Tool-use design assignment

### Week 7: Security And Safety

Topics:

- Prompt injection
- Indirect prompt injection
- Sensitive data leakage
- Insecure tool execution
- Excessive agency

Deliverable:

- Threat model and adversarial eval set

### Week 8: Cost, Latency, And Scaling

Topics:

- Latency budgets
- Model routing
- Caching
- Batching
- Streaming
- Hosted vs open-source inference

Deliverable:

- Cost and latency budget for a production AI feature

### Week 9: Case Studies

Topics:

- Customer support agents
- Enterprise document Q&A
- AI search
- Coding assistants

Deliverable:

- Design review of a complete AI system

### Week 10: Frontier To Production

Topics:

- Reading papers and model releases
- Evaluating new frameworks
- Separating hype from production value
- Updating architecture guidance

Deliverable:

- Frontier note with adopt/watch/ignore recommendation

## Capstone

Design a production AI system end to end.

The capstone must include:

- Problem statement
- Users and constraints
- Architecture diagram
- Data flow
- Model and retrieval choices
- Eval plan
- Observability plan
- Security review
- Cost and latency budget
- Rollout plan
- Failure-mode analysis

Suggested capstones:

- Enterprise knowledge assistant
- AI customer support agent
- AI research assistant
- AI coding assistant
- AI data analyst
- Voice operations agent
