# Atlas: Organization And Process

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers the human systems around the technical one: who builds and owns AI features, how risk is reviewed, what gates a launch, and how to prepare when the interview is about all of the above.

## Team Shapes

AI work cuts across roles that most org charts keep apart: product engineers own the user experience, ML engineers own models and evals, data engineers own pipelines, and someone has to own prompts, which behave like code but change like content. Central platform teams give leverage and consistency; embedded AI engineers give speed and product context. The design is decided by how many teams ship AI features, whether evals and observability are provided as a platform or rebuilt per team, and who carries the pager when quality drops at midnight.

Coverage: (planned)

## Model Risk Review

Regulated and risk-averse organizations formalize the question of whether a model should ship: documented intended use, known failure modes, evaluation evidence, and sign-off from someone accountable who is not the builder. Done badly it is a quarterly PDF nobody reads; done well it is a lightweight gate proportional to blast radius. The design is decided by tiering systems so a support macro and a credit decision get different scrutiny, the evidence a review requires from the eval pipeline, and how continuously deployed prompt changes fit a process built for annual model releases.

Coverage: (planned)

## Launch Gates

Shipping an AI feature needs a definition of ready that goes beyond code review: eval thresholds met, red-team findings resolved, rollback plan tested, cost model sanity-checked, observability wired, and a staged rollout plan with kill criteria. Gates that live in a wiki get skipped under deadline pressure; gates that live in the deploy pipeline do not. The design is decided by which checks block versus warn, staged exposure from internal users to full traffic, and pre-agreed metrics that trigger rollback without a meeting.

Coverage: [Covered](../patterns/retries-fallbacks-release-gates.md)

## Interview Prep For AI System Design

AI system design interviews test a specific skill: taking an ambiguous product prompt like "design an AI support agent" and driving to architecture, tradeoffs, failure modes, evaluation, and cost, out loud, in 45 minutes. The classic system design canon does not cover retrieval quality, eval pipelines, or injection defense, and interviewers increasingly ask for exactly those. Preparation is decided by practicing full designs against realistic prompts and reviewing worked examples; this repo's [case studies](../case-studies/README.md) and [assignments](../assignments/README.md) are built for that practice, and a dedicated interview guide with a time-boxed answer framework is on the roadmap.

Coverage: (planned)
