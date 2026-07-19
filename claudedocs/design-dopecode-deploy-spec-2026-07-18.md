# EXECUTION SPEC — DMX-DOPECODE-DEPLOY-001 (rescoped): deploy `dopecode` as sibling MCP service

**Program**: DMX-SVCFEAT item `c14414ff` (tree `f64aa1a9`), rescoped per the **CONFIRMED** reconciliation
(`claudedocs/mcpint-svcfeat-reconciliation-2026-07-17.md`, governing) · **Date**: 2026-07-18
**Binding inputs**: tool-placement-map §2 + §6 (`docs/03-reference/mcp/tool-placement-map.md:25-41,:83-94`),
ADR-MCPINT-001 (accepted; Consequences amendment `docs/90-adr/adr-mcpint-001-catalog-v2-single-source.md:247-252`),
AGENTS.md §12 transport/port invariants.
**One-line scope**: containerize the 46-tool `services/serena` engine as a NEW compose service +
catalog entry named `dopecode`, alongside — never replacing — upstream serena; 31 tools contractual,
9 disabled; complexity tools carry an honest interim scorer until IMP-COMPLEX-008.

---

## 0. Why the deploy path is currently broken (do not re-derive)

The compose service `serena` (`compose.yml:543-567`) builds
`docker/mcp-servers/serena/Dockerfile`, which installs **upstream serena from git**
(`git+https://github.com/oraios/serena.git@f561204…`) and copies **only**
`wrapper.py` / `info_server.py` / `start_with_info.sh`. The boot chain is
`start_with_info.sh` → `python wrapper.py` → `mcp-proxy … -- serena start-mcp-server`
(`docker/mcp-servers/serena/wrapper.py:28-35`). **Nothing anywhere boots
`services/serena/mcp_server.py`** — the 248 KB, 46-tool candidate engine
(`Server("serena-v2")`, `services/serena/mcp_server.py:396`; stdio transport `:32-33`,
run loop at file tail) has never been containerized. That is the gap this packet closes.

