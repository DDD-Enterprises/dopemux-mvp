---
id: adr-conport-hardening-scope-and-trinity-boundaries
title: "ADR: ConPort hardening scope and Trinity boundaries"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-16'
prelude: Records which ConPort coverage gaps are in-scope, operator-decisions, or Trinity non-goals, and re-sequences the DMX-CONPORT-OPTIMAL series behind a gated migration-apply foundation.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-memory-trinity-authority-and-interaction-model
    - adr-conport-as-decision-progress-and-context-authority
---

# ADR: ConPort hardening scope and Trinity boundaries

**Status:** Proposed
**Date:** 2026-06-16
**Owners:** Dopemux Memory Plane
**Decision Type:** Scope / Authority Boundary / Series Sequencing
**Scope:** `DMX-CONPORT-OPTIMAL` series, ConPort server (`docker/mcp-servers-source/conport/`), companion `DMX-CONPORT-HARDENING` series
**Evidence base:** [conport-optimal-coverage-and-hardening-analysis-2026-06-16.md](../../claudedocs/conport-optimal-coverage-and-hardening-analysis-2026-06-16.md) (17-agent adversarial workflow + live-runtime verification + gpt-5.2 review)

## Context

The loaded 18-packet `DMX-CONPORT-OPTIMAL` series rebuilds/extends ConPort — the canonical Memory-Trinity authority for decisions/progress/structured-context ([adr-memory-trinity-authority-and-interaction-model](adr-memory-trinity-authority-and-interaction-model.md)). An expansion analysis (see evidence base) surfaced a class of operational, security, concurrency, consumer-resilience, and contract-reconciliation gaps the series did not address, plus a **root cause beneath Tier-2/Tier-3**: the server never applies its migrations, so five feature packets target tables/columns that do not exist at runtime (RUNTIME-VERIFIED against the live `mcp-conport` container and `dopemux_knowledge_graph` DB).

Two questions needed durable answers so contributors stop re-deriving them: **(1)** which gaps does the Memory Trinity boundary actually exclude (vs merely not-yet-built)? **(2)** what is the correct sequencing given the migration root cause?

## Decision

### D1 — A gated migration-apply foundation (Tier-0) precedes all feature packets

The series is re-sequenced. A new **Tier-0 foundation** blocks TP-202/203/301/302/303:
- A **gated, operator-invoked, idempotent, ordered** migration runner — **never** silent auto-apply on server start. Process-start must not be a state-mutating event (preserves determinism/replayability).
- A **recorded, checksummed `schema_version`** so a version number means the same migrations everywhere (tamper-evident).
- A **fail-closed health gate**: when expected migrations are absent or partially applied, the server reports **degraded** and **refuses writes**.
- A `max_depth` clamp + regression-guard on the traversal handler. **Reconciliation (git-verified):** the CTE column-name and `int(decision_id)` fixes were already landed by PR #894, so the Tier-0 traversal packet (002) is a VERIFIED-NO-OP regression-guard plus the one surviving fix (`max_depth` unclamped at `:2023`), **not** a re-fix.
- **No feature packet — including TP-202 — runs until the gate is green.** Writing under wrong-schema assumptions risks irreversible divergence of canonical memory (worse than downtime for an audit-grade store).

Two design parameters are deferred to packet authoring: (Q1) migration history append-only in-DB vs external log; (Q2) read-only-when-degraded vs refuse-all.

### D2 — Operational/security hardening is IN-SCOPE; only cross-plane authority expansion is a Trinity non-goal

The Memory Trinity boundary excludes **cross-plane authority escalation**, not operational hardening. Therefore:
- **IN-SCOPE (fix at source):** the 4 confirmed bugs, the migration/foundation gaps, health-gate honesty, the traversal fix.
- **OPERATOR-DECISION (commit a default-off seam + document):** write-path auth (H-101), write audit log (H-102), rate limiting (H-103), admin-scoping of `fork`/`promote`/`promote_all`. These ship **default-off** because ConPort's threat model assumes a trusted local/network boundary; turning them on is an operator's deployment choice, not a code default. **All such seams target the `:3005` FastMCP surface** that agents actually bind (`.mcp.json`), not the `:3004` HTTP surface the original framing assumed.
- **TRINITY NON-GOAL (document, do not build):** authority/source_surface response labels (single-plane = implicitly canonical); entity-vs-decision relationship-table consolidation; the multi-tenant `user_id` surface (its tables are absent at runtime and tenancy is a cross-plane concern).

### D3 — Reclassifications correcting the original plan

- **Entity-relationship DB FK + CHECK constraints** → **OPERATOR_DECISION**, not a mandatory amendment (app-layer enum enforcement exists; only integrity argument is orphan-edge accumulation). The TP-202 packet text asserting a `metadata` column is **corrected** — the live table has `strength`.
- **Vocabulary divergence** between `entity_relationships` and `decision_relationships` (share 3/6 terms) → **document the intentional split** in TP-109; do **not** force-merge.
- **Typed degradation contract (4a)** → **DEFER** (over-scoped); keep only the trivial dead-logger fix.
- **DCP facade degradation (4b)** → **REFUTED** as already-handled; verify, then no amendment.

## Consequences

**Positive:** feature packets stop targeting nonexistent schema; canonical memory is protected from schema-drift poisoning; security posture is explicit and operator-controlled rather than absent-by-accident; the Trinity boundary is documented so future reviewers don't re-litigate it; the loaded orchestrator DAG (`44452f53`) is untouched (amendments are text-only; Tier-0 and HARDENING load as separate roots).

**Negative / costs:** adds a Tier-0 critical path before the visible feature work; introduces an operator migration step (deliberately — the alternative undermines auditability); default-off seams mean security is not on unless deployed-on (documented, not hidden).

**Residual risk / UNKNOWN:** discovery was cap-bounded (not exhausted); the production 3005/3004 binding and the live-image-vs-HEAD version were not fully reconciled; the traversal endpoint was not `curl`-tested. These must be closed before the §3.3 security verdicts are treated as final.

## Alternatives considered

- **Silent auto-apply migrations on startup** — rejected: makes process-start a state-mutating event, breaks replayability, risks partial-apply in an undefined state (gpt-5.2-validated).
- **Let TP-202 run first** (it writes the one existing table) — rejected: gpt-5.2 closed this door; rows written under pre-foundation assumptions can be invalidated by the traversal/constraint fixes and mask the foundation problem.
- **Treat auth/audit as IN-SCOPE mandatory** — rejected: ConPort's trusted-boundary threat model makes these operator deployment choices; committing them default-off preserves both options.
- **Execute the original plan as approved** — rejected: runtime evidence falsified its premises (the "headline" TP-202 FK fix is moot against an unmigrated DB with a dead reader).

## References

- Evidence dossier: [conport-optimal-coverage-and-hardening-analysis-2026-06-16.md](../../claudedocs/conport-optimal-coverage-and-hardening-analysis-2026-06-16.md)
- Trinity boundary: [adr-memory-trinity-authority-and-interaction-model](adr-memory-trinity-authority-and-interaction-model.md)
- Series: `task-packets/generated/DMX-CONPORT-OPTIMAL/` (orchestrator root `44452f53`)
