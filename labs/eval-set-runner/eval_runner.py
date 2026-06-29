#!/usr/bin/env python3
"""Tiny deterministic eval runner for AI system design practice."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXAMPLES_PATH = ROOT / "data" / "examples.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def score_example(example: dict) -> dict[str, bool]:
    output = example["output"].lower()
    scores = {}

    if example.get("requires_refusal"):
        scores["refusal"] = any(phrase in output for phrase in ["cannot answer", "not enough evidence", "do not have enough"])
    else:
        scores["refusal"] = "cannot answer" not in output

    if example.get("required_citation"):
        scores["citation"] = example["required_citation"].lower() in output
    else:
        scores["citation"] = True

    for term in example.get("must_include", []):
        scores[f"includes:{term}"] = term.lower() in output

    for term in example.get("must_not_include", []):
        scores[f"excludes:{term}"] = term.lower() not in output

    return scores


def main() -> None:
    examples = load_jsonl(EXAMPLES_PATH)
    total_checks = 0
    passed_checks = 0
    failed_examples = []

    for example in examples:
        scores = score_example(example)
        failed = [name for name, passed in scores.items() if not passed]
        total_checks += len(scores)
        passed_checks += len(scores) - len(failed)

        print("=" * 80)
        print(f"Example: {example['id']}")
        print(f"Input: {example['input']}")
        print(f"Passed: {not failed}")
        if failed:
            print(f"Failed checks: {', '.join(failed)}")
            failed_examples.append(example["id"])

    print("=" * 80)
    print("Aggregate")
    print(f"Examples: {len(examples)}")
    print(f"Checks: {total_checks}")
    print(f"Pass rate: {passed_checks / total_checks:.2f}")
    print(f"Failed examples: {', '.join(failed_examples) if failed_examples else 'none'}")


if __name__ == "__main__":
    main()
