---
id: adr-dmx-mcp-peer-project-preflight-001
title: 'ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001: Distinguish Peer MCP Instances from Ownership Collisions'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - TP-DMX-MCP-PEER-PROJECT-PREFLIGHT-001
    - adr-mcpint-001
---

# ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001

## Distinguish Peer MCP Instances from Ownership Collisions

**Status:** PROPOSED
**Decision date:** 2026-07-26
**Owner:** Dopemux operator and MCP lifecycle authority
**Scope:** `dopemux-mvp` MCP doctor and lifecycle preflight
**Related implementation packet:** `TP-DMX-MCP-PEER-PROJECT-PREFLIGHT-001`
**Related pull request:** PR #1086, to be superseded rather than merged as-is

---

## 1. Decision summary

Dopemux MCP preflight must distinguish:

1. A **peer-project service instance** whose name matches a service family but whose ports and canonical container identity do not conflict with the target project.
2. A genuine **ownership conflict** involving the target project’s expected container identity or assigned ports.
3. The **Task Orchestrator fixed-port ownership rule**, which remains a separate fail-closed singleton policy.

Peer ConPort and dope-memory containers on non-overlapping ports must not block startup for the target project.

Task Orchestrator remains `single_active_project` on reserved port `7890`. This ADR does not authorize shared multi-project Task Orchestrator state.

---

## 2. Claim ledger

### OBSERVED

* `find_containers_for_service()` currently treats a container as a candidate when either its name contains a generic service hint or its published ports overlap the expected ports.
* Doctor classifies a labelled candidate belonging to another project as `DOCKER_CONTAINER_WRONG_PROJECT` with severity `FAIL`, regardless of why it became a candidate.
* Lifecycle includes `DOCKER_CONTAINER_WRONG_PROJECT` in its blocking finding set.
* Lifecycle only ignores Docker findings when their service is outside the selected service set. A selected peer ConPort or dope-memory therefore blocks startup today.
* PR #1086 contains a candidate non-overlapping-port filter and a corresponding regression test. It also changes Task Orchestrator from `single_active_project` to `multi_project_singleton`.
* Dopemux is the operator control layer responsible for MCP startup and coordination.

### INFERRED

* Generic service-name discovery is useful for diagnostics, but generic name resemblance alone is insufficient evidence that a peer container represents the target project’s service.
* Removing `DOCKER_CONTAINER_WRONG_PROJECT` from lifecycle’s blocking set globally would weaken legitimate ownership protection.
* PR #1086 combines two independently reviewable decisions and therefore has an unsafe scope boundary.

### PROPOSED

* Introduce explicit non-blocking peer-instance findings.
* Preserve hard blocking for exact expected identity or expected-port conflicts.
* Preserve the existing Task Orchestrator single-active-project policy.
* Supersede PR #1086 with a narrow replacement PR.

### UNKNOWN

* Whether current main exposes one reusable canonical helper for computing the exact expected container name in every MCP lifecycle path.
* Whether the local Docker engine remains wedged when implementation begins.
* Whether a later ADR will authorize shared Task Orchestrator state.

---

## 3. Context

Dopemux supports multiple projects with project-scoped ConPort and dope-memory instances. Their allocated host ports can differ safely.

Current discovery is intentionally broad: it searches by generic service-name hints as well as expected ports. The defect appears later, when every foreign labelled match becomes a hard ownership failure even when it does not occupy the target project’s ports and is not the target project’s expected container.

This creates a false-positive chain:

```text
peer container has "conport" or "dope-memory" in its name
  -> broad discovery includes it
  -> foreign project labels produce WRONG_PROJECT
  -> doctor emits FAIL
  -> lifecycle treats finding as blocking
  -> selected services do not start
```

The same treatment must not be applied to Task Orchestrator. Task Orchestrator uses reserved port `7890` and has a separate fixed-port ownership gate. A wrong-project Task Orchestrator holder is a genuine ownership conflict under the currently accepted operating model.

---

## 4. Decision

### 4.1 Candidate discovery may remain broad

Doctor may continue collecting containers by:

* generic service-name hints;
* exact expected container identity;
* expected port overlap.

Broad discovery is diagnostic input only. It does not itself establish ownership or collision.

### 4.2 Classification must consider the match reason

| Condition                                                                                                    | Finding                                                               |     Severity | Start blocking |
| ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- | -----------: | -------------: |
| Foreign project, generic family-name match only, no expected-port overlap, not exact expected container      | `DOCKER_PEER_PROJECT_INSTANCE`                                        |         INFO |             No |
| Unlabelled container, generic family-name match only, no expected-port overlap, not exact expected container | `DOCKER_PEER_INSTANCE_UNLABELED`                                      |         WARN |             No |
| Exact expected container identity with wrong-project labels                                                  | `DOCKER_CONTAINER_WRONG_PROJECT`                                      |         FAIL |            Yes |
| Exact expected container identity with unresolved ownership                                                  | Existing fail-closed unknown finding                                  | UNKNOWN/FAIL |            Yes |
| Any container publishing a target project expected port                                                      | `DOCKER_CONTAINER_PORT_COLLISION` or `DOCKER_CONTAINER_WRONG_PROJECT` |         FAIL |            Yes |
| Correct target labels and expected identity                                                                  | `DOCKER_CONTAINER_MATCH`                                              |         INFO |             No |
| Foreign Task Orchestrator holder on reserved `7890`                                                          | Existing Task Orchestrator wrong-project finding                      |         FAIL |            Yes |

“Exact expected container identity” means the container name generated by the canonical lifecycle naming contract, not a substring such as `conport`.

### 4.3 Do not weaken lifecycle ownership protection

