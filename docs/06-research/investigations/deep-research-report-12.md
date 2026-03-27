---
id: deep-research-report 12
title: Deep Research Report 12
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-24'
prelude: Deep Research Report 12 (reference) for dopemux documentation and developer
  workflows.
---
# Modular Agent Capability Systems for Dopemux

## Context and design principles

Modern “agentic” systems are increasingly built as **tool-using, stateful, multi-step controllers**, not just single-turn chat. Recent surveys commonly frame this as an LLM that can (a) **reason**, (b) **act** (e.g., tools), and (c) **interact** (with users, environments, or other agents). citeturn1search3 Multi-agent variants then use **multiple LLM-based agents** with explicit coordination structures (centralized, peer-to-peer, hierarchical, etc.) to tackle tasks that are hard for one agent to do reliably. citeturn1search7turn18view3

Two core empirical lessons show up repeatedly across the literature and production experience:

**Chaining makes errors contagious (and sometimes irreversible).**
Multi-agent composition can add capability, but it also adds *attack surface* and *failure surface*. Research and practitioner analyses highlight that minor inaccuracies can propagate through dependencies and “solidify” into false consensus, making issues hard to trace. citeturn11search2 This is consistent with multi-agent workflow papers that explicitly warn about **cascading hallucinations** when systems are naively chained. citeturn16search0 In single-agent settings, hallucinations can also “snowball” when the model over-commits to early mistakes and then generates further false justifications. citeturn16academia41

**Predictability comes more from control-systems engineering than from prompt craft.**
A strong pattern in agent work is separating *high-level planning* from *low-level execution*. Plan-then-execute architectures are argued to improve predictability and cost-efficiency and can strengthen security by enforcing control-flow integrity (especially versus indirect prompt injection). citeturn10view1 State-machine / graph orchestration frameworks emphasise explicit state and control flow, durable execution, human-in-the-loop checkpoints, and memory primitives for long-running workflows. citeturn9view0

For governance, risk frameworks matter because agentic systems are *socio-technical* and change over time. The entity["organization","National Institute of Standards and Technology","us standards institute"] AI Risk Management Framework emphasises lifecycle risk management and explicitly highlights Test, Evaluation, Verification, and Validation (TEVV) as a continuous process across the AI lifecycle. citeturn14view0 It also calls out organisational governance practices like inventories, decommissioning practices, role clarity, and leadership accountability. citeturn19view0

Security-wise, the entity["organization","OWASP","web app security org"] LLM Top 10 is a widely cited taxonomy for practical risks—including prompt injection, insecure/improper output handling, denial of service via resource exhaustion, and “excessive agency” (dangerous autonomy + permissions). citeturn0search1turn6search1turn16search3turn16search6

Design principles that follow from this evidence base:

- **Treat your orchestrator as a “control plane.”** It should be deterministic where possible: explicit state transitions, explicit termination rules, budgets, and policy checks.
- **Treat each agent as a “capability module.”** Agents should be swappable units with contracts (inputs, outputs, tools, proof).
- **Assume non-determinism, even when you try to turn it off.** Multiple studies show output variance under “deterministic” settings; in other words, you can reduce variance, but should plan for residual drift. citeturn17view0turn17view1
- **Assume prompt injection is not “solved.”** Security research and guidance explicitly recommend defense-in-depth; prompt injection exists because the same channel often carries both instructions and data. citeturn9view3turn9view4

## Agent taxonomy

This taxonomy is designed to match your requested top-level categories (planning, engineering, product, governance) while keeping each agent’s boundaries crisp enough to test and audit.

### Planning agents

Planning agents should create *structured intent → plan → constraints* artefacts. They are upstream of tool execution and should generally be **non-privileged** (read-only tools at most).

A useful baseline split is **Planner vs Executor**, mirroring research and frameworks that separate planning from execution to improve predictability and reduce confusion. citeturn10view1turn14view2

Core planning roles:

