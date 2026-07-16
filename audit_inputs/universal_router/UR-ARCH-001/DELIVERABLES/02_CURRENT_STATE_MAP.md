# Current State Map

## Baseline

- **OBSERVED:** The accepted static census baseline is commit `b176747b339685e781de04268c46b7ae123abfbf` on `origin/main` as recorded on 2026-07-10.
- **OBSERVED:** The census performed no provider calls, service starts, config installs, or source/config edits.
- **OBSERVED:** Live host availability, credentials, provider health, and desktop entitlement were outside that census and remain `UNKNOWN` unless separately observed.

## Current routing and execution slices

| Label | Slice | Current authority | Current state | Router treatment |
|---|---|---|---|---|
| **OBSERVED** | Operator control | `dopemux` CLI | Active operator entrypoint | Reference and extend with a new `route` command group. |
| **OBSERVED** | DCP classification | `src/dopemux/dcp/routing_classifier.py` | Pure, fail-closed, no runner dispatch | Consume `DCPClassificationRef`; do not duplicate semantics. |
| **OBSERVED** | DCP backend preference | `routing_backend_policy.py` | Inert recommendation, not execution permission | Treat as advisory input only. |
| **OBSERVED** | Quota, cooldown, paid cap, admission | Freeflow | SQLite-backed subsystem | Request/read `FreeflowAdmissionDecision`; never copy its ledger. |
| **OBSERVED** | Provider proxy and fallback transport | LiteLLM manager/proxy | Active infrastructure with overlapping config/manager surfaces | Use read-only adapter first; do not create another proxy manager. |
| **OBSERVED** | Proxy telemetry | LiteLLM trace callback | Partial token/model/provider observations when enabled | Normalize as `ModelIdentityObservation` and `UsageObservation`; never treat as attestation by default. |
| **OBSERVED** | Specialized extraction routing | RTE v5 plus its model map and pricing | Active extraction-specific route ladders, preflight, strict-schema, spend artifacts | Keep canonical and isolated; reference its decision. |
| **OBSERVED** | Workflow views and transitions | Task Orchestrator | Active workflow authority | Router may publish a projection reference; no workflow mutation. |
| **OBSERVED** | Capability-family assignment | Task Orchestrator `AgentCoordinator` | Chooses ConPort/Serena/PAL capability families, not provider model IDs | Leave isolated. |
| **OBSERVED** | Execution after accepted handoff | external dopetask via `scripts/dopetask` | Canonical execution boundary | Router stops before execution in release one. |
| **OBSERVED** | Proof and handoff evidence | existing proof/handoff contracts | Existing governance authority | Reference by ID and artifact location; do not fork schemas. |
| **OBSERVED** | Independent audit result | existing embedded-audit/proof surfaces | Separate verdict authority | Reference only. |
| **OBSERVED** | PR review intake/readiness | PR Steward | Post-PR evidence gate | Reference only; never choose routes. |
| **OBSERVED** | Human approval | operator/governance plane | External to automatic route selection | Store only `HumanApprovalRef`, never approval authority. |

## Active Dopemux provider path

1. **OBSERVED:** The Dopemux CLI exposes routing commands.
2. **OBSERVED:** `RoutingConfig` loads and validates user routing configuration and can materialize LiteLLM/CCR configuration.
3. **OBSERVED:** Freeflow may rank or admit candidate routes under quota, cooldown, privacy, and paid-cap rules.
4. **OBSERVED:** LiteLLM performs provider proxying when the operator has started and configured the relevant services.
5. **OBSERVED:** Structured trace logging is optional and is not proof that every request is logged.
6. **PROPOSED:** The Universal Router should sit before Freeflow admission as a cross-lane recommender and after DCP classification as an orchestration decision maker.

## Active RTE path

1. **OBSERVED:** RTE selects extraction-specific cost profiles and route ladders from its own tracked map.
2. **OBSERVED:** RTE owns provider locks, strict-schema requirements, repair/sidefill behavior, preflight, request options, pricing, and spend artifacts for extraction runs.
3. **PROPOSED:** Universal routing must not replace, flatten, or globally reinterpret those RTE rules.
4. **PROPOSED:** A universal route may recommend `RTE_SPECIALIZED` and then reference the RTE route decision when one exists.

