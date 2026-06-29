# Assignment: Design Agent Workflow

## Scenario

You are designing an AI operations assistant for a SaaS company. Internal employees can ask it to investigate customer issues, summarize account state, draft support replies, and create follow-up tasks.

The assistant can read from internal systems and propose actions. Some actions require human approval.

## Requirements

- Read customer account state
- Search support history
- Search internal documentation
- Draft a response for a human support agent
- Create a follow-up task after approval
- Escalate risky or ambiguous cases
- Produce a trace of every tool call

## Non-Goals

- Autonomous refunds
- Autonomous account closure
- Direct customer replies without review
- Unrestricted database access
- Multi-agent architecture in the first version

## Constraints

- Customer data is sensitive
- Tool failures are common
- Human support agents need low-friction summaries
- Some requests involve billing or legal risk
- The system must avoid runaway tool loops

## Deliverable

Write a design doc that includes:

1. Workflow diagram
2. Tool registry
3. Permission model
4. Tool-call validation strategy
5. Human approval points
6. Autonomy budget
7. Error handling
8. Evaluation plan
9. Observability plan
10. Security review
11. Rollout plan

## Design Questions

Answer these explicitly:

- Which steps are deterministic workflow steps?
- Which steps require model judgment?
- Which tools are read-only?
- Which tools can cause side effects?
- What actions require approval?
- How do you prevent repeated failed tool calls?
- How do you validate tool arguments?
- How do you replay a trace without repeating side effects?
- What happens if a tool returns sensitive data?
- What makes the system stop?

## Expected Tradeoffs

You should discuss:

- Workflow vs agent
- Read tools vs write tools
- Single model vs model router
- Strict approval vs user experience
- Tool result summarization vs full context
- Small autonomy budget vs task completion rate

## Evaluation Rubric

| Dimension | Strong answer |
| --- | --- |
| Tool boundaries | Separates model proposal from application authorization |
| Safety | Uses least privilege, approval gates, and side-effect logging |
| Evals | Scores tool choice, arguments, stop behavior, and final response |
| Observability | Captures tool list, proposed calls, validation, results, and approvals |
| Error handling | Handles retries, timeouts, unavailable tools, and partial results |
| Rollout | Starts in suggestion mode before enabling actions |

## Stretch Goals

- Add idempotency keys for write tools
- Add a policy simulator
- Add a human review dashboard
- Add adversarial prompt-injection evals
