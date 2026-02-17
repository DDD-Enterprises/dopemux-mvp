# Gap Analysis: Multi-Layer Memory for Dopemux

## 1) Baseline Constraints from Current Dopemux (Anchors)
- [VERIFIED] Event-driven substrate exists (Redis Streams with consumer groups, ack/retry) in dopecon-bridge and dope-memory consumer. (source: `services/dopecon-bridge/event_bus.py:70-80`, `services/dopecon-bridge/event_bus.py:239-317`, `services/working-memory-assistant/eventbus_consumer.py:313-332`)
- [VERIFIED] Deterministic retrieval primitives already exist: fixed sort + cursor token + Top-K caps. (source: `services/working-memory-assistant/chronicle/store.py:297-314`, `services/working-memory-assistant/mcp/server.py:88-120`, `services/working-memory-assistant/mcp/server.py:156-157`)
- [VERIFIED] Redaction-first persistence exists and is compatible with strict policies. (source: `services/working-memory-assistant/promotion/redactor.py:102-179`)
- [VERIFIED] Context hydration exists today via request middleware (`X-Context-Token`) and service-local retrieval surfaces. (source: `services/dopecon-bridge/main.py:628-665`, `services/dope-context/src/mcp/server.py:1500-1533`)
- [VERIFIED] Spec already states “no duplication”, Top-3 boundaries, deterministic behavior, and stream contracts. (source: `docs/spec/dope-memory/v1/00_overview.md:26-48`, `docs/spec/dope-memory/v1/01_architecture.md:50-117`)

## 2) Proposed Minimal Multi-Layer Memory Architecture (v1.1)

## 2.1 Lane Model
- [INFERRED] Define explicit lanes (strict ownership boundaries):
  1. `facts_lane` (canonical structured facts/decisions/tasks pointers only)
  2. `worklog_lane` (temporal narrative and recency)
  3. `reflection_lane` (derived summaries/cards/trajectory)
  4. `operator_prefs_lane` (user/routine preferences, ADHD settings pointers)
  5. `safety_lane` (redaction/audit policy events and violations)

- [INFERRED] Ownership and source-of-truth:
  - `facts_lane`: references DopeQuery/ConPort IDs, never duplicates full fact blobs.
  - `worklog_lane` + `reflection_lane`: owned by Dope-Memory SQLite canonical.
  - `operator_prefs_lane`: ADHD engine + profile config pointers.
  - `safety_lane`: Dope-Memory redaction/audit ledger.

Why this fits current repo:
- [VERIFIED] Current schema already separates raw vs curated vs reflection/trajectory tables. (source: `services/working-memory-assistant/chronicle/schema.sql:5-146`)
- [VERIFIED] Existing promotion model already prevents broad event duplication. (source: `services/working-memory-assistant/promotion/promotion.py:13-35`, `docs/spec/dope-memory/v1/01_architecture.md:78-86`)

## 2.2 Per-Lane Opt-In Injection Policy
- [INFERRED] Add explicit policy file: `config/memory/lanes.yaml`.
- [INFERRED] Injection is disabled by default for every lane unless enabled by role/mode/workflow.

Suggested config knobs:
```yaml
version: 1
lanes:
  facts_lane:
    inject_default: false
    allowed_roles: [planner, architect]
    allowed_modes: [PLAN, REVIEW]
    max_items_default: 3
  worklog_lane:
    inject_default: true
    allowed_roles: [operator, implementer]
    allowed_modes: [ACT, RECOVER]
    max_items_default: 3
  reflection_lane:
    inject_default: true
    allowed_roles: [operator, reviewer]
    allowed_modes: [REVIEW, RECOVER]
    max_items_default: 3
  operator_prefs_lane:
    inject_default: false
    allowed_roles: [operator]
    allowed_modes: [ACT, RECOVER]
    max_items_default: 1
  safety_lane:
    inject_default: true
    allowed_roles: [all]
    allowed_modes: [all]
    max_items_default: 3
```

Anchors for feasibility:
- [VERIFIED] Top-K and filter boundaries already exist in MCP/HTTP APIs. (source: `services/working-memory-assistant/mcp/server.py:132-209`, `services/working-memory-assistant/dope_memory_main.py:907-975`)
- [VERIFIED] Mode-aware behavior already appears in profiles and router defaults/background/think channels. (source: `src/dopemux/profile_models.py:133-200`, `src/dopemux/dope_brainz_router.py:111-137`)

## 2.3 Event Bus Integration Map (Write/Inject/Compact)

- [INFERRED] Add canonical events under dotted names and stream families:
  - Stream `activity.events.v1` (existing): source events
  - Stream `memory.derived.v1` (existing): promoted outputs
  - New stream `memory.lanes.v1`: lane-write + lane-injection decisions

