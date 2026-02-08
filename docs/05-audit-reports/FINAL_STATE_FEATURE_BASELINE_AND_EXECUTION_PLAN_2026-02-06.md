---
id: FINAL_STATE_FEATURE_BASELINE_AND_EXECUTION_PLAN_2026_02_06
title: Final State Feature Baseline and Execution Plan 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Repository-wide verified baseline of components, features, integrations, UI/UX surfaces, and a phased production-readiness execution plan.
---
# Final State Feature Baseline and Execution Plan (2026-02-06)

## Scope

This report reconciles:

1. `docs/04-explanation/history/DESIGN_EVOLUTION_2026.md`
2. `docs/04-explanation/history/PROJECT_ARCHAEOLOGY_REPORT.md`
3. `docs/04-explanation/history/UNBUILT_FEATURES_AND_ROADMAP.md`
4. Current code state in `services/`, `src/dopemux/`, `docker/mcp-servers/`, and UI directories
5. Current architecture contracts in `services/registry.yaml`, `compose.yml`, and `docker-compose.smoke.yml`
6. Historical service master histories in `docs/archive/services/history/`

This is a verified baseline, not a design-only document.

## Evidence Artifacts

Generated during this pass:

- `reports/service_inventory_snapshot.json`
- `reports/agents_status_snapshot.json`
- `reports/component_feature_inventory.json`
- `reports/component_code_metrics.json`
- `reports/service_interaction_signals.json`
- `reports/compose_service_inventory.json`
- `reports/service_maturity_signals.json`
- `reports/docs_unbuilt_signal_index.json`
- `reports/master_history_headings.json`
- `reports/master_history_status_signals.json`
- `reports/strict_closure/source_graph.json`
- `reports/strict_closure/claim_catalog.json`
- `reports/strict_closure/component_scorecards.json`
- `reports/strict_closure/conport_real_import_integrity_2026-02-06.json`
- `reports/strict_closure/conport_backlog_extract_2026-02-06.json`
- `reports/strict_closure/conport_master_todo_miss_extract_2026-02-06.json`
- `reports/strict_closure/conport_master_todo_secondary_miss_extract_2026-02-06.json`
- `reports/strict_closure/conport_master_todo_coverage_recheck_2026-02-06.json`
- `reports/strict_closure/conport_master_live_true_open_delta_2026-02-06.json`
- `reports/strict_closure/conport_master_live_true_open_delta_recheck_2026-02-06.json`
- `reports/strict_closure/kg_dependency_unification_verification_2026-02-06.json`
- `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json`
- `reports/strict_closure/litellm_blocker_verification_2026-02-06.json`
- `reports/strict_closure/profile_workstream_verification_2026-02-06.json`
- `reports/strict_closure/mcp_response_budget_verification_2026-02-06.json`
- `reports/strict_closure/file_pattern_analyzer_verification_2026-02-06.json`
- `reports/strict_closure/profile_detector_threshold_tests_verification_2026-02-06.json`
- `reports/strict_closure/profile_config_swap_restart_verification_2026-02-06.json`
- `reports/strict_closure/profile_error_recovery_rollback_verification_2026-02-06.json`
- `reports/strict_closure/profile_switch_command_verification_2026-02-06.json`
- `reports/strict_closure/profile_switch_time_optimization_verification_2026-02-06.json`
- `reports/strict_closure/profile_switch_integration_tests_verification_2026-02-06.json`
- `reports/strict_closure/profile_current_detection_verification_2026-02-06.json`
- `reports/strict_closure/auto_detection_service_verification_2026-02-06.json`
- `reports/strict_closure/profile_management_commands_verification_2026-02-06.json`
- `reports/strict_closure/profile_analytics_verification_2026-02-06.json`
- `reports/strict_closure/dope_context_decision_auto_index_unified_search_verification_2026-02-06.json`
- `reports/strict_closure/profile_optimization_suggestions_verification_2026-02-06.json`
- `reports/strict_closure/profile_usage_analysis_and_init_wizard_verification_2026-02-06.json`
- `reports/strict_closure/profile_documentation_completion_verification_2026-02-06.json`
- `reports/strict_closure/profile_week2_integration_testing_verification_2026-02-06.json`
- `reports/strict_closure/conport_relationship_backfill_2026-02-06.json`
- `reports/strict_closure/age_pg_compat_stress_2026-02-06.json`
- `reports/strict_closure/leantime_bridge_readiness_2026-02-06.json`
- `reports/strict_closure/leantime_bridge_readiness_2026-02-07.json`
- `reports/strict_closure/leantime_route_error_contract_verification_2026-02-07.json`
- `reports/strict_closure/leantime_api_key_automation_verification_2026-02-08.json`
- `reports/strict_closure/conport_live_progress_backlog_2026-02-07.csv`
- `reports/strict_closure/conport_live_backlog_delta_2026-02-07.json`
- `reports/strict_closure/conport_live_progress_backlog_2026-02-08.csv`
- `reports/strict_closure/conport_live_backlog_delta_2026-02-08.json`
- `reports/strict_closure/semantic_search_reference_inventory_2026-02-07.json`
- `reports/strict_closure/runtime_stability_hotfixes_2026-02-08.json`
- `reports/strict_closure/history_docs_link_integrity_2026-02-08.json`
- `docs/05-audit-reports/SEMANTIC_SEARCH_REFERENCE_INVENTORY_2026-02-07.md`
- `docs/05-audit-reports/RUNTIME_STABILITY_HOTFIXES_2026-02-08.md`
- `docs/05-audit-reports/CONPORT_REAL_IMPORT_INTEGRITY_2026-02-06.md`
- `docs/05-audit-reports/CONPORT_MASTER_TODO_MISS_MATRIX_2026-02-06.md`
- `docs/05-audit-reports/CONPORT_FULL_TODO_COVERAGE_MATRIX_2026-02-06.md`
- `docs/05-audit-reports/CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026-02-06.md`
- `docs/05-audit-reports/KG_DEPENDENCY_UNIFICATION_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/LITELLM_BLOCKER_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_WORKSTREAM_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/MCP_RESPONSE_BUDGET_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/FILE_PATTERN_ANALYZER_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_DETECTOR_THRESHOLD_TESTS_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_CONFIG_SWAP_RESTART_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_ERROR_RECOVERY_ROLLBACK_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_SWITCH_COMMAND_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_SWITCH_TIME_OPTIMIZATION_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_SWITCH_INTEGRATION_TESTS_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_CURRENT_DETECTION_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/AUTO_DETECTION_SERVICE_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_MANAGEMENT_COMMANDS_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_ANALYTICS_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/DOPE_CONTEXT_DECISION_AUTO_INDEX_UNIFIED_SEARCH_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_OPTIMIZATION_SUGGESTIONS_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_USAGE_ANALYSIS_AND_INIT_WIZARD_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_DOCUMENTATION_COMPLETION_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/PROFILE_WEEK2_INTEGRATION_TESTING_VERIFICATION_2026-02-06.md`
- `docs/05-audit-reports/AGE_PG_COMPAT_STRESS_2026-02-06.md`
- `docs/05-audit-reports/LEANTIME_BRIDGE_READINESS_2026-02-06.md`