- **Intent & scope clarifier**: Turns user requests into a constrained objective, assumptions, and success criteria (what “done” means).
- **Decomposer**: Breaks objectives into steps/subtasks; should output a DAG or ordered steps, plus dependencies and stop conditions.
- **Router**: Chooses which agents run for each step, based on contract compatibility and risk level.
- **Context builder**: Decides what to retrieve and what to omit (context engineering), reducing state drift and token bloat. citeturn6search12
- **Budgeter**: Adds cost/latency bounds to the plan (max iterations, max tool calls, max tokens), mitigating resource-exhaustion risks. citeturn16search3

### Engineering agents

Engineering agents produce *code, configurations, tests, and executable artefacts*. These are the agents most likely to be dangerous if mis-scoped, because “tooling” often implies write access or code execution.

Typical engineering roles:

- **Coder**: Implements a requested module, but cannot modify production directly; outputs patch/diff + tests.
- **Integrator**: Wires modules together; config changes; dependency management; should also output rollback steps.
- **Test author**: Generates unit/integration tests and “tool-call tests” (routing and policy tests).
- **Tool adapter**: Defines tool schemas, argument validators, error handling, and redaction rules.
- **Reliability engineer**: Adds retries, idempotency, rate limiting, circuit breakers, and state checkpoints.

A practical multi-agent engineering pattern is to explicitly separate the “decision-making agent” from an “executor agent” that interfaces with the environment, reducing coupling and increasing reuse. citeturn3view2turn14view2

### Product agents

Product agents translate between human goals and system behaviour. Their core job is to make the system legible, usable, and safe *by default*.

Roles:

- **Requirements writer**: User stories, acceptance criteria, and “non-goals.”
- **UX writer**: User-facing explanations of what happened, why, and what can be done next.
- **Interaction designer**: “Plan-then-execute” UX (show plan, request approvals) to increase user agency and reduce surprise. citeturn2search7turn10view1
- **Evaluation designer**: Defines “what good looks like,” builds rubrics, and chooses test sets aligned to risk.

### Governance agents

Governance agents exist because the system *will* fail in ways that look like success unless you design for auditability.

Roles:

- **Auditor**: Independently validates outputs (correctness, evidence, policy compliance).
- **Security reviewer**: Prompt injection, tool boundary review, data handling, and “excessive agency” checks. citeturn16search6turn6search1turn9view3
- **Risk manager**: Maintains hazard/risk registers, monitors drift and incidents, aligns with TEVV processes. citeturn14view0turn4view3
- **Memory steward**: Controls what gets written to long-term memory to prevent poisoning and duplication. citeturn9view4turn6search7turn6search4

To ground this in Canadian practice culture: the entity["organization","Engineers and Geoscientists BC","engineering regulator bc"] safety-critical software guideline explicitly recommends systematic hazard analysis, reliability techniques (including redundant computation / N-version programming), and checkpoints/backups as reliability measures. citeturn13view0turn13view3 While Dopemux may not be “safety-critical,” importing the discipline of *hazards, mitigations, and recorded artefacts* is high-leverage for multi-agent reliability.

## Agent contract

The contract is the core unit of scale. Without it, “adding agents” is just adding unpredictable degrees of freedom.

A strong contract model is directly analogous to **Design by Contract**: preconditions, postconditions, and invariants specify component behaviour and enable systematic checking. citeturn3view3turn2search23 In an agent system, that becomes: **input schema (preconditions), output schema (postconditions), and behavioural invariants (must-always rules).**

### Contract fields you asked for

Below is a contract spec that is deliberately minimal-but-complete, optimised for predictable outputs and enforcement.

**Agent Contract (normative template)**

**Identity**
- `name`: stable identifier (e.g., `planner.decomposer.v1`)
- `category`: planning | engineering | product | governance
- `version`: semver-like; contract-breaking changes bump major

**Inputs**
- `input_schema`: required fields and types
- `context_requirements`: what context keys must exist (and max length)
- `assumptions_allowed`: explicit list; anything else must be asked or declared unknown

