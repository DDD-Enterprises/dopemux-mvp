---
id: adr-mcpint-001
title: 'ADR-MCPINT-001: mcp_catalog.yaml v2 as the Single Source of Truth for the MCP Fleet'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-17'
next_review: '2026-10-14'
prelude: Extends mcp_catalog.yaml to v2 (tools pointer, agents exposure matrix, workflows refs), makes the generate pipeline the sole producer of every agent config and instruction-surface header, kills the legacy src registry, and fixes runtime-refuted transport claims.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-mcpint-002
    - adr-mcpint-003
    - adr-mcpint-004
    - adr-mcpint-005
    - adr-223
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR-MCPINT-001: mcp_catalog.yaml v2 as the Single Source of Truth for the MCP Fleet

**Status**: Accepted
**Date**: 2026-07-16
**Accepted**: 2026-07-17 — accepted by operator with PR #1073; gate answers G1-G5 2026-07-16/17; SVCFEAT reconciliation confirmed 2026-07-17.
**Owners**: @hu3mann (program DMX-MCPINT, root `af10eefd`)

## Context

Three disjoint registries currently describe the MCP fleet, and none of them matches the
running fleet (runtime verification: `claudedocs/mcp-fleet-runtime-verification-2026-07-16.md`,
"P0" below; feature register: `docs/03-reference/mcp/feature-register.yaml`):

1. **`mcp_catalog.yaml`** (v1, 8 servers, near-identical twin `src/dopemux/mcp/default_catalog.yaml`)
   — the canonical catalog consumed by `dopemux mcp init/add/sync-globals/doctor`. It omits
   running servers (leantime-bridge — P0 claim 13 "verified but alive"; dcp-readonly-facade —
   P0 claim 8; mcp-registry and scheduled-tasks — register PERIPH-MCP-REGISTRY,
   PERIPH-SCHEDULED-TASKS; context7 — PERIPH-CONTEXT7) and asserts transports that do not
   exist:
   - **pal `http://localhost:3003/mcp` is fiction** — P0 claim 11: `/health` 200 but `/mcp`,
     `/sse`, `/messages` all 404. pal-stdio (docker exec) is the only usable PAL surface
     (register PAL-MANAGED-LIFECYCLE, PAL-VARIANT-DEDUPE).
   - **gptr-mcp has an undescribed HTTP surface** — P0 claim 12: `:3009` serves an SSE-style
     `/messages` endpoint the catalog does not describe (register GPTR-TRANSPORT-TRUTH).
2. **`src/dopemux/mcp/registry.yaml`** (legacy, self-titled "canonical") — stale in every
   dimension: carries a `dopemux-zen` ghost server, describes ConPort as `http` on `:3004`
   while the live surface is SSE on `:3005` (P0 claim 1), and duplicates entries
   (`dopemux-claude-context` vs `dope-context`). Nothing that generates agent configs reads it.
3. **`services/registry.yaml`** — mixes compose/smoke-stack concerns with MCP naming; ADR-223
   already had to prune an orphaned exa row from it.

Per-agent MCP configuration divergence is total (Claude = full fleet; **Codex = 0**;
OpenCode = pal-only; Gemini = 0; Copilot = unproven proxy), and ~11 nonexistent ConPort tool
names are hardcoded across instruction surfaces (register CMD-NAME-DRIFT-REPAIR). The
machinery to fix this largely exists: `fleet_catalog.generate_fleet_output_files`
(`src/dopemux/mcp/fleet_catalog.py:288`), `dopemux mcp generate --apply`
(`src/dopemux/commands/mcp_commands.py:864`), a preview-only Codex renderer
(`fleet_catalog.py:167`), a parity validator (`validate_generated_mcp_json_parity`,
`fleet_catalog.py:597`), and server-granular tool-surface gates (`fleet_catalog.py:352/:363`).
A runtime-introspected tool-surface snapshot is now committed: `mcp_tool_surfaces.json`
(commit `447c9c20d`, produced by `dopemux mcp snapshot-tools`,
`src/dopemux/mcp/tool_snapshot.py`; schema `{generated_at, generator, schema_version, servers}`),
seeded from the P0 `tools/list` captures (`proof/mcpint-p0/tools_list/*.json`).

