# Memory Context Fabric — Interfaces & Data Contracts

**Date**: 2026-07-04 · **Status**: DESIGN (fold-in artifact) · **Companion to**: `memory-context-fabric-design-2026-07-04.md` (v3 design spec), `tp-mcf-001-authority-map-2026-07-04.md` (current-runtime truth).
**Purpose**: define the Context Fabric as a **bounded subsystem** — its public surface, data schemas, plane-interaction contracts, and invariants — so it can be folded into a larger dopemux architecture with clear boundaries. This is contract-level design; it names interfaces, not implementations.

---

## 0. Subsystem summary (one-paragraph fold-in)

The **Memory Context Fabric** is a coordination subsystem that makes the three Memory Trinity planes (dope-memory = chronicle, ConPort = decisions, dope-context = retrieval) behave as one implicit memory. It **captures** everything the developer and agents do (conversation transcripts + lifecycle hooks), **routes** it through redaction/dedup into the planes via their canonical writers, and **assembles + injects** relevant context back into sessions. It owns no truth: it is a canonical-writer *client*, a cross-plane *reader/assembler*, and a hook/injection *coordinator*. Its dependencies are the three planes, the Redis event bus, and the native-hook substrate. Its consumers are agent sessions (Claude Code / Codex) that emit events and receive context.

---

## 1. Public surface (what consumers use)

### 1.1 MCP tools (retrieval — read side)

| Tool | Signature | Returns | Notes |
|---|---|---|---|
| `context.recall` | `(query: str, k?: int=3, modalities?: [temporal\|structural\|semantic], workspace_id?: str)` | `ContextBundle` | fuses whichever modalities are built; degrades gracefully |
| `context.recap` | `(hours_back?: int=24, k?: int=3, workspace_id?: str)` | `ContextBundle` | session-continuity recap (chronicle + open decisions) |

Both are **read-only** and **token-budgeted**. Neither writes to any plane.

### 1.2 Capture entry (write side — not a user tool)

Capture is **ambient**, not invoked: it runs as (a) a transcript-file watcher and (b) native-hook handlers. Both funnel to the existing spine `dope_memory.capture_client.emit_capture_event(event: CaptureEnvelope, *, mode, repo_root, emit_event_bus)`. There is no public "write memory" tool; operators may still escalate explicitly via `/decision`, `/caveat`, `/save`.

### 1.3 Injection (hook output — not a tool)

The Fabric's SessionStart hook contributes a `ContextBundle` to the session's injected context (via `system-reminder`), alongside the existing MCP-health/orchestrator/workflow injections. Phase-2 proactive injection surfaces additional bundles mid-session under rate/relevance gates.

---

## 2. Data contracts (schemas)

### 2.1 `CaptureEnvelope` (normalized event — capture input)

```
CaptureEnvelope {
  event_id:      str        # deterministic content hash (type|session|ts_bucket|payload); REQUIRED-stable
  ts:            str (ISO)  # SOURCE timestamp — REQUIRED for transcript events (no now() fallback)
  session_id:    str|null
  workspace_id:  str        # per-worktree scope
  instance_id:   str
  type:          str        # event type (see 2.2)
  source:        str        # "transcript" | "claude_hook" | "cli" | "mcp" | "conport" (receipt) | ...
  payload:       object     # REDACTED before storage
}
```
Storage: `dope-memory.raw_activity_events` (raw, TTL). Redis fan-out envelope adds `data = stable_json(payload)` on stream `activity.events.v1`.

### 2.2 Event-type taxonomy

