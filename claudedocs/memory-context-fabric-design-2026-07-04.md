# Memory Context Fabric — Design Spec (v3, reaudit-corrected)

**Date**: 2026-07-04
**Status**: Architecture CONDITIONAL-GO (2× external audit). Planning baseline. TP-MCF-001 = GO (no runtime change). Downstream packets gated per the Section 6 matrix.
**Goal**: dopemux *keeps track of everything* and agents *work together seamlessly and implicitly to capture and inject the needed context at all times, including conversation history* — without an operator running `/save` or `/decision`.

**Approved cornerstones**: transcript files **and** hooks · capture broad **raw**, **promote curated** · injection phased (recap+retrieval now, proactive later) · ambitious rebuild · **Context Fabric** orchestration layer over the Memory Trinity (Approach B).

**v3 changelog** (reaudit, all claims re-verified against code):
1. **Privacy vs external embedding** — "nothing sent externally" was too flat: dope-context embeds via **Voyage (cloud)**. Corrected: storage local by default; **raw transcript content is never sent to external embedding providers**; semantic projection of conversation-derived content requires a local embedding backend *or* explicit redaction+approval+provider-policy.
2. **Quarantine** — now defined as a **local safety artifact (not memory truth)** with a named writer (the TP-MCF-002 ingest adapter); path/table declared; not searched/promoted/mirrored/projected.
3. **Hook events are a TARGET source, not current** — native hooks emit to `dopemux:events`; dope-memory's consumer listens on `activity.events.v1`. TP-MCF-002/003 must decide the wiring; don't assume current hook activity is chronicle input.
4. **Candidate decisions** — must use a **distinct event type** (`conversation.decision_candidate`), never `decision.logged` (which the bridge emits only *after* a successful ConPort write); trust encoded in `details_json.trust` + `promotion_rule`.
5. **Transcript idempotency** — ingest must **fail/quarantine on missing source timestamp**, never fall back to ingest-time `now` (which `emit_capture_event` otherwise does), or replay-safety is lost.
6. Non-blocking: `task.*` → exact `{task.completed, task.failed, task.blocked}`; dope-context `/index` kept as "wire exists dope-memory side, dope-context route/collection not proven"; ConPort = "relationship traversal exists (`workspace-relationships`), `graph.neighbors` MCP parity not proven."

---

## 0. Current runtime truth vs. target (honesty table)

