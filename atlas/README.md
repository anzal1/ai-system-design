# The AI System Design Atlas

Last reviewed: 2026-09-21

The Atlas is the breadth layer of this repo. The patterns, decision guides, and case studies go deep on individual problems. The Atlas answers a different question: what does the whole field of AI system design contain, and how much of it does this repo cover today?

Every territory of the field appears here. Every topic gets one tight paragraph: what the problem is and what decides the design. Every topic carries an honest coverage marker.

## Coverage Markers

- `Covered` links to an existing repo page that treats the topic in depth.
- `(planned)` means the topic matters, the repo does not yet have a dedicated page for it, and pretending otherwise would make the Atlas useless.

A `Covered` link means the linked page addresses the topic substantively, not that it exhausts it. A `(planned)` marker is a roadmap entry, not an apology.

## Territories

| Territory | Covered | Planned |
| --- | --- | --- |
| [Retrieval And Knowledge](./retrieval-and-knowledge.md) | 6 | 2 |
| [Model Layer](./model-layer.md) | 4 | 4 |
| [Inference And Serving](./inference-and-serving.md) | 0 | 7 |
| [Agents And Orchestration](./agents-and-orchestration.md) | 5 | 3 |
| [Evaluation And Quality](./evaluation-and-quality.md) | 4 | 3 |
| [Safety And Security](./safety-and-security.md) | 4 | 3 |
| [Data Engineering For AI](./data-engineering-for-ai.md) | 2 | 4 |
| [Product And UX](./product-and-ux.md) | 2 | 4 |
| [Cost And Operations](./cost-and-operations.md) | 5 | 2 |
| [Organization And Process](./organization-and-process.md) | 1 | 3 |

Total: 33 topics covered, 35 planned.

## How To Read The Atlas

Use it three ways:

1. As a map. If you are new to AI system design, read every territory file once. Each takes a few minutes and tells you what problems exist before you need to solve them.
2. As an index. If you are designing a specific system, find the territory, read the topic paragraphs, and follow the `Covered` links for depth.
3. As a roadmap. The `(planned)` markers are the repo's honest gap list. The inference and serving territory is the largest gap: this repo currently assumes hosted inference, and self-hosted serving deserves its own module.

## Relationship To The Rest Of The Repo

The Atlas does not replace [MODULE_STATUS.md](../MODULE_STATUS.md), which tracks course completeness by module. The Atlas tracks field completeness by topic. A module can be course-complete while its territory still has planned topics, because a course needs a coherent path more than it needs exhaustive breadth.