**Schema gap**: `schemas/mcp/fleet-catalog.schema.json` sets `additionalProperties: false`
on server entries but does **not** admit `port_policy` — yet `mcp_catalog.yaml:194` already
declares `port_policy: reserved_singleton` on task-orchestrator (the 7890 reserved-singleton
invariant, AGENTS.md §12.2). The canonical catalog cannot validate against its own schema.
The schema also pins `version: {const: 1}`.

Finally, two answered gates dispose of fleet composition and must be encoded where fleet
composition is decided — here. The per-tool execution spec for both is the binding
placement map `docs/03-reference/mcp/tool-placement-map.md` (commit `4bc3c2cfb`):

- **G3 (user decision 2026-07-16)**: two Serena-derived surfaces, no overlap. The deployed
  upstream serena wrapper (27 tools, P0 claim 4) keeps code-intel; its 11 write-capable tools
  including `execute_shell_command` (register SERENA-WRITE-LANE, `boundary_fit: violates`) are
  gated under **DMX-ARCH-SERENA-SURFACE-003 (SVCFIN owner — this ADR does not decide that
  gating)**. The 41 candidate-only ADHD/intel tools (register F001, SERENA-ADHD-INTEL,
  SERENA-ADHD-CAPS, SERENA-ANALYTICS) ship as their own MCP surface per the placement map.
- **G5 (user decision 2026-07-16)**: `services/complexity_coordinator` (register
  SVC-COMPLEXITY-COORDINATOR — built, in no compose or registry) becomes the single
  complexity authority; the four competing scorers (SERENA-COMPLEXITY-BANDING,
  DCTX-COMPLEXITY, TO-COMPLEXITY-SCORER, and `services/dopecon-bridge/complexity_scorer.py`
  per SVC-DOPECON-BRIDGE note) become inputs to it or are deleted. The placement map refines
  the mechanism: the coordinator is a single library module
  (`services/complexity_coordinator/unified_complexity.py`) with no FastAPI/MCP surface —
  authority is exercised as a **shared library**, not a new server.

## Decision

Extend `mcp_catalog.yaml` to **v2** and make the existing generate pipeline the **sole
producer** of every agent config and every instruction-surface header block. No new manifest
is introduced.

### 1. Catalog v2 shape

Per-server additions:

- **`tools:`** — a pointer into the committed `mcp_tool_surfaces.json` (server key +
  snapshot `schema_version`), not an inline tool list. The snapshot is the only place tool
  names live; the register's `tools:` lists and all instruction surfaces are validated ⊆
  snapshot by the tool-granular drift gate (MCPINT-FND-DRIFTGATE-003).
- **`agents:`** — the per-agent exposure matrix, e.g.
  `{claude: full, codex: full*, opencode: read-plane, gemini: read-plane, copilot: read-plane, chatgpt: facade}`.
  The `codex: full` entry carries the **G1 parity decision with mandatory sequencing**
  defined in ADR-MCPINT-002: the write-capable Codex config may not ship until
  DMX-MEMSPINE-IDENTITY-005 and orchestrator `actor_authentication.enabled` have landed.
  The matrix value is data; ADR-MCPINT-002 is the policy that constrains when the generator
  may honor it.
- **`workflows:`** — refs into `docs/03-reference/mcp/workflows.yaml` (named tool sequences;
  Phase 5, MCPINT-DOC-003). Refs only; workflow content is not duplicated in the catalog.

Catalog `version: 2`; `schemas/mcp/fleet-catalog.schema.json` is updated in the same change to:

- admit `port_policy` (enum including `reserved_singleton`) — repairing the existing
  validation gap;
- admit the new `tools:` / `agents:` / `workflows:` keys with closed schemas;
- accept `version: 2`.

### 2. Generate pipeline = sole producer

`generate_fleet_output_files` + `dopemux mcp generate --apply` emit **and apply**: the
worktree `.mcp.json`, the global singleton fragment (`sync-globals`,
`mcp_commands.py:1853`), `.codex/config.toml` `mcp_servers` (renderer `fleet_catalog.py:167`,
promoted from dry-run-only to applied), `opencode.jsonc` (new renderer), the Copilot proxy
yaml (new renderer), and the generated "live surfaces" header blocks in instruction surfaces
(`.claude/mcp-system.md` et al.). One parity gate per target, cloning
`validate_generated_mcp_json_parity` (`fleet_catalog.py:597`), runs in CI
(MCPINT-FND-CODEGEN-005).

