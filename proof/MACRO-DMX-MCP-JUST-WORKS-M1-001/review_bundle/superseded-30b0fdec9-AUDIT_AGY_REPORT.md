END_OF_PROMPT a202f49c-30b0fdec

# Independent L3 Audit Report — `MACRO-DMX-MCP-JUST-WORKS-M1-001`

## 1. Scope & Audit Execution

- **Repository / Branch**: `DDD-Enterprises/dopemux-mvp` (`feat/mcp-just-works-m1`)
- **Pinned HEAD SHA**: `30b0fdec996fcd782bf2f816900f9ff4dabd4c01`
- **Base SHA (branch-authored diff)**: `5742575c4` (21 commits, `98e068aec..30b0fdec9`, in [COMMITS.txt](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/COMMITS.txt#L1-L21))
- **Mounted Subject Bundle**:
  - [subject.diff](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1-L19517) (full 19,517-line diff across all 67 changed files, read in full)
  - [FILES.sha256](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/FILES.sha256#L1-L67) (67 file SHA-256 digests at `30b0fdec996fcd782bf2f816900f9ff4dabd4c01`)
  - [design.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/design.md#L1-L299), [plan.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/plan.md#L1-L378), [howto-mcp-setup-other-repos.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/howto-mcp-setup-other-repos.md#L1-L603), [LEDGER_SUMMARY.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/LEDGER_SUMMARY.md#L1-L191), [VALIDATIONS.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/VALIDATIONS.md#L1-L17)
- **Delegation & Cost-First Policy Note**: Per the Global Cost-First Delegation policy (`Delegated review cannot replace a required independent audit unless its independence and route satisfy the governing audit contract`), no subagents were spawned; all static verification was performed directly by the independent auditor using deterministic local file reads (`requested: gemini-4-argon-high`, `observed: UNKNOWN`, `effort: UNKNOWN`). No live host shell or network was used; all runtime/live validations are bucketed `NOT_RUN` and controller/implementer test logs are recorded under `author_claims_not_reproduced`.

---

## 2. Verification of Branch Claims (D1–D10) & Controller Review Focus (1–6)

### Claim Verification Summary (D1–D10)
- **D1 (Launcher-shaped `.mcp.json` entries)**: Verified in [.mcp.json](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L569-L597), [mcp_catalog.yaml](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1682-L1720), [default_catalog.yaml](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L4062-L4100), and [`_render_local_entry`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L2612-L2637) (`src/dopemux/commands/mcp_commands.py:1025-1043`). Renders `conport`, `dope-memory`, and `task-orchestrator` as `{"type": "stdio", "command": "${DOPEMUX_BIN:-dopemux}", "args": ["mcp", "launch", "<name>"]}` with no `url` or `env` block. `mcp>=1.28.1,<2` is promoted to core dependencies in [pyproject.toml](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1728-L1747) (`pyproject.toml:31`).
- **D2 (`dopemux mcp launch` proxy + lifecycle + orchestrator gate + reconnect guard)**: Verified in [launcher.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L5836-L6455) (`src/dopemux/mcp/launcher.py:1-614`) and [stdio_proxy.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L9296-L10107) (`src/dopemux/mcp/stdio_proxy.py:1-811`).
- **D3 (Git-only identity with `--trust-env`)**: Verified in [`resolve_project_identity`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L7891-L7905) (`src/dopemux/mcp/project_identity.py:104-114`), [`resolve_identity_view`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L9183-L9227) (`src/dopemux/mcp/runtime_state.py:106-127`), and [`get_repo_root`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L10116-L10193) (`src/dopemux/worktree_commands.py:53-102`).
- **D4 (Detached build on missing image + shared image tag per service)**: Verified in [`compose_image_name`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L4484-L4522) (`src/dopemux/mcp/docker_runtime.py:487-516`, `dopemux-<service>:<12-hex-sha256>`) and [`_build_image_if_missing`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L6222-L6295) (`src/dopemux/mcp/launcher.py:387-460`, per-service `build-<service>.pid` bounded by `build_timeout_secs()`, `start_new_session=True`, raising `LAUNCH_IMAGE_BUILDING`).
- **D5 (ConPort tenant resolution & provisioning)**: Verified in [conport_tenant.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L3179-L4055) (`src/dopemux/mcp/conport_tenant.py:1-876`).
- **D6 (Hooks dispatcher in linked worktrees)**: Verified in [run_native_hooks.sh](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L521-L552) (`.claude/hooks/run_native_hooks.sh:14-39`), [`native_hooks.main`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1868-L1899) (`src/dopemux/claude/native_hooks.py:694-716`), [`native_hooks_run`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1904-L1943) (`src/dopemux/cli.py:4156-4187`), and [.claude/settings.json](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L557-L564) (`.claude/settings.json:109-113`, 60s `SessionEnd` timeout).
- **D7 (Flock locks with inode re-check and lock order)**: Verified in [locks.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L7481-L7807) (`src/dopemux/mcp/locks.py:1-321`).
- **D8 (Reap-only bounded cleanup)**: Verified in [reap.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L7910-L9178) (`src/dopemux/mcp/reap.py:1-1263`).
- **D9/D10 (CLI commands & documentation)**: Verified `launch`, `switch-project`, `reap`, `--trust-env`, `init` sidecar provisioning/pre-build, and `doctor` checks in [mcp_commands.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1981-L3125), plus docs in [howto-mcp-setup-other-repos.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/howto-mcp-setup-other-repos.md#L1-L603), [.claude/claude.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L1-L515), and [AGENTS.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L598-L621) (with one low doc-drift finding `F1` in `AGENTS.md:309`).

### Controller Review Focus (1–6) Confirmation with `path:line`
1. **Secrets never printed/argv/logged (D5)**: **CONFIRMED**.
   - `TenantCredentials.db_password` sets `repr=False` (`src/dopemux/mcp/conport_tenant.py:155`).
   - `write_secrets` writes atomically with `os.fchmod(fd, 0o600)` inside a `0o700` directory (`src/dopemux/mcp/conport_tenant.py:211-240`).
   - `default_psql_runner` feeds SQL over `stdin` (`input_text=sql`) to `docker exec -i dopemux-postgres-age psql ...`, never argv (`src/dopemux/mcp/conport_tenant.py:345-362`).
   - `scram_sha256_verifier` computes RFC 5802 / RFC 7677 `SCRAM-SHA-256$4096:<salt>$<StoredKey>:<ServerKey>` (`src/dopemux/mcp/conport_tenant.py:374-414`); `provision_database` passes only the SCRAM verifier to `CREATE ROLE` (`src/dopemux/mcp/conport_tenant.py:570-591`) and adds both `password` and `verifier` to `hidden`.
   - `_redacted_tail` replaces all `hidden` secrets (raw and `urllib.parse.quote`d) and `scheme://user:password@` URLs **before** slicing `clean[-limit:]` (`src/dopemux/mcp/conport_tenant.py:438-452`). Launcher start failures additionally scrub `*_PASSWORD`/`*_SECRET`/`*_TOKEN`/`*_KEY` env values, tenant secret file values, URL credentials, and key-value assignments via `_redact_stderr_tail` (`src/dopemux/mcp/launcher.py:318-373`).
   - `adopt_with_gate` writes `DATABASE_URL=...` to a `0o600` temp file (`os.fchmod(fd, 0o600)`) and passes `--env-file <tmp>` to `docker exec`, unlinking in `finally` (`src/dopemux/mcp/conport_tenant.py:650-694`).
   - `generate_mcp_env` filters `k not in SECRET_ENV_KEYS and not k.endswith("_PASSWORD")` (`src/dopemux/mcp/docker_runtime.py:265-282`), and `lifecycle.py` overlays `tenant_compose_env(tenant)` only onto `up_env` for `conport` (`src/dopemux/mcp/lifecycle.py:1886-1914`), never writing `CONPORT_DB_*` to `mcp.env`, `start-plan.json`, or findings.
2. **Two launchers racing; lock order; inode re-check; instance lock around attach and stop**: **CONFIRMED**.
   - `_flock` opens/creates the lock file (`0o600` in `0o700` dir), acquires `fcntl.flock`, and compares `os.fstat(fd)` vs `os.stat(path)` `(st_dev, st_ino)`, retrying up to 50 times if unlinked or replaced while waiting (`src/dopemux/mcp/locks.py:93-143`).
   - Documented lock order (`src/dopemux/mcp/locks.py:11-26`) is respected everywhere:
     - `instance_lock` outside `registry_lock` and `provision_lock`: `ensure_backend` (`src/dopemux/mcp/launcher.py:463-485`) acquires `instance_lock(target.runtime_dir)` before calling `run_lifecycle("start")`, which acquires `registry_lock` (`src/dopemux/mcp/lifecycle.py:2170-2177`) and `provision_lock` (`src/dopemux/mcp/lifecycle.py:1303,1340`).
     - `reserved_port_lock(7890)` (re-entrant per thread via `_reentrant_flock`, `src/dopemux/mcp/locks.py:199-223`) outside `registry_lock`: `ensure_orchestrator` (`src/dopemux/mcp/launcher.py:517`), `_start_services` (`src/dopemux/mcp/lifecycle.py:1803-1812`), and `mcp_switch_project_cmd` (`src/dopemux/commands/mcp_commands.py:2492-2550`) acquire `reserved_port_lock(7890)` before `registry_lock`.
   - `launch` records its attachment inside `with instance_lock(target.runtime_dir): attach_record = attach(target.runtime_dir)` (`src/dopemux/mcp/launcher.py:563-564`) and releases the lock before `_run_reaper()` and `ensure_backend()`.
   - `run_lifecycle("stop")` wraps container stop + `_release_stopped_state` inside `instance_lock(runtime_dir)` (`src/dopemux/mcp/lifecycle.py:2131-2142`) and updates `RuntimeRegistry` via `save_state_locked` (`src/dopemux/mcp/lifecycle.py:2179-2191`).
3. **Backend restart: resend-once; "Session terminated"; reconnect guard refusing changed owner; backoff and window budget**: **CONFIRMED**.
   - Streamable HTTP `32600 "Session terminated"` is matched by `_session_terminated` (`src/dopemux/mcp/stdio_proxy.py:190-200`) and resent at most once (`MAX_SENDS_PER_REQUEST = 2`, `src/dopemux/mcp/stdio_proxy.py:104,463-501`). Dead read-streams (`_can_receive`, `src/dopemux/mcp/stdio_proxy.py:203-220`) or closed write-streams (`ClosedResourceError` / `BrokenResourceError`) trigger reconnect before write; in-flight requests that drop mid-call raise `CONNECTION_CLOSED` without replay (`src/dopemux/mcp/stdio_proxy.py:483-496`).
   - Reconnect guard (`launcher.reconnect_guard`, `src/dopemux/mcp/launcher.py:213-266`) runs at two checkpoints on **every** session including the first (`_guarded_session` / `_session_once`, `src/dopemux/mcp/stdio_proxy.py:343-375`): (1) before connecting, and (2) immediately after `session.initialize()` before exposing `self.session` to any runner request. Refusal (or any unexpected guard exception, fail-closed as `LAUNCH_RECONNECT_GUARD_FAILED`, `src/dopemux/mcp/stdio_proxy.py:391-408`) prints `<code>: <remedy>` to stderr, returns `McpError(-32000, "<code>: <remedy>")` to the runner (via `_answer_with_refusal` on first-session refusal, `src/dopemux/mcp/stdio_proxy.py:525-557`), and exits `1`.
   - Reconnect backoff starts at `RECONNECT_BACKOFF_S = 0.25`, doubles up to `RECONNECT_BACKOFF_MAX_S = 2.0` within `RECONNECT_WAIT_S = 10.0` (`src/dopemux/mcp/stdio_proxy.py:106-110,377-389`), and allows at most one reconnect per `RECONNECT_WINDOW_S = 60.0` (`src/dopemux/mcp/stdio_proxy.py:111,316-329`).
4. **Reap safety**: **CONFIRMED**.
   - Containers are joined by `(dopemux.project_id, dopemux.worktree_hash)` with `dopemux.managed == "true"` and `dopemux.scope == "worktree"` (`src/dopemux/mcp/reap.py:296-339`); `project`/`singleton` scopes and `task-orchestrator` (`_ORCHESTRATOR`, `src/dopemux/mcp/reap.py:403-413,474-484`) are never reaped or marked stopped.
   - Fail-closed idle rule: missing `last_detach` returns `False` (`_idle_long_enough`, `src/dopemux/mcp/reap.py:238-246`); dead attachment pruning updates `last_detach` to `max(dead_mtime)` (`src/dopemux/mcp/reap.py:141-196`); unreadable worktree paths fail closed (`_worktree_gone`, `src/dopemux/mcp/reap.py:229-235`).
   - Under `instance_lock(cand.runtime_dir, blocking=blocking_lock)`, `_reap_one` re-verifies `live_attachments(cand.runtime_dir) == 0` and `_still_eligible(cand, ...)` (`src/dopemux/mcp/reap.py:666-677`).
   - Automatic reaps (`maybe_reap`, `src/dopemux/mcp/reap.py:822-932`) respect kill-switches (`DOPEMUX_MCP_REAP=0|false|off` and `<runtime_root>/reap.disabled`, `src/dopemux/mcp/reap.py:88-100`), use non-blocking `instance_lock`, bound `registry_lock` wait to `min(time left, 2 s)` via `save_states_locked` (`src/dopemux/mcp/reap.py:608-640,685-719`), cap per-command timeout to `min(cmd_timeout_s, time left)`, and restore `reap.last` when all candidates are skipped as `cap`/`deadline`/`locked`/`stale` or when inspection times out.
   - State-only candidates (`src/dopemux/mcp/reap.py:423-468`) clean up orphaned registry/lease/runtime-dir state when a worktree is gone and no containers remain.
5. **Ambient environment scrub (Review Focus 5)**: **CONFIRMED**.
   - `AMBIENT_SCRUB_VARS` (`src/dopemux/mcp/docker_runtime.py:51-74`) defines the exact 20 identity, tenant credential, port, and container-name variables.
   - Scrubbed across CLI lifecycle commands (`_lifecycle_process_env`, `src/dopemux/commands/mcp_commands.py:138-151`), launcher (`_lifecycle_env`, `src/dopemux/mcp/launcher.py:274-305`), compose interpolation (`env_with_compose_interpolation(..., scrub_ambient=True)`, `src/dopemux/mcp/lifecycle.py:1765,1893`), and `mcp init` (`_init_sidecars`, `src/dopemux/commands/mcp_commands.py:2079`).
6. **Known deferred items ([LEDGER_SUMMARY.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/LEDGER_SUMMARY.md#L121-L133))**:
   - Reviewed items #1–#7 in `LEDGER_SUMMARY.md §Deferred`. None warrant elevation to a blocking M1 finding: they are either explicitly scoped to M2 (shared-store row migration, global `~/.claude.json` audit, Codex/Gemini parity) or low-probability edge conditions (TO restart during an in-flight tool call, TO ownership change via `mcp start --repo B` without `switch-project` where checkpoint 1/2 still guards reconnects, or multi-worktree concurrent first-provision gate retry).

---

## 3. Acceptance Checks Mapping (`plan.md` §Review Focus 1–5 & `design.md` §6 T1–T11)

- **Plan Review Focus 1–5 (Static + Unit Test Coverage in Diff)**:
  - **RF1 (Launch from subdirectory -> git toplevel)**: Verified in [`resolve_launch_root`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L5972-L5994) and [`test_resolve_launch_root_from_subdirectory`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L13261-L13266).
  - **RF2 (Two launchers for same worktree serialize on `launch.lock`)**: Verified in [`ensure_backend`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L6298-L6329) and [`test_two_launchers_one_start`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L13389-L13422).
  - **RF3 (Two worktrees starting concurrently keep both records in `instances.json` and `port-leases.json`)**: Verified in [`locked_reload_and_save`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L7713-L7750), [`test_locked_reload_and_save_merges_concurrent_upserts`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L15757-L15768), and [`test_final_registry_save_reloads_under_lock`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L15380-L15415).
  - **RF4 (Ambient `DOPEMUX_*` ignored unless `--trust-env`)**: Verified in [test_mcp_identity_git_only.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L12650-L13029) and [`test_cli_lifecycle_commands_scrub_ambient_vars_unless_trust_env`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L10744-L10764).
  - **RF5 (ConPort tenant resolution order, no password leak, `0600` secrets, no shared-DB DDL)**: Verified in [test_mcp_conport_tenant.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L10850-L12344).
- **Design §6 Live Acceptance Scenarios (T1–T11)**:
  - **T1 (Fresh worktree in `dopemux-mvp`)**: Static code/tests verified (`test_mcp_launcher.py`, `test_native_hooks_dispatcher.py`); live Claude session + Docker execution is `NOT_RUN` (no live host/Docker in static audit environment).
  - **T2 (Second worktree in `dopemux-mvp` simultaneously)**: Static code/tests verified (`test_mcp_port_allocator.py`, `test_mcp_locks.py`); live multi-worktree Docker run is `NOT_RUN`.
  - **T3 (Sourced envrc from another repo in shell)**: Static code/tests verified (`test_mcp_identity_git_only.py`, `test_mcp_commands_lifecycle.py`); live shell run is `NOT_RUN`.
  - **T4 (Onboard a second repo from scratch)**: Static code/tests verified (`test_mcp_conport_tenant.py`, `test_docs_no_envrc_recipe.py`); live Postgres + Docker build run is `NOT_RUN`.
  - **T5 (Legacy project with rows in `dopemux_knowledge_graph`)**: Static code/tests verified (`test_resolve_tenant_legacy_shared_when_rows_exist`, `test_start_marks_legacy_shared_store_and_passes_no_credentials`); live Postgres run is `NOT_RUN`.
  - **T6 (Project with existing `CONPORT_DB_*` in `.envrc.dopemux-mcp`)**: Static code/tests verified (`test_resolve_tenant_adopts_envrc_and_copies_to_secrets`, `test_main_checkout_envrc_is_adopted_from_a_linked_worktree`); live run is `NOT_RUN`.
  - **T7 (Second project while Project A holds `task-orchestrator` on `:7890`)**: Static code/tests verified (`test_ensure_orchestrator_wrong_project_refuses`, `test_conport_start_proceeds_while_another_project_owns_the_orchestrator`, `test_mcp_switch_project.py`); live run is `NOT_RUN`.
  - **T8 (Deleted worktree reaped)**: Static code/tests verified (`test_plan_reap_candidate_when_worktree_missing`, `test_apply_reap_stops_removes_releases_and_rmtree`); live Docker run is `NOT_RUN`.
  - **T9 (Idle worktree reaped, active worktree spared)**: Static code/tests verified (`test_plan_reap_candidate_when_idle_and_detached`, `test_plan_reap_not_candidate_when_attached`, `test_a_detach_refreshed_after_planning_makes_the_candidate_stale`); live Docker run is `NOT_RUN`.
  - **T10 (Simultaneous first launch in same worktree)**: Static code/tests verified (`test_two_launchers_one_start`); live process race is `NOT_RUN`.
  - **T11 (Cold image build on launch)**: Static code/tests verified (`test_ensure_backend_image_missing_spawns_build_and_exits`, `test_one_services_build_never_blocks_the_others`); live Docker build is `NOT_RUN`.

---

## 4. Findings

### `F1` — Stale per-worktree image-build claim in `AGENTS.md` (Severity: `low`)
- **Location**: [AGENTS.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L606-L607) (`AGENTS.md:309`)
- **Summary**: `AGENTS.md:309` still states *"The first launch in a new worktree builds its images (`LAUNCH_IMAGE_BUILDING`; then `/mcp reconnect all`)."* After commit `02658fcbe` (D4 / internal review finding I4), sidecar images are tagged per service and Dockerfile hash (`dopemux-<service>:<12-hex-sha256>`) and shared across all worktrees and projects on the host ([docker_runtime.py](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L4484-L4522), [howto-mcp-setup-other-repos.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/howto-mcp-setup-other-repos.md#L122-L128), [.claude/claude.md](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-30b0fdec/subject.diff#L273-L276)).
- **Unblock**: Update `AGENTS.md:309` to match `.claude/claude.md:270-273` and `docs/02-how-to/mcp-setup-other-repos.md:122-128` (clarifying that images are shared per service and Dockerfile version across worktrees and projects, so only the first launch on a host per Dockerfile version triggers `LAUNCH_IMAGE_BUILDING`).

---

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "observed_head": "30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "head_match": true,
    "base": "5742575c4",
    "file_hashes": {
      ".claude/claude.md": "4f1f3e5e5784111649c5f76d3bbc267031f026cfc4b469a7898218067da683e1",
      ".claude/hooks/run_native_hooks.sh": "25f97f0d011529879878c634990979ac5b5c9808cbaf75673a836a40a9495446",
      ".claude/modules/shared/governance-principles.md": "a5108186986ece85d361a7494b617896354da289a31f541b570aa5d42ac12766",
      ".claude/settings.json": "cfe4c34299463e19af4de655861960769fc3354457b2c6ea44b2d0ff3b541765",
      ".mcp.json": "53f32189b424a8ddbd6c595336c0cd613dba5627ffb75f9666a525b89bbfa740",
      "AGENTS.md": "af4fd6e7a516a9268d76b24185cb5cbd125186be449700b36082e0f8501508ae",
      "claudedocs/mcp-just-works-design-2026-11-05.md": "2b2691fbaa781fbcdd8dccf8eea8fc4ea7611260bd034ed92b923a34f754e4a3",
      "claudedocs/mcp-just-works-m1-plan-2026-11-05.md": "4cc68c6d7bb2c5f2c849e9af5f02b8eeae76bd18f636e6c824c83e1e031ed8a6",
      "claudedocs/mcp-launch-root-probe-2026-11-05.md": "f0107cde23f1655e0b1b62f9e32dffbc61e82c93aaec17bcd6131ff725978782",
      "docs/02-how-to/mcp-setup-other-repos.md": "547e8032727b7c4b48dda2a8ea396386dd3ec4bef519dff00871a737e0200826",
      "docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md": "93f67cda7f77b07f5976a449189c84480af0842666f71d3cb1251b0206493106",
      "mcp-proxy-config.copilot.yaml": "769c4ff6d821a4fb9ab40b74b1afe6a5a5adcae025d3071906ea0af51e7e71a4",
      "mcp_catalog.yaml": "6aa71c9d51cd4979fa778f93f850d8b44b85fcce47ff34c338ebb474af3f062e",
      "pyproject.toml": "58c63c8267cd199b7d62c9e0a1fba4652d3bb28a2de021a86e254fd432bd662a",
      "schemas/mcp/fleet-catalog-v2.schema.json": "2f5a7382187804bd533a894a59d6cb7b94351c939c616c0c937d2d3e76b9084c",
      "schemas/mcp/fleet-catalog.schema.json": "e33afe733bdb5822887d15675c7bca67d5571998a21cdd54547f5c43043be6f5",
      "scripts/doc_mine.py": "bb0a6e62165d11cb230c15caf41457c518e4cb4ead1e9df53598d345ec642182",
      "scripts/proofs/run_dnh_mcp_e2e.py": "0ca0e04ecac1bc552cd3ce4a0a6a0bfd9544256401c33f5e121613ac4fe2d19c",
      "src/dopemux/adhd_error_messages.py": "26ed37c19ac5960e7ec3f30e2d6c687dfbffd238922b61169981dabbd14e535b",
      "src/dopemux/claude/native_hooks.py": "6edaf3f43a7f02c3ab44c08d0b067551bcccec7e8acf0579de001b63827df7bb",
      "src/dopemux/cli.py": "91ab2bc6238296104883a071fd37eda705758cfc0c3b5b1f1eebe1207984be3b",
      "src/dopemux/commands/mcp_commands.py": "49a526ae700b4d3bf924dcc472bb884508e0a2cf258963d1dc0e2b5db07b585c",
      "src/dopemux/mcp/agent_bootstrap.py": "c4061b9a30147ebc66c4548c27a77c38264919bad33c837ca80a062e459c80b5",
      "src/dopemux/mcp/config_repair.py": "3911e1c7422998155d548f9ca4b0b61c675214ccb9186ca897063b2b5e8be904",
      "src/dopemux/mcp/conport_tenant.py": "ed617f6324270e3ceb2c7c0a668ed30144c91ef5c1d1ad19fbd74d2f19ecf33d",
      "src/dopemux/mcp/default_catalog.yaml": "6aa71c9d51cd4979fa778f93f850d8b44b85fcce47ff34c338ebb474af3f062e",
      "src/dopemux/mcp/docker_inspect.py": "881a825e018abfcc7c7d6f2ba017e8a7687176b7303fa15ed1ea564faf6461a9",
      "src/dopemux/mcp/docker_runtime.py": "078aeb0327735fe02bee8305d947b01d7eeaa1e287dd70e1e20a6ab3eee76d23",
      "src/dopemux/mcp/doctor.py": "e117c8d90e2df11d08b45bac2160975770fe0a15f63e27fdea89bbd1d98da6d2",
      "src/dopemux/mcp/fleet_catalog.py": "7352fed0b7ecce1b9f957ad6a32b490ca91c06c76793fbe4cc465e78e85718fd",
      "src/dopemux/mcp/launcher.py": "8bae5716c2ce1db0e0a30827c384e007071e6086bcecf20de101805e167c3d7f",
      "src/dopemux/mcp/lifecycle.py": "8fa97734e24383f88359bfebbfc85f70dd7bb4b912d9e6f102e04fa6027b7876",
      "src/dopemux/mcp/locks.py": "72d72c434a02ba9ed481f14d7696b1006e58de68c9cbe91009c71268b9472a8e",
      "src/dopemux/mcp/mcp_json.py": "ca24effbc9728db325e3cf8f5e6a45f4e3046ca35051bf4d57c711ef7ee6524b",
      "src/dopemux/mcp/port_allocator.py": "2d51347176fbe2517321284a8eac25db1520a2d5bb3ecda6598ba5218025fdc4",
      "src/dopemux/mcp/project_identity.py": "3358bc22ead2a2073910caccdf6d676f46a850f67604d066eb20ff48a869e70b",
      "src/dopemux/mcp/reap.py": "ffb3bbdae5468b3ba010d071b3b02893df15432ea7e51d78b842d48069f96902",
      "src/dopemux/mcp/runtime_state.py": "32d2538eeacfc601844a3049eb08ae7bb86c69d7bb443596472ab1951613c609",
      "src/dopemux/mcp/stdio_proxy.py": "e5188be8e9a031bcccab808a48d301f46a5986fb716d1550912f5cf9052b3783",
      "src/dopemux/worktree_commands.py": "565057cd11e282801d4fb04a4cd4405056d13ff1c2c7ebbaa1cb64aeed33ad9d",
      "tests/arch/test_compose_required_vars.py": "0fd6ae1c6671d74d8b4f87333d9efe40ef2de1e823986a685a1b74a2855de952",
      "tests/arch/test_mcp_fleet_catalog_contract.py": "ddf4e55909390bc966d54efe6969933404ba231a6c16593644120c0454dfee14",
      "tests/test_native_hooks_workflow.py": "c92b260697f05c1dc0c70902343b1143cdb70e00f817b6b2bab8f3d0066e3571",
      "tests/unit/runner_memory_2a_r2_w07/test_generator_gate.py": "081673b72cd0fe6250439d0d1aea6775ea4e4231b3ad68745336bf6f9493fc11",
      "tests/unit/test_docs_no_envrc_recipe.py": "26d5c67fc1e698e24d898e8e7b70fb3f560e3883f2857b286767622448e2e5af",
      "tests/unit/test_mcp_commands_catalog.py": "7d8be56395d36f74d0fe2e99b93cd23a1de1668b7d1ec05d8ab270caee921739",
      "tests/unit/test_mcp_commands_lifecycle.py": "3b6c8be6311903c7f772a5cbf34486dddef3beeb6db173e0e9fb45a93a8bccf8",
      "tests/unit/test_mcp_commands_repair.py": "bac8203601c8f62bed907c8cc921dfe6bda4d9b7ee03c4c5bd1538ecc81eb087",
      "tests/unit/test_mcp_commands_snapshot.py": "e186617a915ab0a5238dff27c0701863115026b001985d2840236b491435b037",
      "tests/unit/test_mcp_conport_tenant.py": "c0e468f4b02c93ad67205d23888034c9ad278ebfc8fb0c8e1541d2813c75192d",
      "tests/unit/test_mcp_doctor_repo_aware.py": "699b51faeeb3331ab209740665dba3c8c9a2e230055e8142785029c1e9b0964f",
      "tests/unit/test_mcp_fleet_catalog.py": "4a8d7bbf36f7204076cd909c0e48f117d7b244b3bb6e284801309b9f24d043d1",
      "tests/unit/test_mcp_identity_git_only.py": "79be954be951abb02208c666d832967eb510f5bf3700f02b6384e988fcf65160",
      "tests/unit/test_mcp_launcher.py": "f64f886b35229e424f2f1b8006bfbba355424494773ceffc9d476104fe29b058",
      "tests/unit/test_mcp_launcher_render.py": "d821b655d6eb4e6e764651fca51a8cbc2bc633c58165e55b29557d85fec05923",
      "tests/unit/test_mcp_lifecycle.py": "b7fae4fef0a288107cab6e4fa3b9af698350e01808809107d2bf2b89001f60fa",
      "tests/unit/test_mcp_lifecycle_ports_from_leases.py": "77deaa9a1d578acadee43e1fa059fddacee67d79738a60471432a8742df501da",
      "tests/unit/test_mcp_locks.py": "fe03f4da82ff8c4e82fdf3f89ebf533b1f67da9e637542de975dd5eaf7bfccc8",
      "tests/unit/test_mcp_port_allocator.py": "f4215352a4bee019b88e0602d7d1392dc0631d0a91afc03fabcb99bd5060d1cd",
      "tests/unit/test_mcp_profile_doctor.py": "05716fa700def0d089968149c2ddf0cd784da1103e2f22f0265120e6d8768b06",
      "tests/unit/test_mcp_reap.py": "bb815692bd1463b43cd06894125ac57f7af95e8d922e23c507e4f5f1d0cfc67e",
      "tests/unit/test_mcp_runtime_launcher.py": "8d00048c789166f239a409719ef45391d4f423969a72feb645a27ba6f4a52756",
      "tests/unit/test_mcp_stdio_proxy.py": "986cf2236353503d95a84f6eae3056367043d5397f1e0f2e171c994860dc2cfb",
      "tests/unit/test_mcp_switch_project.py": "ed004622baac644233eb8bf1b288a284c098e1b3865b0a99e469d8bd7a3bfb9c",
      "tests/unit/test_native_hooks_dispatcher.py": "2368f87e1191e27248d19aeac0a83230b9fb1fa0cdecf147ebba99cc1951f536",
      "tests/unit/test_native_hooks_register.py": "1a6e246c31296debef543e9d636a27cba475d98ade565213bf689950777b038c",
      "uv.lock": "92069428a66d2261dec5a47965de2b983fc5f3c22100a5b0811d82a9237c0cee"
    }
  },
  "auditor": {
    "runner": "agy",
    "model_requested": "gemini-4-argon-high",
    "model_observed": "UNKNOWN",
    "effort": "UNKNOWN",
    "independent_of_implementer": true
  },
  "checks": [
    {
      "id": "DIFF_READ_FULL",
      "command_or_method": "Static read_file of subject.diff lines 1-19517, FILES.sha256, COMMITS.txt, design.md, plan.md, howto-mcp-setup-other-repos.md, LEDGER_SUMMARY.md, VALIDATIONS.md",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Read all 19,517 lines of subject.diff (5742575c4..30b0fdec996fcd782bf2f816900f9ff4dabd4c01 across 67 changed files) and all supporting subject artifacts in full."
    },
    {
      "id": "SECRETS_ARGV_LOG_REVIEW",
      "command_or_method": "Static code and test inspection of src/dopemux/mcp/conport_tenant.py, src/dopemux/mcp/docker_runtime.py, src/dopemux/mcp/lifecycle.py, src/dopemux/mcp/launcher.py, and tests/unit/test_mcp_conport_tenant.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Verified 0600 atomic secrets file inside 0700 dir (conport_tenant.py:211-240), repr=False on TenantCredentials.db_password (conport_tenant.py:155), psql stdin delivery (conport_tenant.py:345-362), RFC 7677 SCRAM-SHA-256 verifier for CREATE ROLE (conport_tenant.py:374-414, 570-591), pre-truncation redaction of raw/URL-encoded secrets and URLs in _redacted_tail (conport_tenant.py:438-452) and launcher._redact_stderr_tail (launcher.py:318-373), 0600 --env-file for migration gate (conport_tenant.py:650-694), and exclusion of CONPORT_DB_* from mcp.env and start-plan.json (docker_runtime.py:265-282, lifecycle.py:1886-1914)."
    },
    {
      "id": "LOCK_ORDER_AND_INODE_REVIEW",
      "command_or_method": "Static code and test inspection of src/dopemux/mcp/locks.py, src/dopemux/mcp/launcher.py, src/dopemux/mcp/lifecycle.py, src/dopemux/mcp/reap.py, src/dopemux/commands/mcp_commands.py, and tests/unit/test_mcp_locks.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Verified fstat(fd) vs stat(path) (st_dev, st_ino) re-check with bounded retry in _flock (locks.py:93-143), thread-reentrant reserved_port_lock (locks.py:199-223), documented lock order (instance_lock outside registry_lock and provision_lock; reserved_port_lock(7890) outside registry_lock), attach under instance_lock released before reap/ensure_backend (launcher.py:563-568), and stop under instance_lock with save_state_locked (lifecycle.py:2131-2191)."
    },
    {
      "id": "RECONNECT_AND_OWNERSHIP_GUARD_REVIEW",
      "command_or_method": "Static code and test inspection of src/dopemux/mcp/stdio_proxy.py, src/dopemux/mcp/launcher.py, tests/unit/test_mcp_stdio_proxy.py, and tests/unit/test_mcp_launcher.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Verified resend-once on 32600 'Session terminated' and dead-read/closed-write streams without replaying in-flight dropped requests (stdio_proxy.py:190-220, 463-501); two-checkpoint reconnect_guard before connect and post-initialize on first session and every reconnect (stdio_proxy.py:343-375, launcher.py:213-266); fail-closed ProxyRefused delivery (-32000) via _answer_with_refusal / _unavailable (stdio_proxy.py:391-408, 525-557); backoff 0.25s..2.0s over 10s and 1-reconnect-per-60s window (stdio_proxy.py:104-111, 316-329, 377-389)."
    },
    {
      "id": "REAP_SAFETY_AND_BOUNDEDNESS_REVIEW",
      "command_or_method": "Static code and test inspection of src/dopemux/mcp/reap.py, src/dopemux/claude/native_hooks.py, src/dopemux/mcp/launcher.py, and tests/unit/test_mcp_reap.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Verified label join on (project_id, worktree_hash) restricted to dopemux.managed=true and dopemux.scope=worktree (reap.py:296-339); task-orchestrator never stopped or marked stopped (reap.py:403-413, 474-484); fail-closed idle check requiring last_detach and dead-PID mtime preservation (reap.py:141-196, 238-246); under-lock re-evaluation of live_attachments and _still_eligible (reap.py:666-677); non-blocking instance_lock, min(time left, 2s) registry_lock wait via save_states_locked, per-call deadline clamping, and throttle restoration on no-op/timeout in maybe_reap (reap.py:608-640, 822-932)."
    },
    {
      "id": "AMBIENT_ENV_SCRUB_REVIEW",
      "command_or_method": "Static code and test inspection of src/dopemux/mcp/docker_runtime.py, src/dopemux/mcp/project_identity.py, src/dopemux/mcp/runtime_state.py, src/dopemux/worktree_commands.py, src/dopemux/commands/mcp_commands.py, src/dopemux/mcp/launcher.py, and src/dopemux/mcp/lifecycle.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Verified AMBIENT_SCRUB_VARS (docker_runtime.py:51-74) is scrubbed across CLI lifecycle commands (mcp_commands.py:138-151), launcher (launcher.py:274-305), compose interpolation (lifecycle.py:1765, 1893), and mcp init (mcp_commands.py:2079), and git-only identity resolution ignores ambient DOPEMUX_* unless --trust-env is passed."
    },
    {
      "id": "DOCS_VS_CODE_TRUTHFULNESS",
      "command_or_method": "Static comparison of docs/02-how-to/mcp-setup-other-repos.md, .claude/claude.md, AGENTS.md, and claudedocs/mcp-just-works-design-2026-11-05.md against implementation",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Verified docs/02-how-to/mcp-setup-other-repos.md and .claude/claude.md accurately match the implemented CLI flags, exit codes, finding codes, lock files, secrets paths, and shared image tags; noted one low-severity stale sentence in AGENTS.md:309 (recorded as finding F1)."
    },
    {
      "id": "LIVE_AND_PYTEST_SUITES_T1_T11",
      "command_or_method": "Pytest execution and live Docker/Postgres/Claude acceptance scenarios T1-T11",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Auditor operates on read-only static subject bundle without live host shell/Docker/Postgres execution; live checks T1-T11 and pytest runs reported in VALIDATIONS.md and LEDGER_SUMMARY.md are bucketed NOT_RUN."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "low",
      "location": "AGENTS.md:309",
      "summary": "AGENTS.md still states that the first launch in a new worktree builds its images, whereas sidecar images are now shared per service and Dockerfile version across all worktrees and projects on the host.",
      "evidence": "AGENTS.md:309-310 says 'The first launch in a new worktree builds its images (LAUNCH_IMAGE_BUILDING; then /mcp reconnect all).' Commit 02658fcbe changed docker_runtime.compose_image_name (src/dopemux/mcp/docker_runtime.py:487-516) to tag dopemux-<service>:<12-hex-sha256> per service and Dockerfile content, and updated docs/02-how-to/mcp-setup-other-repos.md:122-128 and .claude/claude.md:270-273 accordingly, leaving AGENTS.md:309 with the pre-I4 wording."
    }
  ],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "VALIDATIONS.md claim: focused MCP + hooks unit and architecture pytest suite passed (299 passed in 11.42s) at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "VALIDATIONS.md claim: make test-fast passed (2232 passed, 8 skipped in 34.47s) at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "VALIDATIONS.md claim: docs_validator.py and doc_mine.py --check passed (0 violations, 560/560 checks) at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "VALIDATIONS.md claim: ruff, black --check, isort --check-only, and mypy diff checks passed on changed files at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "LEDGER_SUMMARY.md claim: owner-run live Docker/Postgres/launcher/reap checks (T1-T11 and live probes) passed on host"
  ],
  "remaining_risks": [
    "AGENTS.md:309 contains stale wording implying image builds happen per new worktree rather than once per service/Dockerfile version on the host (Finding F1, low).",
    "In stdio_proxy.py:316-329, an initial connect failure consumes the 60-second reconnect window budget via the immediate startup retry, so if the backend subsequently restarts within 60 seconds of that retry, the proxy will exit 1 and require '/mcp reconnect' rather than auto-healing a second time inside the same 60-second window.",
    "Deferred M1 items documented in LEDGER_SUMMARY.md §Deferred (e.g., M2 legacy shared-store row migration, M2 ~/.claude.json global audit, and in-flight tool calls during a task-orchestrator restart returning CONNECTION_CLOSED without replay) remain open by design."
  ],
  "unknowns": [
    "Live execution of the unit/arch test suites and linters in VALIDATIONS.md at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01 (not re-run in static audit environment).",
    "Live owner-run acceptance checks T1-T11 from claudedocs/mcp-just-works-design-2026-11-05.md §6 against a running Docker daemon, dopemux-postgres-age container, and Claude Code /mcp session (NOT_RUN by auditor)."
  ],
  "skip_reason": null,
  "unblock": [
    "Update AGENTS.md:309 to state that sidecar images are shared per service and Dockerfile version across all worktrees and projects on a host (matching .claude/claude.md:270-273 and docs/02-how-to/mcp-setup-other-repos.md:122-128)."
  ],
  "acceptance": "NOT_GRANTED"
}
```
