# DR-04: Audit Routing, Evaluation, and Independence

## Objective

Research defensible ways to classify pull-request audit complexity and risk, choose the smallest
sufficient audit route, evaluate audit quality, and preserve independence without forcing
premium models onto trivial evidence-only changes.

## Research questions

### Classification

- Which diff features predict audit difficulty or security risk?
- How should docs-only, test-only, schema, dependency, CI, auth, secrets, persistence,
  destructive, and release changes be classified?
- Which conditions must bypass model selection and fail closed?
- Which decisions can be deterministic?
- How should size, file count, code ownership, language, dependency graph, and historical defect
  data affect complexity?

### Routing

- When is mechanical validation alone sufficient?
- When is one lightweight plan-backed model sufficient?
- When is a stronger model justified?
- When are two independent auditors required?
- When should an audit escalate to GPT-5.6 Pro or Claude Opus?
- How should plan exhaustion, runner unavailability, malformed output, and conflicting findings
  be handled?
- Why must environment failure remain separate from model-quality failure?

### Independence

- Which dimensions matter:
  - different runner;
  - different provider;
  - different model family;
  - different session;
  - different prompt author;
  - different credential profile;
  - different execution host?
- When is same-provider review acceptable?
- How should unknown actual model identity constrain independence claims?
- Can a human plus mechanical validation satisfy independence for evidence-only changes?

### Evaluation

- What benchmark corpus is required?
- How should expected findings be adjudicated?
- Which metrics matter:
  - severe defect recall;
  - false positive rate;
  - unsupported claims;
  - schema validity;
  - evidence grounding;
  - contradiction detection;
  - unnecessary escalation;
  - latency;
  - plan usage;
  - operator correction?
- What thresholds should block automatic routing?
- How should route certification expire or be revoked?

## Required deliverables

- Proposed PR classification taxonomy.
- Proposed mechanical-only eligibility rule.
- Proposed model-routing ladder.
- Audit independence policy options.
- Benchmark and shadow-evaluation design.
- Certification and revocation criteria.
- Explicit distinction between research evidence and final Dopemux policy.

## Source posture

Use software-review research, secure-development guidance, agent evaluation literature, and
official vendor docs. Do not treat one vendor's benchmark as neutral truth.
