---
id: docs-dedup-diff-report
title: Docs Dedup Diff Report
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Docs Dedup Diff Report (explanation) for dopemux documentation and developer
  workflows.
---
# Documentation Dedup Diff Report

Generated: 2026-03-26

## Summary

- **Total suffixed files (-2 or -3)**: 171
- **Pairs where original exists**: 34 (need resolution)
- **Orphan suffixed files (no original)**: 137 (safe to rename by removing suffix)

---

## Pairs Needing Resolution

All 34 pairs were individually diffed. The nature of differences fell into 5 distinct categories:

### Category A: Internal link suffix drift (keep original)

The suffixed version has internal links that still point to other `-2`/`-3`-suffixed filenames, while the original has been updated to canonical (no-suffix) link targets. The original is the correctly-healed version.

| Suffixed File | Original File | Diff Lines | Larger | Recommendation |
|---|---|---|---|---|
| `docs/01-tutorials/multi-project-2.md` | `docs/01-tutorials/multi-project.md` | 4 | equal | keep original (link fix: `WORKTREE_SWITCHING_GUIDE.md` → `worktree-switching-guide.md`) |
| `docs/02-how-to/developing-zen-2.md` | `docs/02-how-to/developing-zen.md` | 4 | equal | keep original (link fix: `development-setup-2.md` → `development-setup.md`) |
| `docs/02-how-to/development-setup-2.md` | `docs/02-how-to/development-setup.md` | 4 | equal | keep original (link fix: `developing-zen-2.md` → `developing-zen.md`) |
| `docs/03-reference/governance/conflict-ledger-2.md` | `docs/03-reference/governance/conflict-ledger.md` | 4 | equal | keep original (link fix: `authority-map-2.md` → `authority-map.md`) |
| `docs/03-reference/planes/pm/_handoff/pm-fric-01-handoff-2.md` | `docs/03-reference/planes/pm/_handoff/pm-fric-01-handoff.md` | 10 | equal | keep original (links: `pm-friction-map-2.md`, `pm-fric-01-handoff-2.md` → unsuffixed) |
| `docs/03-reference/planes/pm/_handoff/pm-fric-02-handoff-2.md` | `docs/03-reference/planes/pm/_handoff/pm-fric-02-handoff.md` | 8 | equal | keep original (links: `pm-friction-map-2.md`, `pm-fric-02-handoff-2.md` → unsuffixed) |
| `docs/03-reference/planes/pm/pm-adhd-requirements-2.md` | `docs/03-reference/planes/pm/pm-adhd-requirements.md` | 8 | equal | keep original (link fix: `pm-friction-map-2.md` → `pm-friction-map.md`) |
| `docs/03-reference/planes/pm/pm-output-boundaries-2.md` | `docs/03-reference/planes/pm/pm-output-boundaries.md` | 4 | equal | keep original (link fix: `pm-friction-map-2.md`, `signal-vs-noise-analysis-2.md` → unsuffixed) |
| `docs/03-reference/planes/pm/dopemux/_opus_inputs/bundle_20260213/00-bundle-index-2.md` | `docs/03-reference/planes/pm/dopemux/_opus_inputs/bundle_20260213/00-bundle-index.md` | 4 | equal | keep original (link fix: `comprehensive-set-2.md` → `comprehensive-set.md`) |
| `docs/03-reference/planes/pm/dopemux/_opus_inputs/bundle_20260213/comprehensive-set-2.md` | `docs/03-reference/planes/pm/dopemux/_opus_inputs/bundle_20260213/comprehensive-set.md` | 4 | equal | keep original (link fix: `12-opus-prompts-ready-2.md` → `12-opus-prompts-ready.md`) |
| `docs/03-reference/planes/pm/dopemux/_opus_inputs/bundle_20260213/12-opus-prompts-ready-2.md` | `docs/03-reference/planes/pm/dopemux/_opus_inputs/bundle_20260213/12-opus-prompts-ready.md` | 38 | equal | keep original (all 11 sibling bundle links stripped of `-2` suffix) |
| `docs/03-reference/planes/pm/dopemux/00-index-2.md` | `docs/03-reference/planes/pm/dopemux/00-index.md` | 46 | equal | keep original (all 14 chapter links stripped of `-2` suffix) |
| `docs/03-reference/planes/pm/dopemux/07-dopetask-integration-2.md` | `docs/03-reference/planes/pm/dopemux/07-dopetask-integration.md` | 4 | equal | keep original (version bump: `dopetask version=0.1.4` → `0.2.0` in original) |
| `docs/04-explanation/implementation-plans/dashboard-day9-index-2.md` | `docs/04-explanation/implementation-plans/dashboard-day9-index.md` | 8 | equal | keep original (link fix: `dashboard-day9-deep-research-2.md` → unsuffixed) |
| `docs/04-explanation/history/design-evolution-2026-2.md` | `docs/04-explanation/history/design-evolution-2026.md` | 40 | equal | keep original (16 archive history links stripped of `-2` suffix; also `unbuilt-features-and-roadmap-2.md`, `project-archaeology-report-2.md` → unsuffixed) |
| `docs/03-reference/services/performance-baseline-2.md` | `docs/03-reference/services/performance-baseline.md` | 4 | equal | keep original (port corrected: task-orchestrator 3014 → 8000) |
| `docs/03-reference/services/server-registry-2.md` | `docs/03-reference/services/server-registry.md` | 8 | equal | keep original (task-orchestrator port/health-check URL: 3014 → 8000) |

