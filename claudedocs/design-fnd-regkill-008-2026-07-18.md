# DESIGN — MCPINT-FND-REGKILL-008: ConfigManager off the legacy registry, then kill it

**Program**: DMX-MCPINT · **Date**: 2026-07-18 · **Status**: Design (proposed) · **ADR authority**: ADR-MCPINT-001 §3 "Registry consolidation" (accepted 2026-07-17) + Migration step 3 (`docs/90-adr/adr-mcpint-001-catalog-v2-single-source.md:137-143, :289-291`)
**Prior deferrals honored**: (1) registry-only `local:` fallbacks + health metadata absent from the catalog; (2) the `dopemux-*` name web; (3) known-rot reproduction risk.

---

## 0. Ground truth (reader census, verified this worktree)

`src/dopemux/mcp/registry.yaml` self-documents its own reader census in the DEPRECATED
header (`registry.yaml:1-23`). Verified against code:

| Reader | Evidence | Nature |
|---|---|---|
| `ConfigManager` (sole **runtime** reader) | `src/dopemux/config/manager.py:22` (import), `:347` (`_get_default_mcp_servers` in `load_config`), `:371` (`_repair_legacy_mcp_servers`), `:533` (`_get_default_config`), `:654` (`_detect_docker_mode`), `:704` (`_generate_server_config`), `:769` | generates default `mcp_servers` entries + repairs legacy user configs |
| `src/dopemux/mcp/__init__.py:1-9` | re-exports `MCPRegistry`, `MCPServerDefinition`, `DockerConfig`, `LocalConfig`, `DEFAULT_COMPOSE_FILE` | API surface only; no other importer exists (`grep MCPRegistry src/` → only `config/manager.py` + `mcp/__init__.py`) |
| `fleet_catalog.validate_legacy_registry_contract` | `src/dopemux/mcp/fleet_catalog.py:1000-1028`, called at `tests/arch/test_mcp_fleet_catalog_contract.py:155` | arch test: registry docker/health claims ⊆ compose |
| Tests pinning registry shape | `tests/test_mcp_registry.py` (4 tests, pins the six `dopemux-*` keys at `:13-20`), `tests/test_mcp_config_generation.py` (pins bridge/exec rendering + template-name resolution) | direct |
| `dopemux-*` **name web** (does NOT read the file; keys on its names) | `claude_config.MCP_NAME_MAPPING` (`src/dopemux/claude_config.py:27-46`, resolution `:321`, `:456`), `roles/catalog.py:94-137` (role server lists) + `:296` (hard-requires `"dopemux-conport"`), `profile_manager.py:253-258`, project templates `config/manager.py:826-876` | indirect — breaks only if generated *names* change |

Distinct file: `services/registry.yaml` + `tests/arch/test_registry_compose_alignment.py`
are the **compose/smoke registry** (ADR-001 "demote" target) — *not* in this packet's
kill scope and unaffected by it.

**Runtime consumers of the generated `mcp_servers` dict** (what actually breaks if
defaults change): `claude/launcher.py:274,:460,:469` (launch loop over enabled servers),
`roles/catalog.py:290-315` (availability = key presence; enablement toggling),
`tmux/cli.py:1699`, `cli.py:1831`, profile filtering via `claude_config.py:315,:449`.

**Known rot, re-verified**:
- `dopemux-zen` ghost (`registry.yaml:120-128`) + a live env-override block for it
  (`config/manager.py:801-814`) — nothing can start `npx zen-mcp`; zen was renamed PAL.
