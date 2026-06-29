# Tool Policy Simulator Lab

This lab teaches a core agent design lesson:

> The model can propose a tool call, but the application must authorize it.

The lab uses a small set of proposed tool calls and a deterministic policy engine. It does not require an LLM.

## What You Will Learn

- How to classify tool risk
- How to separate model proposal from execution authority
- How to require approval for side effects
- How to block unsafe or unauthorized tool calls
- How policy failures become eval cases

## Run

From the repo root:

```bash
python3 labs/tool-policy-simulator/policy_simulator.py
```

## Files

```text
labs/tool-policy-simulator/
├── README.md
├── policy_simulator.py
└── data/
    └── tool_calls.jsonl
```

## Exercise

1. Run the simulator.
2. Inspect which proposed calls are allowed, blocked, or require approval.
3. Add one new write tool call.
4. Add one new policy rule.
5. Re-run and explain whether the policy behavior is correct.

## Design Questions

- Which tool calls should never be fully autonomous?
- Which arguments need schema validation?
- Which calls require user ownership checks?
- Which calls require human approval?
- How would you audit a bad tool call after the fact?

## Production Connection

In production, this policy layer should sit outside the model. Prompt instructions alone are not a permission system.
