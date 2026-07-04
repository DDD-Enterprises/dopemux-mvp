# Dopemux MCP Fleet — Forgotten Features / Dormant Capabilities Addendum

**Date**: 2026-07-04
**Parent doc**: `claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md` (fleet audit + target design)
**Scope**: Archaeology of archive/ + quarantine/ + dead-code surfaces the parent audit's 8 wiring/config agents did not deep-dive — abandoned services, deprecated packages, and design docs describing patterns that were built once and then lost.
**Method**: 6 read-only archaeology agents mined `src/conport/memory_server.py` + `services/conport_kg/` (quarantined 2026-06-22), dead in-repo MCP servers (gptr/leantime-bridge/mcp-capture/mcp-integration-bridge), a Claude-Mem/Mem0 design-review corpus, archived MCP doc sets (token-limit fixes, HTTP/SSE transport notes), `services/serena/` (45+ modules), and the deprecated PM/TaskMaster stack in `services/task-orchestrator` (Python) + `services/adhd_engine/`. Findings are written to three scratchpad files (paths below) and synthesized here. **Docker was down during the parent audit and remains unverified here — every dormant-code claim in this document is a static-code read, not a runtime observation.**
**Source scratchpads**:
- `1-conport-memory.md` (ConPort/conport_kg quarantine)
- `2-deadcode-mem-archivedocs.md` (dead MCP servers, Claude-Mem/Mem0 DR, archived doc patterns)
- `3-serena-pm.md` (Serena dormant modules, PM/TaskMaster deprecated stack)

---

## 1. Executive summary

The dominant finding across all three archaeology passes is the same one the parent audit already flagged for the live fleet, extended into the archive: **most "missing" MCP capability is not un-built, it's BUILT-BUT-DISCONNECTED.** Three large, functioning subsystems sit dormant behind the live surfaces — `services/serena/`'s 45+ ADHD modules (complexity banding, fatigue detection, adaptive learning), `services/adhd_engine/` + the Python `task-orchestrator`'s predictive-risk and complexity-scoring ML, and `conport_kg`'s AGE graph-traversal and event-orchestration code — all fully written, none wired to a live MCP tool. This is a second, independent line of evidence for the 2026-05-31 ADHD audit's central verdict that the ADHD intelligence layer is largely aspirational at runtime: it isn't aspirational because nobody built it, it's aspirational because what was built was never connected. A second, smaller category is **patterns lost in migration** — progressive token truncation, MCP-boundary response truncation, HTTP/SSE dual-transport, and a health/registry contract that all existed in earlier doc-described implementations and were dropped (or partially reinvented) when servers were rewritten or replaced. A third category is genuinely **not built anywhere** — vector semantic search over ConPort (Milvus/Voyage), graph-based decision genealogy, and ML-driven sprint auto-planning are real gaps, not disconnections. This document classifies every distinct feature the six agents found into WIRE-EXISTING (built, just needs a connection — the highest-ROI bucket), RESURRECT (designed or drafted, not built), INTENTIONALLY-DROPPED (leave it, with the reason), SUPERSEDED (already covered by the parent audit's roadmap or the new fleet catalog), or DECISION-NEEDED (genuine open question, usually a governance-boundary conflict). The single sharpest boundary conflict found: ConPort's abandoned `mem.search`/`mem.upsert` vector-semantic-search design directly contradicts the Memory Trinity law that assigns semantic retrieval to dope-context, not ConPort — this is flagged DECISION-NEEDED, not a clean resurrect, however tempting the "this is the missing `semantic_search_conport`" framing in the source file is.

---

## 2. Classified feature register

Legend — **Verdict**: WIRE-EXISTING (built, disconnected, connect it) · RESURRECT (designed/drafted, not built, worth building) · INTENTIONALLY-DROPPED (leave as-is, reason given) · SUPERSEDED (already covered elsewhere, cite where) · DECISION-NEEDED (open question, often a boundary conflict). **Confidence**: VERIFIED (agent read the code directly) vs INFERRED (agent judgment/estimate, not confirmed by direct read of a working path). All rows below are code-existence claims only — "exists" is not "works"; nothing here was runtime-tested (Docker down).

### 2.1 Plane: ConPort (conport_kg quarantine)

