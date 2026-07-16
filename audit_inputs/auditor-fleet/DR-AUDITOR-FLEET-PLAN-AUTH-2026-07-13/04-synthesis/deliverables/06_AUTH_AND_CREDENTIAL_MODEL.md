# Authentication and Credential Model

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `06_AUTH_AND_CREDENTIAL_MODEL.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Core rule

`PROPOSED` Authentication eligibility is not a single switch. A route becomes executable only when all of these gates pass independently:

1. vendor permission;
2. credential type and owner;
3. deployment-class authorization;
4. provisioning without unsupported credential copying;
5. storage and OS isolation;
6. revocation and expiry handling;
7. installed-version conformance;
8. network policy;
9. model/provider identity receipt;
10. route certification.

## Credential classes

| Class | Label | Examples | Allowed posture |
|---|---|---|---|
| `MECHANICAL_NONE` | `OBSERVED` | Git/Python validators | Automatic in credential-free worker |
| `PLAN_INTERACTIVE` | `CLAIMED` | Named-user browser/device login | Manual or operator-triggered only unless vendor explicitly authorizes deployment |
| `PLAN_AUTOMATION_TOKEN` | `CLAIMED` | Claude setup-token, Codex Business/Enterprise access token | Still blocked until local containment and certification pass |
| `PLAN_CACHED_STATE` | `CLAIMED` + `UNKNOWN` | Copied cached login/session | Manual and serialized at most; never shared pool by default |
| `DIRECT_API_KEY` | `CLAIMED` | OpenAI, Anthropic, Gemini, xAI API keys | Exceptional fallback after privacy, cost, containment, and certification gates |
| `WORKLOAD_IDENTITY` | `CLAIMED` | API-side workload identity or service account | API-billed route, never described as plan-backed |
| `OPENROUTER_KEY` | `CLAIMED` | Per-environment router key | Public low-risk fallback by default; exact endpoint policy required |
| `GITHUB_VERIFY` | `PROPOSED` | Read-only GitHub App installation token | Broker verification only |
| `GITHUB_PUBLISH` | `PROPOSED` | Separate publisher App installation token | Exact-head checks/status only |

## Isolation model

`PROPOSED`

Each credential-bearing tool receives:

- a dedicated non-admin OS user or isolated VM;
- a separate home directory and config root;
- a separate keychain or secret store;
- a separate temp and log directory;
- no shared writable plugin, MCP, hook, skill, extension, memory, or cache directory;
- no GitHub write credential;
- no candidate-code execution;
- an explicit revocation handle in the run receipt.

The broker does not read credential files. It calls a narrow per-tool worker boundary and receives only a normalized result.

## Tool authentication dispositions

| Tool | Accepted research posture | Synthesis status | Minimum credential prerequisites |
|---|---|---|---|
| Claude Code | First-party subscription OAuth and one-year setup-token are documented | `BLOCKED_PENDING_EVIDENCE` | First-party token only, owner/seat mapping, inventory and revocation method, dedicated user/VM, effective config proof, route certificate |
| Codex | ChatGPT sign-in, device auth, API key, cached auth, and Business/Enterprise access tokens are documented | `BLOCKED_PENDING_EVIDENCE` | Prefer Business/Enterprise access token for trusted non-interactive use; expiry/admin revocation; no personal shared pool; conformance and certificate |
| Gemini CLI | Consumer AI Pro/Ultra login service ended; fresh headless auth is API/Vertex | `BLOCKED_PLAN_ROUTE` | Exact supported account class or separate API/Vertex route, no consumer-plan claim, isolation, receipt, certificate |
| AGY / Antigravity | First-party CLI/SDK exists, lifecycle incomplete | `MANUAL_OR_RESEARCH_ONLY` | Official unattended lifecycle, revocation, runner class, receipt contract, containment, certificate |
| Grok Build | Headless exists; explicit non-browser route is API key; plan session governance unknown | `OPERATOR_TRIGGERED_OR_BLOCKED` | Installed-version conformance, plan-session permission or separate xAI API route, lifecycle, containment, certificate |
| OpenCode | Headless wrapper and per-user credential storage exist | `RESEARCH_ONLY` | Upstream vendor permission, actual provider identity, deterministic fallback disablement, isolated provider credential, certificate |
| OpenRouter | API key and management controls exist | `DESIGNABLE_DISABLED` | Per-environment key, credit cap, management-key isolation, exact model/provider profile, privacy approval, certificate |

## Credential lifecycle states

```text
UNPROVISIONED
  -> PROVISIONED_DISABLED
  -> CONFORMANCE_PENDING
  -> CERTIFIED_OPERATOR_TRIGGERED
  -> CERTIFIED_AUTOMATED
  -> DEGRADED
  -> REVOKED
```

`PROPOSED` Any change in credential owner, token type, expiry, provider, tool version, config profile, or worker image demotes the route to `CONFORMANCE_PENDING` or `REVOKED`.

## Receipt requirements

Every credentialed run must record, without exposing the secret:

- `credential_class`;
- `credential_owner_type` and non-sensitive owner identifier;
- `deployment_class`;
- `plan_or_api_billing_route`;
- `provisioning_method`;
- `revocation_handle_type`;
- `credential_profile_hash`;
- `effective_config_hash`;
- `tool_version`;
- `requested_model` and observed identity evidence;
- `fallback_used`;
- expiry or rotation policy identifier.

## Prohibited patterns

`REJECTED`

- Copying a human workstation session into a shared runner pool.
- One OS account holding every provider credential.
- Provider credentials in GitHub Actions secrets for PR-controlled jobs.
- Provider and GitHub write credentials in the same worker.
- Treating absence of environment API keys as proof of plan billing.
- Treating browser login success as CI authorization.
- Describing API workload identity as subscription use.
- Logging raw tokens, cookies, keychain records, or auth files in proof.

## Carried unknowns

`UNKNOWN` Token inventory and revocation for Claude setup-token, personal Codex concurrency and machine-copy limits, Gemini organization runner permission, Antigravity lifecycle, Grok plan-session governance, OpenCode third-party authorization, direct provisioning to isolated users/VMs, and provider-attested model identity remain unresolved.