`DOCKER_CONTAINER_WRONG_PROJECT` remains in `BLOCKING_FINDING_CODES`.

The correction must occur by emitting a different finding for genuine non-colliding peer instances, not by globally downgrading the existing ownership-conflict code.

### 4.4 Task Orchestrator remains single-active-project

This ADR preserves:

```yaml
state_scope: single_active_project
reserved_port: 7890
```

It does not authorize:

```yaml
state_scope: multi_project_singleton
```

A Task Orchestrator instance owned by another project must continue to block target-project Task Orchestrator startup. No automatic stop, stealing, adoption, or shared reuse is authorized.

### 4.5 No partial-service continuation in this decision

This ADR does not change the current whole-operation lifecycle semantics when a selected service has a legitimate blocker.

Operators may explicitly select:

```bash
dopemux mcp start --repo <repo> --services conport,dope-memory
```

Once peer-container false positives are corrected, this selection should work even while another project owns Task Orchestrator.

Allowing unblocked services to continue automatically when another selected service is blocked requires a separate ADR.

### 4.6 Docker unavailability remains fail-closed for mutations

When `docker ps` fails or times out:

* doctor must report Docker as unavailable;
* lifecycle must not make container-ownership assertions from missing evidence;
* start mutations remain blocked unless an explicitly accepted degraded mode exists;
* no stale container inventory may be presented as current truth.

The current Docker helper has a bounded timeout and returns structured unavailability rather than an unbounded hang.

### 4.7 PR #1086 disposition

PR #1086 must not be merged as-is.

Its peer-container test and narrow classification concept may be used as advisory source material. Its Task Orchestrator shared-singleton changes, catalog changes, identity changes, proof, and acceptance claims do not transfer to the replacement implementation.

**Disposition:** `SUPERSEDE_WITH_NARROW_REPLACEMENT`

---

## 5. Invariants

The following must remain true:

1. Foreign containers cannot be adopted as target-project services from name resemblance alone.
2. A container occupying a target project’s expected port remains a hard blocker.
3. An exact expected container with wrong or unknown ownership remains fail-closed.
4. Task Orchestrator remains one active project owner on port `7890`.
5. No foreign container is automatically stopped.
6. No project settings, containers, or runtime state are silently mutated by doctor.
7. Docker-unavailable state cannot produce positive ownership claims.
8. The implementation does not introduce shared Task Orchestrator state.
9. The implementation does not add partial-start behavior.
10. Tests must prove the distinction between peer presence and collision.

---

## 6. Consequences

### Positive

* adOps can start its project-scoped ConPort and dope-memory services while dNh project-scoped services remain active on different ports.
* Legitimate ownership and port-collision protections remain intact.
* Task Orchestrator policy remains explicit rather than being changed as collateral damage.
* Multi-project host operation becomes less brittle without relaxing fail-closed boundaries.

### Negative

* Doctor gains a more detailed classification model.
* Operators may see additional informational peer-instance findings.
* Exact container-name derivation must remain synchronized with lifecycle naming.
* Full `mcp up` can still block when another project owns Task Orchestrator.

### Neutral

* This decision does not repair a wedged Docker engine.
* This decision does not make Task Orchestrator multi-tenant.
* This decision does not change allocated ports.
* This decision does not alter `.mcp.json` or `.envrc.dopemux-mcp` generation.

---

## 7. Rejected alternatives

### Remove `DOCKER_CONTAINER_WRONG_PROJECT` from blocking findings

Rejected because it would allow genuine target-name and target-port ownership conflicts to pass preflight.

### Filter every non-overlapping container out before diagnostics

Rejected because peer-instance visibility is operationally useful. They should be reported accurately rather than erased.

### Merge PR #1086 as-is

Rejected because it bundles the peer-instance fix with an unapproved Task Orchestrator authority change.

### Automatically stop foreign containers

Rejected because Dopemux must not seize another project’s active runtime without explicit operator authorization.

### Share Task Orchestrator across projects

Rejected for this ADR. That requires an independent architecture decision covering state isolation, project identity, workflow authority, data partitioning, migration, rollback, and compatibility.

### Add per-service partial continuation now

Deferred. It expands lifecycle semantics beyond the root-cause repair.

### Add a doctor bypass

Rejected because bypassing ownership checks would trade operator friction for silent runtime ambiguity.

---

## 8. Validation requirements

Acceptance requires tests proving:

1. Foreign labelled ConPort on a non-overlapping port produces a non-blocking peer finding.
2. Foreign labelled dope-memory on a non-overlapping port produces a non-blocking peer finding.
3. An expected-port overlap remains blocking.
4. An exact expected container identity with wrong labels remains blocking.
5. An exact expected container identity without trusted labels remains fail-closed.
6. Wrong-project Task Orchestrator on `7890` remains blocking.
7. Lifecycle permits selected ConPort and dope-memory startup when only non-colliding peers exist.
8. Docker timeout produces Docker-unavailable state and no stale ownership claims.
9. `mcp_catalog.yaml` remains unchanged with respect to Task Orchestrator state scope.
10. No `shared_singleton` lifecycle action is introduced.

Final completion requires executed tests, codereview, precommit, embedded audit, proof artifacts, and current PR Steward readiness. Tool output alone is not proof.

---

## 9. Rollback

Rollback consists of reverting the replacement implementation commit and restoring prior doctor classifications.

No database migration, port reassignment, container recreation, or persistent state migration is authorized by this ADR.

---

## 10. Status transition

This ADR may move from `PROPOSED` to `ACCEPTED` when:

* the implementation packet is approved;
* the replacement PR remains within this ADR’s scope;
* required tests pass;
* embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS`;
* PR Steward reports `READY`;
* no Task Orchestrator state-scope change is present.