**Outputs**
- `output_schema`: required fields and types
- `status`: `success | partial | blocked | failed`
- `artifacts`: list of produced artefacts (plans, diffs, test results, evidence bundle)
- `traceability`: mapping from artefacts → originating task step(s)

**Tools**
- `allowed_tools`: explicit list (no wildcard)
- `tool_scopes`: read/write permissions, resource allowlists (domains, DB tables, repos)
- `tool_rate_limits`: max calls, cooldowns, max bytes in/out
- `tool_output_sanitization`: what must be stripped/redacted before downstream use

**Forbidden actions**
- `no_side_effects_without_approval`: disallow write tools unless orchestration grants a signed “approval token”
- `no_external_network`: unless explicitly needed and filtered
- `no_secret_access`: may not request, store, or output secrets
- `no_memory_write`: except via Memory Steward agent, or via a specific memory tool with strict schema

**Proof requirements**
This is where “predictability” becomes enforceable. A proof requirement is a required artefact that can be verified mechanically.

Examples aligned to TEVV:
- `tests`: unit/integration tests required for engineering outputs
- `citations_or_sources`: required when claiming factual statements (or declare “no sources used”)
- `tool_call_log`: every tool call must be logged with args + result hashes
- `acceptance_checks`: deterministic validators on the output schema (JSON schema validation, linters, type checks)
- `risk_flags`: if any action touches high-impact scopes, must output risk annotation

This is consistent with NIST’s emphasis on TEVV as an ongoing lifecycle process and with the idea that verification/validation roles should be distinct from the builders. citeturn14view0turn19view0

### Contract enforcement mechanism: “tool gateway + schema gate + termination gate”

A contract is only real if it can be enforced. In practice, three gates catch most catastrophic behaviour:

**Schema gate (before publish):**
Reject any agent output that fails schema validation, missing proof artefacts, or contains disallowed fields. (This is how you prevent “fake completion”: the agent can’t claim success without the required receipts.)

**Tool gateway (before execute):**
Route *every* tool call through a policy engine that checks tool name, scope, arguments, rate limits, and risk class. This is directly motivated by OWASP’s emphasis on insecure output handling (downstream execution of model output) and excessive agency (too many permissions/autonomy). citeturn6search1turn16search6turn5search7

**Termination gate (stop conditions):**
You need explicit “done” semantics. Tool-loop agents often run until a special submit/finish signal occurs; this is a known pattern in agent runtimes. citeturn5search0turn5search24 Dopemux should formalise termination in the contract: max steps, max time, max retries, and explicit “submit” signalling.

## Specialization vs generalization

This is the architectural fork in the road. The wrong choice doesn’t fail fast; it fails as a slow drift into chaos (the worst kind).

### Many small agents

**Benefits**
- **Boundary clarity and unit-testability:** Each agent does one job, so you can validate outputs with strong schemas and deterministic checks.
- **Least privilege is easier:** Small agents can be tool-scoped tightly (important for excessive-agency risk). citeturn16search6
- **Replaceability:** You can swap a single weak link without retraining everything.
- **Better human governance:** Stakeholders can reason about and review each agent’s mandate.

**Costs**
- **Coordination overhead:** Routing complexity rises; inter-agent messaging becomes another attack surface. Surveys of multi-agent collaboration explicitly treat coordination protocols and structures as major design dimensions. citeturn18view1
- **Error cascades:** More hops means more opportunities for hallucinations or misinterpretations to propagate. citeturn11search2turn16search0
- **Cost explosion:** Each “hop” may be another model call; adversaries can amplify this via Model DoS-style prompts. citeturn16search3

### Fewer, more flexible agents

**Benefits**
- **Simpler orchestration:** Fewer routes, fewer contracts, fewer edges.
- **Lower operational cost (sometimes):** Fewer LLM calls and fewer tool loops.
- **Less surface for message corruption:** Fewer handoffs reduces “telephone-game” risk.

**Costs**
- **Harder to constrain:** A generalist agent tends to need broader tools/permissions.
- **Harder to test:** Broad mandates are difficult to validate with deterministic proofs.
- **Harder to audit:** If one agent both plans and executes, you lose the separation that research argues improves predictability and security. citeturn10view1turn14view2

