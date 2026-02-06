---
id: CONPORT_FULL_TODO_COVERAGE_MATRIX_2026_02_06
title: ConPort Full Todo Coverage Matrix 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Full-bundle ConPort TODO/BLOCKED coverage check against current master fix docs with unresolved-item extraction for strict closure.
---
# ConPort Full TODO Coverage Matrix (2026-02-06)

## Scope

This pass scans all available ConPort import bundles under `reports/conport_sqlite_exports/**/import_bundles/*_conport_import_bundle.json` and evaluates TODO/BLOCKED description coverage against the active master fix docs:

1. `docs/05-audit-reports/CONPORT_MASTER_TODO_MISS_MATRIX_2026-02-06.md`
2. `docs/05-audit-reports/FINAL_STATE_FEATURE_BASELINE_AND_EXECUTION_PLAN_2026-02-06.md`
3. `docs/05-audit-reports/LEANTIME_BRIDGE_READINESS_2026-02-06.md`

## Summary

1. Unique pending items discovered: `231`
2. Explicitly represented in master docs: `64`
3. Underrepresented in master docs: `167`
4. BLOCKED items: `1`
5. TODO items: `230`

Task-type distribution:
- `DAY_PLAN`: `14`
- `EPIC`: `4`
- `NUMERIC_3`: `79`
- `OTHER`: `105`
- `TASK_PLAN`: `25`
- `WEEK_PLAN`: `4`

## Runtime Override Notes

The only historical `BLOCKED` entry in this extraction has been runtime-verified as stale:

1. `litellm` database exists in current PostgreSQL runtime.
2. `mcp-litellm` is healthy and reachable.
3. Blocker status should be reclassified to `resolved_in_runtime` for active planning.

Evidence:

- `reports/strict_closure/litellm_blocker_verification_2026-02-06.json`
- `docs/05-audit-reports/LITELLM_BLOCKER_VERIFICATION_2026-02-06.md`

## Highest-Priority Underrepresented Items

