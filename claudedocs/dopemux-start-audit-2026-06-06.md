# dopemux start — Read-Only Audit Report

**Date:** 2026-06-06  
**Commit:** `e35aae0e4` (branch `claude/modest-cartwright-340c04`, clean tree)  
**Confidence:** VERIFIED for all claims marked OBSERVED; INFERRED where noted; UNKNOWN where noted.

---

## 1. Scope & Method

### What was inspected

| Artifact | Lines / Size | Method |
|---|---|---|
| `src/dopemux/cli.py` | 6,408 lines | Read directly |
| `compose.yml` | 677 lines | Read directly + parsed via Python |
| All 22 test files listed in the task prompt | varies | Read directly |
| `.env.example` | 61 lines | Read directly |
| `src/dopemux/mcp/gate.py` | ~150 lines | Read directly |
| `src/dopemux/mcp/provision.py` | referenced | Inferred from tests |

### CLI-not-installed caveat

`python -m dopemux` is unavailable in this worktree (package not pip-installed). The `dopemux` console-script entry point (`dopemux.cli:main`) is only reachable via `pytest.ini` `pythonpath = src` during test runs. This means:

- **No integration test can invoke the real `dopemux start` binary end-to-end** in this environment without first installing the package.
- All integration tests listed use `click.testing.CliRunner` (in-process invocation of `cli`) or direct function imports — this is the only feasible approach.
- The worktree *does* have `.dopemux/` initialized (`mcp.instances.toml` exists), so the "project not initialized" branch should not trigger if `Path.cwd()` resolves to the worktree root.

### Authority used

Runtime code (`cli.py`) outranks all other sources. Compose file parsed programmatically (not trusted from task-prompt description). `.env.example` inspected for secret inventory.

---

## 2. Command Surface Matrix

OBSERVED from decorator lines 846–958 of `src/dopemux/cli.py`.

| Flag(s) | Python Param | Type | Default | What it does | Interactions / Mutual Exclusions |
|---|---|---|---|---|---|
| `--session / -s` | `session` | `str\|None` | None | Restore a specific session ID via `ContextManager.restore_session()` | No conflicts |
| `--background / -b` | `background` | bool flag | False | Detached `Popen` (stdout/stderr=DEVNULL, start_new_session=True); skips interactive role wizard | No conflicts |
| `--debug` | `debug` | bool flag | False | Passed to `ClaudeLauncher.launch(debug=True)` → adds `--debug` to claude command | No conflicts |
| `--dangerous` | `dangerous` | bool flag | False | Triggers `_activate_dangerous_mode()` — 1hr timeout, 2 interactive confirms, sets 7 env vars | Equivalent to `--dangerously-skip-permissions` |
| `--dangerously-skip-permissions` | `dangerously_skip_permissions` | bool flag | False | Same as `--dangerous` (identical code path at line 2386) | Equivalent to `--dangerous` |
| `--no-mcp` | `no_mcp` | bool flag | False | Skips `_start_mcp_servers_with_progress()` call | Skips autoindex too |
| `--no-recovery` | `no_recovery` | bool flag | False | Skips `show_recovery_menu_sync()` call | No conflicts |
| `--litellm` | `use_litellm` | bool flag | False | Starts `LiteLLMProxyManager` (per-instance, needs OPENROUTER_API_KEY) | Auto-enables CCR unless `--no-claude-router` |
| `--alt-routing` | `use_alt_routing` | bool flag | False | Full alt-routing subprocess path: loads `.env.routing`, needs `DOPEMUX_LITELLM_DB_URL`, starts `litellm` subprocess on 0.0.0.0, 20s health wait | MUTEX with provider flags (`--grok`/`--codex`/`--altp`) |
| `--claude-router / --no-claude-router` | `use_claude_router` | bool flag | **False** | Starts `DopeBrainzRouterManager.ensure_started()` | Auto-enabled when `--litellm` is set or `--altp` is used |
| `--role / -r` | `role` | `str\|None` | None | Activates role via `activate_role()` in `roles/catalog.py`; applies profile; sets up ClaudeConfigurator | If not provided and not `--background`/`--dry-run` and tty → interactive wizard |
| `--dry-run` | `dry_run` | bool flag | False | Prints plan, skips MCP startup and Claude launch; exits after role/profile preview | Skips LiteLLM DB sync too |
| `--grok` | `use_grok` | bool flag | False | Single-target routing to xAI Grok; needs `XAI_API_KEY`; starts `start_simple_proxy()` on port 4000-4002 | MUTEX with `--codex`, `--altp`, `--alt-routing` |
| `--codex` | `use_codex` | bool flag | False | Single-target routing to OpenAI GPT-5 Codex via OpenRouter; needs `OPENAI_API_KEY`; same proxy path as `--grok` | MUTEX with `--grok`, `--altp`, `--alt-routing` |
| `--altp` | `use_altp` | bool flag | False | Tier-matched routing (opus→Codex, sonnet→GPT-5-Mini, haiku→Grok); needs all 3 ALTP_* keys; auto-enables CCR | MUTEX with `--grok`, `--codex`, `--alt-routing`; silently no-ops in subscription mode |
| `--no-routing-repair` | `no_routing_repair` | bool flag | False | In `api` routing mode: skip the LiteLLM/CCR health repair loop; raises immediately if unhealthy | Only meaningful in `api` routing mode |
| `--routing-repair-max` | `routing_repair_max` | int | 3 | Max passes for `LaunchdServiceManager.repair()` | Only meaningful in `api` routing mode |
| `--routing-repair-no-sync-keys` | `routing_repair_no_sync_keys` | bool flag | False | Skip API key sync in repair | Only meaningful in `api` routing mode |
| `--routing-fallback-subscription` | `routing_fallback_subscription` | bool flag | False | If repair fails, fall back to subscription mode instead of raising | Only meaningful in `api` routing mode |

**Notable design notes (OBSERVED):**

