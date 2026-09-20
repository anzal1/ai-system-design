# Atlas: Inference And Serving

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers what happens between a request and a token: the mechanics of LLM inference and the systems that serve it. It is the largest gap in the repo today, because the existing modules assume hosted inference. Every topic here is on the roadmap.

## Prefill Vs Decode

LLM inference has two phases with opposite performance profiles: prefill processes the whole prompt in parallel and is compute-bound, decode generates one token at a time and is memory-bandwidth-bound. Time to first token is dominated by prefill, tokens per second by decode, and optimizing one can hurt the other. The design is decided by your prompt-to-output length ratio and which latency metric your product actually depends on.

Coverage: (planned)

## KV Cache Management

The KV cache stores attention state for every token in context, and it is the resource that runs out first: a single long-context request can consume gigabytes of GPU memory. Paged attention, prefix sharing, and cache eviction policies decide how many concurrent requests a GPU can hold. The design is decided by context lengths in your traffic, how much prompt prefix is shared across requests, and how you degrade when the cache is full.

Coverage: (planned)

## Continuous Batching

Static batching waits for a batch to fill and holds every request until the longest one finishes. Continuous batching admits and evicts requests at token granularity, which is why it multiplies throughput and is now the default in serious serving engines. The design is decided by your traffic's arrival pattern and output-length variance, and by the scheduling policy that trades a new request's time to first token against running requests' decode speed.

Coverage: (planned)

## Speculative Decoding

A small draft model proposes several tokens and the large model verifies them in one pass, cutting decode latency without changing outputs. The speedup depends entirely on the draft model's acceptance rate on your traffic, and it spends extra compute to save time. The design is decided by whether decode latency is your bottleneck, whether a good draft model exists for your domain, and whether you have spare compute headroom to burn on speculation.

Coverage: (planned)

## Streaming

Streaming delivers tokens as they are generated, which transforms perceived latency but complicates everything downstream: output validation can no longer see the whole response before the user does, tool calls arrive incrementally, and errors surface mid-stream after partial content has rendered. The design is decided by whether your output must be validated before display, how your protocol handles mid-stream failure, and what the client does with partial structured output.

Coverage: (planned)

## GPU Capacity Planning

GPU capacity for LLM serving is not planned in requests per second but in concurrent KV cache footprint and decode throughput, and both depend on token-length distributions that shift as your product changes. Overprovisioning is expensive; underprovisioning means queueing, which compounds latency. The design is decided by your traffic's token-length percentiles, your latency SLO, the utilization you can sustain without violating it, and whether bursts are handled by queueing, shedding, or falling back to a hosted API.

Coverage: (planned)

## Self-Hosted Serving Stacks

Running your own inference means choosing a serving engine such as vLLM, SGLang, or TensorRT-LLM, and owning everything around it: model loading, health checks, autoscaling on GPU-shaped signals, observability at the token level, and upgrades in a stack that moves monthly. The design is decided by the throughput and latency you need, the engine's support for your model architecture and quantization format, and honestly assessing the operations capacity of the team that will carry the pager.

Coverage: (planned)
