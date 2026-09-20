# Atlas: Product And UX

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers the interface between a probabilistic system and a person: shaping perception of latency, communicating uncertainty, and designing for the failures that will happen.

## Streaming UX

Streaming is a product decision before it is an infrastructure one: token-by-token output feels alive for chat but is wrong for a form field or a number that must be correct before it is shown. Streaming also commits you to showing content you have not finished validating. The design is decided by whether partial output has value to the user, what happens visually when a stream fails or gets retracted mid-answer, and how structured elements like tables and citations render while incomplete.

Coverage: (planned)

## Latency Perception

Users experience time to first token, not total generation time, and perceived latency is a design surface: skeleton states, progress narration for agent steps, and precomputed instant responses all buy patience without buying GPUs. Silence is the killer; a ten-second wait with visible progress beats a four-second blank screen. The design is decided by which latency metric your interaction pattern exposes, what honest intermediate signal you can show, and where the budget from the underlying system actually goes.

Coverage: [Covered](../patterns/cost-latency-budgeting.md)

## Confidence Display

The model is sometimes wrong and the interface has to decide what to do about it: citations that ground answers, hedged language, abstention when retrieval found nothing, or explicit confidence signals. Displayed confidence is a promise, and miscalibrated confidence is worse than none because users calibrate their trust to it. The design is decided by whether you have a confidence signal that actually correlates with correctness, the cost to the user of trusting a wrong answer, and whether abstaining is an acceptable output for your product.

Coverage: (planned)

## Correction Loops

Users will catch the system being wrong, and the product must decide what a correction does: fixes the current answer, persists to memory, updates the knowledge source, or vanishes into nothing. A correction that visibly does nothing teaches users to stop correcting. The design is decided by which layer the correction belongs to, how a user-asserted fact is validated before the system starts repeating it, and whether corrections are scoped to the user or shared across tenants.

Coverage: (planned)

## Feedback Capture

Thumbs up and down are sparse, biased toward extremes, and often mean something other than quality, yet feedback is the cheapest production quality signal you can get. Implicit signals like retry, edit distance on model output, copy events, and abandonment usually carry more information than explicit ratings. The design is decided by which implicit signals your interaction pattern produces, how feedback joins to the full trace that produced the response, and who consumes the signal for evals, routing, or retraining.

Coverage: [Covered](../evals-observability/online-monitoring.md)

## Failure UX

The system will fail: retrieval will come up empty, tools will error, models will time out, and outputs will be wrong in ways no gate caught. Failure UX designs those moments instead of leaving them to the exception handler: honest degraded modes, useful fallback content, escalation to a human, and never a fake answer to hide an error. The design is decided by enumerating your actual failure modes, deciding for each whether to retry silently, degrade visibly, or hand off, and writing the failure states into the design spec with the same care as the happy path.

Coverage: (planned)
