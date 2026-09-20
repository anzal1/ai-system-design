"""Token-aware rate limiter from scratch.

Request-count limits fail for LLM workloads because requests are not the unit
of cost. One request can carry 200 tokens or 200,000. This limiter meters the
thing that actually consumes capacity: tokens. It combines three mechanisms
that production gateways layer together:

  1. A token bucket per tenant, refilled in tokens per second, so sustained
     throughput is capped while short bursts are absorbed.
  2. A global concurrency semaphore, because GPU serving capacity is bounded
     by in-flight requests regardless of any per-tenant math.
  3. 429 responses that carry a Retry-After computed from the bucket deficit,
     so well-behaved clients back off exactly as long as needed and no longer.

Pure stdlib. Deterministic. Time is simulated: the clock is a float we
advance, never a sleep. Run: python3 rate_limiter.py
"""

import heapq
import random
from collections import defaultdict

# ---------------------------------------------------------------------------
# Token bucket. Capacity and refill are in LLM tokens, not requests.
# ---------------------------------------------------------------------------

class TokenBucket:
    def __init__(self, capacity_tokens, refill_per_sec):
        self.capacity = capacity_tokens
        self.refill = refill_per_sec
        self.level = float(capacity_tokens)  # start full
        self.updated_at = 0.0

    def _advance(self, now):
        elapsed = now - self.updated_at
        if elapsed > 0:
            self.level = min(self.capacity, self.level + elapsed * self.refill)
            self.updated_at = now

    def try_consume(self, now, tokens):
        """Returns (admitted, retry_after_seconds)."""
        self._advance(now)
        if tokens <= self.level:
            self.level -= tokens
            return True, 0.0
        # Deficit divided by refill rate is the exact earliest time this
        # request could succeed. That number is the honest Retry-After.
        deficit = tokens - self.level
        return False, deficit / self.refill


# ---------------------------------------------------------------------------
# Global concurrency semaphore. Simulated: acquire/release are explicit
# events on the simulated clock, no threads involved.
# ---------------------------------------------------------------------------

class Semaphore:
    def __init__(self, limit):
        self.limit = limit
        self.in_flight = 0
        self.peak = 0

    def try_acquire(self):
        if self.in_flight >= self.limit:
            return False
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        return True

    def release(self):
        assert self.in_flight > 0
        self.in_flight -= 1


# ---------------------------------------------------------------------------
# The gateway: per-tenant buckets in front of a shared semaphore.
# Admission checks the bucket first (cheap, per-tenant fairness), then the
# semaphore (global capacity). A semaphore rejection does not drain the
# bucket: the tenant did nothing wrong, the cluster is just full.
# ---------------------------------------------------------------------------

class Gateway:
    def __init__(self, per_tenant_capacity, per_tenant_refill, max_concurrency,
                 unit="tokens"):
        self.buckets = defaultdict(
            lambda: TokenBucket(per_tenant_capacity, per_tenant_refill))
        self.sem = Semaphore(max_concurrency)
        # unit "tokens" charges the request's token count against the bucket.
        # unit "requests" charges 1, which is the naive limiter this module
        # argues against. Both run against identical traffic in the demo.
        self.unit = unit

    def admit(self, now, tenant, tokens):
        """Returns (status, retry_after). status: 'ok' | '429' | '503'."""
        bucket = self.buckets[tenant]
        charge = tokens if self.unit == "tokens" else 1
        ok, retry_after = bucket.try_consume(now, charge)
        if not ok:
            return "429", retry_after
        if not self.sem.try_acquire():
            # Refund the bucket: the tenant is within budget, capacity is the
            # bottleneck. Billing them a rate-limit charge here would let one
            # tenant's burst consume everyone's future budget.
            bucket.level = min(bucket.capacity, bucket.level + charge)
            return "503", 0.5  # generic backoff, capacity frees up fast
        return "ok", 0.0


# ---------------------------------------------------------------------------
# Traffic simulation: event-driven over a heap of (time, event) tuples.
# Tenants have different shapes: steady, bursty, and one abusive whale.
# Well-behaved clients honor Retry-After exactly. That is the point of
# sending an honest value: clients that respect it self-schedule fairly.
# ---------------------------------------------------------------------------

