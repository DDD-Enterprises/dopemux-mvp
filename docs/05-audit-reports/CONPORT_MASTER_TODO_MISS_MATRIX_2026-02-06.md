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

Follow-on deep extraction now adds `4` additional TODO checkpoint tasks from structured `custom_data` status payloads that were not included in the original full-coverage artifact.

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

1. Complete Leantime web installation wizard at `http://localhost:8080`.
2. Create/confirm admin user and generate API token from the completed setup.
3. Valid Leantime API credentials are configured for bridge runtime.
4. `GET /health?deep=1` returns `200` with upstream reachability.
5. `POST /api/tools/list_projects` returns `200` and non-empty project payload.
6. Leantime queue worker failures drop to zero across repeated log windows.

## Secondary Explicit-Task Miss Extraction

A second pass compared ConPort backlog task-line samples to the current master-doc text and found additional explicit tasks that were still underrepresented as first-class todo lines.

Summary:

1. todo samples checked: `25`
2. explicitly covered: `6`
3. secondary misses: `19`

Secondary misses now promoted into master fix scope:

1. `1.1.1: Set up PostgreSQL AGE test environment`
2. `1.2.1: Analyze Context Integration layer`
3. `1.2.2: Document architecture decision`
4. `1.3.1: Create dopemux-core package structure`
5. `1.3.4: Write unit tests for dopemux-core`
6. `2.1.1: Remove ConPort semantic_search MCP tool`
7. `2.1.2: Update docs and add deprecation warnings`
8. `2.2.1: Remove ConPort embedding_service and import from core`
9. `2.2.3: Validate embedding quality and schema`
10. `2.3.1: Refactor Serena ADHD to use ADHDConfigService`
11. `2.3.2: Refactor dope-context ADHD to use ADHDConfigService`
12. `2.3.3: Refactor ConPort ADHD to use ADHDConfigService`
13. `3.1.1: Design and populate conport_integration_links`
14. `3.1.2: Implement bidirectional linking logic`
15. `3.1.3: Create trace_decision_to_code MCP tool`
16. `3.1.4: Write integration tests for knowledge graph`
17. `3.1.5: Validate graph traversal performance`
18. `3.1.6: Document knowledge graph usage`
19. `3.2.1: Integrate dope-context in Serena and add Find Similar command`

Evidence:

- `reports/strict_closure/conport_master_todo_secondary_miss_extract_2026-02-06.json`

## Deep Status-Field Miss Extraction (Custom Data)

A deep pass against ConPort import-bundle `custom_data` values (including nested TODO/BLOCKED status fields) identified additional explicit milestone checkpoints that were still not represented in the active master fix docs.

Summary:

1. raw status records scanned: `646`
2. source mix: `630` progress entries + `16` custom-data status records
3. unique status-task items: `235`
4. uncovered in current master docs: `166`
5. net-new uncovered items vs previous full-coverage artifact: `4`

Newly extracted misses promoted into master fix scope:

1. `week1 checkpoint | Criteria: Functional: Full workflow FOCUSED -> activation -> 15min no activity -> deactivation`
2. `week2 checkpoint | Criteria: macOS Focus Mode reliable across versions`
3. `week3 checkpoint | Criteria: Slack status updates working reliably`
4. `week4 checkpoint final | Criteria: 60% interruption reduction (from 20/day baseline)`

Owner bucket recommendation:

1. Week 1: `ADHD engine + runtime/orchestration`
2. Week 2: `Desktop integration`
3. Week 3: `Notifications/integrations`
4. Week 4: `Product operations + analytics`

Evidence:

- `reports/strict_closure/conport_deep_status_task_extract_2026-02-06.json`
- `docs/05-audit-reports/CONPORT_DEEP_STATUS_TASK_EXTRACT_2026-02-06.md`

Recheck after promoting these 4 items into this matrix:

1. unique status-task items: `235`
2. uncovered in active master docs: `162`
3. net-new uncovered vs prior full-coverage artifact: `0`

Evidence:

- `reports/strict_closure/conport_deep_status_task_recheck_2026-02-06.json`

### Secondary Miss Implementation Map

