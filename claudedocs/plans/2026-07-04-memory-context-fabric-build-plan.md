# Memory Context Fabric — Master Build Plan

> **For agentic workers:** This is the entry point. Pick up ONE packet plan at a time, in dependency order. Each packet plan is self-contained (exact files, complete code, TDD steps, commits) — REQUIRED SUB-SKILL where available: `superpowers:subagent-driven-development` or `superpowers:executing-plans`. If you have neither, execute the packet plan's checkbox steps literally, in order, committing where the plan says to commit.

**Goal:** Build the Memory Context Fabric — the subsystem that makes dopemux capture everything (including conversation history) and inject the needed context into sessions implicitly — as a sequence of independently shippable, test-gated packets.

**Architecture:** A coordination layer over the Memory Trinity (dope-memory = chronicle, ConPort = decisions, dope-context = retrieval). The Fabric is a canonical-writer *client* and cross-plane *reader* — it owns no truth, no storage, no fourth datastore. Capture flows transcript-files + hooks → redact → dedup → route into the existing `capture_client` spine; retrieval/injection assembles authority-labeled, token-budgeted bundles back into sessions.

**Tech stack:** Python 3.12 (`mise exec -- python`), SQLite (chronicle ledger), pytest (`tests/unit/`), click CLI, existing dope-memory capture spine (`src/dopemux/memory/capture_client.py`), Claude Code native hooks (`src/dopemux/claude/native_hooks.py`).

## Global constraints (apply to every packet)

- **Interpreter:** `mise exec -- python` (3.12) — never the system python3.
- **Authority docs (the spec — read before building):** `claudedocs/memory-context-fabric-design-2026-07-04.md` (v3), `claudedocs/memory-context-fabric-interfaces-2026-07-04.md`, `claudedocs/tp-mcf-001-authority-map-2026-07-04.md`. Runtime code outranks docs; if they conflict, report it, don't silently choose.
- **Boundary invariant:** Fabric code never imports a plane's storage internals; every write goes through a canonical writer (`emit_capture_event`, ConPort API, dope-context indexer). No new datastore.
- **Never break the session:** all capture/injection failure paths are fail-open for the user's session, and logged — never silently "succeeded".
- **Hermetic tests:** ledger via `DOPEMUX_CAPTURE_LEDGER_PATH` → `tmp_path`; no Docker, no Redis, no network in unit tests.
- **Proof per packet (AGENTS.md discipline):** `git status` before/after, `git diff --stat`, test outputs with exit codes, and the packet's own proof-gate checklist. Report PASS / FAIL / NOT_RUN honestly.
- **Branch:** work on/off `claude/memory-context-fabric`; PR to `main` per packet (one packet = one PR).

---

## Dependency graph & sequencing

```
TP-MCF-001 (DONE — authority map, no code)
    │
    ▼
TP-MCF-002  transcript ingest → raw ledger only          [BUILD NOW — plan ready]
    │
    ▼
TP-MCF-003  conversation.decision_candidate + promotion   [BUILD NOW — plan ready]
    │
    ▼
TP-MCF-004  SessionStart recap injection                  [BUILD NOW — plan ready]
    │                     (independent of 002/003 at code level; sequenced after
    │                      so the recap has real chronicle content to show)
    ├──────────────┬──────────────────────┐
    ▼              ▼                      │
TP-MCF-005      TP-MCF-006                │   [DECISION FORKS — do not build until decided]
semantic mem    ConPort graph             │
    │              │                      │
    └──────┬───────┘                      │
           ▼                              │
TP-MCF-007  Fabric orchestrator + context.recall/recap ◄──┘  [BLOCKED on 002-004; 005/006 optional modalities]
           ▼
TP-MCF-008  summarization worker (LLM, candidate-only)       [BLOCKED on 003+007]
           ▼
TP-MCF-009  proactive mid-session injection                  [BLOCKED on 007; kill-switch mandatory]
```

## Packet index

| Packet | Status | Plan / spec location |
|---|---|---|
| TP-MCF-001 | **DONE** | `claudedocs/tp-mcf-001-authority-map-2026-07-04.md` |
| TP-MCF-002 | **READY TO BUILD** | `claudedocs/plans/2026-07-04-tp-mcf-002-transcript-ingest.md` |
| TP-MCF-003 | **READY TO BUILD** (after 002 merges) | `claudedocs/plans/2026-07-04-tp-mcf-003-deterministic-promotion.md` |
| TP-MCF-004 | **READY TO BUILD** (parallel-safe with 003) | `claudedocs/plans/2026-07-04-tp-mcf-004-sessionstart-recap.md` |
| TP-MCF-005 | **DECISION REQUIRED** — see fork below | this document, §Fork 005 |
| TP-MCF-006 | **DECISION REQUIRED** — see fork below | this document, §Fork 006 |
| TP-MCF-007..009 | **BLOCKED** — scoped stubs below | this document, §Deferred packets |

---

## Fork 005 — semantic memory projection (decide before building)

**Question:** where does semantic (similarity) memory live?

