# Trust and Threat Model

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `04_TRUST_AND_THREAT_MODEL.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Security objective

`PROPOSED` Process hostile PR evidence without allowing it to reach persistent provider credentials, GitHub write authority, canonical governance state, or unbounded execution surfaces.

## Trust zones

```text
Zone U0: Untrusted contributor content
  PR code, diff, title, body, comments, filenames, instructions, artifacts, caches

Zone G1: GitHub trusted-main request job
  Base-branch workflow, no PR-head checkout, no provider credential

Zone B2: Local Audit Broker
  Request verification, route eligibility, leasing, sealed result spool
  No candidate execution, no provider credential, no GitHub write credential

Zone W3: Credential-free disposable worker
  Mechanical validation or explicitly authorized candidate execution
  No network by default, no persistent secrets

Zone A4: Isolated model adapter
  Per-tool credential boundary, data-only input, no candidate execution
  Disabled until all gates pass

Zone P5: Publisher
  Exact-head GitHub write only, no provider credential, no candidate execution

Zone H6: Human and governance
  Human approval, embedded-audit semantics, PR Steward decision intake
```

## Assets

| Asset | Label | Required protection |
|---|---|---|
| Provider plan sessions, refresh state, API keys | `PROPOSED` | Per-tool isolation, no candidate access, no proof leakage |
| GitHub App keys and installation tokens | `PROPOSED` | Publisher or read-only verifier only, least privilege |
| Private repository diffs and client data | `PROPOSED` | Classification, redaction, route approval, retention proof |
| Broker policy and replay store | `PROPOSED` | Integrity, append-only audit trail, restricted writers |
| Exact-head request and result envelopes | `PROPOSED` | Canonicalization, digest binding, freshness, idempotency |
| Proof artifacts | `PROPOSED` | Redaction, chain of custody, schema validation |
| Worker images and tool profiles | `PROPOSED` | Version pinning, hash capture, revocation on drift |

## Adversaries and failure sources

| Source | Label | Capabilities assumed |
|---|---|---|
| Malicious contributor | `INFERRED` | Controls code, metadata, filenames, instructions, artifacts, caches, timing |
| Compromised dependency or action | `INFERRED` | Executes during unsafe checkout/build, poisons cache or artifact |
| Prompt injection | `INFERRED` | Attempts to induce shell, file, network, plugin, MCP, or disclosure actions |
| Compromised or drifting model route | `INFERRED` | Produces malformed, unsupported, biased, or misleading findings |
| Compromised worker image | `INFERRED` | Exfiltrates inputs, falsifies results, persists state |
| Operator error | `INFERRED` | Selects wrong PR, route, privacy class, or publishes stale evidence |
| Provider or quota failure | `INFERRED` | Causes retries, fallback pressure, incomplete receipts |
| Broker defect | `INFERRED` | Misbinds SHAs, replays requests, overprivileges worker or publisher |

## Primary attack paths and controls

| Attack path | Risk | Enforcement controls | Required response |
|---|---|---|---|
| PR-controlled workflow reaches credential-bearing runner | Secret theft and persistence | Architecture exclusion, runner-group restrictions as defense in depth | Reject design |
| Trusted workflow checks out PR head | Privileged code execution | No PR-head checkout; API diff retrieval only | Fail workflow |
| Diff text instructs model to use tools | Prompt-driven exfiltration | External no-tool profile, data-only adapter, OS/network policy | Terminate and record containment violation |
| Low-trust artifact consumed by privileged worker | Artifact poisoning | Treat bytes as data, verify producer and digest, never execute | Reject artifact |
| Shared cache crosses trust levels | Cache poisoning | No executable shared caches; content-addressed trusted caches only | Purge and revoke image |
| Stale or replayed request | Wrong-code audit | Nonce, expiry, durable replay store, exact-head API recheck | `REJECTED_FRESHNESS` or `STALE_HEAD` |
| Model receives GitHub write token | Repository mutation | Separate publisher, no token in adapter environment | Security incident |
| Broker receives all provider credentials | Cross-tool blast radius | Per-tool OS user/worker, broker invokes narrow adapter boundary | Revoke affected profile |
| Silent provider fallback | Provenance and privacy drift | Exact route profile, fallback disabled, returned metadata validation | Invalidate result |
| Schema-invalid result is salvaged | False proof | Strict result schema, diagnostics separate from governed result | `MODEL_OUTPUT_INVALID` |
| Plan exhaustion triggers premium API | Cost and privacy escalation | Typed environment failure, separate human fallback approval | No automatic fallback |
| Head changes before publication | Stale approval evidence | Final GitHub API head check | Do not publish |

## Enforcement-source matrix

| Control | Prompt | Adapter wrapper | OS user | VM/container | GitHub | Human |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Treat PR content as hostile | ✓ | ✓ |  |  |  | ✓ |
| No PR-head checkout in trusted context |  | ✓ |  |  | ✓ | ✓ |
| Strict request/result schema |  | ✓ |  |  |  |  |
| Exact-head API verification |  | ✓ |  |  | ✓ |  |
| No model GitHub write credential |  | ✓ | ✓ | ✓ | ✓ |  |
| Per-tool credential isolation |  | ✓ | ✓ | ✓ |  |  |
| No-network mechanical worker |  | ✓ |  | ✓ |  |  |
| Shell/file/tool denial | advisory only | ✓ | ✓ | ✓ |  |  |
| Route privacy approval |  | ✓ |  |  |  | ✓ |
| Merge/release approval |  |  |  |  |  | ✓ |

Prompt instructions are never counted as the only enforcement layer.

## Residual risk

`UNKNOWN`

- Complete per-tool egress allowlists are not established.
- Same-host macOS user isolation is not VM-equivalent.
- Model identity attestation remains absent.
- The final disposable-worker technology is not selected.
- Provider credential revocation behavior is incomplete for several plan routes.

These residuals block affected model adapters. They do not justify weakening the architecture.
