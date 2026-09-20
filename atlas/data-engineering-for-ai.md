# Atlas: Data Engineering For AI

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers the pipelines that feed AI systems: getting data in, keeping it fresh, and producing the labeled and synthetic data that evaluation and training consume.

## Ingestion

Everything downstream inherits the quality of ingestion: connectors to source systems, permission metadata carried alongside content, deduplication, and the difference between a one-time bulk load and a pipeline that runs forever. Ingestion that drops permissions creates leaks; ingestion that drops documents creates invisible knowledge gaps. The design is decided by the number and messiness of source systems, whether sources push changes or must be polled, and how failures are detected when the symptom is only a slightly worse answer.

Coverage: [Covered](../patterns/rag.md)

## Document Processing Pipelines

Real documents are hostile: scanned PDFs, tables that lose meaning when linearized, slides where layout is the content, and HTML full of navigation junk. Parsing quality bounds retrieval quality, and errors here are silent because the pipeline still produces text. The design is decided by your document mix, whether tables and figures carry answers users need, the OCR and layout-parsing stack you can afford per document, and sampling parsed output for quality instead of assuming it.

Coverage: (planned)

## Embedding Pipelines

Embedding at scale is an operational system: batch jobs with rate limits and retries, versioning that records which model embedded which chunk, and the migration problem when you change embedding models and every stored vector becomes incompatible. Mixing vectors from different models silently breaks retrieval. The design is decided by corpus size against embedding throughput and cost, a reindexing strategy you can execute without downtime, and metadata that makes every vector traceable to its model version.

Coverage: (planned)

## Freshness And Pipeline SLAs

Users assume the assistant knows what changed this morning, so data freshness becomes a product guarantee: the lag from a source update to its appearance in retrieval is an SLA whether you declared one or not. Deletions are the sharp edge, because content removed for legal or personnel reasons must leave the index and its caches quickly. The design is decided by the staleness tolerance per data source, monitoring that measures actual end-to-end lag, and a deletion path that is verified rather than assumed.

Coverage: (planned)

## Synthetic Data

When real data is scarce, sensitive, or missing the hard cases, models can generate training and eval data: paraphrased queries, edge-case documents, adversarial inputs. Used carelessly it teaches the system the generator's blind spots and inflates eval scores with easy examples. The design is decided by whether synthetic examples are validated against real distributions, how much of your eval set you allow to be synthetic, and keeping generated data out of the benchmarks that judge the model that generated it.

Coverage: (planned)

## Labeling Operations

Human labels are the ground truth for evals, judge validation, and fine-tuning, and their quality is a system property: unclear rubrics, fatigued reviewers, and unmeasured inter-annotator agreement produce labels worse than no labels. The design is decided by rubric specificity, agreement measurement before trusting any labeled set, the routing that puts hard cases in front of the right reviewers, and whether the labeling loop runs continuously or decays after launch.

Coverage: [Covered](../patterns/human-review-queue.md)
