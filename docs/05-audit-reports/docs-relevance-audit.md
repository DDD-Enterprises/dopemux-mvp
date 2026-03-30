---
title: Documentation Relevance Audit
type: explanation
generated: 2026-03-26
scope: docs/ (active, non-archive)
tool: claude-code
id: docs-relevance-audit
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Documentation Relevance Audit (explanation) for dopemux documentation and
  developer workflows.
---
# Documentation Relevance Audit

Generated: **2026-03-26**
Scope: `docs/` — active files only (archive excluded)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total active docs scanned | 840 |
| Stale by `date` field (pre-2025-09-01) | 0 |
| Stale by `last_review` field (pre-2025-09-01) | 0 |
| Expired drafts/proposed (pre-2025-12-26) | 1 |
| Docs past `next_review` date (before 2026-03-26) | 204 |
| — of which: `draft` status past review | 46 |
| — of which: `proposed` status past review | 13 |
| Files with no YAML frontmatter | 10 |
| Broken internal links (key docs only) | 12 |
| Archive directories mirroring active names | 6 direct + 6 semantic |
| Duplicate `-2`/`-3` files in audit-reports section | 11 base files |

**Bottom line**: No date-field staleness was found because most docs carry recently-updated frontmatter. The real signal is the `next_review` field: **204 docs** (24% of the corpus) missed their review window, concentrated heavily in `05-audit-reports` (all draft) and `90-adr` (all proposed). Twelve broken internal links exist in the two master index files. The archive mirrors several active sections by name, creating confusion about canonical authority.

---

## 1. Staleness Findings

### 1a. Docs with `date` before 2025-09-01

None found. All active docs carry a `date` field of 2025-09-01 or later.

### 1b. Docs with `last_review` before 2025-09-01

None found. All reviewed docs carry a `last_review` of 2025-09-01 or later.

### 1c. Expired Drafts / Proposed (created before 2025-12-26, still draft/proposed)

| File | Date | Status | Recommendation |
|------|------|--------|----------------|
| `90-adr/adr-180-automatic-instance-resume-2.md` | 2025-10-04 | proposed | Accept, supersede, or move to archive |

### 1d. Docs Past `next_review` Date (204 total)

This is the primary staleness signal. Breakdown by section:

| Section | Past-Review Count | Notes |
|---------|-------------------|-------|
| `05-audit-reports` | ~120 | All with `draft` status; see §1d-i |
| `90-adr` | ~30 | Mix of `proposed` and `accepted`; see §1d-ii |
| `03-reference` | ~25 | Various operational docs |
| `04-explanation` | ~20 | Architecture, design decisions |
| `01-tutorials` | 6 | Quick-launch, installation, profile guides |
| `02-how-to` | 12 | Deployment, instance management, integrations |
| `06-research` | 4 | Investigation reports |

**All `next_review` dates cluster in two waves**: Feb 2026-02-08 (bulk batch-stamped) and 2026-01-15 (earlier batch). No document in the corpus has a future `next_review` set beyond 2026-06-19 except the two master index files.

#### 1d-i: Draft Audit Reports Past Review (46 files, all in `05-audit-reports/`)

These are point-in-time snapshot documents from a February 2026 audit sprint. They carry `status: draft` and `next_review: 2026-02-20` or `-2026-02-22` — all now 4–5 weeks overdue. Selected examples:

| File | next_review | Concern |
|------|-------------|---------|
| `ACTIVE_DOCS_CONTRADICTION_MATRIX_2026-02-06.md` | 2026-02-20 | UPPERCASE filename; -2 duplicate exists |
| `CONPORT_DEEP_STATUS_TASK_EXTRACT_2026-02-06.md` | 2026-02-20 | UPPERCASE; -2 duplicate exists |
| `CONPORT_LIVE_BACKLOG_EXECUTION_PACKET_2026-02-06.md` | 2026-02-20 | UPPERCASE; -2 duplicate exists |
| `adr-197-p0-stage1-stage2-implementation-pr-plan-2026-02-06.md` | 2026-02-20 | -2 duplicate exists |
| `runtime-stability-hotfixes-2026-02-08.md` | 2026-02-22 | Recent, may still be relevant |
| `semantic-search-reference-inventory-2026-02-07.md` | 2026-02-21 | Operational reference |

**Pattern**: 11 of the 148 audit-report files have both an original and a `-2` variant (same base name). These are likely exact or near-exact duplicates. See §4 for deduplication recommendation.

