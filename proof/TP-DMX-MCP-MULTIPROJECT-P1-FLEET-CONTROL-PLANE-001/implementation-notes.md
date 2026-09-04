# Implementation Notes

## Scope

Implements TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001 against P0's
merged, frozen identity/sharing contracts (`a8a7514b4` / PR #1306,
`328a31e9a` / PR #1311). Base main/tree at authoring:
`328a31e9a48bc20c29f4d1cde79273f587d987ee` / `30aff5f9ec2637da252f00617641ad31a7946046`.
Reharvested and confirmed unchanged at dispatch: `origin/main` was already at
`328a31e9a`, so no drift.

Executed in an isolated worktree (`.worktrees/mcp-multiproject-p1-fleet-control-plane`,
branch `codex/mcp-multiproject-p1-fleet-control-plane`), never reusing an R0/P0
worktree. Overlap reharvest at dispatch: PR #1297 (`feat/t0-semantic-compilation-001`)
touches only `src/dopemux/mcp/capability_compiler.py` and
`config/mcp/capability-shadow-policy.yaml`; PR #1271
(`dependabot/uv/mcp-2.0.0`) touches only `pyproject.toml`/`uv.lock`. Both
remain open and exact-path-disjoint from this packet's diff.

## Disclosure: preflight census miss

The packet's preflight step 1 grep (`rg -n 'scope|state_scope|port_policy|
resolve_project_identity|ProjectIdentity|PortLeaseRegistry' src/dopemux/mcp
src/dopemux/commands tests`) was run and *did* list
`tests/arch/test_mcp_multiproject_contracts.py` in its raw output. When I
narrowed the census from the noisy generic-`scope` match to the specific
symbol names (`resolve_project_identity`/`ProjectIdentity`/`PortLeaseRegistry`/
`state_scope`/`port_policy`), that file dropped out of the narrowed list
because it doesn't reference those specific symbols -- it only diff-checks
paths. That's how the P0 test defect below was missed at preflight instead
of caught before writing any code. Recorded so a future packet's preflight
also greps for "which tests assert directly on `git diff` output," not just
symbol references.

## Disclosure: P0 test defect repaired, allowlist widened (operator-authorized)

`tests/arch/test_mcp_multiproject_contracts.py::test_no_runtime_effect_diff`
asserted P0's own no-runtime-effect invariant
(`FORBIDDEN_P0_PREFIXES` including `src/dopemux/mcp/`) against the *live*
`git diff --name-only origin/main...HEAD`. That makes it fail for **every**
future MCP tranche (P1 through P8) the moment it touches
`src/dopemux/mcp/**` -- exactly what those tranches are chartered to do. The
test was internally inconsistent with the packet series it was written to
protect, discovered when this packet's own verify command list (which
includes this file) started failing on legitimate, fully-allowlisted P1
changes.

This file is **not** in the original P1 `commit.allowlist`. I stopped and
asked the operator via `AskUserQuestion` rather than editing it unilaterally
or declaring `BLOCKED_P1_ALLOWLIST_INCOMPLETE` without surfacing the choice.
Operator selected: *"Widen allowlist + pin to P0's historical range
(Recommended)."* Verified clean before writing the fix:
`git diff --name-only 2b00c648e a8a7514b4` (P0's own merge-base -> merge
commit) contains no `src/dopemux/mcp/`, `mcp_catalog.yaml`,
`src/dopemux/commands/mcp_commands.py`, `services/`, `docker/`, `.mcp.json`,
or root compose paths.

Fix: `test_no_runtime_effect_diff` now diffs `P0_MERGE_RANGE =
("2b00c648e", "a8a7514b4")` instead of `origin/main...HEAD`, asserting a
permanent historical fact about P0 rather than gating every future diff.
This also fixes it for P2-P8, not just this packet.

**Classification: operator-authorized packet amendment repairing a
pre-existing P0 governance-test defect, not a substantive repair against
P1's own one-bounded-substantive-repair budget.** The auditor should treat
this as scope the operator explicitly widened at dispatch time, distinct
from any repair applied after the final independent audit.

`task-packets/TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.json`'s
`commit.allowlist` (published as part of this packet, below) includes
`tests/arch/test_mcp_multiproject_contracts.py` to reflect this.

## Task 1: preflight

Consumer census re-run with precise symbol greps (`resolve_project_identity`,
`ProjectIdentity`, `PortLeaseRegistry`, `state_scope`, `port_policy`)
narrowed the noisy generic-`scope` hits to real consumers. Non-allowlisted
files that reference these symbols but require **no mutation** for P1's
requirements: `lifecycle.py`, `doctor.py`, `port_allocator.py`,
`lease_migration.py`, `port_leases.py`, `task_orchestrator_identity.py`,
`port_diagnostics.py` -- all remain legacy v1 consumers that keep operating
unchanged; P1 builds new v2 modules alongside them, per the dormant/
default-off strategy, rather than modifying their behavior.

## Task 2: registry-backed execution identity

`identity_registry.py` (atomic, generation-versioned store; IDs issued only
by `register_project`/`register_workspace`/`register_instance`, never from
path/env/probe evidence) and `identity.py` (`resolve_execution_identity`,
fail-closed to UNKNOWN/CONFLICTING). `project_identity.py` gains
`as_locator_aliases()` as a compatibility bridge; its existing behavior and
callers are unchanged.

"Stale generation" enforcement for identity resolution itself was
deliberately **not** implemented at this layer -- see the module docstring
in `identity.py`. It's enforced where the schemas actually bind it: at the
lease (`service_leases.lease_verdict`) and, transitively, ownership layers,
via `registry_generation` comparison against the identity registry's current
generation.

## Task 3: catalog-v2 compiler and compatibility projection

`fleet_catalog.py` gains `load_root_catalog_v2`, `join_catalog_topology`,
`compile_catalog_v2`, `legacy_client_projection`, `catalog_semantic_fingerprint`.

**`CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED`**, even though
`test_fingerprint_equal_between_real_v1_and_legacy_projected_v2` proves zero
semantic drift against the real, current `mcp_catalog.yaml`/`default_catalog.yaml`
(byte-identical to each other, confirmed). Reason:
`fleet_catalog.load_root_catalog` (`src/dopemux/mcp/fleet_catalog.py:194`)
and `mcp_commands._load_catalog` (`src/dopemux/commands/mcp_commands.py:576`)
both hard-raise `Unsupported catalog version` when `version != 1`, and the
latter backs every `dopemux mcp start/stop/up/down/status/generate/ensure/
init/add/remove/list/doctor` command. Flipping the live file to
`version: 2` without also making both loaders version-tolerant (accept v1 or
v2, project v2 through `legacy_client_projection` internally) would be an
immediate fleet-wide CLI outage on next invocation -- not a dormant change.
Making `_load_catalog` version-tolerant is out of this packet's
`mcp_commands.py` grant ("read-only identity/catalog/reconcile preview
surfaces only" -- that loader also backs every mutating command). Follow-on
recommendation: a future tranche makes both loaders version-tolerant first;
cutover then becomes a one-line file flip with the compiler already proven.

`mcp_catalog.yaml`/`default_catalog.yaml` are untouched by this packet
(`test_live_catalog_files_are_untouched_by_this_packet` asserts this against
the real diff).

Catalog<->topology join: 3 servers require an explicit alias
(`CATALOG_TO_TOPOLOGY_ALIAS` in `fleet_catalog.py`) beyond identity matching
-- `pal`->`pal-http-wrapper`, `github-official`->`github-official-readonly`,
`task-orchestrator`->`task-orchestrator-kotlin` -- each backed by a
corroborating-text citation in code comments, not name-similarity alone. The
remaining 7 topology rows (`postgres-age`, `redis-primary`, `qdrant`,
`redis-events-engine`, `redis-events`, `python-workflow-service`,
`litellm-and-external-research-proxies`) are non-catalog infrastructure.
The join is closed (0 unresolved, 0 unexplained) against the real data,
verified by `test_topology_join_is_closed_for_real_catalog`.

New v2-only governance fields (`state_authority`, `mutation_class`,
`endpoint_policy`, `probe`, `idle_policy`, and the `identity_scope` remap)
are rule-based off `authority_role`/`transport`/`sharing_class`, are
explicitly **not** part of the semantic-drift comparison (which only covers
profile membership, placement, endpoints, commands/args, environment key
names, tool/admin/aux metadata per the packet's own list), and are
documented as best-effort classification pending P2-P8 domain review.

## Task 4: service-lease-v2

`service_leases.py`: `LeaseKey` enforces the sharing-class key shape at
construction (RETIRED always rejected); `ServiceLeaseRegistry` atomic
persistence; `lease_verdict` is the fail-closed read-side check (ACTIVE is
the only verdict that authorizes anything); `preview_legacy_migration`
classifies legacy v1 `PortLease`-shaped dicts into convertible/ambiguous/
rejected without ever opening the legacy registry file itself (the function
only reads the list it's handed).

## Task 5: ownership evidence

`ownership.py`: `evaluate_ownership` requires all four evidence classes
verified for OWNED/mutation_eligible; an explicit `WRONG_PROJECT` label
denies as FOREIGN even with 3-of-4 verified; a circumstantial
`COMPOSE_MATCH`/`MATCH` label with no formal evidence denies as AMBIGUOUS;
probe-only ("right family, no labels") stays UNKNOWN. `docker_inspect.py`
gains `inspect_container_mounts` (new, read-only `docker inspect --format
'{{json .Mounts}}'`) as the storage/mount evidence source; no existing
function's signature or behavior changed.

## Task 6: generic atomic materialization

`materialization.py`: stage-then-rename-then-flip-symlink pattern (temp
sibling directory -> fsync every file -> atomic directory rename into
`generations/gen-<id>` -> atomic `current` symlink flip). Two
failure-injection tests prove no mixed generations: a mid-write failure
(before the directory rename) and a post-rename-pre-flip failure both leave
the prior complete generation and `current` untouched, with the orphaned
partial/complete-but-unpromoted generation cleaned up. Refuses any
`output_root` overlapping a known shared/global Claude/Codex/OpenCode/
Gemini/Copilot config root (tested against nested and exact-match cases).

## Task 7: read-only reconcile and control-plane composition

`reconcile.py`/`control_plane.py`: pure composition, no executor exists
anywhere in this packet. `build_control_plane_plan` requires
`resolution_status == VERIFIED` or returns an all-blocked, zero-selection
plan. RETIRED `sharing_class` servers are never selected;
`target_class == RETIRED` (e.g. `pal-http-wrapper` today) is inert per
contract and the server *is* still selected -- both directions covered by
tests (`test_target_class_retired_is_inert_and_still_selected`,
`test_sharing_class_retired_is_never_selected`).

Minimal, strictly-additive touches to existing live modules:
- `docker_runtime.py`: `build_v2_labels()` -- new `dopemux.v2.*` label
  namespace, verified disjoint from `build_labels()`'s keys; not called from
  any container-creation path.
- `runtime_state.py`: `canonical_identity_summary()` -- a
  `ProjectIdentityView`-shaped read-only rendering of a
  `ResolvedExecutionIdentity`; no existing function changed.
- `mcp_commands.py`: `dopemux mcp control-plane identity|reconcile`
  read-only preview commands. Both load the identity/lease registries with
  `create_missing=False` (verified by test to never create either store);
  neither touches `_load_catalog`/`_catalog_path` or writes
  `mcp_catalog.yaml`.
- `fleet.py`: **skipped.** No strictly-additive insertion point was found
  without touching `FleetDoctorReport`'s `status` computation or its
  existing report shape. The packet's requirement is "existing fleet/
  runtime_state **may** consume canonical identity for read decisions" --
  permissive, not mandatory -- so this was left for a later tranche rather
  than risk a live-diagnostic-surface regression.

## Task 8: docs and rollback

`docs/03-reference/mcp/multiproject-control-plane.md` documents the
dormant/no-activation boundary, registry/lease paths and test isolation, the
catalog-v2 compatibility gate and cutover stop condition, and rollback
(`git revert <P1-merge-commit>`, no runtime cleanup expected since no live
state was ever written).

## Runtime mutation verification

```text
RUNTIME_MUTATION=NONE
```

No implementation or test in this packet wrote to
`~/.dopemux/mcp/registry/*.json`, started/stopped/adopted a Docker
container, wrote `mcp_catalog.yaml`/`default_catalog.yaml`, or touched
ConPort/dope-memory/Redis/Task Orchestrator runtime state. All registry/lease
tests use `tmp_path`; all CLI-command tests set
`DOPEMUX_MCP_IDENTITY_REGISTRY`/`DOPEMUX_MCP_SERVICE_LEASE_REGISTRY` to
nonexistent `tmp_path` locations and assert those paths remain absent after
invocation.