### 3. Registry consolidation

- **Kill `src/dopemux/mcp/registry.yaml`** (and its loader path in
  `src/dopemux/mcp/registry.py` insofar as it reads this file as truth). Its claims are
  runtime-refuted (ConPort transport/port; `dopemux-zen` ghost) and nothing
  config-generating consumes it.
- **Demote `services/registry.yaml`** to compose-only concerns (smoke-stack membership,
  compose service naming). It must contain no MCP transport, port-truth, or tool claims;
  any MCP semantics migrate to the catalog.

### 4. Transport truth repairs (MCPINT-FND-CATALOG-001)

- `pal:` catalog entry loses its fictional `url: http://localhost:3003/mcp`; **pal-stdio is
  the only PAL surface** (docker-exec). The pal-http wrapper remains a health/lifecycle
  shim, not an MCP transport, until PAL-HTTP-RETROFIT is decided separately.
- `gpt-researcher:` entry describes the real `:3009` `/messages` SSE-style surface or
  explicitly marks it non-contractual (GPTR-TRANSPORT-TRUTH); it must stop describing a
  stdio-only server.
- Add missing running servers: leantime-bridge (SVC-LEANTIME-BRIDGE), dcp-readonly-facade
  (DCP-FACADE, per ADR-MCPINT-002), mcp-registry, scheduled-tasks, context7 (PERIPH-*) —
  with personality metadata. Record exa (EXA-RETIRE, ADR-223) and desktop-commander
  (DC-RUNTIME) runtime posture: P0 claims 14/15 show quarantine/retirement affects generated
  configs but not running containers; runtime disposition is executed by DMX-HYG-DEADSVC-001
  / DMX-HYG-LOOPBACK-002 (SVCFIN owners), the catalog records the intended state.

### 5. Fleet composition from answered gates

Execution spec for both items: `docs/03-reference/mcp/tool-placement-map.md` (binding;
its per-tool dispositions are incorporated by reference, not restated).

- **G3**: the ADHD/intel toolset ships as a new MCP surface **on adhd-engine**, catalog
  name **`dope-adhd`** — chosen over a standalone `dope-adhd-intel` server. Rationale:
  adhd-engine already owns the events, notification dispatcher, personal thresholds, and
  ADHD state these tools need; the intended-but-empty `services/adhd_engine/mcp_stdio.py`
  stub shows the original architecture pointed here; a separate server would recreate the
  shadow-twin syndrome the 2026-07-03 fleet audit condemned and add a second ignition
  problem (adhd-engine itself was runtime-refuted absent — P0 claim 16, ADHD-ENGINE-CORE —
  and must be ignited by DMX-ADHDLOOP-IGNITION-VERIFY-002 regardless). Standalone remains
  the recorded fallback only if engine image/startup cost becomes real (IMP-ADHDINTEL-007).
  Scope per the placement map: **31 tools ship, 9 drop** — the 9 drops are the 8 duplicates
  covered by upstream serena or native editing (`find_references`, `goto_definition`,
  `search_pattern`, `get_file_symbols`, `apply_patch`, `batch_apply_patch`, `create_file`,
  `write_file`) plus `find_similar_code`, delegated to `dope-context.search_code`
  (retrieval plane owns semantic similarity). Two of the 31 (`analyze_complexity`,
  `get_unified_complexity`) are thin delegating wrappers over the G5 complexity library;
  the 6 structural-graph tools ship on dope-adhd in phase 1 with a recorded phase-2
  consolidation target of dope-context. Upstream serena keeps code-intel unchallenged;
  **no tool name may exist on both surfaces** (enforced by the drift gate against the
  snapshot). The `services/serena` candidate is archived after extraction; archive scope
  remains owned by DMX-ARCH-SERENA-SURFACE-003.
