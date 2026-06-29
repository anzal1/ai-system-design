# OpenTelemetry GenAI Conventions

Last reviewed: 2026-06-29

## What Changed

OpenTelemetry has been developing GenAI semantic conventions covering model calls, spans, metrics, events, agents, providers, and MCP-related telemetry.

## Why It Matters

AI observability is fragmented. Teams often log prompts, retrieval, tools, and model usage in incompatible ways. Shared conventions can make traces easier to compare across services, providers, and observability tools.

## Architecture Impact

GenAI telemetry conventions affect:

- Trace schemas
- Model call spans
- Agent spans
- Tool-call traces
- Token and cost metrics
- Provider-specific attributes
- Cross-service debugging

## Evaluation Impact

Telemetry standards do not replace evals, but they make eval data easier to connect to production traces.

Useful connections:

- Trace ID to eval example
- Model version to regression report
- Prompt version to failure cluster
- Tool-call span to tool correctness score

## Security Impact

Standard telemetry can accidentally standardize sensitive fields. Teams still need redaction, access control, and retention policy.

## Cost And Latency Impact

Standard model-call metrics make it easier to track:

- Token usage
- Request latency
- Streaming behavior
- Provider errors
- Retry and fallback cost

## What Is Still Unproven

- Which conventions will stabilize across vendors
- How consistently AI frameworks will emit compatible telemetry
- How teams will balance debuggability with sensitive prompt and context data

## Recommendation

**Trial.**

Adopt the vocabulary where useful, but keep product-specific fields for retrieval, evals, policy decisions, and user feedback.

## Sources

- [OpenTelemetry GenAI semantic conventions repository](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai)
- [AI Observability](../patterns/ai-observability.md)
