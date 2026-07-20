# Dopemux — Historical Planned-Features Register (RAW, Explore-agent output 2026-07-16)

> **Provenance**: verbatim output of the DMX-MCPINT Phase-1 exploration agent
> (documentation archaeology over claudedocs/, docs/90-adr/, task-packets/,
> .claude/modules/, services/ READMEs). This is the RAW INPUT to
> MCPINT-P1-REGISTER-001 (`docs/03-reference/mcp/feature-register.yaml`).
> Status labels are doc-asserted; runtime claims cross-checked separately in
> `claudedocs/mcp-fleet-runtime-verification-2026-07-16.md` (P0).

**Scope basis / caveat.** Worktree `trusting-engelbart @ dd3f59353` at mining time.
Status labels are **doc-asserted, not runtime-verified** — every source audit ran with
Docker down (`NOT_RUN` on live behavior). Where the freshest doc
(`dopemux-completion-plan-2026-07-07.md`) says "shipped," it may be shipped on a
*newer branch than this checkout*.

**Status legend:** SHIPPED (wired + consumed) · PARTIAL (built, some paths broken/blocked) · BUILT-UNWIRED (code exists, no live consumer — "stranded") · PLANNED-NEVER-BUILT (doc/design only) · ABANDONED/SUPERSEDED (killed or replaced) · DECISION-NEEDED (open governance call).