Executed verification checks (latest pass on 2026-02-06):

- `pytest -q --no-cov tests/arch/test_registry_compose_alignment.py` (passes)
- `pytest -q --no-cov services/agents/test_tool_orchestrator.py services/agents/test_cognitive_guardian_kg.py` (passes)
- `pytest -q --no-cov tests/unit/test_taskmaster_bridge.py::TestTaskMasterMCPClient::test_parse_prd_failure` (passes)
- `pytest -q --no-cov tests/unit/test_ui_dashboard_backend_api.py tests/unit/test_pattern_correlation_engine.py tests/unit/test_unified_complexity_coordinator.py` (passes)
- `pytest -q --no-cov tests/shared/test_dopecon_bridge_client.py` (passes)
- `pytest -q --no-cov tests/unit/test_leantime_bridge.py` (passes)
- `pytest -q --no-cov tests/unit/test_profile_cli_registration.py` (passes)
- `pytest -q --no-cov tests/unit/test_profile_usage_analysis_command.py tests/unit/test_profile_analyzer.py tests/unit/test_profile_wizard.py` (passes)
- `pytest -q --no-cov tests/test_mobile_runtime.py` (passes)
- `PYTHONPATH=/Users/hue/code/dopemux-mvp/services/dope-context pytest -q --no-cov -k 'not trio' services/dope-context/tests/test_mcp_server.py` (passes)
- `scripts/verify_profile_week2_integration.sh` (passes)
- `npm --prefix ui-dashboard run build` (passes)
- `python scripts/deploy/migration/validate_age_pg_compat_stress.py ...` (passes via `mcp-conport` runtime with `overall_ok=true`)
- `docker exec dopemux-mcp-leantime-bridge ... /health?deep=1` and `/api/tools/list_projects` (both return `200`; upstream install/token gate closed in current environment)
- `pytest -q --no-cov tests/unit/test_adhd_engine_settings_contract.py` (passes)
- `pytest -q --no-cov tests/unit/test_task_orchestrator_workflow_api.py tests/unit/test_task_orchestrator_workflow_models.py tests/unit/test_task_orchestrator_workflow_service.py tests/unit/test_cli_workflow_commands.py` (passes)
- `pytest -q --no-cov tests/unit/test_adhd_engine_task_orchestrator_url.py` (passes)
- `docker compose up -d --build --force-recreate adhd-engine` (container healthy, startup verified)
- `docker compose up -d --build --force-recreate genetic-agent` (container healthy, startup verified)

## Executive Findings

1. Repository-scale drift is real: code, docs, registry, compose, and tests disagree in multiple critical places.
2. The three archaeology docs are directionally useful but contain stale assertions.
3. Core orchestration/event/memory components exist and are non-trivial; immediate contract/test/build blockers found in this pass were remediated, but broader architecture and docs parity work remains.
4. ADR-197 Stage-1/Stage-2 workflow is now implemented across runtime API, coordinator operations, persistence, and CLI commands; remaining work is production hardening and deeper integration coverage.
5. The largest systemic risk is governance: no current single source of truth is actually enforced end-to-end despite docs claiming that it is.
6. Leantime bridge readiness blocker was closed in this wave: deep health and project-list calls now return `200`, and setup/token automation is verified.

## Claim Verification Matrix

| Claim | Source | Verification | Evidence | Conclusion |
|---|---|---|---|---|
| 6/7 infrastructure agents are missing | `UNBUILT_FEATURES_AND_ROADMAP.md` | False | Files exist for all 7 modules in `services/agents/` | Implementation exists; readiness is mixed, not missing |
| Auto-resume is unbuilt | `UNBUILT_FEATURES_AND_ROADMAP.md` | False/Partial | Orphan detection + resume in `src/dopemux/instance_manager.py`, `src/dopemux/worktree_recovery.py`, `src/dopemux/cli.py` | Feature exists; needs stabilization/testing |
| Task-Orchestrator event adapters are unbuilt | `UNBUILT_FEATURES_AND_ROADMAP.md` | False | Event handlers/adapters present in `services/task-orchestrator/app/services/enhanced_orchestrator.py` and `services/task-orchestrator/app/adapters/conport_insight_publisher.py` | Implemented at code level |
| Idea -> Epic workflow is missing | `UNBUILT_FEATURES_AND_ROADMAP.md` | False | Runtime and CLI references now exist in `services/task-orchestrator/app/main.py`, `services/task-orchestrator/app/services/workflow_service.py`, `services/task-orchestrator/app/services/workflow_store.py`, `services/task-orchestrator/app/models/workflow.py`, `src/dopemux/cli.py` | Reclassify as Implemented with remaining hardening backlog |
| Zen MCP server was deleted (root cause for stalled features) | `PROJECT_ARCHAEOLOGY_REPORT.md` | Partial | `docker/mcp-servers/zen` removed; commit indicates rename to PAL (`refactor: rename zen MCP server to PAL`) | Renamed/rebased, not purely removed; migration incomplete |
| Persona command system was deleted | `PROJECT_ARCHAEOLOGY_REPORT.md` | True | `git log --diff-filter=D --summary -- .claude/commands` shows bulk deletions | Deterministic prompt library was reduced significantly |
| DopeconBridge is event-bus centric | `DESIGN_EVOLUTION_2026.md` | True | Redis Streams event bus implementation in `services/dopecon-bridge/event_bus.py` and usage in integrations/tests | Correct |
| Task-Orchestrator is central PM-plane coordinator | `DESIGN_EVOLUTION_2026.md` | Mostly true | Large codebase and event integration exist; Leantime/ConPort adapters present | Correct directionally; integration quality varies |
| WMA guarantees <200ms capture and instant recovery | `DESIGN_EVOLUTION_2026.md` | Unverified | Performance claims documented, but no current benchmark evidence in this pass | Needs benchmark suite and SLO validation |
| Registry is the single source of truth | `docs/03-reference/ports-and-registry-truth.md` | Partial | `tests/arch/test_registry_compose_alignment.py` now passes for smoke stack after remediation | Smoke contract repaired; full-stack canonicalization still pending |