### Category B: Internal links AND UPPERCASE filename references (keep original)

The suffixed version references other `-2`-suffixed audit report filenames; the original was updated to reference the UPPERCASE-named canonical versions produced during the consolidation sprint.

| Suffixed File | Original File | Diff Lines | Larger | Recommendation |
|---|---|---|---|---|
| `docs/05-audit-reports/conport-deep-status-task-extract-2026-02-06-2.md` | `docs/05-audit-reports/conport-deep-status-task-extract-2026-02-06.md` | 10 | equal | keep original (4 references updated from `-2.md` to `UPPERCASE.md` canonical names) |
| `docs/05-audit-reports/conport-full-todo-coverage-matrix-2026-02-06-2.md` | `docs/05-audit-reports/conport-full-todo-coverage-matrix-2026-02-06.md` | 16 | equal | keep original (5 references updated to UPPERCASE canonical names) |
| `docs/05-audit-reports/conport-live-backlog-execution-packet-2026-02-06-2.md` | `docs/05-audit-reports/conport-live-backlog-execution-packet-2026-02-06.md` | 12 | equal | keep original (3 references updated to UPPERCASE canonical names) |
| `docs/05-audit-reports/conport-master-todo-miss-matrix-2026-02-06-2.md` | `docs/05-audit-reports/conport-master-todo-miss-matrix-2026-02-06.md` | 48 | equal | keep original (12 references updated to UPPERCASE canonical names) |
| `docs/05-audit-reports/conport-underrepresented-execution-packet-2026-02-06-2.md` | `docs/05-audit-reports/conport-underrepresented-execution-packet-2026-02-06.md` | 176 | equal | keep original (22 references updated to UPPERCASE canonical names) |
| `docs/05-audit-reports/final-state-feature-baseline-and-execution-plan-2026-02-06-2.md` | `docs/05-audit-reports/final-state-feature-baseline-and-execution-plan-2026-02-06.md` | 102 | equal | keep original (32 references updated to UPPERCASE canonical names) |
| `docs/05-audit-reports/active-docs-contradiction-matrix-2026-02-06-2.md` | `docs/05-audit-reports/active-docs-contradiction-matrix-2026-02-06.md` | 48 | equal | keep original (2 link targets updated to canonical filenames) |
| `docs/05-audit-reports/adr-197-p0-stage1-stage2-implementation-pr-plan-2026-02-06-2.md` | `docs/05-audit-reports/adr-197-p0-stage1-stage2-implementation-pr-plan-2026-02-06.md` | 8 | equal | keep original (2 references updated: `adr-197-task-epic-workflow-system-2.md` → `-3.md` and `architecture-3-0-implementation.md` suffix swap) |
| `docs/05-audit-reports/audit-summary-2025-10-16-2.md` | `docs/05-audit-reports/audit-summary-2025-10-16.md` | 10 | equal | keep original (links updated: `final-audit-report-2.md` → `FINAL-AUDIT-REPORT.md`, `PHASE-1-COMPLETE.md` uppercase) |
| `docs/05-audit-reports/audit-summary-2025-10-16-3.md` | `docs/05-audit-reports/audit-summary-2025-10-16.md` | 10 | equal | keep original (same as -2 but with `-3.md` variant links; original has UPPERCASE canonical) |
| `docs/05-audit-reports/deployment-ready-summary-2.md` | `docs/05-audit-reports/deployment-ready-summary.md` | 8 | equal | keep original (path reference updated: `final-audit-report-2.md` → `claudedocs/DEPLOYMENT-READY-SUMMARY.md`) |

