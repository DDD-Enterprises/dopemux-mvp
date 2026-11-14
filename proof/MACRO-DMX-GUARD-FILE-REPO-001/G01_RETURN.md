# G01 return — the guard reads the file's own repo and notebook_path

**Status**: READY_FOR_AUDIT (child's word; acceptance is not the team lead's). Audit NOT_RUN, held for J-FREEZE.
**Commit**: `3d5226e0b` on `fix/guard-file-repo-root`. Rollback: `git revert 3d5226e0b`.
**Route**: requested `claude-code-agent` / `claude-sonnet-5-5` / effort UNKNOWN (Agent tool selector `sonnet`, `developer` agent). Observed model UNKNOWN: no runtime receipt.

## Attempts

| Round | Result | Duration | Subagent tokens | Tool uses | Advisor calls |
|---|---|---|---|---|---|
| First attempt | READY_FOR_AUDIT, built to T04 as issued | 77,142 ms | 71,948 | 18 | 0 |
| Correction round (Amendment 01) | READY_FOR_AUDIT | 42,234 ms | 79,977 | 10 | 0 |

Caps: 60 min, 600,000 tokens, 150 tool uses. The retry was not used. The supervisor found the bypass in the first attempt's review; the fault was in T04, not in the child's work (Amendment 01).

## Team lead's checks (re-run, not taken from the child)

| Command | Exit | Bucket |
|---|---|---|
| `pytest tests/unit/dcp_surface_guard/` | 0 | PASS, 8 passed (T06's six plus Amendment 01's two) |
| `pytest tests/test_dcp_surface_guard.py tests/unit/runner_memory_2a_r2_w09 tests/dcp` | 1 | 458 passed, 1 failed: the pre-existing `test_16_no_forbidden_files_modified` named in T07, same as the baseline |
| Same plus `tests/unit/dcp_surface_guard`, with `CLAUDECODE` unset | 1 | 466 passed, the same 1 pre-existing failure |
| The other test files that load the guard or the native hooks (`tests/coldstart/test_l0_membership.py`, `tests/test_config_sanitization.py`, `tests/test_native_hooks_workflow.py`, `tests/test_orchestrator_enforcement_hooks.py`, `tests/test_orchestrator_subagent_protocol.py`, `tests/unit/test_activity_ratelimit.py`) | 0 | PASS, 72 passed; also 72 with main's guard |
| `tests/unit/runner_memory_2a_r2_w06` | 0 | PASS, 24 passed |
| `git diff --check` | 0 | PASS |
| `git status --porcelain` before commit | — | PASS: only the three write-surface files |
| Scan of the changed files for home paths and e-mail addresses | — | PASS, no match |

## Old guard against new, on a scratch repository

`surface_guard_block` from main and from `3d5226e0b`, same inputs, project root = the scratch main checkout:

| Edit | Old | New |
|---|---|---|
| `services/task-orchestrator/x.py` in the main checkout | BLOCKED | BLOCKED |
| same, with `services/.git` planted | BLOCKED | BLOCKED |
| same, with `services/task-orchestrator/.git` planted | BLOCKED | BLOCKED |
| same path in a sibling worktree (`.worktrees/sib`, `.git` file) | allowed | BLOCKED |
| same, with `services/.git` planted in the sibling | allowed | BLOCKED |
| same path in a separate repository outside the project | allowed | BLOCKED |
| a symlink in the main checkout pointing into the red lane | BLOCKED | BLOCKED |
| `services/dopecon-bridge/ddg_mcp_stdio.py` (exempt), main and sibling | allowed | allowed |
| an ordinary file under `src/` | allowed | allowed |
| a NotebookEdit `notebook_path` in the sibling's red lane | allowed | BLOCKED |

Everything the old guard blocked stays blocked. Before Amendment 01, the two planted cases were allowed.

## For the auditor

- An edit inside any other git repository whose own layout has `services/task-orchestrator/` is now blocked from a session in this project. That is stricter than the plan required. The supervisor left it because it fails closed and the case is unlikely. An auditor may rule otherwise.
- `file_repo_root` is not used inside the guard after Amendment 01; it stays because Wave 2B's W09 uses it.
- A non-string `file_path` used to be turned into a string and is now ignored (T03).
- Shell-command and `apply_patch` edits are still unguarded; Wave 2B W09 owns them (plan row C17).
