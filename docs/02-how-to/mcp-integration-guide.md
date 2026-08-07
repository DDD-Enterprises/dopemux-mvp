---
id: mcp-integration-guide
title: MCP Integration Guide — Catalog, Generated Configs, and Implicit Use
type: how-to
owner: '@hu3mann'
date: '2026-07-18'
author: '@hu3mann'
last_review: '2026-07-18'
next_review: '2026-10-16'
prelude: The one curated guide to the DMX-MCPINT integration — catalog v2 as single
  source, generated agent configs and their parity gates, adding servers, implicit
  context channels, tool-name discipline, and the debug runbook.
---
# MCP Integration Guide

The durable operating model from program DMX-MCPINT (ADR-MCPINT-001..005, all
ACCEPTED 2026-07-17). Each section leads with the rule; details follow.

## 1. The model in one page

**Rule: `mcp_catalog.yaml` is the single source of truth for the MCP fleet.
Everything agent-facing is generated from it. Nothing generated is hand-edited.**

The catalog carries the v2 fields (ADR-MCPINT-001): per-server `agents:` exposure
matrix, `tools:` pointer into the committed `mcp_tool_surfaces.json` snapshot,
`admin_tools:` (operator-only, e.g. ConPort `fork_instance`/`promote`/`promote_all`),
`aux_surfaces:` (runtime-observed non-contractual endpoints), and `managed: false`
for host-level externals. (The literal `version:` key is still `1` — see §7.)

Generated targets and their parity gates (all gates live in
`src/dopemux/mcp/fleet_catalog.py`, run by `tests/arch/test_mcp_fleet_catalog_contract.py`):

| Generated target | Renderer | Parity gate |
|---|---|---|
| worktree `.mcp.json` (per-worktree defaults) | `render_per_worktree_mcp_json` | `validate_generated_mcp_json_parity` |
| global singleton fragment (`sync-globals` → `~/.claude.json`) | `render_singleton_mcp_servers` | `validate_decision_required_generated_config_quarantine` |
| `opencode.jsonc` managed `mcp` block | `render_opencode_jsonc` | `validate_opencode_jsonc_parity` |
| `mcp-proxy-config.copilot.yaml` (whole file) | `render_copilot_proxy_config` | `validate_copilot_proxy_config_parity` |
| `.codex/config.toml` managed `mcp_servers` region | `merge_codex_config_toml` | `validate_codex_config_toml_parity` |
| preview bundle under `--output-dir` (codex/opencode previews, `health/mcp-health-probes.json`, `docs/mcp-fleet.md`) | `generate_fleet_output_files` | reviewed, not committed |

Two more standing gates: `validate_catalog_personality_contract` (authority/lifecycle
metadata cannot drift) and `validate_catalog_compose_alignment` (catalog ports and
docker-exec targets must match `compose.yml`). The bundled twin
`src/dopemux/mcp/default_catalog.yaml` is sync-gated against the root catalog.

Two structural facts complete the model:

- **The DCP read-only facade is the read plane for non-attributed agents**
  (ADR-MCPINT-002): OpenCode, Gemini, Copilot, ChatGPT — and Codex until its
  parity preconditions land — read through `dcp-readonly-facade`, never through
  a second read door.
- **`native_hooks.py` SessionStart is the only implicit-context channel**
  (ADR-MCPINT-003): context that arrives unsummoned enters there and nowhere else.

## 2. How agent configs are produced

**Rule: agent configs come from `dopemux mcp generate --apply` — NEVER from an
editor. Hand-edits to generated files or managed regions fail CI parity gates,
and hand-authored `[mcp_servers.*]` tables outside the Codex markers abort the merge.**

Flow: `dopemux mcp generate` (dry-run default, prints what would be written) →
`dopemux mcp generate --apply --output-dir <dir>` writes the preview bundle to
`<dir>` **and** updates the in-repo agent config targets. Per agent:

- **claude** — worktree `.mcp.json` (defaults: conport, dope-memory,
  task-orchestrator) plus global singletons applied via `dopemux mcp sync-globals`.
- **codex** — full fleet in the `.codex/config.toml` managed region, but only
  behind `--allow-sequenced`, which the CLI **refuses** until both ADR-MCPINT-002
  G1 prerequisites land: (1) **DMX-MEMSPINE-IDENTITY-005** (per-request
  memory-spine identity, fail-closed writes) and (2) task-orchestrator
  **`actor_authentication.enabled`**. Until then the Codex preview always lands
  under `--output-dir` and the in-repo file stays read-plane.