**Primary source docs:**
- `claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md` — **[CANON]**
- `claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md` — **[FORGOT]**
- `claudedocs/service-audit-2026-07-04.md` + `...-appendix-memory-spine.md` — **[SVCAUD]**
- `claudedocs/adhd-surfaces-deep-dive-2026-07-04.md` (+ `-second/-third-opinion`) — **[ADHDDD]**
- `claudedocs/adhd-cognitive-ux-audit-2026-05-31.md` / `...-remediation-plan-...` — **[ADHD531]**
- `claudedocs/memory-context-fabric-design-2026-07-04.md` / `-interfaces-` / `-README-` / `tp-mcf-001-authority-map-2026-07-04.md` — **[MCF]**
- `claudedocs/design-dcp-mcp-skills-hooks-2026-06-10.md` — **[DCPHOOK]**
- `claudedocs/dopemux-completion-plan-2026-07-07.md` — **[PLAN]** (freshest status)
- `docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md` — **[DCPTC]**
- `docs/03-reference/serena-v2-mcp-tools.md` — **[SERV2]**
- `docs/90-adr/adr-223-retire-exa-mcp-server.md` — **[ADR223]**
- `task-packets/generated/DMX-CONPORT-OPTIMAL/*.json` — **[COPT]**
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-*` — **[DCPMR]**
- `task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-*.json` — **[FLEET]**
- `.claude/modules/shared/adhd-patterns.md` — **[ADHDMOD]**

---

## 1. ConPort (Memory Trinity plane 1 — decisions/progress/context authority)

Live shipped surface: `log_decision, get_decisions, log_progress, get_progress, update_progress, get_context, update_context, save_custom_data, get_custom_data, delete_custom_data, search_content, get_recent_activity, get_active_work, workspace_summary, promote, promote_all, fork_instance` (~17 SSE tools).

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Decisions log/get/search | [CANON]§3.2, live | Log/retrieve/FTS-search architectural decisions. | SHIPPED |
| Progress CRUD + lifecycle | [CANON]§3.2, live | Create/update/query progress entries with status lifecycle. | SHIPPED |
| Active + product context | [CANON]§3.2; [COPT]-201 | Active context shipped; **product-context model** (migration 008 + REST + MCP tools) still a packet. | PARTIAL (product context PLANNED-NEVER-BUILT) |
| Custom-data CRUD via MCP | [COPT]-104 | Expose get/save/delete custom_data on MCP surface. | SHIPPED (recently) |
| `search_content` via MCP | [COPT]-105 | Expose search on MCP surface. | SHIPPED (recently) |
| JSON-RPC parity + SSE transport fix | [COPT]-106; [CANON]§4 | Close JSON-RPC discovery gaps (advertises 13 of 17; 3 "dark", 1 missing) + fix SSE URL. | PLANNED / PARTIAL |
| Gate auto-fork write on GET | [COPT]-107; [CANON]§4 | `GET /api/progress` currently *mutates* (auto-fork ON); gate behind `?auto_fork=true`. | PLANNED-NEVER-BUILT (live hazard) |
| Relationship / knowledge-graph traversal | [CANON]§4; [MCF]; [COPT]-203 | Read-only relationship traversal via `/api/workspace-relationships` → `get_related_decisions`. Plain table, **no write API, no AGE/Cypher at runtime**. UUID-safe recursive CTE depth 1-3 is a packet. | PARTIAL (read only) |
| Entity-relationship **write** API (`link_items`/`get_linked_items`) | [COPT]-202 | MCP tools to create typed relationships. | PLANNED-NEVER-BUILT |
| Decision→progress traversal | [COPT]-204 | Endpoint + MCP tool linking decisions to progress. | PLANNED-NEVER-BUILT |
| Decision-outcome retrospective | [COPT]-301 | Endpoint + MCP tool recording decision outcomes. | PLANNED-NEVER-BUILT |
| Review-reminders | [COPT]-302 | REST + MCP tools for review reminders. | PLANNED-NEVER-BUILT |
| Decision-to-decision typed relationships (genealogy `BUILDS_UPON`) | [COPT]-303; [FORGOT]§2.1 | Typed decision-lineage routes + MCP tools; generation tracking. | PLANNED-NEVER-BUILT |
| Dark admin methods (fork/promote) | [CANON]§3.2, live | Instance fork + promotion admin ops. | SHIPPED (partly "dark"/undocumented) |
| Operator-gated enhanced schema (13-table target) | [CANON]§3.1; [COPT]-100 | Migration foundation gate; enhanced schema applied only when operator-gated (ADR PR #917/#936). | PARTIAL |
| Per-worktree instance isolation | [CANON]§4 | Isolate state per worktree. **Inert over SSE** (one global `DOPEMUX_INSTANCE_ID`); target = per-request identity. | PLANNED-NEVER-BUILT (design defect) |
| Append-only decision invariants (INV-MEM-002/003/004) | [CANON]§7.3; [PLAN]-B5 | Enforce append-only via REVOKE + trigger migration — or delete from doctrine. "Currently fiction." | DECISION-NEEDED |
| Fail-closed `_ensure_schema` verify | [CANON]§4 | Schema-verify is currently **fail-open** (new bug); make fail-closed. | PLANNED-NEVER-BUILT |
| Vector semantic search (`mem.search`, Milvus + Voyage/OpenAI) | [FORGOT]§2.1 (`memory_server.py:905-930`) | Embedding-backed semantic search over ConPort. **Milvus never deployed.** Conflicts with Trinity (semantic = dope-context). | ABANDONED / DECISION-NEEDED (vaporware, see Z) |
| Semantic node upsert (`mem.upsert`) | [FORGOT]§2.1 | Embeddings → Milvus+PG upsert. | ABANDONED (see Z) |
| Progressive-disclosure tiers (DecisionCard/Summary/FullContext, cognitive-load scoring) | [FORGOT]§2.1 (`conport_kg/queries/models.py`) | ADHD tiered decision views. | PLANNED-NEVER-BUILT (quarantined code) |
| ADHD neighborhood exploration (1-hop→2-hop, max-10/hop) | [FORGOT]§2.1 | Progressive graph exploration. | PLANNED-NEVER-BUILT (quarantined) |
| Event-driven KG orchestration (auto-trigger on decision.logged/task.started + Redis precache) | [FORGOT]§2.1 (`conport_kg/orchestrator.py`) | Auto KG updates on events; explicit "TODO publish to bus" in source. | BUILT-UNWIRED (quarantined) |
| Decision impact graph (centrality/influence scoring) | [FORGOT]§2.1 | Score decision influence. | PLANNED-NEVER-BUILT (data model only) |
| Zep conversational memory | [FORGOT]§2.1 (`memory_server.py:113`) | Config stub, never implemented. | ABANDONED (spec-only stub) |
| Direct PG AGE client (`age_client.py`, <50ms) | [FORGOT]§2.1 | Cypher graph client; Tier-0 migrations never applied. | BUILT-UNWIRED / DECISION-NEEDED |
| DCP facade re-enable search + `get_linked_items` reader | [COPT]-206 | Wire ConPort search back into facade. | PLANNED-NEVER-BUILT |
| Integration test scaffolding (testcontainers PG+Redis) | [COPT]-108 | Integration suite. | PLANNED-NEVER-BUILT |
| ConPort single-surface (retire upstream-wrapper shadow twin) | [CANON]§7.1; [PLAN]-E5 | `.claude/commands` reference 6 tool names the real SSE server lacks; wrappers launch upstream `context-portal-mcp`. Retire the twin. | DECISION-NEEDED (shadow-twin) |

---

## 2. dope-memory (Memory Trinity plane 2 — chronicle/recap/reflection authority)

Live shipped surface: `memory_store, memory_search, memory_recap, memory_replay_session, memory_reflections, memory_generate_reflection, memory_trajectory, memory_correct, memory_mark_issue, memory_link_resolution` (10 `/mcp` tools).

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Event intake → redaction → raw store (7-day TTL) → promotion → curated chronicle | [CANON]§3.2 | Full capture spine (`capture_client.py`). Spine is REAL; **but hooks pinged wrong Redis stream** (`dopemux:events` vs `activity.events.v1`) → chronicle was empty (24.5k heartbeat rows, 0 curated). | PARTIAL → [PLAN] says mirror now runtime-proven 0→1 |
| Recap / replay / reflection / trajectory | [CANON]§3.2, live | Session recap, replay, reflections, trajectory ranking. Tools SHIPPED but ranked an empty table pre-fix. | SHIPPED (surface); data PARTIAL |
| Supersession-style correction (`memory_correct`) | [FORGOT]§2.2 | Correct/retract via supersession. | SHIPPED |
| Workspace + instance partitioning | [CANON]§3.2 | Per-worktree + per-instance scoping. Instance identity **can't pass through `.mcp.json` env to HTTP servers** (design misunderstanding); target = per-request. | PLANNED-NEVER-BUILT (identity) |
| Mirror receipts from ConPort (Trinity Rule 1) | [CANON]§3.1, §7.2; [PLAN]-B3 | ConPort decision writes mirror to chronicle. Exists only in a **gated CLI path**; skill-layer `/decision`/`/caveat`/`/followup` receipts still TODO. | PARTIAL |
| Promotion allowlist (7 promotable event types) | [CANON]§7.2 correction | `{decision.logged, task.completed/failed/blocked, error.encountered, workflow.phase_changed, manual.memory_store}`. | SHIPPED |
| `error.encountered` capture (native_hooks → capture_client) | [CANON]§7.2; [SVCAUD]§4 | Hook emits on PostToolUseFailure. Shipped in #993. | SHIPPED |
| `decision.logged` chronicle fill | [SVCAUD]§4 | Blocked by stream-name mismatch (~4-line fix). | PARTIAL/PLANNED |
| `task.*` / `workflow.phase_changed` producers | [SVCAUD]§4; [PLAN]-B1 | PM emits only `task.blocked/completed` + phase-change with `from_phase` hardcoded `"unknown"`; `task.created/failed/assigned`, `blocker.cleared` never emitted. | PARTIAL |
| ADHD-aware recap (`adhd_state` annotation, fewer cards when scattered) | [PLAN]-C5 | Recap adapts to attention state; consumer side still TODO. | PARTIAL |
| Event_id idempotency dedup on consumer | [FORGOT]§2.2 | `EventBusConsumer` has no event_id dedup → dup entries on retry. | PLANNED-NEVER-BUILT |
| Session context re-injection at SessionStart | [FORGOT]§2.2 | Auto-inject last recap at session start. | PLANNED-NEVER-BUILT (see MCF TP-MCF-004) |
| Pre-storage redaction (secret/PII masking) | [FORGOT]§2.2; [MCF]§5 | Mask before chronicle.append; current = strip-and-store-minimal (leaks key names). | PLANNED-NEVER-BUILT |
| `/mcp` JSON-RPC parity | [FORGOT]§2.2 | Only `/tools/*` today; add full JSON-RPC. | PARTIAL |
| Entity/user/project scoping; memory decay/TTL; import/export; `replay_from_event_id` determinism | [FORGOT]§2.2 | Claude-Mem DR reference patterns. | PLANNED-NEVER-BUILT (deferred) |
| Instance-identity fail-closed on writes | [PLAN]-B2 | Reject identity-less writes rather than defaulting to `A`/`default`. | PLANNED-NEVER-BUILT |
| WMA prototype archival / dead stdio shim (:8096) removal / `dope-query` husk | [CANON]§4; [ADHDDD]§9 | ~3.6k-line prototype co-resident; dead shim; `dope-query` named in ADR but empty. | ABANDONED (kill-list) |

---

## 3. task-orchestrator (workflow-transition authority)

Live shipped surface (Kotlin jar v3.8.0, :7890): 14 tools.

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Persistent work-item graph; roles queue→work→review→terminal; trigger transitions + gates | [CANON]§3.2, live; 18 `/dx:*` cmds | Work-item lifecycle w/ legal transitions + note-schema gates + proof-bundle-in-note. | SHIPPED |
| Dependency graph + blocked queries | [CANON]§3.2 | Dep management + blocked-item queries. | SHIPPED (upstream bug: undercounts blocked 0 vs 27) |
| Repo-scoped singleton lifecycle | [CANON]§2, §4 | Git-common-dir-hashed HTTP singleton (best-engineered lifecycle path). **No auto-start.** | PARTIAL (no ignition) |
| Auto-start via `ensure` + truth-pack regen at v3.8.0 | [CANON]§7.1; [PLAN]-E3 | Ensure layer auto-starts singleton; regen stale v2.2.0 truth pack. | PLANNED-NEVER-BUILT |
| Rename Python `services/task-orchestrator` → `workflow-api` (end name collision) | [CANON]§7.1; [SVCAUD]§6 | In-repo Python FastAPI (:8000) shares the name — a *different system*. | DECISION-NEEDED |
| Task complexity scoring (ML bands 0–1, cognitive load, energy tagging) | [FORGOT]§2.6 (ADR-207 ML risk) | Score PRD tasks; `/dx:prd-parse` returns unscored flat lists today. **3rd of 3 competing complexity scorers.** | BUILT-UNWIRED (dormant) |
| Predictive Risk Assessment (562 lines, 8 categories incl. hyperfocus burnout) | [FORGOT]§2.6 (`predictive_risk_assessment.py`) | ML safety net; "~3 lines to hook." | BUILT-UNWIRED (highest-ROI stranded item) |
| Energy-Aware Task Routing (`get_task_recommendations`) | [FORGOT]§2.6 | Route tasks by energy; live but shallow placeholder. | PARTIAL (stub) |
| Dependency Auto-Inference (`analyze_dependencies`) | [FORGOT]§2.6 | Semantic + critical-path inference; current = keyword-only stub. | PARTIAL (stub) |
| Sprint Auto-Planning (`automate_sprint_planning`) | [FORGOT]§2.6 | ML sprint planning; ConPort has no sprint API. | PLANNED-NEVER-BUILT (see Z) |
| Multi-Team Coordination (562 lines, batched comms ≤3/day) | [FORGOT]§2.6 (`multi_team_coordination.py`) | Multi-agent coordination. Dormant-by-design for single-operator MVP. | BUILT-UNWIRED (intentional) |
| Status normalization (pending/in_progress vs TODO/DONE/BLOCKED cross-surface) | [FORGOT]§2.6 | One dialect map across surfaces. | DECISION-NEEDED |
| Decision traceability (task→ConPort decision links) | [FORGOT]§2.6 | Governance-critical for proof bundles. | PLANNED-NEVER-BUILT (P0 gap) |
| ADR-203 un-deprecation; ADR-207 capabilities | `docs/90-adr/adr-203*`, `adr-207-task-orchestrator*` | Un-deprecate orchestrator; capability expansion. | (ADR-backed intent) |

---

## 4. PAL (reasoning suite — off-compose standalone)

Live shipped surface (zen fork v9.0.2, 18 tools).

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| 18-tool multi-model reasoning suite backing AGENTS.md §5 chains | [CANON]§3.2, live | Full reasoning/analysis toolkit. | SHIPPED (consumed by Claude + Codex) |
| Managed lifecycle (`ensure-pal.sh`, real healthcheck, H3 remediation) | [CANON]§7.1; [PLAN]-E3; [FLEET]-003 | PAL runs off-compose, unmanaged, no ensure script, `required=true` for Codex → hard dependency; healthcheck is `exit 0` no-op. | PLANNED-NEVER-BUILT |
| Delete 2 unconsumed compose PAL variants + dedupe registry keys | [CANON]§7.1 | Two managed compose variants nobody uses; registry has dup YAML keys. | DECISION-NEEDED (kill-list) |
| HTTP/SSE dual-transport retrofit to PAL | [FORGOT]§2.4/§3b#10 | Apply task-orchestrator's HTTP-singleton pattern to fix container-leak class. | PLANNED-NEVER-BUILT |

---

## 5. Serena (technical-context plane — deliberately outside Trinity)

Three surfaces: deployed = upstream oraios wrapper (:3006); local candidate = `services/serena/` (33 tools per [SERV2], 45 per [CANON] incl. 6 write tools); phantom `v2/mcp_server.py` path in the broken wrapper.

Local candidate tool groups ([SERV2]): Files (`read_file`,`list_dir`), Health (`get_workspace_status`), Tier-1 nav (`find_symbol`,`goto_definition`,`get_context`,`find_references`), Tier-2 ADHD (`analyze_complexity`,`filter_by_focus`,`suggest_next_step`,`get_reading_order`), Enhanced nav (`find_similar_code`,`predict_navigation_from_git`,`find_test_file`,`get_unified_complexity`), Tier-3 (`find_relationships`,`get_navigation_patterns`,`update_focus_mode`), **Feature-1 family** (below).

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Symbol nav / def / ref / project scoping (read-only default) | [CANON]§3.2; [SERV2] | LSP-backed code intelligence. Deployed = upstream wrapper. | SHIPPED (upstream) / BUILT-UNWIRED (local 33-tool candidate) |
| ADHD caps (≤10 results, 3-level depth, complexity bands) | [CANON]§3.2 | Bounded ADHD-friendly output. Implemented in local candidate only. | BUILT-UNWIRED |
| Edit lane behind separate policy + flag (6 write tools) | [CANON]§4, §7.1 | Write tools kept out of default profile per sanctioned read-only contract. | DECISION-NEEDED (violates contract if promoted) |
| **F001 Untracked-Work Detection** (`detect/track/snooze/ignore/get_config/update_config`) | [SVCAUD]§2; [SERV2] Feature-1; `docs/03-reference/f001-*` | Detect uncommitted work with no ConPort task → confidence-score → cross-session reminders (backoff, quiet hours, snooze 1h/4h/1d) → auto-track ≥0.85 → auto-close on commit (≥80% file overlap). Complete lifecycle, 974-line storage. **Unreachable at runtime** (wrapper builds only `wrapper.py`). | BUILT-UNWIRED (design 4/5, reachability 1/5) |
| Abandonment tracking (`get_abandoned_work`,`mark_abandoned`,`get_abandonment_stats`; 7-day = abandoned) | [SERV2]; [FORGOT]§2.5 | Guilt-free abandonment framing. | BUILT-UNWIRED |
| Branch organization suggestion (`suggest_branch_organization`) | [SERV2] | Suggest branch structure for untracked work. | BUILT-UNWIRED |
| Pattern stats (`get_pattern_stats`,`get_top_patterns`) | [SERV2]; [FORGOT]§2.5 | Navigation-pattern + ADHD-risk typing. | BUILT-UNWIRED |
| Metrics dashboard (`get_metrics_dashboard`,`get_metric_history`,`save_metrics_snapshot`; F1–F6 analytics) | [SERV2]; [FORGOT]§2.5 | Serena feature analytics. | BUILT-UNWIRED |
| Complexity banding (0–1 + 🟢🟡🟠🔴 + "tackle at peak focus") | [FORGOT]§2.5 (`adhd_features.py CodeComplexityAnalyzer`) | ADHD complexity signal. **1st of 3 competing complexity scorers.** | BUILT-UNWIRED (CRITICAL per source) |
| Focus Mode Manager (5 modes LIGHT→HYPERFOCUS, break reminders, switch tracking) | [FORGOT]§2.5 (`focus_manager.py`) | Focus-mode state machine. | BUILT-UNWIRED |
| Fatigue Detection Engine (8 indicators + 8 responses) | [FORGOT]§2.5 (`intelligence/fatigue_detection_engine.py`) | Detect fatigue → adaptive response. | BUILT-UNWIRED |
| Adaptive Learning Engine (per-user attention patterns, cross-session) | [FORGOT]§2.5 (`intelligence/adaptive_learning.py`) | Personalization foundation. | BUILT-UNWIRED (#1 in source TOP-3) |
| Personal Learning Profile (persists accommodation prefs) | [FORGOT]§2.5 (`learning_profile_manager.py`) | Persist per-user prefs. | BUILT-UNWIRED |
| Cognitive Load Orchestrator (real-time load → unified response) | [FORGOT]§2.5 (`intelligence/cognitive_load_orchestrator.py`) | Combine ADHD signals into one. | BUILT-UNWIRED |
| Context-Switching Optimizer; Progressive Disclosure Director (3-level, max-5); Git Prediction (`predict_navigation_from_git`) | [FORGOT]§2.5; [SERV2] | Interruption/resumption support; disclosure; next-files-from-git. | BUILT-UNWIRED |
| Multi-workspace pinned instances (`multi_workspace_wrapper.py`) | [SERV2] | Per-workspace pinned Serena instances. | BUILT-UNWIRED |
| Serena single-surface decision (ADR + archive/promote) | [CANON]§7.1; [PLAN]-E6; ADR-202 | Deployed=upstream becomes documented reality; archive the 45-tool candidate or promote via ADR+proof. | DECISION-NEEDED |
| F002 Multi-session support | `docs/03-reference/f002-multi-session-support*.md` | Multi-session Serena support (design series). | PLANNED-NEVER-BUILT (design) |

---

## 6. dope-context (Memory Trinity plane 3 — retrieval, read-only)

Live shipped surface: 18 tools.

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| AST-aware hybrid dense+sparse code+docs indexing (Voyage+Qdrant+BM25+rerank) | [CANON]§3.2, live | Hybrid retrieval pipeline. | SHIPPED |
| Search profiles; SHA256 sync; per-worktree collections | [CANON]§3.2 | Multi-profile search, incremental sync. | SHIPPED |
| Autonomous indexing (opt-in) | [CANON]§3.2; [FORGOT]§2.2 | Background index; opt-in triggers. | SHIPPED |
| Complexity scoring (`get_chunk_complexity`) | [CANON]§3.2, §7.1-3.3 | Per-chunk complexity. Docstring lies ("Tree-sitter" but ast); results don't carry per-hit complexity despite doctrine. **2nd of 3 competing scorers.** | PARTIAL |
| Lexical-only Phase-1 enforcement | [CANON]§3.2 | Required by repo rules, "never proven." | PLANNED-NEVER-BUILT |
| Fix fail-open healthcheck (`|| exit 0` → `|| exit 1`) | [CANON]§4; [SVCAUD]§5; [PLAN]-P0 | Healthcheck always passes. | PLANNED-NEVER-BUILT |
| Qdrant collection GC (keyed to `git worktree list`) | [CANON]§6.3; [PLAN]-F2 | GC orphan collections per deleted worktree. | PLANNED-NEVER-BUILT |
| Voyage cost guard | [CANON]§4; [PLAN]-F2 | Cap embedding API cost. | PLANNED-NEVER-BUILT |
| Delete `simple_server.py` mock (fabricates results) | [CANON]§4 | Mock fabricates plausible results. | ABANDONED (kill-list) |
| Chronicle→dope-context indexing (Trinity Rule 2, `ENABLE_DOPECONTEXT_INDEX`) | [CANON]§7.2; [PLAN]-B4 | Flag on after curated entries exist. | PLANNED-NEVER-BUILT (flagged off) |
| Derived `memory_{hash}` semantic projection (`index_memory`/`search_memory`) | [MCF]§3, TP-MCF-005 | New memory-semantic collection; blocked by Voyage-external privacy conflict + ADR. | PLANNED-NEVER-BUILT (see Z) |
| Complexity-scoring unification | [CANON]§7.1-3.3; [FORGOT]§2.6 | Unify Serena + dope-context + ADR-207 scorers or drop claim → **built as `complexity_coordinator` service** (see §17). | PARTIAL (coordinator built, unwired) |

---

## 7. gpt-researcher (research plane)

Live shipped surface (upstream clone, 5 tools).

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| deep_research / quick_search / write_report / sources / context | [CANON]§3.2, live | Autonomous web research + report gen; `/research:*` commands. | SHIPPED |
| ConPort `research_id` persistence | [CANON]§3.2 | Persist research via `/research:*`. | SHIPPED (design) |
| Unify contradictory healthcheck (curl vs pgrep) | [CANON]§4, §7.1 | Reconcile healthcheck. | PLANNED-NEVER-BUILT |
| Archive dead in-repo twin (`services/dopemux-gpt-researcher`) | [CANON]§7.1; [SVCAUD]§7; [PLAN]-D4 | Dead MCP twin; but hosts **live extraction backend** (`cli.py:4328`) that must relocate to `src/dopemux/extraction/` first. | DECISION-NEEDED |
| `summarize_research` (brief/bullets/detailed ADHD formatting) | [FORGOT]§2.3 | ADHD result formatting on live server. | PLANNED-NEVER-BUILT (dead-twin feature) |
| `code_examples` (framework+lang+concept scoped) | [FORGOT]§2.3 | Scoped code search. | PLANNED-NEVER-BUILT |
| `trend_analysis` (day/week/month/year) | [FORGOT]§2.3 | Timeframe-filtered research. | PLANNED-NEVER-BUILT |
| `quick_search` ADHD result-limiting | [FORGOT]§2.3 | Cap results. | PLANNED-NEVER-BUILT |
| `documentation_search` | [FORGOT]§2.3 | Redundant with Context7 + dope-context. | ABANDONED (intentionally dropped) |

---

## 8. exa (quick neural search)

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Quick neural search lane (4 tools, :3011) | [CANON]§3.2; [ADR223] | "Exa for quick lookups" doctrine. Built, healthy, **zero consumers**, catalog entry targeted wrong container (`mcp-litellm`). | **ABANDONED/RETIRED** — ADR-223 (2026-07-04). `WebSearch` is the fallback. **[P0 runtime note: container still Up (healthy) bound 0.0.0.0:3011]** |

---

## 9. desktop-commander

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Terminal/process control (doctrine) | [CANON]§3.2, §7.1 | Doctrine says terminal control; screenshot/window/focus/type tools in dead alt code. | SUPERSEDED — in-repo server is a **facade** (macOS `osascript` inside Linux container). Target: delete facade, run real upstream on host. **[P0: compose SSE :3012 answers with 4 GUI tools]** |
| Wire-or-retire decision | [ADR223] consequences | Last `decision-required` server after exa retired; default-off per [PLAN]. | DECISION-NEEDED |
| Token-safe response (file paths not base64: 12 vs 168K tokens) | [FORGOT]§2.4 | Lost discipline to re-enforce on rebuild. | PLANNED-NEVER-BUILT |

---

## 10. DCP — read-only facade + registry + lanes + model routing

**Facade 12-tool contract** [DCPTC]: `list_projects, get_project_capabilities, get_repo_state_snapshot, list_proof_bundles, fetch_proof_bundle` (local/git, packet 0004); `search_decisions, search_progress, search_chronicle, replay_chronicle_session` (ConPort+dope-memory, 0005); `search_code_docs, get_index_status, get_workflow_status_snapshot` (dope-context+task-orch, 0006).

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Loopback evidence projection to external LLMs (ChatGPT via tunnel) | [CANON]§3.2; [DCPTC] | Read-only facade w/ untrusted-by-default envelopes, denylist, redaction, authority labels. Structurally fail-closed; 537/539 tests. | SHIPPED (facade) / **absent from every registry/compose/.mcp.json** |
| Local/git tools (0004) | [DCPTC] 1a | list_projects, capabilities, repo snapshot, proof-bundle list/fetch (symlink-escape blocked, 256KB read cap). | SHIPPED |
| `search_decisions` (0005) | [DCPTC] 1b | ConPort decisions list. **`query` mode deferred** (backend `/api/search/{ws}` 500s on UUID serialization). | PARTIAL |
| `search_progress` (0005) | [DCPTC] 1b | Fail-closed unless `progress_readonly_safe` (auto-fork write hazard). | PARTIAL (BLOCKED by default) |
| `search_chronicle` / `replay_chronicle_session` (0005) | [DCPTC] 1b | dope-memory reads (POST, side-effect-free). | SHIPPED |
| `search_code_docs` / `get_index_status` (0006) | [DCPTC] 1c; [CANON]§4 G1 | dope-context reads. **Return BLOCKED in Phase 1** (facade REST-only; dope-context is MCP-JSON-RPC). 3 of 12 tools unwired. | PLANNED-NEVER-BUILT (G1) |
| `get_workflow_status_snapshot` (0006) | [DCPTC] 1c | task-orch queue/blockers/state (read-only). | SHIPPED |
| Close G1 + contract test (`exposed == TOOL_CONTRACT`) | [CANON]§7.1; [FLEET]-006 | Wire 3 tools + freshness gate. | PLANNED-NEVER-BUILT |
| Phase-2 dope-context MCP-JSON-RPC read bridge | [CANON]§7.1; [MCF]§3 | Transport bridge facade→JSON-RPC. | PLANNED-NEVER-BUILT |
| **Routing classification engine** (pure-function) | [DCPMR]-0002 | Classify task → routing lane (Opus=judgment/Sonnet=impl/Haiku=mechanical). | SHIPPED (engine) |
| Routing classifier reconciliation / status-precedence fix | [DCPMR]-0002R, -PRE-PROMPT6-0002 | Fix status precedence in classifier. | SHIPPED |
| Routing classifier provenance hardening | [DCPMR]-0006 | Harden provenance on classifier. | PLANNED |
| Trusted-input provenance contract | [DCPMR]-0007 | Contract for trusted inputs. | PLANNED |
| **Read-only DCP CLI projection** | [DCPMR]-0004 | `dopemux dcp` read-only CLI over the facade. | SHIPPED |
| **DCP Lane Engine MVP** (`decide_lane()`) | [DCPMR]-0005; [CANON]§7.1 | Compute execution lane. Built but **zero non-test consumers** ("latent security is not security"). Wire into dispatch or ADR to shelf. | BUILT-UNWIRED / DECISION-NEEDED |
| Lane engine fail-closed on forged unknowns + hard-forbidden passive actions | [DCPMR]-0005-POSTMERGE-FIX | Reject forged UNKNOWN; block passive actions. | SHIPPED |
| DCP charter v1 (11 systems mapped, `live_write=false`, red lane DCP-RED-MERGE-SEAM-0001, `LIVE_WRITE_READY` undefined-and-blocking) | [CANON]§3.1 | Execution-eligibility as unforgeable computed capability; provenance lowers trust. | SHIPPED (structurally) |
| PCP live-write gate | [CANON]§4 | Fail-closed; no default writer exists. | SHIPPED (fail-closed) |
| Denylist runtime middleware | [CANON]§4 | Currently data+tests+advisory hooks, not runtime middleware. | PLANNED-NEVER-BUILT |
| Kill dead neighbors (mcp-integration-bridge w/ secret-leaking debug endpoint, mcp-client, router) | [CANON]§7.1; [SVCAUD]§4 | Remove Dockerfiles so nothing dead is startable. | DECISION-NEEDED (kill-list) |

---

## 11. ADHD engine

Real engine = `services/adhd_engine/` (51 files, ~2,847 LOC). Routes exist server-side: `/log-intent, /save-context, /external-activity, /log-git-event, /state, /api/v1/state`.

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Attention/energy state assessment (`attention_monitor.py`) | [ADHDDD]§4; [SVCAUD]§3 | Track energy baseline + state transitions. | SHIPPED (core), honesty-fixed (UNAVAILABLE banding) |
| Engine **ignition** (default-start / `enabled_in_smoke`) | [SVCAUD]§3; [PLAN]-A2 | Flip smoke-on; fix event_bus init + health-check port (:3025). | PARTIAL → [PLAN] "ignition shipped this cycle" **[P0: NO CONTAINER on this host — refuted at runtime]** |
| PredictiveADHDEngine (IP-005, LSTM) | [ADHDDD]§6 | Predict hyperfocus/scatter/focus next window. | SHIPPED (engine); consumer PARTIAL |
| ConPort URL config fix (:3010→:3004) | [SVCAUD]§3; [PLAN]-P0 | Default pointed at dope-context's port. | PARTIAL |
| `native_hooks` PostToolUse → `/external-activity` ingress | [SVCAUD]§3; [PLAN]-C2 | First always-on real signal source. | PLANNED-NEVER-BUILT |
| **Interruption shield** (DND, suppression during hyperfocus) | [ADHDDD]§4b (root twin ~420 LOC); [PLAN]-C3 | Suppress non-critical notifications in deep-work windows. **Entirely unwired.** Canonical home = `services/adhd_engine/domains/interruption-shield/`. | BUILT-UNWIRED / DECISION-NEEDED |
| **Notifications** — adhd-notifier (break reminders, FCM, daily reporter) | [ADHDDD]§2a (1,272 LOC) | 25-min break reminders + daily summaries + push. Never registered/composed/hooked. | BUILT-UNWIRED → [PLAN] "notifier port shipped" |
| DesktopNotificationChannel (host macOS, self-disable in-container) | [PLAN]-C4 | Desktop notifications for hyperfocus/overwhelm. | PARTIAL (proof pending) |
| **Recap** — ADHD-aware recap consumer | [PLAN]-C5 | Fewer cards when scattered in TUI/CLI recap. | PLANNED-NEVER-BUILT |
| Context Preservation (`context_preserver.py`) | [FORGOT]§2.6 | Live backend; not wired to PM display. | BUILT-UNWIRED |
| Overwhelm Detection/Suppression (`event_coordinator.py`) | [FORGOT]§2.6 | Telemetry exists; PM exposes no snapshot. | BUILT-UNWIRED |
| Suppression telemetry | `docs/systems/suppression-telemetry/` | Notification-suppression metrics. | (design/systems doc) |
| Automatic timers / recurring auto-save / forced hyperfocus breaks | [ADHDMOD]; [CANON]§3.3; [ADHD531] | **Explicitly specification-only.** | PLANNED-NEVER-BUILT (aspirational, marked as such) |
| Decision-reduction; 7±2 cap; task-ordering by attention state; progress viz | [ADHDMOD] | Claude-facing behavioral rules. | SHIPPED (behavioral guidance, not runtime enforcement) |
| Fabricated-telemetry honesty fixes (C2/H4/C3) | [SVCAUD]§3; [ADHD531] | UNAVAILABLE banding; demo labels; dashboard builds. | SHIPPED |
| ML-predictions LSTM standalone (1,282 LOC) | [ADHDDD]§6 | Duplicate of PredictiveADHDEngine. | ABANDONED (delete-safe) |
| ML-risk-assessment (1,159 LOC) | [SVCAUD]§7 | Risk ML; zero imports. | ABANDONED (dead) |
| Dead triangle (workflow_manager/adhd_orchestrator/main_orchestrator/rte_adapter) | [ADHDDD]§4 | RTE→ConPort decomposition + orchestration; zero callers. | ABANDONED (delete-safe) |
| RTE → ADHD energy → ConPort task decomposition | [ADHDDD]§4 (`rte_adapter.py`) | Read DOCTOR_FULL artifacts → bite-sized tasks. | ABANDONED (broken) |

---

## 12. Event bus / promotion / chronicle spine + Memory Context Fabric (MCF)

MCF public surface [MCF-interfaces]: `context.recall(query,k,modalities,workspace_id)`, `context.recap(hours_back,k,workspace_id)` → `ContextBundle`.

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| Named-stream event contract (`activity.events.v1`) | [SVCAUD]§4, §9; [CANON]§7.2 | ConPort/bridge publish → chronicle consumer. Stream split broke the spine. | PARTIAL |
| Heartbeat rate-limiting | [CANON]§7.2; [PLAN]-A4 | Drop `session-active` spam (24,539 rows). | PLANNED-NEVER-BUILT |
| Context Fabric orchestration layer (capture→redact→dedup→route→promote→retrieve→inject) | [MCF-design] | Coordinating layer over Trinity; owns no truth. Approach B. | PLANNED-NEVER-BUILT (design, CONDITIONAL-GO) |
| TP-MCF-001 repo-truth authority map | [MCF] | Authority map (no runtime change). | PLANNED (GO) |
| TP-MCF-002 transcript ingest → raw ledger | [MCF] | Ingest conversation transcripts; quarantine; redact. | PLANNED-NEVER-BUILT (CONDITIONAL-GO) |
| TP-MCF-003 deterministic promotion (transcript→chronicle) | [MCF] | Promote safe deterministic classes. | PLANNED-NEVER-BUILT (NO-GO until schema) |
| TP-MCF-004 SessionStart recap injection | [MCF] | Extend native_hooks SessionStart with bounded Top-3 recap. | PLANNED-NEVER-BUILT (CONDITIONAL-GO) |
| TP-MCF-005 semantic memory projection | [MCF] | dope-context `memory_{hash}`; blocked by external-embedding privacy + ADR. | PLANNED-NEVER-BUILT (NO-GO, see Z) |
| TP-MCF-006 ConPort graph on active runtime | [MCF] | Verify `graph.neighbors` MCP or ship relationship-query only. | PLANNED-NEVER-BUILT (CONDITIONAL-GO) |
| TP-MCF-007+ Fabric orchestrator / summarizer / proactive injection | [MCF]§6 | recall/recap service; LLM distillation; proactive surfacing. | PLANNED-NEVER-BUILT (NO-GO) |
| Transcript quarantine (non-queryable safety artifact) | [MCF]§2 | `.dopemux/quarantine/` or non-queryable table. | PLANNED-NEVER-BUILT |
| Progressive token truncation (shared MCP utility, 9K budget) | [FORGOT]§2.4/§3b#8 | Fleet-wide bulk-query truncation; lost in migration. | PLANNED-NEVER-BUILT |
| MCP boundary-enforcement truncation (single `call_tool()` point) | [FORGOT]§2.4/§3b#9 | One interception point fleet-wide. | PLANNED-NEVER-BUILT |
| mcp-capture (`capture/emit`, lane-aware, SHA256 dedup, audit trail) | [CANON]§2; [FORGOT]§2.2 | Chronicle capture/emit tool. Finished + tested, registered nowhere. | BUILT-UNWIRED |
| copilot transcript ingester | [SVCAUD]§4 | Ingest Copilot transcripts. Live library, nothing schedules it. | BUILT-UNWIRED |

---

## 13. Hooks (H-series + orchestrator hooks) — ⚠ H-numbering collides across docs

All lifecycle events route through `src/dopemux/claude/native_hooks.py`.

| Hook | Source | Planned behavior | Status |
|---|---|---|---|
| **H1** DCP surface guard (PreToolUse) | [DCPHOOK]§6 | Hard-block red-lane edits + contract-surface advisory. | (per [DCPHOOK]: DESIGN_READY; per current code: wired in native_hooks) |
| **H2** facade denylist nudge (PostToolUse) | [DCPHOOK]§7 | Warn on denied-route token in facade edits. | (as above) |
| **H3** MCP health preflight (SessionStart) | [DCPHOOK]§8 | Probe servers + leaked-container count. | (as above) |
| **H3′** (different) `ensure --fast` at SessionStart | [CANON]§6.1, §7.2 | Call `dopemux mcp ensure --fast` — numbering collision with H3. | PLANNED-NEVER-BUILT |
| **H4** proof-tracking guard (PostToolUse) | [DCPHOOK]§9 | Nudge on gitignored TRACK-tier proof writes. | (wired) |
| **H5** untracked-work SessionStart hook | [PLAN] | F001-lite probe at session start. | doc-asserted SHIPPED |
| Stop-time context save; energy-warning; progress/edit tracking | [ADHDMOD] | Hook scripts "dormant unless invoked by dispatcher." | PARTIAL (orphaned scripts per integration-surface map) |
| Orchestrator enforcement hooks (actor auth, complete-gate) | [DCPHOOK]§0; [SVCAUD]§6 | Server-side proof-bundle complete-gate; actor auth dormant behind `actor_authentication.enabled`. | PARTIAL |
| 5 DCP skills (`/proof:bundle`, `/mcp:doctor`, `/dcp:doctor`, `/dcp:denylist-check`, `/tp:validate`) | [DCPHOOK]§1-5 | Wrap existing engines. | partly SHIPPED (present in session skill list) |

---

## 14. Dashboards

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| TUI HUD (`src/dopemux/tui/`, Textual, 8 orchestrator-data panels) | [SVCAUD]§7; [ADHDDD] | Real operator dashboard. | SHIPPED (live, canonical) |
| React ui-dashboard (`ui-dashboard/`, 2,306 modules) | [SVCAUD]§3 | Optional web view of ADHD state. | SHIPPED (builds clean; dual npm/pnpm lockfiles) |
| adhd-dashboard (`services/adhd-dashboard/backend.py`) | [ADHDDD]§3; [SVCAUD]§3; [PLAN]-D1 | FastAPI `/state` mirror of TUI. Orphan (not in compose), reads wrong stream. | BUILT-UNWIRED / DECISION-NEEDED — **now SVCFIN-owned (DMX-DASH-WIRE-001: keep+wire decision)** |
| conport_kg_ui (decision-genealogy terminal UI) | `services/conport_kg_ui/README.md` | ADHD-optimized TUI for decision genealogy. | BUILT-UNWIRED (depends on dead conport_kg) |
| PM cockpit Textual shell | `task-packets/DMX-COCKPIT-PM-TEXTUAL-001.json`; `docs/05-audit-reports/cockpit-*-2026-04-24.md` | PM cockpit + Grand Orchestrator cockpit (`TP-PRMS-052`). | PLANNED (packet series) |
| Cockpit archived ADHD-lifestyle intent | `DMX-COCKPIT-ARCHIVE-INTENT-001.json` | Extract archived ADHD lifestyle features. | PLANNED (design pack) |
| monitoring-dashboard (1,886 LOC) | [SVCAUD]§7 | 0.0.0.0:8098 unauth + startup-fatal import. | ABANDONED (dead, security note) |
| Top-level `dashboard/` (2,011 LOC) | [SVCAUD]§7 | Aspirational drop 2026-04-05. | ABANDONED (dead) |

---

## 15. SuperClaude command layer / `/dx:` commands

| Feature | Source | Planned behavior | Status |
|---|---|---|---|
| 18 `/dx:*` commands | [CANON]§3.3; session skill list | Orchestrator work-item command surface. | SHIPPED (present as skills) |
| `/dx:implement` focus timers, save checkpoints, break prompts, forced pauses | [ADHDMOD] | ADHD automation. | PLANNED-NEVER-BUILT ("not proven wired") |
| `/dx:prd-parse` (PRD→15–90min chunks + complexity + energy tags + review gate) | [ADHDMOD]; [FORGOT]§2.3 | Chunk PRDs with ADHD metadata. | PARTIAL (unscored flat lists today) |
| `/dx:load`, `/dx:save`, `/dx:analyze`, `/dx:review` | [ADHDMOD] | Context restore/save; PAL analysis → ConPort. | SHIPPED (behavioral) |
| SuperClaude `/sc:*` family | session skill list; `.claude/modules/superclaude-*.md` | Workflow layer. | SHIPPED (skill layer) |
| Skill-layer mirror receipts (`/decision`,`/caveat`,`/followup` → dope-memory) | [PLAN]-B3 | Append chronicle mirror receipt. | PLANNED-NEVER-BUILT |

---

## 16. Peripheral / live-but-undocumented MCP servers

| Server | Source | Behavior | Status |
|---|---|---|---|
| **context7** | Session tool list; only in `docs/planes/pm/_evidence/*` | Library/docs lookup MCP; referenced in CLAUDE.md doctrine. | SHIPPED-but-undocumented (Y) |
| **mcp-registry** (`list_connectors`, `search_mcp_registry`, `suggest_connectors`) | Session tool list | Connector discovery/registry. No doc/service match anywhere. | SHIPPED-but-undocumented (Y) |
| **scheduled-tasks** (`create/list/update/delete_scheduled_task`) | Session tool list | Scheduling MCP. Could answer the "no scheduler" gap for adhd-notifier daily reporter + copilot ingester. | SHIPPED-but-undocumented (Y) |

---

## 17. Supporting services (not classic MCP servers)

| Service | Source | Planned behavior | Status |
|---|---|---|---|
| dopecon-bridge (:3016) | [SVCAUD]§5; `adr-dopecon-bridge-narrowing...` | Transport/proxy only; only multi-consumer event seam → candidate canonical event plane. | SHIPPED (live, healthy) |
| **complexity_coordinator** | `services/complexity_coordinator/README.md`; [CANON]§7.1-3.3 | Unified complexity: AST (dope-context) + LSP/semantic (Serena) + usage + ADHD multiplier → `unified_score`. **The built answer to the 3-competing-scorers problem.** | BUILT-UNWIRED (not in compose/registry) |
| **claude_brain** | `services/claude_brain/README.md` | Prompt optimization + brain integration w/ ADHD accommodations. | BUILT-UNWIRED (undocumented in audits — Y) |
| **webhook_receiver** (:8790) | `services/webhook_receiver/README.md`; compose.yml | OpenAI-first webhook sidecar + provider-agnostic event ledger + poller. | SHIPPED (in compose) but undocumented in fleet audits (Y) |
| **dddpg** | `services/dddpg/DEEP_ANALYSIS_CURRENT_STATE.md` (2025-10-29) | KG bridge/storage/queries + ConPort KG integration. Ancient. | ABANDONED (stale, undocumented — Y) |
| voice-commands | [SVCAUD]§7; [PLAN]-D3 | Voice API + task decomposition. Zero imports. Distinct from live `src/dopemux/voice/`. | ABANDONED (dead; SVCFIN-owned deletion) |
| services/intelligence | [SVCAUD]§7 | Empty. | ABANDONED |
| monitoring / slack-integration | [SVCAUD]§7 | Dead. | ABANDONED |
| mcp-integration-bridge — KG endpoints, workflow templates, progress dashboard, ADHD context middleware | [FORGOT]§2.3 | Rich ADHD/workflow backends; bridge on kill-list (secret-leaking debug endpoint) — resurrect via clean rewrite only. | BUILT-UNWIRED / DECISION-NEEDED |
| RTE (repo-truth-extractor) | [CANON]§9 | Audit-only truth extraction. | SHIPPED (audit tooling) |
| claude_brain / dope-query / session-manager / session-intelligence twins / workspace-watcher / activity-capture | [ADHDDD]§4-10 | Stranded/legacy. | BUILT-UNWIRED or ABANDONED |

---

## (Z) Pure vaporware — planned in docs, in NO working code

| Feature | Server/service | Source | Note |
|---|---|---|---|
| ConPort vector semantic search (Milvus + Voyage/OpenAI) | ConPort | [FORGOT]§2.1 | Milvus never deployed; boundary-conflicts with Trinity. |
| ConPort semantic node upsert (`mem.upsert`) | ConPort | [FORGOT]§2.1 | Same. |
| ConPort decision impact graph | ConPort | [FORGOT]§2.1 | Data model only. |
| Zep conversational memory | ConPort | [FORGOT]§2.1 | Config-only stub. |
| Sprint Auto-Planning end-to-end | task-orchestrator | [FORGOT]§2.6 | ConPort has no sprint API — genuinely unbuilt. |
| Decision traceability (task→ConPort links) | TO / ConPort | [FORGOT]§2.6 | P0 governance gap, unbuilt. |
| dope-context `memory_{hash}` projection | dope-context | [MCF] TP-MCF-005 | Blocked NO-GO (privacy). |
| `graph.neighbors` MCP parity | ConPort | [MCF]§0, TP-MCF-006 | Genealogy unbuilt. |
| Context Fabric `context.recall`/`recap` + orchestrator + proactive injection | MCF | [MCF-interfaces]§1 | Entire MCF public surface design-only. |
| Transcript-file ingest + quarantine | MCF/dope-memory | [MCF]§0 | "MISSING" in runtime truth table. |
| Progressive token truncation + boundary truncation | fleet-wide | [FORGOT]§2.4 | Lost in migration. |
| Session context re-injection at SessionStart | dope-memory | [FORGOT]§2.2 | No continuity mechanism today. |
| Event_id idempotency dedup | dope-memory | [FORGOT]§2.2 | Dup entries possible. |
| ADHD automatic timers / auto-save / forced breaks | ADHD engine | [ADHDMOD] | Spec-only. |
| `/dx:implement` focus timers & break prompts | dx layer | [ADHDMOD] | "not proven wired." |
| gptr ADHD tools (summarize_research etc.) | gpt-researcher | [FORGOT]§2.3 | Only in dead twin. |
| Product-context; relationship writes; retrospective; reminders; genealogy | ConPort | [COPT]-201/202/301/302/303 | Packet-specified, unbuilt. |
| ~~DCP hooks H1–H4~~ | hooks | [DCPHOOK] | Doc says DESIGN_READY; **integration-surface map confirms these now wired in native_hooks — treat as SHIPPED, register accordingly** |

## (Y) Undocumented — exists in code/config but in NO fleet docs

| Feature | Where | Note |
|---|---|---|
| **context7** MCP | live surface + CLAUDE.md doctrine | Absent from catalog + fleet register. |
| **mcp-registry** MCP | live surface | No doc/service match. |
| **scheduled-tasks** MCP | live surface | Undocumented scheduling capability. |
| **webhook_receiver** (:8790) | compose + services/ | Never mentioned in fleet/service audits. |
| **claude_brain** | services/ | Not covered by any audit. |
| **complexity_coordinator** | services/ | The built 3-scorer unifier; audits flag the scorers but never mention it. |
| **dddpg** | services/ | ConPort-KG-adjacent, ancient. |
| ConPort dark admin tools (`fork_instance`, `promote`, `promote_all`) | live surface | Live but under-documented. |
| conport `search_content`, `get_active_work`, `workspace_summary`, `get_recent_activity` | live surface | Recently-added, thinly documented. |
| dope-context `get_search_metrics`/`clear_search_metrics`/`configure_decision_auto_indexing`/`get_chunk_complexity` | live surface | Not in doc-sourced register. |
| Live extraction backend inside `services/dopemux-gpt-researcher` | `cli.py:4328` | Dir documented as dead twin but hosts live backend. |
| dopecon-bridge secret-leaking `/ddg/decisions` proxy + integration-bridge debug endpoint | [CANON]§2; [DCPTC]§2 | Known but under-documented; still startable in-tree. |

---

### Cross-cutting notes
- **Dominant pattern = BUILT-UNWIRED**, not unbuilt ([FORGOT], [ADHDDD], [SVCAUD] converge).
- **Three (arguably four) competing complexity scorers** + the unwired `complexity_coordinator` unifier.
- **Shadow-twin syndrome**: ConPort, Serena, PAL, task-orchestrator, gpt-researcher.
- **Status freshness**: "doc-asserted SHIPPED (newer branch)" items come from the 07-07 completion plan describing PR #1009 work; all runtime claims now superseded by `claudedocs/mcp-fleet-runtime-verification-2026-07-16.md`.