- `--grok`/`--codex`/`--altp`/`--alt-routing`/`--claude-router` are all flagged as deprecated when a `routing.yaml` config exists (line 1054–1060). The new preferred path is `dopemux routing mode api|subscription`.
- `--altp` silently no-ops with a warning instead of failing if routing mode is not `api` (line 1280–1289). This could surprise users.
- `--dangerous` and `--dangerously-skip-permissions` are identical in effect (lines 2386–2389). There is no code difference between them — both simply set `is_dangerous_mode = True`.
- There are **two definitions of `_activate_dangerous_mode()`** in `cli.py` — at line 3875 (with interactive confirm) and line 5914 (without). Line 2389 calls the function in the module scope; Python will use the **last** definition at module load time (line 5914), which lacks interactive confirmation. **This is a bug (OBSERVED).**

---

## 3. Branch Map

OBSERVED from `cli.py` lines 975–2563. Line numbers are approximate ±5 due to file length.

### Phase 0: Preflight (lines 975–1029)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| Always | `boot_sequence()` splash | None | Exception caught silently |
| Always | `validate_agents_in_workspace(workspace_root)` | `get_workspace_root()` succeeds | Exception caught with warning; continues |
| `RoutingConfig` importable | Load `routing.yaml` to set `routing_mode` and `routing_ports` | `routing.yaml` exists | Falls back to legacy-flag behavior with warning |

### Phase 1: Routing Mode Selection (lines 1031–1713)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `routing_mode == "api"` (new config path, no deprecated flags) | `LaunchdServiceManager.check_health()` → repair loop → set `ANTHROPIC_BASE_URL=http://127.0.0.1:{ccr_port}` | LiteLLM+CCR running as launchd services; `DOPEMUX_CCR_API_KEY` in env | Raises `ClickException` unless `--routing-fallback-subscription` |
| `routing_mode == "subscription"` (new config path) | Unsets `ANTHROPIC_BASE_URL`, `DOPEMUX_ROUTING_MODE` | None | None |
| `use_grok or use_codex` (deprecated, legacy path) | `start_simple_proxy()` on port 4000-4002; sets `ANTHROPIC_BASE_URL` | `XAI_API_KEY` (grok) or `OPENAI_API_KEY` (codex); litellm package importable; port 4000-4002 free | `ClickException` on missing key or port collision |
| `use_altp` in api mode (deprecated) | `generate_multi_target_config()`; `start_simple_proxy()`; auto-enables CCR | All 3 `ALTP_*` keys; routing mode == api | `ClickException` on missing keys |
| `use_altp` in subscription mode | Silently warns and disables `use_altp` | None | Silent no-op |
| `use_alt_routing` (deprecated) | Loads `.env.routing`; DB URL resolution; `sync_litellm_database()`; `pkill -f litellm`; spawns `litellm` subprocess on **0.0.0.0**; waits 20 iterations (20s) for health | `DOPEMUX_LITELLM_DB_URL` (or env var chain); PostgreSQL reachable; port 4000-4002 free | `ClickException` on DB not ready or proxy fail |
| `DOPEMUX_DEFAULT_LITELLM == "1"` env | Auto-enables `use_litellm` and `use_claude_router` | None | None |
| `DOPEMUX_USE_OPENROUTER == "1"` env | Calls `_configure_openrouter_litellm()`; sets `ANTHROPIC_BASE_URL=http://127.0.0.1:4000` | LiteLLM proxy running on 4000 | Silent if proxy not running |

### Phase 2: Role & Project Detection (lines 1715–1803)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `--role` provided | `activate_role(role, config_manager, console)` | Role exists in catalog | `sys.exit(1)` on `RoleNotFoundError` |
| No role, interactive tty, not `--background`, not `--dry-run` | `start_wizard()` → interactive role selection | `sys.stdin.isatty()` | User cancel → `sys.exit(0)` |
| No role, non-interactive or background | Defaults to `"developer"` | None | None |
| Role found | `_ensure_role_profile(spec)` → `pending_profile_name` | Profile defined in profiles config | Warning if profile not found |
| `.dopemux/` not found in `cwd` or `workspace_root` | Prompts user to run `dopemux init` | None | `sys.exit(1)` if user declines init |

### Phase 3: Dangerous Mode (line 2382–2389 invokes; defined at 5914)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `dangerous or dangerously_skip_permissions` | `_activate_dangerous_mode()` (line 5914 — **no confirm**); sets 7 env vars | None | None |
| IMPORTANT: The _effective_ `_activate_dangerous_mode()` is the **second definition** at line 5914, which does NOT show warnings or require interactive confirmation. The interactive version at line 3875 is shadowed. |

### Phase 4: Tmux Kill (lines 1873–1893)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `tmux` on PATH and `TMUX` env not set | `tmux kill-server` (destroys ALL tmux sessions) | tmux installed | Exception silently caught; continues |
| Inside tmux (`TMUX` env set) | Skips kill | None | None |

### Phase 5: Instance Management (lines 1976–2101)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| First instance (no running instances) | `instance_id = "A"`, `port_base = 3000` | None | None |
| Running instances detected | Interactive: confirm create new worktree on next port (3030+) | Interactive tty | `RuntimeError` if instance_id exhausted → `sys.exit(1)` |
| `DOPEMUX_FORCE_INSTANCE_ID` set | Overrides instance_id/port if not already in use | Instance ID must be in AVAILABLE_IDS | Silent ignore if ID in use |
| `DOPEMUX_ALLOW_MAIN != "1"` | `check_and_protect_main()` → may set `should_exit` | Git repo | `sys.exit(0)` if on main and no new worktree |

### Phase 6: LiteLLM Manager Path (lines 2179–2242)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `use_litellm` and not alt-routing and not direct-provider-proxy | `LiteLLMProxyManager(project_path, instance_id, port_base).ensure_started()` | `OPENROUTER_API_KEY` set | `sys.exit(1)` if missing key; re-raises on other errors |
| CCR: `use_claude_router` and not direct-provider | `DopeBrainzRouterManager.ensure_started()` | `provider_url` configured; models list non-empty | `sys.exit(1)` |