### Category C: Real content divergence — original is more complete (keep original)

The original has additional content sections not present in the suffixed version.

| Suffixed File | Original File | Diff Lines | Larger | Recommendation |
|---|---|---|---|---|
| `docs/03-reference/extraction/pipeline-reliability-2.md` | `docs/03-reference/extraction/pipeline-reliability.md` | 221 | **original** (125 vs 97 lines) | keep original — original is a fully-rewritten v4 spec with updated IDs (`PIPELINE_RELIABILITY` → `EXTRACTION-PIPELINE-RELIABILITY`), correct service paths (`UPGRADES/` → `services/repo-truth-extractor/`), graph metadata, and ~28 more lines of v4 content |
| `docs/03-reference/planes/pm/pm-architecture-2.md` | `docs/03-reference/planes/pm/pm-architecture.md` | 11 | **original** (243 vs 241 lines) | keep original — original has 2 additional lines: a cross-reference to `pm-metadata-vs-workflow.md` added in the canonical version |
| `docs/04-explanation/architecture/dopemux-architecture-overview-2.md` | `docs/04-explanation/architecture/dopemux-architecture-overview.md` | 21 | **original** (1470 vs 1469 lines) | keep original — 1 line difference; original has corrected frontmatter (`Dopemux_Architecture_Overview` title), updated review dates, corrected service path (`services/conport_kg/` → `services/dope-query/`) |

### Category D: Real content divergence — suffixed version is more complete (keep suffixed)

| Suffixed File | Original File | Diff Lines | Larger | Recommendation |
|---|---|---|---|---|
| `docs/03-reference/extraction/pipeline-transport-layer-2.md` | `docs/03-reference/extraction/pipeline-transport-layer.md` | 160 | **suffixed** (84 vs 77 lines) | keep suffixed — suffixed is 7 lines larger; original has outdated hardcoded path (`/Users/hue/code/dopemux-mvp/UPGRADES/run_extraction_v3.py`) while suffixed has canonical relative path. However both have significant rewrites — suffixed has newer frontmatter author `@hu3mann` and includes extra detail in chunking rules section that the original collapses. **Verify dates then keep whichever is truly newer.** |

### Category E: Internal link self-reference updates (keep original)

The suffixed version contains internal self-referencing links pointing to other `-2`-suffixed siblings; the original was updated to canonical names. The underlying content is otherwise identical.

| Suffixed File | Original File | Diff Lines | Larger | Recommendation |
|---|---|---|---|---|
| `docs/03-reference/planes/pm/dopemux/_opus_inputs/14-doc-roots-and-memory-corpus-map-2.md` | `docs/03-reference/planes/pm/dopemux/_opus_inputs/14-doc-roots-and-memory-corpus-map.md` | 22 | equal | keep original (4 sibling file links updated from `-2.md` to canonical, plus `opus-cross-plane-audit-3.md` → `opus-cross-plane-audit-2.md`) |
| `docs/05-audit-reports/kg-dependency-unification-verification-2026-02-06-2.md` | `docs/05-audit-reports/kg-dependency-unification-verification-2026-02-06.md` | 8 | equal | keep original (1 reference updated: `conport-live-backlog-execution-packet-2026-02-06-2.md` → `CONPORT_LIVE_BACKLOG_EXECUTION_PACKET_2026-02-06.md`) |

---

## Orphan Suffixed Files (rename to remove suffix)

These 137 files have **no unsuffixed counterpart** in the same directory. They are the only copy of that content. They are safe to rename by stripping the `-2` or `-3` suffix.

### 01-tutorials (4 orphans)

- `docs/01-tutorials/examples-2.md` → `examples.md`
- `docs/01-tutorials/installation-2.md` → `installation.md`
- `docs/01-tutorials/installation-3.md` → `installation.md` *(check if -2 and -3 are the same first)*
- `docs/01-tutorials/profiles-2.md` → `profiles.md`
- `docs/01-tutorials/start-here-2.md` → `start-here.md`

### 02-how-to (9 orphans)