| Capability | Current runtime (verified) | Target |
|---|---|---|
| Split-authority Trinity | **REAL** — 3 distinct canonical planes | keep; Fabric coordinates, never owns |
| Raw capture spine | **REAL** — `capture_client.py` (deterministic IDs, redaction, `INSERT OR IGNORE`, raw ledger, Redis fan-out); dope-memory compose `ENABLE_EVENTBUS=true`, ledger `/data/chronicle.sqlite` | reuse; do not rebuild |
| Curated chronicle | **REAL** for `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `workflow.phase_changed`, `manual.memory_store` | add transcript-derived classes (deterministic first) |
| Hook injection substrate | **REAL** — `native_hooks.py` SessionStart injects MCP health + orchestrator + workflow context | extend with a recap bundle |
| **Hook events → dope-memory** | **NOT WIRED** — hooks emit to `dopemux:events`; consumer listens on `activity.events.v1` | TP-MCF-002/003 decide: call `emit_capture_event()` directly, emit to `activity.events.v1`, or bridge the two streams |
| Transcript-file ingest | **MISSING** — hooks emit content-free activity + bounded hook-error captures; `UserPromptSubmit` records to workflow state only when a workflow is active | build as its own adapter (raw-ledger-only first) |
| Semantic memory in dope-context | **NOT REAL** — collections `code_{hash}`/`docs_{hash}` only; `_index_in_dopecontext` POSTs `/index worklog_index` but dope-context route/collection **not proven** | build a derived projection (fork, ADR) or drop; **Voyage embedding is external** — privacy constraint below |
| ConPort graph | **DEAD-SURFACE** in `src/conport/memory_server.py` (declares itself dead). Active runtime: relationship traversal via `/api/workspace-relationships` → `get_related_decisions`; decisions/progress/search/custom-data/`/mcp`. **No `graph.neighbors` MCP parity.** | implement/verify on active Docker ConPort, or ship relationship-query projection only |
| Context Fabric `recall`/`recap` | **MISSING** | build (TP-MCF-007) |
| Redaction on failure | **strip-and-store-minimal** (`redactor.py:123-125` → `{redaction_error, original_keys}`, stored anyway; leaks key names) | **hold/quarantine** for raw transcript events |

The architecture below is the *target*; Section 6 phasing is gated so no phase depends on an unproven/unbuilt earlier capability.

---

## 1. Architecture — the Context Fabric over the Trinity

Coordinating layer (service + hook set + thin client lib) owning capture → redact → dedup → route → promote → retrieve → inject; Trinity planes remain canonical stores. Writes *through* canonical writers, reads *across* them; **never a fourth store.**

**Revised authority model:**

| Domain | Canonical writer | Fabric role |
|---|---|---|
| Raw conversation/event ledger | dope-memory | capture-adapter **client only** |
| Curated chronology | dope-memory promotion path | **candidate promoter**, not a store |
| Structured decisions/progress/context | ConPort | explicit **writer client with provenance** (never auto from conversation) |
| Code/docs retrieval | dope-context | **reader only** |
| Memory semantic projection | **UNKNOWN until implemented** | derived-projection **client only** |
| Transcript quarantine | **TP-MCF-002 ingest adapter** | safety-artifact writer (not memory truth) |
| Event transport | dopecon-bridge / Redis | transport client, **not authority** |
| Hook injection | dopemux native hooks | bundle assembler + hook client |

**Boundary invariant:** Fabric is a canonical-writer client + cross-plane reader/assembler. It must NOT own storage, truth, or any domain authority. **Contract test: the Fabric package imports no plane's storage internals.**

---

## 2. Capture pipeline

Reuses `capture_client.emit_capture_event()`. Sources → spine → **capture → redact → dedup → route → promote**. Operator does nothing.

**Sources:** (1) **transcript-file ingest** (watcher over harness JSONL — the missing conversation history); (2) **hook events — a TARGET source**: they currently emit to `dopemux:events`, which the dope-memory consumer does not read, so TP-MCF-002/003 must explicitly wire them (direct `emit_capture_event()`, emit to `activity.events.v1`, or a `dopemux:events → activity.events.v1` bridge). Do not treat current hook activity as chronicle input.

**Redact.** Current runtime strips-and-stores-minimal on failure (leaks key names). For raw **transcript** events, target = **hold/quarantine**: on redaction failure, write only redacted metadata + a withheld/encrypted payload *reference* to a **local safety artifact** — a declared `.dopemux/quarantine/...` path or a dope-memory-owned **non-queryable** quarantine table. Quarantine is **not memory truth**: never searched, promoted, mirrored, or projected. Writer = the TP-MCF-002 ingest adapter. Non-transcript events may keep strip-minimal, but the policy is **named + tested** either way.

**Semantic indexing is opt-in by class:** raw transcript → **dope-memory only** (never auto-indexed); curated chronicle / ConPort decisions → eligible for projection *with authority label*; secret/PII/credential-bearing content → **never projected.** And (privacy): conversation-derived content is **never embedded via an external provider** without explicit redaction + approval + policy.

**Dedup** — deterministic content-hash `event_id` → re-ingest safe **only if** the ingestor uses transcript-origin timestamps; it must **fail/quarantine on missing source timestamp**, never use ingest-time `now`.

**Route → tiers:** raw ledger (`raw_activity_events`, TTL) always; curated chronicle (`work_log_entries`) for promoted high-signal; semantic projection only for eligible classes.

**Decision detection.** A decision-looking turn → a **candidate decision in dope-memory** using a **distinct event type `conversation.decision_candidate`** (never `decision.logged`), with `details_json.trust="conversation-derived"` + `promotion_rule="conversation_candidate_v1"`. Promotion to a canonical ConPort decision requires an explicit gate (operator confirm or deterministic high-confidence rule). **No auto ConPort writes from conversation.**

---

## 3. Memory model

| Plane | Canonical for | Target capability (status) |
|---|---|---|
| **dope-memory** | chronicle: raw ledger, curated `work_log_entries`, reflections, trajectory | + transcript turns; + `conversation.decision_candidate` entries (build); + non-queryable quarantine artifact |
| **ConPort** | decisions/progress/structured context | active runtime has **relationship traversal** (`workspace-relationships` → `get_related_decisions`); `graph.neighbors` MCP + genealogy are **to implement/verify on Docker ConPort**, or ship relationship-query projection only |
| **dope-context** | code/docs retrieval (read-only) | a **derived** `memory` projection — **UNKNOWN until implemented; needs ADR** (read-only today) **and** a privacy-safe embedding path (Voyage is external) |

**Retrieval modalities** (fused *when built*): temporal (dope-memory recap), structural (ConPort relationship traversal), semantic (dope-context memory projection). Fusion **degrades gracefully** — an unbuilt modality is omitted, never faked. **Provenance/trust** (DCP model): conversation-derived = trust-lower; every projection carries an upstream authority label.

---

## 4. Retrieval + injection

**Retrieval-fusion (TP-MCF-007):** `context.recall(query)` / `context.recap()` query whichever modalities exist, merge/rank/dedup, return a bundle with authority labels + a **token budget** (single-point truncation utility).

**Injection Phase 1 (TP-MCF-004):** extend the **existing** `native_hooks.py` SessionStart path with a **bounded recap** from dope-memory recap/search — Top-3 default, token-budgeted, authority-labeled, **no semantic fusion yet**.

**Injection Phase 2 (TP-MCF-009, later):** proactive mid-session surfacing — **rate limit + relevance threshold + kill switch.** Built last; a bad surfacing is worse than none.

---

## 5. Governance & security

- **Split-authority preserved** — contract test: Fabric imports no plane storage internals.
- **Fail-closed** — transcript redaction → hold/quarantine (named + tested); no silent cross-plane fallback; capture failures fail-open for the *session* but are logged/quarantined, never silently "succeeded."
- **Privacy** — storage local by default; **raw transcript never sent to external embedding providers**; conversation-derived semantic projection requires local embedding or explicit redaction+approval+policy. (dope-context currently embeds via Voyage cloud — this is the constraint that gates TP-MCF-005.)
- **Provenance/trust** — conversation-derived = trust-lower; injected bundles carry authority labels; a conversation-inferred decision never outranks an explicitly-logged one.
- **Per-worktree isolation**; cross-worktree rollup opt-in.

**Minimum proof gates (every packet):** `git status` before/after · `git diff --stat` + full diff · command outputs + exit codes · **redaction tests proving secrets never reach the ledger** · **deterministic replay test proving transcript re-ingest is idempotent (and rejects missing source timestamps)** · **no-Fabric-imports-of-plane-internals test** · semantic projections carry upstream authority labels · hook-injection token-budget test · embedded audit for non-trivial changes. (AGENTS.md: Task Packets + validation; review/precommit discipline.)

---

## 6. Phasing / decomposition — reaudit phase-approval matrix

| Packet | Scope | Status | Hard gates |
|---|---|---|---|
| **TP-MCF-001** — Repo-truth contract audit (no runtime change) | authority map for capture/promotion/ConPort-writes/dope-context-indexing/hooks/bridge | **GO** | exact runtime paths named; dead surfaces marked dead; no semantic/graph claims unless code proves them; **no Fabric code** — produces the exact 002/003 packets |
| **TP-MCF-002** — Transcript ingest → raw ledger only | watcher writing **only** `raw_activity_events` | **CONDITIONAL-GO** | **define quarantine writer + path/table**; **stable-timestamp rule (fail/quarantine on missing)**; deterministic IDs; replay-safe; redaction before storage; no ConPort/dope-context writes; never break the session |
| **TP-MCF-003** — Deterministic promotion (transcript → chronicle) | promote safe deterministic classes (explicit decision markers, task completions, errors/blockers, workflow transitions) | **NO-GO until** candidate-decision event/schema defined (`conversation.decision_candidate` + trust fields) | out of scope: LLM summarization, auto ConPort writes |
| **TP-MCF-004** — SessionStart recap via native hooks | extend `native_hooks.py` SessionStart to inject bounded recap | **CONDITIONAL-GO** | token budget; Top-3; authority labels; **no semantic fusion** |
| **TP-MCF-005** — Semantic memory projection (fork) | (1) real derived dope-context `memory_{hash}` + `index/search_memory` **(needs ADR + local/privacy-safe embedding)**, OR (2) keep semantic memory elsewhere and drop the dope-context claim | **NO-GO** | resolve external-embedding/privacy conflict + ADR fork first |
| **TP-MCF-006** — ConPort graph on active runtime | implement/verify graph traversal in `docker/mcp-servers-source/conport/` | **CONDITIONAL-GO** | relationship traversal exists; `graph.neighbors` MCP + writer authority **not proven** — prove or ship relationship-query projection only |
| **TP-MCF-007+** — Fabric orchestrator / summarizer / proactive injection | recall/recap service; LLM distillation (candidate-only, cheap-model, budgeted); proactive injection (rate/relevance/kill-switch) | **NO-GO until prior gates pass** | depends on unbuilt/unresolved pieces |

**Start = TP-MCF-001** (no code), which produces the exact TP-MCF-002/003 packets. **001/002/003 must reconcile with the in-flight memory-spine roadmap work**, not fork it.

---

## 7. Open decisions / risks (UNKNOWNs to resolve in TP-MCF-001/002)

- **Quarantine ownership** — `.dopemux/quarantine/` path vs dope-memory non-queryable table (decide in TP-MCF-002).
- **Transcript JSONL schema/location** per harness (Claude Code vs Codex) — TP-MCF-002 spike.
- **Candidate-decision event/schema** — `conversation.decision_candidate` + trust encoding (TP-MCF-003 blocker).
- **Semantic projection owner + privacy-safe embedding** — external Voyage vs local backend (TP-MCF-005 fork + ADR).
- **ConPort graph feasibility** — AGE traversal on active runtime vs relationship-query projection only.
- **Hook→dope-memory wiring** — direct emit vs stream bridge (TP-MCF-002/003).
- **Summarization cost** — cheap-model default + budget (TP-MCF-008).
- **P0 reconciliation** with in-flight memory-spine work (a live hazard this session already hit).

---

## Governance footer

**Authority used**: verified code (`capture_client.py`, `redactor.py`, `eventbus_consumer.py`, dope-context `workspace.py`, `native_hooks.py`, active ConPort routes), 2× external design audit (claims re-verified against code), Memory Trinity ADRs, DCP provenance model. **Validation**: design/analysis only — **no code changed, live behavior NOT_RUN.** **Status**: planning baseline; TP-MCF-001 next (no runtime change), producing the 002/003 packets. **Rollback**: delete this file.
