---
id: CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026_02_06
title: ConPort Underrepresented Execution Packet 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Ordered execution packet for top underrepresented ConPort backlog items with owner and verification anchors.
---
# ConPort Underrepresented Execution Packet (2026-02-06)

## Scope

Top `40` underrepresented items from `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json`, converted into owner-routed execution rows for immediate implementation slicing.

## Packet

| # | Status | Priority hint | Item | Recommended owner bucket | Verification anchor |
|---:|---|---|---|---|---|
| `1` | `BLOCKED` | `BLOCKED` | `Setting up LiteLLM database configuration and connection - BLOCKED: Waiting for PostgreSQL 'litellm' database creation (see Decision #210)` | `Platform/Infra + DB` | `DB provisioning + health checks` |
| `2` | `TODO` | `P1` | `EPIC 2: Auto-Detection Engine (P1) \| Duration: 1.5 days \| Complexity: 0.6 \| Energy: Medium \| Deliverables: signal_collectors.py, scorer.py \| Can run PARALLEL with Epic 3` | `CLI + ADHD Engine` | `service-level smoke + unit tests` |
| `3` | `TODO` | `P1` | `EPIC 3: Profile Switching (P1) \| Duration: 1.5 days \| Complexity: 0.7 \| Energy: High \| Deliverables: session_manager.py, claude_manager.py, switcher.py \| Can run PARALLEL with Epic 2` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `4` | `TODO` | `P2` | `EPIC 4: UX Integration (P2) \| Duration: 2.5 days \| Complexity: 0.5 \| Energy: Medium \| Deliverables: statusline_integration.py, suggestion_engine.py, analytics.py, migration.py + docs` | `Docs + Service Owners` | `docs_validator + link checks` |
| `5` | `TODO` | `UNSPECIFIED` | `1.2.3: Config backup & safety \| 1h \| Complexity: 0.6 \| Backup with timestamp, atomic write, rollback function` | `Core Platform` | `service-level smoke + unit tests` |
| `6` | `TODO` | `UNSPECIFIED` | `1.2.4: Integration tests \| 1h \| Complexity: 0.7 \| Test full profile matches existing, developer has 3 MCPs, backup/rollback` | `MCP Platform` | `targeted pytest suites` |
| `7` | `TODO` | `UNSPECIFIED` | `1.4.1: End-to-end test suite \| 1h \| Complexity: 0.6 \| Test default profile, --profile developer, validation errors, Claude starts` | `CLI + ADHD Engine` | `targeted pytest suites` |
| `8` | `TODO` | `UNSPECIFIED` | `1.4.2: Documentation \| 1h \| Complexity: 0.4 \| Update README, create PROFILE-USAGE.md, schema format, examples` | `CLI + ADHD Engine` | `docs_validator + link checks` |
| `9` | `TODO` | `UNSPECIFIED` | `2.1.3: ADHD Engine client \| 1.5h \| Complexity: 0.7 \| Query port 5448, extract energy/attention, 20 points, graceful fallback` | `Core Platform` | `service-level smoke + unit tests` |
| `10` | `TODO` | `UNSPECIFIED` | `2.1.5: File pattern analyzer \| 1h \| Complexity: 0.5 \| Match recent files vs patterns, 0-10 points based on % match` | `Core Platform` | `service-level smoke + unit tests` |
| `11` | `TODO` | `UNSPECIFIED` | `2.2.4: Unit tests \| 0.5h \| Complexity: 0.6 \| Test all confidence thresholds and signal combinations` | `QA + Service Owners` | `targeted pytest suites` |
| `12` | `TODO` | `UNSPECIFIED` | `3.2.3: Config swap & restart \| 1h \| Complexity: 0.7 \| Backup config, atomic write, start Claude, verify success` | `Core Platform` | `service-level smoke + unit tests` |
| `13` | `TODO` | `UNSPECIFIED` | `3.2.4: Error recovery & rollback \| 0.5h \| Complexity: 0.8 \| Restore backup on failure, rollback to previous profile` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `14` | `TODO` | `UNSPECIFIED` | `3.3.1: Configure dope-context auto-index for decisions \| Duration: 30m \| Complexity: 0.5 \| Energy: Medium \| Depends: 2.2.3` | `Core Platform` | `service-level smoke + unit tests` |
| `15` | `TODO` | `UNSPECIFIED` | `3.3.1: dopemux switch <profile> command \| 1.5h \| Complexity: 0.8 \| Validate, save session, shutdown, swap, restart, restore, report time` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `16` | `TODO` | `UNSPECIFIED` | `3.3.2: Switch time optimization \| 1h \| Complexity: 0.7 \| Parallelize session save + config gen, measure each step, target <10s` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `17` | `TODO` | `UNSPECIFIED` | `3.3.2: Test unified search (code + decisions + docs) \| Duration: 30m \| Complexity: 0.5 \| Energy: Medium \| Depends: 3.3.1` | `Docs + Service Owners` | `docs_validator + link checks` |
| `18` | `TODO` | `UNSPECIFIED` | `3.3.3: Integration tests \| 0.5h \| Complexity: 0.6 \| Test switch full->developer->full, session save/restore, <10s timing` | `CLI + ADHD Engine` | `targeted pytest suites` |
| `19` | `TODO` | `UNSPECIFIED` | `4.1.1: Detect current profile from config \| 1h \| Complexity: 0.5 \| Read config.json, match MCP list to profile, cache result` | `MCP Platform` | `CLI regression + config compat tests` |
| `20` | `TODO` | `UNSPECIFIED` | `4.2.1: Background detection service \| 1.5h \| Complexity: 0.6 \| Run every 5min, queue if confidence >0.85, debounce 30min, quiet hours` | `Core Platform` | `service-level smoke + unit tests` |
| `21` | `TODO` | `UNSPECIFIED` | `4.2.2: Suggestion UI design \| 1h \| Complexity: 0.5 \| Gentle prompt with [y/N/never], explain mode shows scores, non-intrusive timing` | `Core Platform` | `service-level smoke + unit tests` |
| `22` | `TODO` | `UNSPECIFIED` | `4.2.3: Suggestion acceptance flow \| 1h \| Complexity: 0.6 \| Confirm -> trigger switch, decline -> log, never -> update config` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `23` | `TODO` | `UNSPECIFIED` | `4.2.4: Configuration options \| 0.5h \| Complexity: 0.4 \| Create profile-settings.yaml with thresholds, quiet hours, frequency` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `24` | `TODO` | `UNSPECIFIED` | `4.3.1: dopemux profile create command \| 1h \| Complexity: 0.6 \| Interactive wizard, select MCPs/ADHD prefs, generate YAML` | `MCP Platform` | `CLI regression + config compat tests` |
| `25` | `TODO` | `UNSPECIFIED` | `4.3.2: dopemux profile edit command \| 0.5h \| Complexity: 0.4 \| Open in $EDITOR, validate after save` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `26` | `TODO` | `UNSPECIFIED` | `4.3.3: dopemux profile copy command \| 0.5h \| Complexity: 0.3 \| Duplicate existing profile for variants` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `27` | `TODO` | `UNSPECIFIED` | `4.3.4: dopemux profile delete command \| 0.5h \| Complexity: 0.4 \| Confirm deletion, prevent full profile delete, archive instead` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `28` | `TODO` | `UNSPECIFIED` | `4.3.5: dopemux profile current command \| 0.5h \| Complexity: 0.3 \| Show active profile, MCP count, selection method` | `MCP Platform` | `CLI regression + config compat tests` |
| `29` | `TODO` | `UNSPECIFIED` | `4.4.1: Metrics collection \| 1.5h \| Complexity: 0.6 \| Track switches (manual/auto), accuracy, switch time, tool usage in ConPort` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `30` | `TODO` | `UNSPECIFIED` | `4.4.2: dopemux profile stats command \| 1h \| Complexity: 0.5 \| Display most used profile, switch frequency, accuracy, performance trends` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `31` | `TODO` | `UNSPECIFIED` | `4.4.3: Analytics dashboard \| 1h \| Complexity: 0.6 \| ASCII charts, time-of-day heatmap, usage insights` | `Core Platform` | `service-level smoke + unit tests` |
| `32` | `TODO` | `UNSPECIFIED` | `4.4.4: Profile optimization suggestions \| 0.5h \| Complexity: 0.5 \| Detect patterns, suggest profile adjustments, archive recommendations` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `33` | `TODO` | `UNSPECIFIED` | `4.5.1: Usage pattern analysis \| 1h \| Complexity: 0.6 \| Analyze git history for branches, directories, commit times` | `Core Platform` | `service-level smoke + unit tests` |
| `34` | `TODO` | `UNSPECIFIED` | `4.5.2: dopemux profile init wizard \| 1.5h \| Complexity: 0.6 \| First-time setup, interactive questions, auto-generate personalized profiles` | `CLI + ADHD Engine` | `CLI regression + config compat tests` |
| `35` | `TODO` | `UNSPECIFIED` | `4.5.3: Migration guide documentation \| 0.5h \| Complexity: 0.4 \| Step-by-step guide, workflow examples, troubleshooting, best practices` | `Docs + Service Owners` | `docs_validator + link checks` |
| `36` | `TODO` | `UNSPECIFIED` | `4.6.1: User documentation \| 1h \| Complexity: 0.4 \| Complete profile user guide, command reference, auto-detection explanation` | `CLI + ADHD Engine` | `docs_validator + link checks` |
| `37` | `TODO` | `UNSPECIFIED` | `4.6.2: Developer documentation \| 1h \| Complexity: 0.5 \| Architecture overview, API docs, extension guide for signal collectors` | `CLI + ADHD Engine` | `docs_validator + link checks` |
| `38` | `TODO` | `UNSPECIFIED` | `Add token budget monitoring and logging to MCP servers for optimization insights (track truncation frequency, budget usage %)` | `MCP Platform` | `service-level smoke + unit tests` |
| `39` | `TODO` | `UNSPECIFIED` | `Create shared MCP response budget utility (services/shared/mcp_response_budget.py) to standardize token management across all MCP servers` | `MCP Platform` | `service-level smoke + unit tests` |
| `40` | `TODO` | `UNSPECIFIED` | `Day 10: Week 2 Integration & Testing (6-7 hours)` | `QA + Service Owners` | `targeted pytest suites` |

