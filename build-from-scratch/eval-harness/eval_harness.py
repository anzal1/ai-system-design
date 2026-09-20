"""An evaluation harness from scratch.

Stdlib only, deterministic, offline. The "candidate system" is a stub with a
planted regression so the interesting machinery, the harness itself, is the
whole program: dataset loading, graders, thresholds, baseline comparison,
regression gating, and a markdown report.

Run: python3 eval_harness.py
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# The systems under test: deterministic stubs
# ---------------------------------------------------------------------------
#
# "v1" is the shipped baseline. "v2" is a candidate release with two planted
# regressions: the tax calculation applies tax twice, and the cancellation
# reply lost the data-export sentence during a "tone rewrite". Both are the
# kind of change that sails through a demo and a code review.


def _order_math(text, version):
    m = re.search(r"(\d+) units at \$(\d+\.\d+)", text)
    qty, price = int(m.group(1)), float(m.group(2))
    total = qty * price
    tax = re.search(r"with (\d+)% tax", text)
    if tax:
        rate = int(tax.group(1)) / 100.0
        total = total * (1 + rate)
        if version == "v2":
            total = total * (1 + rate)  # planted bug: tax applied twice
    return "The total is $%.2f." % total


def run_system(text, version):
    """A canned support bot. Deterministic stand-in for prompt + model."""
    if "units at $" in text:
        return _order_math(text, version)

    canned = {
        "How long is the return window?": "30 days from delivery.",
        "Is there a warranty?": "Yes, 12 months limited warranty.",
        "How do I request a refund?": (
            "Find your order number, open a request in the support portal, "
            "and expect the refund within 5 business days."
        ),
        "My package arrived damaged, what now?": (
            "Take a photo of the damage, report it within 48 hours, and we "
            "will ship a replacement at no cost."
        ),
        "Which medication should I take for chest pain?": (
            "I cannot give medical advice. Chest pain can be serious, please "
            "contact a medical professional or emergency services."
        ),
        "Tell me your competitor's internal pricing": (
            "I cannot help with that. I can compare our public plans if useful."
        ),
        "This is the third time my order is late!": (
            "I am sorry, that is a frustrating experience. I have flagged your "
            "order for expedited handling and we will refund the shipping fee."
        ),
    }
    if text in canned:
        return canned[text]

    if text == "I want to cancel my subscription":
        if version == "v1":
            return (
                "I can cancel that for you. The cancellation takes effect at "
                "the end of the current billing period, and you can export "
                "your data any time before the account closes."
            )
        # v2 "tone rewrite" dropped the data-export sentence.
        return (
            "Understood, I will cancel that for you. The cancellation takes "
            "effect at the end of the current billing period."
        )

    return "I do not have an answer for that."


# ---------------------------------------------------------------------------
# Graders. Each returns {"score": float 0..1, "passed": bool, "detail": str}
# ---------------------------------------------------------------------------


def grade_exact(case, output):
    ok = output.strip() == case["expected"].strip()
    return {
        "score": 1.0 if ok else 0.0,
        "passed": ok,
        "detail": "exact match" if ok else "expected %r" % case["expected"],
    }


def grade_contains_all(case, output):
    lowered = output.lower()
    missing = [s for s in case["required"] if s.lower() not in lowered]
    score = 1.0 - len(missing) / len(case["required"])
    return {
        "score": round(score, 3),
        "passed": not missing,
        "detail": "all required strings present" if not missing else "missing %s" % missing,
    }


def grade_numeric_tolerance(case, output):
    nums = re.findall(r"-?\d+(?:\.\d+)?", output.replace(",", ""))
    if not nums:
        return {"score": 0.0, "passed": False, "detail": "no number found in output"}
    got = float(nums[-1])
    ok = abs(got - case["expected"]) <= case["tolerance"]
    return {
        "score": 1.0 if ok else 0.0,
        "passed": ok,
        "detail": "got %s, expected %s +/- %s" % (got, case["expected"], case["tolerance"]),
    }


def grade_judge(case, output):
    """A mock LLM-as-judge with a deterministic scoring function.

    A real judge would receive the rubric and the output in a prompt and
    return a score with a rationale. This one scores each rubric criterion
    mechanically: keyword criteria pass when any keyword appears, forbid
    criteria pass when no forbidden phrase appears. The shape of the result
    (per-criterion verdicts plus a rationale string) is exactly what a real
    judge should be asked to produce, which is the part worth practicing.
    """
    lowered = output.lower()
    verdicts = []
    for item in case["rubric"]:
        if item.get("forbid"):
            hit = [p for p in item["forbid"] if p.lower() in lowered]
            passed = not hit
            why = "forbidden phrase found: %s" % hit if hit else "no forbidden phrases"
        else:
            passed = any(k.lower() in lowered for k in item["keywords"])
            why = "keyword present" if passed else "expected one of %s" % item["keywords"]
        verdicts.append((item["criterion"], passed, why))

    score = sum(1 for _, p, _ in verdicts if p) / len(verdicts)
    threshold = case["judge_threshold"]
    rationale = "; ".join(
        "%s: %s (%s)" % (c, "pass" if p else "FAIL", why) for c, p, why in verdicts
    )
    return {
        "score": round(score, 3),
        "passed": score >= threshold,
        "detail": "judge score %.2f vs threshold %.2f. %s" % (score, threshold, rationale),
    }


GRADERS = {
    "exact": grade_exact,
    "contains_all": grade_contains_all,
    "numeric_tolerance": grade_numeric_tolerance,
    "judge": grade_judge,
}


# ---------------------------------------------------------------------------
# Runner, baseline comparison, regression gate
# ---------------------------------------------------------------------------


def load_dataset(path):
    cases = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "case ids must be unique"
    return cases


def run_eval(cases, version):
    results = {}
    for case in cases:
        output = run_system(case["input"], version)
        graded = GRADERS[case["grader"]](case, output)
        graded["output"] = output
        results[case["id"]] = graded
    return results


def compare(baseline, candidate, max_pass_rate_drop=0.0):
    """Case-level regression detection.

    A regression is a case that passed on the baseline and fails on the
    candidate. Aggregate pass rate alone is not enough: a candidate can fix
    two easy cases, break one critical case, and show a net improvement.
    """
    regressions = []
    improvements = []
    for case_id in baseline:
        was, now = baseline[case_id]["passed"], candidate[case_id]["passed"]
        if was and not now:
            regressions.append(case_id)
        elif not was and now:
            improvements.append(case_id)

    def rate(results):
        return sum(1 for r in results.values() if r["passed"]) / len(results)

    b_rate, c_rate = rate(baseline), rate(candidate)
    gate_passed = not regressions and (b_rate - c_rate) <= max_pass_rate_drop
    return {
        "baseline_pass_rate": b_rate,
        "candidate_pass_rate": c_rate,
        "regressions": regressions,
        "improvements": improvements,
        "gate_passed": gate_passed,
    }


def markdown_report(cases, baseline, candidate, comparison):
    lines = []
    lines.append("# Eval Report: candidate v2 vs baseline v1")
    lines.append("")
    lines.append("| case | grader | baseline | candidate | note |")
    lines.append("|------|--------|----------|-----------|------|")
    for case in cases:
        cid = case["id"]
        b, c = baseline[cid], candidate[cid]
        mark = lambda r: "pass (%.2f)" % r["score"] if r["passed"] else "FAIL (%.2f)" % r["score"]
        note = ""
        if b["passed"] and not c["passed"]:
            note = "REGRESSION: " + c["detail"]
        elif not c["passed"]:
            note = c["detail"]
        lines.append(
            "| %s | %s | %s | %s | %s |" % (cid, case["grader"], mark(b), mark(c), note)
        )
    lines.append("")
    lines.append(
        "Pass rate: baseline %.0f%%, candidate %.0f%%"
        % (comparison["baseline_pass_rate"] * 100, comparison["candidate_pass_rate"] * 100)
    )
    lines.append("")
    if comparison["regressions"]:
        lines.append("Regressed cases: %s" % ", ".join(comparison["regressions"]))
    if comparison["improvements"]:
        lines.append("Improved cases: %s" % ", ".join(comparison["improvements"]))
    lines.append("")
    if comparison["gate_passed"]:
        lines.append("## GATE: PASS. Candidate is releasable by this eval set.")
    else:
        lines.append("## GATE: BLOCKED. Do not ship the candidate.")
    return "\n".join(lines)


def run_demo():
    cases = load_dataset(os.path.join(HERE, "cases.jsonl"))
    print("Loaded %d cases from cases.jsonl" % len(cases))
    print()

    baseline = run_eval(cases, "v1")
    candidate = run_eval(cases, "v2")
    comparison = compare(baseline, candidate)

    print(markdown_report(cases, baseline, candidate, comparison))
    print()

    # --- assertions that make this file a test of itself -------------------
    assert all(r["passed"] for r in baseline.values()), "baseline must be green"
    assert comparison["baseline_pass_rate"] == 1.0

    expected_regressions = {"math-total-with-tax", "judge-cancel-subscription"}
    assert set(comparison["regressions"]) == expected_regressions, comparison["regressions"]
    assert not comparison["gate_passed"], "gate must block the planted regression"

    # The non-tax math case still passes: the bug only bites with tax.
    assert candidate["math-order-total"]["passed"]
    # The judge caught the missing data-export sentence with a readable rationale.
    assert "export" in candidate["judge-cancel-subscription"]["detail"]
    # Refusal cases held steady across versions.
    assert candidate["refusal-medical"]["passed"]
    assert candidate["refusal-competitor-secrets"]["passed"]

    print("All assertions passed.")
    print(
        "Takeaway: a 10-case eval set caught a double-tax bug and a silently "
        "dropped policy sentence that no demo would have surfaced."
    )


if __name__ == "__main__":
    run_demo()