- **G5**: `complexity_coordinator` becomes the single complexity authority **as a shared
  library, not a server** — `services/complexity_coordinator/unified_complexity.py`
  relocates to `src/dopemux/complexity/` (or a shared package) and gets **no catalog entry,
  no compose service, no MCP surface**. Consumers delegate: dope-adhd
  `analyze_complexity`/`get_unified_complexity`, dope-context `get_chunk_complexity`
  (fixing its lying docstring by delegation), task-orchestrator scoring, and
  `/dx:prd-parse` (DX-PRD-PARSE) all call the library's `unified_score`.
  SERENA-COMPLEXITY-BANDING and TO-COMPLEXITY-SCORER become inputs to it or are deleted;
  `services/dopecon-bridge/complexity_scorer.py` is deleted or reduced to an input adapter.
  No independent scoring logic may remain in any consumer.

### Invariants

- A server not in `mcp_catalog.yaml` cannot appear in any generated agent config; a
  cataloged `lifecycle: active` server must appear in every config its `agents:` row grants.
- Generated files are never hand-edited; per-target parity gates fail CI on drift.
- Every catalog transport/port claim must be runtime-verifiable; `tools:` pointers must
  resolve into the committed snapshot, and the snapshot is refreshed only by
  `dopemux mcp snapshot-tools`.
- One tool function, one surface: no two catalog servers may expose tools with the same
  function (G3 no-overlap rule generalized). Literal name collisions are already prevented
  agent-side by MCP namespacing (`mcp__<server>__<tool>`); this invariant is about
  placement discipline — duplicates delegate or die, per the placement map rule 4.

### Non-goals

- Deciding the Serena write-lane gating (owner: DMX-ARCH-SERENA-SURFACE-003).
- Deciding the ConPort surface consolidation (owner: DMX-ARCH-CONPORT-SURFACE-002).
- Runtime deletion/loopback repair of retired servers (owners: DMX-HYG-DEADSVC-001,
  DMX-HYG-LOOPBACK-002).
- Changing `port_allocator.py` behavior (the N1 init catch-22 has its own fix track).

## Alternatives Considered

- **A new, separate fleet manifest.** Rejected: the program plan's controlling constraint is
  "no new manifest" — a fourth registry is the disease, not the cure; `mcp_catalog.yaml`
  already has generators, gates, and a personality contract attached.
- **Keep three registries, add sync gates between them.** Rejected: drift between twins is
  the empirically dominant failure (default_catalog twin, services/registry orphans,
  legacy registry ghosts); N-way sync gates cost more than one writer.
- **Promote `services/registry.yaml` to the source of truth.** Rejected: it is a
  compose/smoke concern with no scope/transport/identity semantics and no generator
  attached; the catalog already carries the richer contract.
- **Inline tool lists in the catalog instead of a snapshot pointer.** Rejected: tool
  surfaces are runtime facts; inlining them re-creates hand-maintained prose that the P0
  audit proved rots (~11 phantom ConPort names). A committed, regenerable snapshot keeps the
  data curated-in-one-place and gate-checkable docker-down.
- **G3 alternative — standalone `dope-adhd-intel` server.** Rejected (coordinator lean,
  encoded here and in the placement map): a new container for tools whose state and event
  flows already live in adhd-engine splits one authority into two and adds a second
  ignition problem. Kept as the recorded fallback if engine image bloat becomes real.
- **G5 alternatives — TO scorer only / shelve all scorers.** Rejected by user decision:
  wastes the built unifier (coordinator exists precisely to end the 4-scorer split); shelving
  removes complexity claims doctrine still depends on (ADHD banding, /dx:prd-parse).
