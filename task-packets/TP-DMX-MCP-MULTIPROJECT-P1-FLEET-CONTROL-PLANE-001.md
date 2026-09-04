---
id: TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001
title: Tp Dmx Mcp Multiproject P1 Fleet Control Plane 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-09-04'
last_review: '2026-09-04'
next_review: '2026-12-04'
prelude: Tp Dmx Mcp Multiproject P1 Fleet Control Plane 001 (explanation) for
  dopemux documentation and developer workflows.
---
# TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001

```text
PROGRAM=DMX-MCP-MULTIPROJECT
PARENT=TP-DMX-MCP-MULTIPROJECT-P0-POSTMERGE-CLOSURE-001
RISK_LANE=L3
BASE_MAIN_AT_AUTHORING=328a31e9a48bc20c29f4d1cde79273f587d987ee
BASE_TREE_AT_AUTHORING=30aff5f9ec2637da252f00617641ad31a7946046
R2_ARCHITECTURE_SHA256=fa78556b2d51cd3b22d8c42ff36bd6c3964172ddee6a75662cde61db438e3996

STAGE=IMPLEMENTATION_COMPLETE_AWAITING_INDEPENDENT_AUDIT
P1_PACKET_STATUS=EXECUTED
P1_EXECUTION_AUTHORIZED=YES
REPOSITORY_MUTATION=ALLOWLIST_ONLY
RUNTIME_MUTATION=FORBIDDEN
SERVICE_CUTOVER=FORBIDDEN
CONPORT_WAVE2_AUTHORIZED=NO
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO
```

## Objective

Implement the dormant P1 fleet control plane beneath the merged P0 contracts:

```text
registry-backed identity
catalog-v2 runtime/compiler + compatibility projection
service-lease-v2
ownership evidence
generic atomic materialization
read-only reconcile/adopt planning
control-plane composition
```

P1 stops before every service topology flip and runner-specific activation.

## Execution record

```yaml
execution_record:
  stage: implementation
  runner: Claude Code (Claude Sonnet 5)
  worktree: .worktrees/mcp-multiproject-p1-fleet-control-plane
  branch: codex/mcp-multiproject-p1-fleet-control-plane
  authority_ceiling: exact packet allowlist (operator-widened once, see
    implementation-notes.md); no live runtime mutation or service cutover
  audit:
    required: true
    runner: independent, different model family/runtime from the implementer
    independence: REQUIRED
    status: NOT_YET_DISPATCHED_AT_FREEZE
```

## Current truth at authoring

```text
MAIN=328a31e9a48bc20c29f4d1cde79273f587d987ee
TREE=30aff5f9ec2637da252f00617641ad31a7946046
```

Current source still contained the exact P1 defects at authoring:
- `project_identity.py` derived project identity from project-root path hashing (now: unchanged behavior, annotated locator-only, plus a compatibility bridge).
- `port_leases.py` is schema 1.0 with path/hash/scope authority residue (unchanged; new `service_leases.py` implements v2 alongside it).
- `mcp_catalog.yaml` is version 1 and documents absolute-worktree-path workspace identity (unchanged; catalog-v2 compiler exists but cutover is `BLOCKED_NOT_APPLIED`, see implementation-notes.md).
- merged P0 schemas define registry identity, catalog v2, service lease v2, ownership, and receipt contracts (consumed, not modified).

## IN

Only the exact `commit.allowlist` in `TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.json`,
widened once during execution (operator-authorized) to add
`tests/arch/test_mcp_multiproject_contracts.py` -- see implementation-notes.md.

## OUT

```text
services/**
compose.yml
compose.*.yml
compose.*.yaml
pyproject.toml
uv.lock
scripts/mcp-wrappers/**
live Docker/container state
live identity/lease registry state
ConPort storage/runtime
dope-memory ledger/runtime
Redis streams/groups/data
Task Orchestrator runtime/storage
Serena deployment
shared/global runner configuration
MCP SDK upgrade
```

## Activation strategy

New P1 control-plane mechanics are dormant/default-off. Two read-only preview
CLI commands (`dopemux mcp control-plane identity|reconcile`) are live and
usable, but they never auto-register identity, never write leases, and never
mutate the catalog.

Catalog source cutover to v2 is proven zero-drift by the compiler but was
**not applied** -- `CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED` (see
implementation-notes.md for the exact loader-line reasoning).

Unregistered projects remain `UNKNOWN`; P1 never bootstraps registry identity from a path.

## Rollback

Before any later activation:

```bash
git revert <P1-merge-commit>
```

No runtime cleanup should be necessary: P1 execution/validation never touched
live control-plane or service state. If it had, that would be
`FAIL_P1_UNAUTHORIZED_RUNTIME_MUTATION`.

## Stop conditions

None were triggered as terminal blockers. One near-miss, resolved via
operator authorization rather than a silent workaround: a frozen P0
contract test (`tests/arch/test_mcp_multiproject_contracts.py::
test_no_runtime_effect_diff`) asserted against the live branch diff and
would have failed for any legitimate P1 change to `src/dopemux/mcp/**` --
see implementation-notes.md for the full disclosure and repair.

## Return block

```text
PACKET_ID=TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001
RETURN_STATUS=PASS_P1_FROZEN_FOR_OPERATOR_MERGE_DECISION
BASE_MAIN_SHA=328a31e9a48bc20c29f4d1cde79273f587d987ee
CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED
IDENTITY_REGISTRY=PASS
SERVICE_LEASE_V2=PASS
OWNERSHIP=PASS
MATERIALIZATION=PASS
RECONCILE=PASS
FOCUSED_TESTS=PASS
RELEVANT_SUITE=PASS
CHANGE_CONTRACT=L3_PASS
FINAL_INDEPENDENT_AUDIT=PENDING_DISPATCH
AUDITOR_IDENTITY=UNKNOWN
PROOF_VALIDATION=NOT_RUN
PR_STEWARD=NOT_RUN
REPOSITORY_MUTATION=ALLOWLIST_ONLY
RUNTIME_MUTATION=NONE
SERVICE_CUTOVER=NONE
CONPORT_WAVE2_AUTHORIZED=NO
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO
NEXT_GATE=INDEPENDENT_AUDIT_THEN_OPERATOR_MERGE_DECISION
```
