---
id: mcp-just-works-m1-plan-2026-11-05
title: Dopemux MCP "Just Works" M1 — Implementation Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-05'
last_review: '2026-11-05'
next_review: '2026-12-05'
status: DRAFT plan for the approved design; execution gated on owner confirmation of the post-approval design changes (design §9) and choice of execution method
prelude: Task-by-task implementation plan for Milestone 1 of claudedocs/mcp-just-works-design-2026-11-05.md. Nine tasks, each a PR-sized MacroPacket child with its own tests. Lives in claudedocs/ per docs/03-reference/filesystem-guide.md rather than the superpowers default docs/superpowers/plans/.
---
# ━━━◆ Ø ◆━━━

# Dopemux MCP "Just Works" M1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Any checkout of a set-up dopemux project connects `conport`, `dope-memory` and `task-orchestrator` correctly with zero typing, hooks run in every worktree, and worktree sidecars are cleaned up without a daemon.

**Architecture:** Identity comes from git only. Each `.mcp.json` entry becomes a stdio launcher (`dopemux mcp launch <server>`) that finds or starts the worktree's sidecars through the existing lifecycle, with ports from the lease registry, and proxies to them over the official `mcp` SDK. Locks guard the registries and the reserved orchestrator port. ConPort tenants are provisioned on first start with credentials kept under `~/.dopemux`. Cleanup is a reap pass triggered from hooks and launcher starts.

**Tech Stack:** Python 3.12 (`.venv`), click, `mcp` SDK 1.29 (anyio), docker compose through `src/dopemux/mcp/lifecycle.py`, POSIX `sh` for the hook dispatcher, pytest under `tests/unit/` so `make test-fast` runs every new test.

**Spec:** `claudedocs/mcp-just-works-design-2026-11-05.md` (read it first; "D" references below are its decisions).

**Location note:** this plan lives in `claudedocs/` because `docs/03-reference/filesystem-guide.md` reserves that directory for Claude-authored design; do not move it to `docs/superpowers/plans/`.

## Global Constraints

- Work on branch `feat/mcp-just-works-m1` in `<repo>/.worktrees/mcp-just-works-m1`, cut after Task 0 lands. PR route only; never local-merge to `main`. Each task is one MacroPacket child with one mutating implementer, `TP_ROUTE` emitted before dispatch, and an independent L3 audit before merge (AGENTS.md §5, §9).
- Commit per task with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` as the last trailer.
- Ambient `DOPEMUX_WORKSPACE_ROOT`, `DOPEMUX_PROJECT_ROOT`, `DOPEMUX_INSTANCE_ID`, `DOPEMUX_WORKSPACE_ID` and `TASK_ORCHESTRATOR_PROJECT_ROOT` are ignored by every lifecycle command and by the launcher unless `--trust-env` is passed (D3).
- `instance_id` stays `sha1(str(Path(p).resolve()))[:4]` (`port_diagnostics.instance_id_for_path`); lease keys depend on it. `project_id` stays `ProjectIdentity.project_id`. The per-worktree runtime dir stays `~/.dopemux/mcp/runtime/<slug>-<worktree_hash>/` (`lifecycle.py:1207`).
- Rendered launcher entry shape (D1, D2): `{"type": "stdio", "command": "${DOPEMUX_BIN:-dopemux}", "args": ["mcp", "launch", "<name>"], "description": "..."}` with no `env` block.
- Secrets only in `~/.dopemux/mcp/projects/<project_id>/secrets.env`, file mode `0600`, directory `0700`; never in `mcp.env`, never in the repo, never printed (D5).
- Locks are `fcntl.flock` on files: `~/.dopemux/mcp/runtime/registry.lock`, `<runtime_dir>/launch.lock`, `~/.dopemux/mcp/runtime/reserved-7890.lock`, `~/.dopemux/mcp/projects/<project_id>/provision.lock`. Order when nested: instance lock outside, registry lock inside; reserved-port lock outside, registry lock inside; never the reverse (D7).
- Launch wait default 25 s (`DOPEMUX_LAUNCH_WAIT`); backend probe timeout 1 s; reap idle window 1200 s; Stop-hook reap throttle 600 s (D4, D8).
- Reap never touches a container whose `dopemux.scope` label is `project` or `singleton`, and never one without `dopemux.managed=true` (D8).
- `docker/mcp-servers-source/conport/` is red-lane sealed: read `schema.sql` and `migrations/`, never edit them. `scripts/migration/provision_conport_project_db.sh` stays untouched.
- No new always-running process (N6). No raw `docker compose up` outside `lifecycle.py` (A6).
- Validate docs with `.venv/bin/python scripts/docs_validator.py <file>` and `scripts/docs_frontmatter_guard.py <file>`; repo-wide runs fail on pre-existing files and are not a gate here.

## Review Focus

1. A session whose working directory is a subdirectory of the checkout must resolve the checkout's identity, not a per-subdirectory instance. Pinned by Task 2 `test_resolve_target_repo_uses_git_toplevel_from_subdir` and Task 3c `test_resolve_launch_root_from_subdirectory`.
2. A checkout reached through a symlink (macOS `/tmp` is `/private/tmp`) must yield the same `project_id` and `instance_id` as its real path. Pinned by Task 2 `test_identity_stable_across_symlinked_path`.
3. A launcher started outside any git repo, or in a repo whose `.mcp.json` was hand-written, must refuse with a code and make no docker call. Pinned by Task 3c `test_launch_refuses_outside_git_without_docker` and `test_launch_refuses_unmanaged_mcp_json`.
4. A corrupt or empty registry file must not crash a launcher or make reap stop anything. Pinned by Task 3b `test_locked_reload_tolerates_corrupt_registry` and Task 5 `test_plan_reap_with_corrupt_registry_is_empty`.
5. A hook payload without `cwd`, or non-JSON on stdin, must exit 0 and block nothing. Pinned by Task 1 `test_main_without_cwd_uses_process_cwd` and `test_dispatcher_passes_exit_code_through`.

---

### Task 0: Prerequisites (owner-gated, no code)

**Files:** none.

**Interfaces:**
- Produces: a `main` containing #1439 (`native-hooks register` event-keyed schema; `tests/unit/test_native_hooks_register.py`), #1456 (`docker_runtime.COMPOSE_HOST_PATH_VARS`, `RuntimeRegistry.find_stale_running`/`reconcile_stale_running`, `dopemux mcp registry reconcile`), and #1459 (`docker_runtime.docker_image_exists(image, *, runner=None, env=None)`, `compose_image_name(project_name, service)`, `compose_build_command(...)`, `build_timeout_secs(env)`, `up_timeout_secs(env)`, build-then-up planning in `run_lifecycle`).

- [ ] **Step 1: Owner merges #1439 and #1456 into `main`, then retargets and merges #1459** (its base is `fix/mcp-lifecycle-repair-001`, #1456's branch). If #1456 no longer merges cleanly, fold its diff into Task 3b instead and record that in the packet.
- [ ] **Step 2: Create the worktree and branch**

```bash
git -C /Users/hue/code/dopemux-mvp worktree add .worktrees/mcp-just-works-m1 -b feat/mcp-just-works-m1 main
ln -s /Users/hue/code/dopemux-mvp/.venv /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1/.venv
```
The symlink is the interim for the hook crash this plan fixes in Task 1; remove it once Task 1 lands.

- [ ] **Step 3: Baseline** Run: `make test-fast` from the worktree. Expected: PASS (record the count); if it fails on `main`, record the failing names before any change.

---

### Task 1: Hooks run in every worktree (D6)

**Files:**
- Modify: `.claude/hooks/run_native_hooks.sh` (whole file, 34 lines)
- Modify: `src/dopemux/claude/native_hooks.py:665-680` (`main`)
- Modify: `src/dopemux/cli.py:4151-4198` (`native_hooks_register`) and add `native-hooks run` next to it
- Test: `tests/unit/test_native_hooks_dispatcher.py` (new), `tests/unit/test_native_hooks_register.py` (from #1439; extend)

**Interfaces:**
- Consumes: `NativeHookAdapter(project_root: Optional[Path] = None)`; `handle_event(self, event_data) -> Tuple[int, Dict]`; `EXIT_SUCCESS`, `EXIT_BLOCK = 2`.
- Produces: `dopemux native-hooks run` (reads one JSON payload from stdin, writes the response JSON to stdout, exits with the adapter's code); `native_hooks.main()` passes `payload.get("cwd")` as `project_root`; the dispatcher's resolution order below.

Dispatcher resolution order (the one algorithm this task fixes in code):

```sh
#!/usr/bin/env sh
set -eu
TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
COMMON="$(git rev-parse --git-common-dir 2>/dev/null || true)"
MAIN="$TOP"; [ -n "$COMMON" ] && MAIN="$(cd "$TOP" && cd "$(dirname "$COMMON")" 2>/dev/null && pwd)" || true
export CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$TOP}"
HOOK="$TOP/src/dopemux/claude/native_hooks.py"
if [ -f "$HOOK" ]; then
  for PY in "$TOP/.venv/bin/python" "$MAIN/.venv/bin/python"; do
    [ -x "$PY" ] && exec "$PY" "$HOOK"
  done