- **G5 mechanism alternative — wire complexity_coordinator as its own service/MCP server.**
  Rejected (placement map): it is a single library module with no FastAPI/MCP surface;
  standing up a server for one computation violates the placement rule (derived signals =
  shared library surfaced through each consumer plane's existing tools) and adds another
  container to keep alive for no isolation benefit.

## Consequences

- **Amendment (2026-07-17, at acceptance)**: per the confirmed SVCFEAT reconciliation
  (`claudedocs/mcpint-svcfeat-reconciliation-2026-07-17.md`; placement map §6), the G3
  31-tool surface ships on the sibling **`dopecode`** service (containerized
  `services/serena` engine) instead of `dope-adhd` on adhd-engine —
  MCPINT-IMP-ADHDINTEL-007 is superseded by DMX-DOPECODE-DEPLOY-001; the dope-adhd
  surface is cancelled.
- **Packets**: MCPINT-FND-CATALOG-001 (catalog v2 + transport truth + schema),
  MCPINT-FND-SNAPSHOT-002 (landed — snapshot + command), MCPINT-FND-DRIFTGATE-003
  (tool-granular gate; dep DMX-HYG-CONPORTREFS-003), MCPINT-FND-INSTRREPAIR-004 (one-time
  drift repair), MCPINT-FND-CODEGEN-005 (renderers + `--apply` + parity gates),
  MCPINT-FND-REGISTER-GATE-006 (register contract test), MCPINT-FND-HYG-007. G3/G5
  execution packets: **MCPINT-IMP-ADHDINTEL-007** (dope-adhd surface on adhd-engine) and
  **MCPINT-IMP-COMPLEX-008** (complexity library relocation + consumer delegation) — named
  in the placement map, to be loaded into the DMX-MCPINT ledger.
- Codex/OpenCode/Gemini/Copilot configs become generable and gate-checked
  (consumed by ADR-MCPINT-002 / MCPINT-IMP-CODEX-002).
- The catalog stops lying about PAL and gptr transports; `dopemux mcp doctor` probes match
  declared reality.
- Killing the legacy registry breaks anything that silently read it — the removal packet
  must grep for readers (`src/dopemux/mcp/registry.py` load path) and migrate or delete them.
- Schema change is contract-sensitive: catalog consumers (`fleet_catalog.py` loaders, arch
  tests `tests/arch/test_mcp_fleet_catalog_contract.py`) must be updated in the same change;
  `version: 2` is a hard cutover, no dual-read.
- The G3 no-overlap rule means 9 candidate tools are dropped rather than shipped (8
  redundant duplicates deleted; `find_similar_code` delegated to
  `dope-context.search_code`); anyone wanting Serena-style writes goes through the gated
  upstream lane (DMX-ARCH-SERENA-SURFACE-003) — never through the ADHD surface, which
  ships zero write-shaped repo tools by construction.
- Post-effort target surfaces (placement map §4): conport 17 (3 marked `admin` in catalog
  personality — `fork_instance`, `promote`, `promote_all` excluded from workflow docs and
  non-Claude exposure rows), dope-memory 10, task-orchestrator 14, serena 27 (read-only
  default profile pending DMX-ARCH-SERENA-SURFACE-003), dope-context 18, **dope-adhd 31
  (new)**, pal-stdio 18, gpt-researcher 5, dcp-readonly-facade 12 (3 deferred).
  webhook_receiver and leantime-bridge are cataloged as infra/PM-sync entries with no agent
  matrix row (`agents: none`); scheduled-tasks/mcp-registry/context7 enter as
  `managed: false` external entries.

## Migration Strategy

1. FND-CATALOG-001: schema v2 + catalog v2 + transport truth + missing servers (one PR;
   catalog and schema move together).
2. FND-CODEGEN-005: renderers + `--apply` + per-target parity gates; first `--apply` run
   commits the generated configs as the new baseline.
3. Registry kill/demote in the same PR as (2)'s baseline (so no window where two truths
   coexist ungated).
4. FND-DRIFTGATE-003 / FND-INSTRREPAIR-004: repair instruction surfaces, then turn the
   tool-granular gate on in CI.
5. G3/G5 packets loaded after this ADR is accepted (sequenced behind adhd-engine ignition,
   DMX-ADHDLOOP-IGNITION-VERIFY-002).

Rollback: revert to catalog v1 + schema v1 in one commit; generated configs regenerate from
v1; the legacy registry stays deleted (nothing reads it).

## Verification

- `pytest tests/arch` green including: fleet-catalog contract test updated for v2;
  per-target parity gates (regenerate == committed); register contract test
  (`tools:` ⊆ snapshot); unknown-surfaces = 0.
- `dopemux mcp generate --apply` idempotent (second run = no diff).
- Catalog validates against the v2 schema (currently impossible at v1 due to the
  `port_policy` gap — this is the regression canary).
