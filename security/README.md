# Security

Security in AI systems is a system design concern. It cannot be solved only through prompting.

## Current Pages

- [Prompt Injection Threat Model](./prompt-injection.md)
- [Sensitive Data Leakage](./data-leakage.md)
- [Tool Abuse And Excessive Agency](./tool-abuse.md)
- [Vector And Embedding Weaknesses](./vector-embedding-weaknesses.md)

## Core Principle

The model can reason about policy, but the application must enforce policy.

## Security Review Checklist

- Is user input treated as untrusted?
- Is retrieved content treated as untrusted?
- Are permissions enforced before model-visible context?
- Are tool calls validated outside the model?
- Are high-risk actions approved by humans?
- Are traces redacted and access-controlled?
- Are evals covering adversarial cases?
- Are data retention and deletion paths defined?
