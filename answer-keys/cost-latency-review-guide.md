# Cost And Latency Review Guide

## Strong Answer Checklist

- Budgets every stage, not just model generation
- Measures p50, p95, and p99 latency
- Tracks cost per successful task
- Includes token, retrieval, reranking, tool, retry, and fallback costs
- Uses caching only where permissions and freshness allow
- Sets hard limits for agent loops and retries
- Explains streaming as perceived-latency improvement, not cost reduction

## Common Weaknesses

- Optimizes for cheapest model call instead of successful outcome
- Ignores reranking and tool latency
- Uses long context without measuring token growth
- Omits fallback cost
- Ignores cache invalidation and tenant boundaries

## Good Tradeoff Discussion

A strong submission should compare:

- Larger model vs model cascade
- Reranking quality vs latency
- Long context vs retrieval
- Streaming vs total completion time
- Cache hit rate vs data freshness
- Human review cost vs automation risk