## Complete Component Baseline

### Runtime and Orchestration Core

| Component | Current Capability State | Integration State | Readiness |
|---|---|---|---|
| `src/dopemux` | Large CLI/runtime/worktree/orchestration surface | Connected to many services and tmux flows | Medium (feature-rich, low measured coverage) |
| `services/dopecon-bridge` | Redis Streams bus, integration emitters, event routing, tests present | Core hub for cross-service async flow | Medium-High |
| `services/task-orchestrator` | Dependency analysis, event handling, adapters, coordination engines | Strong ties to bridge + ConPort + Leantime semantics | Medium-High |
| `services/adhd_engine` | Cognitive/energy/attention/break logic, multiple domains | Integrated with event flows and external services | Medium |
| `services/serena` | Large intelligence stack, MCP server, code intelligence surfaces | Broad integration references | Medium |
| `services/working-memory-assistant` | WMA API + dope-memory mode (`dope_memory_main.py`) | Integrates with ADHD/ConPort/Serena, smoke service path exists | Medium |
| `services/dope-query` / `services/conport` | KG/context capabilities split across naming eras | Naming and ownership drift with `conport` compose naming | Medium |
| `services/dope-context` | Context indexing/search services | Linked to bridge + multiple AI services | Medium |
| `services/dddpg` | Supporting data/query functionality | Limited standalone surface, referenced by query stack | Medium-Low |
| `services/session-manager` | TUI and session coordination runtime | Integrates with ConPort + agents + ADHD concepts | Medium |

### Cognitive and Agent Layers

| Component | Current Capability State | Integration State | Readiness |
|---|---|---|---|
| `services/agents` | All 7 agent modules present | Many simulation/placeholder paths; tests failing | Low-Medium |
| `services/task-router` | Task-energy/attention matching logic | Weak packaging and no visible test suite | Low-Medium |
| `services/claude_brain` | Cognitive orchestration and adaptation modules | Limited operational proof in this pass | Low-Medium |
| `services/ml-risk-assessment` | Extracted risk logic exists | Not clearly exposed as hardened service | Low-Medium |
| `services/ml-predictions` | Prediction API code present | Minimal proof of integration hardening | Low-Medium |
| `services/genetic_agent` | Large AI-agent codebase and adapters | PAL/Serena/DopeContext/ConPort references | Medium-Low |
| `services/dopemux-gpt-researcher` | Research API pipeline + tests | Integrated but not fully production-validated | Medium-Low |
| `services/intelligence` | Supporting modules | Sparse operational scaffolding | Low |
| `services/complexity_coordinator` | Minimal footprint | Low signal of operationalization | Low |
| `services/session-intelligence` + `services/session_intelligence` | Duplicate naming families | Governance and ownership ambiguity | Low |
| `services/taskmaster` + `services/taskmaster-mcp-client` | Skeletons and adapters | Unit test failure in bridge path | Low |

### Environment, UX, and Notifications

| Component | Current Capability State | Integration State | Readiness |
|---|---|---|---|
| `services/activity-capture` | API and Docker wiring present | No visible test coverage in this pass | Medium-Low |
| `services/workspace-watcher` | Workspace monitoring code | No visible test coverage in this pass | Medium-Low |
| `services/voice-commands` | API and Zen/PAL-style decomposition references | No visible test coverage in this pass | Low-Medium |
| `services/adhd-dashboard` | Dashboard service code present | Not in canonical compose set currently | Medium-Low |
| `services/adhd-notifier` | Notification routing logic exists | Partial integration visibility | Medium-Low |
| `services/monitoring-dashboard` | Unified monitoring API/UI service | Integration and alerting logic present | Medium |
| `services/monitoring` | Monitoring support modules | Operational claims need objective checks | Medium-Low |
| `services/conport_kg_ui` | UI/TUI-oriented KG explorer assets | Sparse service-level hardening evidence | Low-Medium |
| `services/slack-integration` | Script-level integration | Not containerized/hardened | Low |
| `services/mcp-client` | MCP client code path | Fragmented service ownership | Low |

### UI Surfaces (Component, Interaction, UX)

| Surface | State | Evidence | Risk |
|---|---|---|---|
| Terminal statusline and CLI UX | Implemented | Extensive CLI command groups in `src/dopemux/cli.py` and `src/dopemux/tmux/cli.py` | Complexity and low test confidence |
| Textual dashboard (core) | Implemented prototype | `src/dopemux/ui/dashboard.py` | Not validated as default production surface |
| Session manager Textual TUI | Implemented | `services/session-manager/tui/main.py` | Deployment/readiness not unified |
| Monitoring dashboard API/UI | Implemented | `services/monitoring-dashboard/server.py` | Needs production SLO validation |
| React ultra dashboard | Build restored | `npm --prefix ui-dashboard run build` passes after entrypoint/dependency/code fixes | Still needs production data integration and UX hardening |
| UI dashboard backend | Deterministic fallback + live pull adapters | `ui-dashboard-backend/app.py` now supports ADHD/Task-Orchestrator pull with explicit source metadata | Partially integrated (no event-stream push yet) |

