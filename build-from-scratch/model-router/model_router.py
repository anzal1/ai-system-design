"""Model router from scratch.

A router is a portfolio manager. It holds a catalog of models with different
cost, latency, and quality profiles, and it allocates each request to the
cheapest asset that still meets the request's quality and latency constraints.
The interesting parts are the same as in any portfolio problem: classification
of the incoming demand, selection under constraints, hedging against failure
(fallback chains), and a hard budget that overrides greed.

Pure stdlib. Deterministic. Simulated time. Run: python3 model_router.py
"""

import random

# ---------------------------------------------------------------------------
# Model catalog: prices and latencies are data, not code.
# Prices are USD per million tokens. Latency is a simple linear model:
# base milliseconds plus milliseconds per output token.
# quality is a coarse capability tier (1 = smallest, 3 = strongest).
# fail_rate simulates provider errors (timeouts, 529s, bad output).
# ---------------------------------------------------------------------------

CATALOG = {
    "nano": {
        "in_price": 0.10, "out_price": 0.40,
        "base_ms": 180, "ms_per_out_tok": 4,
        "quality": 1, "fail_rate": 0.02,
    },
    "mini": {
        "in_price": 0.80, "out_price": 3.20,
        "base_ms": 350, "ms_per_out_tok": 9,
        "quality": 2, "fail_rate": 0.03,
    },
    "large": {
        "in_price": 3.00, "out_price": 15.00,
        "base_ms": 900, "ms_per_out_tok": 22,
        "quality": 3, "fail_rate": 0.05,
    },
    "large-alt": {  # second provider, same tier, worse price, hedge asset
        "in_price": 3.50, "out_price": 16.00,
        "base_ms": 1100, "ms_per_out_tok": 25,
        "quality": 3, "fail_rate": 0.02,
    },
}

# Fallback chains: if a model fails, try the next entry. Chains stay within
# or above the required quality tier so a failure never silently downgrades.
FALLBACK = {
    "nano": ["mini", "large"],
    "mini": ["large", "large-alt"],
    "large": ["large-alt"],
    "large-alt": ["large"],
}


# ---------------------------------------------------------------------------
# Request classification: rule-based complexity scoring.
# Real routers often start exactly here and only move to learned classifiers
# once rules stop explaining routing mistakes.
# ---------------------------------------------------------------------------

REASONING_MARKERS = (
    "prove", "why", "explain", "compare", "trade-off", "tradeoff",
    "design", "architecture", "debug", "step by step", "analyze",
)
SYNTHESIS_MARKERS = ("summarize", "rewrite", "draft", "plan", "outline")
CODE_MARKERS = ("def ", "class ", "import ", "SELECT ", "function", "```")


def complexity_score(req):
    """Score 0..10. Higher means the request needs a stronger model."""
    text = req["text"].lower()
    score = 0
    # Length of the task statement is a weak but real signal.
    words = len(text.split())
    if words > 40:
        score += 2
    elif words > 15:
        score += 1
    # Reasoning verbs are a strong signal, synthesis verbs a moderate one.
    score += 2 * sum(1 for m in REASONING_MARKERS if m in text)
    score += 2 * any(m in text for m in SYNTHESIS_MARKERS)
    # Code in the request usually means synthesis, not lookup.
    if any(m.lower() in text for m in CODE_MARKERS):
        score += 2
    # Long expected output means the model must sustain structure.
    if req["expect_out_tokens"] > 500:
        score += 2
    # Large input context needs a model that can actually use it.
    if req["in_tokens"] > 8000:
        score += 2
    return min(score, 10)


def required_tier(score):
    if score <= 2:
        return 1
    if score <= 5:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Selection: cost-aware and latency-aware, over eligible models only.
# ---------------------------------------------------------------------------

def estimate_cost(model_name, in_tokens, out_tokens):
    m = CATALOG[model_name]
    return (in_tokens * m["in_price"] + out_tokens * m["out_price"]) / 1e6


def estimate_latency_ms(model_name, out_tokens):
    m = CATALOG[model_name]
    return m["base_ms"] + m["ms_per_out_tok"] * out_tokens