fi
for BIN in "$(command -v dopemux 2>/dev/null || true)" "$HOME/.local/bin/dopemux"; do
  [ -n "$BIN" ] && [ -x "$BIN" ] && exec "$BIN" native-hooks run
done
echo "native hooks: no interpreter found; skipping" >&2
exit 0
```

- [ ] **Step 1: Write the failing dispatcher tests** in `tests/unit/test_native_hooks_dispatcher.py`. Each test builds a real git repo under `tmp_path` with `git worktree add`, copies the dispatcher in, and runs it with `subprocess.run([...], cwd=worktree, input=payload, env=env)` where `env["PATH"]` points at a `bin/` of fake executables that append their `argv` and stdin to a log file.
  - `test_dispatcher_prefers_checkout_hook_file_with_main_venv`: worktree has `src/dopemux/claude/native_hooks.py` (a stub that prints `ran:<its own path>` and exits 2), no `.venv`; main checkout has a fake `.venv/bin/python` that execs the file; assert output contains the worktree's path and `returncode == 2`.
  - `test_dispatcher_uses_installed_dopemux_when_no_hook_file`: no `src/` in checkout; fake `dopemux` on PATH; assert log shows `native-hooks run` and the payload reached its stdin.
  - `test_dispatcher_passes_exit_code_through`: fake `dopemux` exits 2; assert `returncode == 2`.
  - `test_dispatcher_fails_open_when_nothing_found`: empty PATH, no venv, no hook file; assert `returncode == 0`, stdout `== ""`, stderr contains `no interpreter`.
  - `test_dispatcher_keeps_inherited_claude_project_dir`: env has `CLAUDE_PROJECT_DIR=/elsewhere`; fake python prints it; assert unchanged.
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/unit/test_native_hooks_dispatcher.py -v`. Expected: FAIL (current script exits 1 or runs the wrong file).
- [ ] **Step 3: Replace `.claude/hooks/run_native_hooks.sh`** with the script above.
- [ ] **Step 4: Run the same tests.** Expected: PASS.
- [ ] **Step 5: Write the failing `main()` tests** in the same file: `test_main_passes_payload_cwd_to_adapter` (monkeypatch `native_hooks.NativeHookAdapter` with a recorder; feed `{"hook_event_name":"SessionStart","cwd": str(tmp_path)}` on stdin; assert the recorder got `project_root == tmp_path`) and `test_main_without_cwd_uses_process_cwd`.
- [ ] **Step 6: Change `main()`** to `adapter = NativeHookAdapter(project_root=Path(payload["cwd"]) if payload.get("cwd") else None)`. Run tests. Expected: PASS.
- [ ] **Step 7: Write the failing CLI test** `test_native_hooks_run_reads_stdin_and_exits_with_adapter_code` using `CliRunner().invoke(cli, ["native-hooks", "run"], input=json.dumps(payload))` with the adapter monkeypatched to return `(2, {"decision": "block"})`; assert `exit_code == 2` and stdout is that JSON.
- [ ] **Step 8: Add `@native_hooks.command("run") def native_hooks_run() -> None`** in `cli.py` that calls `dopemux.claude.native_hooks.main()`. Run test. Expected: PASS.
- [ ] **Step 9: Extend `tests/unit/test_native_hooks_register.py`**: `test_register_includes_subagent_start` and `test_register_writes_to_git_toplevel_not_cwd` (invoke from a subdirectory; assert `<toplevel>/.claude/settings.json` was written). Implement: add `"SubagentStart"` to the events list; replace `Path.cwd()` with the git toplevel (fallback cwd) in the non-global path.
- [ ] **Step 10: Run** `make test-fast`. Expected: PASS. Remove the `.venv` symlink from Task 0 Step 2 and re-run one hook by hand in the worktree: `echo '{"hook_event_name":"SessionStart","cwd":"'$PWD'"}' | sh .claude/hooks/run_native_hooks.sh`. Expected: exit 0, JSON on stdout, no `ModuleNotFoundError`.
- [ ] **Step 11: Commit** `fix(hooks): dispatch native hooks in linked worktrees; honour payload cwd; add native-hooks run`.

---

### Task 2: Identity from git only (D3)

**Files:**
- Modify: `src/dopemux/mcp/runtime_state.py:105-181`
- Modify: `src/dopemux/mcp/project_identity.py:99-138`
- Modify: `src/dopemux/worktree_commands.py:53-117`
- Modify: `src/dopemux/mcp/lifecycle.py:138-145` (`resolve_target_repo`), `:422-435` (`run_lifecycle` signature), `:443-448` (identity), `:1237-1242` (`DOPE_MEMORY_*` ids)
- Modify: `src/dopemux/mcp/doctor.py:224-236` (signature), `:321-323`
- Modify: `src/dopemux/commands/mcp_commands.py:100-155` (`_trust_env_option`, `_run_lifecycle_cli`), `:1368-1400` (`init` options and target), `:839-856` (`_write_envrc`), `:1676-1798` (doctor), `:2057-2117` (repair-config)
- Test: `tests/unit/test_mcp_identity_git_only.py` (new); update `tests/unit/test_mcp_doctor_repo_aware.py:217-234`, `tests/unit/test_mcp_commands_catalog.py:329-345`

