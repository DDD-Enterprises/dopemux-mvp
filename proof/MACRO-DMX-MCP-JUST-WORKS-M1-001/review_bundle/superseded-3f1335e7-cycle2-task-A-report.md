# Cycle 2 Task A report

Status: DONE_WITH_CONCERNS (coordinator widened ownership for the stub change; the 13 A4 test breaks are fixed; everything green: 290 passed).

## A1 (tests/unit/test_docs_no_envrc_recipe.py:15)
`.claude/CLAUDE.md` -> `.claude/claude.md` (`git ls-files` confirms lowercase is the tracked name). RED not reproducible on macOS (case-insensitive FS); GREEN: file passes.
`grep -rn 'claude/CLAUDE.md' tests/` now only hits tests/integration/test_start_wave3.py lines 6, 9, 106, 109, which are docstring/comment prose explaining the case collision, not paths; left alone.

## A2 (src/dopemux/cli.py, `native_hooks_register`)
Added `session_end_timeout_s = 60` (one place). New SessionEnd hook = `{"type","command","timeout":60}`; an existing full-matcher registration with `command == cmd` and no `timeout` key gets 60 and `changed = True`; an existing `timeout` (any value) is untouched; other events unchanged. Mirrors `.claude/settings.json` (`"timeout": 60`).
Tests added to tests/unit/test_native_hooks_register.py (5): fresh -> 60 and no timeout key on other events; existing without timeout -> patched, rewritten, `.bak` holds old file; sole-stale-timeout case rewrites (no "already registered"); existing `timeout: 120` untouched and "already registered", no backup; second run no-op.
RED: `3 failed, 17 passed` before the change. GREEN: `20 passed`.

## A3 (src/dopemux/mcp/mcp_json.py, `_url_is_repairable`)
Removed the `"${" in url` early return. New `_neutralize_placeholders` (`${N:-d}` -> `d`, `${N}` -> `placeholder`; `import re` added), then urlparse with the same host rules (localhost/127.0.0.1), any userinfo -> False, leftover `$ { }` in netloc -> False, parse ValueError -> False, templated URL with empty host (e.g. `${URL}`) -> False. None/empty -> True. Literal-URL behaviour unchanged.
Tests added to tests/unit/test_mcp_config_repair.py: 21 parametrized cases (both Copilot examples, `http://${HOST}:3005/sse`, the three catalog-rendered URLs, etc.) plus an end-to-end plan test that a templated remote conport URL is preserved, not replaced. RED: 10 failed; GREEN: `35 passed`.
Note: `${PORT-3005}` (no colon) is treated as a name `PORT-3005`, so in the port position it stays repairable (host still local); in host position it is `placeholder` -> False. Pinned in tests.

## A4 (src/dopemux/commands/mcp_commands.py)
- `_run_lifecycle_cli`: `_load_catalog(Path(repo_arg).expanduser().resolve())` when `repo_arg is not None`, else `_load_catalog()`.
- `mcp_switch_project_cmd`: `_load_catalog(target)`.
- `mcp_init_cmd`: `_load_catalog(repo_path)`.
- `mcp_repair_config_cmd`: `_load_catalog(repo_path)` and, beyond the brief, `_catalog_path(repo_path)` (otherwise the reported `catalog_paths` would name the caller's catalog while the target's was loaded).
New tests/unit/test_mcp_commands_repo_catalog.py (8): `init --repo <target> --with target-only-svc` from another cwd succeeds and renders the extra server (no stubs of `_load_catalog`); init without `--repo` still uses the cwd checkout's catalog (target-only server unknown); `_run_lifecycle_cli` for start/stop/restart/status calls `_load_catalog` with the resolved path (monkeypatched `_load_catalog` and `run_lifecycle`); without `--repo` calls `_load_catalog()` with no args. RED against HEAD's mcp_commands.py: 5 failed, 2 passed; GREEN: 7 passed. No dedicated switch-project test (command needs Docker; change is one argument).