### Phase 7: MCP Startup (lines 2419–2447)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `not no_mcp` | `_start_mcp_servers_with_progress()` | Docker running; compose files found | `ClickException("MCP stack provisioning failed.")` or `RuntimeError("Docker compose failed")` or `RuntimeError("MCP Discovery Gate failed.")` |
| `DOPEMUX_SKIP_MCP_START == "1"` | Skip | None | None |
| `DOPEMUX_AUTO_INDEX_ON_STARTUP != "0"` | POST to dope-context `/autoindex/bootstrap` | dope-context service running on `DOPE_CONTEXT_URL` (default 3010) | Non-blocking; returns status dict on failure |

### Phase 8: Context + Claude Launch (lines 2357–2464)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| `--session` provided | `ContextManager.restore_session(session)` | Session file exists | Returns None; fresh session used |
| No `--session` | `ContextManager.restore_latest()` | `.dopemux/` context files | Returns None; fresh session used |
| Always | `ClaudeLauncher(config_manager).launch(...)` | Claude Code on PATH | `ClaudeNotFoundError` raises |
| `--background` | Detached Popen (DEVNULL stdout/stderr) | None | None |
| Not `--background` | Foreground `claude_process.wait()` | None | None |

### Phase 9: Post-Launch (lines 2466–2563)

| Trigger | Effect | Preconditions | Failure mode |
|---|---|---|---|
| Always | `claude_hooks.start_monitoring(str(project_path))` | None | Exception not caught explicitly |
| Always | `AttentionMonitor(project_path).start_monitoring()` | None | Exception not caught explicitly |
| `instance_id` and `port_base` set | `save_instance_state_sync(state, workspace_id, conport_port=3004)` | ConPort running on port 3004 | Exception not caught — potential crash |
| Ctrl+C (not `--background`) | Mark instance stopped in ConPort; `ctx.invoke(save)`; `attention_monitor.stop_monitoring()` | ConPort accessible | Silent if ConPort unavailable |

---

## 4. Stack Inventory

OBSERVED from `compose.yml`. All 23 services confirmed. 20 have healthchecks; 3 do not.

| Service | Default Port(s) | Depends On | Healthcheck | Host Binding | Required for Usable Cockpit | Secrets Required |
|---|---|---|---|---|---|---|
| postgres | 5432 | — | yes (`pg_isready`) | 0.0.0.0 (exposed) | YES (foundation) | `AGE_PASSWORD` |
| redis-events | 6379 | — | yes (`redis-cli ping`) | 0.0.0.0 (exposed) | YES (event bus) | `REDIS_PASSWORD` (opt) |
| redis-primary | 6380 | — | yes (`redis-cli ping`) | 0.0.0.0 (exposed) | YES (caching) | `REDIS_PASSWORD` (opt) |
| mysql_leantime | (internal) | — | yes (`mysqladmin ping`) | none (no published port) | Optional (Leantime PM) | `MYSQL_ROOT_PASSWORD` |
| redis_leantime | (internal) | — | yes (`redis-cli ping`) | none | Optional (Leantime PM) | `REDIS_PASSWORD` (opt) |
| leantime | 8080 | mysql_leantime, redis_leantime | yes (curl /) | 0.0.0.0 (exposed) | Optional (PM UI) | `LEANTIME_TOKEN` |
| redis-ui | 8081 | — | **NO** | 0.0.0.0 (exposed) | No (debug UI) | none |
| mcp-qdrant | 6333, 6334 | — | **NO** | 0.0.0.0 (exposed) | YES (embeddings) | `QDRANT_API_KEY` (opt) |
| conport | 3004, 3005, 4004 | postgres, redis-primary, mcp-qdrant, dopecon-bridge | yes (curl /health) | 0.0.0.0 (exposed) | YES (knowledge graph) | `AGE_PASSWORD` |
| pal | 3003 | — | **trivial** (`exit 0`) | 0.0.0.0 (exposed) | Conditional (PAL reasoning) | `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` |
| litellm | 4000 | postgres | yes (curl /health with auth) | 0.0.0.0 (exposed) | Conditional (api routing mode) | `LITELLM_MASTER_KEY`, `ANTHROPIC_API_KEY` |
| dope-context | 3010 | mcp-qdrant | yes (curl /health, exit 0 on fail) | 127.0.0.1 (loopback) | YES (autoindex) | `VOYAGE_API_KEY`, `HOST_CODE_PARENT_DIR`, `HOST_PROJECT_RELATIVE_PATH` |
| dopecon-bridge | 3016 | postgres, redis-events, mcp-qdrant | yes (curl /health) | 0.0.0.0 (exposed) | YES (event routing) | `AGE_PASSWORD` |
| task-orchestrator | 8000 | redis-primary, conport, leantime | yes (curl /health) | 0.0.0.0 (exposed) | Optional (orchestration) | `TASK_ORCHESTRATOR_API_KEY`, `LEANTIME_TOKEN` |
| adhd-engine | 3025 | redis-primary | yes (curl /health) | 127.0.0.1 (loopback) | Conditional (attention monitor) | `ADHD_ENGINE_API_KEY`, `ADHD_ENGINE_REDIS_PREFIX` |
| dope-memory | 3020 | postgres, redis-events | yes (curl /health) | 0.0.0.0 (exposed) | Optional (working memory) | `AGE_PASSWORD`, `WMA_SECRET_KEY` |
| serena | 3006, 4006 | — | yes (curl /health on 4006) | 0.0.0.0 (exposed) | Optional (code nav) | `DOPEMUX_WORKSPACE_ROOT` |
| gptr-mcp | 3009 | — | yes (curl /health) | 0.0.0.0 (exposed) | Optional (deep research) | `OPENAI_API_KEY`, `TAVILY_API_KEY` |
| desktop-commander | 3012 | — | yes (curl /health) | 127.0.0.1 (loopback) | Optional | `DISPLAY` |
| exa | 3011 | — | yes (curl /health) | 0.0.0.0 (exposed) | Optional (search) | `EXA_API_KEY` (NOT in .env.example) |
| leantime-bridge | 3015 | mcp-qdrant, leantime | yes (curl /health) | 127.0.0.1 (loopback) | Optional (PM integration) | `LEANTIME_TOKEN` |
| webhook-receiver | 8790 | — | yes (urllib) | 127.0.0.1 (loopback) | Optional | `OPENAI_WEBHOOK_SECRET` (NOT in .env.example) |
| webhook-poller | (no port) | — | **NO** | none | Optional | none |

