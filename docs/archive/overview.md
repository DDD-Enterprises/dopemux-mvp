---
id: docs-archive-overview
title: Documentation Archive Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-05'
last_review: '2026-10-10'
next_review: '2027-04-10'
prelude: Index of the frozen documentation archive kept in-repo for archaeology, with the manifest contract and the rules for adding or recovering files.
---
# ━━━◆ Ø ◆━━━

Status: [FROZEN] Archive consolidated 2026-10-10

# Documentation Archive

This tree holds historical, superseded, duplicated, and point-in-time documentation that the project keeps for archaeology. Nothing here is deleted or exported; the operator ruling of 2026-10-10 is that archived and out-of-date material stays in the repository.

## Contract

- Every file under `docs/archive/` has one row in [`MANIFEST.jsonl`](MANIFEST.jsonl) with `original_path`, `archive_path`, `sha256`, `source_commit`, `wave`, `reason`, `disposition_candidate`, and `recorded_at`.
- The only writer is `scripts/docs_archive_move.py`. It `git mv`s files into `docs/archive/<wave-id>/<original path>` and appends the manifest rows. The `docs-archive-manifest-guard` pre-commit hook rejects any archive file without a row.
- `disposition_candidate` records what a future operator decision could do (`keep`, `delete-later`, `export-later`). The current ruling is `keep` for everything; the field is a ledger, not an instruction.
- Documentation gates (frontmatter, graph validator, prohibited patterns, markdownlint, lychee) and the `dope-context` indexer skip this tree. Links inside it are not maintained.
- To recover a file, `git mv` it back to its `original_path` and append a manifest row with reason `restored`, or read it in place with `git log --follow`.

## Subtrees

| Subtree | Files | What it is |
|---|---|---|
| `w1-history-sourcefiles/` | 694 | LLM research input pack assembled 2026-05-01 (commit `71f60c601`), formerly `docs/04-explanation/history/sourceFiles/`. Not documentation; kept as corpus. |
| `history/` | 495 | Earlier normalized "HISTORICAL" docs and preliminary research findings. |
| `pipeline-v2/` | 284 | Pipeline v2 and `UPGRADE`/`UPGRADE_legacy` prompt sets; many six-way duplicates. |
| `completed-projects/` | 256 | Records of finished initiatives (ConPort KG, Serena v2, dashboard). |
| `unclassified-top-level/` | 206 | Directories relocated by the 2026-05-01 hygiene pass without a better home. |
| `implementation-plans/` | 190 | Historical implementation plans and trackers. |
| `session-notes/`, `sessions/`, `claude-sessions/`, `conport-sessions/` | 344 | Session logs and summaries, 2025-10 onward. |
| `services/`, `mcp-servers/`, `mcp-servers-source/` | 115 | Superseded per-service docs. |
| `reports/`, `audit-reports/`, `test-reports/`, `test-resources/` | 51 | Point-in-time reports. |
| `deprecated/`, `component-implementations/`, `development/`, `implementation-history/` | 130 | Deprecated designs and component completion notes. |
| `root-relocated/`, `pm-plane-taskmaster-legacy/`, `consolidation-reports/`, `integration-transient/`, `prompts-transient/` | 64 | Relocated root files, TaskMaster-era PM docs, the 2026-05-01 consolidation reports, transient prompts. |
| remaining small subtrees and loose files | 35 | `scripts/`, `happy-coder-docs/`, `claudedocs/`, `migrations/`, `instructions/`, `deployment-guides/`, `blueprints/`, `empty-stubs/`, and single files. |

Counts are tracked files at consolidation time; the manifest is authoritative.

## Provenance

- 2026-05-01: repo-hygiene PRs #561–#564 moved historical docs here under the rule "nothing is deleted".
- 2026-10-10: consolidation W0/W1 froze the tree, added the manifest, and moved the research quarantine in. Plan: [`docs/05-audit-reports/docs-consolidation-audit-and-plan-2026-10-09.md`](../05-audit-reports/docs-consolidation-audit-and-plan-2026-10-09.md). Later waves add `w3-parallel-trees/`, `w4-suffix-variants/`, `w5-root/`, `w6-superseded/`.