## Local runner evidence

| Label | Runner | Proven locally | Not proven locally | First-release use |
|---|---|---|---|---|
| **OBSERVED** | Codex CLI 0.144.1 | Non-interactive execution, JSONL, output schema, read-only sandbox, ephemeral session; one contained smoke succeeded | Provider-attested actual model, credits/cost, hard tool denial, subagent inheritance | Advisory candidate only; no execution in release one. |
| **OBSERVED** | Claude Code 2.1.178 | Model and effort flags, print mode, JSON/schema output, no-session persistence, tool selection, budget cap, agent listing | Successful contained authenticated smoke, provider-attested identity, subagent inheritance | Advisory fallback candidate. |
| **OBSERVED** | Gemini CLI 0.46.0 | Model flag, headless prompting, JSON/stream JSON | Safe no-tool/no-persistence containment, reasoning control, identity, usage/cost | Broad-context advisory candidate only when a fresh snapshot allows it. |
| **OBSERVED** | AGY 1.1.1 | Model flag, print/prompt mode, agent selection | Structured output, hard containment, usage/cost, actual identity, authentication | Preferred audit route is `UNKNOWN` until a safe capability snapshot proves it. |
| **OBSERVED** | LiteLLM 1.89.1 | Installed, callback interfaces present, Dopemux integration source exists | Live host health and provider calls from the probe environment | Observation/proxy adapter only. |
| **OBSERVED** | OpenRouter local configuration | Configured aliases exist | Key availability, live route, strict-free admission, actual provider identity | Treat as unavailable or unknown unless a fresh health/admission snapshot says otherwise. |

## Dormant, advisory, or prohibited foundations

- **OBSERVED:** `services/task-router` has no tracked source and no active caller in the current census.
- **PROPOSED:** Do not revive it.
- **OBSERVED:** `src/dopemux/agent_orchestrator.py` is test-imported and scaffold/mock-oriented, not proven runtime authority.
- **PROPOSED:** Classify it `LEAVE_ISOLATED`.
- **OBSERVED:** `services/agents/**` has no proven production dispatch or usage ledger.
- **PROPOSED:** Classify it `LEAVE_ISOLATED`.
- **OBSERVED:** `config/ai/model-routing.policy.yaml` is advisory and has no observed runtime reader.
- **PROPOSED:** Do not silently promote it. Migrate useful rules through a reviewed, versioned executable policy.

## Missing universal capabilities

| Label | Missing capability | Consequence |
|---|---|---|
| **OBSERVED** | No cross-subsystem universal decision record | Current systems cannot explain one complete recommendation without synthesis. |
| **OBSERVED** | No canonical capability/provider-health snapshot owner | Availability and runner capability are scattered and fast-decaying. |
| **OBSERVED** | No provider-attested identity contract | Pinned-model, benchmark, and independent-audit claims cannot be certified reliably. |
| **OBSERVED** | No universal usage normalization | Tokens, estimates, costs, and credits can be conflated. |
| **OBSERVED** | No executable universal policy owner | Advisory proposals cannot safely drive runtime. |
| **PROPOSED** | Add only these narrow capabilities inside Dopemux Universal Router. | Avoids creating a parallel platform. |

## Required record separation

| # | Label | Record | Owner |
|---:|---|---|---|
| 1 | **OBSERVED** | DCP classification result | DCP |
| 2 | **PROPOSED** | Universal orchestration decision | Universal Router |
| 3 | **OBSERVED** | Freeflow admission decision | Freeflow |
| 4 | **OBSERVED** | LiteLLM provider/proxy observation | LiteLLM integration |
| 5 | **OBSERVED** | RTE specialized route decision | RTE |
| 6 | **PROPOSED** | Runner execution request | Future runner adapter caller, not release-one automation |
| 7 | **OBSERVED** | Dopetask accepted handoff | dopetask/handoff authority |
| 8 | **OBSERVED** | Validation result | Validator/test system |
| 9 | **OBSERVED** | Independent audit result | Auditor/proof system |
| 10 | **OBSERVED** | PR Steward readiness | PR Steward |