def select_model(req, tier):
    """Pick the cheapest eligible model that fits the latency budget.

    Eligible means quality >= required tier. If nothing fits the latency
    budget we still return the fastest eligible model rather than failing:
    a slow correct answer beats no answer for most products.
    """
    eligible = [n for n, m in CATALOG.items() if m["quality"] >= tier]
    fits = [
        n for n in eligible
        if estimate_latency_ms(n, req["expect_out_tokens"]) <= req["latency_budget_ms"]
    ]
    pool = fits if fits else eligible
    key = lambda n: estimate_cost(n, req["in_tokens"], req["expect_out_tokens"])
    if not fits:
        key = lambda n: estimate_latency_ms(n, req["expect_out_tokens"])
    return min(pool, key=key)


# ---------------------------------------------------------------------------
# Budget governor: a hard spend cap with a soft degradation band.
# Above 80 percent of budget, tier-2 work is downgraded to tier 1 to stretch
# the remaining budget. At 100 percent, non-critical requests are rejected.
# ---------------------------------------------------------------------------

class BudgetGovernor:
    def __init__(self, budget_usd):
        self.budget = budget_usd
        self.spent = 0.0
        self.downgrades = 0
        self.rejections = 0

    def adjust_tier(self, tier, critical):
        frac = self.spent / self.budget if self.budget else 1.0
        if frac >= 1.0 and not critical:
            self.rejections += 1
            return None  # reject
        if frac >= 0.8 and tier == 2 and not critical:
            self.downgrades += 1
            return 1
        return tier

    def charge(self, cost):
        self.spent += cost


# ---------------------------------------------------------------------------
# Execution with fallback chains. Failures are simulated with seeded
# randomness. A failed call still costs money and time: we bill the input
# tokens (the request was processed) and add the latency to the total.
# ---------------------------------------------------------------------------

def execute(req, model_name, rng, stats, governor):
    chain = [model_name] + FALLBACK[model_name]
    total_latency = 0.0
    for i, name in enumerate(chain):
        m = CATALOG[name]
        latency = estimate_latency_ms(name, req["expect_out_tokens"])
        failed = rng.random() < m["fail_rate"]
        if failed:
            # Failed call: bill input tokens, eat the base latency, move on.
            cost = req["in_tokens"] * m["in_price"] / 1e6
            governor.charge(cost)
            stats["spend"][name] += cost
            total_latency += m["base_ms"]
            stats["fallbacks"] += 1
            continue
        cost = estimate_cost(name, req["in_tokens"], req["expect_out_tokens"])
        governor.charge(cost)
        stats["spend"][name] += cost
        stats["served_by"][name] += 1
        total_latency += latency
        stats["latencies"].append(total_latency)
        stats["hops"].append(i)
        return name, total_latency
    stats["exhausted"] += 1
    return None, total_latency


# ---------------------------------------------------------------------------
# Workload: a deterministic batch of mixed requests.
# ---------------------------------------------------------------------------

SIMPLE = [
    "classify sentiment: great product",
    "extract the invoice number from this line",
    "translate hello to french",
    "is this email spam yes or no",
]
MEDIUM = [
    "summarize this support thread and list the customer's three main complaints "
    "so the escalation team can follow up quickly",
    "rewrite this paragraph for a technical audience and keep the numbers intact "
    "while tightening the structure of every sentence",
]
HARD = [
    "explain why this distributed lock implementation is unsafe under network "
    "partitions, prove the failure interleaving step by step, and design a fix "
    "using fencing tokens: def acquire(lock, ttl): ...",
    "compare three sharding architectures for a multi-tenant vector store, "
    "analyze the trade-off between tenant isolation and cache locality, and "
    "design the migration plan step by step",
]