**Interfaces:**
- Consumes: `ProjectIdentity.project_id/project_root/worktree_root` (`project_identity.py:28-61`); `instance_id_for_path(path) -> str` (`port_diagnostics.py:59`); `_lifecycle_repo_option()` (`mcp_commands.py:100`).
- Produces: `resolve_identity_view(repo_path: Path, *, envrc_values: Optional[Mapping[str, str]] = None, trust_env: bool = False) -> ProjectIdentityView` (identity via `resolve_project_identity(cwd=repo_path, env=env_map if trust_env else {})`; `instance_id = instance_id_for_path(worktree)` and `workspace_id = worktree` unless `trust_env`); `resolve_project_identity(cwd=None, env=None)` where `env=None` means `{}`; `get_repo_root(fallback_cwd: bool = True, *, trust_env: bool = False) -> Optional[str]` git-first; `resolve_target_repo(repo: Optional[str | Path], *, cwd: Optional[Path] = None) -> Path` (None → `git rev-parse --show-toplevel` of cwd, fallback cwd); `run_lifecycle(..., trust_env: bool = False)`; `run_mcp_doctor(..., trust_env: bool = False)`; `_trust_env_option()` click option `--trust-env` on start/stop/restart/up/down/status/doctor/repair-config/init; `mcp init --repo PATH`; `_write_envrc(..., preserve: Mapping[str, str])` re-emitting any existing `CONPORT_DB_*` lines.

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_mcp_identity_git_only.py` (real git via the `_git_init` helper pattern from `tests/unit/test_mcp_commands_repair.py:30-45`, linked worktrees via `git worktree add`):
  - `test_identity_view_ignores_ambient_env_for_linked_worktree`: `envrc_values` naming a foreign repo in all five vars; assert `project_root == main`, `worktree_root == linked`, `instance_id == instance_id_for_path(linked)`, `workspace_id == str(linked)`, and no evidence line contains `forced identity`.
  - `test_identity_view_trust_env_keeps_override`: same input with `trust_env=True`; assert `project_root == foreign`.
  - `test_identity_stable_across_symlinked_path`: `os.symlink(repo, tmp_path/"link")`; assert equal `project_id` and `instance_id` for both paths.
  - `test_resolve_project_identity_none_env_is_empty`: `monkeypatch.setenv("DOPEMUX_PROJECT_ROOT", foreign)`; `resolve_project_identity(cwd=repo)` → `project_root == repo`.
  - `test_get_repo_root_prefers_git_over_env`, `test_get_repo_root_trust_env_restores_precedence`.
  - `test_resolve_target_repo_uses_git_toplevel_from_subdir`.
  - `test_run_lifecycle_dry_run_identity_matches_clean_shell`: call `run_lifecycle("start", repo=linked, catalog=_catalog(), dry_run=True, process_env={<five foreign vars>}, docker_runner=_docker_empty(), registry_path=..., product_root=...)` twice, once with `process_env={}`; assert `result.project_identity` equal.
  - `test_init_repo_option_targets_given_checkout_not_env`: `CliRunner().invoke(mcp_commands.mcp, ["init", "--repo", str(repo)])` with `DOPEMUX_WORKSPACE_ROOT` set to another repo and `DOPEMUX_MCP_PORT_LEASE_REGISTRY` to a tmp file; assert `repo/".mcp.json"` exists and the other repo is untouched.
  - `test_init_force_preserves_conport_db_keys`: pre-existing envrc with `export CONPORT_DB_NAME=x`; after `init --force --repo`, the line is still present.
- [ ] **Step 2: Run** the file. Expected: FAIL (import errors for `trust_env`, forced-identity evidence present, env precedence).
- [ ] **Step 3: Implement `resolve_identity_view`**: delete the forced-override block (`runtime_state.py:113-137`), add `trust_env`, compute identity git-only, take `instance_id`/`workspace_id` from the path unless `trust_env`.
- [ ] **Step 4: Implement `resolve_project_identity` env default** (`project_identity.py:110`: `env_map = env or {}`); grep callers passing `None` and leave them (they now mean git-only).
- [ ] **Step 5: Implement `get_repo_root` git-first** and `resolve_target_repo` with `cwd` support.
- [ ] **Step 6: Thread `trust_env`** through `run_lifecycle` → `resolve_identity_view`; `run_mcp_doctor` → `resolve_identity_view`; `_run_lifecycle_cli`; the nine commands via `_trust_env_option()`. Derive `DOPE_MEMORY_WORKSPACE_ID`/`DOPE_MEMORY_INSTANCE_ID` at `lifecycle.py:1237-1242` from the identity view, not `doctor_env`.
- [ ] **Step 7: `init`**: add `_lifecycle_repo_option()` and `_trust_env_option()`; target = `repo_arg` else `get_repo_root(fallback_cwd=False, trust_env=trust_env)`; identity via `resolve_project_identity(cwd=repo_path, env=({} if not trust_env else dict(os.environ)))`; `_write_envrc(..., preserve=existing CONPORT_DB_* from load_envrc)`.
- [ ] **Step 8: Update the two existing tests**: rename `test_resolve_identity_forces_repo_over_ambient` to `test_resolve_identity_ignores_ambient` asserting the Step 1 shape; keep `test_mcp_commands_catalog.py:339` (explicit `env=` override outside git still works) unchanged and confirm it passes.
- [ ] **Step 9: Run** `make test-fast`. Expected: PASS. Note: `ENVRC_MISSING` remains a blocker until Task 3b; a fresh worktree still cannot start after this task, by design.
- [ ] **Step 10: Commit** `fix(mcp): identity from git only; --trust-env; init --repo; preserve tenant keys on --force`.

---

### Task 3a: Catalog client shape, launcher render, parity (D1, D2)

**Files:**
- Modify: `mcp_catalog.yaml:536-620` (conport, dope-memory, task-orchestrator) and `src/dopemux/mcp/default_catalog.yaml` (same three)
- Modify: `src/dopemux/commands/mcp_commands.py:619-651` (`_render_local_entry`), `:1240` (`_ensure_fast_problems`)
- Modify: `src/dopemux/mcp/mcp_json.py:157-230` (`plan_mcp_json_repairs`, type comparison)
- Modify: `src/dopemux/mcp/doctor.py:429-445` (transport check)
- Modify: `src/dopemux/mcp/runtime_state.py:312-403` (`build_desired_services`)
- Modify: `src/dopemux/mcp/fleet_catalog.py:595-650` (`render_copilot_proxy_config`), and the other `url_template` consumers at `:629, :656, :711, :1079, :1294, :1429, :1555`, `src/dopemux/mcp/tool_snapshot.py:552`, `mcp_commands.py:1257`
- Modify: `pyproject.toml:28-66` (add `mcp>=1.28.1,<2` to core `dependencies`), `uv.lock`
- Regenerate: `.mcp.json`, `mcp-proxy-config.copilot.yaml`
- Test: `tests/unit/test_mcp_fleet_catalog.py:38, :430`, `tests/unit/test_mcp_commands_catalog.py:63`, `tests/arch/test_mcp_fleet_catalog_contract.py:160, :703, :733`, new `tests/unit/test_mcp_launcher_render.py`

**Interfaces:**
- Consumes: catalog entry fields `transport`, `url_template`, `requires_env`, `optional_env`, `env_template`, `scope`.
- Produces: catalog field `client: launcher` (absent means today's URL/command render); `catalog_client_shape(spec) -> Literal["launcher", "direct"]` in `fleet_catalog.py`; `expected_client_type(spec) -> str` returning `"stdio"` for launcher else `spec["transport"]`, used by `doctor.py:429-445` and `mcp_json.plan_mcp_json_repairs`; `sidecar_url(spec, ports: Mapping[str, int]) -> str` in `runtime_state.py` that expands `url_template`'s `${VAR:-default}` with the given ports (used by `build_desired_services` and by Task 3c); the launcher entry shape from Global Constraints.

- [ ] **Step 1: Write the failing render tests** in `tests/unit/test_mcp_launcher_render.py`: `test_render_local_entry_launcher_shape` (spec with `client: launcher`, `transport: sse` → exact dict from Global Constraints, no `env` key); `test_render_local_entry_without_client_unchanged` (today's URL shape); `test_expected_client_type_launcher_is_stdio`; `test_sidecar_url_expands_port_var` (`url_template` `http://localhost:${CONPORT_MCP_PORT:-3005}/sse` with `{"CONPORT_MCP_PORT": 3007}` → `http://localhost:3007/sse`, and default when absent).
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement** `catalog_client_shape`, `expected_client_type`, the `_render_local_entry` launcher branch, `sidecar_url`. Run. Expected: PASS.
- [ ] **Step 4: Write the failing doctor and repair tests** in the same file: `test_doctor_accepts_stdio_entry_for_launcher_spec` (fixture repo via `_write_fixture_repo` from `tests/unit/test_mcp_doctor_repo_aware.py:80-118` with a launcher `.mcp.json` entry and a `client: launcher` catalog; assert no `TRANSPORT_MISMATCH`), `test_repair_plans_launcher_entry_from_url_entry` (`plan_mcp_json_repairs` on an old URL entry proposes the launcher entry), `test_build_desired_services_uses_sidecar_url_for_launcher` (expected URL built from `url_template` plus ports, not from `.mcp.json`).
- [ ] **Step 5: Implement** the three. Run. Expected: PASS.
- [ ] **Step 6: Set `client: launcher` and `requires_env: []`** on the three entries in both catalogs. Regenerate committed files: `.venv/bin/dopemux mcp repair-config --repo . --apply` (writes `.mcp.json`), and `mcp-proxy-config.copilot.yaml` by `render_copilot_proxy_config` (launcher entries render as `command`/`args`). Update `test_copilot_proxy_config_renders_catalog_transports_and_env` to the new conport expectation.
- [ ] **Step 7: Run** `.venv/bin/python -m pytest tests/unit/test_mcp_fleet_catalog.py tests/unit/test_mcp_commands_catalog.py tests/arch/test_mcp_fleet_catalog_contract.py -v`. Expected: PASS, parity restored.
- [ ] **Step 8: Move `mcp` to core dependencies** in `pyproject.toml`; run `uv lock`; `uv sync --frozen --extra test`; `.venv/bin/python -c "import mcp.client.sse, mcp.client.streamable_http, mcp.server.lowlevel, mcp.server.stdio"`. Expected: no error.
- [ ] **Step 9: Run** `make test-fast`. Expected: PASS. Then `claude mcp list` from the worktree. Expected: the three servers listed as stdio commands (they will fail to connect until Task 3c; that is expected and must be noted in the packet).
- [ ] **Step 10: Commit** `feat(mcp): catalog client shape and stdio launcher render; mcp sdk in core deps`.

