# Cycle 2 — Task A: mechanical fixes batch (PR #1503 bot findings + AGY low)

Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1` (branch `feat/mcp-just-works-m1`, HEAD 0cde3a921 = origin/main merged in). Python: `.venv/bin/python` in the worktree (Python 3.12). Run focused tests with `.venv/bin/python -m pytest <files> -q -p no:cacheprovider`.

Every item below is a reviewer finding on the open PR. Fix each one exactly as described; do not widen. Test-first for every code change: write or extend the test, see it fail, make it pass.

## A1. Test parametrizes the wrong filename case (Copilot; CI "Unit Tests" is red on Linux)

File: `tests/unit/test_docs_no_envrc_recipe.py` line 15, the `DOCS` tuple.
The tracked document is `.claude/claude.md` (lowercase; confirm with `git ls-files .claude | grep -i 'claude.md$'`). `.claude/CLAUDE.md` only resolves on case-insensitive macOS; on Linux CI the test raises `FileNotFoundError`.
Change the entry to `".claude/claude.md"`. Run the test file. (No other test should name `.claude/CLAUDE.md`: `grep -rn 'claude/CLAUDE.md' tests/` must come back empty afterwards; if other hits exist, fix them the same way and list them.)

## A2. `native-hooks register` emits SessionEnd hooks without a timeout (Copilot)

File: `src/dopemux/cli.py`, command `native_hooks_register` (search `@native_hooks.command("register")`, body around lines 4170–4280). Tests: `tests/unit/test_native_hooks_register.py`.

Why: the project's own `.claude/settings.json` gives the SessionEnd hook `"timeout": 60` because SessionEnd hooks otherwise share a 1.5 s budget and the SessionEnd handler can spend up to 45 s reaping before saving session history. The register command writes SessionEnd entries without it, so registrations in other projects or in `~/.claude/settings.json` get killed early.

Required behaviour (SessionEnd only; every other event stays exactly as today, no `timeout` key):
1. A new SessionEnd registration is `{"type": "command", "command": cmd, "timeout": 60}`.
2. An existing full-matcher group (matcher omitted, `""` or `"*"`) that already contains a hook whose `command == cmd` for SessionEnd but has no `timeout` (or a different one? no: only add when the key is absent) gets `"timeout": 60` set on that hook entry, and `changed = True`, so the file is rewritten (backup + atomic replace as today) and the success message prints.
3. An existing SessionEnd registration that already has `timeout` is left alone (still "already registered" when nothing else changed).
4. Idempotent: running register twice changes nothing the second time.

Keep the constant in one place in that function (e.g. `session_end_timeout_s = 60`) and mirror the shape in `.claude/settings.json` (read it: `python3 -c 'import json;print(json.load(open(".claude/settings.json"))["hooks"]["SessionEnd"])'`).

Tests to add in `tests/unit/test_native_hooks_register.py` (follow the file's existing fixtures/invocation style; read it first): (a) fresh registration → SessionEnd hook has `timeout == 60`, `Stop` hook has no `timeout` key; (b) pre-existing SessionEnd registration without timeout → patched to 60 and the file is rewritten; (c) pre-existing with `timeout: 60` → unchanged, "already registered" path; (d) second run is a no-op.

## A3. `_url_is_repairable()` accepts any templated URL (Copilot)

File: `src/dopemux/mcp/mcp_json.py`, function `_url_is_repairable` (around line 225). Tests: `tests/unit/test_mcp_config_repair.py` (read it first; add cases there).

Bug: the early `if "${" in url: return True` makes every URL containing a `${...}` placeholder "repairable", so an operator-pointed remote or credential-bearing endpoint such as `https://remote.example:${REMOTE_PORT:-443}/sse` or `http://user:${PASSWORD}@localhost:3005/sse` is replaced by a local launcher entry and its URL/env is lost. The guard exists precisely to preserve such entries (see the `preserved` list at the call site, reason "non-localhost or credential URL preserved").