Known wrapper ambiguity to not copy blindly: `wrapper.py` docstring claims "Streamable
HTTP" (`:3-4`) but invokes `mcp-proxy --transport sse` (`:31`); catalog + AGENTS.md
§12.1 declare serena `http` `POST /mcp`. For dopecode, the transport claim in the
catalog MUST be what a runtime probe shows (ADR-001 invariant: "Every catalog
transport/port claim must be runtime-verifiable", `adr-mcpint-001:200-203`).

## (a) Name, port, transport

- **Service/catalog name**: `dopecode` (compose service `dopecode`, container
  `dopemux-mcp-dopecode`).
- **Port**: **3007** (MCP), **4007** (health/info) — mirrors the serena 3006/4006 pair
  (`compose.yml:552-553`). Loopback-bound:
  `127.0.0.1:${DOPECODE_PORT:-3007}:3007` and `127.0.0.1:${DOPECODE_HTTP_PORT:-4007}:4007`.
  Free-port check against compose (full host-port enumeration, this worktree): 3003,
  3004/3005/4004, 3006/4006, 3009, 3010, 3012, 3015, 3016, 3020, 3025, 4000, 5432,
  6333/6334, 6379/6380, 7890/8000, 8080/8081, 8790 — **3007/4007 unclaimed**; the
  catalog claims no 3007 either. **3030 is deliberately avoided** — informally eyed for
  the dcp-readonly-facade listener that MCPINT-IMP-FACADE-001 will bind
  (`mcp_catalog.yaml:239-243` — facade url intentionally absent until then).
  Singleton scope ⇒ no per-worktree hash offset, and the port gets pre-seeded into the
  `_allocate_ports` collision map automatically once cataloged (AGENTS.md §12.2).
- **Transport**: target **`http` (Streamable HTTP, `POST /mcp`)** to match the sibling
  row in AGENTS.md §12.1 (pal/serena/dope-context = http). The engine is stdio-native,
  so the container fronts it with `mcp-proxy` (already a proven pattern in the serena
  image, Dockerfile: `uv pip install mcp-proxy`). **Gate**: before the catalog entry
  gains `url:`, run the §12.4 probe (`curl -X POST http://localhost:3007/mcp` with an
  `initialize` body). If the installed mcp-proxy only emits SSE, the catalog says
  `sse` + `GET /sse` — record runtime truth, not aspiration.

## (b) Containerization plan — what `services/serena` actually needs to boot

**New files**: `docker/mcp-servers/dopecode/{Dockerfile,wrapper.py,info_server.py,start.sh}`
+ compose service block. Upstream serena's image/files are NOT touched.

1. **Entry point**: `mcp-proxy --transport <verified> --port 3007 --host 0.0.0.0 --
   python /app/services/serena/mcp_server.py` (replacing the upstream wrapper's
   `serena start-mcp-server` child). `mcp_server.py` runs `stdio_server()` and needs
   cwd/`sys.path` at `/app/services/serena` — it inserts its own dir for flat imports
   (`mcp_server.py:43-49`) and falls back between `services.shared.mcp.response_budget`
   and `shared.mcp.response_budget` (`:51-60`), so copy **both** `services/serena/` and
   `services/shared/` (contains `response_budget.py`, `pal_client.py` — verified present).
2. **Deps**: base `python:3.11-slim` + `uv pip install --system .[services]` (the
   `[services]` extra, `pyproject.toml:93-131`, carries everything the engine imports:
   `mcp>=1.23.3`, `asyncpg`, `tree-sitter` + 5 grammars, `aioredis`, `sqlalchemy`,
   `structlog`). `COPY pyproject.toml src/ tools/ services/serena/ services/shared/`.
   `git` + `curl` apt packages (git detector shells out; healthcheck curls). Do **not**
   install upstream serena from git — that's the upstream image's business.
3. **Storage paths — runtime truth, note the correction**: the tasking said "F001
   SQLite"; the code says otherwise. **There is no SQLite anywhere in
   `services/serena/`** (repo-wide grep). Actual persistence:
   - **F001 untracked-work**: ConPort `custom_data` via `UntrackedWorkStorage`
     (`services/serena/untracked_work_storage.py:28-97` — `log_custom_data`), reached
     through `ConPortDBClient` connecting **direct to Postgres on port 5455**
     (`mcp_server.py:575-584`). In-container this must become
     `host=<compose postgres service>`, `port=5432` (5455 is the host-side mapping) —
     parameterize via env (`DOPECODE_CONPORT_DB_HOST/PORT`), never hardcode.
   - **Intelligence layer**: asyncpg pool to `postgresql://serena:…@localhost:5432/serena_intelligence`
     (`services/serena/intelligence/database.py:46-50`) — lazy-loaded; failures are
     recorded in `initialization_errors`, not fatal (`mcp_server.py:588-595` pattern).
     Provision the DB or accept degraded-lazy start; either way the smoke test (§f)
     pins which one shipped.
   - **Structural graph**: asyncpg `serena_code_graph` (`services/serena/code_graph_storage.py:114`).
   - **Navigation cache**: Redis `redis://localhost:6379` default (`mcp_server.py:744-748`)
     → point at the compose redis service via env.
   - **Workspace**: ro mount `${DOPEMUX_WORKSPACE_ROOT:-.}:/workspace:ro` +
     `DOPEMUX_WORKSPACE_ID` env (read at `mcp_server.py:496`), same as serena
     (`compose.yml:558-560`).
4. **LSP runtime needs — none for the contractual 31**: the "Minimal LSP client" in the
   engine backs `goto_definition` (`mcp_server.py:124`), which is on the **disabled**
   list. No language servers ship in the image. If DopeCode's LSP-007 packet later
   promotes LSP tools, that packet owns the runtime.
5. **Healthcheck**: `info_server.py`-style sidecar on :4007 (`curl -f
   http://localhost:4007/health`), matching serena's compose healthcheck shape
   (`compose.yml:562-567`) — required by fleet contract tests that assert compose
   healthchecks exist.

## (c) Contractual-vs-disabled split — mechanism

31 contractual / 9 disabled, per placement map §2 (§6 substitutes home=`dopecode`).
Disabled: `find_references`, `goto_definition`, `search_pattern`, `get_file_symbols`,
`apply_patch`, `batch_apply_patch`, `create_file`, `write_file` (8 upstream/native
dupes) + `find_similar_code` (delegated to `dope-context.search_code`).

**Recommended mechanism: env-var tool-filter list** —
`DOPECODE_DISABLED_TOOLS="find_references,goto_definition,search_pattern,get_file_symbols,apply_patch,batch_apply_patch,create_file,write_file,find_similar_code"`,
set in compose (default baked into the image env), enforced in `mcp_server.py` at
**both** `list_tools` (filter out) and `call_tool` (explicit error naming the
replacement tool). This makes the committed `mcp_tool_surfaces.json` snapshot capture
exactly 31 — the disabled 9 become non-contractual *by construction*, and the
no-overlap drift gate needs no special-casing.

- **Why not code removal**: the reconciliation explicitly reserves later promotion of
  the write layer via DopeCode's own packets (ROLLBACK-004, RENAME-006, LSP-007 —
  reconciliation §2.3); deletion inside a 248 KB file forecloses that and bloats the diff.
