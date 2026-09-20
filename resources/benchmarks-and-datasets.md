# Benchmarks And Datasets

Last reviewed: 2026-09-21

Curated, capped at 15 entries. A benchmark is listed only if it informs a system design decision. Treat all public scores as screening signals: your private eval set decides, these narrow the shortlist. See the [benchmark contamination](../atlas/evaluation-and-quality.md) topic before trusting any number here.

## Retrieval And Embeddings

- [MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316): the standard comparison of embedding models across retrieval, clustering, and classification; informs embedding model selection before you run your own retrieval evals.
- [BEIR](https://github.com/beir-cellar/beir): heterogeneous zero-shot retrieval benchmark across 18 datasets; informs how well a retriever generalizes to domains it was not trained on, which is your domain.
- [MS MARCO](https://microsoft.github.io/msmarco/): the large-scale passage ranking dataset most retrievers and rerankers were trained or evaluated on; informs reranker selection and provides realistic query-passage training pairs.
- [Natural Questions](https://ai.google.com/research/NaturalQuestions): real Google queries with answers grounded in Wikipedia; informs end-to-end RAG evaluation with genuinely user-shaped questions.
- [HotpotQA](https://hotpotqa.github.io/): multi-hop questions requiring evidence from multiple documents; informs whether you need multi-hop retrieval such as GraphRAG or query decomposition.

## Model Capability

- [MMLU](https://arxiv.org/abs/2009.03300): 57-subject knowledge benchmark, heavily saturated and likely contaminated; informs rough capability tiering of models and teaches the contamination lesson by example.
- [GPQA](https://arxiv.org/abs/2311.12022): graduate-level questions designed to be Google-proof; informs frontier-model comparison where MMLU no longer discriminates.
- [HELM](https://crfm.stanford.edu/helm/): Stanford's holistic evaluation framework measuring accuracy alongside calibration, robustness, and toxicity; informs multi-dimensional model comparison beyond a single score.
- [TruthfulQA](https://arxiv.org/abs/2109.07958): questions where imitating common human misconceptions produces wrong answers; informs hallucination-sensitivity assessment for user-facing products.
- [LMArena Chatbot Arena](https://lmarena.ai/): pairwise human preference rankings from live blind votes; informs which models users actually prefer, with the caveat that preference is not correctness.

## Long Context

- [RULER](https://arxiv.org/abs/2404.06654): measures effective context length versus claimed context length; informs the long context vs RAG decision with evidence that advertised windows overstate usable ones.
- [LongBench](https://arxiv.org/abs/2308.14508): bilingual multi-task long-context benchmark; informs model choice for summarization and QA over long documents.

## Code And Agents

- [HumanEval](https://arxiv.org/abs/2107.03374): the original function-synthesis benchmark for code models; informs quick screening of code capability, now largely saturated.
- [SWE-bench](https://www.swebench.com/): real GitHub issues that agents must resolve in real repositories; informs agentic coding-tool selection with the most production-shaped task available.
- [tau-bench](https://arxiv.org/abs/2406.12045): tool-using agents interacting with simulated users under policy constraints; informs agent architecture choices by measuring reliability over repeated trials, not just single-run success.
