# Assignments

Assignments are design problems. They should force tradeoffs and make learners produce engineering artifacts.

## Current Assignments

1. [Design Enterprise RAG](./design-enterprise-rag.md)
2. [Design Agent Workflow](./design-agent-workflow.md)

## Required Submission Format

Every assignment response should include:

- Problem statement
- Assumptions
- Requirements and non-goals
- Architecture diagram
- Data flow
- Component responsibilities
- Design decisions and tradeoffs
- Failure modes
- Evaluation plan
- Observability plan
- Security review
- Cost and latency budget
- Rollout plan

## Review Rubric

Use this rubric for self-review or peer review.

| Dimension | Strong answer |
| --- | --- |
| Requirements | Separates user goals, system constraints, and non-goals |
| Architecture | Defines clear component boundaries and data flow |
| Tradeoffs | Explains why alternatives were accepted or rejected |
| Failure modes | Covers realistic production failures, not just generic risks |
| Evaluation | Tests task success, safety, regressions, and edge cases |
| Observability | Captures enough traces to debug failures |
| Security | Puts permissions and validation outside the model |
| Cost and latency | Budgets each major step in the request path |
| Rollout | Uses staged release, monitoring, and rollback criteria |