- `docs/02-how-to/docker-setup-moved-2.md` → `docker-setup-moved.md`
- `docs/02-how-to/mobile/implementation-2.md` → `implementation.md`
- `docs/02-how-to/mobile/setup-2.md` → `setup.md`
- `docs/02-how-to/packaging/configuration-2.md` → `configuration.md`
- `docs/02-how-to/packaging/install-2.md` → `install.md`
- `docs/02-how-to/profile-usage-2.md` → `profile-usage.md`
- `docs/02-how-to/profile-usage-3.md` → `profile-usage.md` *(check -2 and -3 against each other)*
- `docs/02-how-to/root-relocated/checklist-2.md` → `checklist.md`

### 03-reference (37 orphans)

- `docs/03-reference/best-practices/mcp-token-management-moved-2.md` → `mcp-token-management-moved.md`
- `docs/03-reference/configuration/profile-yaml-schema-2.md` → `profile-yaml-schema.md`
- `docs/03-reference/f001-enhanced-untracked-work-system-2.md` → `f001-enhanced-untracked-work-system.md`
- `docs/03-reference/f002-multi-session-support-2.md` → `f002-multi-session-support.md`
- `docs/03-reference/governance/tp-gov-001-proof-and-handoff-contract-hardening-2.md` → `tp-gov-001-proof-and-handoff-contract-hardening.md`
- `docs/03-reference/instructions/agents-2.md` → `agents.md`
- `docs/03-reference/instructions/claude-2.md` → `claude.md`
- `docs/03-reference/instructions/claude-3.md` → `claude.md` *(check -2 and -3)*
- `docs/03-reference/instructions/codex-2.md` → `codex.md`
- `docs/03-reference/instructions/codex-3.md` → `codex.md` *(check -2 and -3)*
- `docs/03-reference/instructions/gemini-2.md` → `gemini.md`
- `docs/03-reference/planes/pm/_evidence/readme-2.md` → `readme.md`
- `docs/03-reference/planes/pm/dopemux/opus-cross-plane-audit-2.md` → `opus-cross-plane-audit.md`
- `docs/03-reference/planes/pm/hub-2.md` → `hub.md`
- `docs/03-reference/planes/pm/hub-3.md` → `hub.md` *(check -2 and -3)*
- `docs/03-reference/planes/pm/pm-plane-gaps-2.md` → `pm-plane-gaps.md`
- `docs/03-reference/planes/pm/readme-2.md` → `readme.md`
- `docs/03-reference/planes/pm/readme-3.md` → `readme.md` *(check -2 and -3)*
- `docs/03-reference/planes/pm/supervisor-2.md` → `supervisor.md`
- `docs/03-reference/planes/pm/supervisor-3.md` → `supervisor.md` *(check -2 and -3)*
- `docs/03-reference/pr-pipeline/merge/flight-deck/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/merge/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/claude/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/codex/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/copilot/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/cursor/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/gemini/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/jules/readme-2.md` → `readme.md`
- `docs/03-reference/pr-pipeline/prep/adapters/vibe/guardrails-2.md` → `guardrails.md`
- `docs/03-reference/pr-pipeline/prep/adapters/vibe/readme-2.md` → `readme.md`
- `docs/03-reference/skills/pr-merge-specialist/skill-2.md` → `skill.md`
- `docs/03-reference/spec/dope-memory/v1/readme-2-moved-2.md` → `readme-2-moved.md` *(already has unusual name; verify intent)*
- `docs/03-reference/spec/dope-memory/v1/readme-2.md` → *(this is already named `readme-2` conceptually; context needed — may be the v2 spec)*
- `docs/03-reference/spec/dope-memory/v1/readme-3.md` → *(check -2 and -3 against each other)*
- `docs/03-reference/spec/uberslicer/design-2.md` → `design.md`
- `docs/03-reference/systems/adhd-features/readme-2.md` → `readme.md`
- `docs/03-reference/systems/adhd-intelligence/adhd-engine-deep-dive-part2-2.md` → `adhd-engine-deep-dive-part2.md`
- `docs/03-reference/systems/dopecon-bridge/readme-2.md` → `readme.md`
- `docs/03-reference/systems/dopecon-bridge/readme-3.md` → `readme.md` *(check -2 and -3)*
- `docs/03-reference/systems/multi-workspace/readme-2.md` → `readme.md`
- `docs/03-reference/systems/production/readme-2.md` → `readme.md`
- `docs/03-reference/task-packets/tp-cloudflare-webhooks-0001-2.md` → `tp-cloudflare-webhooks-0001.md`

### 04-explanation (48 orphans)