**OBSERVED anomalies:**
- `pal` healthcheck is `exit 0` — always passes regardless of actual service state. This means the compose dependency graph treats PAL as healthy even if it is completely non-functional.
- `mcp-qdrant` has no healthcheck. Conport's `service_started` condition for qdrant means it starts without confirming qdrant readiness.
- `EXA_API_KEY` and `OPENAI_WEBHOOK_SECRET` and `MYSQL_ROOT_PASSWORD` are required by compose services but are absent from `.env.example`.
- `dope-context` healthcheck uses `exit 0` on curl failure — it always reports healthy.

---

## 5. Current Coverage Map

OBSERVED from reading each test file.

| Test File | What It Asserts | Real Services or Mocks |
|---|---|---|
| `tests/integration/test_start_command.py` | Basic env setup (ContextManager, Launcher called with right args); `--litellm` flag configures proxy/router mgrs; `--dangerous` sets env vars; `--no-mcp` skips MCP call; auto-config MCP triggers. 4 tests. | All mocked (Popen, managers, AttentionMonitor) |
| `tests/test_cli_mcp_startup.py` | `_resolve_mcp_dir()` strategy fallbacks; `_start_mcp_servers_with_progress()` raises on None; skip flag works; Popen called; autoindex calls endpoint; autoindex can be disabled. 7 tests. | All mocked (Popen, requests.post) |
| `tests/dopemux/test_startup_integration.py` | `show_recovery_menu_sync` importable; graceful on non-git dir; no orphaned sessions → None; menu called with correct args; error handling on bad path. 8 tests. | Mostly real (spawns temp git repos); mocks `WorktreeRecoveryMenu` for interactive tests |
| `tests/unit/test_task_orchestrator_startup.py` | Task-orchestrator service `app.main` imports without pre-configured src path; coordinator fallback raises RuntimeError. 2 tests. | No real services (module load via importlib) |
| `tests/test_claude_launcher.py` | `ClaudeLauncher` detection (PATH, config, not-found); `launch()` interactive/background/debug; config generation (env vars, MCP servers, ADHD vars, timeout, disabled servers); env preparation; MCP validation. 17 tests. | All mocked (Popen, subprocess, shutil.which) |
| `tests/test_instance_manager_env.py` | `get_instance_env_vars()` computes HOST_CODE_PARENT_DIR/HOST_PROJECT_RELATIVE_PATH correctly for instance A and B. 1 test. | No real services |
| `tests/test_instance_manager_ports.py` | Port offset calculations for instances A and B. 1 test. | No real services |
| `tests/dopemux/test_instance_state_filtering.py` | `InstanceStateManager` orphan filtering (age, count, sorting). | Mocked ConPort |
| `tests/test_roles_catalog.py` | `available_roles()` includes core personas; role activation logic. | No real services |
| `tests/unit/test_launcher_wizard.py` | Wizard uses shared console; footer renders status chip; role selection uses interactive prompts. 3 tests. | No real services (monkeypatched) |
| `tests/test_routing_config.py` | `RoutingConfig` alias audit/repair; routing doctor; alias contract. | No real services |
| `tests/unit/test_alt_routing_config.py` | `_load_litellm_models()` helper loads from instance dir config; config selection logic. 2 tests. | No real services |
| `tests/mcp/test_discovery_gate.py` | `DiscoveryGate.run()` with mock aiohttp server; tool validation. **Has no assertions on failure** — prints only (noted in strict test comments as vacuous). | Mock aiohttp TCP server |
| `tests/mcp/test_discovery_gate_strict.py` | Provenance-aware failure policy: mandatory server unreachable → BLOCK; optional server unreachable → WARN; `strict_optional` escalates to BLOCK; tool-glob mismatch logic. | Mocked resolver + discovery (fully deterministic) |
| `tests/mcp/test_resolver.py` | `InstanceResolver` precedence: repo_profile > env_var > global fallback. | Temp filesystem + env vars |
| `tests/mcp/test_provision.py` | `MCPProvisioner.ensure_stack_present()` first-run (symlink); idempotency; instance overlay uniqueness. | Temp filesystem |
| `tests/mcp/test_conport_mcp_real.py` | ConPort `EnhancedConPortServer` MCP endpoint: `tools/list`, `log_progress`, `search_context`. | Mocked asyncpg + redis |
| `tests/mcp/test_conport_surface_contract.py` | 4 async tests for ConPort MCP tool API contract: `log_progress` defaults to `IN_PROGRESS` status; `log_decision` formats summary with topic prefix; tests both fastmcp and stdio transports. Uses mocked `_post_json`. | Mocked `_post_json` (no real services) |
| `tests/mcp/test_mcp_internal_lockdown.py` | `_build_child_env()` does not leak undeclared secrets; `SessionManager._safe_session_filename` sanitizes. | No real services |
| `tests/unit/test_health.py` | `HealthChecker` init, `check_all()`, exception handling. | Mocked psutil + docker |
| `tests/test_mcp_config_generation.py` | Template MCP names exist in registry; docker HTTP uses bridge; MCP name mapping. | No real services |
| `tests/test_mcp_registry.py` | Registry loads, contains required servers, schema valid, names unique. | No real services |

**What is well-covered (do not duplicate):**

