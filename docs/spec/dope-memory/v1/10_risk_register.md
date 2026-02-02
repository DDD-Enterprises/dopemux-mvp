---
id: 10_risk_register
title: 10_Risk_Register
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Dope-Memory v1 — Risk Register

## R1: Noise overload (implicit capture too broad)
Description
- Logging all file saves/git actions as curated entries overwhelms the chronicle and harms ADHD-first objective.
Mitigation
- Phase 1 promotes high-signal only.
- Store noisy events in raw buffer with short retention.
- Add explicit promotion rules only after real usage proves value.

## R2: Secret/PII leakage into logs
Description
- Event payloads may contain tokens, credentials, or private keys.
Mitigation
- Dual redaction pass (ingest + promotion).
- Denylist path hashing.
- Regex scrubbing for common secret formats.
- Fail closed on redaction errors.

## R3: Duplication with DopeQuery and DopeContext
Description
- Dope-Memory may drift into becoming a second canonical store or semantic archive.
Mitigation
- Strict ownership boundaries:
  - DopeQuery owns decisions and truth.
  - DopeContext owns semantic archival.
  - Dope-Memory owns temporal narrative + reflections.

## R4: Non-deterministic retrieval erodes trust
Description
- If tool results reorder unpredictably, the system becomes unreliable.
Mitigation
- Deterministic ranking rules.
- Stable tie-breakers.
- Cursor scope hash validation.
- No LLM scoring in Phase 1 ranking.

## R5: Mirroring inconsistencies (SQLite ↔ Postgres)
Description
- Postgres mirror may diverge or lag.
Mitigation
- SQLite is canonical.
- Mirror worker is idempotent upsert.
- Track mirror checkpoints by last synced ts/id.
- Tolerate Postgres downtime.

## R6: EventBus at-least-once semantics cause duplicates
Description
- Replayed events could insert duplicates.
Mitigation
- Use event id as primary key in raw store.
- Use curated entry id as primary key for upserts.
- Promotion engine must be idempotent: same event id -> same curated id.

## R7: Trajectory boosting causes confusing relevance (Phase 2)
Description
- Boosting active stream might hide older-but-critical decisions.
Mitigation
- Keep deterministic baseline ordering.
- Boost is bounded and transparent.
- Provide "sort=importance" override.

## R8: Causal edge pollution (Phase 3)
Description
- Auto-created edges may be wrong, polluting KG and harming future retrieval.
Mitigation
- Only propose edges by default.
- Require explicit acceptance or strict heuristics.
- Store confidence and evidence windows.
- Provide rollback and edge quarantine.

## R9: Focus-state gating conflicts with user intent (Phase 4)
Description
- Suppressing context during focus mode could block needed info.
Mitigation
- Always allow explicit search to override gating.
- Gating affects proactive surfacing, not explicit requests.

## R10: Legal/compliance logging risks
Description
- Logs might capture sensitive client or personal data if used outside dev context.
Mitigation
- Scope Dope-Memory to dev workspace events.
- Add opt-out denylist for paths/projects.
- Redaction patterns include emails, phone numbers if needed in future.

## R11: Storage growth
Description
- Curated log grows indefinitely.
Mitigation
- Support archive/export.
- Optional compaction via reflection cards (Phase 2).
- Optional retention policy per category (later).

## R12: Multi-instance confusion
Description
- Mixing worktrees without strict scoping can surface wrong context.
Mitigation
- Mandatory workspace_id + instance_id filters for all queries.
- Include instance_id in all stored rows and response items.
