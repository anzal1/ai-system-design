"""Vector search from scratch: hashed embeddings, brute force, HNSW-lite.

Part A: an embedding function with no ML. Character n-grams hashed
into a fixed-width vector (the hashing trick), L2 normalized. It has
no semantics, but it has real cosine-similarity behavior: texts that
share surface form land near each other, and that is enough to build
and honestly benchmark the search side.

Part B: brute-force cosine search, then HNSW-lite, a simplified but
faithful version of Hierarchical Navigable Small World graphs:
random level assignment, greedy descent through upper layers, and
best-first search with an ef beam at layer 0.

The benchmark builds both indexes over a few thousand synthetic
vectors and reports distance comparisons per query and recall@10.

Stdlib only. Deterministic. Run: python3 vector_index.py
"""

import heapq
import math
import random
import time
import zlib

# ---------------------------------------------------------------------------
# Part A: embedding via the hashing trick over character n-grams.
# ---------------------------------------------------------------------------


def embed(text, dim=256, n=3):
    """Map text to a unit vector. Each character n-gram is hashed to a
    bucket (crc32 for determinism across runs); a second hash bit sets
    the sign, which keeps hash collisions from only ever adding mass.
    This is feature hashing, the same trick Vowpal Wabbit made standard."""
    vec = [0.0] * dim
    padded = f" {text.lower()} "
    for i in range(len(padded) - n + 1):
        gram = padded[i : i + n]
        h = zlib.crc32(gram.encode("utf-8"))
        bucket = (h >> 1) % dim
        sign = 1.0 if h & 1 else -1.0
        vec[bucket] += sign
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def cosine(a, b):
    """Dot product; inputs are unit vectors."""
    return sum(x * y for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# Part B1: brute-force search.
# ---------------------------------------------------------------------------


class BruteForceIndex:
    def __init__(self):
        self.vectors = []
        self.comparisons = 0

    def add(self, vec):
        self.vectors.append(vec)

    def search(self, q, k=10):
        scored = []
        for i, v in enumerate(self.vectors):
            self.comparisons += 1
            scored.append((cosine(q, v), i))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored[:k]


# ---------------------------------------------------------------------------
# Part B2: HNSW-lite.
# ---------------------------------------------------------------------------


class HNSWLite:
    """A small-but-faithful HNSW.

    Kept from the paper: exponentially distributed layer assignment,
    greedy single-entry descent through upper layers, best-first
    beam search (ef) at the target layer, bidirectional links capped
    at M per node (2M at layer 0), and the neighbor-selection
    heuristic. The heuristic is not optional garnish: keeping only
    the M closest candidates lets tight clusters link only to
    themselves, the graph fragments into islands, and recall
    collapses (try it: replace _select_neighbors with cands[:cap]
    and watch recall@10 drop below 0.3 on this benchmark).

    Simplified away: deletions, concurrency, and the ef auto-tuning
    real libraries layer on top. Those matter in production; they do
    not change the shape of the algorithm.
    """

    def __init__(self, M=8, ef_construction=64, seed=7):
        self.M = M
        self.M0 = 2 * M
        self.efc = ef_construction
        self.mL = 1.0 / math.log(M)
        self.rng = random.Random(seed)
        self.vectors = []
        self.graph = []          # graph[level][node] -> neighbor list
        self.entry = None
        self.max_level = -1
        self.comparisons = 0

    def _dist(self, a, b):
        self.comparisons += 1
        # Squared euclidean; on unit vectors it ranks identically to
        # cosine distance (|a-b|^2 = 2 - 2*cos).
        return sum((x - y) * (x - y) for x, y in zip(a, b))

    def _search_layer(self, q, entry_points, ef, level):
        """Best-first search: expand the closest unexpanded candidate
        until no candidate can improve the worst of the ef results."""
        visited = set(entry_points)
        candidates = []  # min-heap by distance
        results = []     # max-heap (negated) of the ef best so far
        for e in entry_points:
            d = self._dist(q, self.vectors[e])
            heapq.heappush(candidates, (d, e))
            heapq.heappush(results, (-d, e))
        while candidates:
            d, node = heapq.heappop(candidates)
            if d > -results[0][0]:
                break  # nothing left can beat the current worst result
            for nb in self.graph[level][node]:
                if nb in visited:
                    continue
                visited.add(nb)
                dnb = self._dist(q, self.vectors[nb])
                if len(results) < ef or dnb < -results[0][0]:
                    heapq.heappush(candidates, (dnb, nb))
                    heapq.heappush(results, (-dnb, nb))
                    if len(results) > ef:
                        heapq.heappop(results)
        return sorted((-nd, node) for nd, node in results)

    def _select_neighbors(self, cands, cap):
        """The paper's heuristic (Algorithm 4). A candidate is kept only
        if it is closer to the query point than to every neighbor already
        selected. This forces links to spread across directions and
        clusters instead of piling into the nearest one, which is what
        keeps the graph connected. Skipped candidates backfill if the
        selection comes up short (the keepPrunedConnections option)."""
        selected = []
        for d, n in cands:
            if len(selected) >= cap:
                break
            if all(self._dist(self.vectors[n], self.vectors[s]) >= d
                   for _, s in selected):
                selected.append((d, n))
        if len(selected) < cap:
            chosen = {n for _, n in selected}
            for d, n in cands:
                if len(selected) >= cap:
                    break
                if n not in chosen:
                    selected.append((d, n))
        return [n for _, n in selected]

    def add(self, vec):
        idx = len(self.vectors)
        self.vectors.append(vec)
        level = int(-math.log(self.rng.random()) * self.mL)
        while len(self.graph) <= level:
            self.graph.append({})
        for lc in range(level + 1):
            self.graph[lc][idx] = []

        if self.entry is None:
            self.entry = idx
            self.max_level = level
            return

        # Greedy descent through layers above the new node's level.
        ep = [self.entry]
        for lc in range(self.max_level, level, -1):
            ep = [self._search_layer(vec, ep, 1, lc)[0][1]]

        # Insert with a wider beam at each layer the node lives on.
        for lc in range(min(level, self.max_level), -1, -1):
            cands = self._search_layer(vec, ep, self.efc, lc)
            cap = self.M0 if lc == 0 else self.M
            neighbors = self._select_neighbors(cands, cap)
            self.graph[lc][idx] = list(neighbors)
            for n in neighbors:
                links = self.graph[lc][n]
                links.append(idx)
                if len(links) > cap:
                    # Re-select n's neighbors with the same heuristic.
                    ranked = sorted(
                        (self._dist(self.vectors[n], self.vectors[m]), m)
                        for m in links
                    )
                    self.graph[lc][n] = self._select_neighbors(ranked, cap)
            ep = [n for _, n in cands]

        if level > self.max_level:
            self.max_level = level
            self.entry = idx

    def search(self, q, k=10, ef=32):
        ep = [self.entry]
        for lc in range(self.max_level, 0, -1):
            ep = [self._search_layer(q, ep, 1, lc)[0][1]]
        results = self._search_layer(q, ep, max(ef, k), 0)
        # Return (cosine, idx) to match the brute-force interface.
        return [(1.0 - d / 2.0, i) for d, i in results[:k]]


# ---------------------------------------------------------------------------
# Demo.
# ---------------------------------------------------------------------------


def demo_embeddings():
    print("=" * 72)
    print("Part A: hashed n-gram embeddings (dim=256, char trigrams)")
    print("=" * 72)
    corpus = {
        "timeout1": "database connection timed out after thirty seconds",
        "timeout2": "db connection timeout error, retried three times",
        "deploy": "deployment rolled back after failed health checks",
        "recipe": "slow roasted tomato soup with fresh basil",
    }
    vecs = {k: embed(v) for k, v in corpus.items()}
    pairs = [
        ("timeout1", "timeout2"),
        ("timeout1", "deploy"),
        ("timeout1", "recipe"),
        ("deploy", "recipe"),
    ]
    sims = {}
    for a, b in pairs:
        sims[(a, b)] = cosine(vecs[a], vecs[b])
        print(f"  cos({a:9}, {b:9}) = {sims[(a, b)]:+.3f}")

    assert sims[("timeout1", "timeout2")] > sims[("timeout1", "deploy")]
    assert sims[("timeout1", "timeout2")] > sims[("timeout1", "recipe")]
    assert sims[("timeout1", "timeout2")] > 0.3, "related pair should be clearly similar"
    assert abs(sims[("deploy", "recipe")]) < 0.3, "unrelated pair should be near zero"
    print("  Related texts score higher than unrelated ones. No ML involved:")
    print("  shared character n-grams are the only signal.")


def synthetic_vectors(n, dim, centers, rng, noise=0.35):
    """Clustered unit vectors: realistic for embeddings, which are
    never uniform on the sphere. Queries are drawn from the same
    centers as the base set, the way real queries resemble the
    corpus they search."""
    out = []
    for i in range(n):
        c = centers[i % len(centers)]
        v = [x + rng.gauss(0, noise) for x in c]
        norm = math.sqrt(sum(x * x for x in v))
        out.append([x / norm for x in v])
    return out


def demo_benchmark():
    print()
    print("=" * 72)
    print("Part B: brute force vs HNSW-lite")
    print("=" * 72)
    rng = random.Random(42)
    dim, n_base, n_queries, k = 32, 3000, 25, 10
    centers = [[rng.gauss(0, 1) for _ in range(dim)] for _ in range(12)]
    base = synthetic_vectors(n_base, dim, centers, rng)
    queries = synthetic_vectors(n_queries, dim, centers, random.Random(1234))

    bf = BruteForceIndex()
    for v in base:
        bf.add(v)

    hnsw = HNSWLite(M=8, ef_construction=64, seed=7)
    t0 = time.perf_counter()
    for v in base:
        hnsw.add(v)
    build_s = time.perf_counter() - t0
    print(f"\n  built HNSW-lite over {n_base} vectors (dim={dim}) "
          f"in {build_s:.1f}s, {hnsw.comparisons} distance comps, "
          f"{len(hnsw.graph)} layers")

    # Ground truth from brute force.
    bf.comparisons = 0
    t0 = time.perf_counter()
    truth = [set(i for _, i in bf.search(q, k)) for q in queries]
    bf_time = time.perf_counter() - t0
    bf_comps = bf.comparisons / n_queries

    print(f"\n  {'ef':>4} {'recall@10':>10} {'comps/query':>12} "
          f"{'vs brute force':>15}")
    results_by_ef = {}
    for ef in (10, 32, 64, 128):
        hnsw.comparisons = 0
        t0 = time.perf_counter()
        recalls = []
        for q, gt in zip(queries, truth):
            found = set(i for _, i in hnsw.search(q, k, ef=ef))
            recalls.append(len(found & gt) / k)
        hnsw_time = time.perf_counter() - t0
        recall = sum(recalls) / len(recalls)
        comps = hnsw.comparisons / n_queries
        results_by_ef[ef] = (recall, comps)
        print(f"  {ef:>4} {recall:>10.3f} {comps:>12.0f} "
              f"{comps / bf_comps:>14.1%}")
    print(f"\n  brute force: recall 1.000 by definition, "
          f"{bf_comps:.0f} comps/query, {bf_time / n_queries * 1000:.1f} ms/query")

    # ----- Correctness asserts ------------------------------------------
    recall32, comps32 = results_by_ef[32]
    assert recall32 >= 0.90, f"recall@10 at ef=32 too low: {recall32:.3f}"
    assert comps32 < 0.5 * bf_comps, \
        "HNSW-lite should do far fewer comparisons than brute force"
    # More beam width buys recall, never loses it (monotone in practice
    # on this data).
    assert results_by_ef[128][0] >= results_by_ef[10][0]
    assert results_by_ef[128][0] >= 0.97, "wide beam should be near exact"
    # And costs more comparisons.
    assert results_by_ef[128][1] > results_by_ef[10][1]

    print("\nAll asserts passed.")
    print("Takeaway: the graph answers with a fraction of the comparisons")
    print("by giving up certainty. ef is the dial: every ANN index sells")
    print("recall to buy latency, and the exchange rate is measurable.")


if __name__ == "__main__":
    demo_embeddings()
    demo_benchmark()
