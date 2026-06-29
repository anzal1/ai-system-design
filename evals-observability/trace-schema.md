# Trace Schema For AI Applications

Last reviewed: 2026-06-29

## Problem

AI failures are hard to debug without structured traces. A user complaint like "the answer was wrong" is not actionable unless the team can inspect the model, prompt, retrieval, tools, validation, and output path.

## Minimum Trace Schema

```json
{
  "trace_id": "trace_123",
  "request_id": "req_123",
  "user_scope": {
    "tenant_id": "tenant_123",
    "role": "support_agent"
  },
  "versions": {
    "prompt": "support-agent-v12",
    "model": "primary-model-2026-06",
    "retrieval": "hybrid-rag-v4",
    "tools": "tool-registry-v8",
    "schema": "answer-schema-v3",
    "policy": "safety-policy-v5"
  },
  "input": {
    "intent": "refund_question",
    "risk_label": "billing"
  },
  "retrieval": {
    "query": "refund after 90 days",
    "chunks": [
      {
        "chunk_id": "doc_refunds:12",
        "score": 0.82,
        "source_id": "doc_refunds"
      }
    ]
  },
  "model": {
    "route": "primary",
    "input_tokens": 2400,
    "output_tokens": 220
  },
  "validation": {
    "schema_passed": true,
    "citation_passed": false,
    "policy_passed": true
  },
  "latency_ms": {
    "retrieval": 310,
    "generation": 1800,
    "validation": 120
  }
}
```

## Trace Categories

### Identity And Scope

Capture tenant, role, entitlement, and feature entry point. Avoid storing raw personal data unless needed and approved.

### Versions

Track every behavior-affecting version: prompt, model, retrieval, tool registry, schema, policy, and eval dataset.

### Retrieval

Store source IDs, chunk IDs, scores, filters, and final context IDs. Store raw text only with redaction and access control.

### Tool Calls

Store tool name, arguments, validation result, approval result, execution result, and side-effect ID.

### Validation

Store structured output validation, business-rule validation, citation checks, safety checks, and refusal checks.

### Outcome

Store final response, feedback, reviewer labels, downstream actions, and user-visible errors.

## Redaction Rules

Separate trace fields into:

- Public metadata
- Internal debug metadata
- Sensitive raw context
- Secrets that should never be logged

## Design Review Questions

- Can a bad answer be reproduced?
- Can we tell whether retrieval, generation, tools, or validation failed?
- Can we compare behavior across versions?
- Can we build eval examples from traces?
- Are sensitive fields access-controlled?

## Further Reading

- [AI Observability](../patterns/ai-observability.md)
- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai)