Proposed event map:
1. `decision.logged` -> write to `facts_lane` pointer + `worklog_lane` promoted note
2. `task.completed|failed|blocked` -> write `worklog_lane`; trigger `reflection_lane` boundary check
3. `session.ended|idle.detected` -> generate `reflection_lane` card
4. `memory.injection.requested` -> evaluate lane policy deterministically; emit `memory.injection.decided`
5. `memory.compaction.requested` -> lane-local compaction job; emit `memory.compaction.completed`

Anchors:
- [VERIFIED] Session boundary, reflection, pulse, derived publish already implemented in Dope-Memory consumer. (source: `services/working-memory-assistant/eventbus_consumer.py:382-392`, `services/working-memory-assistant/eventbus_consumer.py:639-687`, `services/working-memory-assistant/eventbus_consumer.py:493-516`)
- [VERIFIED] Cross-plane event routing already emits structured coordination events. (source: `services/dopecon-bridge/main.py:2826-2937`)

## 2.4 Storage + Search Surface (Lane-Aware)
- [INFERRED] Keep SQLite canonical for all lane payloads; add lane column to curated and reflection entities:
  - `work_log_entries.lane TEXT NOT NULL DEFAULT 'worklog_lane'`
  - `reflection_cards.lane TEXT NOT NULL DEFAULT 'reflection_lane'`
  - new table `lane_injection_audit` for deterministic injection decisions.

- [INFERRED] Optional vector sync remains non-canonical:
  - keep existing DopeContext best-effort indexing path
  - attach lane metadata (`lane`, `workspace_id`, `instance_id`, `entry_id`) to indexed docs.

Anchors:
- [VERIFIED] Current system already treats Postgres mirror/vector indexing as non-canonical/best-effort. (source: `docs/spec/dope-memory/v1/00_overview.md:39-43`, `services/working-memory-assistant/eventbus_consumer.py:714-753`)

## 2.5 Deterministic Injection Decision Interface
- [INFERRED] Add explicit tool/endpoint contract:

```json
POST /tools/memory_injection_decide
{
  "workspace_id": "...",
  "instance_id": "...",
  "role": "implementer",
  "mode": "ACT",
  "workflow_phase": "implementation",
  "requested_lanes": ["worklog_lane", "facts_lane"],
  "top_k": 3
}
```

Response:
```json
{
  "decision_id": "...",
  "granted_lanes": ["worklog_lane"],
  "denied_lanes": [{"lane":"facts_lane","reason":"role_not_allowed"}],
  "items": [...],
  "policy_version": 1
}
```

- [INFERRED] Always persist decision in `lane_injection_audit` with deterministic reasons and scope hash.

## 3) Gap Matrix
- Gap 1: No centralized lane policy artifact.
  - [VERIFIED baseline] policies are scattered across service code/spec/profile files.
  - [INFERRED fix] add `config/memory/lanes.yaml` + validator in CI.

- Gap 2: Injection decisions are not uniformly auditable.
  - [VERIFIED baseline] context hydration/search happen in multiple services with local logic. (source: `services/dopecon-bridge/main.py:628-665`, `services/dope-context/src/mcp/server.py:1500-1533`)
  - [INFERRED fix] emit `memory.injection.decided` + write `lane_injection_audit` rows.

- Gap 3: Registry drift for memory-related services.
  - [VERIFIED baseline] `services/dope-context` exists but registry entries shown do not include `name: dope-context`. (source: `_audit_out/_sources/services_dir_listing.txt:12-12`, `services/registry.yaml:20-293`)
  - [INFERRED fix] registry reconciliation gate for memory service set.

- Gap 4: Duplicate/legacy memory implementations uncertainty.
  - [VERIFIED baseline] `wma_core.py` is labeled prototype while dope-memory HTTP+consumer path is active. (source: `services/working-memory-assistant/wma_core.py:1-7`, `services/working-memory-assistant/dope_memory_main.py:3-12`)
  - [INFERRED fix] formally deprecate/retire prototype path or codify as fallback mode.

## 4) Minimal Implementation Sequence
1. [INFERRED] Introduce lane policy schema + loader + CI validation.
2. [INFERRED] Add `lane` field and `lane_injection_audit` table migration to SQLite canonical.
3. [INFERRED] Implement `memory_injection_decide` endpoint with deterministic reason codes.
4. [INFERRED] Emit `memory.injection.decided` and `memory.compaction.*` events.
5. [INFERRED] Wire role/mode from existing profile/router/ADHD state into decision call path.
6. [INFERRED] Reconcile service registry with memory-related deployed services.

## 5) UNKNOWNs Blocking Full Closure
- [UNKNOWN] True production status/ownership of `claude_brain`, `intelligence`, and `session-intelligence` services.
- [UNKNOWN] Whether `dope-context` omission in registry is intentional or drift.
- [UNKNOWN] Final source-of-truth contract for preference/state between ADHD engine and memory injection beyond current adapter calls.