### Compose and Infrastructure Components (Not Fully Represented in `services/` Runtime Taxonomy)

| Component | Source of truth today | State | Risk |
|---|---|---|---|
| `postgres` | registry + compose | Active infrastructure dependency | Smoke-stack port alignment fixed; multi-compose alias drift remains |
| `redis` / `redis-primary` / `redis-events` | registry + compose aliases | Multiple naming variants in compose | Naming and topology ambiguity |
| `qdrant` / `mcp-qdrant` | registry + compose aliases | Active vector infrastructure | Smoke-stack host/container alignment fixed; alias governance still needed |
| `pal` (Zen successor) | compose + `docker/mcp-servers/pal` | Active but migration-incomplete ecosystem | Residual stale Zen references |
| `exa` | registry + compose | Present and referenced | Registry/compose smoke inclusion inconsistency |
| `litellm` | registry + compose | Present and referenced | Intentionally excluded from smoke baseline; still needs explicit contract coverage in broader stack tests |
| `desktop-commander` | registry + compose | Present | Needs consistent contract tests |
| `leantime-bridge` | registry + compose | Present | Workflow-stage integration not complete |
| `gptr-mcp` | compose-only naming | Present in compose but not registry canonical list | Governance drift |

### Historical Components and Archaeology-Validated Changes

| Artifact | Verified historical state | Current implication |
|---|---|---|
| `docker/mcp-servers/zen` | Removed by rename commit to PAL | Documentation and code still contain stale `zen` references |
| `.claude/commands/*` command library | Bulk deletion verified in git history | Deterministic prompt behaviors were reduced; only a small subset remains |
| Master history docs under `docs/archive/services/history` | Present and rich, but not correctly linked from history index doc | Knowledge exists but is partially disconnected from current navigation |

## Interaction Baseline (Verified)

### Primary Control and Data Flows

1. **Event Flow**: Services publish/consume through DopeconBridge Redis Streams (`dopemux:events`).
2. **Coordination Flow**: Task-Orchestrator subscribes to bridge events and writes updates/insights via ConPort adapters.
3. **Cognitive Flow**: ADHD Engine and Serena feed state/recommendations into orchestration and UI surfaces.
4. **Memory Flow**: Working Memory Assistant and dope-memory mode preserve/recover context and integrate with ADHD/ConPort.
5. **PM Flow**: Leantime bridge paths exist, but stage-1/2 pipeline semantics are not fully implemented in runtime.

### Critical Contract Drift

1. **Registry vs Compose**: `services/registry.yaml` and `compose.yml` diverge materially.
2. **Naming Drift**: `dope-query` vs `conport`, `adhd-engine` vs `adhd_engine`, `zen` vs `pal`.
3. **Port Drift**: Smoke-stack mismatches were fixed in this pass; broader multi-compose drift remains.
4. **Architecture Doc Drift**: ADR-207 body is now restored; remaining drift is
   cross-doc link integrity and stale references in dependent architecture docs.

## Additional Gaps Not Fully Captured in the 3 Input Files

1. History-doc link integrity recheck now passes for the three archaeology docs
   (`DESIGN_EVOLUTION_2026.md`, `PROJECT_ARCHAEOLOGY_REPORT.md`,
   `UNBUILT_FEATURES_AND_ROADMAP.md`); keep link checks in ongoing parity gates
   (`reports/strict_closure/history_docs_link_integrity_2026-02-08.json`).
2. `ui-dashboard-backend` now provides deterministic fallback plus optional live pull integration, but still lacks an event-stream push channel.
3. Coverage policy (`fail-under=80`) still blocks targeted verification unless `--no-cov` is used.
4. Multiple service directories have minimal scaffolding and no tests, but remain present in architecture narratives.
5. First non-dry-run ConPort historical import surfaced schema-shape drift (`ag_catalog` assumptions vs live `public` tables); importer and backfill hardening are now in place and verified for one selected bundle.
6. Full import/backfill replay across remaining exported historical bundles is still pending a dedupe/merge policy decision (avoid duplicating historical records in active runtime DB).
7. Historical ConPort backlog extraction surfaced additional unresolved work (132 TODO, 1 BLOCKED) not yet fully reflected in the active prioritized gap register.
8. Leantime bridge deep integration is now operational (`/health?deep=1` and `/api/tools/list_projects` return `200`), with `LEANTIME_API_TOKEN` wired in runtime.
9. Serena HTTP API had host-specific path coupling (`/Users/hue/code/dopemux-mvp`) in runtime endpoint code; this was fixed in current wave, but explicit contract tests for workspace-path resolution across container/host runtimes are still missing.
10. New deterministic capture client module (`src/dopemux/memory/capture_client.py`) is present but not yet wired as the default ingress in CLI/plugin/MCP capture surfaces.
11. Capture client executes schema bootstrap (`executescript`) on every emit, creating avoidable per-event overhead risk against WMA capture latency targets.
12. Capture client contract coverage is incomplete (mode precedence, fail-closed repo resolution, redactor/schema dependency failure modes, event-stream toggle behavior).

## Resolved In Current Wave

1. ConPort relationship restoration reached full parity for selected bundle (`111/111` `context_links` -> `entity_relationships`).
2. AGE/PG compatibility and concurrency stress validation completed with `overall_ok=true` and zero query failures.
3. AGE extension registration drift was fixed (`CREATE EXTENSION age`) and validated (`extversion 1.6.0`).
4. Profile CLI command-shadowing defect was fixed by unifying profile-group registration; `profile apply`, `profile current`, `profile create`, `profile copy`, `profile edit`, `profile delete`, and top-level `switch` are now exposed with command-registration test coverage, and manual switches now log telemetry as best-effort.
5. Shared MCP response-budget utility is now implemented and integrated in Serena + GPT-Researcher MCP servers with unit test coverage.
6. Serena HTTP API workspace resolution is now runtime-safe (env/cwd based) and no longer pinned to host-local path assumptions:
   `services/serena/http_server.py` (`fix(serena): remove hardcoded workspace path in http api`, commit `6a2451cc`).
