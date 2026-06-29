#!/usr/bin/env python3
"""Deterministic tool-call policy simulator for agent system design."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CALLS_PATH = ROOT / "data" / "tool_calls.jsonl"

RISK_LEVELS = {
    "search_docs": 1,
    "get_account": 2,
    "create_ticket": 3,
    "issue_refund": 4,
    "close_account": 4,
    "run_shell": 5,
}

ROLE_ALLOWED_TOOLS = {
    "support_agent": {"search_docs", "get_account", "create_ticket"},
    "billing_manager": {"search_docs", "get_account", "create_ticket", "issue_refund"},
    "admin": set(RISK_LEVELS),
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def decide(call: dict) -> tuple[str, str]:
    tool = call["tool"]
    role = call["role"]
    args = call.get("args", {})

    if tool not in RISK_LEVELS:
        return "block", "unknown tool"

    if tool not in ROLE_ALLOWED_TOOLS.get(role, set()):
        return "block", "role cannot use tool"

    if RISK_LEVELS[tool] >= 4 and not call.get("human_approved"):
        return "approval_required", "high-risk side effect"

    if tool in {"get_account", "issue_refund", "close_account"} and not args.get("account_id"):
        return "block", "missing account_id"

    if tool == "issue_refund" and args.get("amount_usd", 0) > 500:
        return "approval_required", "refund above threshold"

    if tool == "run_shell":
        return "block", "shell execution disabled in this environment"

    return "allow", "policy passed"


def main() -> None:
    calls = load_jsonl(CALLS_PATH)
    expected_matches = 0

    for call in calls:
        decision, reason = decide(call)
        expected = call["expected_decision"]
        matched = decision == expected
        expected_matches += int(matched)

        print("=" * 80)
        print(f"Case: {call['id']}")
        print(f"Role: {call['role']}")
        print(f"Tool: {call['tool']}")
        print(f"Decision: {decision}")
        print(f"Reason: {reason}")
        print(f"Expected: {expected}")
        print(f"Matched: {matched}")

    print("=" * 80)
    print(f"Policy accuracy on fixture: {expected_matches / len(calls):.2f}")
    print()
    print("Failure analysis")
    print("- Which blocked calls are authorization failures?")
    print("- Which approval-required calls are business-risk decisions?")
    print("- Which cases should become trace-based agent evals?")


if __name__ == "__main__":
    main()
