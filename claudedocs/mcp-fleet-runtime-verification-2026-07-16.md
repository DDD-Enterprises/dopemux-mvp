# MCP Fleet Runtime Verification — 2026-07-16 (DMX-MCPINT P0)

**Program**: DMX-MCPINT (orchestrator root `af10eefd`, packet MCPINT-P0-AUDIT-001 `ab5b5d62`)
**Worktree**: `.claude/worktrees/trusting-engelbart-d2fbfe` @ branch `claude/mcp-dopemux-integration-audit-877f32`
**Proof bundle**: `proof/mcpint-p0/` (per-server `tools/list` JSON, `supplement.json`, `docker_ps_snapshot.txt`, env captures, litellm crash log)
**Method**: live JSON-RPC `initialize` + `tools/list` per server (streamable-HTTP POST `/mcp`; classic SSE `GET /sse` → endpoint → POST), plus HTTP health and auth probes. Every prior fleet/service audit ran docker-down (all runtime claims NOT_RUN); this converts them.

## 0. Session narrative (how the fleet got up)

Docker Desktop backend had been running ~21h in a wedged state: `docker ps`/`docker info`
hung indefinitely, published ports (e.g. TO :7890) accepted no connections. `osascript quit`
left `com.docker.backend --autostart` alive; SIGTERM insufficient; SIGKILL + relaunch
restored the engine in ~10s and auto-restored 25 containers. This wedge-class outage is
itself a finding: **no health/ensure layer detects "backend up, engine dead"** —
`dopemux mcp doctor`/`ensure` would have hung with the CLI.

## 1. Claim verification table

