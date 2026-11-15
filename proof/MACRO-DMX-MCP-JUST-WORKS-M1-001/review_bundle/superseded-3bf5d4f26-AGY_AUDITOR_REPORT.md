END_OF_PROMPT f6570e69-3bf5d4f2

# Independent L3 Audit Report — `MACRO-DMX-MCP-JUST-WORKS-M1-001`

## 1. Scope & Subject Verification
- **Repository / Branch**: `DDD-Enterprises/dopemux-mvp`, branch `feat/mcp-just-works-m1`
- **Pinned HEAD SHA**: `3bf5d4f26deb3368e965b86599a2a05520a1e59b` (`head_match: true`, verified via [`COMMITS.txt`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/COMMITS.txt#L1-L20))
- **Base SHA**: `5742575c4` (20 commits in branch-authored range `5742575c4..3bf5d4f26deb3368e965b86599a2a05520a1e59b`)
- **Materials Inspected in Full**: [`subject.diff`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L1-L19071) (all 19,071 lines across 67 changed files), [`subject-src.diff`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L1-L7562), [`FILES.sha256`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/FILES.sha256#L1-L67), [`COMMITS.txt`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/COMMITS.txt#L1-L20), [`design.md`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/design.md#L1-L298), [`plan.md`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/plan.md#L1-L377), [`howto-mcp-setup-other-repos.md`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/howto-mcp-setup-other-repos.md#L1-L587), [`LEDGER_SUMMARY.md`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/LEDGER_SUMMARY.md#L1-L188), and [`VALIDATIONS.md`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/VALIDATIONS.md#L1-L17).
- **Delegation & Execution Note**: Under the governing audit contract ("You are the independent auditor... Fail closed: anything you did not verify yourself at the pinned subject is not PASS") and the cost-first delegation exception ("Delegated review cannot replace a required independent audit unless its independence and route satisfy the governing audit contract"), all required static checks were verified directly by this auditor without subagent delegation. Requested model: `gemini-4-argon-high`; observed model/effort: `UNKNOWN` (no runtime receipt exposed in sandbox).

## 2. Branch Claims Verification (D1–D10)
- **D1 (`.mcp.json` launcher shape)**: Verified in [`.mcp.json`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L505-L563), [`mcp_catalog.yaml`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L2532-L2589), [`mcp-proxy-config.copilot.yaml`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L2488-L2531), [`mcp_commands.py:_render_local_entry`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L1019-L1038), and [`fleet_catalog.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L3699-L3748).
- **D2 (`dopemux mcp launch` stdio proxy + lifecycle + orchestrator gate + reconnect guard)**: Verified in [`launcher.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L3749-L4542) and [`stdio_proxy.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L6714-L7495).
- **D3 (Git-only identity with `--trust-env`)**: Verified in [`runtime_state.py:resolve_identity_view`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L6538-L6648), [`project_identity.py:resolve_project_identity`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L5571-L5608), [`worktree_commands.py:get_repo_root`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L7496-L7562), and [`mcp_commands.py:_trust_env_option`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L337-L364).
- **D4 (Detached image build + typed `LAUNCH_IMAGE_BUILDING` refusal + shared per-service image tag)**: Verified in [`launcher.py:_build_image_if_missing`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L4215-L4275) and [`docker_runtime.py:compose_image_name`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L3179-L3205).
- **D5 (ConPort tenant resolution/provisioning, `0600` secrets, SCRAM verifier, two-phase gate via `docker exec --env-file`, per-migration resume, fail-closed unknown history)**: Verified in [`conport_tenant.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L1687-L2992) and [`lifecycle.py:_prepare_conport_tenant` / `_run_tenant_gate`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L4770-L4857).
- **D6 (Hooks dispatcher from hook cwd + fail-open fallback)**: Verified in [`.claude/hooks/run_native_hooks.sh`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L90-L148), [`native_hooks.py:main`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L230-L259), and [`cli.py:native_hooks_run` / `native_hooks_register`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L263-L309).
- **D7 (`flock` locks with inode re-check and documented lock order)**: Verified in [`locks.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L5216-L5476).
- **D8 (Bounded, kill-switchable reap-only cleanup)**: Verified in [`reap.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L5609-L6537), [`native_hooks.py:_best_effort_reap`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L186-L225), and [`launcher.py:_run_reaper`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L4458-L4472).
- **D9/D10 (CLI commands & setup docs)**: Verified in [`mcp_commands.py`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L310-L1546) and [`docs/02-how-to/mcp-setup-other-repos.md`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/howto-mcp-setup-other-repos.md#L1-L587) (with one low-severity stale sentence in [`AGENTS.md:309-310`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L606-L607), recorded as `F1`).

## 3. Review Focus Verification (`path:line`)
1. **Secrets never printed/argv/logged (D5) — CONFIRMED**:
   - `TenantCredentials.db_password` sets `field(repr=False)` (`src/dopemux/mcp/conport_tenant.py:153`).
   - `~/.dopemux/mcp/projects/<project_id>/secrets.env` is written atomically with parent mode `0700` and file mode `0600` (`src/dopemux/mcp/conport_tenant.py:208-224, 244-248`).
   - `psql_command` (`src/dopemux/mcp/docker_runtime.py:440-456`) and `default_psql_runner` (`src/dopemux/mcp/conport_tenant.py:354-384`) pass SQL on stdin (`input=sql`), never in `argv`.
   - `provision_database` (`src/dopemux/mcp/conport_tenant.py:404-422, 659-665`) derives a `SCRAM-SHA-256$4096:...` verifier via `scram_sha256_verifier(password)` and sends only the verifier in `CREATE ROLE ... LOGIN PASSWORD '...'` so plaintext passwords never enter Postgres statement logs; `_redacted_tail(raw, [password, verifier])` scrubs both before slicing `raw[-300:]` (`src/dopemux/mcp/conport_tenant.py:432-440, 620, 630`).
   - `adopt_with_gate` (`src/dopemux/mcp/conport_tenant.py:720-780`) writes `DATABASE_URL=...` to a `0600` temporary file (`tempfile.mkstemp`, `os.fchmod(fd, 0o600)`), runs `docker exec --env-file <tmp> ... migrations/conport_migration_gate.py apply|verify`, unlinks `<tmp>` in `finally`, and scrubs `creds.db_password` via `_redacted_tail` before truncating error tails.
   - `generate_mcp_env` (`src/dopemux/mcp/docker_runtime.py:293-315`) strips `SECRET_ENV_KEYS` and `*_PASSWORD`/`*_SECRET`/`*_TOKEN`. `lifecycle._start_services` (`src/dopemux/mcp/lifecycle.py:1645-1695, 1892-1949`) never writes `CONPORT_DB_*` to `mcp.env` or `start-plan.json`, passing `tenant_compose_env(tenant)` only via `extra=` in the `conport` `compose up` subprocess env (`src/dopemux/mcp/lifecycle.py:1895-1897`).
   - `mcp_commands._init_sidecars` (`src/dopemux/commands/mcp_commands.py:2065-2070`) and `doctor._check_conport_tenant` (`src/dopemux/mcp/doctor.py:669-747`) emit only `creds.source` and row/state evidence. `launcher.launch` (`src/dopemux/mcp/launcher.py:725-742`) defaults `env=None` and reads `os.environ` at call time.

2. **Two launchers racing; lock order; inode re-check; instance lock around attach and stop — CONFIRMED**:
   - Documented lock order (`src/dopemux/mcp/locks.py:8-28`) is strictly respected across all call sites:
     - `instance_lock` (`<runtime_dir>/launch.lock`) wraps `registry_lock` (`~/.dopemux/mcp/runtime/registry.lock`) in `launcher.ensure_backend` -> `run_lifecycle("start")` (`src/dopemux/mcp/launcher.py:450-460`, `src/dopemux/mcp/lifecycle.py:2129, 4185`), `run_lifecycle("stop")` (`src/dopemux/mcp/lifecycle.py:1333, 2395, 2419`), and `reap._reap_one` (`src/dopemux/mcp/reap.py:553, 566, 788`).
     - `reserved_port_lock(7890)` (thread-reentrant via `_HELD_RESERVED` in `src/dopemux/mcp/locks.py:37-68`) wraps `registry_lock` in `launcher.ensure_orchestrator` -> `run_lifecycle("start")` (`src/dopemux/mcp/launcher.py:537`, `src/dopemux/mcp/lifecycle.py:680, 2036, 2129`) and `mcp_switch_project_cmd` (`src/dopemux/commands/mcp_commands.py:470, 495`).
     - `instance_lock` wraps `provision_lock(project_id)` in `launcher.ensure_backend` -> `run_lifecycle("start")` -> `_prepare_conport_tenant` / `_run_tenant_gate` (`src/dopemux/mcp/conport_tenant.py:916, 927, 951`, `src/dopemux/mcp/lifecycle.py:1578`), and `provision_lock` never acquires an inner lock.
   - `launcher.launch` acquires `with instance_lock(target.runtime_dir): record = attach(target.runtime_dir)` (`src/dopemux/mcp/launcher.py:760-762`) and releases it before `_run_reaper` (`src/dopemux/mcp/launcher.py:767`) and `ensure_backend` (`src/dopemux/mcp/launcher.py:772`).
   - Inside `ensure_backend`'s `with instance_lock(target.runtime_dir):` (`src/dopemux/mcp/launcher.py:450-453`), `find_backend(target)` and `probe(backend)` are re-checked before invoking `lifecycle("start")`, so a second racing launcher reuses the sidecar started by the first.
   - `_flock` (`src/dopemux/mcp/locks.py:78-121`) compares `(os.fstat(fd).st_dev, os.fstat(fd).st_ino)` with `(os.stat(path).st_dev, os.stat(path).st_ino)` after `fcntl.flock`, unlocking and retrying up to 50 times if `shutil.rmtree(runtime_dir)` unlinked the lock file while the waiter blocked.

3. **Backend restart: resend-once; "Session terminated"; reconnect guard refusing changed owner; backoff and window budget — CONFIRMED**:
   - `_session_terminated` (`src/dopemux/mcp/stdio_proxy.py:192-202`) checks `error.code == 32600` AND `"Session terminated" in (error.message or "")`.
   - `forward` (`src/dopemux/mcp/stdio_proxy.py:463-501`) bounds `MAX_SENDS_PER_REQUEST = 2`: unwritten requests (`ClosedResourceError`/`BrokenResourceError`) and unprocessed Streamable HTTP 404 responses (`_session_terminated`) drop the dead session and retry once on the reconnected session; in-flight `CONNECTION_CLOSED` errors drop the session and return `McpError(CONNECTION_CLOSED, "... dropped during the request; not retried")` without replay.
   - Two-checkpoint owner guard (`src/dopemux/mcp/stdio_proxy.py:347-379`, `src/dopemux/mcp/launcher.py:604-695`): `_guarded_session` runs `_guard_allows()` before connecting (checkpoint 1), and `_session_once` runs `_guard_allows()` immediately after `session.initialize()` (checkpoint 2) before publishing `self.session` or calling `on_started(init)`. This runs on the **first session** (`src/dopemux/mcp/stdio_proxy.py:313, 319`) and on **every reconnect** (`src/dopemux/mcp/stdio_proxy.py:386`). When the first session is refused, `_answer_with_refusal` (`src/dopemux/mcp/stdio_proxy.py:529-586`) answers the runner's `initialize`, returns `McpError(-32000, "<code>: <remedy>")` on the first request, and exits `1`.
   - Reconnect backoff and window budget (`src/dopemux/mcp/stdio_proxy.py:108-114, 320-331, 381-393`): `_reconnect` retries failed connects with exponential backoff (`0.25 -> 0.5 -> 1.0 -> 2.0 s`) up to `RECONNECT_WAIT_S = 10.0 s`; `run` allows at most one reconnect per `RECONNECT_WINDOW_S = 60.0 s`.

4. **Reap safety: label join, scope exclusions, fail-closed idle rule, deadlines, kill-switch precedence, state-only candidates, orchestrator never marked stopped — CONFIRMED**:
   - `plan_reap` (`src/dopemux/mcp/reap.py:412-436`) requires `dopemux.managed=true`, `dopemux.scope=worktree`, `dopemux.project_id`, `_SAFE_HASH.fullmatch(worktree_hash)`, and a matching `RuntimeRegistry` entry; `project` and `singleton` scopes are never reaped.
   - Idle rule fails closed (`src/dopemux/mcp/reap.py:362-366, 439-446`): an existing worktree is never reaped unless `last_detach` exists and its age is `>= idle_s` (1200 s default). Pruned dead PID files in `attached/<pid>` stamp `last_detach` with `max(existing_mtime, dead_pid_mtime)` (`src/dopemux/mcp/reap.py:217-243`).
   - `maybe_reap` (`src/dopemux/mcp/reap.py:819-912`) checks `reaping_disabled_reason` (`DOPEMUX_MCP_REAP` in `{"0", "off", "false"}` or `<runtime_dir>/reap.disabled`, `src/dopemux/mcp/reap.py:258-269`) first, caps `inspect_all_managed_containers` timeout to `min(10.0, cmd_timeout_s, left)`, uses `blocking_locks=False` (`LockBusy` -> `skip_reason="locked"`, `src/dopemux/mcp/reap.py:788-790`), caps each `docker stop`/`rm` timeout to `min(cmd_timeout_s, left)` (`src/dopemux/mcp/reap.py:665-680`), and restores `reap.last` via `_restore_throttle` (`src/dopemux/mcp/reap.py:878-880, 902-910`) when inspection fails or every candidate is skipped for `"deadline"`/`"locked"`. Explicit `dopemux mcp reap --apply` overrides the automatic kill switch with a stderr note (`src/dopemux/commands/mcp_commands.py:305-309`).
   - `_state_only_candidates` (`src/dopemux/mcp/reap.py:461-506`) emits `state_only=True` only when no managed container exists for `(project_id, worktree_hash)`, the worktree is missing, `live_attachments == 0`, and unfinished state remains. `_owned_by` (`src/dopemux/mcp/reap.py:512-522`) excludes `task-orchestrator`, so the orchestrator registry record and project-scoped lease are never marked `stopped` or `released`.

5. **Ambient environment scrub — CONFIRMED**:
   - `AMBIENT_SCRUB_VARS` (`src/dopemux/mcp/docker_runtime.py:51-74`) enumerates all 21 identity, tenant credential (`CONPORT_DB_*`), port, and container-name variables.
   - Applied in `_lifecycle_process_env(trust_env)` (`src/dopemux/commands/mcp_commands.py:140-154`), `launcher._lifecycle_env` (`src/dopemux/mcp/launcher.py:373-393`, which also scrubs all catalog `port_var`/`extra_port_vars` and sets `trust_env=False`), and `env_with_compose_interpolation(..., scrub_ambient=True)` (`src/dopemux/mcp/docker_runtime.py:137-194`, used in `mcp_commands.py:2079`, `launcher.py:493`, and `lifecycle.py:1768, 1895`).

6. **Known deferred items (`LEDGER_SUMMARY.md` §Deferred D-1..D-9) — CONFIRMED**:
   - Reviewed `D-1..D-9` in [`LEDGER_SUMMARY.md:107-119`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/LEDGER_SUMMARY.md#L107-L119). None are re-raised as blocking M1 findings; each is either guarded by a fail-closed M1 mechanism or explicitly scoped to M2 / separate packets in `design.md` §10.

## 4. Acceptance Checks Mapping (Design §6 T1–T11 & Plan §Review Focus)
| Item | Static Code & Unit Test Evidence (Verified) | Live Host Execution |
|---|---|---|
| **T1** (`mcp init --repo`, no envrc sourcing) | `mcp_commands.py:1401-1615`, `tests/unit/test_docs_no_envrc_recipe.py:57-91`, `tests/unit/test_mcp_conport_tenant.py:11232-11287` | `NOT_RUN` (no live shell/Docker in audit sandbox) |
| **T2** (Fresh worktree cold-start via `mcp launch`) | `launcher.py:428-476`, `tests/unit/test_mcp_launcher.py:13081-13103, 13157-13190` | `NOT_RUN` (no live shell/Docker in audit sandbox) |
| **T3** (Two worktrees simultaneously, disjoint ports, shared tenant) | `port_allocator.py:282-360`, `tests/unit/test_mcp_port_allocator.py:15852-15895`, `tests/unit/test_mcp_conport_tenant.py:11104-11133` | `NOT_RUN` (no live shell/Docker in audit sandbox) |
| **T4** (Two projects simultaneously; TO `:7890` blocked on B until `switch-project`) | `launcher.py:525-580`, `lifecycle.py:1244-1269`, `tests/unit/test_mcp_launcher.py:13225-13245`, `tests/unit/test_mcp_lifecycle.py:14546-14583` | `NOT_RUN` (no live shell/Docker in audit sandbox) |
| **T5** (`switch-project` moves `:7890`; old session reconnect guard refuses B) | `mcp_commands.py:432-527`, `stdio_proxy.py:347-379`, `tests/unit/test_mcp_switch_project.py:18357-18558`, `tests/unit/test_mcp_launcher.py:14057-14150` | `NOT_RUN` (no live shell/Docker in audit sandbox) |
| **T6** (Polluted shell with foreign `.envrc.dopemux-mcp` ignored without `--trust-env`) | `runtime_state.py:124-213`, `mcp_commands.py:140-154`, `tests/unit/test_mcp_identity_git_only.py:12499-12731`, `tests/unit/test_mcp_commands_lifecycle.py:10512-10576` | `NOT_RUN` (no live shell/Docker in audit sandbox) |
| **T7** (Hooks in linked worktree without `.venv` or without `native_hooks.py`) | `.claude/hooks/run_native_hooks.sh:21-38`, `tests/unit/test_native_hooks_dispatcher.py:18690-18780` | `NOT_RUN` (no live shell in audit sandbox) |
| **T8** (Backend container restart mid-session reconnects and resends once) | `stdio_proxy.py:313-393, 463-501`, `tests/unit/test_mcp_stdio_proxy.py:17725-17863, 18024-18076` | `NOT_RUN` (no live Docker in audit sandbox) |
| **T9** (First launch without pre-built image spawns detached build + `LAUNCH_IMAGE_BUILDING`) | `launcher.py:479-522`, `tests/unit/test_mcp_launcher.py:13121-13155, 13856-13909` | `NOT_RUN` (no live Docker in audit sandbox) |
| **T10** (ConPort tenant resolution order + SCRAM + gate via `--env-file`) | `conport_tenant.py:404-441, 720-780, 902-1091`, `tests/unit/test_mcp_conport_tenant.py:10793-12113` | `NOT_RUN` (no live Docker/Postgres in audit sandbox) |
| **T11** (`reap` removes removed/idle worktrees, honours kill switch & attachments) | `reap.py:390-912`, `tests/unit/test_mcp_reap.py:16115-17218` | `NOT_RUN` (no live Docker in audit sandbox) |

## 5. Findings & Unblock Steps
- **`F1` (`low`) — [`AGENTS.md:309-310`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L606-L607)**:
  - **Summary**: `AGENTS.md` §12.3 still states `"The first launch in a new worktree builds its images (LAUNCH_IMAGE_BUILDING; then /mcp reconnect all)."` Commit `eb3f0624b` updated [`docker_runtime.py:compose_image_name`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject-src.diff#L3179-L3205) so sidecar images are shared across all worktrees and projects per service and Dockerfile version (`dopemux-<service>:<12-hex-key>`), and updated [`.claude/claude.md:279-281`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/subject.diff#L387-L390) and [`docs/02-how-to/mcp-setup-other-repos.md:126-130`](file:///private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/audit-subject-3bf5d4f2/howto-mcp-setup-other-repos.md#L126-L130), but missed that sentence in `AGENTS.md`.
  - **Optional Remediation**: Update `AGENTS.md:309-310` to match `.claude/claude.md:279-281` ("The first launch on a host per Dockerfile version builds the images (`LAUNCH_IMAGE_BUILDING`; then `/mcp reconnect all`); every worktree and project shares them.").

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "3bf5d4f26deb3368e965b86599a2a05520a1e59b",
    "observed_head": "3bf5d4f26deb3368e965b86599a2a05520a1e59b",
    "head_match": true,
    "base": "5742575c4",
    "file_hashes": {
      ".claude/claude.md": "4f1f3e5e5784111649c5f76d3bbc267031f026cfc4b469a7898218067da683e1",
      ".claude/hooks/run_native_hooks.sh": "25f97f0d011529879878c634990979ac5b5c9808cbaf75673a836a40a9495446",
      ".claude/modules/shared/governance-principles.md": "a5108186986ece85d361a7494b617896354da289a31f541b570aa5d42ac12766",
      ".claude/settings.json": "cfe4c34299463e19af4de655861960769fc3354457b2c6ea44b2d0ff3b541765",
      ".mcp.json": "53f32189b424a8ddbd6c595336c0cd613dba5627ffb75f9666a525b89bbfa740",
      "AGENTS.md": "af4fd6e7a516a9268d76b24185cb5cbd125186be449700b36082e0f8501508ae",
      "claudedocs/mcp-just-works-design-2026-11-05.md": "191267cf6ea7a272164d553f1ad48e097212170d089efeb6d9ac1cde3e275d4c",
      "claudedocs/mcp-just-works-m1-plan-2026-11-05.md": "3925ed00306b3a44d60c6f8e4afbebfac6122c63a147d839622547a309b7d607",
      "claudedocs/mcp-launch-root-probe-2026-11-05.md": "f0107cde23f1655e0b1b62f9e32dffbc61e82c93aaec17bcd6131ff725978782",
      "docs/02-how-to/mcp-setup-other-repos.md": "bcbdc732da1508e5a78fe1abb9b743b4a3afca126644ea57895b03b62d2fdc40",
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
      "src/dopemux/mcp/conport_tenant.py": "5ae27b50dd30551897cfbf2a0ec4f6f99fe105f0fe6a0567664ed7ef959ec0a8",
      "src/dopemux/mcp/default_catalog.yaml": "6aa71c9d51cd4979fa778f93f850d8b44b85fcce47ff34c338ebb474af3f062e",
      "src/dopemux/mcp/docker_inspect.py": "881a825e018abfcc7c7d6f2ba017e8a7687176b7303fa15ed1ea564faf6461a9",
      "src/dopemux/mcp/docker_runtime.py": "078aeb0327735fe02bee8305d947b01d7eeaa1e287dd70e1e20a6ab3eee76d23",
      "src/dopemux/mcp/doctor.py": "e117c8d90e2df11d08b45bac2160975770fe0a15f63e27fdea89bbd1d98da6d2",
      "src/dopemux/mcp/fleet_catalog.py": "7352fed0b7ecce1b9f957ad6a32b490ca91c06c76793fbe4cc465e78e85718fd",
      "src/dopemux/mcp/launcher.py": "7eff6236db4b7bf7704c265d212fdb8518b89edc3aea0fad1f5c3f3ff84deb52",
      "src/dopemux/mcp/lifecycle.py": "8fa97734e24383f88359bfebbfc85f70dd7bb4b912d9e6f102e04fa6027b7876",
      "src/dopemux/mcp/locks.py": "97f24e35f3b36d8c1a44d1cd4983a573037cc62fb9adf54a78ad9cea8c90c85b",
      "src/dopemux/mcp/mcp_json.py": "ca24effbc9728db325e3cf8f5e6a45f4e3046ca35051bf4d57c711ef7ee6524b",
      "src/dopemux/mcp/port_allocator.py": "2d51347176fbe2517321284a8eac25db1520a2d5bb3ecda6598ba5218025fdc4",
      "src/dopemux/mcp/project_identity.py": "3358bc22ead2a2073910caccdf6d676f46a850f67604d066eb20ff48a869e70b",
      "src/dopemux/mcp/reap.py": "2476f443868f9878b425dff8ff45f081acc1422d289d106b2fbafeb7b0b355b6",
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
      "tests/unit/test_mcp_launcher.py": "0b483cdac39f1279a71a7c4f550b61bb0f9fd2d0db78094f0d7b7b3e14050923",
      "tests/unit/test_mcp_launcher_render.py": "d821b655d6eb4e6e764651fca51a8cbc2bc633c58165e55b29557d85fec05923",
      "tests/unit/test_mcp_lifecycle.py": "b7fae4fef0a288107cab6e4fa3b9af698350e01808809107d2bf2b89001f60fa",
      "tests/unit/test_mcp_lifecycle_ports_from_leases.py": "77deaa9a1d578acadee43e1fa059fddacee67d79738a60471432a8742df501da",
      "tests/unit/test_mcp_locks.py": "fe03f4da82ff8c4e82fdf3f89ebf533b1f67da9e637542de975dd5eaf7bfccc8",
      "tests/unit/test_mcp_port_allocator.py": "f4215352a4bee019b88e0602d7d1392dc0631d0a91afc03fabcb99bd5060d1cd",
      "tests/unit/test_mcp_profile_doctor.py": "05716fa700def0d089968149c2ddf0cd784da1103e2f22f0265120e6d8768b06",
      "tests/unit/test_mcp_reap.py": "b575ca7f6b2a1d8990290b19c1d3b1b21ca8e0eaeffeeaab088670c8aaa945d2",
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
      "id": "C1_diff_read_in_full",
      "command_or_method": "read_file across subject.diff (lines 1-19071), subject-src.diff (lines 1-7562), FILES.sha256, COMMITS.txt, design.md, plan.md, howto-mcp-setup-other-repos.md, LEDGER_SUMMARY.md, VALIDATIONS.md",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "All 19,071 lines of subject.diff (67 files across 20 commits 5742575c4..3bf5d4f26deb3368e965b86599a2a05520a1e59b) and supporting subject documents read and verified."
    },
    {
      "id": "C2_secrets_argv_log_review",
      "command_or_method": "Static audit of src/dopemux/mcp/conport_tenant.py, src/dopemux/mcp/docker_runtime.py, src/dopemux/mcp/lifecycle.py, src/dopemux/commands/mcp_commands.py, src/dopemux/mcp/doctor.py, src/dopemux/mcp/launcher.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:153 (repr=False), 208-224 (0700 dir / 0600 secrets.env), 354-384 (psql SQL on stdin), 404-440 & 659-665 (SCRAM-SHA-256 verifier on stdin; _redacted_tail scrubs password and verifier before 300-char slice), 720-780 (adopt_with_gate uses 0600 temp --env-file removed in finally); docker_runtime.py:293-315 (generate_mcp_env strips secrets); lifecycle.py:1645-1695 & 1892-1949 (tenant_compose_env passed only to conport compose up env, never mcp.env or start-plan.json)."
    },
    {
      "id": "C3_lock_order_and_inode_review",
      "command_or_method": "Static audit of src/dopemux/mcp/locks.py, src/dopemux/mcp/launcher.py, src/dopemux/mcp/lifecycle.py, src/dopemux/mcp/reap.py, src/dopemux/mcp/conport_tenant.py, src/dopemux/commands/mcp_commands.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "locks.py:8-28 & 78-121 (_flock inode/device re-check fstat vs stat with 50-attempt retry on unlink; thread-reentrant reserved_port_lock). Lock order (instance_lock > registry_lock, reserved_port_lock > registry_lock, instance_lock > provision_lock) holds at all call sites: launcher.py:450, 537, 761; lifecycle.py:680, 1333, 1578, 2036, 2129, 2395, 2419, 4185; reap.py:553, 566, 788; mcp_commands.py:470, 495."
    },
    {
      "id": "C4_reconnect_and_guard_review",
      "command_or_method": "Static audit of src/dopemux/mcp/stdio_proxy.py and src/dopemux/mcp/launcher.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:192-202 (_session_terminated checks code 32600 and 'Session terminated'), 347-379 (checkpoint 1 before connect and checkpoint 2 after session.initialize() on both first session and every reconnect), 463-501 (MAX_SENDS_PER_REQUEST=2; in-flight CONNECTION_CLOSED never replayed), 529-586 (_answer_with_refusal surfaces -32000 refusal when first session is refused), 108-114 & 381-393 (backoff 0.25..2.0s over 10s wait, 1 reconnect per 60s window); launcher.py:604-695 (reconnect_guard)."
    },
    {
      "id": "C5_reap_safety_review",
      "command_or_method": "Static audit of src/dopemux/mcp/reap.py, src/dopemux/claude/native_hooks.py, src/dopemux/mcp/launcher.py, src/dopemux/commands/mcp_commands.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "reap.py:258-269 & 833-834 (kill-switch precedence), 352-366 & 412-446 (worktree scope + RuntimeRegistry join; missing last_detach never idle), 461-522 (state-only candidates when no container exists; _owned_by excludes task-orchestrator), 665-680 & 785-912 (non-blocking instance_lock in maybe_reap, bounded docker inspect/stop/rm timeouts, _restore_throttle when nothing attempted)."
    },
    {
      "id": "C6_ambient_env_scrub_review",
      "command_or_method": "Static audit of src/dopemux/mcp/docker_runtime.py, src/dopemux/mcp/runtime_state.py, src/dopemux/mcp/project_identity.py, src/dopemux/worktree_commands.py, src/dopemux/mcp/launcher.py, src/dopemux/commands/mcp_commands.py",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "docker_runtime.py:51-74 (21 vars in AMBIENT_SCRUB_VARS) & 137-194 (env_with_compose_interpolation scrub_ambient=True); mcp_commands.py:140-154 (_lifecycle_process_env); launcher.py:373-393 (_lifecycle_env scrubs AMBIENT_SCRUB_VARS plus catalog port vars); runtime_state.py:124-213, project_identity.py:114-149, worktree_commands.py:53-112 (git-only identity unless trust_env=True)."
    },
    {
      "id": "C7_docs_vs_code_truthfulness_howto",
      "command_or_method": "Static audit comparing docs/02-how-to/mcp-setup-other-repos.md, .claude/claude.md, and AGENTS.md against src/dopemux/mcp/*",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "docs/02-how-to/mcp-setup-other-repos.md (lines 1-587) and .claude/claude.md accurately match all CLI flags, refusal codes, lock/reap semantics, and shared image tags; one stale sentence in AGENTS.md:309-310 noted as low finding F1."
    },
    {
      "id": "C8_live_validations_and_acceptance_T1_T11",
      "command_or_method": "Live execution of pytest / git diff / docs_validator / Docker acceptance checks T1-T11",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Auditor environment is a read-only scratchpad without live host shell or Docker daemon; VALIDATIONS.md and LEDGER_SUMMARY.md claims are recorded under author_claims_not_reproduced and unknowns."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "low",
      "location": "AGENTS.md:309",
      "summary": "AGENTS.md §12.3 still states that the first launch in a new worktree builds its images, whereas sidecar images are now shared per service and Dockerfile version across all worktrees and projects.",
      "evidence": "AGENTS.md:309-310 says 'The first launch in a new worktree builds its images (LAUNCH_IMAGE_BUILDING; then /mcp reconnect all).' Commit eb3f0624b changed docker_runtime.py:compose_image_name (lines 195-221) to tag dopemux-<service>:<12-hex-dockerfile-key> host-wide and updated .claude/claude.md:279-281 and docs/02-how-to/mcp-setup-other-repos.md:126-130, but did not update AGENTS.md:309-310."
    }
  ],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "VALIDATIONS.md: pytest (make test-fast + 15 new/touched test files) -> 1647 passed, 8 skipped, 1 xfailed in 56.34s",
    "VALIDATIONS.md: pytest tests/test_native_hooks_workflow.py tests/unit/test_native_hooks_dispatcher.py tests/unit/test_native_hooks_register.py -> 34 passed in 2.68s",
    "VALIDATIONS.md: python scripts/docs_validator.py && python scripts/docs_frontmatter_guard.py -> exit 0 (All 612 documents are valid)",
    "VALIDATIONS.md: git diff 5742575c4..3bf5d4f26 -- src/ tests/ | flake8/black/isort/mypy --diff -> 0 new issues",
    "LEDGER_SUMMARY.md: Live owner-run checks L1-L8 and design §6 T1-T11 against live Docker, dopemux-postgres-age, and target checkouts"
  ],
  "remaining_risks": [
    "AGENTS.md:309-310 retains pre-eb3f0624b wording ('first launch in a new worktree builds its images') while .claude/claude.md and docs/02-how-to/mcp-setup-other-repos.md state the host-wide shared image rule (F1, low).",
    "Shared sidecar image tag dopemux-<service>:<12-hex-key> hashes only the service name and Dockerfile bytes (docker_runtime.py:195-221); edits to Python sources under services/ that do not touch the Dockerfile require manual 'docker image rm' or 'docker compose build' as documented in docs/02-how-to/mcp-setup-other-repos.md:130.",
    "Deferred M1 items D-1..D-9 recorded in LEDGER_SUMMARY.md (mid-session EnterWorktree requiring /mcp reconnect all; single host-wide task-orchestrator on :7890 mitigated by switch-project and two-checkpoint reconnect guard; per-worktree conport/dope-memory containers mitigated by reap; legacy shared Postgres row migration deferred to M2)."
  ],
  "unknowns": [
    "Live execution of design §6 acceptance checks T1-T11 and test suites at 3bf5d4f26deb3368e965b86599a2a05520a1e59b (not runnable in the read-only audit environment without live Docker/Postgres).",
    "Observed runtime model and effort receipt for this auditor session (not exposed by runner environment)."
  ],
  "skip_reason": null,
  "unblock": [
    "Optional polish: update AGENTS.md:309-310 to state that sidecar images are built once per host and Dockerfile version rather than per new worktree."
  ],
  "acceptance": "NOT_GRANTED"
}
```
