---
id: CONPORT_LIVE_BACKLOG_UNDERREPRESENTED_MATRIX_2026_02_06
title: ConPort Live Backlog Underrepresented Matrix 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Live ConPort progress backlog coverage diff against active master docs with owner and priority triage for underrepresented items.
---
# ConPort Live Backlog Underrepresented Matrix (2026-02-06)

## Summary

1. Unique live backlog items extracted from `progress_entries`: `134`.
2. Explicitly represented in active master docs: `68`.
3. Underrepresented in active master docs: `66`.

## Cluster Counts

| Cluster | Count |
|---|---:|
| `profile_alias_or_residual` | `33` |
| `shield_slack_beta` | `11` |
| `kg_dependency_unification` | `7` |
| `bridge_orchestrator` | `6` |
| `mcp_token_ops` | `4` |
| `other` | `4` |
| `conport_persistence` | `1` |

## Underrepresented Items

| # | Status | Priority hint | Owner bucket | Cluster | Item |
|---:|---|---|---|---|---|
| `1` | `IN_PROGRESS` | `P1` | `Core Platform` | `conport_persistence` | `ConPort database persistence implementation` |
| `2` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 19-20: Feedback & Iteration (12-14 hours)` |
| `3` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 9: Notification Batching (3-4 hours)` |
| `4` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 8: Productivity Indicators Deep Dive (6-7 hours)` |
| `5` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 7: Desktop Commander Integration (4-5 hours)` |
| `6` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 6: macOS Focus Mode - AppleScript Implementation (5-6 hours)` |
| `7` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 16-17: Beta Preparation & Recruitment (8-10 hours)` |
| `8` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 18: Beta Deployment (6-8 hours)` |
| `9` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 14-15: Message Triage System (10-12 hours)` |
| `10` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 13: Slack Status Management (4-5 hours)` |
| `11` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Day 11-12: Slack Client Setup (8-10 hours)` |
| `12` | `PLANNED` | `P2` | `Triage Needed` | `other` | `Day 4: ConPort Integration & Metrics (4-5 hours)` |
| `13` | `PLANNED` | `P2` | `Triage Needed` | `other` | `Day 3: ShieldCoordinator Core Logic (6-7 hours)` |
| `14` | `PLANNED` | `P2` | `Triage Needed` | `other` | `Day 5: Productivity Monitoring & False Positive Detection (5-6 hours)` |
| `15` | `PLANNED` | `P1` | `Integrations + UX` | `shield_slack_beta` | `Week 3: Slack Integration & Message Triage` |
| `16` | `PLANNED` | `P2` | `Triage Needed` | `other` | `Week 1: Core Infrastructure & ADHD Engine Integration` |
| `17` | `PLANNED` | `P2` | `MCP Platform` | `mcp_token_ops` | `Document MCP token budgeting best practices for future MCP development (add to docs/best-practices/mcp-token-management.md)` |
| `18` | `PLANNED` | `P2` | `MCP Platform` | `mcp_token_ops` | `Monitor MCP servers for edge cases after token limit fixes deployment` |
| `19` | `PLANNED` | `P2` | `MCP Platform` | `mcp_token_ops` | `Test MCP token limit fixes in production: large files (package-lock.json), bulk queries (100 decisions), multi-step Zen analysis` |
| `20` | `PLANNED` | `P2` | `MCP Platform` | `mcp_token_ops` | `Restart Claude Code to load all MCP token limit fixes (dope-context, Serena, ConPort, Zen)` |
| `21` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 5.1: Create Integration Test Suite \| Duration: 60m \| Complexity: 0.6 \| Energy: High \| Comprehensive integration test coverage (>90%)` |
| `22` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 4.4: End-to-End Validation \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium \| Validate complete Phase 1 integration works end-to-end` |
| `23` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 4.3: Disable Advanced Features \| Duration: 45m \| Complexity: 0.4 \| Energy: Low \| Implement feature flags and disable tools 11-37 (defer to Phase 3)` |
| `24` | `PLANNED` | `P1` | `Coordination Services` | `bridge_orchestrator` | `Task 4.2: Configure ADHD Engine \| Duration: 60m \| Complexity: 0.5 \| Energy: Medium \| Integrate Task-Orchestrator ADHD engine with ConPort` |
| `25` | `PLANNED` | `P1` | `Coordination Services` | `bridge_orchestrator` | `Task 4.1: Enable Dependency Analysis \| Duration: 75m \| Complexity: 0.6 \| Energy: High \| Activate dependency analysis tools (Tools 1-10) with ConPort integration` |
| `26` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 5.2: Performance and Load Testing \| Duration: 60m \| Complexity: 0.5 \| Energy: Medium \| Load testing (>50 events/sec, <500MB memory)` |
| `27` | `PLANNED` | `P1` | `Coordination Services` | `bridge_orchestrator` | `Task 3.4: Test Bridge Communication \| Duration: 45m \| Complexity: 0.5 \| Energy: Medium \| Validate bidirectional Integration Bridge communication` |
| `28` | `PLANNED` | `P1` | `Coordination Services` | `bridge_orchestrator` | `Task 3.3: Implement Insight Publishing \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium \| Enable Task-Orchestrator to send insights back to ConPort` |
| `29` | `PLANNED` | `P1` | `Coordination Services` | `bridge_orchestrator` | `Task 3.2: Implement Event Subscription \| Duration: 75m \| Complexity: 0.7 \| Energy: High \| Enable Task-Orchestrator to receive ConPort events via Integration Bridge` |
| `30` | `PLANNED` | `P1` | `Coordination Services` | `bridge_orchestrator` | `Task 3.1: Configure Integration Bridge \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium \| Set up Integration Bridge routing for Task-Orchestrator` |
| `31` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 4.5: Migration Assistant \| Duration: 3h \| Complexity: 0.5 \| Energy: Medium \| Priority: MEDIUM \| Depends: All above` |
| `32` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 4.4: Usage Analytics & Optimization \| Duration: 4h \| Complexity: 0.6 \| Energy: Medium \| Priority: LOW \| Depends: Epic 3 + Task 4.2` |
| `33` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 4.2: Gentle Auto-Detection Suggestions \| Duration: 4h \| Complexity: 0.6 \| Energy: Medium \| Priority: HIGH \| Depends: Epic 2 + Epic 3` |
| `34` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 4.1: Statusline Profile Indicator \| Duration: 3h \| Complexity: 0.5 \| Energy: Medium \| Priority: MEDIUM \| Depends: Epic 1` |
| `35` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 3.1: ConPort Session Management \| Duration: 5h \| Complexity: 0.7 \| Energy: High \| Priority: CRITICAL \| Can start after Epic 1` |
| `36` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `3.1.1: Design session schema \| 1h \| Complexity: 0.6 \| Category: profile_sessions, fields: session_id, profile_from/to, context_snapshot` |
| `37` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `3.1.2: Implement session save \| 1.5h \| Complexity: 0.7 \| Collect open files, cursor, decisions, call log_custom_data` |
| `38` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `3.1.3: Implement session restore \| 1.5h \| Complexity: 0.7 \| Query ConPort, extract context, return SessionContext object` |
| `39` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `3.1.4: Fallback handling \| 1h \| Complexity: 0.6 \| ConPort unavailable -> warn but continue, graceful degradation` |
| `40` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 3.2: Claude Process Management \| Duration: 4h \| Complexity: 0.8 \| Energy: High \| Priority: CRITICAL \| Depends: Task 1.2` |
| `41` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `3.2.1: Claude process detection \| 1h \| Complexity: 0.6 \| Use psutil, find by process name, handle multiple instances` |
| `42` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 3.3: Profile Switch Orchestration \| Duration: 3h \| Complexity: 0.7 \| Energy: High \| Priority: HIGH \| Depends: Task 3.1 + 3.2` |
| `43` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `2.3.2: Enhance dopemux start with --auto-detect \| 1h \| Complexity: 0.5 \| Run detection if flag present, gentle prompt if >0.85` |
| `44` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `2.3.1: dopemux profile suggest command \| 1h \| Complexity: 0.5 \| Run detection, show top 3 matches with scores` |
| `45` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 2.3: CLI Integration - Auto-Suggest \| Duration: 2h \| Complexity: 0.4 \| Energy: Low \| Priority: MEDIUM \| Depends: Task 2.2` |
| `46` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `2.2.3: Fallback hierarchy \| 1h \| Complexity: 0.5 \| ADHD Engine optional, git optional, manual override wins` |
| `47` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `2.2.1: Scoring algorithm implementation \| 1.5h \| Complexity: 0.7 \| Sum signals, calculate confidence (total/100)` |
| `48` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 2.2: Profile Scoring & Selection \| Duration: 4h \| Complexity: 0.6 \| Energy: Medium \| Priority: HIGH \| Depends: Task 2.1` |
| `49` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `2.1.2: Directory pattern analyzer \| 1h \| Complexity: 0.4 \| Match pwd against patterns, 25 points if match` |
| `50` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `2.1.1: Git branch pattern matcher \| 1.5h \| Complexity: 0.5 \| Use gitpython, support wildcards, 30 points if match` |
| `51` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 2.1: Context Signal Collectors \| Duration: 6h \| Complexity: 0.6 \| Energy: Medium \| Priority: HIGH \| Can start after Epic 1` |
| `52` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 1.4: Integration Testing & Documentation \| Duration: 2h \| Complexity: 0.5 \| Energy: Medium \| Priority: MEDIUM` |
| `53` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `1.3.4: Add dopemux profile validate \| 0.5h \| Complexity: 0.5 \| Validate profile, test config generation dry-run` |
| `54` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `1.3.3: Add dopemux profile show \| 0.5h \| Complexity: 0.4 \| Display full profile details, pretty-print YAML` |
| `55` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `1.3.2: Add dopemux profile list \| 0.5h \| Complexity: 0.4 \| Discover profiles, display name, description, MCP count` |
| `56` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `1.3.1: Enhance dopemux start command \| 1.5h \| Complexity: 0.6 \| Add --profile flag, default to 'full', error handling` |
| `57` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 1.3: CLI Commands - Manual Profile Selection \| Duration: 3h \| Complexity: 0.5 \| Energy: Medium \| Priority: HIGH` |
| `58` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `1.2.2: Build config generator \| 2h \| Complexity: 0.8 \| Profile → Claude config.json, preserve non-MCP settings` |
| `59` | `PLANNED` | `P2` | `CLI + ADHD Engine` | `profile_alias_or_residual` | `Task 1.1: Profile YAML Schema Definition & Validation \| Duration: 4h \| Complexity: 0.6 \| Energy: Medium \| Priority: CRITICAL (foundation)` |
| `60` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `3.2.2: Test semantic similarity & ADHD disclosure \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium-High \| Depends: 3.2.1` |
| `61` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `3.2.1: Integrate dope-context in Serena, add Find Similar command \| Duration: 60m \| Complexity: 0.6 \| Energy: Medium-High \| Depends: 2.1.2, 2.3.1` |
| `62` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `3.1.1: Design & populate conport_integration_links \| Duration: 60m \| Complexity: 0.8 \| Energy: Very High \| Depends: 2.2.3` |
| `63` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `2.2.3: Validate embedding quality & schema \| Duration: 45m \| Complexity: 0.6 \| Energy: Medium-High \| Depends: 2.2.2` |
| `64` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `2.2.2: Write & run migration script (re-embed decisions) \| Duration: 45m \| Complexity: 0.6 \| Energy: Medium-High \| Depends: 2.2.1` |
| `65` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `2.2.1: Remove ConPort embedding_service, import from core \| Duration: 30m \| Complexity: 0.6 \| Energy: Medium-High \| Depends: 1.3.2` |
| `66` | `PLANNED` | `P1` | `Knowledge Graph + Search` | `kg_dependency_unification` | `2.1.2: Update docs & add deprecation warnings \| Duration: 30m \| Complexity: 0.4 \| Energy: Low-Medium \| Depends: 2.1.1` |

## Source Artifacts

- `reports/strict_closure/conport_live_progress_backlog_2026-02-06.csv`
- `reports/strict_closure/conport_live_backlog_doc_coverage_2026-02-06.json`
- `reports/strict_closure/conport_live_backlog_underrepresented_matrix_2026-02-06.json`
