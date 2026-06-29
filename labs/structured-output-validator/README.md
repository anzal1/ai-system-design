# Structured Output Validator Lab

This lab teaches a production lesson:

> Schema-valid output is necessary, but not sufficient. You also need business-rule validation.

The lab uses standard-library Python and a tiny fixture of model-like outputs.

## Run

From the repo root:

```bash
python3 labs/structured-output-validator/validator.py
```

## What You Will Learn

- How to separate schema checks from business checks
- Why valid JSON can still be unsafe or wrong
- How validation failures become eval cases
- Why downstream code should not trust model-generated IDs or actions

## Exercise

1. Run the validator.
2. Inspect which examples pass schema but fail business rules.
3. Add a new required field.
4. Add a new business rule.
5. Re-run and explain the failure modes.

## Production Connection

In production, structured output validation should happen before:

- Displaying critical output
- Executing a tool call
- Writing to a database
- Sending a message
- Triggering a workflow
