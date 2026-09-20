# Build A Token-Aware Rate Limiter From Scratch

One file, pure Python stdlib, no threads, no sleeps. You build the admission layer that sits in front of an LLM serving fleet: per-tenant token buckets, a global concurrency semaphore, and honest 429 responses with Retry-After.

## Problem

Request-count limits fail for LLM workloads because a request is not a unit of cost. One request can carry 200 tokens or 200,000. A tenant sending one request per second of 20,000-token prompts consumes 25 times the capacity of a tenant sending one request per second of 800-token prompts, and a request limiter treats them identically. The demo makes this concrete: the same traffic run through a request limiter lets a token-heavy tenant extract about 1.7 million tokens while a token limiter caps it near 320,000, and Jain's fairness index on tokens served jumps from 0.32 to 0.66.

The second problem is that per-tenant math says nothing about the fleet. GPU serving capacity is bounded by concurrent in-flight requests. Even a perfectly fair set of tenants can jointly exceed it, so admission needs a global gate too.

## What You Build

- A token bucket denominated in LLM tokens, with capacity (burst allowance) and refill rate (sustained throughput) as separate knobs
- Per-tenant buckets created lazily, one per tenant
- A global concurrency semaphore with peak tracking
- A gateway that returns `ok`, `429` (tenant over budget, with an exact Retry-After), or `503` (fleet full, with a generic short backoff)
- An event-driven simulation on a simulated clock: two steady tenants, one bursty tenant, and one whale sending huge prompts, all with retry behavior that honors Retry-After
- A head-to-head comparison of the same arrivals through a token limiter and a request limiter, with fairness stats

## How It Works

1. The bucket is lazy: it stores a level and a timestamp, and computes refill on access as `elapsed * refill_rate`, capped at capacity. No timers, no background threads.
2. Admission charges the request's estimated token count against the tenant's bucket. If the bucket is short, the response is a 429 carrying `deficit / refill_rate` as Retry-After. That value is exact: a client that waits precisely that long succeeds on its first retry, and the unit test proves it.
3. If the bucket admits but the semaphore is full, the gateway refunds the bucket and returns 503. The tenant did nothing wrong; charging their budget for the fleet's congestion would convert a capacity problem into an unfair billing problem.
4. The simulation is a single heap of timestamped events (arrivals, retries, slot releases). Time is a float that jumps from event to event, which is why 60 simulated seconds run in milliseconds.

## Design Decisions

- **Meter tokens, not requests.** The bucket unit is the resource the fleet actually spends. The demo runs both units over identical traffic so the difference is measured, not asserted.
- **Capacity and refill are separate knobs.** Capacity is the burst you tolerate; refill is the throughput you sell. The bursty tenant's 8-request spikes fit inside capacity, while the whale's sustained demand hits the refill ceiling.
- **Retry-After is computed, not guessed.** `deficit / refill_rate` is the earliest instant the request can succeed. Honest values make well-behaved clients self-schedule; round-number guesses cause synchronized retry storms.
- **429 and 503 are different signals.** 429 means "you, specifically, slow down" and carries a per-tenant wait. 503 means "everyone, briefly" and must not drain the tenant's bucket.
- **Charge on admission using the estimate.** Output length is unknown at admission time. This implementation charges the declared token count up front; production systems charge an estimate and reconcile after completion.

## Failure Modes

- Token counts at admission are estimates. If clients under-declare, or outputs run long, the fleet does more work than the buckets recorded. Reconciliation after completion, or a debt mechanism that dips the bucket negative, closes the gap.
- Retry storms: if many clients ignore Retry-After and retry on a fixed interval, rejections synchronize into waves. The limiter holds, but the front door takes pointless load.
- Bucket state lives in one process here. Behind a load balancer with per-instance buckets, a tenant gets N times the intended rate. Shared state (or consistent hashing of tenants to instances) is required.
- The refund-on-503 path assumes the semaphore check is cheap and immediate. If admission and execution are separated by a queue, a request can pass both gates and still starve.
- A single global semaphore treats all requests as equal load, but a 100,000-token prompt occupies a slot far longer than a 500-token one. Slot-seconds, not slots, is the truer unit.

## What Production Systems Do Differently

- Buckets live in shared storage (Redis with Lua scripts, or a dedicated limiter service) so all gateway replicas see one level per tenant, with local caches to absorb the read load.
- Input and output tokens are often limited separately, because output tokens dominate serving cost, and the output count is only known after the fact. Providers reconcile actual usage against the estimated charge.
- Limits are hierarchical: per API key, per tenant, per organization, per model, plus a global fleet limit, each with its own bucket.
- Rate limit headers expose remaining budget continuously (limit, remaining, reset), not just on rejection, so clients can pace proactively.
- Weighted fair queueing or deficit round robin replaces plain rejection when the operator wants to reorder rather than refuse work under contention.
- Admission ties into autoscaling: sustained 503 rates are a scaling signal, not just a client-facing error.

## Run It

```bash
python3 rate_limiter.py
```

Runs in well under a second. Prints per-tenant admission stats for the token limiter, a token-limiter versus request-limiter comparison on identical traffic, Jain fairness for both, and peak concurrency. Inline asserts validate bucket refill math, exact Retry-After behavior, no overfill, semaphore bounds, per-tenant token ceilings, and that the token limiter is measurably fairer than the request limiter.

## Exercises

1. Change the whale's client to ignore Retry-After and retry every 0.1 seconds instead. Measure how many extra 429s the gateway serves and confirm tokens served barely changes. The limiter protects capacity; it cannot protect the front door.
2. Add output-token reconciliation: charge an estimate at admission, then adjust the bucket when the request completes with an actual count drawn from a seeded distribution. Allow the bucket to go negative and observe how debt delays the next admission.
3. Replace the single semaphore with slot-seconds: each request holds capacity proportional to its token count times service time. Show that the whale's requests now crowd out fewer small requests.
4. Split the bucket into separate input-token and output-token buckets with different refill rates, and design traffic that passes one but not the other.
5. Simulate two gateway replicas, each with its own bucket map and half the arrivals per tenant. Measure how far a tenant can exceed the intended global rate, then fix it with a shared bucket keyed by tenant.

## Further Reading

- [Anthropic API rate limits](https://docs.claude.com/en/api/rate-limits) documents production token-bucket limits with separate input and output token buckets per model, the shape this module builds.
- [Stripe: scaling your API with rate limiters](https://stripe.com/blog/rate-limiters) is the classic engineering write-up on layering request limiters and concurrency limiters in production, with the operational reasoning behind each layer.
- [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) defines the 429 status code and its Retry-After semantics, the contract this gateway implements.
- [Jain, Chiu, Hawe (1984): A Quantitative Measure of Fairness](https://arxiv.org/abs/cs/9809099) introduced the fairness index the demo reports, worth reading for what the index does and does not capture.
