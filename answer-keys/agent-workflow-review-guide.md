# Agent Workflow Review Guide

## Strong Answer Checklist

- Starts with workflow where steps are known
- Uses agentic behavior only for open-ended investigation
- Separates model proposal from tool authorization
- Classifies tools by risk level
- Requires approval for side effects
- Defines step, cost, retry, and time budgets
- Logs every tool call and policy decision
- Evaluates tool choice, arguments, stop behavior, and final output
- Handles tool errors and partial results
- Starts rollout in suggestion mode

## Common Weaknesses

- Gives the model unrestricted tools
- Treats prompt instructions as security controls
- Omits idempotency for write tools
- Does not define stop criteria
- Evaluates only final answer, not trace behavior
- Skips human approval for high-risk actions

## Good Tradeoff Discussion

A strong submission should compare:

- Workflow vs agent
- Read tools vs write tools
- Strict approval vs speed
- Single model vs model routing
- Full tool output vs summarized tool output
- Autonomy budget vs task completion
