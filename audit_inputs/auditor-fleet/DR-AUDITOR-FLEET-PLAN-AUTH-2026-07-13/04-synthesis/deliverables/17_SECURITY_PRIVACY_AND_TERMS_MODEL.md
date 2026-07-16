# Security, Privacy, and Terms Model

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `17_SECURITY_PRIVACY_AND_TERMS_MODEL.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Governing principle

`PROPOSED` Technical possibility is not vendor permission. A cached credential is not automatically a sanctioned worker identity. A router label is not a privacy contract. A model result is not governance authority.

## Security gates

| Gate | Required evidence | Failure disposition |
|---|---|---|
| Hostile-data separation | Broker and credential zones cannot execute PR-controlled code | Reject architecture or adapter |
| Credential isolation | Per-tool user/VM, no cross-tool secrets | Disable adapter |
| Containment | Installed-version negative checks for every prohibited surface | Disable adapter |
| Network | Enforced worker policy and observed provider behavior | Disable unattended route |
| Exact-head provenance | Repo/PR/SHA/workflow/digest/freshness/replay evidence | Reject request/result |
| Publication separation | Publisher only, no model write token | Security incident if violated |
| Proof integrity | Strict schema, hashes, chain of custody | Reject governed proof |

## Privacy classification

| Class | Definition | Default route posture |
|---|---|---|
| `PUBLIC` | Public repository content without secrets | Certified local or approved public API route |
| `PRIVATE` | Non-public repository content without suspected secrets | Local preferred; approved direct API; OpenRouter default deny |
| `SENSITIVE` | Possible secrets, vulnerabilities, credentials, incident details | No egress until triage; direct approved exception only |
| `CLIENT` | Client data or contract-governed source | Commercial contract and client/privacy approval required |
| `RELEASE` | Signing, provenance, release authority, confidential launch | Model evidence only; no route receives authority |

## Data minimization

`PROPOSED`

- Send the minimum diff and context needed for the audit role.
- Prefer file excerpts over full repository export.
- Remove secrets before route admission.
- Hash prompts, configs, and evidence; do not store redundant raw content.
- Separate operational logs from sensitive payload storage.
- Redact before durable proof and again before GitHub publication.
- Retain manual screenshots or transcripts only when necessary and approved.

## Vendor permission matrix

| Route | Terms posture | Architecture disposition |
|---|---|---|
| Claude Code first-party setup-token | Explicit automation mechanism claimed | Candidate after lifecycle, containment, identity, and certification |
| Claude subscription through OpenCode | Strong terms risk, direct Anthropic confirmation carried | Block |
| Codex Business/Enterprise access token | Explicit trusted workflow mechanism claimed | Candidate after local gates |
| Personal Codex cached auth | Advanced and fragile | Operator-triggered, private, serialized at most |
| Gemini consumer plan auth | Service ended June 18, 2026 | Reject |
| Gemini Workspace/Code Assist plan | Runner permission unknown | Block unattended use |
| AGY plan session | First-party product, lifecycle incomplete | Manual/research only |
| Grok plan session | Headless exists, runner governance unknown | Operator-triggered or blocked |
| OpenCode provider integration | Upstream-dependent | Block until upstream permission proven |
| OpenRouter | Normal API key route | Fallback only, privacy and endpoint approval separate |
| Direct provider API | Normal API route | Exceptional fallback after contract/privacy approval |

## Retention and ZDR

`CLAIMED` Accepted research shows feature-level retention exceptions across direct providers and warns that OpenRouter labels are not definitive upstream policy sources.

`PROPOSED` Route approval must bind:

- exact provider project/account;
- exact endpoint and region where relevant;
- enabled features, tools, caching, grounding, files, storage, and background modes;
- retention and training-use terms;
- DPA or commercial contract status;
- approval date and expiry;
- redaction requirements.

Unknown feature retention blocks sensitive data.

## Cost and privacy coupling

`INFERRED` Cheap fallback often enlarges the trust chain. The system must not trade a small token bill for an unreviewed router, unknown endpoint, or weaker retention posture.

## Plan-use posture

`PROPOSED`

- Treat subscription routes as non-deterministic operator capacity, not a metered queue budget.
- Do not infer per-request plan credits from tokens.
- Do not infer concurrency from a few successful runs.
- Record throttling and reset evidence separately from API cost.
- Do not evade limits through credential sharing or account rotation.

## Governance authority

`PROPOSED` Security and privacy approval determines whether evidence may be produced. It does not determine merge readiness. Embedded-audit and PR Steward consume evidence; the human operator remains approval authority.

## Required reviews before model activation

1. Vendor terms and account-class review.
2. Credential lifecycle and revocation review.
3. Installed-version containment review.
4. Network and telemetry review.
5. Data classification and retention review.
6. Cost-control review.
7. Evaluation and certification review.
8. Independent architecture and security audit.

Until all apply to the exact route, the adapter remains disabled.
