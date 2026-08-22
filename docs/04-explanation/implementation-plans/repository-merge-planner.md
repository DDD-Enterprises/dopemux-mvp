---
title: "Repository Merge Planner Implementation Plan"
type: explanation
status: draft
prelude: "Fixture-first implementation sequence for the read-only merge planner."
tags: [implementation-plan, control-tower, repository-planner]
---

# Repository Merge Planner Implementation Plan

> **Execution gate:** Create and validate a canonical Dopemux Task Packet before
> implementation. Governance/authority-boundary changes require one independent
> embedded audit only after the content head is frozen.

**Goal:** Deliver a read-only, source-backed vertical slice across Dopemux,
dNh CRM, and AdOps, then enable automatic GitHub evidence refresh and approved
conversation-decision intake.

**Architecture:** Pure projection core under
`src/dopemux/repository_planner/`, loopback service under
`services/repository-planner/`, and React/MUI feature under
`ui-dashboard/src/features/repository-planner/`. Existing DCP nine-family
facade remains unchanged.

## Constraints

- `authority = NONE`; no project/TO/GitHub mutation.
- GitHub transport supports allowlisted `GET`/`HEAD` only.
- dNh `tools/gov` semantics are the producer-contract source.
- AdOps uses an adapter/export, not a second greenfield kernel.
- Runtime/source truth outranks this plan.
- Missing evidence remains `UNKNOWN`.
- Frozen fixture first; live network second.
- No OpenRouter/OpenCode/custom proxy route.
- No model call until the packet's single final embedded-audit stage.

## Task 0: Create the canonical implementation packet

**Files:**

- Create: `task-packets/TP-DMX-REPOSITORY-MERGE-PLANNER-001.json`
- Modify: `task-packets/INDEX.md`
- Later create: `proof/TP-DMX-REPOSITORY-MERGE-PLANNER-001/**`

The JSON must validate against
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` and pin:

- repo identity/marker and base branch/commit;
- L2 governance/authority-boundary risk;
- exact code, schema, service, UI, fixture, docs, and proof allowlist;
- no-write invariants;
- validation and embedded-audit obligations;
- stop conditions for credentials, unexpected runtime wiring, or scope drift.

First validation:

```bash
python -m jsonschema -i task-packets/TP-DMX-REPOSITORY-MERGE-PLANNER-001.json +  docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
```

## Task 1: Freeze the source-backed vertical-slice fixture

**Files:**

- Create: `tests/fixtures/repository_planner/portfolio_v1/`
- Create: `tests/fixtures/repository_planner/portfolio_v1/SOURCES.json`
- Create: `tests/repository_planner/test_fixture_integrity.py`

Capture one read-only snapshot for each repository:

- Dopemux: a current packet/proof/PR example;
- dNh CRM: a `tools/gov` proof/readiness example;
- AdOps: PR `#277` plus the local-only legacy candidate represented as
  blocked evidence context, never as ready.

`SOURCES.json` records repository, ref/commit, GitHub URL/path, fetched time,
content SHA-256, license/privacy classification, and redaction notes.

Tests first:

- every fixture file is listed and hashed;
- no secrets/tokens/local absolute paths;
- local-only candidate -> `REMOTE_COMMIT_ABSENT`;
- at least one blocking conflict and one unknown are present;
- fixture bytes validate independently of network.

## Task 2: Define strict models and schemas

**Files:**

- Create: `src/dopemux/repository_planner/__init__.py`
- Create: `src/dopemux/repository_planner/models.py`
- Create: `schemas/project_control_plane/repository-planner-source.v1.schema.json`
- Create: `schemas/project_control_plane/repository-planner-portfolio.v1.schema.json`
- Create: `tests/repository_planner/test_models.py`

Model:

- source/provenance references;
- freshness and source errors;
- repository/lane/candidate/audit/decision evidence;
- dNh-compatible readiness;
- lifecycle facts separately;
- conflicts with materiality;
- unknowns;
- recommendations and simulation marker.

Use strict canonical objects. Reject unknown top-level fields. Require
`authority: NONE` and `surface_class: PROJECTION`.

## Task 3: Implement adapters

**Files:**

- Create: `src/dopemux/repository_planner/adapters/base.py`
- Create: `src/dopemux/repository_planner/adapters/dnh_v1.py`
- Create: `src/dopemux/repository_planner/adapters/adops_v1.py`
- Create: `src/dopemux/repository_planner/adapters/dopemux.py`
- Create: `tests/repository_planner/test_adapters.py`

Adapters accept verified bytes plus source locator and return normalized
evidence. They do not fetch, repair, mutate, or infer readiness from absence.

Tests cover:

- dNh readiness vocabulary preserved;
- AdOps malformed/missing export isolated;
- Dopemux runtime truth and packet scope kept distinct;
- Task Orchestrator state has `authority: NONE`;
- unapproved conversation context cannot become a decision;
- unknown producer fields do not leak into canonical fields.

## Task 4: Render the first useful screen from fixtures

**Files:**

- Create: `ui-dashboard/src/features/repository-planner/types.ts`
- Create: `ui-dashboard/src/features/repository-planner/RepositoryPlannerPage.tsx`
- Create: `ui-dashboard/src/features/repository-planner/PortfolioTable.tsx`
- Create: `ui-dashboard/src/features/repository-planner/LaneDetails.tsx`
- Create: `ui-dashboard/src/features/repository-planner/ConflictPanel.tsx`
- Create: `ui-dashboard/src/features/repository-planner/ProvenancePanel.tsx`
- Create: `ui-dashboard/src/features/repository-planner/__tests__/`