Survey of `_load_catalog()` sites (line numbers at HEAD before edits):
| site | decision |
|---|---|
| 1600 mcp_generate_cmd | cwd-only: no --repo option |
| 1961 mcp_ensure_cmd | cwd-only: no --repo |
| 2309 mcp_add_cmd | cwd-only: uses cwd git root, no --repo |
| 2381 mcp_list_cmd | cwd-only: no --repo |
| 2532 mcp_doctor_cmd | LEFT cwd-only: `repo_arg` is resolved AFTER the load (and `_catalog_path()` too); same defect class, flagged below |
| 2588 _mcp_doctor_legacy | cwd-only: legacy rejects --repo |
| 2661 _mcp_doctor_profile | LEFT: `repo_arg` resolved after the load; same defect class, flagged |
| 2707 profile list | cwd-only: no --repo |
| 2745 profile show | LEFT: `repo_arg` resolved after the load; same defect class, flagged |
| 2815 leases reconcile | cwd-only: host-wide registry, no --repo |
| 3006 fleet init / 3064 fleet doctor | cwd-only by design: take many --worktrees, a single catalog is the fleet's |
| 3099 sync-globals | cwd-only: global ~/.claude.json, no --repo |
| 3211 snapshot-tools | cwd-only: live fleet, no --repo |

### Stub widening (coordinator ruling, ownership widened)
Every `_load_catalog` / `_catalog_path` monkeypatch in the five files now accepts arguments (`lambda *_a, **_k: ...`; conport_tenant wraps `_init_catalog()`); no other edits, assertions unchanged (confirmed via `git diff`: only lambda lines).
| file | stubs widened |
|---|---|
| tests/unit/test_mcp_commands_catalog.py | 21 `_load_catalog` + 2 `_catalog_path` (42 lines) |
| tests/unit/test_mcp_commands_lifecycle.py | 5 `_load_catalog` |
| tests/unit/test_mcp_commands_repair.py | 1 `_load_catalog` + 1 `_catalog_path` (fixture) |
| tests/unit/test_mcp_conport_tenant.py | 1 `_load_catalog` (`_init_catalog`) + 1 `_catalog_path` |
| tests/unit/test_mcp_identity_git_only.py | 1 `_load_catalog` + 1 `_catalog_path` (fixture) |

### repair-config catalog path assertion
Added `test_repair_config_repo_reports_and_uses_the_targets_catalog` to tests/unit/test_mcp_commands_repo_catalog.py (real catalogs, no stubs): `repair-config --repo <target> --dry-run --json` from another cwd reports `inputs.catalog_paths == [<target>/mcp_catalog.yaml]`. RED verified by reverting `_catalog_path(repo_path)` to `_catalog_path()` (fails), GREEN with the change. The two existing repair tests pass with the widened stubs.

