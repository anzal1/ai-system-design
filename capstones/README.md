# Capstones

The capstone is the final proof that a learner can design a production AI system end to end.

## Required Deliverables

Every capstone must include:

- Problem statement
- Users and constraints
- Requirements and non-goals
- Architecture diagram
- Data flow
- Model strategy
- Retrieval strategy
- Tool strategy
- Evaluation plan
- Observability plan
- Security review
- Cost and latency budget
- Rollout plan
- Failure modes
- Open questions

## Suggested Capstones

- [Enterprise Knowledge Assistant](./enterprise-knowledge-assistant.md)
- AI support agent
- AI search engine
- AI code assistant
- AI data analyst
- Voice operations agent
- Agentic incident-response assistant

## Scoring Rubric

| Dimension | Strong capstone |
| --- | --- |
| Problem | Clear user, task, and constraints |
| Architecture | Components and boundaries are explicit |
| Retrieval | Handles sources, permissions, freshness, and citations |
| Tools | Tool permissions and approval are outside the model |
| Evals | Includes offline, online, regression, and safety evals |
| Observability | Traces can reproduce failures |
| Security | Covers prompt injection, leakage, and side effects |
| Cost/latency | Budgets the full path |
| Rollout | Uses staged release and rollback criteria |
