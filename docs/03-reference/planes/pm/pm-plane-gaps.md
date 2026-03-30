---
id: PM_PLANE_GAPS
title: Pm Plane Gaps
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Pm Plane gaps (Phase 0) with path-line evidence only.
---
# PM Plane Gaps (Phase 0)

Status: evidence locked.

## Severity Rubric
- P0: state trustworthiness or auditability break.
- P1: persistent drift/risk requiring Phase 1 follow-up.
- P2: implementation/documentation mismatch with contained blast radius.
- P3: operational hygiene issue.

## Gap Table

| Severity | Gap | Impact | Evidence | Phase 0 disposition |
|---|---|---|---|---|
| P0 | Decision traceability gap in scoped taskmaster runtime | Scoped taskmaster runtime files do not show concrete decision-link linkage implementation; search returns only a descriptive comment. | `docs/planes/pm/_evidence/PM-INV-00.outputs/54_taskmaster_traceability_rg.txt.nl.txt:L1-L1`; `services/taskmaster/server.py:L52-L52`; `services/taskmaster/bridge_adapter.py:L67-L90` | Documented as confirmed gap; defer implementation work to Phase 1. |
| P1 | Task status model split across PM surfaces | Different status vocabularies are active (`TaskStatus` enum values vs string statuses like `TODO/DONE`), increasing cross-surface drift risk. \| `services/task-orchestrator/task_orchestrator/models.py:L13-L22`; `services/taskmaster/bridge_adapter.py:L67-L70`; `services/taskmaster/bridge_adapter.py:L288-L310` | Documented; no normalization work in Phase 0. |
| P1 | Expected taskmaster files missing (`models.py`, `main.py`) \| Missing expected files reduce deterministic entrypoint/model discovery in taskmaster scope. \| `docs/planes/pm/_evidence/PM-INV-00.outputs/55_expected_presence_check.nl.txt:L2-L4`; `docs/planes/pm/_evidence/PM-INV-00.outputs/21_taskmaster_files.txt.nl.txt:L1-L10` | Documented as unknown/missing for retargeting. |
| P1 | ADR truth-split risk from ADR-207 naming multiplex | Multiple `ADR-207-*` files exist (main + appendices/session/plan), so references to “ADR-207” without suffix can be ambiguous. \| `docs/planes/pm/_evidence/PM-INV-00.outputs/52_adr_name_truthsplit_rg.txt.nl.txt:L5-L5`; `docs/planes/pm/_evidence/PM-INV-00.outputs/52_adr_name_truthsplit_rg.txt.nl.txt:L31-L37`; `docs/planes/pm/_evidence/PM-INV-00.outputs/52_adr_name_truthsplit_rg.txt.nl.txt:L39-L41` | Documented; require explicit ADR file naming in future packets. |
| P2 | `RedisStreamsAdapter` behavior is local fan-out when disconnected \| Adapter named for Redis Streams still dispatches to in-process subscriptions even when disconnected; persistence semantics are unclear from scoped file alone. \| `src/dopemux/event_bus.py:L127-L156` | Documented as runtime semantics gap for follow-up audit. |
| P3 | Tooling gap (rg) | No tooling gap detected in this run; `rg` is installed and deterministic search completed with exit `0`. \| `docs/planes/pm/_evidence/PM-INV-00.outputs/56_rg_check.nl.txt:L1-L7`; `docs/planes/pm/_evidence/PM-INV-00.outputs/50_search_rg.exit.txt:L1-L1` | Closed for Phase 0 (not a blocker). |

## Decision Traceability Status (Required)

Status: **gap present** for scoped taskmaster runtime surfaces (implementation not evidenced, comment-only hit).

Evidence:
- `docs/planes/pm/_evidence/PM-INV-00.outputs/54_taskmaster_traceability_rg.txt.nl.txt:L1-L1`
- `services/taskmaster/server.py:L52-L52`
- `docs/planes/pm/_evidence/PM-INV-00.outputs/53_core_surface_traceability_rg.txt.nl.txt:L1-L2`

## Unknown or Missing

| Expectation | Search/Check artifact | Result | Why it matters |
|---|---|---|---|
| `services/taskmaster/models.py` exists \| `55_expected_presence_check.nl.txt` \| Missing \| No scoped canonical task schema file for taskmaster. (`docs/planes/pm/_evidence/PM-INV-00.outputs/55_expected_presence_check.nl.txt:L2-L2`) |
| `services/taskmaster/main.py` exists \| `55_expected_presence_check.nl.txt` \| Missing \| No separate scoped main entrypoint file for taskmaster. (`docs/planes/pm/_evidence/PM-INV-00.outputs/55_expected_presence_check.nl.txt:L4-L4`) |
| Runtime taskmaster decision-link functions exist (`linked_item`, `link_conport_items`, `log_progress`) \| `54_taskmaster_traceability_rg.txt` \| Not found in scoped runtime files (comment-only hit). \| Traceability from task events to decisions cannot be proven from scoped taskmaster files. (`docs/planes/pm/_evidence/PM-INV-00.outputs/54_taskmaster_traceability_rg.txt.nl.txt:L1-L1`) |