TENANTS = {
    # name: (mean tokens/request, requests/sec, burstiness)
    "steady-a": {"mean_tokens": 800, "rps": 2.0, "burst": 1},
    "steady-b": {"mean_tokens": 800, "rps": 2.0, "burst": 1},
    "bursty": {"mean_tokens": 1200, "rps": 1.0, "burst": 8},   # 8-request spikes
    "whale": {"mean_tokens": 20000, "rps": 1.5, "burst": 1},   # huge prompts
}

SIM_SECONDS = 60.0
SERVICE_TIME = 0.8  # seconds a request occupies a concurrency slot
MAX_RETRIES = 3


def build_arrivals(rng):
    """Precompute all arrival events deterministically."""
    events = []
    for tenant, cfg in TENANTS.items():
        t = 0.0
        while t < SIM_SECONDS:
            gap = rng.expovariate(cfg["rps"]) * cfg["burst"]
            t += gap
            if t >= SIM_SECONDS:
                break
            for _ in range(cfg["burst"]):
                tokens = max(50, int(rng.gauss(cfg["mean_tokens"],
                                               cfg["mean_tokens"] * 0.2)))
                events.append((t, tenant, tokens))
    events.sort()
    return events


def simulate(gateway, arrivals):
    stats = {t: defaultdict(int) for t in TENANTS}
    for t in TENANTS:
        stats[t]["retry_wait"] = 0.0
    # Heap of (time, seq, kind, payload). seq breaks ties deterministically.
    heap = []
    seq = 0
    for (at, tenant, tokens) in arrivals:
        heapq.heappush(heap, (at, seq, "arrive", (tenant, tokens, 0)))
        seq += 1

    end_time = 0.0
    while heap:
        now, _, kind, payload = heapq.heappop(heap)
        end_time = max(end_time, now)
        if kind == "release":
            gateway.sem.release()
            continue
        tenant, tokens, attempt = payload
        st = stats[tenant]
        st["attempts"] += 1
        status, retry_after = gateway.admit(now, tenant, tokens)
        if status == "ok":
            st["admitted"] += 1
            st["tokens_served"] += tokens
            heapq.heappush(heap, (now + SERVICE_TIME, seq, "release", None))
            seq += 1
        elif status == "429":
            st["throttled"] += 1
            assert retry_after > 0, "429 must carry a positive Retry-After"
            if attempt < MAX_RETRIES:
                st["retry_wait"] += retry_after
                heapq.heappush(heap, (now + retry_after, seq, "arrive",
                                      (tenant, tokens, attempt + 1)))
                seq += 1
            else:
                st["dropped"] += 1
        else:  # 503, global capacity
            st["shed"] += 1
            if attempt < MAX_RETRIES:
                heapq.heappush(heap, (now + retry_after, seq, "arrive",
                                      (tenant, tokens, attempt + 1)))
                seq += 1
            else:
                st["dropped"] += 1
    return stats, end_time


def jain_fairness(values):
    """Jain's index: 1.0 is perfectly fair, 1/n is maximally unfair."""
    if not values or sum(values) == 0:
        return 1.0
    n = len(values)
    return sum(values) ** 2 / (n * sum(v * v for v in values))