- `docs/04-explanation/architecture/architecture-consolidation-synthesis-2.md` → `architecture-consolidation-synthesis.md`
- `docs/04-explanation/architecture/ultra-deep-architecture-analysis-2.md` → `ultra-deep-architecture-analysis.md`
- `docs/04-explanation/concepts/worktree-switching-guide-moved-2.md` → `worktree-switching-guide-moved.md`
- `docs/04-explanation/cross-component-analysis-2.md` → `cross-component-analysis.md`
- `docs/04-explanation/design-decisions/dopemux-multi-ai-orchestrator-design-2.md` → `dopemux-multi-ai-orchestrator-design.md`
- `docs/04-explanation/design-decisions/dopemux-unified-design-philosophy-2.md` → `dopemux-unified-design-philosophy.md`
- `docs/04-explanation/design-decisions/profile-manager-design-2.md` → `profile-manager-design.md`
- `docs/04-explanation/design-decisions/ui-implementation-roadmap-2.md` → `ui-implementation-roadmap.md`
- `docs/04-explanation/dopemux-orchestrator-final-spec-2.md` → `dopemux-orchestrator-final-spec.md`
- `docs/04-explanation/dopemux-ui-complete-master-plan-2.md` → `dopemux-ui-complete-master-plan.md`
- `docs/04-explanation/integrations/dopetask-kernel-integration-moved-2.md` → `dopetask-kernel-integration-moved.md`
- `docs/04-explanation/migrations/migration-taskx-to-dopetask-moved-2.md` → `migration-taskx-to-dopetask-moved.md`
- `docs/04-explanation/technical-deep-dives/activity-capture-deep-dive-2.md` → `activity-capture-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/activity-capture-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/adhd-dashboard-deep-dive-2.md` → `adhd-dashboard-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/adhd-dashboard-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/adhd-engine-deep-dive-part1-2.md` → `adhd-engine-deep-dive-part1.md`
- `docs/04-explanation/technical-deep-dives/adhd-engine-deep-dive-part2-2.md` → `adhd-engine-deep-dive-part2.md`
- `docs/04-explanation/technical-deep-dives/adhd-engine-deep-dive-part3-2.md` → `adhd-engine-deep-dive-part3.md`
- `docs/04-explanation/technical-deep-dives/adhd-engine-deep-dive-part4-2.md` → `adhd-engine-deep-dive-part4.md`
- `docs/04-explanation/technical-deep-dives/adhd-notifier-deep-dive-2.md` → `adhd-notifier-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/adhd-notifier-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/desktop-commander-deep-dive-2.md` → `desktop-commander-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/desktop-commander-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md` → `dope-memory-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/dopemux-context-deep-dive-2.md` → `dopemux-context-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/leantime-bridge-deep-dive-2.md` → `leantime-bridge-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/leantime-bridge-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/litellm-deep-dive-2.md` → `litellm-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/litellm-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/plane-coordinator-deep-dive-2.md` → `plane-coordinator-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/plane-coordinator-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/voice-commands-deep-dive-2.md` → `voice-commands-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/voice-commands-deep-dive-3.md` → *(check -2 and -3)*
- `docs/04-explanation/technical-deep-dives/workspace-watcher-deep-dive-2.md` → `workspace-watcher-deep-dive.md`
- `docs/04-explanation/technical-deep-dives/workspace-watcher-deep-dive-3.md` → *(check -2 and -3)*

### 05-audit-reports (20 orphans)