def make_workload(rng, n=300):
    reqs = []
    for i in range(n):
        r = rng.random()
        if r < 0.55:
            text = rng.choice(SIMPLE)
            in_tok, out_tok, budget = rng.randint(50, 300), rng.randint(5, 40), 1500
        elif r < 0.85:
            text = rng.choice(MEDIUM)
            in_tok, out_tok, budget = rng.randint(500, 3000), rng.randint(150, 400), 6000
        else:
            text = rng.choice(HARD)
            in_tok, out_tok, budget = rng.randint(2000, 12000), rng.randint(400, 1200), 40000
        reqs.append({
            "id": i, "text": text, "in_tokens": in_tok,
            "expect_out_tokens": out_tok, "latency_budget_ms": budget,
            "critical": rng.random() < 0.05,
        })
    return reqs


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def main():
    rng = random.Random(42)

    # --- unit checks on classification ------------------------------------
    trivial = {"text": "translate hello to french", "in_tokens": 60,
               "expect_out_tokens": 10, "latency_budget_ms": 1500}
    gnarly = {"text": HARD[0], "in_tokens": 9000,
              "expect_out_tokens": 900, "latency_budget_ms": 40000}
    assert complexity_score(trivial) < complexity_score(gnarly)
    assert required_tier(complexity_score(trivial)) == 1
    assert required_tier(complexity_score(gnarly)) == 3

    # --- unit checks on selection ------------------------------------------
    assert select_model(trivial, 1) == "nano", "simple work goes to the cheap model"
    picked = select_model(gnarly, 3)
    assert CATALOG[picked]["quality"] == 3, "hard work never lands on a weak model"
    # Tight latency budget forces a faster model even at tier 2.
    rushed = dict(trivial, latency_budget_ms=300, expect_out_tokens=10)
    assert estimate_latency_ms(select_model(rushed, 1), 10) <= 300

    # --- run the batch ------------------------------------------------------
    governor = BudgetGovernor(budget_usd=1.90)
    stats = {
        "spend": {n: 0.0 for n in CATALOG},
        "served_by": {n: 0 for n in CATALOG},
        "latencies": [], "hops": [], "fallbacks": 0, "exhausted": 0,
    }
    workload = make_workload(rng)
    rejected = 0
    for req in workload:
        tier = required_tier(complexity_score(req))
        tier = governor.adjust_tier(tier, req["critical"])
        if tier is None:
            rejected += 1
            continue
        model = select_model(req, tier)
        execute(req, model, rng, stats, governor)

    # --- report -------------------------------------------------------------
    lat = sorted(stats["latencies"])
    total_spend = sum(stats["spend"].values())
    print("MODEL ROUTER DEMO")
    print(f"  requests: {len(workload)}  served: {len(lat)}  "
          f"rejected by governor: {rejected}  chains exhausted: {stats['exhausted']}")
    print(f"\n  per-model spend and traffic (budget ${governor.budget:.2f}):")
    for name in CATALOG:
        print(f"    {name:<10} served {stats['served_by'][name]:>4}   "
              f"spend ${stats['spend'][name]:.4f}")
    print(f"    {'total':<10} {'':>11}   spend ${total_spend:.4f}")
    print(f"\n  latency ms: p50 {percentile(lat, 0.50):7.0f}   "
          f"p95 {percentile(lat, 0.95):7.0f}   p99 {percentile(lat, 0.99):7.0f}")
    print(f"  fallback attempts: {stats['fallbacks']}   "
          f"requests needing >0 hops: {sum(1 for h in stats['hops'] if h > 0)}")
    print(f"  governor: downgrades {governor.downgrades}, "
          f"rejections {governor.rejections}, spent ${governor.spent:.4f}")

    # Single-model baseline for the portfolio argument.
    baseline = sum(estimate_cost("large", r["in_tokens"], r["expect_out_tokens"])
                   for r in workload)
    print(f"\n  all-on-large baseline: ${baseline:.4f}   "
          f"router spend: ${governor.spent:.4f}   "
          f"saved: {100 * (1 - governor.spent / baseline):.0f}%")

    # --- behavioral asserts --------------------------------------------------
    assert abs(total_spend - governor.spent) < 1e-9
    # The governor admits before it knows the exact cost, so it can overshoot
    # by at most one request. 0.06 is the worst-case single-request cost here.
    assert governor.spent <= governor.budget + 0.06, "governor holds spend near budget"
    assert stats["served_by"]["nano"] > stats["served_by"]["large"], \
        "most traffic is simple and lands on the cheap model"
    assert stats["fallbacks"] > 0, "seeded failures exercised the fallback chains"
    assert governor.spent < baseline, "portfolio beats the single strong model on cost"
    print("\n  all asserts passed")


if __name__ == "__main__":
    main()