- **opencode** — managed block between `// BEGIN dopemux-managed mcp` /
  `// END dopemux-managed mcp` markers in `opencode.jsonc`; user keys
  (`permission`, `instructions`, …) are preserved. `read-plane` rows render as
  direct config only for read-safe planes (today: reasoning → pal-stdio);
  everything else defers to the facade and is named in a comment.
- **copilot** — `mcp-proxy-config.copilot.yaml`, fully generated; planned-active
  servers without a truthful endpoint are listed as deferred, never invented.

Exposure changes are catalog `agents:` edits + regeneration — a one-line catalog
change, not a config edit (ADR-MCPINT-002 invariant).

## 3. How to add a new MCP server

**Rule: catalog entry → snapshot → generate → gates green. A server not in
`mcp_catalog.yaml` cannot appear in any generated agent config.**

1. **Catalog entry** with the required personality metadata — every server must
   carry `plane`, `authority_role`, `lifecycle`, `management_model`,
   `identity_scope` (gate: `validate_catalog_personality_contract`), plus
   `scope`, `transport`, a runtime-verifiable endpoint (`url`/`url_template` or
   `command`+`args`), an `agents:` matrix (or the string `none`), and a `tools:`
   pointer (`snapshot_key` + `schema_version`). `lifecycle: decision-required`
   must name a `follow_on_decision` and is quarantined from every startable
   generated config.
2. **Snapshot the tool surface**: `dopemux mcp snapshot-tools` refreshes
   `mcp_tool_surfaces.json` — the only place tool names live. The catalog
   `tools:` pointer must resolve into the committed snapshot.
3. **Regenerate**: `dopemux mcp generate --apply --output-dir <dir>`.
4. **Gates green**: `pytest tests/arch/test_mcp_fleet_catalog_contract.py`
   (schema, personality, compose alignment, quarantine, parity). The schema is
   closed — unknown fields are rejected, so the schema and catalog move together.

Host-level servers this repo does not manage use the external shape (no
endpoint keys allowed; the schema enforces it):

```yaml
  my-host-tool:
    scope: singleton
    transport: external
    managed: false
    plane: automation
    authority_role: task-scheduler
    lifecycle: operator-managed
    management_model: external
    identity_scope: host-session
    follow_on_decision: none
    agents: {claude: full, codex: none, opencode: none, gemini: none, copilot: none, chatgpt: none}
    description: "Documented for fleet-map completeness (ADR-MCPINT-001 §4)."
```

## 4. How implicit context works

**Rule: implicit context is Claude-only and enters through exactly one channel —
`native_hooks.py` SessionStart. The channel list is CLOSED (ADR-MCPINT-003);
adding one requires a superseding ADR.**

Four bounded blocks (statuses per `docs/03-reference/mcp/workflows.yaml`
`session-start`, which is `status: partial`):

| # | Block | Status |
|---|---|---|
| 1 | task-orchestrator `get_context` replay (cached from PostToolUse) | **live** |
| 2 | dope-memory recap (bounded Top-3, ~1200 chars) | pending **MCPINT-IMP-RECAP-003**, BLOCKED by DMX-MEMSPINE-IDENTITY-005 |
| 3 | fleet-capability line (cached health probe, 60s TTL) | pending **MCPINT-IMP-HEALTH-004** |
| 4 | untracked-work probe (H5 lite) | **live** (dedupes against the DopeCode F001 backend once DMX-DOPECODE-DEPLOY-001 lands) |

**Budgets**: ~3KB total across all four blocks; 2s timeout per block;
**fail-open** — a dead backend yields a missing block, never a blocked session
and never a stack trace. PostToolUse is limited to two channels (TO cache
refresh + the SVCFIN-owned ADHD activity ingress), plus the one sanctioned
flag-gated exception (`DOPEMUX_ENABLE_PREDICTIVE_RISK`, MCPINT-IMP-RISK-005
pilot). Non-Claude agents get context by explicit reads through the facade —
no implicit channel exists for them.

## 5. Tool-name discipline

**Rule: `mcp_tool_surfaces.json` is the truth for tool names. If a name is not
in the snapshot, it does not exist — no matter what a doc, memory, or habit says.**
Refresh only via `dopemux mcp snapshot-tools`.

Dead-name traps (all found live in instruction surfaces during the P0 audit):