Required behaviour: remove the early return. Neutralize placeholders before parsing, then apply the same host and userinfo rules as for literal URLs:
- `${NAME:-default}` → `default`; `${NAME}` (no default) → the literal token `placeholder`.
- Parse with `urlparse`. Hostname must be in the existing local set (`localhost`, `127.0.0.1`); a hostname that is the `placeholder` token, or anything else, is NOT provably local → `False`.
- Any userinfo (`parsed.username`/`parsed.password`, or `@` in the netloc) → `False`, templated or not.
- A URL that still contains `$`, `{` or `}` in its netloc after neutralization, or fails to parse → `False`.
- Missing/None URL → `True` (unchanged).

Cases to test (at least): the two Copilot examples → `False`; `http://${HOST}:3005/sse` → `False`; `http://localhost:${CONPORT_PORT:-3005}/sse` → `True`; `http://127.0.0.1:${PORT}/mcp` → `True`; `http://${CONPORT_HOST:-localhost}:3005/sse` → `True`; `http://localhost:3005/sse` → `True`; `https://remote.example/sse` → `False` (existing behaviour). Also check the templated URLs the catalog itself renders (`grep -n 'url:' src/dopemux/mcp/mcp_catalog.yaml | grep '\${'`) still count as repairable where the host is localhost; existing tests in `test_mcp_config_repair.py` must keep passing without weakening them.

## A4. `init --repo <target>` loads the caller's catalog, not the target's (Codex P2)

File: `src/dopemux/commands/mcp_commands.py`. `_load_catalog(repo: Optional[Path] = None)` (line ~918) → `_catalog_path(repo)` looks for `<repo>/mcp_catalog.yaml` and falls back to the bundled default. `mcp_init_cmd` (line ~2168) resolves the target (`repo_path`, from `--repo` or the cwd checkout) and then calls `_load_catalog()` with no argument, so a target with a repo-local catalog gets the caller's (or bundled) catalog: target-only `--with` services fail as unknown and differing defaults render config and leases from the wrong catalog. The launcher already loads the target checkout's catalog (`launcher.py`: `_load_catalog(launch_root)`).

Required changes (same defect class, identical pattern; keep `_load_catalog()` when no target was given):
1. `mcp_init_cmd`: `catalog = _load_catalog(repo_path)` (the resolved target, always known there).
2. `_run_lifecycle_cli` (line ~170, shared by `start/stop/restart/status --repo`): pass the resolved `--repo` path when `repo_arg is not None` (`Path(repo_arg).expanduser().resolve()`), else `_load_catalog()`.
3. `mcp_switch_project_cmd` (line ~412–416): `target = lc.resolve_target_repo(repo_arg)` precedes the load → `_load_catalog(target)`.
4. The site at line ~2929–2930 (`repo_path = _resolve_repo_arg(repo_arg, ...)` then `_load_catalog()`) → `_load_catalog(repo_path)`.
5. Survey every other `_load_catalog()` call in the file (`grep -n '_load_catalog()' src/dopemux/commands/mcp_commands.py`); fix any other site where a `--repo`/`repo_arg` target has been resolved just before, and list in your report the sites you left as cwd-only (with one line each on why).

Tests: read `tests/unit/test_mcp_commands_catalog.py`, `tests/unit/test_mcp_identity_git_only.py` and `tests/unit/test_mcp_doctor_repo_aware.py` for the existing patterns of (a) a temp git repo with a repo-local `mcp_catalog.yaml` and (b) how `init` is exercised with its heavy steps stubbed (tenant provisioning, image pre-build, docker). Add: `init --repo <target>` invoked from a different cwd, where only the target's catalog defines an extra per-worktree server, with `--with <that-server>` → succeeds and the rendered `.mcp.json` in the target contains it; and a unit test that `_run_lifecycle_cli("status", repo_arg=<path>, ...)` calls `_load_catalog` with the resolved path (monkeypatch `_load_catalog` and `run_lifecycle`). Put new tests in a new file `tests/unit/test_mcp_commands_repo_catalog.py` if the existing files do not fit.

