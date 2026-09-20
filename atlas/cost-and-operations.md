# Atlas: Cost And Operations

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers running an AI system as a business and as a production service: modeling cost, controlling spend, observing behavior, and responding when it breaks.

## Cost Modeling

AI unit economics are token economics: cost per request is prompt tokens plus output tokens plus retrieval, reranking, and retries, multiplied across a traffic distribution with a long expensive tail. Averages mislead because a small fraction of requests can dominate spend. The design is decided by modeling cost at the percentiles rather than the mean, attributing spend to features and tenants so you know what is expensive, and knowing your marginal cost before pricing the product.

Coverage: [Covered](../patterns/cost-latency-budgeting.md)

## Caching Layers

The same or similar requests recur, and every layer of caching trades freshness and correctness for cost: provider-side prompt caching for shared prefixes, exact-match response caches, and semantic caches that answer new queries with old responses. Semantic caching is the sharp edge, because a near-match that is actually a different question serves a confident wrong answer. The design is decided by prefix structure in your prompts, tolerance for stale or approximate responses per endpoint, and cache invalidation when prompts, models, or knowledge change.

Coverage: [Covered](../patterns/prompt-caching.md)

## Budgets And Spend Controls

Costs in an AI system are user-triggered and unbounded by default: an agent loop, a retry storm, or one abusive tenant can burn a month's budget in hours. Controls mean per-request token ceilings, per-tenant quotas, spend alerts with someone on the other end, and kill switches that degrade the feature instead of the company. The design is decided by which limits fail gracefully from the user's perspective, how fast anomalous spend is detected, and where the authority to shut things off lives at 3 a.m.

Coverage: [Covered](../patterns/cost-latency-budgeting.md)

## Capacity Planning

Whether you buy tokens or run GPUs, capacity is a forecast: provider rate limits are a ceiling you must reserve ahead of growth, and self-hosted fleets take procurement lead times measured in months. Traffic grows in steps when features launch, not smoothly. The design is decided by forecasting token volume rather than request volume, the headroom your latency SLO requires, and a burst strategy of queueing, shedding, or overflow to a secondary provider that you have tested before you need it.

Coverage: (planned)

## Observability

You cannot debug what you did not record: AI observability means tracing every request end to end, with prompt version, model version, retrieved documents, tool calls, token counts, latency per stage, and the quality signals attached. Standards like OpenTelemetry GenAI conventions make traces portable across tools. The design is decided by a trace schema rich enough to reconstruct any bad answer, sampling and redaction that balance detail against cost and privacy, and dashboards that surface quality drift, not just uptime.

Coverage: [Covered](../patterns/ai-observability.md)

## Incident Response

AI incidents include a class ordinary runbooks miss: quality regressions with no error rate, a provider model update that changed behavior overnight, injection attacks in progress, and a cache serving wrong answers at scale. Detection is harder because the system stays green while being wrong. The design is decided by defining what counts as an AI incident before one happens, playbooks for rollback of prompts, models, and indexes independently, and postmortems that turn each incident into eval cases and monitors.

Coverage: [Covered](../patterns/ai-incident-response.md)

## SLOs For Probabilistic Systems

Classic SLOs assume a binary success, but an AI request can return 200 OK and a wrong answer, so quality itself needs objectives: faithfulness rates, resolution rates, judge scores over sliding windows, with error budgets that gate releases. The unsolved part is measurement noise, because quality metrics move for reasons other than regressions. The design is decided by which quality metric is stable enough to promise, the window and threshold that separate signal from noise, and what the organization actually does when the budget is spent.

Coverage: (planned)