- Port offset calculation for multi-instance (test_instance_manager_ports.py)
- HOST path calculation for dope-context mounts (test_instance_manager_env.py)
- Role catalog presence and activation (test_roles_catalog.py)
- MCP provisioner symlink/idempotency (test_provision.py)
- Discovery gate provenance-aware failure policy (test_discovery_gate_strict.py)
- Secret leakage prevention in child envs (test_mcp_internal_lockdown.py)
- Registry schema validity (test_mcp_registry.py)
- Claude launcher interactive/background/debug modes (test_claude_launcher.py)
- `--litellm` flag proxy/router manager lifecycle (test_start_command.py)
- Autoindex startup endpoint call (test_cli_mcp_startup.py)

---

## 6. Gap Register

Severity: **CRIT** = startup silently broken or security regression; **HIGH** = major path untested; **MED** = important branch with mocked-only coverage; **LOW** = nice-to-have.

### CRIT

| ID | Branch / Component | Gap | Why it matters | Coverable by |
|---|---|---|---|---|
| GAP-C1 | `_activate_dangerous_mode()` — duplicate definition | There are two definitions (line 3875 with confirm, line 5914 without). Python uses the last one; the one invoked at line 2389 has no interactive confirmation or security warnings. All existing tests mock it out or check env vars only — none verify confirm behavior. | Security regression: users expect two interactive confirms before dangerous mode activates; they get zero. | Contract test: assert `_activate_dangerous_mode()` is the function at line 3875 (or that the invoked function requires stdin confirm). No secrets needed. |
| GAP-C2 | `save_instance_state_sync()` at startup (line 2517) | Called unconditionally after Claude launch with no exception handling. If ConPort is unreachable, this will raise and crash the process after Claude has already started. | Process dies after Claude launches — user sees partial startup. | Contract test: mock `save_instance_state_sync` to raise; assert start exits gracefully. No secrets. |
| GAP-C3 | `--alt-routing` starts litellm on `0.0.0.0` (line 1612) | The litellm subprocess is bound to `0.0.0.0` — network-accessible with the master key as the only auth. No test exercises this path or validates the bind address. | Secret-carrying service exposed to local network. | Contract test: assert subprocess args do not include `0.0.0.0` (or document the intentional exposure). No real services needed. |

### HIGH

| ID | Branch / Component | Gap | Why it matters | Coverable by |
|---|---|---|---|---|
| GAP-H1 | `api` routing mode (RoutingConfig + LaunchdServiceManager) | No test exercises the `routing_mode == "api"` path. The entire `LaunchdServiceManager` health check + repair loop is untested. | Default new-config path for all api-key users. | Contract test (mocked LaunchdServiceManager); no real services. |
| GAP-H2 | `routing_mode == "api"` repair failure → `--routing-fallback-subscription` fallback | Branch at line 1160 where repair fails and fallback is invoked, including `_ensure_env_consistent_with_mode("subscription")`. | Fallback cleans up env vars; if it doesn't, stale ANTHROPIC_BASE_URL could break Claude. | Contract test (mocked health always-fail + routing_fallback_subscription=True). |
| GAP-H3 | `--grok` / `--codex` legacy provider paths | `start_simple_proxy()` is called; env vars set (ANTHROPIC_BASE_URL, LITELLM_MASTER_KEY, ANTHROPIC_API_KEY). No integration test exercises this path beyond unit tests of the proxy function itself. | Used by some workflows; key conflicts with existing ANTHROPIC_API_KEY. | Contract test with mocked `start_simple_proxy`. Needs `XAI_API_KEY` or `OPENAI_API_KEY` for real run. |
| GAP-H4 | `--altp` silent no-op in subscription mode | When `--altp` is passed but routing mode is subscription, the flag silently disables itself (line 1288). No test verifies this behavior. | User confusion: `--altp` appears to succeed but does nothing. | Contract test: invoke with `--altp`, mock routing to return "subscription", assert `use_altp == False` after and warning logged. |
| GAP-H5 | `tmux kill-server` at startup (lines 1874–1892) | No test verifies that tmux kill-server is called, or that it is skipped when inside tmux (`TMUX` env set). | Destroys all existing tmux sessions on the machine. | Contract test: mock `subprocess.run`; assert called or not-called based on `TMUX` env. |
| GAP-H6 | `check_and_protect_main()` + worktree creation (lines 1950–2055) | Interactive path (user sees multi-instance table, confirms worktree creation) is exercised only via a worktree recovery unit test that doesn't cover the full InstanceManager flow. No test verifies `DOPEMUX_ALLOW_MAIN=1` bypass. | Worktree creation mutates git state. Protection bypass via env var is untested. | Contract test: mock `InstanceManager`; test `DOPEMUX_ALLOW_MAIN=1` skips the check. |
| GAP-H7 | `wire_conport_project.py` subprocess (lines 1914–1922) | Called as a subprocess via `check_call([sys.executable, wire_script])`. Exception is silently caught. No test verifies this call succeeds or fails gracefully. | If script is absent or broken, silent skip could leave ConPort unwired. | Contract test: mock `check_call`; assert called with correct script path. |

### MED

