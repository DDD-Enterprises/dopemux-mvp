# Current State and Evidence Map

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `02_CURRENT_STATE_AND_EVIDENCE_MAP.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Input integrity

`OBSERVED` The synthesis manifest contains 51 accepted records. In the supplied workspace, 49 accepted artifacts are physically present and match their manifest SHA-256 values. Two accepted records, `START_HERE.md` and `PAL_EXECUTION_RULES.md`, are absent. They are not treated as inspected evidence.

`OBSERVED` No hash mismatch was found among the 49 present accepted artifacts.

## Truth order applied

1. `OBSERVED` host and runtime facts from the accepted capability probe.
2. Accepted Deep Research findings and reports.
3. Repository authority and governance contracts.
4. Vendor documentation only as represented in accepted research.
5. `INFERRED` architecture implications.

This ordering prevents a glossy vendor page from repainting a silent local probe as a working system.

## Evidence map

| Evidence class | Accepted artifacts used | What they establish | What they do not establish |
|---|---|---|---|
| Host observations | `PROBE_SUMMARY.md`, `AUDITOR_CAPABILITY_MATRIX.json`, `MODEL_IDENTITY_OBSERVATIONS.json`, `NETWORK_AND_CONTAINMENT_OBSERVATIONS.md`, `BLOCKERS_AND_UNKNOWNS.json` | Installed tools, static flags, no live calls, network-import defect, unknown auth and identity | Live route safety, plan billing, serving model, complete containment |
| Mechanical inventory | `MECHANICAL_VALIDATION_INVENTORY.json`, `ROUTING_CONSTRAINTS.md` | Read-only validators, authority limits, excluded mutating commands | Semantic correctness beyond validator scope |
| Vendor auth and terms | DR-01 report and findings | First-party credential surfaces, plan/API separation, terms risks | Local credential provenance, actual entitlement, complete runner permission |
| Broker and runner security | DR-02 report and findings | Hostile-data model, exact-head requirements, rejected generic runner, separation of publisher | Implemented broker, tested OIDC, selected VM technology |
| Tool containment | DR-03 report and findings | Documented and observed control surfaces, adapter research priority | Live clean-room behavior, exit contracts, identity evidence |
| Routing and evaluation | DR-04 report and findings | Five-class taxonomy, risk floor, route ladder, certification design | Dopemux-specific route quality or certified thresholds |
| Privacy and cost | DR-05 report and findings | API controls, OpenRouter constraints, cost reservation model, privacy classes | Approved route, exact endpoint contract, local total cost |
| Repository authority | `AGENTS.md`, `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `system-boundaries.md` | Dopemux operator authority, bridge non-authority, proof discipline, split system boundaries | A new runtime implementation or canonical audit broker |
| Proof and handoff | `proof-contract.md`, `proof-bundle-schema.md`, `handoff-contract.md` | Existing proof bundle and handoff obligations | The exact embedded-audit machine schema, which was referenced but not supplied as an accepted artifact |
| Advisory routing | `Multi-Model Routing Policy.txt`, `model-routing.policy.yaml` | Stage-routing intent and explicit advisory status | Runtime routing authority or accepted tool/model bindings |
| Acceptance | `DR-CAMPAIGN-ACCEPTANCE.json`, `.md`, `SYNTHESIS-INPUT-MANIFEST.json` | Synthesis authorization and fail-closed carried unknowns | Adapter activation or route certification |

## Current host state