7. ADHD engine runtime health recheck after settings-contract hotfix shows sustained healthy state with successful `/health` probes and Dopecon bridge reads (`dopemux-mvp-adhd-engine-1`).

## ConPort Backlog Misses Extracted Into Master Fix Scope

Source: `reports/strict_closure/conport_backlog_extract_2026-02-06.json` (from historical SQLite snapshot import bundle).

1. Historical BLOCKED LiteLLM DB dependency from ConPort backlog was runtime-reverified and is now stale/resolved:
   `reports/strict_closure/litellm_blocker_verification_2026-02-06.json`.
2. Legacy architecture-consolidation epic backlog remains unresolved:
   `EPIC: Architecture Consolidation - Shared Infrastructure Layer | 3 phases, 27 tasks, 24h total | P0-P2 priorities`.
3. Legacy profile/automation epics are now represented in active runtime and compatibility module surfaces:
   profile manager implementation epic, auto-detection engine epic, profile switching epic, UX integration epic.
4. Knowledge-graph integration backlog still open in historical queue:
   `conport_integration_links`, bidirectional linking, `trace_decision_to_code` MCP tool, and traversal performance validation.
5. Historical dependency-unification backlog still open:
   remove duplicated semantic-search paths, centralize ADHD config service, and complete migration test coverage around those changes.

Secondary extract: `reports/strict_closure/conport_master_todo_miss_extract_2026-02-06.json`.

1. Unique pending items mined from all export bundles: 231 (230 TODO, 1 BLOCKED).
2. Coverage diff against this master doc: 24 pending items were not represented clearly enough in the active plan text.
3. Missed clusters now explicitly in scope:
   AGE/PG stress + compatibility validation tasks, Slack client/status/triage workflow tasks, macOS focus/window-management integration tasks, beta-prep/recruitment/deployment tasks, and Leantime readiness automation/regression coverage tasks.
4. Normalized priority matrix for the 24 underrepresented items:
   `docs/05-audit-reports/CONPORT_MASTER_TODO_MISS_MATRIX_2026-02-06.md`.
5. Secondary explicit-task-line extraction against current master docs surfaced `19` additional underrepresented implementation tasks from historical TODO samples (core package extraction, semantic/embedding deprecation path, ADHDConfigService rollouts, KG link/tool/test/perf/documentation tasks):
   `reports/strict_closure/conport_master_todo_secondary_miss_extract_2026-02-06.json`.
6. Coverage recheck confirms the original `24` miss-extract items are now explicitly represented in master docs (`24/24` closure):
   `reports/strict_closure/conport_master_todo_coverage_recheck_2026-02-06.json`.
7. Full-bundle ConPort TODO/BLOCKED coverage extraction across all available import bundles shows `231` unique pending items with `167` still underrepresented in current master docs:
   `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json`.
8. First execution packet for the underrepresented set is now materialized with owner buckets and verification anchors for the top `40` items:
   `docs/05-audit-reports/CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026-02-06.md`.
9. Profile/auto-detection workstream verification shows `12` extracted tasks already implemented and `3` partial, reducing true open scope in that cluster:
   `reports/strict_closure/profile_workstream_verification_2026-02-06.json`.
10. Shared MCP response-budget work item from the underrepresented packet is now implemented and verified:
   `reports/strict_closure/mcp_response_budget_verification_2026-02-06.json`.
11. Deep status-field extraction from ConPort `custom_data` payloads identified `4` additional missed milestone checkpoints (not present in the prior full-coverage artifact), and these are now explicitly promoted in the master miss matrix:
   `reports/strict_closure/conport_deep_status_task_extract_2026-02-06.json`.
12. Recheck confirms the `4` deep-extraction misses are now represented in active master docs (`new_uncovered_vs_full_coverage = 0`):
   `reports/strict_closure/conport_deep_status_task_recheck_2026-02-06.json`.
13. Config backup-safety backlog item (`1.2.3`) is now implemented in `ConfigGenerator` with atomic write, rollback safety, and targeted unit tests:
   `reports/strict_closure/config_backup_safety_verification_2026-02-06.json`.
14. Profile-config integration backlog item (`1.2.4`) is now implemented with explicit tests for full-profile parity, developer 3-MCP shape, and backup rollback restore:
   `reports/strict_closure/profile_config_integration_verification_2026-02-06.json`.
15. End-to-end profile start-flow backlog item (`1.4.1`) is now implemented with additive `dopemux start --profile` support and dry-run coverage for success and invalid-profile paths:
   `reports/strict_closure/profile_start_e2e_verification_2026-02-06.json`.
16. Profile documentation backlog item (`1.4.2`) is now implemented with README updates, a dedicated profile usage guide, and schema-linked examples:
   `reports/strict_closure/profile_documentation_verification_2026-02-06.json`.
17. ADHD-engine signal collection backlog item (`2.1.3`) is now implemented with runtime endpoint probing (5448-first), energy/attention extraction, and graceful fallback:
   `reports/strict_closure/adhd_engine_profile_detector_verification_2026-02-06.json`.
18. File-pattern analyzer backlog item (`2.1.5`) is now implemented with percentage-based 0-10 scoring against deduplicated recent files:
   `reports/strict_closure/file_pattern_analyzer_verification_2026-02-06.json`.
19. Detector threshold-coverage backlog item (`2.2.4`) is now implemented with explicit unit coverage for auto/prompt/none confidence transitions and signal combinations:
   `reports/strict_closure/profile_detector_threshold_tests_verification_2026-02-06.json`.