| Dead name (do not use) | Live name | Server |
|---|---|---|
| `update_active_context` | `update_context` | conport |
| `get_active_context` | `get_context` | conport |
| `search_decisions_fts` | `search_content` | conport |
| `log_custom_data` | `save_custom_data` | conport |
| `mcp__zen__*` | `mcp__pal-stdio__*` | PAL renamed; pal-stdio is the sole PAL surface (the pal `:3003/mcp` URL is fiction) |
| `serena-v2` / `mcp__serena-v2__*` | `mcp__serena__*` | catalog key is `serena` |

**Drift-gate coverage today**: `find_unknown_command_tool_surfaces` scans
`.claude/commands/*.md` — server-granular for every `mcp__<server>__<tool>`
reference, tool-granular for conport (via the static `_CONPORT_TOOL_SNAPSHOT`
in `fleet_catalog.py`). The full snapshot-backed, all-server, all-surface
tool-granular gate is MCPINT-FND-DRIFTGATE-003 (pending). Known snapshot holes:
stdio servers (pal-stdio, gpt-researcher, MCP_DOCKER) are captured as
`unreachable` with zero tools — their counts (18 / 5) stand on session evidence
until exec-transport capture lands.

## 6. Debug runbook

**Rule: follow AGENTS.md §12.4 in order — source envrc → `dopemux mcp doctor` →
transport-correct curl probe → container logs → `./mcp_server_health_report.sh`
→ port-collision check.** Transport truth: a `406` on `GET /mcp` means the
server is Streamable HTTP and you should POST JSON-RPC — never flip it to SSE.

Three runtime lessons this program paid for (evidence:
`claudedocs/mcp-fleet-runtime-verification-2026-07-16.md` §0, N1, N4, N6):

1. **Docker wedge — backend up, engine dead.** `docker ps` hangs and published
   ports refuse connections while `com.docker.backend` looks alive. SIGTERM and
   `osascript quit` are insufficient: `pkill -9 -f com.docker.backend`, relaunch
   Docker Desktop; the engine restores in ~10s and containers auto-restart. No
   doctor detects this state — if every docker command hangs, suspect the wedge.
2. **ConPort "unhealthy" but SSE answering.** The compose healthcheck rides the
   `:3004` HTTP health listener, which can reset connections while the real MCP
   surface on `:3005/sse` works fine. Trust the SSE probe over `docker ps`
   health; if the MCP surface itself fails, `docker restart mcp-conport`.
3. **`mcp init` reserved-singleton catch-22 — FIXED 2026-07-16 (#1052,
   `268dd05c1f`).** A *healthy* task-orchestrator on reserved port 7890 used to
   read as "occupied by an unknown process" because reserved singletons never
   write leases yet occupancy was judged by lease identity (`port_allocator.py`).
   The fix added a positive MCP identity probe: when the reserved port is
   occupied with no matching lease, `port_allocator` performs the `initialize`
   handshake and checks `result.serverInfo.name` — a match (`mcp-task-orchestrator*`)
   assigns the port with no lease (singleton policy preserved); an unknown or
   unreachable occupant still blocks. **Current behavior**: `mcp init` recognizes
   a healthy singleton on 7890 automatically; there is no hand-editing of
   `.envrc.dopemux-mcp` required or supported for this case. See also the
   multi-instance fleet design's reserved-singleton probe allowlist (§3.2 of
   `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md`), which extends the
   same identity-probe pattern to other host-singleton servers.

## 7. Known gaps this guide papers over

- Catalog `version:` is literally `1` (schema `const: 1`, `load_root_catalog`
  requires it) although ADR-MCPINT-001 mandates a `version: 2` cutover — the v2
  *fields* landed, the version bump did not.
- Catalog `workflows:` refs are unpopulated even though `workflows.yaml` exists.
- `workflows.yaml` references server `dopecode` (SVCFEAT amendment) which has no
  catalog entry or snapshot key yet — those steps are `pending:` and
  non-contractual until DMX-DOPECODE-DEPLOY-001.
- `src/dopemux/mcp/registry.yaml` is deprecated-but-present (live consumers
  named in its header), not yet killed as ADR-MCPINT-001 §3 directs.

## References

- ADRs: `docs/90-adr/adr-mcpint-001..005` · placement map:
  `docs/03-reference/mcp/tool-placement-map.md` · workflows:
  `docs/03-reference/mcp/workflows.yaml`
- Doctrine: `AGENTS.md` §12 (transports, ports, debug) and §12.5 (generated
  surfaces + implicit use)
- Setup in other repos: `docs/02-how-to/mcp-setup-other-repos.md` · transport
  bugs: `docs/02-how-to/mcp-transport-and-port-bugs.md`