| Status | Priority hint | Type | Item | Bundle hits |
|---|---|---|---|---:|
| `BLOCKED` | `BLOCKED` | `OTHER` | `Setting up LiteLLM database configuration and connection - BLOCKED: Waiting for PostgreSQL 'litellm' database creation (see Decision #210)` | `4` |
| `TODO` | `P1` | `EPIC` | `EPIC 2: Auto-Detection Engine (P1) \| Duration: 1.5 days \| Complexity: 0.6 \| Energy: Medium \| Deliverables: signal_collectors.py, scorer.py \| Can run PARALLEL with Epic 3` | `4` |
| `TODO` | `P1` | `EPIC` | `EPIC 3: Profile Switching (P1) \| Duration: 1.5 days \| Complexity: 0.7 \| Energy: High \| Deliverables: session_manager.py, claude_manager.py, switcher.py \| Can run PARALLEL with Epic 2` | `4` |
| `TODO` | `P2` | `EPIC` | `EPIC 4: UX Integration (P2) \| Duration: 2.5 days \| Complexity: 0.5 \| Energy: Medium \| Deliverables: statusline_integration.py, suggestion_engine.py, analytics.py, migration.py + docs` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `1.2.3: Config backup & safety \| 1h \| Complexity: 0.6 \| Backup with timestamp, atomic write, rollback function` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `1.2.4: Integration tests \| 1h \| Complexity: 0.7 \| Test full profile matches existing, developer has 3 MCPs, backup/rollback` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `1.4.1: End-to-end test suite \| 1h \| Complexity: 0.6 \| Test default profile, --profile developer, validation errors, Claude starts` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `1.4.2: Documentation \| 1h \| Complexity: 0.4 \| Update README, create PROFILE-USAGE.md, schema format, examples` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `2.1.3: ADHD Engine client \| 1.5h \| Complexity: 0.7 \| Query port 5448, extract energy/attention, 20 points, graceful fallback` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `2.1.5: File pattern analyzer \| 1h \| Complexity: 0.5 \| Match recent files vs patterns, 0-10 points based on % match` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `2.2.4: Unit tests \| 0.5h \| Complexity: 0.6 \| Test all confidence thresholds and signal combinations` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.2.3: Config swap & restart \| 1h \| Complexity: 0.7 \| Backup config, atomic write, start Claude, verify success` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.2.4: Error recovery & rollback \| 0.5h \| Complexity: 0.8 \| Restore backup on failure, rollback to previous profile` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.3.1: Configure dope-context auto-index for decisions \| Duration: 30m \| Complexity: 0.5 \| Energy: Medium \| Depends: 2.2.3` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.3.1: dopemux switch <profile> command \| 1.5h \| Complexity: 0.8 \| Validate, save session, shutdown, swap, restart, restore, report time` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.3.2: Switch time optimization \| 1h \| Complexity: 0.7 \| Parallelize session save + config gen, measure each step, target <10s` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.3.2: Test unified search (code + decisions + docs) \| Duration: 30m \| Complexity: 0.5 \| Energy: Medium \| Depends: 3.3.1` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `3.3.3: Integration tests \| 0.5h \| Complexity: 0.6 \| Test switch full->developer->full, session save/restore, <10s timing` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.1.1: Detect current profile from config \| 1h \| Complexity: 0.5 \| Read config.json, match MCP list to profile, cache result` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.2.1: Background detection service \| 1.5h \| Complexity: 0.6 \| Run every 5min, queue if confidence >0.85, debounce 30min, quiet hours` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.2.2: Suggestion UI design \| 1h \| Complexity: 0.5 \| Gentle prompt with [y/N/never], explain mode shows scores, non-intrusive timing` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.2.3: Suggestion acceptance flow \| 1h \| Complexity: 0.6 \| Confirm -> trigger switch, decline -> log, never -> update config` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.2.4: Configuration options \| 0.5h \| Complexity: 0.4 \| Create profile-settings.yaml with thresholds, quiet hours, frequency` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.3.1: dopemux profile create command \| 1h \| Complexity: 0.6 \| Interactive wizard, select MCPs/ADHD prefs, generate YAML` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.3.2: dopemux profile edit command \| 0.5h \| Complexity: 0.4 \| Open in $EDITOR, validate after save` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.3.3: dopemux profile copy command \| 0.5h \| Complexity: 0.3 \| Duplicate existing profile for variants` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.3.4: dopemux profile delete command \| 0.5h \| Complexity: 0.4 \| Confirm deletion, prevent full profile delete, archive instead` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.3.5: dopemux profile current command \| 0.5h \| Complexity: 0.3 \| Show active profile, MCP count, selection method` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.4.1: Metrics collection \| 1.5h \| Complexity: 0.6 \| Track switches (manual/auto), accuracy, switch time, tool usage in ConPort` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.4.2: dopemux profile stats command \| 1h \| Complexity: 0.5 \| Display most used profile, switch frequency, accuracy, performance trends` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.4.3: Analytics dashboard \| 1h \| Complexity: 0.6 \| ASCII charts, time-of-day heatmap, usage insights` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.4.4: Profile optimization suggestions \| 0.5h \| Complexity: 0.5 \| Detect patterns, suggest profile adjustments, archive recommendations` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.5.1: Usage pattern analysis \| 1h \| Complexity: 0.6 \| Analyze git history for branches, directories, commit times` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.5.2: dopemux profile init wizard \| 1.5h \| Complexity: 0.6 \| First-time setup, interactive questions, auto-generate personalized profiles` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.5.3: Migration guide documentation \| 0.5h \| Complexity: 0.4 \| Step-by-step guide, workflow examples, troubleshooting, best practices` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.6.1: User documentation \| 1h \| Complexity: 0.4 \| Complete profile user guide, command reference, auto-detection explanation` | `4` |
| `TODO` | `UNSPECIFIED` | `NUMERIC_3` | `4.6.2: Developer documentation \| 1h \| Complexity: 0.5 \| Architecture overview, API docs, extension guide for signal collectors` | `4` |
| `TODO` | `UNSPECIFIED` | `OTHER` | `Add token budget monitoring and logging to MCP servers for optimization insights (track truncation frequency, budget usage %)` | `4` |
| `TODO` | `UNSPECIFIED` | `OTHER` | `Create shared MCP response budget utility (services/shared/mcp_response_budget.py) to standardize token management across all MCP servers` | `4` |
| `TODO` | `UNSPECIFIED` | `DAY_PLAN` | `Day 10: Week 2 Integration & Testing (6-7 hours)` | `4` |
| `TODO` | `UNSPECIFIED` | `DAY_PLAN` | `Day 4: ConPort Integration & Metrics (4-5 hours)` | `4` |
| `TODO` | `UNSPECIFIED` | `DAY_PLAN` | `Day 5: Productivity Monitoring & False Positive Detection (5-6 hours)` | `4` |
| `TODO` | `UNSPECIFIED` | `DAY_PLAN` | `Day 7: Desktop Commander Integration (4-5 hours)` | `4` |
| `TODO` | `UNSPECIFIED` | `OTHER` | `Document MCP token budgeting best practices for future MCP development (add to docs/best-practices/mcp-token-management.md)` | `4` |
| `TODO` | `UNSPECIFIED` | `OTHER` | `Monitor MCP servers for edge cases after token limit fixes deployment` | `4` |
| `TODO` | `UNSPECIFIED` | `OTHER` | `Restart Claude Code to load all MCP token limit fixes (dope-context, Serena, ConPort, Zen)` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 1.1: Profile YAML Schema Definition & Validation \| Duration: 4h \| Complexity: 0.6 \| Energy: Medium \| Priority: CRITICAL (foundation)` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 1.3: CLI Commands - Manual Profile Selection \| Duration: 3h \| Complexity: 0.5 \| Energy: Medium \| Priority: HIGH` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 1.4: Integration Testing & Documentation \| Duration: 2h \| Complexity: 0.5 \| Energy: Medium \| Priority: MEDIUM` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 2.1: Context Signal Collectors \| Duration: 6h \| Complexity: 0.6 \| Energy: Medium \| Priority: HIGH \| Can start after Epic 1` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 2.2: Profile Scoring & Selection \| Duration: 4h \| Complexity: 0.6 \| Energy: Medium \| Priority: HIGH \| Depends: Task 2.1` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 2.3: CLI Integration - Auto-Suggest \| Duration: 2h \| Complexity: 0.4 \| Energy: Low \| Priority: MEDIUM \| Depends: Task 2.2` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.1: ConPort Session Management \| Duration: 5h \| Complexity: 0.7 \| Energy: High \| Priority: CRITICAL \| Can start after Epic 1` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.1: Configure Integration Bridge \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium \| Set up Integration Bridge routing for Task-Orchestrator` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.2: Claude Process Management \| Duration: 4h \| Complexity: 0.8 \| Energy: High \| Priority: CRITICAL \| Depends: Task 1.2` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.2: Implement Event Subscription \| Duration: 75m \| Complexity: 0.7 \| Energy: High \| Enable Task-Orchestrator to receive ConPort events via Integration Bridge` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.3: Implement Insight Publishing \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium \| Enable Task-Orchestrator to send insights back to ConPort` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.3: Profile Switch Orchestration \| Duration: 3h \| Complexity: 0.7 \| Energy: High \| Priority: HIGH \| Depends: Task 3.1 + 3.2` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 3.4: Test Bridge Communication \| Duration: 45m \| Complexity: 0.5 \| Energy: Medium \| Validate bidirectional Integration Bridge communication` | `4` |
| `TODO` | `UNSPECIFIED` | `TASK_PLAN` | `Task 4.1: Enable Dependency Analysis \| Duration: 75m \| Complexity: 0.6 \| Energy: High \| Activate dependency analysis tools (Tools 1-10) with ConPort integration` | `4` |

## Closure Guidance

1. Keep the original 24-item miss matrix as closed representation baseline (`24/24` explicit coverage).
2. Promote the remaining underrepresented set (`167`) into phased owner-mapped work packets, starting with P0/P1 hints and high bundle-hit recurrence.
3. Maintain additive/no-break compatibility while implementing each item and update master docs after each closure slice.

## Evidence Artifact

- `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json`