20. Profile config swap and restart backlog item (`3.2.3`) is now implemented with backup-safe config application and optional restart command support in `profile apply/use`:
   `reports/strict_closure/profile_config_swap_restart_verification_2026-02-06.json`.
21. Profile error recovery and rollback backlog item (`3.2.4`) is now implemented with failure-path guardrails that preserve prior active state and restore Claude config backups when activation fails:
   `reports/strict_closure/profile_error_recovery_rollback_verification_2026-02-06.json`.
22. Profile switch-command backlog item (`3.3.1`) is now implemented with orchestrated save/swap/restart/restore behavior and compatibility-preserving command surface:
   `reports/strict_closure/profile_switch_command_verification_2026-02-06.json`.
23. Switch time-optimization backlog item (`3.3.2`) is now implemented with parallel save/apply execution and step-level timing telemetry with target-threshold warning:
   `reports/strict_closure/profile_switch_time_optimization_verification_2026-02-06.json`.
24. Switch integration-test backlog item (`3.3.3`) is now implemented with full->developer->full flow validation and save/restore/timing assertions:
   `reports/strict_closure/profile_switch_integration_tests_verification_2026-02-06.json`.
25. Current-profile detection backlog item (`4.1.1`) is now implemented with Claude-config MCP-set matching and workspace marker cache updates:
   `reports/strict_closure/profile_current_detection_verification_2026-02-06.json`.
26. Auto-detection service backlog items (`4.2.1` through `4.2.4`) are now implemented and verified for 5-minute cadence, confidence/debounce/quiet-hour gating, suggestion UX, acceptance branches, and persisted settings:
   `reports/strict_closure/auto_detection_service_verification_2026-02-06.json`.
27. Profile management command backlog items (`4.3.1` through `4.3.5`) are now implemented and verified for create/edit/copy/delete/current workflows, including interactive create and fallback current-profile detection:
   `reports/strict_closure/profile_management_commands_verification_2026-02-06.json`.
28. Profile analytics backlog items (`4.4.1` through `4.4.3`) are now implemented and verified for metrics capture, stats command insights, and ASCII dashboard/heatmap rendering:
   `reports/strict_closure/profile_analytics_verification_2026-02-06.json`.
29. Dope-context decision auto-index configuration backlog item (`3.3.1`) is now implemented with workspace-scoped decision retrieval settings and persisted config:
   `reports/strict_closure/dope_context_decision_auto_index_unified_search_verification_2026-02-06.json`.
30. Unified search validation backlog item (`3.3.2`) is now implemented with merged code/docs/decision behavior verification:
   `reports/strict_closure/dope_context_decision_auto_index_unified_search_verification_2026-02-06.json`.
31. Profile optimization suggestion backlog item (`4.4.4`) is now implemented with deterministic recommendation generation and ConPort archival:
   `reports/strict_closure/profile_optimization_suggestions_verification_2026-02-06.json`.
32. Usage pattern analysis backlog item (`4.5.1`) is now implemented with `dopemux profile analyze-usage` and unit coverage:
   `reports/strict_closure/profile_usage_analysis_and_init_wizard_verification_2026-02-06.json`.
33. Profile init wizard backlog item (`4.5.2`) is now implemented and verified with wizard build/save coverage:
   `reports/strict_closure/profile_usage_analysis_and_init_wizard_verification_2026-02-06.json`.
34. Migration guide documentation backlog item (`4.5.3`) is now implemented with code-truth tutorial updates:
   `reports/strict_closure/profile_documentation_completion_verification_2026-02-06.json`.
35. User documentation backlog item (`4.6.1`) is now implemented with complete tutorial and operational command guidance:
   `reports/strict_closure/profile_documentation_completion_verification_2026-02-06.json`.
36. Developer documentation backlog item (`4.6.2`) is now implemented with architecture, interface, and signal-collector extension guidance:
   `reports/strict_closure/profile_documentation_completion_verification_2026-02-06.json`.
37. Remaining profile UX docs polish (`4.6.3`) is now addressed for active docs through command-parity updates and index refresh:
   `reports/strict_closure/profile_documentation_completion_verification_2026-02-06.json`.
38. Week-2 integration/testing backlog item (`Day 10`) is now implemented with a reusable end-to-end verification harness:
   `reports/strict_closure/profile_week2_integration_testing_verification_2026-02-06.json`.
39. Historical EPIC deliverable module gaps for rows `2`, `3`, and `4` are now implemented with compatibility shims (`signal_collectors`, `scorer`, `session_manager`, `claude_manager`, `switcher`, `statusline_integration`, `suggestion_engine`, `analytics`, `migration`) and targeted verification coverage:
   `reports/strict_closure/profile_epic_compat_shims_verification_2026-02-06.json`.
40. Live ConPort backlog extraction from runtime `progress_entries` now shows `134` unique active backlog items with `66` still underrepresented in active master docs, and has been promoted into an owner-routed matrix:
   `reports/strict_closure/conport_live_backlog_doc_coverage_2026-02-06.json`.
41. Live underrepresented backlog clusters are now explicitly enumerated for closure (`profile_alias_or_residual=33`, `shield_slack_beta=11`, `kg_dependency_unification=7`, `bridge_orchestrator=6`, `mcp_token_ops=4`, `conport_persistence=1`, `other=4`):
   `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_UNDERREPRESENTED_MATRIX_2026-02-06.md`.
42. Live underrepresented backlog has now been triaged into `25` likely true-open candidates, `33` likely alias/already-implemented phrasing mismatches, and `8` resolved-in-current-wave items:
   `reports/strict_closure/conport_live_backlog_true_open_candidates_2026-02-06.json`.
43. A dedicated live backlog execution packet is now materialized for the true-open set with owner and verification anchors, and now includes runtime/documentation reclassification for persistence, MCP token-doc parity, and bridge-orchestrator integration tasks:
   `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_EXECUTION_PACKET_2026-02-06.md`.
44. Live true-open packet rows have now been explicitly promoted into the master miss matrix to close literal line-coverage drift (`25/25` exact-line additions; canonical residual pre-promotion `14`):
   `reports/strict_closure/conport_master_live_true_open_delta_2026-02-06.json`.