| # | Claim (source) | Verdict | Evidence |
|---|---|---|---|
| 1 | ConPort deployed surface = slim 17-tool stdio set, not enhanced_server (fleet audit 07-03; Agent C) | **VERIFIED** | SSE probe :3005 → 17 tools, names exactly match `conport_mcp_stdio.py` (`tools_list/conport.json`) |
| 2 | task-orchestrator :7890 = Kotlin v3.8.0, 14 v3 tools | **VERIFIED** | `initialize` → `mcp-task-orchestrator-current 3.8.0`; 14 tools (`task-orchestrator-7890.json`) |
| 3 | :8000 "task-orchestrator" = unrelated Python FastAPI (name collision) | **VERIFIED** | `/mcp` 404; `/health` = `{"service":"task-orchestrator","status":"ok"}`; FastAPI Swagger at `/docs` (`supplement.json`) |
| 4 | Serena deployed = upstream wrapper, 27 tools | **VERIFIED** (with a twist) | :3006 → 27 tools; health self-identifies `"service":"serena-v2"` on :4006 — the *name* "serena-v2" is live even though the 40-tool in-repo candidate is not |
| 5 | dope-context = 18 tools, clean 1:1 | **VERIFIED** | :3010 → 18 tools (`dope-context.json`) |
| 6 | dope-memory = 10 tools | **VERIFIED** | :3020 → 10 tools (`dope-memory.json`) |
| 7 | dopecon-bridge `/events` dead publish path (JWT 401, empty user store) | **VERIFIED** | unauth POST `/events` → `401 {"detail":"Not authenticated"}` (`supplement.json`) |
| 8 | DCP read-only facade dark (no listener, no config) | **VERIFIED** | no compose service, no catalog entry, no port; 12-tool server exists only in `services/dcp-readonly-facade` source/tests |
| 9 | ENABLE_MIRROR_SYNC default off | **VERIFIED** | `ENABLE_MIRROR_SYNC=false` on `dopemux-dope-memory-1` (`env_dope_memory.json`) |
| 10 | Trinity Rule 2 indexing flag off | **VERIFIED** | no `ENABLE_DOPECONTEXT_INDEX` in `mcp-dope-context` env at all (unset = off) (`env_dope_context.json`) |
| 11 | pal-stdio is the live PAL; pal-http :3003/mcp per catalog | **PARTIALLY REFUTES CATALOG** | pal-http `/health` 200 (`mcp_process_running: true`, the #993 fix live) but `/mcp`, `/sse`, `/messages` all 404 — catalog's `:3003/mcp` endpoint does not exist; only pal-stdio (docker exec) is a usable PAL surface |
| 12 | gptr-mcp = stdio-exec only (catalog) | **REFINED** | :3009 serves an SSE-style `/messages` endpoint (400 on wrong content-type, not 404) + healthy `/health` — an HTTP surface exists that the catalog doesn't describe |
| 13 | leantime-bridge orphaned from catalog | **VERIFIED (but alive)** | `/health` 200 self-describing `"transport":"http-sse"`; running + healthy yet absent from `mcp_catalog.yaml` |
| 14 | desktop-commander quarantine (catalog `decision-required`) | **VERIFIED-BUT-INERT** | container up, SSE :3012 answers with 4 GUI tools (`desktop-commander.json`) — quarantine only removes it from generated configs, not from runtime |
| 15 | exa retired (ADR-223) | **REFUTED AT RUNTIME** | `mcp-exa` Up (healthy), bound `0.0.0.0:3011` — retired server running AND world-bound (loopback violation on a retired surface). Host compose state predates the prune; graveyard PR unexecuted here |
| 16 | adhd-engine ignition (smoke-on, :3025) | **REFUTED AT RUNTIME** | :3025 connection refused; `adhd-engine` ABSENT from `docker ps -a` (never created in this host's compose project) |
| 17 | 2026-07-06 graveyard prune | **NOT executed on this branch/host** | `session_intelligence`, `voice-commands`, dead twins all present in tree; exa/desktop-commander containers running |

## 2. New findings (not in any prior audit)

| # | Finding | Severity | Detail |
|---|---|---|---|
| N1 | **`dopemux mcp init` catch-22 on reserved singleton** | HIGH (blocks config regen fleet-wide) | `port_allocator.py:355-383`: reserved singletons never write leases, but occupancy legitimacy is judged *only* by lease identity → any healthy TO on 7890 = "occupied by an unknown process" = BLOCKED. `mcp init --force` cannot run while the fleet is healthy. Background fix task spawned. |
| N2 | **Workspace-identity contamination on primary dope-memory** | HIGH (memory-spine integrity) | `dopemux-dope-memory-1` (compose project `dopemux`) carries `DOPE_MEMORY_WORKSPACE_ID=dNh_CRM` — another repo's workspace ID on the primary memory container. Chronicle writes from this host attribute to the wrong workspace. Runtime proof of the MEMSPINE-IDENTITY-005 hazard class; strengthens the per-request-identity design over env-based. |
| N3 | **mcp-litellm crash-loop, root cause broken image dep** | MED | `ImportError: cannot import name 'DatasourceOverride' from 'prisma.types'` (`litellm_crashloop.log`); :4000 refuses connections → model-routing backend down. |
| N4 | **Docker-wedge blind spot** | MED | 21h wedged backend; all doctors/health checks assume a responsive docker CLI. No watchdog distinguishes "engine dead" from "services down". |
| N5 | **Per-project twin containers coexist on primary ports plane** | MED | `task-orchestrator-dnh_crm-*`, `mcp-conport_dnh_crm_8d6d` run beside primary singletons; combined with N2, cross-project runtime bleed is systemic, not hypothetical. |
| N6 | conport HTTP health port :3004 resets connections | LOW | MCP surface on :3005 works; the separate health listener drops connections (`supplement.json`) — compose healthcheck may be passing against a different path/port than the one documented. |
| N7 | Shell-sandbox note (harness, not repo) | INFO | Loop-heavy one-liners intermittently ran in a no-exec sandbox during this session; probes were moved into Python scripts. Recorded for reproducibility of the proof bundle. |

## 3. Live tool-surface snapshot (seed for FND-SNAPSHOT-002)

Captured in `proof/mcpint-p0/tools_list/*.json` (raw `tools/list` responses):

| Server | Transport verified | Tools |
|---|---|---|
| conport (:3005) | SSE | 17 |
| dope-memory (:3020) | streamable HTTP | 10 |
| task-orchestrator (:7890) | streamable HTTP | 14 |
| serena (:3006) | streamable HTTP | 27 |
| dope-context (:3010) | streamable HTTP | 18 |
| desktop-commander (:3012) | SSE | 4 |
| pal-http (:3003) | — (no MCP endpoint found) | n/a (healthy wrapper, `/mcp` 404) |
| gptr-mcp (:3009) | SSE-style `/messages` exists; tools/list not captured this pass | n/a |
| leantime-bridge (:3015) | http-sse self-described; tools/list not captured this pass | n/a |
| to-compose (:8000) | not MCP (FastAPI) | n/a |

pal-stdio + gptr stdio surfaces (docker exec) not re-captured here; session-observed
counts (18 / 5) stand from the fleet inventory. FND-SNAPSHOT-002 should add exec-transport
capture for pal-stdio, gptr-mcp, and the two `/messages` SSE surfaces.

## 4. Delta vs prior audits (post-#1036/#1037/#1042/#1044)

- Catalog/generator/gates machinery (fleet_catalog.py, ensure, personality contract) — landed and intact; the runtime, however, still diverges from catalog in both directions (running-but-uncataloged: leantime-bridge, exa, dnh_crm twins; cataloged-but-wrong: pal `:3003/mcp`).
- DCP registry v2 (#1036) — in tree, tested, still dark (no deployment vector).
- Runtime stack restore (#1037) — files present; the port-lease layer works but carries the N1 catch-22.
- Chronicle spine — mirror code present; `ENABLE_MIRROR_SYNC=false` + N2 identity contamination mean the spine is still not trustworthy end-to-end on this host.

## 5. Consequences fed forward

- **P1 register**: entries for every claim above get `last_verified: 2026-07-16` + proof path.
- **FND-CATALOG-001**: must also fix pal transport truth (`:3003/mcp` is fiction) and decide exa/desktop-commander runtime posture, not just catalog posture.
- **IMP-EVENTS-006 / G2**: 401 bridge path re-confirmed; capture_client direct-Redis remains the only working ingress.
- **MEMSPINE-IDENTITY-005 (SVCFIN)**: N2 is the runtime smoking gun; raise its priority.
- **New candidate packet (not yet loaded)**: docker-wedge watchdog + `ensure` timeout hardening (N4) — hold for triage rather than scope-creep P0.

**Validation buckets**: PASS = probes in §1/§2 with saved evidence; NOT_RUN = pal-stdio/gptr stdio tools/list capture (deferred to FND-SNAPSHOT-002); FAIL = none.