- `dopemux-conport` claims `transport: http`, `port: 3004` (`registry.yaml:26-34`);
  runtime truth is **SSE on :3005** (P0 claim 1; catalog `mcp_catalog.yaml:322-343`).
  The generated bridge (`manager.py:716-728`) targets `http://localhost:3004` — the
  HTTP/health port — and the bridge itself is HTTP-only ("Bridge stdio JSON-RPC to MCP
  HTTP", `src/dopemux/mcp/http_stdio_bridge.py:110-111`), so this entry is broken by
  construction twice over.
- Duplicate pair `dopemux-claude-context` (:86-99) vs `dope-context` (:101-109), both
  pointing at compose service `dope-context`/:3010.
- `_repair_legacy_mcp_servers` repairs `mas-sequential-thinking` (`manager.py:410-416`)
  — a server the registry does not even define, so `_generate()` returns `None` and the
  repair silently no-ops. The repair path is already partially dead.
- `dopemux-serena` carries `port: 3006` but `health_url` on **:4006**
  (`registry.yaml:49-50`) — health metadata is consumed **only** by the arch test
  (`fleet_catalog.py:1019-1027`); ConfigManager never reads `health_url`.

That last point dissolves half of deferral blocker (1): the "health metadata the catalog
lacks" has exactly one consumer, and it is a test that dies with the registry.

---

## 1. Question (a) — catalog `local_fallback:`/health fields, or ConfigManager behavior change?

**Answer: no catalog schema change. ConfigManager's defaults change behavior, and the
changes are enumerated and accepted.**

What ConfigManager actually needs per server, and where the catalog already has it:

| Registry field used | Used at | Catalog v2 equivalent |
|---|---|---|
| `transport` | `manager.py:713,:730` | `transport` (http/sse/stdio/external) |
| `docker.port` (bridge base-url) | `manager.py:723` | parse from `url` / `url_template` + `default_port_base` |
| `docker.service` + `compose_file` (auto-mode `compose ps` probe) | `manager.py:663-689` | `docker_compose_service` (compose file is a constant, `manager.py:10`) |
| `local.command/args` (non-docker fallback) | `manager.py:750-758` | **absent — deliberately** |
| `docker.exec` (stdio-in-docker) | `manager.py:733-748` | `command` + `args` (e.g. pal-stdio `mcp_catalog.yaml:184-185`, gptr `:149-150`) |
| `default_enabled` / `required_for_auto` | `manager.py:95-96 (registry.py)`, `:655-658` | `defaults.per_worktree` + `lifecycle: active` + `agents` row |
| `docker.health_url` | **never** (arch test only) | not needed; `dopemux mcp doctor` probes from catalog |

The only genuine gap is the `local:` fallback (uvx `context-portal-mcp`, host `serena
start-mcp-server`, `npx @zilliz/claude-context-mcp`, uvx `pal-mcp-server` —
`registry.yaml:35-40,:51-54,:95-99,:115-119`). These are precisely the class of
hand-maintained, runtime-unverified claims catalog v2 was designed to exclude
(ADR-001 rejected alternative "inline tool lists…re-creates hand-maintained prose that
rots", `adr-mcpint-001:228-231`). None of the four has a runtime-verification artifact;
the conport one is actively dangerous (a local stdio context-portal instance writes to a
different store — the workspace-contamination bug class already on record for
dope-memory). **The fallback retires.** In auto mode with docker down,
`_get_default_mcp_servers` now returns only catalog `stdio` (docker-exec) entries and
logs one actionable warning pointing at `dopemux mcp init` / `docker compose up`.

**Behavior deltas (docker mode), all accepted:**
1. `dopemux-zen` disappears from defaults; its env block `manager.py:801-814` is deleted.
2. `dopemux-conport` is emitted **present but `enabled: false`** with a reason string:
   SSE transport, and `http_stdio_bridge` cannot speak SSE. Key presence keeps
   `roles/catalog.py:290,:296` (availability by key; conport hard-required) and profile
   validation working; enablement is truthfully off until an SSE-capable bridge exists
   (follow-up, out of scope — agents already reach conport via the canonical `.mcp.json`
   path). Same disabled-entry treatment for `dopemux-desktop-commander` and
   `dopemux-leantime-bridge` (both `sse` in the catalog, `mcp_catalog.yaml:126,:227`).
3. `dopemux-claude-context`/`dope-context` duplicate collapses to one entry generated
   from the catalog `dope-context` (:3010), still published under the legacy alias (see
   (b)); the env overrides at `manager.py:790-795` carry over unchanged.
4. `dopemux-pal` regenerates from catalog `pal-stdio` (`docker exec -i mcp-pal-stdio …`,
   `mcp_catalog.yaml:184-185`) instead of the unverified `uvx pal-mcp-server`; the
   `DISABLED_TOOLS` env block `manager.py:796-800` carries over.
5. `dopemux-serena` bridge to :3006 — unchanged output.

### Rejected alternatives for (a)
- **Grow the catalog with `local_fallback:` + `health:` fields (schema v2.x)** — re-imports
  the unverifiable hand-maintained runtime claims v2 exists to kill, and spends a
  contract-sensitive schema change (`tests/arch/test_mcp_fleet_catalog_contract.py`
  update, ADR-001 consequence `:267-269`) to preserve a fallback with zero verified users.
- **Behavior-preserving adapter (bit-identical defaults)** — must reproduce
  runtime-refuted claims (conport http:3004, zen ghost); see (c).
- **Keep registry.yaml as a "legacy defaults" data file read by a catalog-aware loader**
  — leaves two truths on disk, which is the disease ADR-001 §3 names.

---

## 2. Question (b) — the `dopemux-*` name mapping strategy

**Answer: compat shim table now; rename sweep is a separate follow-up packet, not part
of REGKILL-008.**

The `dopemux-*` names are not just internal: they are the keys under which servers live
in users' `~/.claude.json` (written by `claude_config.ClaudeConfigManager`,
`claude_config.py:130,:343-388`) and in saved user/project configs
(`manager.py:418-437`). A rename sweep is therefore a **user-state migration**, not a
grep-and-replace: it needs a `~/.claude.json` key-migration path, a saved-config repair,
and touches ~8 src modules (`claude_config.py`, `roles/catalog.py`, `profile_manager.py`,
`profile_models.py`, `profile_analyzer.py`, `config/manager.py` templates,
`global_config.py`, `project_init.py`) plus ~10 test files (`test_roles_catalog.py`,
`test_claude_config.py`, `test_profile_models.py`, `test_mcp_config_generation.py`, …).
Bundling that into the registry kill maximizes blast radius for zero registry-kill
benefit.

Mechanism in this packet:
- The new adapter owns one frozen table `LEGACY_ALIAS_BY_CATALOG = {"conport":
  "dopemux-conport", "serena": "dopemux-serena", "dope-context":
  "dopemux-claude-context", "pal-stdio": "dopemux-pal", "gpt-researcher":
  "dopemux-gpt-researcher", "desktop-commander": "dopemux-desktop-commander",
  "leantime-bridge": "dopemux-leantime-bridge"}` and emits defaults under the alias
  names. `MCP_NAME_MAPPING` (`claude_config.py:27-46`) stays as-is minus its two `zen`
  rows; a unit test asserts the two tables are consistent (every alias value resolvable
  through `MCP_NAME_MAPPING`, every mapping target produced by the adapter or explicitly
  retired) so the tables cannot drift apart silently.
- Downstream (`roles/catalog.py:94-137`, templates `manager.py:826-876`, profiles) is
  untouched and stays green.

### Rejected alternative
- **Rename sweep to catalog short names in this packet** — converts a 2-slice registry
  kill into a cross-module + user-state migration; the alias boundary is cheap, already
  half-exists (`MCP_NAME_MAPPING` maps short→prefixed today), and can be retired
  independently later.

---

## 3. Question (c) — preserve-then-fix vs fix-during-migration

**Answer: fix-during-migration.**

A behavior-preserving adapter would have to re-emit: the conport bridge to
`http://localhost:3004` (an HTTP/health port, for an SSE server, through an HTTP-only
bridge — three stacked falsehoods), the `dopemux-zen` entry + env block, and the
`claude-context`/`dope-context` twin. ADR-001 kills the registry *because* "its claims
are runtime-refuted … and nothing config-generating consumes it"
(`adr-mcpint-001:137-140`); porting the refuted claims into fresh code inverts the
ADR's rationale. Worse, preserve-then-fix means writing **new tests that assert refuted
claims** and rewriting them one commit later.

**Test impact per choice** (same file set either way; the difference is churn count):

| Test file | preserve-then-fix | fix-during |
|---|---|---|
| `tests/test_mcp_config_generation.py` (bridge/template/no-host-path tests) | rewritten twice (adapter port, then truth fix) | rewritten once |
| `tests/test_config_manager.py`, `tests/unit/test_mcp_config_repair.py`, `tests/unit/test_mcp_commands_repair.py` | twice | once |
| `tests/test_roles_catalog.py` | untouched, then touched (conport disabled-entry) | once |
| `tests/test_claude_config.py`, `tests/test_profile_models.py` | untouched | expected green (names preserved); zen-row removal only |
| `tests/test_mcp_registry.py` | deleted at kill | deleted at kill (slice 2) |
| `tests/arch/test_mcp_fleet_catalog_contract.py:155` | legacy-contract call kept passing against reproduced claims, then deleted | deleted at kill (slice 2) |

---

## 4. Question (d) — execution slicing (RECOMMENDED: 3 slices, 2 in this packet)

**Slice 1 — Adapter + ConfigManager switchover (registry becomes read-by-nothing-at-runtime).**
- Add `src/dopemux/mcp/legacy_config_adapter.py`: renders the legacy
  `MCPServerConfig`-shaped dicts from `fleet_catalog.load_root_catalog()`; three render
  classes — streamable-http entry → `http_stdio_bridge` command; stdio entry →
  `command/args` passthrough; sse entry → present-but-disabled with reason. Owns
  `LEGACY_ALIAS_BY_CATALOG`.
- `config/manager.py`: `_get_default_mcp_servers`, `_generate_server_config`,
  `_detect_docker_mode` (compose-service set from catalog `lifecycle: active` +
  `docker_compose_service`), `_repair_legacy_mcp_servers` all route through the adapter;
  `MCPRegistry` import (`manager.py:22`) removed; zen env block (`:801-814`) and the
  dead `mas-sequential-thinking` repair (`:410-416`) deleted.
- Tests: rewrite the files in §3's table (once).
- **Verification**: `pytest tests/test_mcp_config_generation.py tests/test_config_manager.py
  tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_commands_repair.py
  tests/test_roles_catalog.py tests/test_claude_config.py tests/test_profile_models.py`;
  before/after snapshot diff of `ConfigManager()._get_default_mcp_servers(mcp_mode="docker")`
  attached to the commit with the expected-delta table from §1 (zen −1, conport
  disabled, claude-context dedup, pal→docker-exec); `grep -rn MCPRegistry src/ | grep -v
  mcp/registry.py mcp/__init__.py` → 0 hits.

**Slice 2 — Kill.**
- Delete `src/dopemux/mcp/registry.yaml`, `src/dopemux/mcp/registry.py`, the
  `mcp/__init__.py:1-9` re-exports, `tests/test_mcp_registry.py`,
  `fleet_catalog.validate_legacy_registry_contract` (`fleet_catalog.py:1000-1028`) and
  its call site (`tests/arch/test_mcp_fleet_catalog_contract.py:155`).
- Execute the ADR-mandated reader grep (`adr-mcpint-001:265-266`): repo-wide
  `MCPRegistry|mcp/registry|registry\.yaml` (excluding `services/registry.yaml`) must be 0.
- **Verification**: `pytest tests/arch tests/test_mcp_config_generation.py`; `python -c
  "import dopemux.mcp"`; full-suite smoke on the touched packages.

**Slice 3 — name-web sweep (SEPARATE follow-up packet, not REGKILL-008).**
`dopemux-*` → catalog short names across the 8 modules + user-config migration +
`MCP_NAME_MAPPING` retirement. Optional; the shim is stable indefinitely.

Slices 1 and 2 are separate commits but should land in **one PR**, satisfying ADR-001
Migration step 3's "no window where two truths coexist ungated" (`adr-mcpint-001:290-291`).

---

## 5. Question (e) — rollback story

- **Slice 1 revert** (`git revert <s1-sha>`): restores registry consumption exactly —
  slice 1 deliberately does not touch `registry.yaml`/`registry.py`, so revert is
  self-contained.
- **Slice 2 revert**: restores the deleted files from git; slice 1's adapter keeps
  working (it never read them), so a slice-2-only revert is safe and inert.
- **No persistent-state migration exists to roll back**: defaults are computed at
  `load_config()` time (`manager.py:339-350`); user files are only written on explicit
  user actions (`save_user_config` `manager.py:418-424`, `add_mcp_server` `:444-448`).
  The repair path (`:365-416`) rewrites only entries it positively recognizes; under the
  adapter it can only substitute catalog-truth values, so a rollback never has to undo a
  data migration — worst case a user re-saves a config with adapter-generated defaults,
  which the restored registry path treats as an explicitly-configured `mcp_servers`
  block (`manager.py:341-342`) and leaves alone.
- Consistent with ADR-001's own rollback note: "the legacy registry stays deleted
  (nothing reads it)" (`adr-mcpint-001:297-298`).

---

## 6. Decision summary

**Recommended path (one path)**: No catalog schema change → catalog-backed
`legacy_config_adapter` with legacy-alias emission and truth-fixed output (zen gone,
conport/dc/leantime present-disabled, pal via docker-exec, claude-context deduped;
`local:` fallbacks retired) → kill registry files + loader + registry-shaped tests in
the same PR, second commit → name sweep deferred to its own packet.

**Rejected (one line each)**:
- Catalog grows `local_fallback:`/health fields — re-imports the rot class v2 was built to kill, for a fallback with no verified user.
- Behavior-preserving adapter — reproduces runtime-refuted claims and double-churns ~7 test files.
- Rename sweep inside this packet — converts a registry kill into a user-state migration.
- Keep registry.yaml as data for a new loader — two truths on disk, ADR-001 §3's named disease.
- SSE support in `http_stdio_bridge` now — real fix for conport-in-launcher, but out of scope; disabled-entry is honest until it lands.

**Confidence**: high on the census and rot findings (all runtime-code-cited);
medium on the exact test-rewrite line counts (unit repair tests not read line-by-line —
audit at implementation).