**Option A — derived dope-context `memory_{hash}` projection.**
Scope if chosen: new per-worktree Qdrant collection `memory_{hash}` beside `code_{hash}`/`docs_{hash}` (`services/dope-context/src/utils/workspace.py:164-182`); new `index_memory`/`search_memory` MCP tools; indexer consumes *curated chronicle entries and ConPort decisions only* (never raw transcript); every vector payload carries `{source_system, authority_label, provenance}`.
Prerequisites: **(1) an ADR** amending dope-context's read-only code/docs charter to permit a *derived, non-canonical* memory projection; **(2) the privacy gate** — dope-context embeds via Voyage (external cloud: `indexing_pipeline.py:285-300,580`), so conversation-derived content requires either a local embedding backend for the memory collection or explicit redaction+approval+policy. Raw transcript is never embedded externally, full stop.
Cost: Medium-Large (new collection lifecycle, 2 tools, indexer wiring, ADR).

**Option B — no dope-context involvement.**
Scope if chosen: drop the semantic modality; `context.recall` runs on temporal (chronicle) + structural (ConPort relationships) only; delete the `memory_{hash}` claims from the design docs; also delete or fix the dead `_index_in_dopecontext` painted socket (`eventbus_consumer.py:716-745`).
Cost: Small (doc edits + one dead-code removal).

**Recommendation:** A, *after* 002–004 prove the capture pipeline in practice — the recall quality gap between temporal-only and temporal+semantic is the strongest argument, but it's only measurable once the chronicle has content. Decide with data.

## Fork 006 — ConPort graph exposure (decide before building)

**Question:** implement graph traversal MCP tools on the **active** Docker ConPort, or settle for the existing HTTP relationship endpoint?

**Option A — implement `graph.neighbors` + genealogy on the active runtime.**
Scope if chosen: port the traversal *concepts* (not the code) from dead `src/conport/memory_server.py` / quarantined `services/conport_kg/` into `docker/mcp-servers-source/conport/enhanced_server.py`'s dispatch map (14 tools today, `:1757-1774`); tools: `conport_graph_neighbors(item_id, rel_types?, depth<=2, limit<=10)`, `conport_decision_genealogy(decision_id)`; requires proving the AGE graph tables are populated and the relationship *writer* path works (authority map flags writer authority as unproven).
Cost: Medium — plus a real risk the AGE data layer needs repair first.

**Option B — relationship-query projection only.**
Scope if chosen: the Fabric's structural modality calls the existing `GET /api/workspace-relationships` (`enhanced_server.py:266,2125`) and stops there; no new ConPort tools.
Cost: Zero new ConPort work; bounded structural recall.

**Recommendation:** B for the first Fabric release (007), upgrade to A only if genealogy queries prove wanted. Nothing in 007 hard-depends on A.

---

## Deferred packets (scoped stubs — do not build yet)

**TP-MCF-007 — Fabric orchestrator + `context.recall`/`context.recap` MCP surface.** The coordinating service: retrieval-fusion over whichever modalities exist (temporal always; structural per Fork 006; semantic per Fork 005), returning `ContextBundle` per the interfaces doc §2.4; graceful degradation (unbuilt modality omitted, never faked); single-point token budgeting; the no-plane-internals contract test. Blocked on 002–004 merged. Plan to be written when unblocked.

**TP-MCF-008 — summarization worker.** Async LLM distillation of transcript turns → curated chronicle entries + `conversation.decision_candidate`s (candidate-only, never auto-ConPort). Cheap-model default per the model-routing policy; explicit cost/rate budget; builds on 003's schema. Blocked on 003+007.

**TP-MCF-009 — proactive mid-session injection.** Relevance-gated, rate-limited, kill-switched context surfacing via hooks. The largest UX blast radius — last deliberately. Blocked on 007.

---

## Hand-off protocol for external agents (Codex / Grok / Antigravity)

1. **Read** the three authority docs (Global constraints above), then the ONE packet plan you're executing. Do not read ahead into other packets' scope.
2. **Verify the worktree**: `git status` clean (except `.claude/claude_config.json`, a known machine-local artifact), branch off `claude/memory-context-fabric` or `main` post-merge.
3. **Execute the packet plan's tasks in order** — each task is test-first with explicit commands and expected outputs; commit exactly where the plan says.
4. **Never expand scope**: if the plan conflicts with runtime code, STOP and report the conflict (runtime outranks plan); do not improvise contract changes (schemas, allowlists, event shapes are contract-sensitive surfaces).
5. **Produce the proof bundle**: diff stat, test outputs + exit codes, the packet's proof-gate checklist, residual risks, rollback (revert the packet's commits).
6. **One packet = one PR** to `main`, titled `feat(memory): TP-MCF-00X — <packet name>`.

### Orchestrator loading (optional, deferred)
These plans are deliberately *files, not orchestrator items*: the chain is sequential, so orchestrator coordination adds cost without parallelism. If the operator later fans out to multiple workers, generate task-orchestrator work-items from the packet index table (one item per packet, `depends_on` per the dependency graph) in a single cheap session — the plans themselves remain the source of truth.

## Governance footer
**Validation:** planning artifact only — no code changed. Plans for 002/003/004 are separately authored and self-reviewed against the v3 spec + authority map. **Rollback:** delete `claudedocs/plans/`.