- **Promotable** (reach the curated chronicle; allowlist duplicated in `capture_client.py` + `promotion.py` — keep synced):
  `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `workflow.phase_changed`, `manual.memory_store`, **`conversation.decision_candidate`** (new, trust-lower).
- **Non-promotable** (raw ledger only, TTL): `session.*`, `file.*`, `tool.*`, transcript turn events, hook activity.
- **Quarantined** (redaction-failure safety artifact; never promoted/searched/projected): transcript turns whose redaction failed.

### 2.3 `PromotedEntry` (curated chronicle — `work_log_entries`)

```
PromotedEntry {
  ...core fields...
  category, entry_type, outcome, importance_score
  source_event_id, source_event_type, source_adapter, source_event_ts_utc, promotion_rule   # provenance chain
  details_json:  object     # trust lives here — NO dedicated `trust` column exists
                            # candidate decisions: details_json.trust="conversation-derived",
                            #                      promotion_rule="conversation_candidate_v1"
}
```

### 2.4 `ContextBundle` (retrieval/injection output)

```
ContextBundle {
  items: [ ContextItem ]
  token_cost: int           # enforced <= budget
  truncated: bool
  workspace_id: str
}
ContextItem {
  content:        str
  source_system:  "dope-memory" | "conport" | "dope-context"
  authority_label:"canonical" | "mirror" | "derived" | "conversation-inferred"
  trust:          "high" | "conversation-derived"
  freshness:      str (ISO)
  provenance:     { source_event_id?, decision_id?, ... }
}
```
Every item is authority-labeled so a consuming agent knows what to trust. A conversation-inferred item never outranks a canonical one.

---

## 3. Plane-interaction contracts (what the Fabric calls; never bypasses canonical writers)

| Plane | Fabric calls (client) | Fabric NEVER does |
|---|---|---|
| **dope-memory** | `emit_capture_event()` (raw + promotion); recap/search reads; **quarantine writer** (own adapter, non-queryable artifact) | write `work_log_entries` directly; bypass the spine |
| **ConPort** | `log_decision(..., provenance=conversation-derived)` **only via an explicit gate**; read relationship traversal (`GET /api/workspace-relationships`) | auto-write decisions from conversation; treat `graph.neighbors` as present (it is dead code — see TP-MCF-006) |
| **dope-context** | (target) `index_memory`/`search_memory` on a **derived** `memory_{hash}` collection — **UNKNOWN until built**; read `search_code`/`docs_search` | send **raw transcript** to external embedding (Voyage); treat semantic memory as present today |
| **Redis event bus** | publish/consume for capture→promotion transport | treat transport as authority |
| **native hooks** | assemble + inject `ContextBundle` at SessionStart (+ proactive later) | assume current `dopemux:events` pings feed the chronicle (they don't — wrong stream) |

---

## 4. Invariants (contract tests — the subsystem's guarantees)

1. **No plane-internal imports** — the Fabric package imports no plane's storage internals (structural test).
2. **Canonical-writer-only writes** — every Fabric write goes through a plane's canonical writer; no fourth store.
3. **Fail-closed redaction** — transcript redaction failure → quarantine, never the queryable ledger (test: no secret reaches the ledger).
4. **Replay-safe capture** — deterministic `event_id` + `INSERT OR IGNORE`; transcript ingest **rejects missing source timestamps** (test: re-ingest idempotent).
5. **Provenance only lowers trust** — conversation-derived items are trust-lower; labels never elevate.
6. **Token budget** — every `ContextBundle` respects the budget (test).
7. **Graceful degradation** — an unbuilt modality is omitted, never faked.
8. **Locality** — raw transcript content never leaves local storage for an external embedding provider without redaction + approval + policy.

---

## 5. Dependencies & scoping (fold-in wiring)

- **Depends on**: dope-memory (`capture_client`, promotion, recap), ConPort (active Docker runtime: decision write + relationship traversal), dope-context (code/docs retrieval today; a derived memory projection to build), Redis (`activity.events.v1`), native hooks (`native_hooks.py` SessionStart), the redactor.
- **Scope**: per-worktree (`workspace_id` = worktree). Chronicle ledger `.dopemux/chronicle.sqlite`; quarantine `.dopemux/quarantine/…`; Qdrant `memory_{hash}` (when built). Optional cross-worktree rollup (`global_rollup.py`).
- **Relation to other subsystems**: sibling to the **DCP read-only facade** (which projects *outbound* to external LLMs) — the Fabric is *inbound + local*. Reuses DCP's provenance/trust model and the fleet-audit "orchestrate, don't own" pattern.
- **Not owned by the Fabric**: any canonical truth, decision/graph/PM/retrieval authority, or a new datastore.

---

## Governance footer

**Authority used**: the v3 design spec + TP-MCF-001 authority map (both file:line-grounded in the active runtime), Memory Trinity ADRs, DCP provenance model. **Validation**: contract-level design only — **no code, live behavior NOT_RUN**; the `index_memory`/`memory_{hash}` and `graph.neighbors` surfaces are explicitly marked UNKNOWN/dead per TP-MCF-001. **Rollback**: delete this file.