def main():
    rng = random.Random(7)

    # --- unit checks: the bucket itself -------------------------------------
    b = TokenBucket(capacity_tokens=1000, refill_per_sec=100)
    ok, _ = b.try_consume(0.0, 900)
    assert ok and abs(b.level - 100) < 1e-9
    ok, retry = b.try_consume(0.0, 300)  # 200 short
    assert not ok and abs(retry - 2.0) < 1e-9, "retry-after = deficit / refill"
    ok, _ = b.try_consume(2.0, 300)  # exactly refilled by then
    assert ok, "honoring Retry-After succeeds on the first retry"
    b.try_consume(1000.0, 0)
    assert b.level <= b.capacity, "bucket never overfills"

    # Request-count blindness in one line: a request limiter treats these
    # equally, a token limiter does not.
    small, huge = 200, 180000
    rl = TokenBucket(100000, 10000)
    assert rl.try_consume(0.0, small)[0] and not rl.try_consume(0.0, huge)[0]

    # --- unit check: semaphore ----------------------------------------------
    s = Semaphore(2)
    assert s.try_acquire() and s.try_acquire() and not s.try_acquire()
    s.release()
    assert s.try_acquire()

    # --- run the same traffic through both limiters --------------------------
    arrivals = build_arrivals(rng)
    tok_gw = Gateway(per_tenant_capacity=30000, per_tenant_refill=4000,
                     max_concurrency=6, unit="tokens")
    tok_stats, tok_end = simulate(tok_gw, arrivals)
    req_gw = Gateway(per_tenant_capacity=10, per_tenant_refill=3,
                     max_concurrency=6, unit="requests")
    req_stats, _ = simulate(req_gw, arrivals)

    print("TOKEN-AWARE RATE LIMITER DEMO")
    print(f"  simulated {SIM_SECONDS:.0f}s, {len(arrivals)} arrivals, "
          f"concurrency limit {tok_gw.sem.limit}")
    print(f"  token limiter: 30000-token bucket @ 4000 tok/s per tenant")
    print(f"  request limiter (baseline): 10-request bucket @ 3 req/s per tenant")

    print(f"\n  token limiter:")
    print(f"  {'tenant':<10} {'attempts':>8} {'admitted':>8} {'429s':>6} "
          f"{'503s':>6} {'dropped':>8} {'tokens served':>14} {'avg retry-after':>16}")
    tok_served, req_served = {}, {}
    for tenant in TENANTS:
        st = tok_stats[tenant]
        tok_served[tenant] = st["tokens_served"]
        req_served[tenant] = req_stats[tenant]["tokens_served"]
        avg_ra = st["retry_wait"] / st["throttled"] if st["throttled"] else 0.0
        print(f"  {tenant:<10} {st['attempts']:>8} {st['admitted']:>8} "
              f"{st['throttled']:>6} {st['shed']:>6} {st['dropped']:>8} "
              f"{st['tokens_served']:>14} {avg_ra:>15.2f}s")

    print(f"\n  tokens served, token limiter vs request limiter:")
    for tenant in TENANTS:
        print(f"    {tenant:<10} {tok_served[tenant]:>10} vs {req_served[tenant]:>10}")

    tok_fair = jain_fairness(list(tok_served.values()))
    req_fair = jain_fairness(list(req_served.values()))
    # Retries can extend the clock past SIM_SECONDS, and the bucket keeps
    # refilling, so the honest ceiling uses the actual end of the run.
    ceiling = 4000 * tok_end + 30000  # refill plus initial burst allowance
    print(f"\n  Jain fairness on tokens served: token limiter {tok_fair:.3f}, "
          f"request limiter {req_fair:.3f} (1.000 = perfectly even)")
    print(f"  whale extracted {req_served['whale']} tokens past the request "
          f"limiter, {tok_served['whale']} past the token limiter")
    print(f"  peak concurrency observed: {tok_gw.sem.peak} / {tok_gw.sem.limit}")

    # --- behavioral asserts --------------------------------------------------
    for gw in (tok_gw, req_gw):
        assert gw.sem.peak <= gw.sem.limit, "semaphore bound held"
        assert gw.sem.in_flight == 0, "all slots released at end"
    for tenant in TENANTS:
        assert tok_served[tenant] <= ceiling + 1, f"{tenant} exceeded token ceiling"
    assert tok_stats["whale"]["throttled"] > tok_stats["steady-a"]["throttled"], \
        "the token-heavy tenant hits the token limiter hardest"
    assert req_served["whale"] > 3 * tok_served["whale"], \
        "the request limiter let the whale extract several times more tokens"
    assert tok_fair > req_fair, \
        "metering tokens is fairer than metering requests on token-skewed traffic"
    # Steady tenants are barely touched by the switch: they were never the problem.
    assert abs(tok_served["steady-a"] - req_served["steady-a"]) \
        < 0.25 * req_served["steady-a"]
    print("\n  all asserts passed")


if __name__ == "__main__":
    main()
