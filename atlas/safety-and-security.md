# Atlas: Safety And Security

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers what an attacker or an unlucky user can make the system do, and what the system can leak, break, or say that it should not.

## Prompt Injection

Any text the model reads can carry instructions, and the model cannot reliably tell data from commands: a retrieved document, a web page, or an email can redirect the system that processes it. There is no known complete fix, so the defense is architectural. The design is decided by which untrusted content reaches the model, what authority the model holds when it reads that content, and containment layers that limit what a successfully injected model can actually do.

Coverage: [Covered](../security/prompt-injection.md)

## Data Leakage

AI systems concentrate sensitive data in new places: prompts and traces in logs, user content in third-party API calls, proprietary data in fine-tunes, and cross-tenant bleed through shared retrieval indexes or caches. The design is decided by where data crosses trust boundaries in your pipeline, tenant isolation in every store the model reads, retention and redaction policy for traces, and the terms under which providers may retain or train on your traffic.

Coverage: [Covered](../security/data-leakage.md)

## Tool Abuse And Excessive Agency

A model with tools can be manipulated into destructive actions, and it can also just make a mistake with the same result: deleting data, sending messages, spending money. The vulnerability is granting authority the task did not require. The design is decided by least-privilege scoping of every tool, which actions are irreversible and therefore need confirmation, and rate limits and anomaly detection that bound the damage of a compromised loop.

Coverage: [Covered](../security/tool-abuse.md)

## Embedding And Vector Store Weaknesses

Vector stores are databases that security reviews forget: embeddings can be partially inverted to recover source text, indexes often skip the access controls the source documents had, and a poisoned document plants content that retrieval will faithfully deliver to the model. The design is decided by treating embeddings as the data they encode, enforcing document-level permissions at query time, and validating what enters the index.

Coverage: [Covered](../security/vector-embedding-weaknesses.md)

## Supply Chain

An AI system inherits risk from everything it pulls in: model weights from public hubs, datasets of unknown provenance, prompt templates and MCP servers from third parties, and the fast-moving dependency tree of the serving stack. A malicious or compromised component executes inside your trust boundary. The design is decided by provenance verification for models and datasets, review gates for third-party tools and servers, and pinning and scanning the same way you would for any other dependency, plus registries that know what is deployed.

Coverage: (planned)

## Content Safety

Systems that generate text for users can produce harmful, off-brand, or legally risky output, and the tolerance varies wildly by product: a coding tool and a children's education app do not share a policy. Moderation layers, refusal behavior, and output filtering each catch different failures and each add latency and false positives. The design is decided by an explicit written policy for your product, where in the pipeline enforcement sits, and how misfires are measured and appealed.

Coverage: (planned)

## Compliance And Audit

Regulated deployments must answer questions the base system does not ask: who approved this model, what data trained or prompted it, why did it make this decision, and can you reproduce the exact output a customer complained about. Frameworks like the EU AI Act and NIST AI RMF turn these into obligations. The design is decided by which regimes apply to your deployment, the traceability to reconstruct any decision from logged prompt, model version, and retrieved context, and retention that satisfies audit without hoarding sensitive data.

Coverage: (planned)
