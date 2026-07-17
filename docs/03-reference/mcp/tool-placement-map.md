# MCP Tool Placement Map — where every custom tool belongs

**Program**: DMX-MCPINT · **Date**: 2026-07-16 · **Status**: Design (feeds ADR-mcpint-001/002, IMP-ADHDINTEL-007, IMP-COMPLEX-008, FND-CATALOG-001)
**Inputs**: G3 decision (two surfaces, no overlap — all ADHD features kept), G5 decision (complexity_coordinator = single scorer), live tool-delta analysis (candidate serena: 46 defined, 41 not in upstream; upstream: 27 live, 22 not in candidate), `mcp_tool_surfaces.json`, feature register.

## 1. Plane taxonomy and the placement rule

Every agent-facing tool gets exactly ONE home server, chosen by plane authority:

| Plane | Authority (server) | What belongs here |
|---|---|---|
| memory/decisions (Trinity 1) | conport | decisions, progress, context, custom data — writes + canonical reads |
| chronicle (Trinity 2) | dope-memory | session memory, recap, replay, reflection, correction |
| retrieval (Trinity 3) | dope-context | semantic/lexical search over code+docs+indexed projections; index lifecycle |
| workflow | task-orchestrator | work items, transitions, dependencies, notes, gates |
| code-intel | serena (upstream) | symbol nav, definitions/references, symbol editing, serena memories |
| **adhd** | **adhd-engine (new MCP surface)** | attention/energy state, F001 untracked-work lifecycle, focus/fatigue/learning intelligence, usage analytics, ADHD-aware guidance |
| reasoning | pal-stdio | multi-model analysis chains |
| research | gpt-researcher | web research + reports |
| dcp-read | dcp-readonly-facade | cross-plane READ projection for non-attributed agents |
| infra (non-agent) | services w/o MCP surface | webhook_receiver, litellm, redis, bridges |

**Placement rule for any new tool**: (1) who is the canonical WRITER of the data it touches? → that plane's server. (2) Pure read spanning planes? → facade. (3) Derived/computed signal used by several planes? → a shared **library**, surfaced through each consumer plane's existing tools — never a new server for a single computation. (4) Overlaps an existing tool's function? → delegate or drop; never ship the duplicate.

## 2. The 41 Serena-candidate tools — placement (G3 execution spec)

Target: new MCP surface **on adhd-engine** (catalog name `dope-adhd`). Rationale: the engine already owns the events, notification dispatcher, personal thresholds, and state these tools need; an intended-but-empty `services/adhd_engine/mcp_stdio.py` stub confirms the original architecture pointed here; no new service to operate. (Standalone `dope-adhd-intel` remains the fallback if engine image bloat becomes real.)

| Disposition | Tools | Home / action |
|---|---|---|
| **SHIP on dope-adhd** — F001 lifecycle (10) | detect_untracked_work(+_enhanced), track/snooze/ignore_untracked_work, get/update_untracked_work_config, get_abandoned_work, mark_abandoned, get_abandonment_stats, suggest_branch_organization | adhd plane; storage ports with them; auto-track keeps writing to ConPort via slim surface (log_progress); H5 hook probe stays as the lite front-end and dedupes against this backend |
| **SHIP on dope-adhd** — intelligence (4) | filter_by_focus, suggest_next_step, get_reading_order, update_focus_mode | adhd plane (focus modes, fatigue, adaptive learning engines ride behind these) |
| **SHIP on dope-adhd, DELEGATING** — complexity (2) | analyze_complexity, get_unified_complexity | thin wrappers over the **complexity_coordinator library** (G5); no independent scoring logic remains here |
| **SHIP on dope-adhd** — usage analytics (6) | get_metrics_dashboard, get_metric_history, save_metrics_snapshot, get_pattern_stats, get_top_patterns, get_navigation_patterns | adhd plane (developer-behavior analytics); feeds recap/dashboards |
| **SHIP on dope-adhd** — workflow-ish nav (3) | predict_navigation_from_git, find_test_file, get_workspace_status | behavioral/git-derived guidance, not LSP truth — adhd plane fits; get_workspace_status doubles as the surface's health tool |
| **SHIP on dope-adhd (phase 1), consolidation target dope-context (phase 2)** — structural graph (6) | find_callers, find_callees, get_import_graph, get_ast_outline, find_relationships, get_context | no upstream overlap, so no-overlap holds; implementation is entangled with the candidate's Tree-sitter/SQLite stack — port as-is now, revisit moving into dope-context (the AST plane) once IMP-COMPLEX-008 settles the shared-parsing question |
| **DROP — delegate to dope-context** (1) | find_similar_code | true duplicate of `dope-context.search_code` (plane 3 owns semantic similarity); instruction surfaces point there |
| **DROP — upstream covers** (4) | find_references, goto_definition, search_pattern, get_file_symbols | upstream serena: find_referencing_symbols, find_symbol, search_for_pattern, get_symbols_overview |
| **DROP — upstream + native cover; write-lane policy** (4) | apply_patch, batch_apply_patch, create_file, write_file | upstream editing suite + agents' native Edit/Write; adding writes to an ADHD server violates plane discipline |

