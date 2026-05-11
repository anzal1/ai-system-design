# Content Standard

This project is only useful if the quality bar stays high.

AI System Design is not trying to publish a lot of content. It is trying to publish content that helps engineers make better design decisions.

## Required Shape

Most pages should follow this structure unless there is a clear reason not to:

```text
# Title

## Problem
## When To Use
## Architecture
## Data Flow
## Core Components
## Design Decisions
## Failure Modes
## Evaluation Strategy
## Observability
## Cost And Latency
## Security Concerns
## Implementation Sketch
## Further Reading
```

Shorter frontier notes may use:

```text
# Title

## What Changed
## Why It Matters
## Production Impact
## What Is Still Unproven
## Sources
```

## Acceptance Criteria

A page is ready when it:

- Explains a system design decision, pattern, failure mode, or evaluation method
- States assumptions clearly
- Uses concrete architecture language
- Includes tradeoffs, not just recommendations
- Includes failure modes
- Includes evaluation or validation strategy
- Includes cost, latency, security, or operational concerns where relevant
- Cites primary, official, academic, or production-relevant sources

## Rejection Criteria

Do not submit:

- Generic AI introductions
- Prompt hack lists
- Unsourced claims
- Copy-paste paper summaries
- Vendor marketing
- "Top 10 tools" posts
- News without production interpretation
- Content that explains what a term means but not how it affects system design

## Source Hierarchy

Prefer sources in this order:

1. Official docs, standards, model/system cards, and reference architectures
2. Peer-reviewed or widely cited research
3. Open-source implementations and benchmark repos
4. Engineering blogs from teams that built or operated the system
5. Practitioner posts with concrete evidence

Avoid relying on thin summaries, SEO articles, social posts, or vendor claims unless they are clearly labeled as opinion.

## Writing Style

Use direct engineering prose.

Good:

> Add reranking when first-stage retrieval has high recall but poor ordering. Measure whether it improves answer faithfulness and citation support before accepting the added latency.

Bad:

> Reranking supercharges your AI app and unlocks next-generation intelligence.

## Diagrams

Use Mermaid diagrams when a data flow or architecture would be easier to understand visually. Keep diagrams simple enough to review in a pull request.

## Freshness

AI infrastructure changes quickly. Pages that depend on current model capabilities, provider APIs, pricing, or benchmarks should include a `Last reviewed` line near the top.
