---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# PM Plane

Purpose: evidence-first audit, redesign constraints, and deterministic rails for the Dopemux PM/task-management plane.

## Non-negotiables
- No fabrication. If not evidenced, mark `UNKNOWN` and add `Evidence needed: ...`.
- Evidence-first. Load-bearing claims require file+line citations or command evidence.
- Current implementation is source of truth.
- Trinity boundaries are explicit: PM vs Memory vs Search ownership must be called out.

## Pass Workflow (A/B/C)

1. Pass A (`pm-plane/fric-01`)
- Capture Phase 1 evidence in `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`.
- Draft:
- `docs/planes/pm/pm-friction-map.md`
- `docs/planes/pm/signal-vs-noise-analysis.md`
- Create handoff:
- `docs/planes/pm/_handoff/pm-fric-01-handoff.md`

1. Pass B (`pm-plane/fric-02-critique`)
- Tighten the two Phase 1 docs for citation integrity and PM/Memory/Search boundaries.
- Add handoff:
- `docs/planes/pm/_handoff/pm-fric-02-handoff.md`

1. Pass C (`pm-plane/rails-01`)
- Add deterministic verifier rails:
- `scripts/pm_phase1_verify.sh`
- Add harness/evidence note:
- `docs/planes/pm/_evidence/PM-RAILS-01.outputs/test_discovery_plan.txt`
- Keep this README aligned with the workflow and verifier usage.

## Evidence Locations
- Phase 0 evidence: `docs/planes/pm/_evidence/PM-INV-00.outputs/`
- Phase 1 friction evidence: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`
- Phase 1 telemetry evidence: `docs/planes/pm/_evidence/PM-TELEM-01.outputs/`
- Rails notes: `docs/planes/pm/_evidence/PM-RAILS-01.outputs/`
- PM authority evidence bundle: `docs/planes/pm/_evidence/PM-AUTH-01.outputs/`
- PM authority command log: `docs/planes/pm/_evidence/PM-AUTH-01.commands.txt`
- Runtime-truth summaries:
  - `docs/planes/pm/_evidence/task-orchestrator-runtime-truth/`
  - `docs/planes/pm/_evidence/leantime-runtime-truth/`
  - `docs/planes/pm/_evidence/dopecon-bridge-runtime-truth/`
- Handoffs: `docs/planes/pm/_handoff/`

## Current authority and contract set
- `docs/90-adr/adr-index.md`
- `docs/planes/pm/pm-plane-write-adjudication-model.md`
- `docs/planes/pm/pm-plane-write-matrix.md`
- `docs/planes/pm/pm-plane-normalized-tool-surface.md`
- `docs/planes/pm/pm-plane-read-matrix.md`
- `docs/planes/pm/pm-plane-write-surface-policy.md`

## Current supervisor authority packet set

- `docs/05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md`
- `docs/05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-memory-authority-enforcement-packet-2026-04-01.md`

## Verification Commands
- Phase 0 verifier:
```bash
bash scripts/pm_phase0_verify.sh
```
- Phase 1 verifier:
```bash
bash scripts/pm_phase1_verify.sh
```
Verifies: friction evidence bundle, telemetry evidence bundle, and citation presence in Phase 1 docs.

Expected success output:
- `OK: PM Phase 0 verification passed`
- `OK: PM Phase 1 verification passed`
