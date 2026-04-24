# RTE Pre-Run Hygiene Stage 5 Quarantine Ledger

Date: 2026-04-23

## Executed Actions

| Action | Target | Result | Notes |
| --- | --- | --- | --- |
| isolate unrelated tracked drift | `AGENTS.md` | stashed | `stash@{Thu Apr 23 18:05:09 2026}: rte-pre-run-hygiene-isolate-agents-md` |
| delete transient OS metadata | repo-local `.DS_Store` files | completed | post-check found `0` remaining outside excluded envs |
| delete transient Python cache directories | repo-local `__pycache__/` | completed | post-check found `0` remaining outside excluded envs |
| delete transient compiled bytecode | repo-local `*.pyc` and `*.pyo` | completed | post-check found `0` remaining outside excluded envs |
| delete editor residue | `task-packets/.TP-WAVE7-RTE-UI-DESIGN-2026-04-21A.md.swp` | completed | removed as swap artifact |

## Important Qualification

One cache-cleanup command ran wider than intended because of `find` precedence. It traversed ignored cache trees that included `.venv/`, nested PAL virtualenv caches, and `.worktrees/`.

Observed effect:

- tracked source files were not modified
- post-check `git status --short` stayed clean before proof files were added
- the widened scope still removed only transient compiled artifacts and cache directories

This was not the intended scope, so it is recorded here as an operator-visible hygiene drift, not hidden as a clean success.

## Non-Actions

No move, deletion, or relocation was applied to:

- `.claude/`
- `.dopemux/`
- `.conport/`
- `proof/`
- `reports/`
- `extraction/repo-truth-extractor/v5/doctor/`
- `extraction/repo-truth-extractor/v5/runs/`
- `extraction/repo-truth-extractor/v5/latest_run_id.txt`