| ID | Branch / Component | Gap | Why it matters | Coverable by |
|---|---|---|---|---|
| GAP-M1 | `--no-recovery` skips recovery menu | The flag is not tested in integration. The basic recovery menu tests use the module directly. | No test verifies `--no-recovery` flag actually skips the ConPort/git query. | Contract test: mock `show_recovery_menu_sync`; assert not called with `--no-recovery`. |
| GAP-M2 | `pal` healthcheck is `exit 0` | PAL service always reports healthy to compose even if broken. DiscoveryGate has no test with PAL as mandatory repo_profile server. | Users believe PAL is healthy when it may be completely non-functional. | Compose configuration change (out of scope for unit tests); document limitation. |
| GAP-M3 | Dangerous mode 1hr expiry check (`_check_dangerous_mode_expiry()`, line 2383) | No test verifies that an expired dangerous mode is cleaned up before activation, or that a still-live mode is reused without re-prompting. | Without expiry test, could fail open (never expires) or fail closed (expires too aggressively). | Contract test: set `DOPEMUX_DANGEROUS_EXPIRES` to past/future timestamp; assert cleanup/skip behavior. |
| GAP-M4 | `ClaudeConfigurator.setup_project_config()` with role (line 2454) | Called only when `--role` is explicitly passed. No test verifies that role-based config is applied to the project `.claude/` directory. | Role-specific system prompts may not be applied. | Contract test: mock `ClaudeConfigurator`; assert `setup_project_config` called with role arg. |
| GAP-M5 | `_persist_instance_env_exports()` (line 2136, 2342) | Writes env vars to `.dopemux/env/instance_<ID>.sh`. No test verifies the file is created, the allowlist is respected, or that routing vars are persisted. | Env file missing breaks shell re-use of instance. | Contract test: use temp dir; assert file created with expected content. |
| GAP-M6 | `dope-context` healthcheck always-pass | `curl ... || exit 0` means the healthcheck is always healthy. Autoindex startup trigger at line 2428 proceeds regardless of actual dope-context state. | Autoindex called against non-running service — silently fails with `request_failed`. | Document limitation; consider changing healthcheck to `exit 1` on failure. |
| GAP-M7 | `DOPEMUX_FORCE_INSTANCE_ID` override (lines 2082–2104) | No test exercises this env var override. | Advanced users use this for scripted multi-instance setups. | Contract test: mock InstanceManager; assert ID and port overridden correctly. |
| GAP-M8 | Context restore path — `--session` flag (line 2365) | `--session` passes a specific session ID to `restore_session()`. No integration test verifies the `--session` path vs the `restore_latest()` path. | Session-specific restore is untested. | Contract test: mock `ContextManager`; assert `restore_session` vs `restore_latest` called based on flag. |
| GAP-M9 | `DOPEMUX_SKIP_MCP_AUTOCONFIG` env var (line 2392) | No test verifies this env var skips `WorktreeAutoConfigurator.configure_workspace()`. | Escape hatch for broken auto-config is untested. | Contract test: set env var; assert `configure_workspace` not called. |

### LOW

| ID | Branch / Component | Gap | Why it matters | Coverable by |
|---|---|---|---|---|
| GAP-L1 | `_start_minimal_session()` fallback (line 1907) | Called when `project_path_real_exists` is False. This path is exercised for deleted/moved project directories. No test covers this path. | Edge case for damaged installations. | Contract test: mock `Path.is_dir` to return False. |
| GAP-L2 | `DOPEMUX_FAST_ONLY = "1"` for non-A instances (line 2129) | Auto-set for B, C... instances. No test verifies. | Could affect MCP behavior for secondary instances. | Contract test: assert env var set for instance_id != "A". |
| GAP-L3 | `AttentionMonitor.start_monitoring()` failure (line 2475) | No exception handler around this call. If it throws, startup crashes after Claude has launched. | Attention monitor is best-effort; should not crash the session. | Contract test: mock to raise; assert graceful degradation. |
| GAP-L4 | `claude_hooks.start_monitoring()` failure (line 2472) | Same as GAP-L3. | Same reasoning. | Same approach. |

---

## 7. Risk Notes

### Security exposures — 0.0.0.0-bound services

OBSERVED from `compose.yml`. The following services publish to all interfaces (no `127.0.0.1:` prefix):

`postgres` (5432), `redis-events` (6379), `redis-primary` (6380), `leantime` (8080), `redis-ui` (8081), `mcp-qdrant` (6333/6334), `conport` (3004/3005/4004), `pal` (3003), `litellm` (4000), `dopecon-bridge` (3016), `task-orchestrator` (8000), `dope-memory` (3020), `serena` (3006/4006), `gptr-mcp` (3009), `exa` (3011)

That is **15 of 23 services** exposed to the network. PostgreSQL, both Redis instances, and LiteLLM (with master-key auth) are network-accessible on any interface the host has. This is consistent with the known finding from the beta-readiness audit (2026-05-29) and the distributed audit (2026-05-29): "5 security exposures (unauth 0.0.0.0 svcs)".

Additionally, **`--alt-routing` explicitly starts litellm subprocess on `0.0.0.0`** (line 1612 in cli.py). This is a separate exposure from the compose service.

### Task-orchestrator stdio/SQLite contention

INFERRED from memory context: the task-orchestrator jar (`v3.8.0`) supports HTTP/SSE transport but the compose file uses stdio (each client spawns a `--rm` container). Under multi-client churn, SQLite contention causes blocked-alive containers. Observed runtime flaw that affects startup reliability when the task-orchestrator MCP is registered. The HTTP-singleton transport fix (`MCP_TRANSPORT=http`) exists but is not yet applied to this compose.yml — **UNKNOWN** whether the current compose.yml has been updated.

### API/secret key requirements

The following keys are required by specific startup branches. They are not validated by existing tests (except `OPENROUTER_API_KEY` in `test_start_command.py`):

| Key | Required for |
|---|---|
| `ANTHROPIC_API_KEY` | Direct Claude launch (subscription mode) |
| `OPENROUTER_API_KEY` | `--litellm` mode (LiteLLMProxyManager) |
| `XAI_API_KEY` | `--grok` |
| `OPENAI_API_KEY` | `--codex`, PAL service, gptr-mcp |
| `DOPEMUX_LITELLM_DB_URL` (Postgres conn) | `--alt-routing` |
| `ALTP_OPUS_KEY`, `ALTP_SONNET_KEY`, `ALTP_HAIKU_KEY` | `--altp` |
| `DOPEMUX_CCR_API_KEY` | `api` routing mode (CCR) |
| `AGE_PASSWORD` | PostgreSQL / ConPort / dopecon-bridge |
| `VOYAGE_API_KEY` | dope-context embeddings |
| `HOST_CODE_PARENT_DIR` + `HOST_PROJECT_RELATIVE_PATH` | dope-context workspace mount |
| `LEANTIME_TOKEN` | task-orchestrator, leantime-bridge |
| `ADHD_ENGINE_API_KEY` | adhd-engine |
| `TASK_ORCHESTRATOR_API_KEY` | task-orchestrator |
| `LITELLM_MASTER_KEY` | litellm service |
| `TAVILY_API_KEY` | gptr-mcp |
| `EXA_API_KEY` | exa service (NOT in .env.example) |
| `OPENAI_WEBHOOK_SECRET` | webhook-receiver (NOT in .env.example) |