#### 1d-ii: Proposed ADRs Past Review (13 files)

These ADRs were drafted during the Oct 2025 – Feb 2026 audit sprint and have never been accepted or superseded.

| File | next_review | Status |
|------|-------------|--------|
| `adr-180-automatic-instance-resume-2.md` | 2026-01-15 | proposed |
| `adr-201-conport-kg-security-hardening-2.md` | 2026-02-08 | proposed |
| `adr-202-serena-v2-production-validation-2.md` | 2026-02-08 | proposed |
| `adr-203-task-orchestrator-un-deprecation-2.md` | 2026-02-08 | proposed |
| `adr-204-ml-risk-assessment-extraction-2.md` | 2026-02-08 | proposed |
| `adr-205-systematic-audit-methodology-2.md` | 2026-02-08 | proposed |
| `adr-206-code-audit-results-2025-10-16.md` | 2026-02-08 | proposed |
| `adr-207-leantime-api-research-2.md` | 2026-02-08 | proposed |
| `adr-207-phase-1-implementation-plan-2.md` | 2026-02-08 | proposed |
| `adr-207-session-summary-2.md` | 2026-02-08 | proposed |
| `adr-207-session-summary-3.md` | 2026-02-08 | proposed |
| `adr-207-task-orchestrator-capabilities-2.md` | 2026-02-08 | proposed |
| `global-mcp-configuration.md` | 2026-02-08 | proposed |

Note: `adr-207-session-summary-2.md` and `adr-207-session-summary-3.md` are a duplicate pair (both exist in `90-adr/`). Similarly, `adr-213-dual-capture-canonical-ledger-2.md` and `-3.md` are a duplicate pair.

### 1e. Files Without YAML Frontmatter (10 files)

All 10 are in `06-research/investigations/`:

| File | Issue |
|------|-------|
| `deep-research-report 7.md` through `deep-research-report 13.md` (7 files) | No frontmatter; filenames contain spaces |
| `designing-and-stress-testing-agent-systems.md` | No frontmatter |
| `multi-llm-routing-and-cost-optimization.md` | No frontmatter |
| `terminal-ai-control-system-design.md` | No frontmatter |

The three without spaces are listed in `gitStatus` as new untracked files, suggesting they were very recently added and have not yet been formatted to project standards.

---

## 2. Archive Overlap

### 2a. Direct Name Overlaps (archive dir name == active dir name)

| Archive Directory | Active Directory | Risk |
|-------------------|-----------------|------|
| `docs/archive/history/` | `docs/04-explanation/history/` | Ambiguous — which is canonical history? |
| `docs/archive/implementation-plans/` | `docs/04-explanation/implementation-plans/` | Active may contain still-valid plans |
| `docs/archive/migrations/` | `docs/04-explanation/migrations/` | Migration docs in both locations |
| `docs/archive/root-relocated/` | `docs/02-how-to/root-relocated/` | Confusing "relocated" stub in active tree |
| `docs/archive/root-relocated/` | `docs/05-audit-reports/root-relocated/` | Same issue in audit-reports |
| `docs/archive/services/` | `docs/03-reference/services/` | Service docs split between archive and reference |

### 2b. Semantic Overlaps (topics present in both archive and active)

| Topic | Archive Location | Active Location | Concern |
|-------|-----------------|-----------------|---------|
| Audit reports | `archive/audit-reports/` | `05-audit-reports/` | Two separate audit-report stores |
| Reports (general) | `archive/reports/`, `archive/consolidation-reports/`, `archive/test-reports/` | `05-audit-reports/` | Report content fragmented across 4 locations |
| Services | `archive/services/` | `03-reference/services/` | Service references may be split |
| Migrations | `archive/migrations/` | `04-explanation/migrations/` | Overlap on migration docs |
| Implementation plans | `archive/implementation-plans/` | `04-explanation/implementation-plans/` | Plans in both locations |
| History | `archive/history/` | `04-explanation/history/` | History content duplicated |

### 2c. Session/System Overlap

The archive contains a `sessions/` tree with subdirs mirroring every major system (adhd-engine, agents, conport, dope-context, serena, etc.). The active `03-reference/systems/` tree covers the same systems. This is expected (archive = development session notes, active = stable reference), but the boundary is not always clearly signposted in the docs themselves.

---

## 3. Key Doc Accuracy (Spot-Check)

### 3a. `docs/01-tutorials/start-here-2.md`