### A practical compromise that scales

A robust compromise is a **small “spine” of stable agents** plus **plug-in specialists**, all under strict contracts:

- **Spine agents (stable):** Router, Planner, Memory Steward, Auditor.
- **Specialists (pluggable):** Coder, Retriever, UX Writer, Security Reviewer, etc.

This mirrors how some multi-agent frameworks describe extensible collaboration mechanisms and roles, and it aligns with plan-then-execute patterns that separate strategic planning from tactical execution. citeturn18view1turn10view1turn16search1

Routing should be explicit and graph-based where possible. In particular, state-machine / graph orchestration is a strong fit for agent workflows because it forces explicit edges, state transitions, and durable execution semantics. citeturn9view0turn5search1

## Auditor pairing and cross-model verification

Auditing is not a vibe. It’s an architecture.

### Independent validation rules

At minimum, treat the auditor as a *separate component* with **different incentives**:

1. **Auditor must not share the builder’s hidden chain-of-thought or scratchpad.** It should receive only the artefacts and a minimal context bundle required to validate them.
2. **Auditor should be tool-limited (or tool-free) by default.** If the builder had tool access, the auditor primarily checks:
   - schema validity,
   - evidence completeness,
   - consistency between cited evidence and claims,
   - test results and reproducibility artefacts,
   - policy compliance logs.
3. **Auditor must be able to fail closed.** If evidence is missing, status must be `blocked`, not `success`.

This fits NIST’s position that TEVV tasks should occur throughout the lifecycle and that verification/validation ideally involve actors distinct from those performing test/evaluation. citeturn14view0

### Cross-model verification

Cross-model verification is the analog of software “design diversity” and redundancy.

In classical fault-tolerant software, **N-version programming** executes independently-developed versions and adjudicates via voting/decision algorithms. citeturn3view4turn2search1 The analogy for Dopemux is: run at least two independent “reasoning implementations” (different model families, or different prompting/constraints) and compare.

However, classic research also warns that “independence” is not guaranteed: correlated failures and common-mode errors occur even with independent teams, often due to shared specs and shared blind spots. citeturn11search4turn11search5 So Dopemux should treat cross-model verification as *risk reduction*, not a proof of correctness.

Concrete pairing rules that reflect this:

- **Diversity requirement:** Use different model families and/or different decoding constraints for auditor vs builder whenever stakes are medium/high. (Avoid “two instances of the same model with the same prompt” as your only check.)
- **Spec perturbation:** The auditor should re-derive key decisions from the *requirements*, not from the builder’s narrative.
- **Disagreement protocol:** If outputs differ, trigger one of:
  - deterministic validator (tests, schema checks),
  - evidence resolution (retrieve cited document, re-check claim),
  - escalation to human approval for high-impact actions.

### When debate helps (and when it doesn’t)

Multi-agent debate can improve reasoning and factuality in some tasks. citeturn11search3 But evaluation work also finds debate protocols can be sensitive and not reliably superior without careful tuning; “more agents debating” is not a free lunch. citeturn11search26

So for Dopemux, treat debate as an *optional* auditing tool, best suited for:
- ambiguous reasoning tasks,
- proposals with multiple plausible approaches,
- situations where you can score outcomes by deterministic checks.

Avoid debate for:
- tasks that demand strict compliance or deterministic transforms,
- high-cost routing situations,
- places where you already have strong validators (tests, schemas).

## Scaling model for adding new agents safely

Scaling is where most multi-agent projects die—not with a bang, but with a slow accumulation of “just this one exception.”

A safe scaling model should combine: inventory control, contract discipline, staged rollout, and decommissioning.

### Agent addition pipeline

Using NIST-style governance language: maintain an inventory of agents and only introduce agents through a controlled process. citeturn19view0

A scalable “agent onboarding” pipeline:

**Design**
- Define the agent’s boundary and contract (schemas, tools, forbidden actions, proof requirements).
- Define its risk class (low/medium/high) based on tool permissions and data sensitivity.

