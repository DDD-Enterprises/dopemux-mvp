# Containment and Network Architecture

## Core rule

- **PROPOSED:** Every control records what was requested, what was effective, who enforced it, the evidence ref, and confidence.
- **PROPOSED:** `PROMPT_REQUESTED` is a statement of intent only. It cannot satisfy an enforcement requirement.

## Enforcement sources

```text
PROMPT_REQUESTED
RUNNER_ENFORCED
OS_ENFORCED
WRAPPER_ENFORCED
OPERATOR_ENFORCED
UNVERIFIED
```

## Required containment controls

| Control | Label | Required record | Acceptable enforcement for protected routes |
|---|---|---|---|
| Read permissions | **PROPOSED** | roots, patterns, deny list | runner, OS, or wrapper |
| Write permissions | **PROPOSED** | none, allowlist, or unrestricted | OS or wrapper; runner may supplement |
| Worktree isolation | **PROPOSED** | repo, path, branch, marker check | wrapper plus operator workflow |
| File allowlist | **PROPOSED** | exact paths/globs and violation behavior | wrapper or OS |
| Command allowlist | **PROPOSED** | exact commands/patterns and shell policy | wrapper |
| MCP access | **PROPOSED** | deny, allowlisted servers/tools, or unrestricted | runner or wrapper; unknown blocks audit/security |
| Network access | **PROPOSED** | explicit posture and domains/providers | OS/network wrapper or runner where proven |
| Environment redaction | **PROPOSED** | variables retained/removed by name/class | wrapper or OS process launcher |
| Session persistence | **PROPOSED** | ephemeral, persisted, unknown | runner or wrapper evidence |
| Output locations | **PROPOSED** | exact directories/files | wrapper or OS |
| Approval requirements | **PROPOSED** | approval ref/scope/expiry | operator/governance only |

## Default containment profiles

### `READ_ONLY_LOCAL`

- **PROPOSED:** Repo-relative read roots only.
- **PROPOSED:** No writes except router append-only journal when operator invokes `recommend`.
- **PROPOSED:** No MCP by default.
- **PROPOSED:** `OFFLINE` unless a provider call is explicitly part of a future phase.
- **PROPOSED:** Session persistence optional but visible.

### `ADVISORY_PROVIDER`

- **PROPOSED:** Read-only bounded context manifest.
- **PROPOSED:** `APPROVED_PROVIDER_NETWORK` only.
- **PROPOSED:** Environment contains only required provider auth refs, never broad inherited secrets.
- **PROPOSED:** No file writes, commands, MCP, or general network.
- **PROPOSED:** Output goes to a declared temporary or evidence location.

### `BOUNDED_IMPLEMENTATION`

- **PROPOSED:** Dedicated worktree and verified branch.
- **PROPOSED:** File and command allowlists enforced by wrapper.
- **PROPOSED:** Provider network allowed; general web denied unless packet authorizes API lookup.
- **PROPOSED:** MCP denied by default or explicitly allowlisted.
- **PROPOSED:** Environment redaction manifest required.
- **PROPOSED:** Outputs restricted to worktree and proof directory.
- **PROPOSED:** Release one does not use this profile for execution.

### `INDEPENDENT_AUDIT`

- **PROPOSED:** Read-only bounded evidence manifest.
- **PROPOSED:** No shared writable session or worktree with implementer.
- **PROPOSED:** No MCP or tools unless the audit packet explicitly requires a read-only tool and enforcement is proven.
- **PROPOSED:** Disposable session, exact invocation, immutable output hash.
- **PROPOSED:** Independent runner/provider/model/session requirements recorded separately.

### `SECURITY_RELEASE`

- **PROPOSED:** OS/wrapper-enforced read scope, network restrictions, environment redaction, and output protection.
- **PROPOSED:** Human approval required where policy states.
- **PROPOSED:** Unknown enforcement blocks.

## Network postures

### `OFFLINE`

- **PROPOSED:** No provider, web, MCP-over-network, package registry, or remote Git actions.
- **PROPOSED:** Suitable for deterministic policy validation, replay, local inspection, and repository-only classification.

### `SANDBOX_NETWORK_DENIED`

- **OBSERVED:** This posture occurred in local probing and is a containment outcome.
- **PROPOSED:** It may support local analysis but cannot prove provider or host unhealth.
- **PROPOSED:** Health observations from this posture are scoped to the sandbox.

### `APPROVED_PROVIDER_NETWORK`