- **Internal links**: 0 (no markdown links found; the file is a self-contained audit summary with no cross-references)
- **Content relevance**: The file describes a completed security audit from the `code-audit` branch. The headline "Start Here" is misleading — this is a project status snapshot, not an onboarding tutorial. The `next_review: 2026-02-08` date is 47 days past due.
- **Outdated claims**: References `code-audit` branch as "ready to push/merge"; references metrics (DopeconBridge 100% complete) that may have evolved since Feb 2026-02-05.

### 3b. `docs/02-how-to/deployment-worktree.md`

- **Internal links**: 0 (no cross-references found in the file)
- **next_review**: 2026-02-08 — 47 days past due.
- **Content**: Not deeply inspected but no broken link issues.

### 3c. `docs/INDEX.md`

- **Date**: 2026-03-19 (recently updated, 7 days old)
- **next_review**: 2026-06-19 (not yet due)
- **Total internal links**: 13
- **Broken links**: **1**

| Broken Link | Link Text | Correct Path |
|-------------|-----------|--------------|
| `planes/pm/hub-2.md` | PM Plane Hub | `03-reference/planes/pm/hub-2.md` |

Root cause: The link uses a path relative to `docs/` that omits the `03-reference/` prefix. The file `docs/03-reference/planes/pm/hub-2.md` exists.

### 3d. `docs/00-MASTER-INDEX.md`

- **Date**: 2026-02-05; **last_review**: 2026-03-19
- **next_review**: 2026-06-19 (not yet due)
- **Total internal links**: 102
- **Broken links**: **11**

| Broken Link Text | Broken Path | Correct Path (exists) |
|-----------------|-------------|----------------------|
| Callable Surface Inventory | `systems/conport/callable-surface-inventory.md` | `03-reference/systems/conport/callable-surface-inventory.md` |
| Surface Equivalence and Drift | `systems/conport/surface-equivalence-and-drift.md` | `03-reference/systems/conport/surface-equivalence-and-drift.md` |
| Preferred Canonical Surface | `systems/conport/preferred-canonical-surface.md` | `03-reference/systems/conport/preferred-canonical-surface.md` |
| Authority Invariants and Dark Methods | `systems/conport/authority-invariants-and-dark-methods.md` | `03-reference/systems/conport/authority-invariants-and-dark-methods.md` |
| PM Plane Hub | `planes/pm/hub-2.md` | `03-reference/planes/pm/hub-2.md` |
| PM Plane Write Adjudication Model | `planes/pm/pm-plane-write-adjudication-model.md` | `03-reference/planes/pm/pm-plane-write-adjudication-model.md` |
| PM Plane Write Matrix | `planes/pm/pm-plane-write-matrix.md` | `03-reference/planes/pm/pm-plane-write-matrix.md` |
| PM Plane Normalized Tool Surface | `planes/pm/pm-plane-normalized-tool-surface.md` | `03-reference/planes/pm/pm-plane-normalized-tool-surface.md` |
| PM Plane Read Matrix | `planes/pm/pm-plane-read-matrix.md` | `03-reference/planes/pm/pm-plane-read-matrix.md` |
| PM Plane Write Surface Policy | `planes/pm/pm-plane-write-surface-policy.md` | `03-reference/planes/pm/pm-plane-write-surface-policy.md` |
| Master Action Plan | `archive/development/planning/action-plan-master-2.md` | **File does not exist** (checked archive) |

Root cause (10 of 11): Links omit the `03-reference/` path prefix. The target files all exist under `docs/03-reference/`. This is a systematic path error in the MASTER-INDEX, not individual file moves.

Root cause (1 of 11): `archive/development/planning/action-plan-master-2.md` does not exist anywhere in the archive. The file was likely deleted or never committed.

---

## 4. Recommended Actions

### Priority 1 — Fix Now (Broken Navigation)

1. **Fix 11 broken links in `docs/00-MASTER-INDEX.md`**
   - For the 10 `systems/conport/` and `planes/pm/` links: prepend `03-reference/` to each path.
   - For the `archive/development/planning/action-plan-master-2.md` link: remove the link or point to the closest surviving equivalent.

2. **Fix 1 broken link in `docs/INDEX.md`**
   - Change `planes/pm/hub-2.md` to `03-reference/planes/pm/hub-2.md`.

### Priority 2 — Address Expired Drafts and Proposed ADRs

