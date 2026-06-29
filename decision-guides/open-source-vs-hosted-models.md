# Open-Source vs Hosted Models

Last reviewed: 2026-06-29

## Problem

Teams need to decide whether to use hosted model APIs or run open-weight models themselves.

This is not only a model-quality decision. It affects latency, privacy, compliance, cost, reliability, operations, and hiring.

## Short Answer

Use hosted models when speed of development, capability, and reliability matter most.

Use self-hosted open-weight models when control, data locality, cost at scale, or customization matter enough to justify operational complexity.

## Decision Table

| Requirement | Hosted model | Self-hosted model |
| --- | --- | --- |
| Fastest development | Strong | Weak |
| Best frontier capability | Usually strong | Varies |
| Data locality control | Depends | Strong |
| Operational simplicity | Strong | Weak |
| Custom serving optimization | Weak | Strong |
| Predictable unit economics at scale | Depends | Strong if utilized |
| Compliance control | Depends | Strong |
| Small team | Usually better | Risky |

## Hosted Model Strengths

- Fast integration
- Strong capabilities
- Managed reliability
- No inference infrastructure
- Faster access to new models
- Built-in tooling in some providers

## Hosted Model Risks

- Provider lock-in
- Pricing changes
- Rate limits
- Data retention constraints
- Regional availability
- Less control over model internals
- Behavior changes across model versions

## Self-Hosted Strengths

- Data control
- Custom deployment
- Potential cost advantage at high utilization
- Model customization
- Lower dependency on external providers
- Deployment in restricted environments

## Self-Hosted Risks

- Serving complexity
- GPU capacity planning
- Lower model quality for some tasks
- Reliability burden
- Security patching
- Inference optimization work
- Team expertise requirements

## Evaluation Strategy

Compare models on:

- Task success
- Safety behavior
- Latency
- Cost per successful task
- Context length needs
- Tool-use reliability
- Structured output reliability
- Operational risk

Do not compare only benchmark scores.

## Practical Rule

Start hosted unless you have a clear reason not to. Move specific workloads to self-hosted models when evals and economics justify the operational burden.

## Further Reading

- [Model Routing](../patterns/model-routing.md)
