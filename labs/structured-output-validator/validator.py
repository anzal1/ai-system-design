#!/usr/bin/env python3
"""Structured output validation lab.

This intentionally avoids external dependencies so learners can run it anywhere.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXAMPLES_PATH = ROOT / "data" / "outputs.jsonl"

REQUIRED_FIELDS = {
    "answer": str,
    "citations": list,
    "confidence": str,
    "action": str,
}

VALID_CONFIDENCE = {"low", "medium", "high"}
VALID_ACTIONS = {"answer", "refuse", "escalate"}
VALID_CITATIONS = {"doc_refunds", "doc_password_reset", "doc_account_closure"}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def schema_errors(output: dict) -> list[str]:
    errors = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in output:
            errors.append(f"missing field: {field}")
            continue
        if not isinstance(output[field], expected_type):
            errors.append(f"wrong type for {field}")

    if output.get("confidence") not in VALID_CONFIDENCE:
        errors.append("invalid confidence enum")
    if output.get("action") not in VALID_ACTIONS:
        errors.append("invalid action enum")
    return errors


def business_errors(output: dict) -> list[str]:
    errors = []
    citations = set(output.get("citations", []))

    if output.get("action") == "answer" and not citations:
        errors.append("answers require at least one citation")

    if citations - VALID_CITATIONS:
        errors.append("unknown citation id")

    if output.get("confidence") == "high" and output.get("action") == "escalate":
        errors.append("high confidence should not escalate without a risk reason")

    if "refund" in output.get("answer", "").lower() and "doc_refunds" not in citations:
        errors.append("refund answers must cite refund policy")

    return errors


def main() -> None:
    examples = load_jsonl(EXAMPLES_PATH)
    passed = 0

    for example in examples:
        output = example["output"]
        schema = schema_errors(output)
        business = business_errors(output)
        ok = not schema and not business
        passed += int(ok)

        print("=" * 80)
        print(f"Case: {example['id']}")
        print(f"Schema errors: {schema or 'none'}")
        print(f"Business errors: {business or 'none'}")
        print(f"Passed: {ok}")

    print("=" * 80)
    print(f"Passed examples: {passed}/{len(examples)}")
    print()
    print("Failure analysis")
    print("- Which examples are invalid JSON-shaped objects?")
    print("- Which examples pass schema but fail business rules?")
    print("- Which failures should trigger retry, refusal, or human review?")


if __name__ == "__main__":
    main()