- **Why not a single boolean env flag**: no granularity; the drop list is a named
  9-tool contract, and the filter list doubles as its executable documentation.
- **Precedent**: the repo already drives PAL this way
  (`DISABLED_TOOLS: refactor,testgen,…`, `src/dopemux/config/manager.py:796-800`).
- **Guard**: an arch/unit test pins the default filter set == the placement-map drop
  list, so nobody silently re-enables `write_file` via compose edit without tripping CI.

## (d) Complexity delegation stub (G5 interim)

Target state (ADR-001 §5 G5, `adr-mcpint-001:185-194`): `analyze_complexity` and
`get_unified_complexity` become thin wrappers over `src/dopemux/complexity/`
(relocated `unified_complexity.py`). That library does not exist until
**MCPINT-IMP-COMPLEX-008** lands. Interim behavior — honest, non-breaking:

1. **Keep serving** the engine's existing scorer (do not stub-break shipped tools).
2. **Single seam**: route both tools through one module-level `_score(...)` function so
   the IMP-COMPLEX-008 swap is a one-line import change; **no new scoring logic** may be
   added behind the seam (G5: "No independent scoring logic may remain in any consumer").
3. **Provenance in output**: responses carry `"scorer": "dopecode-interim"` (flips to
   `"unified-complexity/<version>"` after the swap), so downstream consumers can detect
   pre-unification scores.
4. **No lying docstrings**: tool descriptions say "interim in-engine scorer; delegates
   to the unified complexity library when IMP-COMPLEX-008 lands" — the exact rot class
   ADR-001 calls out for dope-context's `get_chunk_complexity` ("fixing its lying
   docstring by delegation", `adr-mcpint-001:190-191`) must not be re-created here.
5. IMP-COMPLEX-008's consumer-contract tests (ADR-001 Validation, `:325-326`) pick up
   `dopecode` as a consumer; this spec only reserves the seam.

## (e) Catalog entry draft (paste-ready) + schema note

**Schema note first**: the plane/authority enums (`schemas/mcp/fleet-catalog.schema.json:58-71,:72-89`)
have no ADHD value, and upstream serena already holds `plane: code-intelligence` /
`authority_role: code-intelligence` (`mcp_catalog.yaml:80-81`). Two entries with the
same authority role would violate the one-authority-per-plane doctrine (placement-map
§1). **Add `"adhd"` to the `plane` enum and `"adhd-intelligence"` to `authority_role`**
in the same commit as the catalog entry (contract-sensitive: update
`tests/arch/test_mcp_fleet_catalog_contract.py` alongside, per ADR-001 consequence
`:267-269`). Fallback if the operator rejects the enum addition: `plane:
code-intelligence` with the plane-purity trade-off note from reconciliation §2.4 —
but then the authority-collision must be waived explicitly in the entry description.

```yaml
  dopecode:
    # DopeCode — the 46-tool services/serena engine deployed as its OWN sibling
    # service (SVCFEAT DOPECODE-DEPLOY-001 rescoped per the CONFIRMED reconciliation,
    # claudedocs/mcpint-svcfeat-reconciliation-2026-07-17.md; ADR-MCPINT-001
    # Consequences amendment). Upstream serena (:3006) is untouched; no tool overlap
    # (drift-gate enforced). 31 contractual tools; the 8 upstream-duplicates +
    # find_similar_code are disabled via DOPECODE_DISABLED_TOOLS and are
    # non-contractual. analyze_complexity/get_unified_complexity delegate to
    # src/dopemux/complexity/ when MCPINT-IMP-COMPLEX-008 lands (interim scorer
    # marked in tool output provenance until then).
    scope: singleton
    transport: http            # runtime-verify before adding url (AGENTS.md §12.1/§12.4)
    plane: adhd                # requires schema enum addition (see spec §e)
    authority_role: adhd-intelligence
    lifecycle: planned-active  # deploy commit flips to active + adds url + snapshot
    management_model: compose-service
    identity_scope: per-call-workspace
    follow_on_decision: none
    # url: "http://localhost:3007/mcp"   # added by the deploy commit once the
    #                                    # listener is probed live (facade precedent,
    #                                    # mcp_catalog.yaml dcp-readonly-facade)
    docker_compose_service: dopecode
    requires_env: ["DOPEMUX_WORKSPACE_ID"]
    optional_env: ["DOPECODE_DISABLED_TOOLS", "DOPECODE_CONPORT_DB_HOST", "DOPECODE_CONPORT_DB_PORT"]
    agents:
      claude: full
      codex: full-sequenced
      opencode: read-plane
      gemini: read-plane
      copilot: read-plane
      chatgpt: facade
    tools:
      snapshot_key: dopecode
      schema_version: 1
    description: "DopeCode — services/serena engine as sibling service: F001 untracked-work lifecycle (10), ADHD intelligence (4), complexity-delegating (2), usage analytics (6), nav-guidance (3), structural graph (6). 31 contractual of 46 defined; write/dupe tools disabled (non-contractual)."
```

