# Atlas: Model Layer

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers choosing models, adapting them, and keeping the option to change your mind later.

## Model Selection

Picking the base model for a product is a multi-objective decision: quality on your task, latency, cost per request, context length, tool-use reliability, and license terms. Public benchmarks narrow the field but do not decide it, because they rarely match your task distribution. The design is decided by an eval set built from your own traffic, run against a shortlist, with cost and latency measured at your real prompt sizes.

Coverage: (planned)

## Model Routing

Not every request deserves the most capable model. Routing sends easy requests to cheap fast models and hard ones to expensive models, using rules, classifiers, or cascade patterns that escalate on failure. The design is decided by how separable easy and hard requests are in your traffic, the cost of a misroute in each direction, and whether you can detect a bad cheap-model answer before the user does.

Coverage: [Covered](../patterns/model-routing.md)

## Fallbacks And Retries

Model APIs fail, rate-limit, and degrade, so a production system needs a policy for what happens next: retry with backoff, fall back to another model, or degrade the feature gracefully. The hard part is that a fallback model gives different answers, so failover is a quality event, not just an availability event. The design is decided by your availability target, which requests are safe to retry, and whether the fallback path is tested under real load.

Coverage: [Covered](../patterns/retries-fallbacks-release-gates.md)

## Fine-Tuning

Fine-tuning changes model behavior with your data: style, format compliance, domain vocabulary, and task-specific skill. It does not reliably add knowledge, it creates a model artifact you must version and re-evaluate, and it competes with prompting and retrieval as the cheaper first move. The design is decided by whether prompting has plateaued on a measured eval, whether you have thousands of quality examples, and whether you can absorb the retraining cost every time the base model changes.

Coverage: [Covered](../decision-guides/rag-vs-finetuning.md)

## Distillation

Distillation trains a small model on the outputs of a large one, capturing much of the behavior at a fraction of the serving cost. It works best on narrow, high-volume tasks where the large model's outputs define the target distribution. The design is decided by task narrowness, the volume that justifies the training investment, the quality gap you can tolerate, and provider terms of service on training against model outputs.

Coverage: (planned)

## Quantization

Quantization shrinks model weights to lower precision so the model fits on cheaper hardware and serves faster. The quality loss is real but uneven: some tasks degrade gracefully at 4-bit while others break, and the only trustworthy measurement is your own eval set on the quantized artifact. The design is decided by the memory budget of your target hardware, the throughput you need, and the measured quality delta on your tasks rather than on perplexity.

Coverage: (planned)

## Open Weights Vs Hosted Models

Self-hosting open-weight models buys data control, cost predictability at scale, and independence from provider roadmaps; it costs you GPU operations, quality gaps on frontier tasks, and the burden of keeping up with a fast-moving serving stack. The design is decided by data residency requirements, sustained volume that beats API pricing, in-house infrastructure capability, and how far behind the frontier your task allows you to be.

Coverage: [Covered](../decision-guides/open-source-vs-hosted-models.md)

## Multi-Provider Portability

Building against one provider's API couples you to their pricing, deprecation schedule, and outages. Portability means an abstraction layer over providers, prompts that do not depend on one model's quirks, and evals that gate a provider swap. The catch is that prompts are not portable in practice, so the abstraction only pays off if you maintain per-model prompt variants and test them. The design is decided by how much provider risk you carry, how often you actually expect to switch, and whether the abstraction's lowest-common-denominator API costs you provider-specific features you need.

Coverage: (planned)
