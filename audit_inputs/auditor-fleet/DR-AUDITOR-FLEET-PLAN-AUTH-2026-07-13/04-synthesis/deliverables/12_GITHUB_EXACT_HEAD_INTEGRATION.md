# GitHub Exact-Head Integration

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `12_GITHUB_EXACT_HEAD_INTEGRATION.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Integration objective

`PROPOSED` Accept a narrow, verifiable audit request from GitHub and publish evidence only for the exact PR head that was audited, without executing PR code in a trusted context and without giving the model GitHub write authority.

## Selected later ingress

`PROPOSED` Use a GitHub-hosted, trusted-main workflow that creates a canonical request artifact for **local pull-based pickup**.

The workflow must:

- run from protected base-branch workflow code;
- never check out the PR head;
- never execute candidate actions, scripts, hooks, package installation, tests, or generated binaries;
- fetch PR metadata and diff/patch bytes through GitHub APIs as data;
- record repository ID, PR number, event base SHA, head SHA, workflow path/ref, run ID, run attempt, actor, creation time, expiry, nonce, and payload digest;
- upload only the canonical manifest and inert data payload;
- contain no raw OIDC bearer token and no provider credential.

## Pull-based pickup

`PROPOSED` The local broker polls GitHub with a separate read-only verifier credential. It verifies:

1. repository ID and expected owner/name;
2. workflow run identity and conclusion;
3. exact workflow path and trusted workflow ref;
4. event type and actor policy;
5. run ID and attempt;
6. PR number and current base/head relationship;
7. artifact producer, digest, size, and schema;
8. request expiry and nonce;
9. durable replay status;
10. current head SHA before dispatch.

Artifact attestations may supplement this chain but cannot replace GitHub API verification, freshness, replay protection, or policy authorization.

## Why pull-based pickup

`INFERRED`

- No inbound broker service is required.
- The local host controls polling cadence and can remain dark to the public internet.
- A read-only verifier credential can be isolated from publisher authority.
- The workflow artifact is a data object, not an executable job dispatched onto the local host.

The tradeoff is the need for a local GitHub read credential and polling state.

## Optional OIDC push alternative

`PROPOSED_WITH_LIMITS` A later direct-push mode may use GitHub OIDC with a broker-specific audience and strict claim verification over authenticated TLS. It is not selected for the first automated path because it requires an inbound local service. Raw OIDC tokens must never be stored in artifacts.

## Exact-head verification points

| Point | Check | Failure result |
|---|---|---|
| Request creation | Event base/head values captured | Workflow fails if unavailable |
| Broker pickup | API cross-check of PR and workflow run | `REJECTED_PROVENANCE` |
| Before dispatch | Current head equals request head | `STALE_HEAD` |
| After result validation | Current head still equals request head | `STALE_HEAD` |
| Before publication | Publisher rechecks current head | No publication |
| PR Steward intake | Evidence head equals evaluated PR head | Evidence rejected or stale |

## Publication architecture

`PROPOSED`

### First release

Human operator verifies the current head and publishes or attaches the sealed result manually.

### Later release

A separate least-privilege GitHub App publisher:

- reads only sealed, broker-validated results;
- verifies the broker seal and request digest;
- re-fetches the current PR head;
- creates a check or status for that head only;
- uses an idempotency key derived from repository ID, PR number, head SHA, route, and result digest;
- does not receive provider credentials or execute candidate code.

## Recommended GitHub permission split

| Identity | Read permissions | Write permissions | Secrets |
|---|---|---|---|
| Trusted request workflow | PR metadata and artifact upload as platform permits | Artifact only | No provider secret |
| Broker verifier App | Repository/PR/workflow/artifact read | None | Read-only App credential |
| Publisher App | PR/check metadata read | Checks/status only | Publisher credential only |
| Model adapter | None required | None | One provider credential only |

Exact permissions require a later least-privilege review and account-plan confirmation.

## Stale result policy

`PROPOSED` A result for a superseded head remains retained as historical evidence but cannot be presented as current. It is marked `STALE_HEAD`, excluded from merge-readiness, and must not be silently rebound to the new commit.

## Branch-protection posture

`PROPOSED` Branch protection may require a check emitted by the dedicated publisher. That required check represents the governed intake result, not raw model output. PR Steward and human governance remain the semantic gate.
