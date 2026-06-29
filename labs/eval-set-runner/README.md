# Eval Set Runner Lab

This lab teaches how to turn expected behavior into repeatable checks.

It uses deterministic scoring over a tiny fixture. It is not a replacement for human review or LLM judges. It shows the mechanics of running an eval set and reporting failures.

## What You Will Learn

- How eval examples are structured
- How deterministic checks catch format, refusal, and citation failures
- Why aggregate scores need concrete failure examples
- How production failures become regression tests

## Run

From the repo root:

```bash
python3 labs/eval-set-runner/eval_runner.py
```

## Exercise

1. Run the eval.
2. Inspect failed examples.
3. Add a new failure case.
4. Add a new scorer.
5. Re-run and explain what changed.

## Production Connection

In a real system, outputs would come from your AI application. The runner should store prompt version, model version, retrieval config, trace ID, scores, and failure labels.