### CLI-not-installed reality

No `dopemux` binary is on PATH in this worktree. The `console-script` entry point requires `pip install -e .`. All tests use `CliRunner` (in-process) or direct function imports. This means:

- True end-to-end startup (subprocess: `dopemux start`) is NOT_RUN in any test.
- The `--background` Popen path is tested by mocking Popen but never exercised in a real process.

### Branches hard or impossible to test deterministically

| Branch | Reason |
|---|---|
| Interactive role wizard (`start_wizard()`) | Requires tty; Click's `CliRunner` sets `mix_stderr=False` but does not emulate tty properly for Rich live displays. |
| Worktree creation from multi-instance prompt | Mutates git state; requires interactive confirm. |
| Dangerous mode interactive confirm | Two `click.confirm()` prompts; `CliRunner(input="y\ny\n")` can simulate but the duplicate `_activate_dangerous_mode` definition at 5914 bypasses them anyway (GAP-C1). |
| `--alt-routing` 20s health wait | `time.sleep(1)` loop × 20; tests would need to mock httpx. |
| Full MCP stack startup | Requires Docker + all 23 services running. |
| `save_instance_state_sync` with real ConPort | Requires live ConPort at port 3004. |
| Ctrl+C shutdown flow | Signal-based; hard to test reliably in CliRunner. |

---

## 8. Proposed Test Matrix

The following table maps each branch/component to the recommended test layer and a one-line assertion sketch. Items marked "requires secrets" need real API keys. Items marked "deterministic" can run in CI with no secrets.

| Branch / Component | Recommended Layer | Assertion Sketch | Requires Secrets | Deterministic |
|---|---|---|---|---|
| GAP-C1: `_activate_dangerous_mode` duplicate definition | Contract | Assert `dopemux.cli._activate_dangerous_mode` is identical to the definition at line 3875 (has confirm calls), not the one at 5914. | No | Yes |
| GAP-C2: `save_instance_state_sync` crash after Claude launch | Contract | Mock `save_instance_state_sync` to raise `ConnectionError`; assert `start()` handles gracefully and does not crash. | No | Yes |
| GAP-C3: `--alt-routing` litellm bind address | Contract | Mock `subprocess.Popen`; capture cmd args; assert `"0.0.0.0"` is NOT present (or document intentional exposure). | No | Yes |
| GAP-H1: `api` routing mode health check + repair | Contract | Mock `LaunchdServiceManager.check_health()` → healthy; assert `ANTHROPIC_BASE_URL` set to CCR URL. | No | Yes |
| GAP-H2: `api` repair failure + subscription fallback | Contract | Mock health always-fail + repair always-fail; pass `--routing-fallback-subscription`; assert `ANTHROPIC_BASE_URL` unset. | No | Yes |
| GAP-H3: `--grok` env setup | Contract | Mock `start_simple_proxy` to return `(4000, "sk-test")`; assert env vars set correctly. | No (key check is at CLI entry) | Yes |
| GAP-H4: `--altp` silent no-op in subscription mode | Contract | Mock routing to return "subscription"; pass `--altp`; assert warning logged and no proxy started. | No | Yes |
| GAP-H5: tmux kill-server invocation | Contract | Mock `subprocess.run`; assert called when `TMUX` not set, not called when `TMUX` is set. | No | Yes |
| GAP-H6: `DOPEMUX_ALLOW_MAIN=1` bypass | Contract | Mock `check_and_protect_main`; with env var set, assert it is not called. | No | Yes |
| GAP-H7: wire_conport_project.py call | Contract | Mock `check_call`; assert called with correct script path. | No | Yes |
| GAP-M1: `--no-recovery` skips recovery menu | Contract | Mock `show_recovery_menu_sync`; assert not called with `--no-recovery`. | No | Yes |
| GAP-M3: Dangerous mode expiry check | Contract | Set `DOPEMUX_DANGEROUS_EXPIRES` to past timestamp; assert `_deactivate_dangerous_mode()` called before re-activation. | No | Yes |
| GAP-M4: Role-based `ClaudeConfigurator` | Contract | Mock `ClaudeConfigurator`; pass `--role developer`; assert `setup_project_config(path, role="developer")` called. | No | Yes |
| GAP-M5: `_persist_instance_env_exports()` output | Contract | Use temp dir; run with instance_id=B; assert `.dopemux/env/instance_B.sh` created with expected routing vars. | No | Yes |
| GAP-M7: `DOPEMUX_FORCE_INSTANCE_ID` | Contract | Mock `InstanceManager`; set env var; assert instance_id overridden. | No | Yes |
| GAP-M8: `--session` vs `restore_latest` | Contract | Mock `ContextManager`; assert `restore_session("abc")` vs `restore_latest()` based on flag. | No | Yes |
| GAP-M9: `DOPEMUX_SKIP_MCP_AUTOCONFIG` | Contract | Mock `WorktreeAutoConfigurator`; set env var; assert `configure_workspace` not called. | No | Yes |
| `--alt-routing` full path (DB + health wait) | Both | Contract: mock DB + httpx; Full-stack: real Postgres + real litellm binary. | Secrets for full-stack | Contract: yes |
| `--litellm` + CCR full stack | Full-stack-e2e | LiteLLM + CCR actually start and respond; ANTHROPIC_BASE_URL routes correctly. | `OPENROUTER_API_KEY` | No |
| All 23 compose services start healthy | Full-stack-e2e | `docker compose up -d`; wait for healthchecks; assert all services pass. | All infra secrets | No |
| DiscoveryGate with real Docker stack | Full-stack-e2e | Start compose; run `DiscoveryGate.run()`; assert PASS. | All infra secrets | No |
| GAP-L1: `_start_minimal_session` | Contract | Mock `Path.is_dir` → False; assert `_start_minimal_session` invoked. | No | Yes |
| GAP-L3/L4: `AttentionMonitor`/`claude_hooks` failure | Contract | Mock to raise; assert startup completes without propagating exception. | No | Yes |

