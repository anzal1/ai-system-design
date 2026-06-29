# Maintainers Guide

This repo should stay selective.

## Maintainer Principles

- Prefer fewer strong pages over many weak pages.
- Reject content that does not help a design decision.
- Require sources for factual or current claims.
- Keep hype out of titles and recommendations.
- Push contributors toward failure modes, evals, observability, and security.

## Review Checklist

Before merging, check:

- Does this page solve a real system design problem?
- Are assumptions stated?
- Are tradeoffs explicit?
- Are failure modes realistic?
- Is there an eval strategy?
- Is observability covered?
- Are security and privacy considered?
- Are current claims sourced?
- Does the page fit the repo structure?

## Version Review

Pages involving current model APIs, pricing, standards, or security guidance should include `Last reviewed`.

Review high-change areas quarterly:

- Model routing
- Agents and MCP
- Security risks
- Observability standards
- RAG evaluation
- Frontier notes

## Label Suggestions

Use GitHub labels:

- `topic-request`
- `pattern`
- `source`
- `correction`
- `case-study`
- `lab`
- `security`
- `evals`
- `frontier-note`
- `good-first-issue`
