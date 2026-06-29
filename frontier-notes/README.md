# Frontier Notes

Frontier notes translate new research, model releases, tools, standards, and infrastructure changes into production system design implications.

This folder should not become an AI news feed.

## What Belongs Here

A frontier note belongs here when it changes or challenges a production design decision.

Good topics:

- New model capability that changes routing, latency, cost, or eval strategy
- New agent/tool standard that affects integration architecture
- New security guidance that changes threat modeling
- New evaluation method that changes release gates
- New inference or serving technique that affects scaling
- New retrieval method that affects RAG architecture

Bad topics:

- Generic launch announcements
- Model hype without system implications
- Paper summaries without adoption guidance
- Tool roundups
- Vendor marketing

## Required Format

Each note should include:

```text
# Title

Last reviewed:

## What Changed
## Why It Matters
## Architecture Impact
## Evaluation Impact
## Security Impact
## Cost And Latency Impact
## What Is Still Unproven
## Recommendation
## Sources
```

## Recommendation Labels

Use one of these labels:

- **Adopt:** Strong evidence, clear production value, manageable risk
- **Trial:** Promising, worth testing in controlled systems
- **Watch:** Interesting, but evidence or tooling is immature
- **Ignore For Now:** Mostly hype, unclear value, or high risk

## Review Questions

Before accepting a frontier note, ask:

- Does this change a real system design decision?
- What kind of team or product should care?
- What would we measure before adopting it?
- What could break in production?
- Is the source primary, technical, or evidence-backed?

## Current Priority Areas

- Agent protocols and tool integration
- GenAI observability standards
- RAG evaluation and citation quality
- Prompt injection and tool-use security
- Model routing and smaller-model workflows
- Multimodal system design
- Long-context tradeoffs
