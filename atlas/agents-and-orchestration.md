# Atlas: Agents And Orchestration

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers systems where the model takes actions: calling tools, controlling flow, remembering state, and operating under supervision.

## Tool Use

Giving a model tools turns text generation into action, and every tool is a new failure surface: wrong tool, wrong arguments, wrong sequence, or a correct call whose side effects the model did not anticipate. The design is decided by how you scope each tool's authority, how you validate arguments before execution, and whether failed calls feed back into the loop in a form the model can recover from.

Coverage: [Covered](../patterns/agent-tool-use.md)

## MCP And Tool Gateways

As tool counts grow, ad hoc integrations become unmaintainable, and the Model Context Protocol standardizes how models discover and call tools. A gateway in front of tool servers centralizes authentication, authorization, rate limiting, and audit. The design is decided by how many tools and clients you must connect, where trust boundaries sit between model, gateway, and tool servers, and how you keep a third-party tool server from becoming an injection channel.

Coverage: [Covered](../patterns/mcp-tool-gateway.md)

## Multi-Agent Patterns

Splitting work across multiple agents buys isolation and parallelism: an orchestrator that plans, subagents with narrow tool sets and clean context windows. It also multiplies token cost and introduces coordination failures, where agents duplicate work, contradict each other, or lose critical context at handoff. The design is decided by whether the task genuinely decomposes, how much context each handoff must carry, and whether a single agent with better tools would be simpler.

Coverage: (planned)

## Planning And Control Flow

The central architectural choice is who controls the flow: a fixed workflow where code decides the steps and the model fills them in, or an agent loop where the model decides what to do next. Agent loops handle open-ended tasks but are harder to bound, test, and debug. The design is decided by how predictable the task structure is, the cost of an unbounded loop, and whether you can define stopping conditions the system actually respects.

Coverage: [Covered](../decision-guides/agents-vs-workflows.md)

## Memory Systems

Agents that persist across sessions need memory: what to store, how to retrieve it at the right moment, and when to forget. Memory compounds errors, because a wrong fact written today poisons every future session that retrieves it, and it concentrates sensitive data in one queryable place. The design is decided by what the product genuinely needs remembered, how memories are validated before being written, and how a user inspects and corrects what the system believes about them.

Coverage: (planned)

## Computer Use

Agents that drive a screen with screenshots, clicks, and keystrokes can operate software with no API, at the price of the slowest and least reliable action loop in the field. Every click is a guess about pixel coordinates, and the environment changes under the agent. The design is decided by whether an API or structured integration exists for the same task, how you sandbox the machine the agent controls, and which actions require a human to confirm.

Coverage: (planned)

## Sandboxing And Execution Isolation

An agent that executes code or shell commands must do it somewhere a mistake or an injected instruction cannot reach production. Sandboxing bounds the blast radius with isolated environments, restricted filesystems and networks, and non-production credentials. The design is decided by what the agent legitimately needs to touch, the isolation technology you can operate, and the assumption that some fraction of agent actions will be adversarial because their inputs were.

Coverage: [Covered](../security/tool-abuse.md)

## Human-In-The-Loop

Some actions should not execute without a person: the design problem is deciding which ones, and building a review queue that does not become a rubber stamp. Route too much to humans and they stop reading; route too little and the automation's worst outputs ship. The design is decided by the cost asymmetry of each action's failure, confidence signals good enough to route on, and whether reviewer decisions feed back into improving the routing.

Coverage: [Covered](../patterns/human-review-queue.md)
