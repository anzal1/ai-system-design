# Atlas: Evaluation And Quality

Last reviewed: 2026-09-21

Part of the [AI System Design Atlas](./README.md). This territory covers how you know the system works: measuring quality before launch, in production, and every time anything changes.

## Offline Evals

An offline eval set is the unit test suite of an AI system: curated inputs, expected properties of outputs, and scorers that run on every change to prompt, model, or retrieval. Without one, every change is a guess and every regression is discovered by users. The design is decided by whether the eval set reflects real traffic including the ugly tail, how outputs are scored when there is no single correct answer, and how the set grows from production failures.

Coverage: [Covered](../patterns/eval-pipeline.md)

## LLM-As-Judge

Using a model to grade model outputs makes evaluation scale to open-ended tasks, and imports a new problem: the judge has biases, favoring verbose answers, certain positions, and its own style. A judge you have not validated against human labels is a random number generator with confidence. The design is decided by measured agreement between judge and human graders on your task, rubric specificity, and controls for known biases like position randomization.

Coverage: [Covered](../patterns/eval-pipeline.md)

## Online Experiments And A/B Testing

Offline evals cannot tell you how real users respond, so production changes need controlled rollouts: A/B tests on quality and business metrics, canaries watching for regressions before full exposure. The hard part is that AI quality metrics are noisy and user feedback is sparse and biased. The design is decided by which online metrics actually proxy quality for your product, the sample size your traffic can deliver, and how long you must wait before trusting a result.

Coverage: [Covered](../evals-observability/online-monitoring.md)

## Regression Gates

Every prompt edit, model upgrade, and retrieval change can silently break behavior that used to work, so releases need gates: eval suites that must pass before a change ships, with thresholds that block deployment rather than merely report. The design is decided by which metrics gate versus merely inform, how flaky nondeterministic scorers are handled without teams learning to ignore red, and who owns the decision to override a failed gate.

Coverage: [Covered](../patterns/retries-fallbacks-release-gates.md)

## Red-Teaming

Evals measure expected behavior; red-teaming hunts for the unexpected: adversarial prompts, jailbreaks, injection payloads, and misuse the design never anticipated. It is a practice, not a one-time audit, because every capability you add creates attacks that did not exist before. The design is decided by the threat model for your product, the mix of automated attack generation and human creativity you can fund, and how findings turn into eval cases so fixed holes stay fixed.

Coverage: (planned)

## Benchmark Contamination

Public benchmarks leak into training data, so a model's score may measure memorization rather than capability, and vendor-reported numbers inherit that doubt. Trusting contaminated benchmarks means choosing models on fiction. The design is decided by preferring private, task-specific eval sets for decisions that matter, treating public scores as screening signals only, and rotating or perturbing test data you may want to reuse.

Coverage: (planned)

## Data Flywheels

A production AI system generates its own improvement data: failures become eval cases, user corrections become training examples, and traffic reveals the input distribution no one designed for. Most teams let this exhaust escape. Building the flywheel means capture pipelines, labeling workflows, and privacy boundaries on reuse of user data. The design is decided by which signals are worth capturing, the consent and retention rules that govern reuse, and whether anyone owns turning captured failures into shipped fixes.

Coverage: (planned)