45. Post-promotion recheck confirms exact-line closure for the full live true-open packet (`0` exact misses of `25`), with remaining canonical drift now limited to wording-level variants (`8`):
   `reports/strict_closure/conport_master_live_true_open_delta_recheck_2026-02-06.json`.
46. KG dependency-unification deep verification now records `2` implemented items, `1` implemented-in-code item, and `4` partial items with explicit residual gaps and next actions:
   `reports/strict_closure/kg_dependency_unification_verification_2026-02-06.json`.
47. Serena KG-related regression harnesses were unblocked by fixing annotation-time import failures and async test execution defaults; targeted suites now run green (`13` passed):
   `services/serena/intelligence/database.py`, `services/serena/tree_sitter_analyzer.py`, `pytest.ini`.
48. ConPort semantic-search compatibility paths are now explicitly hard-deprecated in runtime responses/logging and active architecture docs, reducing ambiguity while preserving backward compatibility:
   `services/conport/http_server.py`, `src/dopemux/mcp/conport_mcp_tools.py`, `docs/04-explanation/DOPEMUX-CONTEXT-DEEP-DIVE.md`, `docs/04-explanation/architecture/architecture-3.0-implementation.md`.
49. A caller inventory for deprecated ConPort semantic-search paths is now captured to guide safe shim removal sequencing:
   `reports/strict_closure/kg_dependency_unification_verification_2026-02-06.json`.
50. Live ConPort backlog delta recheck (`2026-02-08` vs `2026-02-07`) confirms no
   newly introduced TODO descriptions and no new master-doc representation gaps:
   `reports/strict_closure/conport_live_backlog_delta_2026-02-08.json`.
51. Task-orchestrator workflow HTTP contracts are now covered by endpoint-level unit tests (success paths + error mapping for `404/409/503/400`), reducing ADR-197 stage-1/stage-2 drift risk:
   `tests/unit/test_task_orchestrator_workflow_api.py`.
52. ADHD engine startup is now resilient to legacy settings objects that do not expose `task_orchestrator_url`; runtime falls back to env/default instead of crashing:
   `services/adhd_engine/core/engine.py`, `tests/unit/test_adhd_engine_task_orchestrator_url.py`.

## Prioritized Gap Register

### P0 (Blockers to Production Readiness)

1. Registry/compose/service naming drift across non-smoke stacks (`compose.yml` vs smoke contracts).
2. Architecture source-of-truth consistency gaps (dependent doc links/references
   need recheck after ADR-207 restoration).
3. PAL migration incompleteness (stale Zen references across runtime/docs).
4. Web UI real-time path still lacks production push transport (currently socket fallback to polling).
5. ADR-197 Stage 1/Stage 2 implementation is in place; full integration hardening and expanded end-to-end coverage remain open.

### P1 (High Impact, Not Immediate Blockers)

1. Harden WMA/dope-memory and settle service boundary/port ownership.
2. Resolve duplicated or ambiguous service families (`session-intelligence` vs `session_intelligence`, taskmaster variants).
3. Add tests for peripheral services with no coverage evidence (workspace-watcher, activity-capture, voice-commands, slack-integration).
4. Clarify `dope-query`/`conport` split and deprecate one naming contract.
5. Triage and merge historically captured ConPort TODO/BLOCKED backlog into current execution ownership map (LiteLLM DB creation blocker reclassified as resolved-in-runtime).
6. Decide and execute policy for replaying the remaining historical ConPort bundles (merge, dedupe, or archive-only import path).
7. Preserve Leantime readiness closure with regression checks (deep-health/project-list probes and token/env compatibility coverage) so PM-plane integration remains operational.
8. Execute the 19-task secondary ConPort miss set and map each task to owner/test/doc evidence.
9. Close the remaining full-bundle underrepresented ConPort backlog set (`167`) in phased owner-assigned packets.
10. Execute packet #1 (`top 40`) from `docs/05-audit-reports/CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026-02-06.md`.
11. Close the live ConPort underrepresented set (`66`) from runtime backlog coverage diff and merge results into the master execution packet:
    `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_UNDERREPRESENTED_MATRIX_2026-02-06.md`.
12. Execute the live true-open packet (`25`) and fold closure evidence back into the master fix stream:
    `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_EXECUTION_PACKET_2026-02-06.md`.
13. Add Serena HTTP API endpoint tests that verify workspace resolution behavior with and without `SERENA_WORKSPACE_PATH` / `WORKSPACE_PATH`.
14. Promote `src/dopemux/memory/capture_client.py` from isolated module to explicit runtime contract (owner, ingress points, compatibility surface) and wire it into active capture paths.
15. Add dedicated capture-client failure-mode and idempotency tests (repo-root fail-closed, missing schema/redactor, mode precedence, deterministic event ID collision behavior).

### P2 (Optimization and Scale)

1. End-to-end latency/SLO instrumentation for event and recovery flows.
2. Performance regression suite for ADHD-aware adaptation logic.
3. Documentation lifecycle controls to prevent future archaeology drift.
4. Remove per-event schema bootstrap from capture pipeline (`capture_client.emit_capture_event`) by introducing one-time init/migration guard and measure impact on capture latency.

## Phased Implementation Plan (Detailed and Prioritized)

## Phase 0: Truth Lock (Week 1)

Goal: establish one deployable truth model.

1. Define canonical service identity map (`service_id`, aliases, canonical ports, canonical compose name).
2. Repair registry/compose alignment until `tests/arch/test_registry_compose_alignment.py` passes.
3. Validate ADR-207 dependent-document links and stale architecture references.
4. Fix broken links in `DESIGN_EVOLUTION_2026.md`.
5. Freeze a signed baseline artifact in `docs/05-audit-reports/`.

Exit criteria:

- Registry alignment test passes.
- No broken internal links in the three history docs.
- ADR-207 is restored and reviewable.

## Phase 1: Contract and Harness Hardening (Weeks 2-3)