| Feature | Source | Current status | Verdict | Effort | Confidence |
|---|---|---|---|---|---|
| Vector semantic search (`mem.search`, Milvus + Voyage/OpenAI embeddings) | `memory_server.py:905-930` | Milvus never deployed; NO runtime | **DECISION-NEEDED** — boundary conflict: Trinity law assigns semantic retrieval to dope-context (read-only plane), not ConPort. Building this in ConPort would create a second semantic-search authority. Parent audit §3.2 lists "(aspirational) semantic search" under ConPort's own doc-sourced capability register, so the docs themselves conflict with the Trinity boundary — needs an explicit ADR call, not a silent resurrect | M | VERIFIED (code) / INFERRED (boundary call) |
| Semantic node upsert (`mem.upsert`, embeddings → Milvus+PG) | `memory_server.py:871-903` | NO runtime | **DECISION-NEEDED** — same boundary conflict as above; upsert-with-embeddings belongs to whichever plane wins the semantic-search decision | M | VERIFIED |
| Graph link creation (`graph.link`: affects/depends_on/implements/discussed_in/produced_by/belongs_to_thread) | `memory_server.py:931-956` | PARTIAL — AGE exists, only `link_conport_items` exposed live | **WIRE-EXISTING** — richer relationship-type vocabulary already modeled, just needs the MCP tool surface widened | S | VERIFIED |
| Graph neighbor traversal (`graph.neighbors`, recursive by rel-type + depth) | `memory_server.py:957-976` | PARTIAL — AGE Cypher exists, NO MCP tool | **WIRE-EXISTING** — source file's own TOP-3 calls this "just expose `conport_get_neighbors`/`conport_find_by_relationship_type`, low cost, high value" | S | VERIFIED |
| Progressive disclosure models (Tier1/2/3: DecisionCard/Summary/FullContext, cognitive-load scoring) | `conport_kg/queries/models.py:14-100` | NO runtime | **RESURRECT** — ADHD UX value, but needs re-derivation as verbose flags on the *live* SSE tool set (not the quarantined server) | M | VERIFIED |
| ADHD neighborhood exploration (1-hop→2-hop progressive, max-10/hop) | `conport_kg/queries/exploration.py:50-100` | NO runtime — AGE written, never wired | **RESURRECT** — depends on graph traversal (above) landing first | M | VERIFIED |
| Event-driven KG orchestration (auto triggers on decision.logged/task.started/file.opened/sprint.planning + Redis precache) | `conport_kg/orchestrator.py:44-180` | NO runtime — handlers complete, explicit `"TODO: publish to Integration Bridge event bus"` in source | **RESURRECT** — overlaps directly with parent audit §7.2 memory-spine fix (event emission at `decision.logged`); should be designed as ONE mechanism, not two competing event paths | L | VERIFIED |
| FTS by tag (3-result ADHD limit) | `conport_kg/queries/overview.py:80+` | NO runtime — replaced by `get_decisions(limit)` | **SUPERSEDED** — live `get_decisions` covers the use case; the ADHD-specific 3-result cap is a UX nicety, not a capability gap | S | VERIFIED |
| Genealogy chain traversal (BUILDS_UPON ancestry, generation tracking) | `conport_kg/queries/deep_context.py:90+` | NO runtime — Cypher drafted, no tool | **RESURRECT** — decision-lineage visibility; depends on graph traversal landing | M | VERIFIED |
| Relationship-type filtering (`find_by_relationship_type`, directional) | `exploration.py:110+` | NO runtime — internal only | **WIRE-EXISTING** — folds into the graph-traversal tool-widening above; no separate build | S | VERIFIED |
| Embedding fallback chain (Voyage→OpenAI→dummy) | `memory_server.py:485-520` | NO runtime | **SUPERSEDED-by-decision-above** — only relevant if semantic search is resurrected in ConPort; otherwise moot | — | VERIFIED |
| Zep conversational memory | `memory_server.py:113` | Config-only, never implemented | **INTENTIONALLY-DROPPED** — spec-only stub, no design behind it, no doc requiring it; not worth resurrecting | — | VERIFIED |
| Decision impact graph (centrality/influence scoring) | `models.py:95+` | Data model only | **RESURRECT-if-wanted** — no consumer identified; low priority, depends on graph traversal | L | VERIFIED |
| Direct PG AGE client (conn pool, agtype parsing, <50ms target) | `conport_kg/age_client.py` | PARTIAL — Tier-0 migrations never applied (per 2026-06-16 ConPort-optimal analysis) | **DECISION-NEEDED** — the 2026-06-16 memory entry on ConPort-optimal-rebuild found the live DB has only decisions+entity_relationships, no AGE-backed graph tables; resurrecting this client requires the Tier-0 migration work first, which is a separate, already-scoped initiative | L | INFERRED (cross-referenced against prior memory, not re-verified live) |

### 2.2 Plane: dope-memory / Memory Trinity (Claude-Mem/Mem0 design review + dead MCP servers)