- `docs/05-audit-reports/audit-summary-2025-10-16-2__moved-2.md` → `audit-summary-2025-10-16-2__moved.md` *(unusual double-suffix; likely old moved marker)*
- `docs/05-audit-reports/audit-summary-2025-10-16-moved-2.md` → `audit-summary-2025-10-16-moved.md`
- `docs/05-audit-reports/deployment-ready-summary-2__moved-2.md` → `deployment-ready-summary-2__moved.md`
- `docs/05-audit-reports/deployment-ready-summary-moved-2.md` → `deployment-ready-summary-moved.md`
- `docs/05-audit-reports/phase-1a-inventory-moved-2.md` → `phase-1a-inventory-moved.md`
- `docs/05-audit-reports/phase-1b-service-catalog-moved-2.md` → `phase-1b-service-catalog-moved.md`
- `docs/05-audit-reports/phase-1c-dependency-map-moved-2.md` → `phase-1c-dependency-map-moved.md`
- `docs/05-audit-reports/phase-1d-documentation-inventory-moved-2.md` → `phase-1d-documentation-inventory-moved.md`
- `docs/05-audit-reports/phase-2-security-quality-complete-moved-2.md` → `phase-2-security-quality-complete-moved.md`
- `docs/05-audit-reports/phase-2a-security-scan-moved-2.md` → `phase-2a-security-scan-moved.md`
- `docs/05-audit-reports/phase-3-manual-review-findings-moved-2.md` → `phase-3-manual-review-findings-moved.md`
- `docs/05-audit-reports/root-relocated/adhd-dashboard-session-summary-2.md` → `adhd-dashboard-session-summary.md`
- `docs/05-audit-reports/root-relocated/compact-dashboard-complete-2.md` → `compact-dashboard-complete.md`
- `docs/05-audit-reports/root-relocated/final-complete-session-summary-2.md` → `final-complete-session-summary.md`
- `docs/05-audit-reports/root-relocated/monitoring-design-sprint-summary-2.md` → `monitoring-design-sprint-summary.md`
- `docs/05-audit-reports/root-relocated/orchestrator-integration-complete-2.md` → `orchestrator-integration-complete.md`
- `docs/05-audit-reports/root-relocated/rgoutput-2__moved-2.md` → `rgoutput-2__moved.md` *(unusual double-suffix)*
- `docs/05-audit-reports/root-relocated/rgoutput-2-moved-2.md` → `rgoutput-2-moved.md`
- `docs/05-audit-reports/root-relocated/rgoutput-2.md` → *(already named `rgoutput-2` — the `-2` is part of the original name, not a suffix; do NOT rename)*
- `docs/05-audit-reports/root-relocated/tp-routing-global-0001-commit1-summary-2.md` → `tp-routing-global-0001-commit1-summary.md`

### 90-adr (29 orphans)

All ADR suffixed files are orphans — no unsuffixed counterpart exists. Safe to rename.

- `docs/90-adr/adr-180-automatic-instance-resume-2.md` → `adr-180-automatic-instance-resume.md`
- `docs/90-adr/adr-197-task-epic-workflow-system-2.md` → `adr-197-task-epic-workflow-system.md`
- `docs/90-adr/adr-201-conport-kg-security-hardening-2.md` → `adr-201-conport-kg-security-hardening.md`
- `docs/90-adr/adr-202-serena-v2-production-validation-2.md` → `adr-202-serena-v2-production-validation.md`
- `docs/90-adr/adr-203-task-orchestrator-un-deprecation-2.md` → `adr-203-task-orchestrator-un-deprecation.md`
- `docs/90-adr/adr-204-ml-risk-assessment-extraction-2.md` → `adr-204-ml-risk-assessment-extraction.md`
- `docs/90-adr/adr-205-systematic-audit-methodology-2.md` → `adr-205-systematic-audit-methodology.md`
- `docs/90-adr/adr-207-leantime-api-research-2.md` → `adr-207-leantime-api-research.md`
- `docs/90-adr/adr-207-phase-1-implementation-plan-2.md` → `adr-207-phase-1-implementation-plan.md`
- `docs/90-adr/adr-207-session-summary-2.md` → `adr-207-session-summary.md`
- `docs/90-adr/adr-207-session-summary-3.md` → *(check -2 and -3 against each other)*
- `docs/90-adr/adr-207-task-orchestrator-capabilities-2.md` → `adr-207-task-orchestrator-capabilities.md`
- `docs/90-adr/adr-208-mcp-config-drift-prevention-2.md` → `adr-208-mcp-config-drift-prevention.md`
- `docs/90-adr/adr-213-capture-adapters-single-ledger-2.md` → `adr-213-capture-adapters-single-ledger.md`
- `docs/90-adr/adr-213-dual-capture-canonical-ledger-2.md` → `adr-213-dual-capture-canonical-ledger.md`
- `docs/90-adr/adr-213-dual-capture-canonical-ledger-3.md` → *(check -2 and -3)*
- `docs/90-adr/adr-214-mcp-leantime-decoupling-2.md` → `adr-214-mcp-leantime-decoupling.md`
- `docs/90-adr/adr-215-upgrades-v4-prompt-artifact-contracts-2.md` → `adr-215-upgrades-v4-prompt-artifact-contracts.md`
- `docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md` → `adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md`
- `docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-2.md` → `adr-217-upgrades-v4-all-services-deep-extraction.md`
- `docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-2.md` → `adr-218-repo-truth-extractor-hard-cutover-namespace.md`
- `docs/90-adr/adr-219-universal-extractor-sync-pipeline-2.md` → `adr-219-universal-extractor-sync-pipeline.md`
- `docs/90-adr/adr-pm-001-canonical-task-object-2.md` → `adr-pm-001-canonical-task-object.md`
- `docs/90-adr/adr-pm-002-pm-event-taxonomy-2.md` → `adr-pm-002-pm-event-taxonomy.md`
- `docs/90-adr/adr-pm-003-storage-derived-mirrored-2.md` → `adr-pm-003-storage-derived-mirrored.md`