---

### Task 3b: Ports from leases, locks, registry reload (D2, D7)

**Files:**
- Create: `src/dopemux/mcp/locks.py`
- Modify: `src/dopemux/mcp/lifecycle.py:36-57` (`BLOCKING_FINDING_CODES`), `:505-520` (`ENVRC_MISSING`), `:560-570` (registry load), `:588` (`_extract_ports`), `:835` (`PORT_UNSET`), `:1505-1515` (final upserts and save)
- Modify: `src/dopemux/mcp/port_leases.py:198, :432` and `src/dopemux/mcp/runtime_registry.py:54, :166` (expose `reload()`; no behaviour change to `save`)
- Test: `tests/unit/test_mcp_locks.py`, `tests/unit/test_mcp_lifecycle_ports_from_leases.py` (new)

**Interfaces:**
- Consumes: `PortLeaseRegistry.load(path=None, *, create_missing=False)`, `.active_leases()`, `.upsert_lease()`, `.save()`; `port_allocator.allocate_ports(...)` called with the same arguments `mcp_commands._allocate_ports` passes (`mcp_commands.py:781-800`); `RuntimeRegistry.load/upsert_instance/mark_stopped/save`; `default_lease_registry_path()`, `default_registry_path()`.
- Produces: `lifecycle.runtime_dir_for(identity: ProjectIdentityView, *, registry_path: Optional[Path] = None) -> Path`, extracted from the expression at `lifecycle.py:1207` and used there, so the launcher and reap compute the same `~/.dopemux/mcp/runtime/<slug>-<worktree_hash>/`; `locks.registry_lock() -> ContextManager[None]`, `locks.instance_lock(runtime_dir: Path)`, `locks.reserved_port_lock(port: int)`, `locks.provision_lock(project_id: str)`, all `fcntl.flock(LOCK_EX)` on the files named in Global Constraints, creating parents `0700`; `locks.locked_reload_and_save(registry_cls, path, mutate: Callable[[registry], None]) -> registry` (lock, fresh `load(create_missing=True)`, `mutate(fresh)`, `fresh.save()`; on a corrupt file it starts from an empty document and records `registry.recovered_from_corrupt = True`); `lifecycle._resolve_ports(identity, selected, catalog, *, lease_path, source="dopemux mcp start") -> Dict[str, int]` (active leases for `(project_id, worktree_root)` first, else allocate under `registry_lock` and save); `ENVRC_MISSING` demoted to INFO and removed from `BLOCKING_FINDING_CODES`; the final registry write at `lifecycle.py:1509-1511` becomes `locked_reload_and_save(RuntimeRegistry, reg_path, mutate)`.

- [ ] **Step 1: Write the failing lock tests** in `tests/unit/test_mcp_locks.py`: `test_registry_lock_is_exclusive_across_processes` (two `subprocess` children holding `registry_lock()` for 0.3 s each; assert total wall time ≥ 0.6 s); `test_locked_reload_and_save_merges_concurrent_upserts` (two children each `locked_reload_and_save` with a different `upsert_instance`; assert both records present); `test_locked_reload_tolerates_corrupt_registry` (file holds `{` ; mutate adds one record; assert file now valid with that record and `recovered_from_corrupt`); `test_lock_files_created_0700_parents`.
- [ ] **Step 2: Run.** Expected: FAIL (module missing).
- [ ] **Step 3: Implement `locks.py`.** Run. Expected: PASS.
- [ ] **Step 4: Write the failing lifecycle tests** in `tests/unit/test_mcp_lifecycle_ports_from_leases.py` using `_fixture_repo`-style repos WITHOUT `.envrc.dopemux-mcp`, `docker_runner=_docker_empty()`, `DOPEMUX_MCP_PORT_LEASE_REGISTRY` and `DOPEMUX_MCP_RUNTIME_REGISTRY` set to tmp files: `test_start_dry_run_without_envrc_allocates_leases_and_is_not_blocked` (assert no `ENVRC_MISSING`/`PORT_UNSET` in `blocking_findings`, `status == "PLANNED"`, leases file has active leases for conport and dope-memory bound to `worktree_root`); `test_start_reuses_existing_active_leases` (second call returns the same ports, lease count unchanged); `test_envrc_ports_still_win_when_present_and_leased` (an envrc with a leased port keeps that port); `test_final_registry_save_reloads_under_lock` (pre-write a foreign record to `instances.json` after `run_lifecycle` loaded it, via a `docker_runner` side effect; assert the foreign record survives).
- [ ] **Step 5: Run.** Expected: FAIL.
- [ ] **Step 6: Implement `_resolve_ports`**, replace `_extract_ports` at `:588`, demote `ENVRC_MISSING`, route the final write through `locked_reload_and_save`. Run. Expected: PASS.
- [ ] **Step 7: Run** `make test-fast` and `tests/unit/test_mcp_lifecycle.py` (existing fixtures with envrc must still pass). Expected: PASS.
- [ ] **Step 8: Commit** `feat(mcp): lifecycle resolves ports from leases; registry and instance locks; reload under lock before save`.

---

### Task 3c: `dopemux mcp launch`, SDK proxy, orchestrator gate, `switch-project` (D2, D4)

**Files:**
- Create: `src/dopemux/mcp/stdio_proxy.py`, `src/dopemux/mcp/launcher.py`
- Modify: `src/dopemux/commands/mcp_commands.py` (add `launch` and `switch-project` after `restart` at `:215`)
- Modify: `src/dopemux/mcp/lifecycle.py:1335-1444` (orchestrator start under `reserved_port_lock`, build-or-wait policy)
- Test: `tests/unit/test_mcp_stdio_proxy.py`, `tests/unit/test_mcp_launcher.py`, `tests/unit/test_mcp_switch_project.py` (new); `tests/unit/test_task_orchestrator_http_singleton.py` (fake docker stub, reuse)
- Artifact: `claudedocs/mcp-launch-root-probe-2026-11-XX.md` (measurement result, committed)