The initial UI loads a checked-in generated fixture module. It must show all
three repositories, ready/blocked/unknown states, a conflict comparison, and
claim-level provenance before any service exists.

Tests cover keyboard navigation, semantic status text, focus return, error
states, and reduced-motion behavior.

## Task 5: Add deterministic conflict and merge-order logic

**Files:**

- Create: `src/dopemux/repository_planner/conflicts.py`
- Create: `src/dopemux/repository_planner/planner.py`
- Create: `tests/repository_planner/test_conflicts.py`
- Create: `tests/repository_planner/test_planner.py`

Tests first:

- blocking conflict -> `DEFER`;
- non-blocking conflict remains visible;
- missing dependency -> `WAIT_DEPENDENCY`;
- cycles produce explicit blockers;
- stale source -> `DEFER`;
- failed/missing audit cannot become ready;
- explicit override remains `CONTROL_TOWER_REVIEW`, never auto-merge;
- tie-breaker is project ID, lane ID, candidate SHA;
- randomized input ordering yields byte-identical recommendation ordering;
- simulation never changes source snapshot.

## Task 6: Add the loopback read API and refresh cache

**Files:**

- Create: `services/repository-planner/app.py`
- Create: `services/repository-planner/config.py`
- Create: `services/repository-planner/refresh.py`
- Create: `services/repository-planner/pyproject.toml`
- Create: `services/repository-planner/tests/`

Endpoints:

- `GET /health`
- `GET /v1/portfolio`
- `GET /v1/projects/{project_id}/lanes/{lane_id}`
- `POST /v1/refresh` only if implemented as a loopback operator trigger that
  performs read-only collection; name and docs must state it mutates cache only.

Prefer `POST /v1/refresh` for honest cache mutation, while proving it has no
external write capability. If the no-mutating-route acceptance rule is retained,
replace it with a UI client-side refresh request to a `GET` endpoint using
cache-control semantics; choose one contract in the Task Packet and test it.

The cache retains last-known data as stale/degraded. One source failure does not
erase others.

## Task 7: Add the allowlisted GitHub reader

**Files:**

- Create: `src/dopemux/repository_planner/github_reader.py`
- Create: `config/repository-planner.sources.yaml`
- Create: `tests/repository_planner/test_github_reader.py`

Use a transport interface whose method enum is only `GET`/`HEAD`. Validate
repository/ref/path against configuration before constructing URLs. Enforce
api.github.com host and reject redirects elsewhere.

Tests cover:

- POST/PATCH/PUT/DELETE impossible or rejected before transport;
- arbitrary repo/URL/ref rejected;
- token absent from logs/errors/models;
- ETag/304 flow;
- rate limit and auth errors sanitized;
- bounded concurrency/timeouts;
- stale fallback;
- submodule/archive/path traversal rejected.

No real network call is required for unit tests.

## Task 8: Wire live refresh into the UI

**Files:**

- Create: `ui-dashboard/src/features/repository-planner/api.ts`
- Create: `ui-dashboard/src/features/repository-planner/hooks.ts`
- Modify: the verified dashboard route/navigation files named by Task 0 inventory
- Modify: `services/registry.yaml` only if the service is actually launched

Feature flag defaults off until the service health contract passes. Fixture mode
remains available. Show last success, age, next refresh, current/stale/degraded,
sanitized source errors, and manual cache refresh progress.

Do not invent a port. Inventory `services/registry.yaml` and active entrypoints
in Task 0, then pin the chosen port and launch wiring in the packet.

## Task 9: Add approved conversation-decision proposals

**Files:**

- Create: `src/dopemux/repository_planner/decision_proposals.py`
- Create: `ui-dashboard/src/features/repository-planner/DecisionProposal.tsx`
- Create: corresponding Python/TypeScript tests

The service accepts an allowlisted thread locator or manual text and produces a
local proposal with normalized text, scope, source hash, and target repository.
It does not approve or commit.

Tests prove:

- non-allowlisted sources rejected;
- raw transcripts not persisted by default;
- proposal has `authority: NONE`;
- approval cannot be performed through planner API;
- manual fallback is marked manual;
- conflicting decision becomes visible reconciliation input.

Actual repository commit/promotion remains a separate project-authority action.

## Task 10: Verification and proof

Run the exact packet-pinned commands, including:

```bash
pytest -q tests/repository_planner services/repository-planner/tests
npm --prefix ui-dashboard test -- repository-planner
python3 scripts/governance/validate_change_contract.py +  --base origin/main --head HEAD --format text
python scripts/docs_validator.py
git diff --check
```

Also verify:

- OpenAPI/request router has no project/GitHub/TO write path;
- network mock saw only allowlisted GitHub `GET`/`HEAD`;
- source fixtures still match `SOURCES.json`;
- repeated fixture projection is byte-identical;
- DCP nine-family registry is unchanged;
- Task Orchestrator remains non-authoritative;
- feature flag defaults safe.

Freeze the content head. Then perform exactly one independent embedded audit
using the repository-authorized route and bind proof to the exact head. Do not
use OpenRouter, OpenCode, or a custom proxy. If auditor identity, credentials, or
route evidence is unavailable, record `SKIPPED`/`NEEDS_SUPERVISOR` and keep
the PR blocked.

## Delivery checkpoints

1. **Checkpoint A:** Task Packet + frozen fixtures + strict schemas.
2. **Checkpoint B:** fixture-backed interactive UI with provenance/conflicts.
3. **Checkpoint C:** deterministic planner + loopback API.
4. **Checkpoint D:** authenticated GET/HEAD refresh.
5. **Checkpoint E:** local decision proposals + final proof/audit.

Each checkpoint is independently reviewable. No checkpoint grants terminal
authority.