- **PROPOSED:** Only the selected provider/proxy path is allowed.
- **PROPOSED:** Credential presence, cost/credit posture, privacy, and approval gates must pass.
- **PROPOSED:** Provider access does not authorize general web access.

### `RESTRICTED_DOMAIN_NETWORK`

- **PROPOSED:** A declared domain allowlist supports bounded vendor documentation/API verification or provider endpoints.
- **PROPOSED:** DNS, redirects, and proxy endpoints must remain inside the approved set or fail closed.

### `GENERAL_NETWORK_ALLOWED`

- **PROPOSED:** Requires explicit packet/operator approval.
- **PROPOSED:** Ineligible for independent audit, security, secret-bearing, or release-sensitive routes unless a stronger separate policy authorizes and contains it.

### `UNKNOWN`

- **PROPOSED:** Any route that requires network blocks.
- **PROPOSED:** Offline-only recommendation may proceed if no network behavior is implied.

## Network selection by task class

| Task class | Label | Default posture |
|---|---|---|
| Cheap local read | **PROPOSED** | `OFFLINE` |
| Repository investigation with local tools | **PROPOSED** | `OFFLINE` |
| Model-assisted advisory analysis | **PROPOSED** | `APPROVED_PROVIDER_NETWORK` |
| API lookup | **PROPOSED** | `RESTRICTED_DOMAIN_NETWORK` |
| Implementation | **PROPOSED** | `APPROVED_PROVIDER_NETWORK`; package/web access only if packet-approved |
| Independent audit | **PROPOSED** | `APPROVED_PROVIDER_NETWORK` with bounded input, or `OFFLINE` local auditor |
| Security/release | **PROPOSED** | `RESTRICTED_DOMAIN_NETWORK` or `APPROVED_PROVIDER_NETWORK`; never general by default |
| RTE live extraction | **OBSERVED** | RTE-specific consent/preflight remains authoritative |

## Environment-failure classification

```text
SANDBOX_DENIAL
DNS_FAILURE
PROXY_LOCAL_UNREACHABLE
HOST_SERVICE_UNREACHABLE
AUTH_MISSING
AUTH_REJECTED
RATE_LIMITED
PROVIDER_OUTAGE
FILESYSTEM_DENIED
WORKTREE_MISMATCH
COMMAND_DENIED
MCP_DENIED
UNKNOWN_ENVIRONMENT_FAILURE
```

- **PROPOSED:** Failure classifier records source posture and evidence.
- **PROPOSED:** `SANDBOX_DENIAL`, `FILESYSTEM_DENIED`, `WORKTREE_MISMATCH`, `COMMAND_DENIED`, and `MCP_DENIED` never count as model quality failures.
- **PROPOSED:** `AUTH_MISSING` and `AUTH_REJECTED` do not justify a more expensive model.
- **PROPOSED:** A same-tier alternative is allowed only when its environment path can plausibly resolve the failure and all hard controls remain satisfied.

## Session persistence

- **PROPOSED:** Persistence is a declared route property, not an incidental runner default.
- **PROPOSED:** Independent audits require disposable or isolated sessions.
- **PROPOSED:** Plan-backed desktop/manual routes with persistent history are advisory and require explicit transcript/redaction handling.
- **PROPOSED:** No-session mode can reduce replay evidence, so the wrapper must capture the required output/proof independently.

## Environment redaction

- **PROPOSED:** Start from deny-all and inject only required variables for protected routes.
- **PROPOSED:** Record variable names/classes and whether they were injected or removed, never values.
- **PROPOSED:** Redact authorization headers, cookies, tokens, API keys, private keys, passwords, and secret-pattern files from journal/export content.
- **PROPOSED:** Redaction failure blocks external sharing and protected execution.

## Output control

- **PROPOSED:** Router outputs go to stdout and the router SQLite journal only.
- **PROPOSED:** Future runner outputs go to packet-declared worktree/proof paths.
- **PROPOSED:** Temporary files use a declared workspace or OS temp directory and are either retained as evidence refs or explicitly removed with a receipt.
- **PROPOSED:** A runner cannot choose arbitrary output locations in a certified route.

## Approval separation

- **PROPOSED:** Operator acceptance says “use this recommendation as the next plan.”
- **PROPOSED:** Human approval says “this protected action is authorized under this scope and expiry.”
- **PROPOSED:** They are separate refs.
- **PROPOSED:** Neither can be inferred from a CLI command invocation alone.