| Task | Owner bucket | Primary target paths | Verification anchor |
|---|---|---|---|
| `1.1.1: Set up PostgreSQL AGE test environment` | ConPort + Infra | `scripts/deploy/migration/validate_age_pg_compat_stress.py`, `docker/`, `services/registry.yaml` | AGE validator and container health checks |
| `1.2.1: Analyze Context Integration layer` | Dope-Context + Architecture | `services/dope-context/src/`, `services/dopecon-bridge/`, `services/task-orchestrator/` | integration-path ADR update |
| `1.2.2: Document architecture decision` | Docs + Core platform | `docs/90-adr/`, `docs/04-explanation/architecture/` | ADR section completeness check |
| `1.3.1: Create dopemux-core package structure` | Core platform | `src/dopemux/` | import-path consistency + packaging tests |
| `1.3.4: Write unit tests for dopemux-core` | Core platform + QA | `tests/unit/`, `tests/contracts/` | targeted pytest suites |
| `2.1.1: Remove ConPort semantic_search MCP tool` | ConPort + Bridge + Serena | `src/dopemux/mcp/conport_mcp_tools.py`, `services/conport/http_server.py`, `services/dopecon-bridge/main.py`, `services/serena/` | API compatibility shim + deprecation tests |
| `2.1.2: Update docs and add deprecation warnings` | Docs + service owners | `docs/03-reference/`, `docs/02-how-to/`, service READMEs | docs parity and link checks |
| `2.2.1: Remove ConPort embedding_service and import from core` | Dope-Context + ConPort | `services/dope-context/src/embeddings/`, `src/dopemux/embeddings/`, `src/conport/memory_server.py` | shared-embedding import contract tests |
| `2.2.3: Validate embedding quality and schema` | AI/ML + Data | `services/dope-context/src/pipeline/`, `src/dopemux/embeddings/`, `mcp-qdrant` wiring | embedding regression + schema validation |
| `2.3.1: Refactor Serena ADHD to use ADHDConfigService` | Serena + ADHD engine | `services/serena/`, `services/adhd_engine/adhd_config_service.py` | Serena config integration tests |
| `2.3.2: Refactor dope-context ADHD to use ADHDConfigService` | Dope-Context + ADHD engine | `services/dope-context/src/`, `services/adhd_engine/adhd_config_service.py` | config-client contract test |
| `2.3.3: Refactor ConPort ADHD to use ADHDConfigService` | ConPort + ADHD engine | `services/conport/`, `services/adhd_engine/adhd_config_service.py` | config fallback/compat tests |
| `3.1.1: Design and populate conport_integration_links` | Serena intelligence + ConPort | `services/serena/intelligence/schema_manager.py`, `services/serena/intelligence/conport_bridge.py` | table lifecycle + seed validation |
| `3.1.2: Implement bidirectional linking logic` | Serena intelligence + Task-Orchestrator | `services/serena/intelligence/conport_bridge.py`, `src/integrations/sync_manager.py`, `services/task-orchestrator/app/adapters/` | bidirectional sync tests |
| `3.1.3: Create trace_decision_to_code MCP tool` | ConPort MCP + Bridge | `src/dopemux/mcp/`, `services/conport/http_server.py`, `services/dopecon-bridge/main.py` | MCP tool contract test |
| `3.1.4: Write integration tests for knowledge graph` | QA + ConPort + Serena | `tests/integration/`, `services/dddpg/test_kg_integration.py` | end-to-end KG suite |
| `3.1.5: Validate graph traversal performance` | Data + Performance | `services/dope-query/`, `services/dddpg/`, performance harness scripts | traversal latency benchmark |
| `3.1.6: Document knowledge graph usage` | Docs + ConPort owners | `docs/03-reference/`, `docs/04-explanation/` | docs truth + usage walkthrough |
| `3.2.1: Integrate dope-context in Serena and add Find Similar command` | Serena + Dope-Context | `services/serena/claude_context_integration.py`, `services/serena/layer1_validation.py`, `services/dope-context/src/mcp/server.py` | command behavior + UX acceptance tests |

## Coverage Recheck Status

Post-update coverage recheck against the original miss extract now shows explicit representation closure:

1. original miss-extract items: `24`
2. explicitly represented now: `24`
3. still not explicit: `0`

Evidence:

- `reports/strict_closure/conport_master_todo_coverage_recheck_2026-02-06.json`

## Full-Bundle Coverage Follow-On

The targeted miss extraction is now explicitly represented, but a full-bundle sweep across all ConPort TODO/BLOCKED records still shows a larger underrepresented set that needs phased closure.

Evidence:

- `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json`
- `docs/05-audit-reports/CONPORT_FULL_TODO_COVERAGE_MATRIX_2026-02-06.md`
- `docs/05-audit-reports/CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026-02-06.md`
- `docs/05-audit-reports/LITELLM_BLOCKER_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_WORKSTREAM_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/MCP_RESPONSE_BUDGET_VERIFICATION_2026-02-06.md`

## Live Runtime Backlog Coverage Diff (Progress Entries)

Live ConPort runtime extraction (`progress_entries` from `dopemux_knowledge_graph`) has now been compared directly against active master docs.

Summary:

1. unique live backlog items: `134`
2. represented in active master docs: `68`
3. underrepresented in active master docs: `66`

Clustered underrepresented work now includes:

1. `profile_alias_or_residual`: `33`
2. `shield_slack_beta`: `11`
3. `kg_dependency_unification`: `7`
4. `bridge_orchestrator`: `6`
5. `mcp_token_ops`: `4`
6. `conport_persistence`: `1`
7. `other`: `4`

Runtime recheck has already reclassified one persistence item and one MCP-token documentation item as resolved:

- `docs/05-audit-reports/CONPORT_PERSISTENCE_VERIFICATION_2026-02-06.md`
- `docs/best-practices/mcp-token-management.md`
- `reports/strict_closure/mcp_token_management_doc_verification_2026-02-06.json`
- `docs/05-audit-reports/BRIDGE_ORCHESTRATOR_INTEGRATION_VERIFICATION_2026-02-06.md`
- `reports/strict_closure/bridge_orchestrator_integration_verification_2026-02-06.json`

