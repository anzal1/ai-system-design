# Courses And Books

Last reviewed: 2026-09-21

Curated, capped at 15 entries. Each entry earns its place by informing a real design decision. If a course or book only explains what terms mean, it does not belong here.

## Books

- [Designing Machine Learning Systems, Chip Huyen](https://www.oreilly.com/library/view/designing-machine-learning-systems/9781098107956/): the pre-LLM production ML canon; informs data pipeline, monitoring, and iteration-loop decisions that LLM systems inherit unchanged.
- [AI Engineering, Chip Huyen](https://www.oreilly.com/library/view/ai-engineering/9781098166298/): the closest thing to a textbook for this repo's subject; informs evaluation strategy, RAG vs fine-tuning, and inference optimization decisions.
- [Designing Data-Intensive Applications, Martin Kleppmann](https://dataintensive.net/): the mental models for consistency, replication, and stream processing that every retrieval index and feedback pipeline quietly depends on.
- [Hands-On Large Language Models, Jay Alammar and Maarten Grootendorst](https://www.oreilly.com/library/view/hands-on-large-language-models/9781098150952/): visual, code-first grounding in how transformers, embeddings, and generation actually work; informs chunking and embedding-model choices with mechanism rather than folklore.
- [Reliable Machine Learning, Chen et al.](https://www.oreilly.com/library/view/reliable-machine-learning/9781098106218/): SRE thinking applied to ML systems; informs SLO, incident response, and on-call design for probabilistic services.
- [Site Reliability Engineering, Google](https://sre.google/sre-book/table-of-contents/): the original error-budget and SLO framework; informs how to adapt reliability practice to systems that fail by being wrong instead of being down.
- [Machine Learning Engineering Open Book, Stas Bekman](https://github.com/stas00/ml-engineering): battle notes from training and serving large models on real GPU fleets; informs capacity planning and self-hosted serving decisions.

## Courses

- [Stanford CS336: Language Modeling from Scratch](https://stanford-cs336.github.io/): builds a language model end to end including the serving math; informs intuition for why inference costs what it costs.
- [Stanford CS224N: NLP with Deep Learning](https://web.stanford.edu/class/cs224n/): the foundations under embeddings and attention; informs retrieval and model-layer decisions at the level of mechanism.
- [Neural Networks: Zero to Hero, Andrej Karpathy](https://karpathy.ai/zero-to-hero.html): from backprop to GPT in code; the fastest route to understanding what you are actually deploying.
- [Full Stack Deep Learning](https://fullstackdeeplearning.com/): production-focused course covering deployment, monitoring, and data flywheels; informs the operational half of every module here.
- [Hugging Face LLM Course](https://huggingface.co/learn/llm-course): free and current on fine-tuning and open-weight tooling; informs the open vs hosted decision with hands-on grounding.
- [Practical Deep Learning for Coders, fast.ai](https://course.fast.ai/): the pragmatic top-down approach to training models; informs when fine-tuning is worth it by making you do it once.
- [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/): one-to-two-hour vendor-partnered courses on RAG, agents, and evals; informs quick tool evaluation before committing to a stack.

## Long-Form Practitioner Guides

- [What We Learned from a Year of Building with LLMs, Yan et al.](https://applied-llms.org/): dense field report from six practitioners; informs evals, caching, and workflow-vs-agent decisions with production evidence.