**Verification**
- Build deterministic validators:
  - schema validation,
  - golden tests with fixed inputs,
  - tool-call policy tests,
  - regression tests based on known failures.
- Require TEVV artefacts proportional to risk. citeturn14view0

**Security and autonomy review**
- Check for OWASP-class vulnerabilities:
  - prompt injection surfaces, citeturn9view3
  - insecure output handling paths (output flowing into execution contexts), citeturn6search1
  - excessive agency (unbounded permissions/autonomy), citeturn16search6
  - model DoS / cost runaway risk. citeturn16search3

**Staged rollout**
- Feature flag the agent (off by default).
- Allow invocation only in shadow mode first (produce outputs but do not execute).
- Promote to limited production with budgets and enhanced monitoring.

**Lifecycle management**
- Maintain decommission procedures for agents that become unsafe, obsolete, or too costly. citeturn19view0

### Predictable outputs at scale requires “replayability,” not perfect determinism

Even with temperature=0, seeds, and careful configuration, multiple studies show LLM outputs can vary across runs; evaluation work recommends quantifying uncertainty and using repeats. citeturn17view0turn17view1 Vendor docs similarly describe “best effort” determinism and warn it is not guaranteed even with seeds and backend fingerprints. citeturn15view0turn17view2

For Dopemux, this implies: don’t promise determinism—promise **replay**:

- Log prompts, tool calls, tool results (hashed), model parameters, and backend fingerprints (when available).
- Make agent runs reproducible “as much as the platform allows,” and treat remaining nondeterminism as a measurable uncertainty budget.

## Pre-mortem for Dopemux

This section is intentionally pessimistic: it’s the list of “how you lose” so you can design constraints that make losing harder.

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["multi-agent orchestration architecture diagram planner executor auditor","prompt injection diagram LLM tool use","agent memory poisoning diagram vector database"],"num_per_query":1}

### Architectural failures

**Bad boundaries**
- Your “planner” starts doing execution because it *can*, and then you’ve recreated a monolith with extra steps.
- Your “coder” starts making product decisions because product agents don’t exist or aren’t first-class.
- Result: nobody knows which agent is responsible for what; audits become political theatre.

**Hidden coupling**
- Agents share “helpful” implicit state (a shared scratchpad, a shared memory store, a shared tool context).
- Small changes (prompt tweak, tool behaviour change) break downstream agents in non-obvious ways.
- This mirrors known multi-agent fragility: complex tasks become complicated by compounded inconsistencies and cascading hallucinations. citeturn16search0

**State drift**
- The “shared state object” accretes contradictory facts over many steps.
- Agents stop trusting the plan, start trusting whatever is most recent.
- Drift becomes self-reinforcing: early errors snowball into later rationalisations. citeturn16academia41
- If long-term memory exists, drift can persist across sessions (see memory poisoning below). citeturn9view4

### Agent failures

**Infinite loops**
- Tool-loop patterns can run until an explicit “submit/finish” signal; if the agent fails to converge, you burn budget. citeturn5search0turn5search24
- Loop triggers: ambiguous goals, conflicting instructions, retry-on-error without backoff, tool failures, and missing termination constraints.

**Fake completion**
- The agent returns a plausible answer without producing required proof artefacts.
- This is especially common when schema and proof requirements aren’t enforced hard (fail-open behaviour).

**Tool misuse**
- Insecure output handling: the model outputs code/commands/HTML that gets executed or rendered downstream without sanitisation. citeturn6search1turn6search25
- “Excessive agency”: broad tools + autonomy cause damaging actions based on ambiguous or manipulated outputs. citeturn16search6turn5search7
- Prompt injection: untrusted content gets into the instruction channel; models cannot reliably distinguish malicious from benign instructions. citeturn9view3turn9view4

### Routing failures

**Cost explosion**
- A router that “tries a few agents” becomes a token furnace.
- Model DoS isn’t only attackers—your own routing strategy can behave like one by triggering deep loops and long contexts. citeturn16search3