---

---

## 9. Stage 1 PAL Validation

**Model**: gpt-5.2 (OpenAI) via PAL codereview  
**Method**: Two-step external validation — strategy + independent expert analysis  
**Status**: COMPLETE — all audit findings confirmed

### Verdict per finding

| ID | Audit Severity | PAL Verdict | Notes |
|---|---|---|---|
| GAP-C1 | CRIT | **CONFIRMED CRIT** | Duplicate def shadowing security guards confirmed. Expert note: assert observable behavior (prompts fired + env vars set after confirms), not line-number identity, to avoid test drift. |
| GAP-C2 | CRIT | **CONFIRMED CRIT** | Unguarded save_instance_state_sync confirmed. PAL also flags `claude_hooks.start_monitoring()` and `AttentionMonitor.start_monitoring()` (lines 2471–2475) as same failure mode — post-launch, unguarded. See NEW-C4 below. |
| GAP-C3 | CRIT | **CONFIRMED CRIT** | 0.0.0.0 bind confirmed. Expert notes fix is trivial (change to 127.0.0.1) and confirms CRIT rating for developer machines on shared networks. |
| GAP-H1 | HIGH | **CONFIRMED HIGH** | api routing mode untested. |
| GAP-H2 | HIGH | **CONFIRMED HIGH** | PAL notes `_ensure_env_consistent_with_mode()` is a partial mitigation (correct call at line 1165) but coverage gap remains real. |
| GAP-H3 | HIGH | **CONFIRMED HIGH** | |
| GAP-H4 | HIGH | **CONFIRMED HIGH** | |
| GAP-H5 | HIGH | **CONFIRMED HIGH** | PAL confirms `pass` + blank line + `logger.error` are all inside the except block (logger.error DOES execute; not truly silent). Still untested. |
| GAP-H6 | HIGH | **CONFIRMED HIGH** | |
| GAP-H7 | HIGH | **CONFIRMED HIGH** | PAL recommends at minimum a `logger.warning` in the except block even if kept best-effort. |

### New issues surfaced by PAL (not in original audit)

| ID | Severity | Finding | Location |
|---|---|---|---|
| NEW-C4 | CRIT | `claude_hooks.start_monitoring()` and `AttentionMonitor.start_monitoring()` called post-launch with no try/except — same failure mode as GAP-C2: crashes after Claude spawns | cli.py:2471–2475 |
| NEW-M1 | MED | Duplicate `_trigger_dope_context_autoindex_startup()` definition elsewhere in file — same shadowing risk as GAP-C1 | cli.py:~2565 and ~3828 |
| NEW-M2 | MED | Duplicate `_deactivate_dangerous_mode()` (lines 3948 and 5928) and `_check_dangerous_mode_expiry()` (line 5944) — second definitions shadow first. Less security-sensitive than GAP-C1 but same root cause. | cli.py:3948, 5928, 5944 |

### Test approach refinements from PAL

- **GAP-C1**: Do not assert `_activate_dangerous_mode is <specific function object>` — line numbers drift. Instead assert **observable behavior**: that `click.confirm` is called twice AND that env vars are only set after both confirmations. Use `CliRunner(input="y\ny\n")` and assert env vars; use `CliRunner(input="n\n")` and assert env vars NOT set.
- **GAP-H2**: Also assert `DOPEMUX_SET_ANTHROPIC_API_KEY` cleanup behavior (line ~991–1004) when fallback to subscription is invoked.
- **GAP-H7**: Even "best effort" call should log a warning on failure — the test should also assert `logger.warning` fires, not just that the exception does not propagate.

### Stage 1 validation summary

- **3 CRIT findings**: all confirmed, none overstated
- **7 HIGH findings**: all confirmed
- **2 new CRIT-grade issues** found by PAL (NEW-C4, same fix pattern as GAP-C2)
- **No findings were downgraded**
- **GAP-C3** slight severity contest (deprecated flag path) — expert and both reviewers agree CRIT is defensible; fix is trivial
- **Test approach**: all proposed tests are sound, deterministic, and require no real services; behavior-based assertions preferred over identity-based for GAP-C1

**Validation confidence**: VERIFIED

---

## Appendix: Known Code Quality Observations

Not gaps per se, but warranting attention:

1. **Duplicate `_activate_dangerous_mode` at lines 3875 and 5914** — the second definition at 5914 wins at runtime and removes all security theater (no confirm dialogs). Either deduplicate or clearly document which definition is intended (GAP-C1).

2. **Duplicate `except (OSError, UnicodeDecodeError) as e:` blocks at lines 1428–1435** — copy-paste artifact in `--alt-routing` master key read. Both branches do the same thing.

3. **Unreachable code at lines 2214–2241** — the `if litellm_proxy_info.already_running` print block is inside a `raise` statement's continuation after `except LiteLLMProxyError`. This code never executes.

4. **`pal` healthcheck `exit 0`** — the PAL compose healthcheck in `compose.yml` is `exit 0`, so Docker always considers PAL healthy regardless of actual service state. `DiscoveryGate` does its own JSON-RPC `tools/list` probe per server (OBSERVED in `gate.py`; it does not rely on compose healthcheck semantics). However, because PAL's provenance in the default resolver is not `repo_profile` mandatory, a non-responsive PAL emits only a WARNING rather than BLOCK. The net effect: users can observe a "startup succeeded" message while PAL is completely non-functional.

5. **`EXA_API_KEY` and `OPENAI_WEBHOOK_SECRET` absent from `.env.example`** — operators deploying from the example will miss these keys, causing silent failures in exa and webhook-receiver.
