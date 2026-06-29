# Agents vs Workflows

Last reviewed: 2026-06-29

## Problem

Teams often call every multi-step LLM system an agent. That hides an important design distinction.

Workflows use predefined code paths. Agents let the model dynamically choose steps and tools.

This distinction matters because agents add flexibility, but also cost, latency, unpredictability, and compounding failure risk.

## Short Answer

Use workflows when the path is known.

Use agents when the path cannot be known ahead of time, the task has clear success criteria, and the system can safely recover from mistakes.

## Decision Table

| Requirement | Prefer workflow | Prefer agent |
| --- | --- | --- |
| Known sequence of steps | Yes | No |
| Need predictable behavior | Yes | No |
| Open-ended investigation | No | Yes |
| Unknown number of steps | No | Yes |
| High-risk side effects | Yes | Only with approval |
| Strict latency budget | Yes | Usually no |
| Clear automated verification | Either | Yes |
| Need human checkpoints | Either | Yes |

## Workflow Examples

- Classify request, retrieve docs, generate answer, validate output
- Extract fields, validate schema, write to database
- Summarize ticket, score urgency, route to queue
- Run evaluator-optimizer loop for a bounded writing task

## Agent Examples

- Investigate an unknown production issue using logs, docs, and dashboards
- Fix a coding task by editing files and running tests
- Research a topic across multiple sources with unknown search depth
- Operate a browser to complete a task with changing page state

## Design Questions

Ask:

- Can we write the steps in code?
- Does the model need to decide what to do next?
- How many steps can it take?
- What tools can it use?
- How do we know it succeeded?
- What happens if it gets stuck?
- What actions need approval?

## Failure Modes

Workflow failures:

- Too rigid for edge cases
- Bad branch conditions
- Hard-coded assumptions break as tasks change

Agent failures:

- Tool loops
- Wrong tool selection
- Compounding errors
- High cost
- Harder debugging
- Unsafe side effects
- Inconsistent user experience

## Evaluation Strategy

For workflows:

- Test each step
- Test branch decisions
- Test end-to-end outputs

For agents:

- Evaluate full traces
- Score tool selection
- Score argument correctness
- Score stop behavior
- Test sandboxed failure recovery
- Test approval boundaries

## Practical Rule

Start with a workflow. Move to an agent only when a workflow cannot handle the task and evals show the agent improves outcomes enough to justify the added risk.

## Further Reading

- [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Agent Tool-Use System Design](../patterns/agent-tool-use.md)