Goal: make verification deterministic.

1. Standardize pytest async configuration and remove environment-dependent failures.
2. Split coverage gates from targeted suites to allow surgical verification without disabling quality policy globally.
3. Fix known failing tests in `services/agents/` and `tests/unit/test_taskmaster_bridge.py`.
4. Create per-service “minimum readiness contract”: health endpoint, Docker path, smoke test, owner.

Exit criteria:

- Targeted suites pass in CI (including async tests).
- Contract check file exists for all tier-1 services.

## Phase 2: Core Integration Closure (Weeks 4-6)

Goal: stabilize the main operating loop.

1. Finalize DopeconBridge ↔ Task-Orchestrator ↔ ConPort contract versioning.
2. Formalize WMA + dope-memory runtime boundary and ports.
3. Harden ADR-197 Stage 1/2 implementation with end-to-end integration coverage and operational safeguards for production readiness.
4. Verify auto-resume end-to-end across crash scenarios with deterministic tests.

Exit criteria:

- End-to-end happy path from idea capture to execution status exists.
- Recovery workflow tests pass for orphaned session resume.

## Phase 3: Agent and PAL Rationalization (Weeks 7-9)

Goal: convert partial agent ecosystem to production-safe.

1. Complete Zen→PAL naming and client migration across code/docs/config.
2. Replace simulation/fallback paths in agents with real MCP integrations where intended.
3. Define an explicit “designed-only vs implemented” boundary per agent capability.
4. Enforce runtime flags for experimental agent features.

Exit criteria:

- No critical stale Zen references in active runtime paths.
- Agent capability matrix is executable and test-backed.

## Phase 4: UI/UX Productionization (Weeks 10-12)

Goal: ship one coherent user experience.

1. Choose primary UI stack for production (terminal-first or web-first with clear fallback).
2. Fix `ui-dashboard` build and connect backend to real service signals (remove simulated random data for production mode).
3. Standardize ADHD UX rules across CLI/TUI/Web (progressive disclosure, load-aware suppression, break prompts).
4. Add UX regression tests for key workflows: start/resume, task routing, break intervention, context recovery.

Exit criteria:

- Selected primary UI builds and runs in CI.
- UX acceptance checklist passes for ADHD-first constraints.

## Phase 5: Reliability, Security, Observability (Weeks 13-15)

Goal: operationally production-ready system.

1. Define SLOs for core paths (event publish/consume, task sync latency, recovery latency, health probe reliability).
2. Implement full observability contract (logs, metrics, traces, alert routing).
3. Complete threat model and authn/authz audit for bridge/orchestrator/memory/data services.
4. Run resilience suite: dependency outages, Redis/Postgres partial failures, retry/backoff validation.

Exit criteria:

- SLO dashboard live.
- Security and resilience sign-off complete.

## Phase 6: Release Cutover (Week 16)

Goal: controlled production rollout.

1. Staging soak test with realistic load and interruption scenarios.
2. Final runbooks and operator playbooks published.
3. Release train with rollback plan and post-release verification checklist.

Exit criteria:

- Production readiness review passes.
- Rollback drill completed.

## End-State Optimized Architecture (Target)

### Layer 1: Infrastructure Plane

- PostgreSQL, Redis, Qdrant, observability stack.
- Strict service contracts for ports, health, auth, and telemetry.

### Layer 2: Memory and Knowledge Plane

- ConPort/DopeQuery as authoritative graph/context store.
- Dope-Memory as temporal chronicle and active context stream.
- Dope-Context as semantic retrieval pipeline.

### Layer 3: Coordination Plane

- DopeconBridge as asynchronous event backbone.
- Task-Orchestrator as workflow intelligence and dependency coordinator.
- Session manager and resume controllers as execution continuity controls.

### Layer 4: Intelligence Plane

- Serena, ADHD Engine, PAL-enabled agent capabilities, risk and prediction services.
- Explicit feature flags for experimental intelligence modules.

### Layer 5: Experience Plane

- Unified CLI/TUI/Web interfaces with shared ADHD UX rules and progressive disclosure contracts.
- One canonical status model rendered across all surfaces.

### Cross-Layer Rules

1. Storage authority remains in memory/data plane.
2. Coordination services do not become persistence silos.
3. UI layers do not embed business logic or private state machines.
4. Experimental features are isolated by flags and versioned contracts.
5. Every architectural claim must map to executable evidence.

## Immediate Next Work (First Sprint)

1. Fix registry/compose alignment failures and naming map.
2. Complete history-doc and architecture link-integrity recheck (ADR-207 body restored).
3. Stabilize test harness (async plugin + targeted suite policy).
4. Resolve `ui-dashboard` build failures.
5. Expand integration/doc verification and operational hardening for implemented ADR-197 Stage 1/2 primitives (`workflow_ideas` and `workflow_epics`).
6. Define and execute replay strategy for the remaining historical ConPort bundles with dedupe guardrails.
7. Fold extracted historical TODO/BLOCKED items (`reports/strict_closure/conport_backlog_extract_2026-02-06.json`) into the master prioritized fix ledger.
8. Maintain Leantime readiness closure by re-running `docs/05-audit-reports/LEANTIME_BRIDGE_READINESS_2026-02-06.md` criteria and refreshing strict-closure evidence on each wave.
9. Resolve the secondary explicit-task miss set from `reports/strict_closure/conport_master_todo_secondary_miss_extract_2026-02-06.json`.
10. Execute and close the full-bundle underrepresented set from `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json` and refresh coverage counts.
11. Execute and close packet #1 and regenerate packet #2 from remaining uncovered items.
12. Add Serena HTTP API workspace-resolution tests and pin expected behavior across host/container environments.
13. Define capture-client ownership and integration plan; wire `src/dopemux/memory/capture_client.py` into the canonical ingress path.
14. Add capture-client contract/performance tests and remove per-event schema-bootstrap overhead.

---

This file is the current audited baseline for “what exists, what is stale, what is missing, and what to do next” across components, interactions, UI, UX, and architecture.