## Implementation Updates (Current Wave)

1. Row `1` (`LiteLLM BLOCKED`) has been runtime-reverified and reclassified as `resolved_in_runtime`:
   - `docs/05-audit-reports/LITELLM_BLOCKER_VERIFICATION_2026-02-06.md`
2. Profile/auto-detection cluster (rows `19` through `35`) has been reclassified with verification:
   - `12 implemented`, `3 partial`
   - `docs/05-audit-reports/PROFILE_WORKSTREAM_VERIFICATION_2026-02-06.md`
3. Row `39` (shared MCP response-budget utility) is now implemented:
   - `docs/05-audit-reports/MCP_RESPONSE_BUDGET_VERIFICATION_2026-02-06.md`
4. Row `38` (MCP token-budget monitoring/logging) is now implemented:
   - `docs/05-audit-reports/MCP_BUDGET_MONITORING_VERIFICATION_2026-02-06.md`
5. Deep status-field extraction surfaced `4` additional checkpoint tasks from ConPort `custom_data`, now promoted into the master miss matrix:
   - `docs/05-audit-reports/CONPORT_DEEP_STATUS_TASK_EXTRACT_2026-02-06.md`
6. Row `5` (`1.2.3 Config backup & safety`) is now implemented:
   - `docs/05-audit-reports/CONFIG_BACKUP_SAFETY_VERIFICATION_2026-02-06.md`
7. Row `6` (`1.2.4 Integration tests`) is now implemented:
   - `docs/05-audit-reports/PROFILE_CONFIG_INTEGRATION_VERIFICATION_2026-02-06.md`

## Source

- `reports/strict_closure/conport_full_todo_coverage_2026-02-06.json`
