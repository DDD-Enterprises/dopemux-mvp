# MACRO-DMX-GUARD-FILE-REPO-001 — Amendment 01: the guard adds readings, never replaces the project root

**Operator words (verbatim, chat, 2026-11-13):** "Approve Amendment 01 (Recommended)"

**In answer to (verbatim):** "I found a hole in my own Task 0 packet before committing anything. G01 did what rule T04 said: check an edit's path against the repository that holds the file, instead of the project root. I tested it: planting a one-line `.git` file in `services/` then lets an edit to the red-lane path `services/task-orchestrator/x.py` through, which today's guard blocks. Amendment 01 changes T04 to add rather than replace: the guard checks the path against the project root and against every enclosing directory that holds a `.git` entry, and blocks if any reading matches. Planting a `.git` can then only add checks, never remove one, while sibling worktrees are still covered. G01's child would make that change in its one correction round, plus two tests for the planted-`.git` case. Approve Amendment 01?"

**Recorded at:** 2026-11-13 (UTC), by the team lead (Control Tower supervisor session), during review of G01's first return. Nothing was committed or pushed.

## Why

G01 returned READY_FOR_AUDIT having built T04 as written: candidates are computed against `file_repo_root(path, project_root)` instead of `project_root`. `file_repo_root` returns the nearest directory holding a `.git` entry, so any `.git` file between the repository root and the file changes the reading. The supervisor compared the old guard (HEAD) and G01's guard on a temporary repository:

| Case | Old guard | G01's guard |
|---|---|---|
| `services/task-orchestrator/x.py`, nothing planted | BLOCKED | BLOCKED |
| same, with a planted `services/.git` file | BLOCKED | **ALLOWED** |
| same, with a planted `services/task-orchestrator/.git` file | BLOCKED | **ALLOWED** |

A `.git` file is an ordinary file that the Write tool can create outside the red lane, so the T04 wording opened a bypass the guard did not have before. The fault is in the issued packet, not in G01's work.

## What changes

T04 now reads:

> In `surface_guard_block` and `surface_guard_warnings`, the path is read against every root in this order: `project_root`, then every ancestor directory of the file's nearest existing ancestor that holds a `.git` entry (file or directory), nearest first. `surface_guard_block` blocks if any reading of any root matches. `surface_guard_warnings` takes the first contract-surface match over the same readings. Planting a `.git` entry can only add readings, never remove one. `project_root` stays the home of the warn cache. The control-character check is unchanged.

`file_repo_root(file_path, fallback)` keeps its definition and signature (nearest root, else `fallback`), because Wave 2B's W09 uses it for advisories. The list of roots comes from a new private helper in the same file, with no subprocess.

T06 gains two tests in `tests/unit/dcp_surface_guard/test_file_repo_root.py`:

- `test_planted_git_file_does_not_hide_a_red_lane_path`: `services/.git` and `services/task-orchestrator/.git` planted inside a main checkout; the edit stays blocked.
- `test_planted_git_file_in_sibling_worktree_does_not_hide_it`: a sibling worktree under the project with `services/.git` planted inside it; the edit stays blocked.

The write surface does not change. The edits are made by G01's child in its one correction round (A01). The issued packet files keep their hashes; this amendment is read alongside them.

## Counters at the first return

G01 child: 77,142 ms, 71,948 subagent tokens, 18 tool uses, advisor calls 0. Caps: 60 min, 600,000 tokens, 150 tool uses.