---

## Special Cases Requiring Manual Review

These files need human judgment before renaming:

### Same-directory -2 and -3 pairs (both orphans — neither has an unsuffixed original)

For these groups, diff the `-2` and `-3` versions against each other to pick the canonical one:

| -2 File | -3 File | Action |
|---|---|---|
| `docs/01-tutorials/installation-2.md` | `docs/01-tutorials/installation-3.md` | diff, keep newer |
| `docs/02-how-to/profile-usage-2.md` | `docs/02-how-to/profile-usage-3.md` | diff, keep newer |
| `docs/03-reference/instructions/claude-2.md` | `docs/03-reference/instructions/claude-3.md` | diff, keep newer |
| `docs/03-reference/instructions/codex-2.md` | `docs/03-reference/instructions/codex-3.md` | diff, keep newer |
| `docs/03-reference/planes/pm/hub-2.md` | `docs/03-reference/planes/pm/hub-3.md` | diff, keep newer |
| `docs/03-reference/planes/pm/readme-2.md` | `docs/03-reference/planes/pm/readme-3.md` | diff, keep newer |
| `docs/03-reference/planes/pm/supervisor-2.md` | `docs/03-reference/planes/pm/supervisor-3.md` | diff, keep newer |
| `docs/03-reference/spec/dope-memory/v1/readme-2.md` | `docs/03-reference/spec/dope-memory/v1/readme-3.md` | diff, keep newer |
| `docs/03-reference/systems/dopecon-bridge/readme-2.md` | `docs/03-reference/systems/dopecon-bridge/readme-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/activity-capture-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/activity-capture-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/adhd-dashboard-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/adhd-dashboard-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/adhd-notifier-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/adhd-notifier-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/desktop-commander-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/desktop-commander-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/leantime-bridge-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/leantime-bridge-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/litellm-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/litellm-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/plane-coordinator-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/plane-coordinator-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/voice-commands-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/voice-commands-deep-dive-3.md` | diff, keep newer |
| `docs/04-explanation/technical-deep-dives/workspace-watcher-deep-dive-2.md` | `docs/04-explanation/technical-deep-dives/workspace-watcher-deep-dive-3.md` | diff, keep newer |
| `docs/90-adr/adr-207-session-summary-2.md` | `docs/90-adr/adr-207-session-summary-3.md` | diff, keep newer |
| `docs/90-adr/adr-213-dual-capture-canonical-ledger-2.md` | `docs/90-adr/adr-213-dual-capture-canonical-ledger-3.md` | diff, keep newer |

### Files where `-2` is part of the base name (NOT a dedup suffix)

These should NOT be renamed — the `-2` is part of the meaningful filename:

- `docs/05-audit-reports/root-relocated/rgoutput-2.md` — the name is `rgoutput-2`, not a suffixed `rgoutput`
- `docs/03-reference/spec/dope-memory/v1/readme-2.md` — may be intended as "readme version 2" spec doc (different from readme.md)

---

## Action Summary

| Category | Count | Action |
|---|---|---|
| Keep original, delete suffixed (Cat A — link drift) | 17 | `git rm <suffixed>` |
| Keep original, delete suffixed (Cat B — UPPERCASE refs) | 12 | `git rm <suffixed>` |
| Keep original, delete suffixed (Cat C — original more complete) | 3 | `git rm <suffixed>` |
| Keep suffixed, update original (Cat D — suffixed more complete) | 1 | verify dates, then `git mv` and update links |
| Orphan renames (clear, single copy) | ~115 | `git mv <file-2.md> <file.md>` |
| Orphan -2/-3 pairs (both orphans, pick one) | 22 pairs | diff then `git mv` winner, `git rm` loser |
| Special base-name files (do not rename) | 2 | no action |