**Inconsistent outputs**
- Different agents produce different formats, different confidence semantics, and incompatible artefacts.
- Users experience this as “the system is moody.”

**Nondeterminism**
- Even with deterministic settings, outputs can vary across runs and platforms; research quantifies significant variability and recommends treating it as uncertainty to manage, not a bug to eliminate. citeturn17view0turn17view1
- In Dopemux, nondeterminism becomes a routing bug when you branch on fragile textual cues rather than on validated structured fields.

### UX failures

**Cognitive overload**
- If Dopemux exposes all intermediate steps, users drown in “agent chatter.”
- If you hide everything, users can’t form a mental model and lose trust.

**Invisible failures**
- The system silently skips a tool, fabricates results, or “summarises away” uncertainty.
- This is common when you don’t require tool-call logs and schema-validated completion.

**Unusable interfaces**
- Asking users to approve ambiguous actions (“Approve this?”) without context creates decision fatigue and rubber-stamping.

Plan-then-execute UX (show plan first, then execute with approvals) is repeatedly used as a pattern to increase user agency and control, especially in higher-risk tasks. citeturn10view1turn2search7

### Memory failures

**Pollution**
- Long-term memory gets injected with malicious or low-quality data, then influences future reasoning.
- Security research demonstrates indirect prompt injection can poison long-term agent memory by manipulating summarisation and persistence, leading to persistent malicious behaviour across sessions. citeturn9view4
- Newer work identifies memory control-flow attacks where retrieval dominates control flow and forces unintended tool usage. citeturn6search4

**Duplication**
- The agent stores the same fact multiple times in slightly different forms; retrieval returns contradictory “truths.”
- Over time, “memory” becomes a garbage heap with excellent semantic search.

**Wrong promotion**
- Ephemeral, uncertain, or user-specific info gets promoted into durable memory (e.g., misunderstood preferences), becoming sticky system behaviour.

### What to enforce

These are hard constraints—things Dopemux simply refuses to do.

**Control-flow integrity**
- Adopt plan-then-execute for any workflow with side effects: plan generation is non-privileged; execution requires explicit step authorisation. citeturn10view1turn16search1

**Least privilege by construction**
- Tools are scoped per agent and per task step; broad tools are split into granular actions.
- High-impact tools require explicit approval tokens and are disallowed in background loops. citeturn16search6turn5search11

**Mandatory schemas and proof artefacts**
- No agent can return `success` without:
  - schema-valid output,
  - required evidence bundle (tests, citations, tool logs),
  - explicit “done” signal.
- This converts “fake completion” into a measurable failure state.

**Budgets with fail-closed behaviour**
- Hard caps: max tool calls, max iterations, max tokens, max wall-clock time.
- Exceeding caps yields `blocked` with a diagnosable reason.
- This directly mitigates Model DoS / cost runaway patterns. citeturn16search3

**Output sanitisation and safe sinks**
- Never pass raw model output directly into execution contexts.
- Apply strict encoding/sanitisation for the destination (SQL, shell, HTML, etc.), aligning to insecure output handling guidance. citeturn6search1turn6search25

**Memory write quarantine**
- Only a Memory Steward can write to long-term memory.
- Memory writes require:
  - source attribution (which step produced it),
  - durability scoring (“will this still be true next month?”),
  - deduplication,
  - expiry/TTL,
  - and a security filter against instruction injection.
- This is a direct response to demonstrated memory poisoning and control-flow hijacks. citeturn9view4turn6search4turn6search7

**Independent audit on high-risk actions**
- For actions with side effects, require:
  - at least one independent auditor run,
  - plus deterministic acceptance tests where possible.
- Treat cross-model checks as risk reduction, not proof—classical N-version theory supports diversity, but correlated failures are real. citeturn3view4turn11search4turn11search5

If Dopemux enforces the above, failures won’t disappear—but they become *bounded, attributable, and reviewable*, which is the difference between “complex system” and “haunted system.” (One of those is fun only in horror movies.)
