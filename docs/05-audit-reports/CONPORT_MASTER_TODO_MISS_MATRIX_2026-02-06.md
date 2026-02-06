---
id: CONPORT_MASTER_TODO_MISS_MATRIX_2026_02_06
title: Conport Master Todo Miss Matrix 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Prioritized matrix of pending items mined from ConPort historical snapshots that were not clearly represented in the active master fix ledger.
---
# ConPort Master TODO Miss Matrix (2026-02-06)

## Scope

This matrix is derived from:

- `reports/strict_closure/conport_master_todo_miss_extract_2026-02-06.json`
- all five available ConPort import bundles

It captures the `24` pending items identified as underrepresented in the active master fix plan.

## Prioritized Miss Matrix

| Item | Priority | Domain | Recommended owner bucket |
|---|---|---|---|
| `1.1.2: Run concurrent operations stress test` | P1 | Data/DB reliability | ConPort + Infra |
| `1.1.3: Validate AGE/PG compatibility` | P1 | Data/DB compatibility | ConPort + Infra |
| `1.3.2: Extract VoyageEmbedder & QdrantClient singletons` | P1 | Architecture consolidation | Core platform |
| `1.3.3: Create ADHDConfigService wrapper` | P1 | Configuration centralization | ADHD engine + Core platform |
| `2.1.4: Time window checker` | P2 | UX heuristics | UI/experience |
| `2.2.2: Suggestion strategy logic` | P2 | UX heuristics | UI/experience |
| `3.2.2: Graceful shutdown` | P1 | Runtime resilience | Runtime/orchestration |
| `4.1.2: Enhance statusline display` | P2 | UX/statusline | CLI/TUI UX |
| `4.6.3: Polish & UX improvements` | P2 | UX polish | CLI/TUI/Web UX |
| `Day 11-12: Slack Client Setup` | P1 | Integration | Notifications/integrations |
| `Day 13: Slack Status Management` | P1 | Integration | Notifications/integrations |
| `Day 14-15: Message Triage System` | P1 | Integration + workflow | Notifications/integrations |
| `Day 16-17: Beta Preparation & Recruitment` | P2 | Release ops | Product operations |
| `Day 18: Beta Deployment` | P1 | Release ops | Product operations |
| `Day 19-20: Feedback & Iteration` | P2 | Release feedback loop | Product operations |
| `Day 3: ShieldCoordinator Core Logic` | P1 | Core runtime logic | ADHD engine + runtime |
| `Day 6: macOS Focus Mode - AppleScript Implementation` | P1 | Platform integration | Desktop integration |
| `Day 8: Productivity Indicators Deep Dive` | P2 | Analytics/metrics | UX + analytics |
| `Day 9: Notification Batching` | P2 | Integration optimization | Notifications/integrations |
| `Task 4.3: Profile Management Commands` | P2 | CLI UX | Core CLI |
| `Task 4.6: Documentation & Polish` | P2 | Documentation parity | Docs + service owners |
| `Week 2: macOS Integration & Window Management` | P1 | Platform integration | Desktop integration |
| `Week 4: Beta Testing & Iteration` | P2 | Validation | Product operations |
| `Leantime manual setup completion` | P1 | External dependency integration | Leantime bridge |

## Immediate Integrations Into Master Fix Stream

1. Treat all P1 items above as in-scope for active wave closure.
2. Promote `Leantime manual setup completion` to explicit dependency gate in release readiness.
3. Group Slack, macOS, and ShieldCoordinator items into a single integration sprint track with dedicated verification scenarios.
4. Keep P2 items in this same push per locked policy (no deferred backlog for this epic run).

## Wave Status Update (2026-02-06)

Completed in this wave with evidence:

1. `1.1.2: Run concurrent operations stress test`
2. `1.1.3: Validate AGE/PG compatibility`

Evidence:

- `reports/strict_closure/age_pg_compat_stress_2026-02-06.json`
- `docs/05-audit-reports/AGE_PG_COMPAT_STRESS_2026-02-06.md`

## Remaining P1 Blocker (Evidenced)

1. `Leantime manual setup completion` remains open.
2. Bridge liveness is up, but upstream readiness is not:
   - `GET /health?deep=1` returns `503` (`leantime=unreachable`)
   - `POST /api/tools/list_projects` returns `502` (all method candidates failed)
   - `LEANTIME_API_TOKEN` is currently unset in bridge runtime
3. Supporting container evidence shows persistent Leantime queue failures and redirect-only traffic patterns.

Evidence:

- `reports/strict_closure/leantime_bridge_readiness_2026-02-06.json`
- `docs/05-audit-reports/LEANTIME_BRIDGE_READINESS_2026-02-06.md`

## Leantime Close Criteria

1. Valid Leantime API credentials are configured for bridge runtime.
2. `GET /health?deep=1` returns `200` with upstream reachability.
3. `POST /api/tools/list_projects` returns `200` and non-empty project payload.
4. Leantime queue worker failures drop to zero across repeated log windows.
