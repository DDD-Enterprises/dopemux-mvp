# Self-Hosted Runner Option

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `11_SELF_HOSTED_RUNNER_OPTION.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Decision

`REJECTED` A persistent generic self-hosted GitHub Actions runner that can execute PR-controlled workflows while holding provider credentials is excluded from both first-release and later architecture.

`PROPOSED_WITH_LIMITS` Ephemeral self-hosted runners may be used later only as credential-free disposable workers for mechanical validation or separately approved candidate-code execution. They are not the broker and do not receive plan credentials.

## Comparative assessment

| Option | Credential exposure | Hostile execution | Persistence risk | Decision |
|---|---:|---:|---:|---|
| Persistent runner with provider credentials | High | High | High | `REJECTED` |
| Persistent runner without provider credentials | Low | High | High | `DEFERRED`; local broker plus disposable worker is simpler |
| Ephemeral runner with provider credentials | High during run | High | Lower after run | `REJECTED` |
| Ephemeral credential-free mechanical runner | None | Bounded | Low | `PROPOSED_LATER` |
| GitHub-hosted trusted request job | No provider credential | No PR code execution | Fresh hosted environment | `SELECTED_LATER_INGRESS` |
| Local broker that is not an Actions runner | No provider credential | No candidate execution | Controlled local state | `SELECTED` |

## Why persistence is not the only problem

`INFERRED` Ephemerality is a cleanup property, not a same-run confidentiality boundary. A malicious job can exfiltrate a credential before the runner disappears. The architecture therefore separates hostile execution from persistent credentials rather than betting on post-run deletion.

## Conditions for any later self-hosted worker

`PROPOSED`

- Runner group restricted to the intended repository and exact trusted workflow.
- Workflow pinned to a protected ref or full commit SHA.
- No provider credentials, personal sessions, GitHub write token, SSH keys, package-registry secrets, or browser sessions.
- No reuse of artifacts or executable caches from low-trust jobs.
- Disposable VM or hardened image, destroyed after one job.
- External log streaming before destruction.
- No inbound service exposure beyond the runner protocol.
- No shared writable host mounts.
- Network `NONE` for mechanical work by default.
- Current head and request digest revalidated by the broker, not trusted from runner labels.
- Labels used only for scheduling, never as authorization evidence.

## Prohibited workflow patterns

`REJECTED`

- `pull_request_target` followed by checkout or execution of the PR head.
- Candidate-controlled reusable workflows in a privileged context.
- Direct interpolation of PR metadata into shell scripts.
- Downloading and executing PR-produced artifacts.
- Restoring shared executable caches into privileged jobs.
- Passing provider credentials through environment secrets to a PR job.
- Allowing a runner job to publish its own merge-readiness result.

## Broker relationship

`PROPOSED` If an ephemeral runner is introduced, the broker remains the verifier and coordinator:

1. Broker validates exact request and route.
2. Broker creates a credential-free work order.
3. Runner executes one bounded job.
4. Runner returns raw evidence only.
5. Broker validates, seals, and rechecks head.
6. Separate publisher or human publishes.

The runner does not decide route eligibility, accept fallback, or write governance state.

## Persistent dedicated runner alternative

`REJECTED` Naming a machine "dedicated audit runner" does not cure the trust collision. If GitHub can schedule untrusted code onto it, the machine is still generic from the attacker's perspective. Runner groups, environments, and approvals narrow reachability but do not sandbox execution after it begins.

## Current status

| Capability | Status |
|---|---|
| Runner registration | `NOT_AUTHORIZED` |
| Ephemeral worker implementation | `NOT_STARTED` |
| Worker image selection | `UNKNOWN` |
| Network allowlists | `UNKNOWN` |
| External log sink | `DESIGNABLE` |
| Provider credentials on runner | `FORBIDDEN` |