| Feature | Source | Current status | Verdict | Effort | Confidence |
|---|---|---|---|---|---|
| Hook→Queue→Dedup→Store: event_id idempotency gate | Claude-Mem DR pattern, agent aa29c0 | dope-memory's `EventBusConsumer` has NO event_id dedup → duplicate entries possible on retry | **RESURRECT** — proven pattern from an external reference system, applied to dopemux's own event consumer; HIGH impact, low cost per source | S | VERIFIED (gap) / INFERRED (fix shape, pattern-reference only) |
| Session context re-injection at SessionStart | Claude-Mem DR pattern | Trinity has NO continuity mechanism today — manual `/mem:recap` only | **RESURRECT** — HIGH impact; direct complement to parent audit §7.2's memory-spine fix (once chronicle has content, auto-inject last recap at session start) | M | INFERRED (pattern-reference) |
| Pre-storage redaction pipeline (secret/PII masking before chronicle.append) | Claude-Mem DR pattern | Not present | **RESURRECT** — MEDIUM priority per source but explicitly blocks production use of the chronicle; should ride along with parent audit Phase 2 (memory spine) | M | INFERRED |
| Entity/user/project scoping | Claude-Mem DR pattern | Not present | DEFER (source's own call) — schema change, no immediate driver | — | INFERRED |
| Memory decay/TTL | Claude-Mem DR pattern | Not present | DEFER (source's own call, LOW priority) | — | INFERRED |
| Import/export chronicle | Claude-Mem DR pattern | Not present | DEFER (LOW) | — | INFERRED |
| dope-memory `/mcp` JSON-RPC parity (only `/tools/*` today) | Claude-Mem DR pattern | Partial surface | **RESURRECT** — MEDIUM; parity gap, not a new capability | M | VERIFIED (gap exists) |
| `replay_from_event_id` determinism | Claude-Mem DR pattern | Not present | DEFER (source's own call) | — | INFERRED |
| Correction-via-supersession | Claude-Mem DR pattern | **Already done** — dope-memory's `memory_correct` implements this | **SUPERSEDED** — no action; source file explicitly notes this is already-shipped | — | VERIFIED |
| Autonomous index (chronicle → search index, opt-in trigger) | Claude-Mem DR pattern | **Already done** — dope-context autonomous indexing covers this | **SUPERSEDED** — no action | — | VERIFIED |
| Chronicle capture/emit (lane-aware, SHA256 dedup, audit trail) | `mcp-capture` service, unregistered MCP | Finished + tested, registered nowhere | **WIRE-EXISTING** — parent audit §2 already lists `mcp-capture` as "nobody" consumer and kill-list candidate for *dead* servers, but this specific capability (audit-trail capture) is functional code, not dead weight; register it rather than archive it, OR fold its logic directly into the `capture_client.py` path parent audit §7.2 already wires | S | VERIFIED |

### 2.3 Plane: cross-cutting / dead in-repo MCP servers (GPT-Researcher, integration bridge, desktop-commander)

| Feature | Source | Current status | Verdict | Effort | Confidence |
|---|---|---|---|---|---|
| gptr `summarize_research` (brief/bullets/detailed ADHD formatting) | dead in-repo gptr server | Live gptr-mcp (upstream) lacks this | **RESURRECT** — real ADHD UX gap on an otherwise-working server | S | VERIFIED |
| gptr `code_examples` (framework+lang+concept scoped) | dead in-repo gptr server | Live gptr/Exa lack scoping | RESURRECT-maybe (source's own qualifier) | M | VERIFIED |
| gptr `trend_analysis` (day/week/month/year timeframe) | dead in-repo gptr server | Live gptr/Exa lack timeframe filter | RESURRECT-maybe | M | VERIFIED |
| gptr `quick_search` ADHD result-limiting | dead in-repo gptr server | Not in live server | RESURRECT-maybe, small | S | VERIFIED |
| gptr `documentation_search` | dead in-repo gptr server | Not in live server | **INTENTIONALLY-DROPPED** — redundant with Context7 + dope-context per source's own verdict | — | VERIFIED |
| KG endpoints (Leantime+ConPort sync, task-dep graph, decision graph) | `mcp-integration-bridge:237` | Missing; Phase-10 TBD | **RESURRECT** — source calls this "critical infra"; but note `mcp-integration-bridge` itself is on the parent audit's kill list (secret-leaking debug endpoint if revived) — any resurrection must happen in a clean rewrite, not by reviving the bridge wholesale | L | VERIFIED (gap) / INFERRED (must-rewrite-not-revive judgment) |
| Workflow templates as MCP tools (feature-dev/bug-fix/setup w/ auto-deps + celebration/momentum) | `mcp-integration-bridge:975-1179` | Backend exists, not surfaced | **RESURRECT** — ADHD value; same caveat as above, don't revive the bridge container itself | M | VERIFIED |
| Project progress dashboard (progress bar, next-focus, streak, motivation) | `mcp-integration-bridge:1564` | Backend exists, not surfaced | **RESURRECT** — ADHD UX; same bridge caveat | M | VERIFIED |
| ConPort ADHD context middleware (request-scoped hydration, delta tracking, Redis fallback, circuit breaker) | `mcp-integration-bridge:338-519` | Exists, not surfaced | **RESURRECT** — session-continuity value; overlaps with parent audit's session re-injection need (§2.2 above) | M | VERIFIED |
| PRD→tasks (disabled by design) | `mcp-integration-bridge` | Disabled | **INTENTIONALLY-DROPPED** — source explicitly says "disabled by design — correct." `/dx:prd-parse` is the sanctioned path | — | VERIFIED |
| Leantime bidirectional write-sync | `mcp-integration-bridge` | Gated | INTENTIONALLY-DROPPED-for-now — gated by design, PM authority-boundary concern; leave gated | — | VERIFIED |
| desktop-commander screenshot/window/focus/type tools | dead alternate desktop-commander | Core tools present in dead code | **SUPERSEDED** — parent audit already covers desktop-commander as a facade problem (macOS `osascript` inside Linux container, every call fails); §7.1 target-state decision is "delete the container facade; run actual upstream DesktopCommanderMCP on the host" — this dormant code doesn't change that call | — | VERIFIED |

### 2.4 Plane: cross-cutting / lost architectural patterns (archived MCP docs)

| Feature | Source | Current status | Verdict | Effort | Confidence |
|---|---|---|---|---|---|
| Progressive token truncation (item-by-item, stop at 9K budget) | `CONPORT_TOKEN_LIMIT_FIX` (archived doc) | Lost in migration; Zen-validated as the only viable bulk-query solution at the time | **RESURRECT** — CRITICAL/architectural per source; should become a **shared MCP utility** used fleet-wide before any bulk-query endpoint is re-enabled, not a per-server reimplementation | M | VERIFIED (doc) / INFERRED (current absence, not re-checked against live ConPort) |
| MCP boundary enforcement (truncate at `call_tool()` TextContent boundary, tool-agnostic single point) | `LEANTIME_TOKEN_LIMIT_FIX` (archived doc) | Standardization lost; was per-endpoint, scattered | **RESURRECT** — should be standardized fleet-wide as one interception point rather than scattered per-endpoint truncation; natural fit as part of the parent audit's Phase 1 catalog/codegen work | M | VERIFIED (doc) |
| HTTP/SSE dual-transport | `HTTP_SERVER_README` (archived doc) | Only Leantime had it originally; **task-orchestrator's singleton launcher already re-derived HTTP-singleton transport independently** (parent audit §2, "best-engineered lifecycle path in the fleet") | **SUPERSEDED** (partially) — task-orchestrator's HTTP singleton is the pattern's living proof point; the *remaining* gap is retrofitting the same pattern to the other stdio-per-client servers (PAL specifically) to solve the same container-leak class of bug the parent audit documents for `pal-mcp-server` | S–M (per additional server) | VERIFIED |
| Token-safe response (file paths not base64: 12 vs 168K tokens) | `DESKTOP_COMMANDER_VALIDATION` (archived doc) | Lost pattern | **RESURRECT** — cheap, high-value discipline; enforce as a lint/convention when desktop-commander is rebuilt (parent audit §7.1 already calls for rebuilding it properly) | S | VERIFIED |
| Health endpoint contract + server registry/metadata (purpose/port/health/required/order) | Archived doc set | Partially reinvented | **SUPERSEDED (partially)** — the parent audit's Phase 1 "one catalog, generated everything" (§6.1, §7 Phase 1) already targets this exact gap; this archaeology confirms the *pattern already existed once* and was lost — reinforces that Phase 1 is not gold-plating, it's recovering a known-good design | — | VERIFIED (doc) / cites parent audit §6.1 |
| uvx native deploy (97% faster startup, 75% less memory) | Archived doc | Not applied | RESURRECT-if-wanted — apply to pure-Python servers (dope-memory, dope-context, mcp-capture if revived); nice-to-have, not urgent | S (per server) | VERIFIED (doc claim, numbers not independently re-verified) |
| Hybrid macOS/Linux OS detection | Archived doc | Not applied | RESURRECT-if-wanted — directly relevant to the desktop-commander facade problem; low priority otherwise | S | VERIFIED (doc) |
| Token-limit audit methodology | Archived doc | Reference material only | **RESURRECT-if-wanted** — a methodology document, useful as a checklist when the catalog/health work (Phase 1) is executed; not a capability itself | — | VERIFIED (doc) |

### 2.5 Plane: Serena (dormant ADHD modules, `services/serena/`)

The deployed Serena is the thin upstream stdio proxy (parent audit §2, §4: "3 surfaces, none reconciled"). All 45+ modules below live in the *local* `services/serena/` candidate that the wrapper script cannot even reach (points at a nonexistent `v2/mcp_server.py` path) — so none of this is one hop from being live; it requires the Serena single-surface decision (parent audit §7.1: "archived or promoted later via ADR + proof") to land first.

| Feature | Source | Current status | Verdict | Effort | Confidence |
|---|---|---|---|---|---|
| Complexity banding (0–1 score + 🟢🟡🟠🔴 + "tackle at peak focus" framing) | `adhd_features.py` `CodeComplexityAnalyzer` | Dormant, local candidate only | **RESURRECT** — CRITICAL priority per source; direct ADHD-doctrine value (matches the 0.0–0.6/0.6–1.0 complexity band already referenced in `~/.claude/MCP_Serena.md`/`MCP_DopeContext.md`) | M | VERIFIED |
| Focus Mode Manager (5 modes LIGHT→HYPERFOCUS, break reminders, switch tracking) | `focus_manager.py` | Dormant | **RESURRECT** — CRITICAL per source | M | VERIFIED |
| Fatigue Detection Engine (8 indicators + 8 adaptive responses) | `intelligence/fatigue_detection_engine.py` | Dormant | **RESURRECT** — CRITICAL per source, in source's TOP-3 (~8h combined with context-switch optimizer) | M | VERIFIED |
| Untracked Work Detector (abandoned git work + ConPort mismatch, 6 sub-detectors) | `untracked_work_detector.py` | Dormant | **RESURRECT** — CRITICAL per source, in TOP-3 ("what did I forget?" relief, ~4h combined with abandonment tracker) | M | VERIFIED |
| Adaptive Learning Engine (per-user attention patterns, cross-session personalization) | `intelligence/adaptive_learning.py` | Dormant | **RESURRECT** — CRITICAL per source, #1 in TOP-3 ("foundation, ~6h") — other modules build on this | M | VERIFIED |
| Personal Learning Profile (persists accommodation prefs) | `learning_profile_manager.py` | Dormant | **RESURRECT** — CRITICAL per source; pairs with Adaptive Learning Engine | S | VERIFIED |
| Cognitive Load Orchestrator (real-time load → unified response) | `intelligence/cognitive_load_orchestrator.py` | Dormant | **RESURRECT** — CRITICAL per source; this is the module that *combines* the others below into a single signal | M | VERIFIED |
| Abandonment Tracker (7-day = abandoned, guilt-free framing) | source not further specified | Dormant | **RESURRECT** — HIGH per source, TOP-3 pairing with Untracked Work Detector | S | VERIFIED |
| Context Switching Optimizer (severity, interruption fatigue, resumption support) | source not further specified | Dormant | **RESURRECT** — HIGH per source, TOP-3 pairing with Fatigue Detection | M | VERIFIED |
| Pattern Recognition (navigation patterns + ADHD-risk typing) | source not further specified | Dormant | **RESURRECT** — HIGH per source | M | VERIFIED |
| Progressive Disclosure Director (3-level, max-5-items) | source not further specified | Dormant | **RESURRECT** — HIGH per source; directly matches the ADHD max-3/max-10 conventions already stated in global doctrine — should reuse, not reinvent, those constants | S | VERIFIED |
| Git Prediction (next-files-from-edit-history) | source not further specified | Dormant | RESURRECT-if-wanted — MEDIUM per source; note the parent audit lists Serena's own `predict_navigation_from_git` as a *documented* tool name in `MCP_Serena_REFERENCE.md` — check for overlap/duplication before building | M | VERIFIED (dormant code) / INFERRED (overlap risk) |
| Metrics Dashboard (F1–F6 analytics) | source not further specified | Dormant | RESURRECT-if-wanted — MEDIUM per source | M | VERIFIED |

### 2.6 Plane: task-orchestrator (deprecated PM/TaskMaster Python stack + adhd_engine)

This is the Python `services/task-orchestrator` + `services/adhd_engine/` stack the parent audit already flags as an unwired parallel MCP surface sharing a name collision with the live Kotlin jar (parent audit §2, §4, §7.1: "rename Python service → `workflow-api`"). The features below are independent of that naming fix — they're capability gaps inside whichever surface ends up canonical.

| Feature | Source | Current status | Verdict | Effort | Confidence |
|---|---|---|---|---|---|
| Task Complexity Scoring (ML bands 0–1, cognitive load, energy tagging) | ADR-207 ML risk module | Dormant; `/dx:prd-parse` returns unscored flat lists today | **RESURRECT** — CRITICAL ADHD gap per source; note this overlaps with Serena's `CodeComplexityAnalyzer` (2.5 above) and dope-context's complexity scorer (parent audit §7.1 3.3: "unify complexity scoring or drop the claim") — **three separate complexity-scoring implementations now exist across the fleet (Serena, dope-context, this ADR-207 module) and none is wired**; resurrecting this one without the unification decision would create a fourth | M | VERIFIED (gap) / INFERRED (fourth-implementation risk) |
| Predictive Risk Assessment (562 lines, 8 risk categories incl. hyperfocus burnout, context-switching) | `predictive_risk_assessment.py` | Dormant ML in orchestrator | **WIRE-EXISTING** — source explicitly says "~3 lines to hook"; this is the highest ROI single item in the entire register — fully-built ML safety net one hook away from live | S | VERIFIED |
| Energy-Aware Task Routing | `get_task_recommendations` | Live but shallow placeholder | **WIRE-EXISTING** — needs wiring to real ADHD-engine telemetry rather than a new build | S–M | VERIFIED |
| Dependency Auto-Inference | `analyze_dependencies` | Live but keyword-only stub | **RESURRECT** — TaskMaster had semantic + critical-path inference; current stub is much weaker | M | VERIFIED |
| Sprint Auto-Planning | `automate_sprint_planning` | Built in orchestrator, unused; ConPort has no sprint API | **RESURRECT-if-wanted** — genuinely not built end-to-end (ConPort side is missing entirely); largest lift in this table | L | VERIFIED |
| Multi-Team Coordination (562 lines, batched comms ≤3/day interruptions) | `multi_team_coordination.py` | Fully built, dormant-by-design for current single-operator MVP | **RESURRECT-if-wanted (later)** — explicitly a "hidden gem for multi-agent futures," not a current gap; correctly dormant for now, don't prioritize | L | VERIFIED |
| Status Normalization (pending/in_progress vs TODO/IN_PROGRESS/DONE/BLOCKED cross-surface drift) | cross-surface observation | P1 gap | **DECISION-NEEDED** — blocks PM reliability; source notes overlap with a separate memory-log item on `task.failed` deferral / PMTaskStatus dialect maps — needs one normalization decision, not a per-surface patch | M | VERIFIED (gap) |
| Decision Traceability (task→ConPort decision links) | cross-surface observation | P0 gap | **RESURRECT** — governance-critical for proof bundles; should be scoped alongside ConPort's relationship-write-API work (packet 201/202 in parent audit §7.1) rather than built standalone | M | VERIFIED (gap) |
| Context Preservation | `adhd_engine/context_preserver.py` | LIVE but not wired to PM display | **WIRE-EXISTING** — backend works, just needs a UI/PM surface | S | VERIFIED |
| Overwhelm Detection/Suppression | `event_coordinator.py` | Telemetry exists; PM doesn't expose a snapshot | **WIRE-EXISTING** | S | VERIFIED |
| Event bus (Redis Streams) triggering orchestrator workflows | live infra | LIVE but PM doesn't trigger event-driven workflows from it | **WIRE-EXISTING** — infra already runs; connects directly to parent audit §7.2's memory-spine event work (same bus, same fix category) | M | VERIFIED |
| PRD complexity scoring | current: SuperClaude + PAL, no ML scoring | PARTIAL | **SUPERSEDED (partially)** by the Task Complexity Scoring row above — same unification question applies | — | VERIFIED |

---

## 3. Prioritized shortlist (impact ÷ effort)

### 3a. WIRE-EXISTING quick wins (dormant code, just needs connecting — highest ROI)

1. **Predictive Risk Assessment hook** (`predictive_risk_assessment.py`, 8 risk categories incl. hyperfocus burnout) — source's own estimate is "~3 lines to hook." Fully-built ML safety net, currently inert. Single highest ROI item found across all six agents.
2. **ConPort graph-neighbor traversal MCP tools** (`graph.neighbors` + `find_by_relationship_type`) — AGE Cypher already complete; expose as `conport_get_neighbors`/`conport_find_by_relationship_type`. Unlocks dependency tracing without touching the quarantined vector-search code.
3. **Context Preservation → PM display wiring** (`adhd_engine/context_preserver.py`) — backend live, no consuming surface. Cheap UI/display hookup.
4. **Overwhelm Detection snapshot exposure** (`event_coordinator.py` telemetry) — same shape as #3: live data, no surface.
5. **Event bus → orchestrator workflow triggers** — Redis Streams infra already runs; PM just doesn't listen to it for workflow-driving events. Note: this is the *same* event bus the parent audit's memory-spine fix (§7.2) targets — solve once, benefit twice.
6. **mcp-capture registration** — finished, tested, unregistered. Either register it as its own MCP server or fold its logic into `capture_client.py` (the path the parent audit already wires for `error.encountered`).
7. **ConPort relationship-vocabulary widening** (`graph.link`'s affects/depends_on/implements/discussed_in/produced_by/belongs_to_thread types) — only `link_conport_items` exposed today; the richer vocabulary is modeled and unused.

### 3b. LOST-PATTERN restorations (some already partly covered by the new fleet catalog — noted)

8. **Progressive token truncation as a shared MCP utility** (item-by-item, 9K budget stop) — Zen-validated pattern from `CONPORT_TOKEN_LIMIT_FIX`, lost in migration. Should land as one fleet-wide utility (used by any server doing bulk queries) rather than reimplemented per-server. **Not yet covered** by the parent audit's Phase 1 catalog work — catalog solves *config* drift, not *response-size* drift; this is a distinct, still-open gap.
9. **MCP boundary-enforcement truncation point** (single interception at `call_tool()` TextContent boundary) — same lost-pattern family as #8, standardizes where truncation happens fleet-wide instead of scattered per-endpoint. Pairs naturally with #8 and with parent audit Phase 1's codegen work.
10. **HTTP/SSE dual-transport retrofit to PAL** — the pattern already has a living, proven implementation (task-orchestrator's singleton launcher, parent audit's "best-engineered lifecycle path"). The *specific* gap left is applying it to `pal-mcp-server`, which the parent audit separately flags as unmanaged/off-compose with no ensure script and a hard Codex dependency (`required=true`). **Largely superseded in principle** (pattern proven) but **not yet applied** to the one server that most needs it.

Honorable mention, not in the top 10 but worth flagging for Phase 1 planning: the **health endpoint contract + server registry/metadata** lost pattern is **already the parent audit's Phase 1 deliverable** ("one catalog, generated everything," §6.1/§7.1) — this archaeology pass is confirmation the pattern is a recovery of prior art, not new scope, and slightly strengthens the case that Phase 1 is not over-engineering.

### 3c. RESURRECT-if-wanted (larger builds, real value, no existing scaffold to just wire)

- **Adaptive Learning Engine + dependents (Serena)** — source's own estimate: foundation ~6h, then Fatigue+Context-Switch ~8h, then Untracked+Abandonment ~4h (~18h total for the full CRITICAL+HIGH cluster). Blocked on the Serena single-surface ADR decision (parent audit §7.1) — building this into the local candidate that the wrapper can't reach yet is wasted work until that decision lands.
- **Semantic memory / graph traversal in ConPort** (progressive disclosure tiers, genealogy chains, ADHD neighborhood exploration) — real value, but each depends on the graph-traversal tools (3a #2 and #7) landing first, and the vector-search half of "semantic memory" is the DECISION-NEEDED boundary conflict in §2.1 — don't bundle these together in one packet.
- **Predictive risk / complexity-scoring unification** — three separate complexity scorers now exist (Serena, dope-context, ADR-207 in task-orchestrator) and none is wired; resurrecting any one without an explicit "pick one, or federate them" decision compounds the shadow-twin problem the parent audit describes for live servers.

---

## 4. What to explicitly NOT do

These are settled or correctly-dropped; re-opening them would be scope creep against decisions already made by the source material itself:

- **`documentation_search` (dead gptr tool)** — redundant with Context7 + dope-context; source's own verdict is "🔴 redundant," don't resurrect.
- **Correction-via-supersession** — already shipped in dope-memory's `memory_correct`. No action.
- **Autonomous indexing** — already shipped in dope-context (`start_autonomous_indexing`/`sync_workspace`). No action.
- **Mem0 hosted-cloud memory** — forbidden by the 2026-05-01 MCP customization synthesis (parent audit §3.1); Claude-Mem/Mem0 patterns are reference-only DR material, never a literal adoption candidate.
- **PRD→tasks auto-generation** — disabled by design; `/dx:prd-parse` (human-review-gated) is the sanctioned path. Source material explicitly calls the current disabled state "correct."
- **Leantime bidirectional write-sync** — gated by design; this is a PM-authority-boundary decision already made (task-orchestrator = workflow-transition legality only, Leantime = PM metadata per parent audit §3.1's authority map). Leave gated.
- **Reviving `mcp-integration-bridge` as a container** — several genuinely valuable capabilities live inside it (KG endpoints, workflow templates, progress dashboard, ADHD context middleware), but the bridge itself is on the parent audit's kill list because of a secret-leaking debug endpoint. Any resurrection of those capabilities must be a clean rewrite against the current fleet, not reactivating the bridge process.
- **Multi-Team Coordination** — fully built, but explicitly dormant-by-design for the current single-operator MVP. Don't prioritize; revisit only if/when multi-agent operation becomes an actual near-term plan.
- **Vector semantic search in ConPort as a default "just resurrect it" item** — flagged DECISION-NEEDED above specifically to prevent this: the source file's framing ("this is the missing `semantic_search_conport`") is seductive but contradicts the Trinity boundary. Do not silently build it into ConPort without an ADR.

---

## 5. Cross-reference to the roadmap

Mapping against the parent audit's Phase 0–5 plan (`claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md` §8) and its packet references (§7.1, §7.3):

| Item | Roadmap fold-in | Notes |
|---|---|---|
| ConPort graph-neighbor tools, relationship-vocabulary widening | **Phase 3, packets 106/107/201/202** | Parent audit already scopes "JSON-RPC parity, kill GET-mutation, product context, relationship write API — the minimum set that makes 'knowledge graph' true." Graph-traversal tool exposure folds directly in here as an *addition* to 201/202's relationship-write-API scope, not a new packet. |
| Decision Traceability (task→ConPort links) | **Phase 3, packets 201/202** | Same packet family — task-to-decision links are a relationship-API consumer. |
| Progressive token truncation, MCP boundary-enforcement truncation | **New: fold into Phase 1** (catalog/codegen work) or a **new net-new packet** if Phase 1 doesn't already scope response-size discipline | Recommend adding this explicitly to Phase 1's CI-gate language (§6.1) rather than assuming it's implied — it is a distinct axis (response size) from what's currently scoped (config drift). |
| HTTP/SSE retrofit to PAL | **Phase 0/1, item "ensure-pal.sh"** | Parent audit already schedules `ensure-pal.sh` + healthcheck for PAL in Phase 0.2/1.3/1.6. The HTTP-singleton-transport *pattern* recovery strengthens the case for that work but doesn't require a new packet — same deliverable. |
| Health endpoint contract + registry metadata | **Phase 1.1/1.2** (unified catalog + codegen) | Already fully scoped; this archaeology is corroborating evidence, not new work. |
| Predictive Risk Assessment wire-up, Energy-Aware Task Routing, Context Preservation/Overwhelm Detection/Event-bus wiring (task-orchestrator + adhd_engine cluster) | **Net-new** — not currently in the parent audit's phases (parent audit's task-orchestrator scope is Kotlin-jar-only: auto-start, truth-pack regen, Python-service rename) | Recommend a **new packet series** (e.g., `TP-DMX-ADHD-ENGINE-WIRE-*`) scoped specifically to wiring the dormant `services/adhd_engine/` + orchestrator-Python ML modules to the (renamed) `workflow-api` surface, sequenced *after* the parent audit's Phase 0/1 name-collision fix so it targets a stable surface. |
| Serena dormant ADHD modules (complexity banding, fatigue detection, adaptive learning, etc.) | **Blocked on Phase 3.2** (Serena single-surface ADR + archive/promote) | Parent audit already identifies this as a precondition ("archived or promoted later via ADR + proof — not left ambient"). No new packet needed yet; this register is the input to that future ADR's cost/benefit case. |
| Memory-spine cluster (event_id dedup, session re-injection, pre-storage redaction, `/mcp` JSON-RPC parity) | **Already substantially scoped — Phase 2 (§7.2, §8 Phase 2)** | Parent audit's Phase 2 covers hook→capture_client wiring, instance identity, mirror receipts, chronicle validation. Event_id dedup and pre-storage redaction are not explicitly named in Phase 2's five bullets — recommend adding them as explicit Phase 2 sub-items (2.6, 2.7) rather than a new phase. Session re-injection is a natural Phase 2 follow-on once chronicle has content (Phase 2.4's acceptance test is the gate). |
| Complexity-scoring unification (Serena vs dope-context vs ADR-207/task-orchestrator) | **Already flagged — Phase 3.3** | Parent audit §7.3/§8 Phase 3.3 already says "complexity-scoring unification or claim removal." This archaeology adds a third implementation to the reconciliation set (ADR-207 in task-orchestrator) that the parent audit's wiring agents likely didn't see since it's dormant/quarantined code, not a live server. Worth folding into 3.3's scope explicitly. |
| Vector semantic search in ConPort (DECISION-NEEDED) | **Not currently in any phase — needs an ADR before it can be scoped** | Recommend this become an explicit agenda item before or alongside Phase 3 (ConPort canonical-surface work), since it's a Trinity-boundary question, not an implementation task. |
| Multi-Team Coordination, Sprint Auto-Planning | **Not in roadmap — correctly out of scope for now** | No fold-in recommended; revisit only alongside future multi-agent or sprint-automation initiatives. |

---

## 6. Governance footer

**Authority used**: three scratchpad archaeology files (agent outputs, static-code reads with file:line citations where given); parent audit doc §3 (canonical feature register), §7 (target-state design), §8 (phased plan); prior memory entries on ConPort-optimal-rebuild (2026-06-16) and the 2026-05-31 ADHD cognitive/UX audit, cross-referenced but not re-verified in this pass.
**Analysis performed**: read all three scratchpad files in full; read the parent audit doc in full; cross-checked every scratchpad row against Memory Trinity boundary law (parent audit §3.1) and the existing Phase 0–5 roadmap (parent audit §8) to classify verdict + roadmap fold-in; flagged one boundary conflict (ConPort vector semantic search vs dope-context's retrieval authority) that the source scratchpad framed as a clean resurrect but which requires an ADR.
**Validation performed**: PASS — internal consistency check that every row in the three source files is represented in §2's register (no dropped items; sub-tables trace 1:1 to source file sections). FAIL — none. NOT_RUN — no code was executed, no MCP tool was called, no dormant module was imported or smoke-tested; every "exists"/"dormant"/"~3 lines to hook" claim is inherited from the archaeology agents' static reads and is **not independently re-verified** in this synthesis pass. Docker was down for the parent audit and was not brought up for this addendum.
**Remaining uncertainty / risk**: dormant-code claims could be stale (files may have been touched, moved, or partially gutted since the archaeology agents read them — no diff was taken against current HEAD for this addendum); effort estimates (S/M/L, "~3 lines," "~6h") are inherited from source-agent judgment, not independently re-derived; the "fourth complexity-scorer" and "must-rewrite-not-revive" observations in §2 are this synthesis's own inference layered on top of the source facts, flagged INFERRED accordingly; whether any currently-running process depends on the quarantined `conport_kg` code path was not checked (verify before any deletion, per parent audit's own caveat for its kill list).
**Files touched**: this document only (`claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md`, newly created). No other files edited. No commit made (per task instructions).
**Git state**: worktree `claude/trusting-engelbart-d2fbfe` (see repo root), branch unchanged, working tree has one new untracked file (this doc) plus pre-existing modified `.claude/claude_config.json` noted in session git status (not touched by this task).
**Rollback plan**: `rm claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md` — fully additive, no other state changed.
**Requested next step**: operator review of the DECISION-NEEDED rows (ConPort vector semantic search boundary call; status normalization dialect choice) before any implementation packet is written; if approved, fold the "net-new" row from §5 (ADHD-engine wiring series) into the task-packet backlog alongside the parent audit's existing Phase 2/3 packets.