**Interfaces:**
- Consumes: Task 3a `sidecar_url`, `catalog_client_shape`; Task 3b `locks.*`, `_resolve_ports`; `RuntimeRegistry.find(*, project_id, worktree_root, service) -> List[Dict]` records with `status`, `ports`, `urls`, `container_names`; `run_lifecycle(...)`; `docker_image_exists`, `compose_image_name`, `compose_build_command` (#1459); `task_orchestrator_identity.identity_from_docker_labels(labels, *, port, container_name) -> TOIdentity`, `match_target(observed, *, project_id, project_root) -> str`; `docker_inspect.inspect_running_containers(runner=None)`; SDK: `mcp.client.sse.sse_client(url, ...)`, `mcp.client.streamable_http.streamablehttp_client(url, ...)`, `mcp.ClientSession`, `mcp.server.lowlevel.Server`, `mcp.server.stdio.stdio_server`, `mcp.shared.memory.create_client_server_memory_streams` for tests.
- Produces:
  - `launcher.LaunchTarget(root: Path, identity: ProjectIdentityView, service: str, spec: Mapping[str, Any], runtime_dir: Path, compose_project: str)` built by `launcher.build_target(root: Path, service: str, *, catalog, registry_path=None) -> LaunchTarget` (`resolve_identity_view(root)`, the catalog spec, `lifecycle.runtime_dir_for`, `docker_runtime.compose_project_name`)
  - `stdio_proxy.BackendSpec(url: str, transport: Literal["sse", "http"], name: str)`
  - `stdio_proxy.run_proxy(backend: BackendSpec, *, session_factory: Optional[Callable[[], AsyncContextManager[ClientSession]]] = None) -> int`: lowlevel `Server(name=backend.name)` served over `stdio_server()`; handlers `list_tools`, `call_tool`, `list_resources`, `list_resource_templates`, `read_resource`, `list_prompts`, `get_prompt`, `set_logging_level`, each delegating to the backend `ClientSession`; backend `ToolListChangedNotification` forwarded as `send_tool_list_changed()`; sampling, elicitation and roots requests from the backend answered with an error `-32601 not supported by dopemux proxy`, never left pending; exit 0 when stdin closes, 1 if the backend session drops after retrying once.
  - `stdio_proxy.probe_backend(backend: BackendSpec, *, timeout_s: float = 1.0) -> bool`: SDK client `initialize()` inside `anyio.fail_after(timeout_s)`; True on success.
  - `launcher.LaunchError(code: str, remedy: str)`; `launcher.resolve_launch_root(explicit: Optional[Path], *, cwd: Path) -> Path` (git toplevel of `explicit or cwd`; `LaunchError("LAUNCH_ROOT_NOT_GIT", ...)` otherwise; `LaunchError("LAUNCH_MCP_JSON_NOT_MANAGED", ...)` when `.mcp.json` entries are not what Task 3a renders).
  - `launcher.find_backend(target: LaunchTarget, *, registry_path=None) -> Optional[BackendSpec]`: `RuntimeRegistry.find(project_id, worktree_root, service)`, newest record with `status == "running"`, `BackendSpec(sidecar_url(spec, record["ports"]), spec["transport"], service)`.
  - `launcher.ensure_backend(target, *, wait_s: float, lifecycle=run_lifecycle, probe=probe_backend, clock=time.monotonic, sleep=time.sleep) -> BackendSpec`: `find_backend` then `probe` → return; else under `instance_lock(runtime_dir)` re-check, then `lifecycle("start", repo=root, services=[service], catalog=..., process_env=..., trust_env=False)`; on `exit_code != 0` raise `LaunchError(first blocking code, remedy)`; then poll `probe` every 0.5 s until `wait_s`, raising `LaunchError("LAUNCH_WAIT_EXCEEDED", "run /mcp reconnect all")`.
  - `launcher.ensure_orchestrator(target, *, docker=inspect_running_containers, lifecycle=run_lifecycle) -> BackendSpec`: under `reserved_port_lock(7890)`: container publishing `127.0.0.1:7890` → `match_target(identity_from_docker_labels(c.labels, port=7890, container_name=c.name), project_id=..., project_root=...)`; `"OK"` → `BackendSpec("http://127.0.0.1:7890/mcp", "http", "task-orchestrator")`; `"WRONG_PROJECT"` → `LaunchError("TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT", f"{owner_root}; run dopemux mcp switch-project here to take it over")`; `"UNKNOWN"`/`"CONFLICT"` or an unlabelled listener → `LaunchError("TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER", "run dopemux mcp doctor")`; nothing listening → `lifecycle("start", services=["task-orchestrator"])` then probe.
  - `launcher.attach(runtime_dir: Path) -> Path` and `launcher.detach(path: Path) -> None` (write and remove `attached/<pid>`; Task 5 moves them to `reap.py` and re-exports here)
  - `launcher.launch(service: str, *, root: Optional[Path] = None, env: Mapping[str, str] = os.environ, registry_path=None, reaper: Callable[[], None] = lambda: None) -> int`: resolve root → `build_target` → `attach` → `reaper()` (Task 5 passes `reap.maybe_reap`; until then the default no-op) → `ensure_orchestrator` or `ensure_backend` → `run_proxy`; on `LaunchError` print `f"{code}: {remedy}"` to stderr and return 3; always `detach` in `finally`.
  - `doctor.py`: finding `DOPEMUX_BIN_NOT_EDITABLE` (WARN) when `shutil.which("dopemux")` resolves to an interpreter whose `dopemux.__file__` is not under the current `product_root()`, with recommendation `uv tool install --editable <product_root>` (D1).
  - Image policy inside `ensure_backend` (D4): before `lifecycle("start")`, if `docker_image_exists(compose_image_name(compose_project, service)) is False` → spawn `subprocess.Popen(compose_build_command(...), stdout=<runtime_dir>/build.log, start_new_session=True)` and raise `LaunchError("LAUNCH_IMAGE_BUILDING", "building image; retry with /mcp reconnect all in a few minutes")`.
  - CLI: `@mcp.command("launch") @click.argument("service") @click.option("--root", type=click.Path(path_type=Path)) @click.option("--wait", type=float, default=None) def mcp_launch_cmd(service, root, wait)` → `sys.exit(launch(service, root=root))` with `wait` from option, else `DOPEMUX_LAUNCH_WAIT`, else 25.
  - CLI: `@mcp.command("switch-project") @_lifecycle_repo_option() @click.option("--yes", is_flag=True) def mcp_switch_project_cmd(repo_arg, yes)`: identify the container on 7890 (labels `dopemux.managed=true`, `dopemux.service=task-orchestrator`); if it is this project's, print and exit 0; else print owner `project_root` and, with `--yes` or interactive confirm, `docker stop <id>` and `docker rm <id>` through `run_cmd`, then `run_lifecycle("start", repo=target, services=["task-orchestrator"])`; refuse (`exit 1`) if the listener is not a managed orchestrator container.

- [ ] **Step 1: Measure root resolution (the probe).** Copy the repo to a scratch dir, replace `.mcp.json` with one entry `{"type":"stdio","command":"sh","args":["-c","printf 'cwd=%s\\nproject=%s\\n' \"$PWD\" \"${CLAUDE_PROJECT_DIR:-}\" >> \"$HOME/.dopemux/launch-probe.log\"; cat >/dev/null"]}`, open Claude Code in the scratch main checkout, in a `git worktree add` of it, and via `EnterWorktree`; repeat with Codex. Record `cwd` per case in `claudedocs/mcp-launch-root-probe-<date>.md` as a table. If any runner's `cwd` is not the session checkout, add `"--root", "${CLAUDE_PROJECT_DIR:-.}"` for that runner in Task 3a's renderer before continuing, and note it in the packet.
- [ ] **Step 2: Write the failing proxy tests** in `tests/unit/test_mcp_stdio_proxy.py` using `create_client_server_memory_streams` for both sides and a fake backend `Server` exposing one tool `echo` and one resource: `test_proxy_lists_and_calls_backend_tools`, `test_proxy_forwards_tool_list_changed`, `test_proxy_answers_backend_sampling_with_error`, `test_probe_backend_false_on_refused_port` (closed localhost port, assert False within 1.5 s).
- [ ] **Step 3: Run.** Expected: FAIL (module missing).
- [ ] **Step 4: Implement `stdio_proxy.py`.** Run. Expected: PASS.
- [ ] **Step 5: Write the failing launcher tests** in `tests/unit/test_mcp_launcher.py` with injected `lifecycle`, `probe`, `docker`, `clock`, `sleep` fakes and tmp registries: `test_resolve_launch_root_from_subdirectory`, `test_launch_refuses_outside_git_without_docker` (docker fake records calls; assert none and exit 3 with `LAUNCH_ROOT_NOT_GIT`), `test_launch_refuses_unmanaged_mcp_json`, `test_ensure_backend_warm_path_skips_lifecycle` (registry record running + probe True → lifecycle not called), `test_ensure_backend_cold_path_starts_then_waits` (probe False,False,True → lifecycle called once, two sleeps), `test_ensure_backend_wait_exceeded`, `test_ensure_backend_image_missing_spawns_build_and_exits` (fake `docker_image_exists` False; assert Popen called with the build command and `LAUNCH_IMAGE_BUILDING`), `test_two_launchers_one_start` (two threads, shared fake lifecycle counter under `instance_lock`; assert 1), `test_ensure_orchestrator_ok_forwards`, `test_ensure_orchestrator_wrong_project_refuses` (labels with foreign `dopemux.project_root`), `test_ensure_orchestrator_unlabelled_refuses`, `test_ensure_orchestrator_free_starts`, `test_attach_record_written_and_removed`.
- [ ] **Step 6: Run.** Expected: FAIL.
- [ ] **Step 7: Implement `launcher.py`** and the `launch` command. Run. Expected: PASS.
- [ ] **Step 8: Write the failing `switch-project` and doctor tests** in `tests/unit/test_mcp_switch_project.py` with a recording `run_cmd` and docker fake: `test_switch_project_noop_when_owned`, `test_switch_project_stops_owner_and_starts_target_with_yes`, `test_switch_project_refuses_unmanaged_listener`; and in `tests/unit/test_mcp_doctor_repo_aware.py`: `test_doctor_warns_when_path_dopemux_is_not_editable_install` (monkeypatch `shutil.which` and the probed `__file__`).
- [ ] **Step 9: Implement `switch-project`**, the doctor finding, and wrap the orchestrator start in `lifecycle.py:1335-1444` with `reserved_port_lock(7890)`. Run. Expected: PASS.
- [ ] **Step 10: Run** `make test-fast`. Expected: PASS. Then live check from the worktree with an untouched shell: `claude mcp list`. Expected: conport, dope-memory connected; task-orchestrator connected or failed with `TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT` naming dNh_CRM's root. Repeat from a shell with main's `.envrc.dopemux-mcp` sourced. Expected: identical.
- [ ] **Step 11: Commit** `feat(mcp): dopemux mcp launch with SDK stdio proxy, orchestrator gate, switch-project`.

---

### Task 4: ConPort tenants (D5)

**Files:**
- Create: `src/dopemux/mcp/conport_tenant.py`
- Modify: `src/dopemux/mcp/lifecycle.py` (conport start: credentials into the compose env; post-start gate), `src/dopemux/mcp/docker_runtime.py:32-39` (`env_with_compose_interpolation(extra: Optional[Mapping[str, str]] = None)`)
- Modify: `src/dopemux/mcp/doctor.py` (conport block after `:732`): `CONPORT_LEGACY_SHARED_STORE` WARN
- Modify: `src/dopemux/commands/mcp_commands.py:1368-1510` (`init` provisions and pre-builds)
- Test: `tests/unit/test_mcp_conport_tenant.py` (new), extend `tests/unit/test_mcp_doctor_repo_aware.py`

**Interfaces:**
- Consumes: `scripts/migration/provision_conport_project_db.sh` as the reference for SQL (role, database, `REVOKE CONNECT ... FROM PUBLIC`, extensions `uuid-ossp`, `pg_trgm`, `age`, filtered `schema.sql`, migrations `001, 002, 003, 004, 007`, `users`/`workspaces`/`user_workspace_access` rows); `docker_runtime.product_root()` for the schema path; Task 3b `locks.provision_lock`; `run_cmd`.
- Produces:
  - `TenantCredentials(db_name: str, db_user: str, db_password: str, source: Literal["secrets", "legacy_envrc", "provisioned", "legacy_shared"])`
  - `secrets_path(project_id: str) -> Path`; `load_secrets(path) -> Optional[TenantCredentials]`; `write_secrets(path, creds) -> None` (`0700` dir, `0600` file, atomic replace)
  - `PsqlRunner = Callable[[str, str], subprocess.CompletedProcess]` (`(database, sql)` executed as `docker exec -i dopemux-postgres-age psql -v ON_ERROR_STOP=1 -U dopemux_age -d <database>`); `default_psql_runner(runner=run_cmd) -> PsqlRunner`
  - `legacy_workspace_aliases(identity) -> List[str]`: `project_root`, its basename, and every path from `git worktree list --porcelain`
  - `count_legacy_rows(aliases, *, psql) -> Optional[int]`: `SELECT count(*)` over the union of the seven workspace-scoped tables (`workspace_contexts, decisions, progress_entries, session_snapshots, custom_data, entity_relationships, search_cache`) in `dopemux_knowledge_graph`; `None` when psql fails
  - `provision_database(*, slug: str, workspace_id: str, password: str, psql, schema_path: Path, migrations_dir: Path) -> None`: the script's steps 1 to 4 and 6; raises `TenantError("ROLE_EXISTS_WITHOUT_SECRETS")` instead of `ALTER ROLE ... PASSWORD` when the role already exists
  - `adopt_with_gate(container_name: str, creds, *, runner=run_cmd) -> None`: `docker exec -e DPMX_CONPORT_MIGRATION_APPLY=1 <container> python migrations/conport_migration_gate.py apply --database-url ...` then `verify`
  - `resolve_tenant(identity, *, envrc_values, psql, secrets_root=None) -> TenantCredentials`: order secrets → envrc `CONPORT_DB_*` (copied to secrets, source `legacy_envrc`) → `count_legacy_rows > 0` → `legacy_shared` (no credentials; compose defaults apply) → provision under `provision_lock(project_id)` with a 48-hex password, write secrets, source `provisioned`; `count_legacy_rows is None` → `legacy_shared` with evidence `postgres unreachable`
  - lifecycle: `creds = resolve_tenant(...)` before the conport compose up; `CONPORT_DB_NAME/USER/PASSWORD` merged into `env_with_compose_interpolation(extra=...)` for that `run_cmd` only; after the conport probe succeeds and `creds.source == "provisioned"`, `adopt_with_gate(container_names["conport"], creds)`; `services["conport"].findings` gets `CONPORT_LEGACY_SHARED_STORE` (WARN) when `source == "legacy_shared"`
  - `init`: after writing config, `resolve_tenant` (provisioning if needed) and `compose_build_command` for conport and dope-memory synchronously with the #1459 budget; prints the tenant source, never the password.

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_mcp_conport_tenant.py` with a recording fake `psql` (returns canned `CompletedProcess` per SQL prefix) and `tmp_path` as `secrets_root`: `test_resolve_tenant_prefers_secrets_file`, `test_resolve_tenant_adopts_envrc_and_copies_to_secrets` (envrc values → secrets file written `0600`, source `legacy_envrc`), `test_resolve_tenant_legacy_shared_when_rows_exist` (fake count 3 → `legacy_shared`, no CREATE statements issued), `test_resolve_tenant_provisions_when_no_history` (fake count 0 → CREATE ROLE, CREATE DATABASE, REVOKE, extensions, schema, 5 migrations, workspace rows in that order; secrets written), `test_provision_refuses_existing_role_without_secrets`, `test_resolve_tenant_unreachable_postgres_is_legacy_shared`, `test_legacy_aliases_include_worktrees`, `test_secrets_never_in_mcp_env` (run `generate_mcp_env` with the creds in env; assert no `PASSWORD` key), `test_password_never_printed` (capsys on `init` output).
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement `conport_tenant.py`.** Run. Expected: PASS.
- [ ] **Step 4: Write the failing lifecycle and doctor tests**: `test_start_passes_tenant_env_to_compose_only` (recording `cmd_runner`; assert the compose `run_cmd` env has `CONPORT_DB_NAME` and `mcp.env` on disk does not), `test_start_runs_gate_after_first_provision`, `test_doctor_warns_legacy_shared_store` (`run_mcp_doctor` with a fake psql count > 0; assert `("CONPORT_LEGACY_SHARED_STORE", "conport")` in codes and status `PASS_WITH_WARNINGS`).
- [ ] **Step 5: Implement** the lifecycle, doctor and `init` changes. Run. Expected: PASS.
- [ ] **Step 6: Run** `make test-fast`. Expected: PASS. Live check (owner present, dopemux-mvp worktree): `dopemux mcp doctor --repo .` Expected: no new FAIL; conport tenant source printed as `legacy_envrc` or `secrets`.
- [ ] **Step 7: Commit** `feat(mcp): automatic ConPort tenant resolution and provisioning; legacy shared-store warning`.

---

### Task 5: Reap-only cleanup and stop releases leases (D8, P-09)

**Files:**
- Create: `src/dopemux/mcp/reap.py`
- Modify: `src/dopemux/mcp/docker_inspect.py` (add `inspect_all_managed_containers`), `src/dopemux/mcp/lifecycle.py:1635-1700` (`_stop_services`), `src/dopemux/mcp/launcher.py` (attach/detach already; call `maybe_reap`), `src/dopemux/claude/native_hooks.py:610-663` (`_on_stop`, `_on_session_end`), `src/dopemux/commands/mcp_commands.py` (add `reap`)
- Test: `tests/unit/test_mcp_reap.py` (new), extend `tests/unit/test_mcp_lifecycle.py`, `tests/test_native_hooks_workflow.py`

**Interfaces:**
- Consumes: `docker_inspect.parse_docker_ps_json_lines`; `PortLeaseRegistry.mark_released(...)` (`port_leases.py:393`); `RuntimeRegistry.mark_stopped(...)`; Task 3b `locks`; `locked_reload_and_save`.
- Produces:
  - `docker_inspect.inspect_all_managed_containers(runner=None) -> DockerInspectResult`: `docker ps -a --filter label=dopemux.managed=true --format {{json .}}`
  - `reap.attach(runtime_dir: Path) -> Path` (writes `attached/<pid>` with an ISO timestamp); `reap.detach(path: Path) -> None` (removes it and writes `last_detach` in `runtime_dir`); `reap.live_attachments(runtime_dir) -> int` (prunes pids that fail `os.kill(pid, 0)`)
  - `reap.ReapCandidate(project_id, worktree_hash, worktree_root, runtime_dir, container_ids: List[str], reason: Literal["worktree_missing", "idle"])`
  - `reap.plan_reap(*, registry: RuntimeRegistry, containers: Sequence[ContainerInfo], now: float, idle_s: float = 1200, exists=Path.exists) -> List[ReapCandidate]`: group containers by `(dopemux.project_id, dopemux.worktree_hash)`, skip `dopemux.scope in {"project", "singleton"}` and unmanaged, candidate when `live_attachments == 0` and (`not exists(worktree_root)` or `now - last_detach >= idle_s`); an unreadable registry yields `[]`
  - `reap.apply_reap(candidates, *, runner=run_cmd, lease_path=None, registry_path=None) -> ReapReport(reaped: List[ReapCandidate], errors: List[str])`: per candidate under `instance_lock`: re-check attachments, `docker stop` then `docker rm` each id, `locked_reload_and_save` marking leases released and instances stopped, `shutil.rmtree(runtime_dir)`
  - `reap.maybe_reap(*, throttle_s: float = 600, state_file: Optional[Path] = None, now=time.time) -> Optional[ReapReport]`: skips when `state_file` mtime is within `throttle_s`; otherwise plan + apply and touch the file
  - lifecycle `_stop_services`: after stopping, `mark_released` for the worktree's leases and remove the runtime dir
  - `native_hooks._on_stop` and `_on_session_end`: call `maybe_reap()` (SessionEnd with `throttle_s=0`) before the existing early returns, wrapped in `try/except Exception` so a reap failure never changes the hook decision
  - CLI `@mcp.command("reap") @click.option("--dry-run/--apply", default=True) @click.option("--json", "json_output", is_flag=True)`

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_mcp_reap.py` with fake container lists and tmp registries: `test_plan_reap_skips_project_and_singleton_scope`, `test_plan_reap_candidate_when_worktree_missing`, `test_plan_reap_candidate_when_idle_and_detached`, `test_plan_reap_not_candidate_when_attached` (live pid = `os.getpid()`), `test_plan_reap_stale_pid_counts_as_detached`, `test_plan_reap_with_corrupt_registry_is_empty`, `test_apply_reap_stops_removes_releases_and_rmtree` (recording runner; assert `docker stop` and `docker rm` per id, lease status released, registry stopped, dir gone), `test_apply_reap_rechecks_attachment_under_lock` (attach between plan and apply → not reaped), `test_maybe_reap_throttles`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement `reap.py` and `inspect_all_managed_containers`.** Run. Expected: PASS.
- [ ] **Step 4: Write the failing integration tests**: in `tests/unit/test_mcp_lifecycle.py` `test_stop_releases_leases_and_removes_runtime_dir`; in `tests/test_native_hooks_workflow.py` `test_stop_hook_calls_maybe_reap_before_allow` and `test_session_end_calls_reap_unthrottled` (monkeypatch `reap.maybe_reap` recorder; assert called with `throttle_s=0` for SessionEnd); `test_reap_failure_does_not_change_hook_decision`.
- [ ] **Step 5: Implement** the lifecycle, hook and CLI changes; wire `maybe_reap()` into `launcher.launch` before `ensure_backend`. Run. Expected: PASS.
- [ ] **Step 6: Run** `make test-fast` and `.venv/bin/python -m pytest tests/test_native_hooks_workflow.py -v`. Expected: PASS. Live check: `dopemux mcp reap --dry-run --json` on the host. Expected: candidates listed only for worktrees that no longer exist or are idle; no `project`/`singleton` scope ids.
- [ ] **Step 7: Commit** `feat(mcp): reap-only cleanup of idle or removed worktree sidecars; stop releases leases`.

---

### Task 6: Documentation (D10)

**Files:**
- Modify: `AGENTS.md:284-295` (§12.3) and `:355-384` (§12.6 command table: `launch`, `switch-project`, `reap` implemented; `reconcile`/`adopt`/`migrate` still planned)
- Modify: `.claude/CLAUDE.md:251-258` (new-repo block and debug sequence)
- Modify: `docs/02-how-to/mcp-setup-other-repos.md` (rewrite body; keep frontmatter `id`, `title`, `type: how-to`; update `date`, `last_review`, `next_review`)
- Modify: `src/dopemux/mcp/lifecycle.py:1250-1255` and `src/dopemux/mcp/agent_bootstrap.py:35, :53` (`recommended_next_actions` no longer says `source .envrc.dopemux-mcp && claude`)
- Modify: `docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md` §5 (one pointer line to the how-to; keep the rest as the historical record)
- Delete: `.claude/WORKTREE_MCP_SETUP.md`
- Test: `tests/scripts/test_docs_hygiene.py` (existing), new `tests/unit/test_docs_no_envrc_recipe.py`

**Interfaces:**
- Produces: the one-command recipe (`dopemux mcp init --repo <path>` once per new project; nothing per worktree; `dopemux mcp switch-project` to move the orchestrator; `dopemux mcp reap --apply` for manual cleanup; `DOPEMUX_BIN` override; `--trust-env` escape hatch), and the M1 limitations list (mid-session `EnterWorktree` needs `/mcp reconnect all`; one orchestrator per host; worktrees on pre-change branches keep URL entries; Codex not rendered).

- [ ] **Step 1: Write the failing doc test** `test_docs_no_envrc_recipe`: grep `AGENTS.md`, `.claude/CLAUDE.md`, `docs/02-how-to/mcp-setup-other-repos.md` for `source .envrc.dopemux-mcp`; assert no hits; assert `.claude/WORKTREE_MCP_SETUP.md` does not exist.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Make the edits and the deletion.**
- [ ] **Step 4: Run** the doc test, `.venv/bin/python scripts/docs_validator.py docs/02-how-to/mcp-setup-other-repos.md`, `scripts/docs_frontmatter_guard.py` on the same file, and `tests/scripts/test_docs_hygiene.py`. Expected: PASS.
- [ ] **Step 5: Commit** `docs(mcp): one-command setup recipe; launcher, switch-project, reap; retire envrc steps`.

---

## Acceptance run (after Task 6, owner present)

Host setup first (D1, owner's machine, once): `uv tool install --editable /Users/hue/code/dopemux-mvp` (with the merged branch checked out), then `dopemux doctor --repo /Users/hue/code/dopemux-mvp` shows no `DOPEMUX_BIN_NOT_EDITABLE`.

Map to design §6. Run each from a clean shell and from a shell with main's env file sourced:

- T1, T2, T3: fresh `git worktree add`, a Claude-made worktree, and Codex in the same worktree → three servers green (orchestrator may be refused per T6), one set of sidecars, registries valid JSON.
- T4: a scratch repo never set up → `dopemux mcp init --repo <path>` → session green; `~/.dopemux/mcp/projects/<id>/secrets.env` mode `0600`; `git grep CONPORT_DB_` in that repo empty.
- T5: dNh_CRM first launch adopts its env-file credentials; data visible; no new database (`psql -l` count unchanged).
- T6, T6b: orchestrator owned elsewhere → refused with the code; `switch-project --yes` then `/mcp reconnect all` → connected.
- T7: in the worktree, `echo '{...PreToolUse red-lane edit...}' | sh .claude/hooks/run_native_hooks.sh` → exit 2.
- T8: `git worktree remove` + session end → after `dopemux mcp reap --apply` (or the next SessionEnd), containers gone, leases released, dir removed, main untouched.
- T9: `dopemux mcp init --force --repo <worktree>` → `git -C <main> status --short .mcp.json .envrc.dopemux-mcp` empty.
- T10: remove the conport image → launcher exits with `LAUNCH_IMAGE_BUILDING` within 5 s; build running; later reconnect works.
- T11: two launchers within 100 ms → one lifecycle start (from `start-plan.json` mtimes and registry `last_start`).

Record results as PASS / FAIL / NOT_RUN per item in the M1 proof bundle.

## Implementation amendments (2026-11-07)

Appended after the final whole-branch review of Milestone 1; the approved text above is unchanged. Where the two differ, this section records what was built.

- **T6 finding codes.** The launcher refuses a foreign orchestrator with `TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT` (the remedy names the owner path) and an unlabeled or unknown `:7890` owner with `TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER`. Both are the lifecycle's existing codes (§9 e). `TASK_ORCHESTRATOR_OWNED_BY_OTHER_PROJECT` was not built.
- **Images are shared per service and Dockerfile version.** The image is `dopemux-<service>:<key>`, where `<key>` hashes the dopemux-mvp checkout path and the service's Dockerfile bytes. Every worktree and project built from that checkout shares it; the compose override and a build-only override set it as `image:`. T1 holds for every later worktree. The first launch on a host, and the first after a Dockerfile change, still builds (`LAUNCH_IMAGE_BUILDING`, one detached build per service, guarded by `<runtime_dir>/build-<service>.pid`). Sidecar source edits that leave the Dockerfile unchanged need a forced rebuild (`docker image rm` the tag; recipe in the how-to). Reap never removes images.
- **T3 (Codex) is out of scope and NOT_RUN.** Per §9 k, the per-worktree servers are not rendered into Codex's config in M1, so T3 was not run.
- **`switch-project`.** It stops and removes the owner's orchestrator container with `docker stop` and `docker rm` under the reserved `:7890` lock, not through the lifecycle stop: the wrapper's data dir is a bind mount, so removing the container loses no data. It then marks the owner's runtime-registry entry `stopped` (registry lock inside the reserved lock) and starts this project's orchestrator through the lifecycle.
- **Reconnect guard.** Before every reconnect, never before the first session, the stdio proxy runs a guard that re-proves the backend's owner from Docker labels. For the task-orchestrator it repeats the launcher's owner verdict (`TASK_ORCHESTRATOR_START_BLOCKED_*`). For `conport` and `dope-memory`, the container publishing the backend port must carry `dopemux.managed=true` and this instance's `dopemux.project_id` and `dopemux.worktree_hash` (`LAUNCH_BACKEND_OWNER_CHANGED`). On a refusal nothing is resent, the waiting request gets `-32000 "<code>: <remedy>"`, the line goes to stderr and the proxy exits 1. A guard that fails for any other reason counts as a refusal (`LAUNCH_RECONNECT_GUARD_FAILED`).
- **Reconnect budget.** The proxy reconnects at most once per 60 s window, and retries a refusing backend with backoff (0.25 s doubling, capped at 2 s) for up to 10 s. A later restart in the same session heals; two drops inside one window end the proxy. Each request is still sent at most twice (one resend after "Session terminated").
- **Reap kill switch and the SessionEnd timeout.** Every automatic reap path (the Stop/SubagentStop and SessionEnd hooks, and each launcher) checks a kill switch first: the file `<runtime root>/reap.disabled` or `DOPEMUX_MCP_REAP=0`/`off`/`false`. The explicit `dopemux mcp reap --apply` ignores it with a note. `.claude/settings.json` gives the SessionEnd hook `"timeout": 60`, because SessionEnd hooks otherwise share a 1.5 s budget (Claude Code docs, read 2026-11-05). Deadlines: Stop 60 s, SessionEnd 45 s, launcher 8 s.
- **D5, unknown history fails closed.** When the shared store's row count for a project cannot be read (Postgres or docker down), the history is unknown, not "has history". A start refuses `conport` with `CONPORT_TENANT_UNKNOWN_HISTORY` and changes nothing; `doctor` reports INFO `CONPORT_TENANT_UNVERIFIED`. Option A (`legacy_shared`) applies only to a project whose rows were counted.
- **D5, no plaintext password to Postgres.** `CREATE ROLE` receives a SCRAM-SHA-256 verifier (RFC 5802/7677, 4096 iterations, 16-byte random salt). The plaintext stays only in the 0600 secrets file, for the client.
- **Superseded: "`.envrc.dopemux-mcp` is no longer read by any command" (design D5, `claudedocs/mcp-just-works-design-2026-11-05.md` line 160).** dopemux still reads the file itself: `init` re-reads its ports and legacy `CONPORT_DB_*` (`init --force` keeps them), the first ConPort tenant resolution adopts legacy `CONPORT_DB_*` from it once (`legacy_envrc`), and `doctor` and each sidecar start take its ports. Nothing needs it sourced, and identity never comes from it; the generated header says so.
- **`init` fails closed on unknown history too.** When Postgres does not answer, `dopemux mcp init` stops with `FAIL CONPORT_TENANT_UNKNOWN_HISTORY` before building any image and changes nothing in the tenant store; the `.mcp.json` it already wrote stays.
