---
id: repo-cli-system-recovery-tranche-2026-05-02-implementation-notes
title: Repo CLI/System Recovery Tranche Implementation Notes
type: proof
owner: '@hu3mann'
author: '@codex'
date: '2026-05-02'
prelude: Implementation notes for TP-DMX-REPOHYG-007.
---

# Implementation Notes

## Worktree

- Path: `/Users/hue/.codex/worktrees/repo-hygiene-20260503-tp007/dopemux-mvp`
- Branch: `codex/recover-cli-system-20260502-work-pr-554-fix`
- Base: `origin/main`

## Recovery Selection

`work/pr-554-fix` was selected as the recovery source. `work/pr-554` was used
only as a comparator. The comparator contains unrelated cockpit/design and
dependency-history commits, so those were not recovered in this tranche.

The recovered patch-unique commit is:

- `595b8e8783863754e9487e00257b57d3af217639`
  `fix(cli): harden dopemux audit surfaces`

The following source commit is patch-equivalent to current `origin/main` and
was not duplicated:

- `98da7f5525c6dd55028fe1cbe42d68bbe6660be1`
  `fix(cli): preserve mcp exits and redact report paths`

## Conflict Resolution

The cherry-pick conflicted in:

- `src/dopemux/cli.py`
- `src/dopemux/commands/code_commands.py`
- `src/dopemux/commands/update_commands.py`

Resolution preserved current `origin/main` command registrations and added the
recovered helper/alias behavior from the source commit. No whole-file restore
from the old branch was used.

## Exclusion

`reports/implementation-notes.md` was added by the source commit but was
removed from the tracked recovery because it is a generic old-branch local note
rather than a current operator-facing report.