| Fact | Label | Evidence | Architectural consequence |
|---|---|---|---|
| All model-capable live probes were `NOT_RUN` | `OBSERVED` | `PROBE_SUMMARY.md` | No model adapter is executable by default. |
| Local auth mode is unknown for every model CLI | `OBSERVED` | `AUTHENTICATION_AND_TERMS_MATRIX.md` | Plan-backed claims require future deployment-specific proof. |
| Actual serving model is unknown | `OBSERVED` | `MODEL_IDENTITY_OBSERVATIONS.json` | Provider/model-family independence cannot be claimed. |
| Mechanical validation is the only observed usable lane | `OBSERVED` | `PROBE_SUMMARY.md` | First release is mechanical-first. |
| Aggregate Dopemux CLI import attempted network access | `OBSERVED` | `NETWORK_AND_CONTAINMENT_OBSERVATIONS.md` | Offline broker preflight must avoid this import path. |
| A prior `uv` validation created a virtual environment | `OBSERVED` | `PROBE_SUMMARY.md`, `BLOCKERS_AND_UNKNOWNS.json` | Offline validators require a strict read-only allowlist. |
| No automatic tool selection exists | `OBSERVED` | `TOOL_SELECTION_CANDIDATES.json` | Route policy remains recommendation-only. |

## Cross-track synthesis facts

| Synthesis fact | Label | Supporting findings | Use |
|---|---|---|---|
| Vendor permission is necessary but not sufficient | `INFERRED` | DR-01 plus DR-02/03 | Split eligibility into permission, credential, containment, identity, network, privacy, and certification gates. |
| Codex and Claude Code are first conformance candidates, not selected lanes | `INFERRED` | `DR03-F020`, `DR04-F24` | Research ordering only. |
| OpenRouter metadata is useful provenance, not attestation | `INFERRED` | DR-03/05 | Keep it fallback transport only. |
| Mechanical evidence can close only narrowly allowlisted evidence changes | `PROPOSED` | `DR04-F04` | Prevent semantic overclaim. |
| Same-provider dual calls are not strong independence | `PROPOSED` | `DR04-F11` to `F14` | Record independence dimensions explicitly. |
| Environment failure is not model-quality evidence | `PROPOSED` | DR-02/04/05 | No automatic premium escalation. |

## Carried contradiction groups

`CONFLICTING`

1. **Codex entitlement scope:** accepted OpenAI sources present different complete plan lists.
2. **Claude through OpenCode:** the strongest prohibition evidence is an OpenCode claim, not matching Anthropic legal text.
3. **Grok Build:** current headless documentation does not prove installed `0.2.99` containment or plan-session runner permission.
4. **AGY:** first-party programmatic surfaces coexist with no proven deterministic unattended audit receipt.
5. **OpenCode:** configured provider/model does not prove actual upstream provider or disabled fallback.
6. **Artifact attestations:** useful provenance support, not established request authorization.
7. **Vendor sandbox docs versus host proof:** documented controls do not replace installed-version conformance.
8. **OpenRouter data labels:** useful filters, not definitive upstream privacy authority.
9. **Provider budget controls:** some are alerts or delayed caps, not synchronous hard stops.

The full verbatim carried contradiction list remains in `21_OPEN_QUESTIONS.json`.

## Unknown groups and blocking scope

| Group | Label | Blocks |
|---|---|---|
| Auth and credential lifecycle | `UNKNOWN` | Unattended plan-backed adapters |
| Installed-version containment and exit behavior | `UNKNOWN` | Clean-room promotion and reliable orchestration |
| Actual provider/model identity | `UNKNOWN` | Strong independence and route proof |
| Route performance and thresholds | `UNKNOWN` | Automatic routing and certification |
| Privacy and client-contract approval | `UNKNOWN` | Private or sensitive egress |
| Plan debit and concurrency | `UNKNOWN` | Subscription queue sizing and automated admission |
| Local operational cost | `UNKNOWN` | Numeric total-cost comparison |
| Exact disposable-worker technology | `UNKNOWN` | Implementation choice, not architectural separation |

## Evidence posture for synthesis outputs

`PROPOSED` Every architecture artifact must maintain four separate concepts:

- what exists on the host;
- what vendors claim is possible;
- what the architecture proposes;
- what remains blocked.

A component can be fully designed and still be non-executable. That is not a defect. It is the point of the gate.
