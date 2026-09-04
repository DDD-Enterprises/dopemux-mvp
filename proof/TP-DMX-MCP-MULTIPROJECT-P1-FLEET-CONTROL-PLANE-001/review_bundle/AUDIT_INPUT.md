# Independent Audit Brief: TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001

You are an **independent auditor**, not the implementer. The implementer was
Claude (Sonnet 5). You are being run via `agy`/Gemini 3.1 Pro (a different
model family and runtime) specifically so this audit is independent.

## Repository

Mounted at the path given to `--add-dir` (a real git worktree). Use real
shell commands (git, python, uv, shasum) inside it -- do not trust anything
in this brief you can independently verify.

```text
CONTENT_HEAD_SHA=86fcbd196cece01b3f4503b9778a4cebfaa51a19
BASE_REF=origin/main (328a31e9a48bc20c29f4d1cde79273f587d987ee)
BRANCH=codex/mcp-multiproject-p1-fleet-control-plane
```

Verify `git rev-parse HEAD` equals `CONTENT_HEAD_SHA` before anything else.
Do not audit any commit other than this exact SHA.

## What this packet claims to be

L3 implementation of a dormant MCP "P1 fleet control plane" beneath already-
merged P0 contracts (schemas under `schemas/mcp/*.schema.json`, ADR at
`docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`).
Read the ADR and `task-packets/TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.md`
(and its `.json` sibling) first -- they are the authoritative contract this
diff must satisfy.

Six new modules under `src/dopemux/mcp/`: `identity_registry.py`,
`identity.py`, `service_leases.py`, `ownership.py`, `materialization.py`,
`reconcile.py`, `control_plane.py`, plus a catalog-v2 compiler section
appended to `fleet_catalog.py`, plus minimal touches to
`docker_inspect.py`, `docker_runtime.py`, `runtime_state.py`, and
`mcp_commands.py` (two new read-only CLI preview commands under
`mcp control-plane`).

## Full disclosure: read this before judging the diff

`proof/TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001/implementation-notes.md`
contains four operator disclosures the implementer made proactively:

1. A preflight census miss (a symbol-narrowed grep dropped a file that later
   caused a real problem).
2. A pre-existing P0 test defect
   (`tests/arch/test_mcp_multiproject_contracts.py::test_no_runtime_effect_diff`)
   that the implementer found, stopped, and asked the operator about via an
   explicit choice (rather than silently patching or declaring blocked) --
   the operator authorized widening the packet's allowlist and pinning the
   test to P0's historical merge range instead of the live branch diff.
3. The catalog/topology alias evidence for 3 non-identity-matching servers.
4. One integration point (`fleet.py`) the implementer chose to skip rather
   than force a touch to a live diagnostic report's status computation.

Weigh #2 specifically: is the repair correct, is the allowlist widening
appropriately scoped (only that one file), and is the classification
("operator-authorized packet amendment for a pre-existing P0 defect, not a
substantive repair against P1's one-bounded-repair budget") defensible?

## Adversarial challenges (from the packet's own Task 9 mandate -- check all)

- path/env/session identity laundering
- auto-registration of a registry record from path/cwd/env/probe
- alias collisions (two records claiming the same alias)
- stale generation acceptance
- project/worktree lease crossover
- port/label/probe ownership laundering (does anything let a label or port
  match alone produce `mutation_eligible=true`?)
- catalog `target_class` activation (does anything treat `target_class` as
  live authority instead of inert data?)
- compatibility placement drift (does `legacy_client_projection` correctly
  reconstruct v1 `scope` for every server, including `serena`, whose
  topology `sharing_class` is `WORKTREE_SCOPED` but whose real client wiring
  today is `singleton`?)
- global config materialization (can `materialize_atomic` be tricked into
  writing under `~/.claude`, `~/.codex`, etc.?)
- hidden reconcile mutation (is there truly no start/stop/adopt/migrate
  executor anywhere in `reconcile.py`/`control_plane.py`?)
- live runtime mutation (did implementation or tests ever touch
  `~/.dopemux/mcp/registry/*`, Docker, or `mcp_catalog.yaml`?)
- P2-P8 authority creep (does anything here activate ConPort Wave 2,
  dope-memory migration, Task Orchestrator project-scope migration,
  redis-events isolation, Serena host sharing, or an MCP SDK bump?)
- dependency-file drift (`pyproject.toml`/`uv.lock` must be untouched)

## Specifically verify (don't just read -- run these)

1. `git diff --stat origin/main...HEAD -- mcp_catalog.yaml src/dopemux/mcp/default_catalog.yaml`
   must be empty (`CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED` -- proven zero
   drift by the compiler, but never applied; implementation-notes.md
   explains why with exact file:line citations for the two hard version
   gates this avoids breaking).
2. `uv run --extra test pytest -q tests/mcp/test_identity_registry_v2.py tests/mcp/test_fleet_catalog_v2_runtime.py tests/mcp/test_service_leases_v2.py tests/mcp/test_ownership_v2.py tests/mcp/test_materialization_v2.py tests/mcp/test_reconcile_v2.py tests/mcp/test_control_plane_v2.py`
   -- should be 117 passed.
3. `uv run --extra test pytest -q tests/arch/test_mcp_multiproject_contracts.py tests/arch/test_mcp_fleet_catalog_contract.py tests/unit/test_mcp_commands_catalog.py tests/unit/test_mcp_doctor_repo_aware.py tests/unit/test_mcp_runtime_registry.py`
   -- should be 190 passed (this is the P0 regression suite + the P1
   additions to it; confirms the test defect repair didn't break anything
   else and no other P0 invariant regressed).
4. `python -m jsonschema -i task-packets/TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
5. Independently recompute: does `tests/mcp/test_fleet_catalog_v2_runtime.py::test_fingerprint_equal_between_real_v1_and_legacy_projected_v2`
   actually compare something non-trivial? Read
   `catalog_semantic_fingerprint` in `fleet_catalog.py` and confirm it isn't
   comparing an empty/constant structure. Cross-check against the
   divergence-detection parametrized test right after it
   (`test_fingerprint_detects_real_divergence`) -- do the four mutation
   cases actually change the fingerprint, i.e. is the comparator load-bearing?
6. In `materialization.py`, read `materialize_atomic` and confirm the
   claimed all-or-nothing property: trace what happens if the process dies
   between `os.rename(staging_dir, final_gen_dir)` and the symlink flip
   succeeding. Is `current` provably left pointing at the prior generation
   in that case?
7. Full changed-file list: `proof/TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001/review_bundle/DIFF_NAME_STATUS.txt`.
   Confirm every path is in the packet's `commit.allowlist` and that nothing
   in `OUT` (see the `.md` packet file) was touched.

## Verdict format

Return, in order:

```text
PACKET_ID=TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001
AUDITED_HEAD_SHA=<what you independently ran `git rev-parse HEAD` and got>
HEAD_MATCHES_CLAIMED=YES|NO
VERDICT=PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR
FINDINGS=<numbered list, each CONFIRMED or SUSPECTED, with file:line>
BLOCKING_FINDINGS_COUNT=<n>
CATALOG_CUTOVER_REASONING_SOUND=YES|NO|PARTIAL
P0_TEST_REPAIR_ASSESSMENT=<your independent judgment, not just agreement>
NO_LIVE_RUNTIME_MUTATION_CONFIRMED=YES|NO
AUDITOR_MODEL=<your exact model identifier as reported by `agy models`/your own self-report>
```
