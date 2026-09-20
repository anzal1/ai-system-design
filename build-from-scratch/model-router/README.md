# Build A Model Router From Scratch

One file, pure Python stdlib, no network. You build the four mechanisms every production router contains: request classification, cost and latency aware selection, fallback chains, and a budget governor.

## Problem

Production AI traffic is not uniform. Most requests are cheap classification or extraction work. A minority need long-context reasoning. Sending everything to the strongest model wastes money on the easy majority. Sending everything to the cheapest model silently fails the hard minority.

Routing is a portfolio problem. You hold a set of assets (models) with different cost, latency, and quality profiles, and you allocate each unit of demand (a request) to the cheapest asset that still meets its constraints. Like any portfolio, you also hedge: providers fail, so every route needs a fallback, and spend needs a hard cap that overrides greedy allocation.

## What You Build

- A model catalog where prices, latencies, quality tiers, and failure rates are plain data
- A rule-based complexity scorer that maps request features to a required quality tier
- A selector that picks the cheapest eligible model inside the request's latency budget
- Fallback chains that never downgrade quality on failure, with failed calls still billed
- A budget governor with a soft degradation band (downgrade tier-2 work) and a hard cap (reject non-critical work)
- A demo that routes 300 mixed requests and prints per-model spend, latency percentiles, fallback counts, and the saving against an all-on-large baseline

## How It Works

1. Each request is scored 0 to 10 from cheap features: task length, reasoning verbs, synthesis verbs, embedded code, expected output length, input context size. The score maps to a required quality tier.
2. The budget governor may adjust the tier. Past 80 percent of budget it downgrades tier-2 requests to tier 1. Past 100 percent it rejects anything not marked critical.
3. The selector filters the catalog to models at or above the tier, then to models whose estimated latency fits the request budget, and picks the cheapest. If nothing fits the latency budget it picks the fastest eligible model, because a slow correct answer beats no answer.
4. Execution walks the fallback chain on simulated failures. A failed call bills its input tokens and adds base latency, because in production a timed-out request is not free.

## Design Decisions

- **Rules before classifiers.** A rule-based scorer is debuggable, versionable, and explains every routing decision. Move to a learned classifier only when rules stop explaining routing mistakes, and keep the rules as a floor.
- **Fallback never downgrades.** Chains only move sideways or up in quality. A provider failure should degrade latency and cost, never correctness. The two same-tier providers exist purely as hedges against each other.
- **The governor acts on tier, not on model.** Downgrading the required tier lets the selector re-run its normal logic instead of hardcoding a panic model. Policy and mechanism stay separate.
- **Failed calls are billed.** Retries and fallbacks are a real cost center. Pricing only successful calls understates spend exactly when the system is under stress.
- **Critical flag bypasses the governor.** Some flows (payment disputes, safety escalations) must complete even over budget. The cap can overshoot by at most one request, and the assert encodes that bound.

## Failure Modes

- The scorer under-scores a hard request and a weak model answers confidently and wrongly. Cost falls while silent failure rate rises. This is the classic routing failure, and it is invisible without per-route evals.
- The latency estimate drifts from reality (provider slows down) and the selector keeps picking a model that no longer fits its budget.
- Correlated provider failures exhaust a chain. Two providers on the same underlying model or region fail together.
- The budget governor turns a spend problem into an availability problem at the worst time, at the end of the billing window when traffic is often highest.
- Keyword rules are gameable: a user who writes "step by step" gets routed to the expensive model.

## What Production Systems Do Differently

- Classification is often a small learned model or a cheap LLM call, trained on labeled routing outcomes rather than hand rules.
- Quality tiers come from per-task eval suites, not a hand-assigned integer. A model earns a route by passing that route's quality gate.
- Selection includes live provider health (error rates, queue depth) and per-tenant policy (data residency, compliance), not just price.
- Budgets are hierarchical (per tenant, per feature, per org) and enforced with rate limits and admission control, not a single scalar.
- Every decision is logged with the signals that produced it, feeding an offline pipeline that retrains or re-tunes the router.
- Cascades are common: try cheap, validate, escalate on low confidence. This file routes once; a cascade routes on the response too.

## Run It

```bash
python3 model_router.py
```

Runs in under a second. Prints per-model spend and traffic, latency percentiles, fallback counts, governor actions, and the saving versus an all-on-large baseline. Inline asserts validate the scorer ordering, tier mapping, cheap-model preference, latency-forced selection, budget bound, and that the portfolio beats the single-model baseline on cost.

## Exercises

1. Add a fifth catalog entry, a local model with near-zero price, high latency, and quality 1, and watch where the selector sends it. Explain why latency budgets keep it off the hot path.
2. Change the failed-call billing to also bill a fraction of output tokens (partial generation before a timeout) and measure how much reported spend rises under a doubled failure rate.
3. Implement a cascade: route tier-2 requests to nano first, simulate a validation check that fails 30 percent of the time, and escalate failures to mini. Compare total cost and p95 latency against direct tier-2 routing.
4. Make the governor budget hierarchical: a per-tenant budget inside the global one. Generate traffic where one tenant is 10x noisier and show the noisy tenant hits its cap without starving the others.
5. Break the router on purpose: craft requests that score low but need tier 3 (short adversarial questions with no marker words). Then design one extra signal that catches your own attack.

## Further Reading

- [Anthropic: choosing the right model](https://docs.claude.com/en/docs/about-claude/models/choosing-a-model) explains the official framing of the cost, latency, and capability trade-off this router automates.
- [RouteLLM (Ong et al., 2024)](https://arxiv.org/abs/2406.18665) is the widely cited paper on learned routing between strong and weak models with cost-quality trade-off curves, the natural next step after rule-based scoring.
- [FrugalGPT (Chen et al., 2023)](https://arxiv.org/abs/2305.05176) introduced LLM cascades with budget constraints and shows the same portfolio argument with measured numbers.
- [../../patterns/model-routing.md](../../patterns/model-routing.md) is the companion pattern page covering routing signals, evaluation strategy, and observability for the production version of this design.
