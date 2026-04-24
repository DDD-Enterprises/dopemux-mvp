# RTE Pre-Run Hygiene Stage 2 Worktree Ledger

Date: 2026-04-23

## Command Record

- `git status --short`
- `git status --short --ignored`
- `git diff --name-only`
- `git ls-files --others --exclude-standard`
- `git check-ignore -v ...`

## Git-Visible Drift Classification

| Path | State | Classification | Reason | Action |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | modified tracked file | unrelated working-tree drift | diff was a Claude memory-context refresh, not RTE runtime truth | isolated later via `git stash`, not discarded |

## Untracked Non-Ignored Files

- none observed from `git ls-files --others --exclude-standard`

## Ignored State Classes Relevant To Hygiene

| Class | Example | Classification | Decision |
| --- | --- | --- | --- |
| RTE evidence | `extraction/repo-truth-extractor/v5/doctor/`, `extraction/repo-truth-extractor/v5/runs/`, `latest_run_id.txt` | relevant run input / readiness evidence | preserve in place |
| proof artifacts | `proof/rte_deep_audit_gemini_007_stage*.md` | evidence / drift artifacts | preserve in place |
| large audit outputs | `reports/**` | potentially relevant operator evidence | preserve in place |
| local control-plane state | `.claude/`, `.dopemux/`, `.conport/` | ambiguous | preserve in place, consider exclusion-only |
| transient OS/editor noise | `.DS_Store`, `*.swp` | unrelated noise | eligible for cleanup |
| transient Python caches | `__pycache__/`, `*.pyc`, `*.pyo` | unrelated noise | eligible for cleanup |

## Contamination Findings

- The git-visible worktree was not broadly dirty.
- The repo contained large ignored trees, so `ignored` could not be equated with `safe to delete`.
- The main contamination risk for a bounded first run was scan-cost noise from hidden local trees and cache artifacts, not tracked source drift.