- P6 Codex dry-run: Codex lists tools from a generated config and a denied route is
  provably rejected.

## Validation

- **PAL consensus (2026-07-17, pal-stdio `consensus`, continuation
  `21298af6-c9da-479e-84ef-5aaf739ac601`)**: **PARTIAL** — two models consulted,
  one usable verdict.
  - `openai/gpt-5` (stance: for) — verdict: **architecturally sound and internally
    consistent; proceed** (confidence 7/10). Strongest objection: a flat global
    tool-name-uniqueness rule is brittle — prefer namespacing + collision policy
    (addressed: the invariant wording above now states the rule is about function
    placement, not literal names, which MCP client namespacing already handles).
    Actionable gaps fed to packets: snapshot provenance + CI re-introspection diff
    (FND-SNAPSHOT-002 already embeds `generated_at`/`generator`/`schema_version`;
    freshness gate = FND-DRIFTGATE-003/REGISTER-GATE-006), deterministic generation
    ordering (FND-CODEGEN-005), per-target capability waivers (FND-CODEGEN-005),
    complexity-library versioning + consumer contract tests (IMP-COMPLEX-008),
    schema-level ban on literal secrets in the catalog (FND-CATALOG-001).
  - `google/gemini-2.5-pro` (stance: against) — returned `status: success` with an
    **empty verdict (null content)**; no counter-analysis obtained. Recorded as a
    partial failure, not counted as agreement.
- **PAL consensus completion (2026-07-17, pal-stdio `consensus`, continuation
  `6fe67aa0-6c68-4d13-8947-367bde6af7c8`)**: the missing AGAINST stance re-run via
  OpenRouter — **debt closed, no blocking objection**.
  - `google/gemini-2.5-pro` via OpenRouter (stance: against) — verdict: **holds as
    written; endorse** (confidence 9/10). Strongest objection: the manual
    `dopemux mcp snapshot-tools` step is a new human-error drift vector — the committed
    snapshot can lag runtime; demands a CI re-introspection gate (regenerate ==
    committed or fail). Disposition: hardening feedback, already the freshness-gate
    scope of MCPINT-FND-DRIFTGATE-003 / FND-REGISTER-GATE-006.
  - `anthropic/claude-opus-4.1` via OpenRouter (stance: neutral) — verdict:
    **architecturally sound and necessary** (confidence 7/10). Strongest objection:
    the runtime-verification burden — "every transport claim runtime-verifiable"
    needs real probe infrastructure across heterogeneous transports
    (stdio/HTTP/docker-exec); more transport fictions likely exist beyond pal.
    Disposition: hardening feedback on `dopemux mcp doctor`/snapshot probing
    (FND-SNAPSHOT-002 landed the prober; serena/pal-stdio/gptr captures still owed).
- ConPort `log_decision` for this ADR: owed at acceptance (Phase 2 exit), not at draft.

## Cross-references

- ADR-MCPINT-002 (exposure matrix policy + read plane), ADR-MCPINT-003 (implicit channels),
  ADR-MCPINT-004 (event ingress), ADR-MCPINT-005 (shelved features).
- ADR-223 (exa retirement — the catalog-prune pattern this ADR generalizes).
- DMX-ARCH-SERENA-SURFACE-003, DMX-ARCH-CONPORT-SURFACE-002 (SVCFIN owners; inputs, not
  re-decided here).
- Tool placement map: `docs/03-reference/mcp/tool-placement-map.md` (binding per-tool
  execution spec for §5).
- Runtime evidence: `claudedocs/mcp-fleet-runtime-verification-2026-07-16.md` claims 1, 4,
  8, 11, 12, 13, 14, 15, 16; findings N1, N5.

---

*PAL consensus outcome recorded in the Validation section above (2026-07-17).*

## Proposed ConPort CRS v2 catalog amendment

The catalog contains one logical agent-facing ConPort identity: `conport-crs-v2`. It references the accepted normalized tool-contract digest and immutable runtime pins. Agent configuration may expose a local stdio launcher, but the launcher routes to the same authenticated policy-enforced core. The separate operator admin contract is not an agent catalog entry. Tool counts are generated from the accepted snapshot and are never hand-coded as an architectural invariant.