**Agents matrix rationale (per accepted ADR-002 pattern)**: identical row to serena/
dope-context (`mcp_catalog.yaml:88-94,:111-117`) — claude full; codex full-sequenced
(gated on IDENTITY-005 + actor-auth per ADR-002); read-plane for opencode/gemini/
copilot; chatgpt facade. DopeCode's contractual surface ships **zero write-shaped repo
tools by construction** (the 4 write tools are in the disabled set), which is what makes
the read-plane rows safe without a DopeCode-specific gating ADR.

**Follow-on catalog effects**: `defaults.per_worktree` unchanged (singleton). The
`tools:` pointer requires the snapshot to gain a `dopecode` key before the entry
validates the register contract; sequence in §f. FND-DRIFTGATE-003/DOC packets gain
`dopecode` as a subject (reconciliation §3 table).

## (f) Verification plan

Ordered; each step gates the next:
1. **Boot + transport truth**: `docker compose up -d dopecode`; §12.4 probe on :3007
   (`initialize` round-trip) + `curl -f localhost:4007/health`. Record which transport
   answered; the catalog `transport:`/`url:` must match it.
2. **Snapshot**: `dopemux mcp snapshot-tools` → `mcp_tool_surfaces.json` gains
   `dopecode` with `tool_count: 31` (filter active). Commit the snapshot in the same PR
   as the catalog entry (register contract: `tools:` pointer must resolve,
   `adr-mcpint-001:200-203`).
3. **No-overlap check**: assert
   `snapshot.servers.dopecode.tools ∩ snapshot.servers.serena.tools == ∅` against
   upstream serena's 27 (`mcp_tool_surfaces.json` `serena` key). Add as an arch test —
   this is the G3 no-overlap invariant made executable for this pair.
4. **Disabled-list guard**: unit test — default `DOPECODE_DISABLED_TOOLS` set == the
   9-name drop list; `call_tool` on a disabled name returns the explicit redirect error.
5. **F001 smoke**: against a scratch workspace, `detect_untracked_work` →
   `track_untracked_work` → verify the ConPort `custom_data` record landed (via conport
   `get_custom_data`); proves the Postgres path (b.3) works in-network, not just on host.
6. **Complexity interim**: call `get_unified_complexity`; assert
   `scorer: "dopecode-interim"` provenance present and description carries the interim
   marker (guards against silent claim-of-unification).
7. **Arch gates + parity**: `pytest tests/arch` (fleet-catalog contract incl. the
   schema enum addition; register contract; snapshot resolution); then
   `dopemux mcp generate --apply` (agents row grants claude full ⇒ generated configs
   change) and re-run — second run must be a no-diff (idempotency,
   `adr-mcpint-001:305`).
8. **Doctor**: `dopemux mcp doctor` reports dopecode reachable on the declared
   transport.

## (g) Non-goals (explicit)

- **Upstream serena untouched**: its image, wrapper, compose block (:3006/:4006),
  catalog entry, and 27-tool surface are not modified. The original SVCFEAT phrasing
  "repoint compose off upstream wrapper" is DEAD — superseded by the confirmed
  reconciliation (§2.1).
- **Write-lane gating stays with DMX-ARCH-SERENA-SURFACE-003** (upstream's read-only
  default profile / gated write profile — reconciliation §2.5, ADR-001 non-goal `:211`).
  Nothing here decides it; DopeCode ships no write tools to gate.
- **No promotion of DopeCode's write/LSP layer** — future surface-ADR amendment via
  ROLLBACK-004 / RENAME-006 / LSP-007, not a default of this deploy.
- **No complexity library work** (IMP-COMPLEX-008 owns relocation + consumer swaps);
  this packet only builds the delegation seam.
- **No adhd-engine dependency**: the ignition cross-dep was dropped at confirmation
  (reconciliation §3); adhd-engine consumes DopeCode signals via events, unchanged.
- **No `services/serena` source-tree rename/relocation** (RENAME-006 owns naming); the
  container copies the tree as-is.
- **No changes to per-worktree defaults or port_allocator behavior** (ADR-001 non-goal
  `:215`).

---

**Confidence**: high on the broken-deploy diagnosis, port survey, storage-backend truth
(all code-cited); medium on mcp-proxy's streamable-http capability in the pinned
version (that's why §a gates the transport claim on a live probe); the "F001 SQLite"
phrase in upstream tasking is refuted by code — recorded in §b.3.