3. **Resolve 13 proposed ADRs in `90-adr/`** (all past review date)
   - For each: accept (promote to `accepted`), reject (move to archive), or supersede (link to a newer ADR).
   - `adr-207-session-summary-2.md` and `-3.md` are duplicates — keep the latest, archive the other.
   - `adr-213-dual-capture-canonical-ledger-2.md` and `-3.md` are duplicates — same treatment.

4. **Decide on 46 draft audit reports in `05-audit-reports/`**
   - These are point-in-time snapshots from the Feb 2026 sprint. Their value is as historical record, not living documentation.
   - Recommended: bulk-move to `docs/archive/audit-reports/` with a single index note in `05-audit-reports/`.
   - At minimum, promote `status: draft` to `status: historical` and remove future `next_review` dates.

5. **Resolve the single expired draft ADR**: `90-adr/adr-180-automatic-instance-resume-2.md` (date 2025-10-04, status proposed) — oldest expired draft in the system.

### Priority 3 — Frontmatter and Filename Hygiene

6. **Add frontmatter to 10 files in `06-research/investigations/`**
   - The 7 `deep-research-report N.md` files have spaces in filenames (non-standard) and no frontmatter.
   - The 3 new untracked investigation files need frontmatter before commit.

7. **Rename UPPERCASE filenames in `05-audit-reports/`**
   - Files like `ACTIVE_DOCS_CONTRADICTION_MATRIX_2026-02-06.md`, `CONPORT_DEEP_STATUS_TASK_EXTRACT_2026-02-06.md`, etc. violate the project's lowercase-kebab convention.
   - 7 UPPERCASE files identified (ACTIVE_DOCS, CONPORT_DEEP, CONPORT_FULL, CONPORT_LIVE, CONPORT_MASTER, CONPORT_UNDERREPRESENTED, FINAL_STATE, KG_DEPENDENCY, PROFILE_DOCUMENTATION_COMPLETION, PROFILE_DOCUMENTATION_VERIFICATION).

### Priority 4 — Deduplicate `-2` / `-3` Variants

8. **Audit the 11 duplicate base-files in `05-audit-reports/`**
   - Files like `conport-deep-status-task-extract-2026-02-06.md` and `conport-deep-status-task-extract-2026-02-06-2.md` likely contain identical or near-identical content.
   - Process: diff each pair; if identical, remove the `-2`; if different, keep the higher-numbered one as canonical and archive the other.

9. **Audit 2 duplicate ADR pairs in `90-adr/`** (session-summary-2/-3, dual-capture-canonical-ledger-2/-3).

### Priority 5 — Clarify Archive Boundaries

10. **Add README stubs to ambiguous archive directories** (`archive/history/`, `archive/implementation-plans/`, `archive/migrations/`, `archive/services/`) explaining what was moved there and when, so they are not confused with their active counterparts.

11. **Rename or remove `root-relocated/` stubs** in `docs/02-how-to/` and `docs/05-audit-reports/`. These appear to be leftover navigation artifacts from a reorganization rather than meaningful content directories.

### Priority 6 — Update `start-here-2.md`

12. **Replace `docs/01-tutorials/start-here-2.md` content or title**
    - The file currently documents a completed audit sprint, not a tutorial. Either replace with genuine onboarding content or rename to `audit-sprint-feb-2026-summary.md` and move to `05-audit-reports/`.

---

## Appendix: Files With No Frontmatter

```
06-research/investigations/deep-research-report 7.md
06-research/investigations/deep-research-report 8.md
06-research/investigations/deep-research-report 9.md
06-research/investigations/deep-research-report 10.md
06-research/investigations/deep-research-report 11.md
06-research/investigations/deep-research-report 12.md
06-research/investigations/deep-research-report 13.md
06-research/investigations/designing-and-stress-testing-agent-systems.md
06-research/investigations/multi-llm-routing-and-cost-optimization.md
06-research/investigations/terminal-ai-control-system-design.md
```

## Appendix: Active Docs by Section

| Section | File Count |
|---------|-----------|
| `01-tutorials/` | 16 |
| `02-how-to/` | 74 |
| `03-reference/` | 406 |
| `04-explanation/` | 105 |
| `05-audit-reports/` | 148 |
| `06-research/` | 34 |
| `90-adr/` | 43 |
| `91-rfc/` | 1 |
| `92-runbooks/` | 1 |
| Root (`docs/*.md`) | 2 |
| **Total** | **830+** |

Archive contains an additional **1,159** `.md` files (not scanned for this audit).