Artifacts:

- `reports/strict_closure/conport_live_progress_backlog_2026-02-06.csv`
- `reports/strict_closure/conport_live_backlog_doc_coverage_2026-02-06.json`
- `reports/strict_closure/conport_live_backlog_underrepresented_matrix_2026-02-06.json`
- `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_UNDERREPRESENTED_MATRIX_2026-02-06.md`
- `reports/strict_closure/conport_live_backlog_true_open_candidates_2026-02-06.json`
- `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_EXECUTION_PACKET_2026-02-06.md`

## Live True-Open Explicit Promotion (Master Doc Closure)

To eliminate remaining wording drift between live backlog and master TODO docs, the full live true-open packet is now promoted into this master matrix as explicit line items.

Summary from delta extraction:

1. Live true-open candidates compared: `25`.
2. Missing in master doc by exact text: `25`.
3. Missing in master doc by canonical phrase: `14`.
4. Closure rule for this wave: explicit line coverage (all 25 listed verbatim).

Promoted live true-open lines:

1. `[kg_dependency_unification | P1] 3.2.2: Test semantic similarity & ADHD disclosure | Duration: 60m | Complexity: 0.6 | Energy: Medium-High | Depends: 3.2.1`
2. `[kg_dependency_unification | P1] 3.2.1: Integrate dope-context in Serena, add Find Similar command | Duration: 60m | Complexity: 0.6 | Energy: Medium-High | Depends: 2.1.2, 2.3.1`
3. `[kg_dependency_unification | P1] 3.1.1: Design & populate conport_integration_links | Duration: 60m | Complexity: 0.8 | Energy: Very High | Depends: 2.2.3`
4. `[kg_dependency_unification | P1] 2.2.3: Validate embedding quality & schema | Duration: 45m | Complexity: 0.6 | Energy: Medium-High | Depends: 2.2.2`
5. `[kg_dependency_unification | P1] 2.2.2: Write & run migration script (re-embed decisions) | Duration: 45m | Complexity: 0.6 | Energy: Medium-High | Depends: 2.2.1`
6. `[kg_dependency_unification | P1] 2.2.1: Remove ConPort embedding_service, import from core | Duration: 30m | Complexity: 0.6 | Energy: Medium-High | Depends: 1.3.2`
7. `[kg_dependency_unification | P1] 2.1.2: Update docs & add deprecation warnings | Duration: 30m | Complexity: 0.4 | Energy: Low-Medium | Depends: 2.1.1`
8. `[shield_slack_beta | P1] Day 19-20: Feedback & Iteration (12-14 hours)`
9. `[shield_slack_beta | P1] Day 9: Notification Batching (3-4 hours)`
10. `[shield_slack_beta | P1] Day 8: Productivity Indicators Deep Dive (6-7 hours)`
11. `[shield_slack_beta | P1] Day 7: Desktop Commander Integration (4-5 hours)`
12. `[shield_slack_beta | P1] Day 6: macOS Focus Mode - AppleScript Implementation (5-6 hours)`
13. `[shield_slack_beta | P1] Day 16-17: Beta Preparation & Recruitment (8-10 hours)`
14. `[shield_slack_beta | P1] Day 18: Beta Deployment (6-8 hours)`
15. `[shield_slack_beta | P1] Day 14-15: Message Triage System (10-12 hours)`
16. `[shield_slack_beta | P1] Day 13: Slack Status Management (4-5 hours)`
17. `[shield_slack_beta | P1] Day 11-12: Slack Client Setup (8-10 hours)`
18. `[shield_slack_beta | P1] Week 3: Slack Integration & Message Triage`
19. `[mcp_token_ops | P2] Monitor MCP servers for edge cases after token limit fixes deployment`
20. `[mcp_token_ops | P2] Test MCP token limit fixes in production: large files (package-lock.json), bulk queries (100 decisions), multi-step Zen analysis`
21. `[mcp_token_ops | P2] Restart Claude Code to load all MCP token limit fixes (dope-context, Serena, ConPort, Zen)`
22. `[other | P2] Day 4: ConPort Integration & Metrics (4-5 hours)`
23. `[other | P2] Day 3: ShieldCoordinator Core Logic (6-7 hours)`
24. `[other | P2] Day 5: Productivity Monitoring & False Positive Detection (5-6 hours)`
25. `[other | P2] Week 1: Core Infrastructure & ADHD Engine Integration`

Supporting artifact:

- `reports/strict_closure/conport_master_live_true_open_delta_2026-02-06.json`

Post-promotion recheck:

1. Live true-open total rechecked: `25`.
2. Missing in master by exact text after promotion: `0`.
3. Exact line coverage status: `closed`.
4. Canonical residual drift after promotion: `8` (wording-level, not line-coverage gaps).

Recheck artifact:

- `reports/strict_closure/conport_master_live_true_open_delta_recheck_2026-02-06.json`
