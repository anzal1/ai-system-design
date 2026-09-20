# Production Postmortems And Failure Reports

Last reviewed: 2026-09-21

Curated, capped at 15 entries. Real accounts of AI systems failing in production, written or ruled on by people with firsthand knowledge. These are the field's cheapest lessons: someone else already paid for them.

## Provider Postmortems

- [OpenAI: March 20 ChatGPT outage](https://openai.com/index/march-20-chatgpt-outage/): a Redis client race condition leaked other users' chat titles and payment details; informs why session isolation and cache keying deserve paranoid review in AI products.
- [OpenAI: Expanding on what we missed with sycophancy](https://openai.com/index/expanding-on-sycophancy/): a model update made GPT-4o agree with users to a harmful degree and had to be rolled back; informs why behavioral evals must gate model updates, not just capability benchmarks.
- [Anthropic: A postmortem of three recent issues](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues): overlapping infrastructure bugs quietly degraded Claude's output quality for weeks; informs why quality regressions are harder to detect than outages and what monitoring catches them.

## Product Failure Writeups

- [Microsoft: Learning from Tay's introduction](https://blogs.microsoft.com/blog/2016/03/25/learning-tays-introduction/): a chatbot trained on adversarial public input turned toxic within a day; the original lesson in why user input is an attack surface for learning systems.
- [Microsoft Bing: Learning from our first week](https://blogs.bing.com/search/february-2023/The-new-Bing-Edge-%E2%80%93-Learning-from-our-first-week): long chat sessions pushed the model off its persona; informs context-length limits and conversation resets as safety controls, not just cost controls.
- [Google: Gemini image generation got it wrong](https://blog.google/products/gemini/gemini-image-generation-issue/): an overcorrected diversity intervention produced historically wrong images and a global pause; informs how safety mitigations themselves need evaluation.
- [Google: AI Overviews, about last week](https://blog.google/products/search/ai-overviews-update-may-2024/): satirical and low-quality web content surfaced as confident answers at search scale; informs source-quality filtering and why edge cases dominate at billions of queries.
- [Honeycomb: All the hard stuff nobody talks about when building products with LLMs](https://www.honeycomb.io/blog/hard-stuff-nobody-talks-about-llm): candid engineering account of context limits, latency, prompt injection, and non-determinism in a shipped feature; informs realistic scoping of a first LLM product.
- [Honeycomb: So we shipped an AI product, did it work?](https://www.honeycomb.io/blog/we-shipped-ai-product): the follow-up with real adoption and cost data; informs how to measure whether an AI feature actually paid off.

## Legal Rulings As Postmortems

- [Moffatt v. Air Canada, 2024 BCCRT 149](https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html): a tribunal held the airline liable for its chatbot's invented refund policy; informs why hallucinated answers are a legal liability and grounding in policy documents is a hard requirement.
- [Mata v. Avianca, Inc.](https://www.courtlistener.com/docket/63107798/mata-v-avianca-inc/): lawyers sanctioned for filing ChatGPT-fabricated case citations; the canonical demonstration that confident fabrication survives human review when the reviewer trusts the tool.