Net: **31 tools ship** on `dope-adhd`, **9 drop** (1 delegated, 8 redundant), 2 of the 31 are delegating wrappers. Nothing the user asked to keep is lost — every dropped tool's *function* exists elsewhere and the drop list contains only duplicates.

## 3. Other custom MCP tools/surfaces — assessment

| Surface | Finding | Placement decision |
|---|---|---|
| **mcp-capture** (stdio MCP, capture/emit, SHA256 dedup, lane-aware) | Real finished server, registered nowhere | **RETIRE** — G2 makes `capture_client` + authenticated `/events` the canonical ingress; a second capture door recreates the two-contract drift that emptied the chronicle. Its dedup/audit ideas fold into capture_client backlog. Register: `retired`, decision `adr:adr-mcpint-004` |
| **complexity_coordinator** (`services/complexity_coordinator/unified_complexity.py`) | A single **library module** (F-NEW-3), not a service — no FastAPI/MCP surface exists | **LIBRARY, not a server** (refines G5): relocate to `src/dopemux/complexity/` (or shared pkg); consumers delegate — dope-adhd `analyze_complexity`/`get_unified_complexity`, dope-context `get_chunk_complexity` (fixes its lying docstring by delegation), TO scoring, `/dx:prd-parse`. dopecon-bridge `complexity_scorer.py` + TO internal scorer become inputs or die. IMP-COMPLEX-008 scope updated |
| **claude_brain** (prompt optimization, 15 files) | No MCP/HTTP surface; library-shaped; unaudited | **HOLD** — assess-or-shelve as a register decision (`held`); not part of this effort's wiring; candidate for adr-mcpint-005 addendum if no consumer emerges |
| **webhook_receiver** (:8790 + poller) | Infra sidecar, in compose, healthy | **Infra plane, non-agent** — catalog as service entry (no MCP exposure, no agent matrix row) |
| **ConPort dark admin tools** (fork_instance, promote, promote_all) | Live on the 17-tool surface | **Stay on conport, marked `admin`** in catalog personality; excluded from workflow docs + non-Claude exposure rows; operator-only |
| **DCP facade 12 tools** | Built, dark | **dcp-read plane** per ADR-mcpint-002 — universal read projection for OpenCode/Gemini/Copilot/ChatGPT (Codex graduates to full parity per G1 after identity+actor-auth) |
| **adhd-engine HTTP routes** (/external-activity, /log-git-event, /state…) | Server-side only | **Stay HTTP** — hook/service ingress, not MCP tools; dope-adhd MCP surface is additive on the same engine |
| **leantime-bridge** (:3015, http-sse, healthy) | In compose, orphaned from catalog | **PM-sync plane**: catalog entry (FND-CATALOG-001) with `agents: none` default — operator/PM flows only |
| **desktop-commander** (SSE :3012, 4 GUI tools) | Quarantined-but-running facade | Unchanged `decision-required` (wire-real-upstream-on-host vs retire); NOT placed by this effort |
| **scheduled-tasks / mcp-registry / context7** (host-level, live) | Undocumented in repo | Catalog as `managed: false` external entries (FND-CATALOG-001) so the map is complete; **scheduled-tasks is the designated scheduler** for the notifier daily-report + copilot-ingester follow-ups |
| **TO predictive-risk (G4)** | 527-line module, dormant | **No new tool surface** — pilots as flag-gated PostToolUse advisory text (IMP-RISK-005); graduates to a TO tool only if the pilot survives |
| **gptr dead-twin ADHD tools** (summarize_research, code_examples, trend_analysis) | Only in the dead twin | Stay shelved; if ever revived their home is the gpt-researcher server itself |
| **Serena upstream write tools** (execute_shell_command, symbol edits, memories writes) | Live on :3006 — violates read-only contract | Gating owned by **DMX-ARCH-SERENA-SURFACE-003**: read-only default profile; write profile behind explicit flag; memories stay (they're serena-plane state, not repo writes) |

## 4. Resulting target surfaces (after this effort)

| Server | Tools (target) |
|---|---|
| conport | 17 (unchanged; 3 marked admin) |
| dope-memory | 10 (unchanged) |
| task-orchestrator | 14 (unchanged) |
| serena (upstream) | 27, read-only default profile (write profile gated) |
| dope-context | 18, `get_chunk_complexity` delegates to complexity library |
| **dope-adhd (NEW, on adhd-engine)** | **31** (10 F001 + 4 intelligence + 2 complexity-delegating + 6 analytics + 3 nav-guidance + 6 structural-graph) |
| pal-stdio | 18 (unchanged) |
| gpt-researcher | 5 (unchanged) |
| dcp-readonly-facade | 12 (deployed; 3 deferred pending JSON-RPC bridge) |
| retired/absorbed | mcp-capture, exa (runtime stop owed), candidate-serena duplicates ×8, find_similar_code (delegated) |

## 5. Open items

1. Standalone-vs-on-engine fallback trigger for dope-adhd: revisit only if engine image/startup cost becomes real (decision recorded in IMP-ADHDINTEL-007).
2. Phase-2 consolidation of the 6 structural-graph tools into dope-context — open until IMP-COMPLEX-008 proves shared parsing.
3. claude_brain assess-or-shelve.
4. desktop-commander wire-or-retire (pre-existing user decision, unchanged).