## A5. Stale sentence in AGENTS.md §12 (AGY low finding F1 at 30b0fdec9)

File: `AGENTS.md` lines ~309–310: "The first launch in a new worktree builds its images (`LAUNCH_IMAGE_BUILDING`; then `/mcp reconnect all`)." is stale: images are tagged `dopemux-<service>:<key>` per service and Dockerfile version and shared by every worktree and project on the host, so only the first launch on a host per Dockerfile version builds. Replace that one sentence with wording consistent with `.claude/claude.md` (its "MCP Transport and Setup Rules" paragraph on images) and `docs/02-how-to/mcp-setup-other-repos.md` lines 122–128, e.g.: "Images are one per service and Dockerfile version (`dopemux-<service>:<key>`), shared by every worktree and project on the host: only the first launch on a host per Dockerfile version builds (`LAUNCH_IMAGE_BUILDING`, then `/mcp reconnect all`); later worktrees reuse them." Keep the paragraph's wrapping style. Do not change anything else in AGENTS.md. Re-run `tests/unit/test_docs_no_envrc_recipe.py` and `grep -rln 'AGENTS.md' tests/unit` for tests that assert on §12 text; run those.

## A6. "Pending approval" note in the how-to (acceptance finding 6) — verify only

`docs/02-how-to/mcp-setup-other-repos.md` already explains "Pending approval" at lines ~118–121 and ~491–494. Read them and confirm in your report that no edit is needed. Do not edit the how-to (another implementer owns it in this cycle).

## Ownership and shared-workspace rules

- You own exactly: `tests/unit/test_docs_no_envrc_recipe.py`, `src/dopemux/cli.py`, `tests/unit/test_native_hooks_register.py`, `src/dopemux/mcp/mcp_json.py`, `tests/unit/test_mcp_config_repair.py`, `src/dopemux/commands/mcp_commands.py`, `tests/unit/test_mcp_commands_repo_catalog.py` (new, optional), `AGENTS.md`. If a fix genuinely needs another file, stop and report NEEDS_CONTEXT naming it.
- Another implementer is editing `src/dopemux/mcp/reap.py`, `lifecycle.py`, `launcher.py`, their tests, the how-to and the design doc at the same time. Never open those for editing, never revert anything in them. A focused test of yours can fail transiently because one of those modules is mid-edit (import error): wait 30 s and retry once; if it persists, report it, do not touch their files.
- Do NOT commit, `git add`, `git stash`, `git checkout`, `git reset` or `git clean`. The controller commits your files by explicit path after your report. Leave your changes in the working tree.
- Do not run `make test-fast` or the whole `tests/unit` tree (the controller runs it once at the end); run the focused files above plus `tests/unit/test_mcp_commands_catalog.py`, `tests/unit/test_mcp_identity_git_only.py`, `tests/unit/test_mcp_doctor_repo_aware.py`, `tests/unit/test_mcp_launcher_render.py` and `tests/unit/test_cli_audit_remediations.py` at the end.
- Format: `.venv/bin/black` and `.venv/bin/isort` (repo config) on the files you changed, if those binaries exist in the venv; otherwise say NOT_RUN.
- Secrets: never print or write credentials; the tests here need none.
- Sealed paths (never touch): `docker/mcp-servers-source/conport/`, `scripts/migration/provision_conport_project_db.sh`, `.claude/`, `proof/`.
- Do not dispatch subagents and do not call the `advisor` tool. Do all reading yourself.

## Report

Write the full report to `.superpowers/sdd/mcp-just-works-m1-plan-2026-11-05/cycle2-task-A-report.md`: per item A1–A6 what changed (file:line), the RED/GREEN evidence (command + relevant output), the survey table for A4 item 5, formatting results, self-review findings, concerns. Then reply with ONLY: Status (DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT), the list of files changed, a one-line test summary, concerns, the report path.