### doctor --repo decision: LEFT UNCHANGED
Not a pure reorder. In `mcp_doctor_cmd` the lines between `_load_catalog()` and the `--repo` resolution are `catalog_path = _catalog_path()` and `catalog_paths = [...]`; these do not read the loaded catalog but they take the same cwd-based lookup, so they would have to move and take the resolved repo as well (otherwise the reported `catalog_paths` would name the caller's catalog). The fix would also make the 4 doctor tests in tests/unit/test_mcp_doctor_repo_aware.py (lines 765-766, 789-790, 952, 1086: zero-arg `_load_catalog`/`_catalog_path` stubs and a zero-arg `def _catalog`) fail until their stubs are widened; that file is outside the granted ownership.

### Deferred, same defect class
- `mcp doctor --repo` (above)
- `mcp doctor --profile ... --repo` (`_mcp_doctor_profile`: catalog loaded before `repo_arg` is resolved)
- `mcp profile show --repo` (catalog loaded before `repo_arg` is resolved)

## A5 (AGENTS.md:310-313)
Replaced the stale "first launch in a new worktree builds its images" sentence with the images-are-shared wording from the brief, wrapped in the paragraph's style. Nothing else touched. tests/unit/test_docs_no_envrc_recipe.py, test_mcp_fleet_catalog.py, tests/test_model_routing_consistency.py pass.

## A6 (verify only)
docs/02-how-to/mcp-setup-other-repos.md lines 118-121 ("Approve the project servers once ... `Pending approval` ... Claude Code's prompt, not a launcher failure") and lines 491-494 (Troubleshooting: "Pending approval" is Claude Code waiting for you to approve the project servers once) both exist and are correct. No edit needed; not edited.

## Formatting
black / isort: NOT_RUN (neither binary exists in .venv/bin).

## Final focused run
owned + widened files + brief list + snapshot/fleet/fleet_catalog: `290 passed`, 0 failed (includes test_mcp_doctor_repo_aware, test_mcp_launcher_render, test_cli_audit_remediations).

## Self-review / concerns
- Doctor, profile doctor and profile show with `--repo` still load the caller's catalog; deferred (see above).
- `_catalog_path(repo_path)` in repair-config kept per coordinator ruling.
- Not committed, staged or stashed. Changed files: AGENTS.md, src/dopemux/cli.py, src/dopemux/commands/mcp_commands.py, src/dopemux/mcp/mcp_json.py, tests/unit/test_docs_no_envrc_recipe.py, tests/unit/test_native_hooks_register.py, tests/unit/test_mcp_config_repair.py, tests/unit/test_mcp_commands_repo_catalog.py (new), plus the five widened files: test_mcp_commands_catalog.py, test_mcp_identity_git_only.py, test_mcp_commands_lifecycle.py, test_mcp_conport_tenant.py, test_mcp_commands_repair.py.

## Fix round 1 (reviewer: tests/unit/test_mcp_switch_project.py stub)

Change: tests/unit/test_mcp_switch_project.py:34 `_load_catalog` stub `lambda: ...` -> `lambda *_a, **_k: ...` (only edit; intent unchanged). That file's 7 tests had raised TypeError from `_load_catalog(target)` in `mcp_switch_project_cmd`; my earlier focused run did not include it.

Survey, `grep -rn "_load_catalog\|_catalog_path" tests/` (zero-arg stubs left) against the call each exercised command makes (mcp_commands.py at the current tree):
| test file | stub(s) left zero-arg | command exercised | call it makes | still bare? |
|---|---|---|---|---|
| test_mcp_commands_snapshot.py (34,75,129,147,179,207) | `_load_catalog` | `mcp snapshot-tools` (mcp_snapshot_tools_cmd, line 3218) | `_load_catalog()` | yes |
| test_mcp_profile_doctor.py (24,44,59,72 ,85) | `_load_catalog` | `mcp_doctor_cmd --profile ...` -> `_mcp_doctor_profile` (2668); `profile list` (2714); `profile show` (2752) | `_load_catalog()` | yes (deferred, unchanged) |
| test_mcp_doctor_repo_aware.py (765,789,952,1086) | `_load_catalog`; `_catalog_path` at 766,790 | `mcp doctor --repo` (2539-2540) | `_load_catalog()`, `_catalog_path()` | yes (doctor left unchanged) |
All other test files in the grep were already widened (catalog, identity_git_only, lifecycle, conport_tenant, repair, switch_project) or use their own launcher-module stubs (`launcher._load_catalog`, already `*a, **k`). tests/commandcode_router/test_normalized_catalog.py defines an unrelated local `_load_catalog`. src callers with an argument: lines 172 (`_run_lifecycle_cli`, only with `--repo`), 421 (switch-project), 2175 (init), 2937-2938 (repair-config), plus the pre-existing launcher path; every other src call is bare. src/dopemux/mcp/instance_overlay.py:81 imports and calls it bare.

Command and output:
`.venv/bin/python -m pytest tests/unit/test_mcp_switch_project.py tests/unit/test_mcp_commands_snapshot.py tests/unit/test_mcp_profile_doctor.py tests/unit/test_mcp_doctor_repo_aware.py tests/unit/test_docs_no_envrc_recipe.py tests/unit/test_native_hooks_register.py tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_commands_repo_catalog.py tests/unit/test_mcp_commands_catalog.py tests/unit/test_mcp_identity_git_only.py tests/unit/test_mcp_launcher_render.py tests/unit/test_cli_audit_remediations.py tests/unit/test_mcp_commands_lifecycle.py tests/unit/test_mcp_conport_tenant.py tests/unit/test_mcp_commands_repair.py tests/unit/test_mcp_fleet_catalog.py tests/unit/test_mcp_fleet.py -q -p no:cacheprovider`
-> `304 passed in 9.64s`.
Files now changed additionally: tests/unit/test_mcp_switch_project.py.

## Task A2 (Codex P1/P2: `init --repo <subdir>` kept the subdirectory)

Facts read: `resolve_project_identity` returns `ProjectIdentity(worktree_root, project_root, git_common_dir)`; `worktree_root` is `git rev-parse --show-toplevel` of the cwd given (or `DOPEMUX_WORKSPACE_ROOT` when env is passed, i.e. `--trust-env`). Outside git it falls back to the given dir and then `_resolve_common_dir` fails, which `mcp_init_cmd` already turns into the "Could not resolve project identity" ClickException (new test pins that nothing is written).

Changes (src/dopemux/commands/mcp_commands.py only, plus one doc half-sentence):
- New helper `_git_toplevel(path)`: git top-level of any directory inside a checkout, the resolved path itself outside git.
- `mcp_init_cmd`: after identity resolution, `repo_path`/`repo` become `identity.worktree_root` when it is an enclosing directory of the given target (so catalog lookup, profile inventory, port/lease allocation, sidecars, all file writes and the printed next steps use the root). The enclosing-only guard means an ambient `--trust-env` workspace override pointing elsewhere never redirects the writes away from `--repo` (previous behaviour kept). Identity doubles without `worktree_root` (existing tests) are tolerated via `getattr`.
- `_run_lifecycle_cli`: catalog from `_git_toplevel(repo_arg)`.
- `switch-project`: `target = _git_toplevel(lc.resolve_target_repo(repo_arg))`.
- `repair-config` via `_resolve_repo_arg`: explicit branch now returns `_git_toplevel(repo_arg)`, so `plan_repair` writes `.mcp.json`/envrc at the root and `_catalog_path(repo_path)` reports the root's catalog.
- docs/02-how-to/mcp-setup-other-repos.md line 93: "any directory inside a checkout is accepted and normalized to its root".

Resolver survey:
| site | resolver | normalizes explicit subdir to toplevel before? | action |
|---|---|---|---|
| init | `Path(repo_arg).resolve()` | no | fixed (identity.worktree_root) |
| lifecycle start/stop/restart/status | `lc.resolve_target_repo(explicit)` inside `run_lifecycle` returns the resolved path as given (only the no-`--repo` branch uses git toplevel); worktree root then comes from `resolve_identity_view` -> `identity.worktree_root`, which IS the toplevel | lifecycle itself yes (via identity view), but my CLI-side catalog load used the raw subdir | catalog load fixed with `_git_toplevel`; `run_lifecycle(repo=repo_arg)` left raw (harmless, it normalizes) |
| switch-project | `lc.resolve_target_repo(explicit)` (no normalization); identity via `resolve_identity_view(target)` normalizes | target and catalog used the subdir | fixed (`_git_toplevel`) |
| repair-config | `_resolve_repo_arg` (explicit branch had no normalization); `plan_repair` resolves the path as given | no | fixed in `_resolve_repo_arg` |

Tests (tests/unit/test_mcp_commands_repo_catalog.py, 15 total now, +7): init `--repo <checkout>/src/pkg` from another cwd writes `.mcp.json` and `.envrc.dopemux-mcp` at the root only, uses the checkout's repo-local catalog (`--with target-only-svc`), envrc names the root, output names the root and not the subdir; init `--repo <non-git dir>` still errors and writes nothing; `_resolve_repo_arg(subdir) == toplevel`; `_git_toplevel` degrades outside git; `_run_lifecycle_cli` loads the toplevel catalog for a subdirectory; `repair-config --repo <subdir>` reports repo, `.mcp.json` path and catalog path of the root; `resolve_identity_view(subdir).worktree_root == toplevel` (survey fact). RED against the previous code: 5 failed (init subdir, `_resolve_repo_arg`, `_git_toplevel` missing, lifecycle, repair-config), 10 passed. GREEN: 15 passed.
No dedicated switch-project subdirectory test (Docker-bound command; shares `_git_toplevel`).

Run: `.venv/bin/python -m pytest tests/unit/test_mcp_switch_project.py tests/unit/test_mcp_commands_lifecycle.py tests/unit/test_docs_no_envrc_recipe.py tests/unit/test_native_hooks_register.py tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_commands_repo_catalog.py tests/unit/test_mcp_commands_catalog.py tests/unit/test_mcp_identity_git_only.py tests/unit/test_mcp_doctor_repo_aware.py tests/unit/test_mcp_launcher_render.py tests/unit/test_cli_audit_remediations.py tests/unit/test_mcp_conport_tenant.py tests/unit/test_mcp_commands_repair.py tests/unit/test_mcp_commands_snapshot.py tests/unit/test_mcp_profile_doctor.py tests/unit/test_mcp_fleet_catalog.py tests/unit/test_mcp_fleet.py -q -p no:cacheprovider` -> `334 passed in 11.73s`.
Files changed in A2: src/dopemux/commands/mcp_commands.py, tests/unit/test_mcp_commands_repo_catalog.py, docs/02-how-to/mcp-setup-other-repos.md. Nothing staged or committed.
Still deferred (same family, `--repo` subdir not normalized there either): `doctor --repo`, `doctor --profile --repo`, `profile show --repo`.

## Task A2 fix round

Important finding (accepted): `_run_lifecycle_cli` passed the raw `repo_arg` to `run_lifecycle(repo=...)`. Correction of my A2 survey row: `run_lifecycle` only normalizes the identity half (`resolve_identity_view`); it first calls `resolve_target_repo(repo)` (returns an explicit path unchanged) and reads `.envrc.dopemux-mcp` / `.mcp.json` from that `target`, so `--repo <subdir>` would have loaded the ROOT catalog but read the config from the subdirectory. Fixed: `_run_lifecycle_cli` computes `target_root = _git_toplevel(repo_arg)` once (when `repo_arg is not None`) and passes it to both `_load_catalog` and `run_lifecycle(repo=...)` (mcp_commands.py ~172-202).

Tests (tests/unit/test_mcp_commands_repo_catalog.py, 19 total):
- NEW real (not faked) test `test_status_repo_subdirectory_reads_mcp_json_from_the_checkout_root`: `status --repo <checkout>/src/pkg --json` with docker inspection stubbed as in test_mcp_commands_lifecycle.py; asserts `project_identity.worktree_root` is the checkout root and that the root `.mcp.json` server appears in `services`. RED with `repo=repo_arg` restored (5 failed incl. this one), GREEN with the fix.
- Existing faked-lifecycle test now also asserts `seen["repo"] == target.resolve()` (the `repo=` argument).
- Minor (a): non-git init test asserts "Could not resolve project identity".
- Minor (b): `_git_toplevel` on a nonexistent path returns the resolved input; with `subprocess.run` raising OSError / TimeoutExpired it returns the resolved input path (3 tests).
- switch-project subdirectory test skipped (Docker-bound), as instructed.

Run (focused list + lifecycle + switch_project): `338 passed in 13.03s`.

Residuals:
- macOS case-insensitivity: a `--repo` typed with different case than git's toplevel makes the `init` enclosing-directory check (`worktree_root in repo_path.parents`) fail, so `init` keeps the typed path instead of switching to the root (the other sites use `_git_toplevel` directly and are unaffected).
- Deferred, same family: `doctor --repo`, `doctor --profile --repo`, `profile show --repo`.

## Task A3 (Copilot: host-placeholder default does not prove locality)

Change (src/dopemux/mcp/mcp_json.py): new `_placeholder_in_userinfo_or_host(url)` masks each `${...}` in the raw authority as one opaque character (so the `:` in `${PORT:-3005}` is not read as the port separator), splits userinfo / host / port, and returns True when a placeholder sits left of the port separator (userinfo, host, or inside an IPv6 bracket). `_url_is_repairable` returns False for such URLs before neutralization. Port-, path- and query-position placeholders are neutralized as before; all existing fail-closed rules (leftover `$ { }` in netloc, parse failure, userinfo, fully templated URL, non-local host) are unchanged.

Tests (tests/unit/test_mcp_config_repair.py): flipped `http://${CONPORT_HOST:-localhost}:3005/sse` to False; added `http://${HOST:-127.0.0.1}:3005/sse`, `http://${USER:-x}@localhost:3005/sse`, `http://[${HOST:-::1}]:3005/sse`, `http://local${SUFFIX:-host}:3005/sse` (all False). Kept True: `http://localhost:${CONPORT_PORT:-3005}/sse`, `http://127.0.0.1:${PORT}/mcp`, `http://localhost:${PORT-3005}/sse`, and the three catalog-rendered URLs; the end-to-end "templated remote conport URL is preserved" test is unchanged and passes. RED first: 3 failed (the CONPORT_HOST flip, `${HOST:-127.0.0.1}`, `local${SUFFIX:-host}`; the userinfo and IPv6 cases were already False via the userinfo/netloc rules), GREEN after the change.

Run: `.venv/bin/python -m pytest tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_launcher_render.py tests/unit/test_mcp_commands_repo_catalog.py -q -p no:cacheprovider` -> `68 passed in 2.23s`. No `.env*` file touched; nothing staged or committed.
