# Executive Verdict

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `01_EXECUTIVE_VERDICT.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Verdict

`PROPOSED` **READY_WITH_BLOCKING_QUESTIONS**

The architecture is coherent enough for independent design audit, but model-capable execution remains blocked. The accepted host evidence proves only the static capability probe and the mechanical validation lane. Every local model invocation, plan-auth route, serving-model identity, and live containment claim remains unobserved. `[LOCAL:PROBE_SUMMARY] [LOCAL:MODEL_IDENTITY] [ACCEPTANCE]`

## Selected architecture

### First release

`PROPOSED` Select an **operator-triggered local Audit Broker** with these properties:

1. Dopemux classifies the PR and recommends a route.
2. A human approves the request and route.
3. The broker verifies repository, PR number, base SHA, head SHA, freshness, and payload digests.
4. The broker executes only the mechanical lane automatically, in a credential-free, no-network disposable worker.
5. Model tools are represented in the adapter registry but remain disabled, manual-receipt-only, operator-triggered-but-blocked, or research-only according to their evidence state.
6. The broker emits a sealed result envelope. It does not publish to GitHub and has no merge, release, or governance authority.
7. A human supplies the result to the existing embedded-audit and PR Steward governance paths.

This is the smallest trustworthy release because it uses the one lane that is actually observed, preserves exact-head proof, and avoids laundering installed CLIs into sanctioned automation. `[DR02:F-022] [DR03:F002] [DR04:F04]`

### Later automation

`PROPOSED` Select a **GitHub-hosted trusted-main request workflow with local pull-based pickup**, followed by:

- a local broker with read-only GitHub verification authority;
- disposable credential-free workers for mechanical checks or any candidate-code execution;
- separately isolated per-tool workers for future data-only model adapters;
- a distinct least-privilege GitHub App publisher bound to the exact head SHA;
- PR Steward and the human operator as the decision layer.

The local host does not become a generic Actions runner. GitHub creates a narrow request artifact; the broker verifies and pulls it. `[DR02:F-009] [DR02:F-010] [DR02:F-023]`

## Current execution status

| Route or component | Claim label | Synthesis disposition | Reason |
|---|---|---|---|
| Mechanical validation | `OBSERVED` | `CURRENTLY_IMPLEMENTABLE` | Offline read-only validators are inventoried, with bounded authority. |
| Audit Broker | `PROPOSED` | `DESIGNABLE_BUT_NOT_IMPLEMENTED` | No broker exists in accepted host evidence. |
| Claude Code adapter | `CLAIMED` + `UNKNOWN` | `BLOCKED_PENDING_EVIDENCE` | First-party automation exists, but local auth, full containment, identity, and route certification are unproven. |
| Codex adapter | `CLAIMED` + `UNKNOWN` | `BLOCKED_PENDING_EVIDENCE` | Strong first-party non-interactive surface exists, but local deployment gates remain open. |
| Gemini CLI adapter | `CONFLICTING` + `UNKNOWN` | `BLOCKED_PENDING_EVIDENCE` | Consumer plan route ended; remaining plan runner permission and strict result contract are unresolved. |
| Grok Build adapter | `CONFLICTING` | `OPERATOR_TRIGGERED_OR_BLOCKED` | Headless capability exists, but installed `0.2.99` conformance and plan-session permission are unresolved. |
| AGY / Antigravity adapter | `CONFLICTING` + `UNKNOWN` | `MANUAL_OR_RESEARCH_ONLY` | Programmatic capability is not a proven unattended audit receipt contract. |
| OpenCode adapter | `CLAIMED` + `UNKNOWN` | `RESEARCH_ONLY` | Upstream permission, actual provider, fallback behavior, and identity are unproven. |
| OpenRouter fallback | `CLAIMED` + `UNKNOWN` | `DESIGNABLE_DISABLED` | It is API transport only; exact endpoint privacy, identity, cost, and certification remain gated. |
| Direct provider API fallback | `CLAIMED` + `UNKNOWN` | `DESIGNABLE_DISABLED` | Better trace surfaces exist, but privacy, contract, credential, cost, and certification approval are absent. |

## Non-negotiable architecture rules

`PROPOSED`

- No `UNKNOWN`, `CLAIMED`, or `CONFLICTING` gate maps to unattended execution.
- Candidate code, metadata, instructions, artifacts, and caches are hostile data.
- A credential-bearing generic self-hosted runner is forbidden.
- The broker coordinates execution; it is not canonical authority.
- The model process receives no GitHub write credential.
- The publisher receives no provider credential and no candidate execution capability.
- Environment failure never upgrades model strength, cost, or privacy exposure.
- Mechanical checks are first-class but never exceed each validator's authority.
- No route is currently certified.
- No model result can approve merge or release.

## Rejected directions

| Alternative | Label | Decision | Diagnosis |
|---|---|---|---|
| Persistent generic self-hosted runner with provider credentials | `REJECTED` | Exclude | It combines hostile scheduling, durable secrets, mutable state, and candidate execution in one blast radius. |
| Ephemeral runner with provider credentials and PR-controlled execution | `REJECTED` | Exclude | Ephemerality cleans up after the run; it does not prevent same-run exfiltration. |
| `pull_request_target` plus PR-head checkout | `REJECTED` | Exclude | It converts trusted workflow context into privileged candidate execution. |
| Broker publishes checks directly using a broad token | `REJECTED` | Exclude | Execution coordination and GitHub write authority must remain separate. |
| OpenRouter auto-routing for judge or audit authority | `REJECTED` | Exclude | Silent provider changes weaken provenance, privacy, and independence. |
| Task-router, PAL, agent helper families, or DopeconBridge as canonical audit authority | `REJECTED` | Exclude | They are advisory, helper, bridge, or unknown-authority surfaces, not canonical writers. |

## Blocking questions

`UNKNOWN` The architecture deliberately carries unresolved vendor permission, credential lifecycle, installed-version containment, model identity, network policy, privacy approval, cost measurement, and route performance. These questions block affected adapters, not the mechanical-first architecture itself. The complete register is in `21_OPEN_QUESTIONS.json`.

## Evidence anchors

- `PROBE_SUMMARY.md`, `ROUTING_CONSTRAINTS.md`, `BLOCKERS_AND_UNKNOWNS.json`
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS-FINDINGS.json`
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY-FINDINGS.json`
- `DR-03-FINDINGS.json`
- `DR-04-FINDINGS.json`
- `DR-05-FINDINGS.json`
- `DR-CAMPAIGN-ACCEPTANCE.json`, `SYNTHESIS-INPUT-MANIFEST.json`
