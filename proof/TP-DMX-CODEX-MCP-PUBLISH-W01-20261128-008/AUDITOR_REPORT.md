I've finished reading and I'm writing the verdict now.

# Audit verdict: PASS_WITH_RISKS (five low findings, none medium or higher)

The 006 F1 defect is corrected in the 007 helper. `build()` now passes `dr.env_with_compose_interpolation(product=R, scrub_ambient=True)` at `W03/run_runtime.py:158`. That supplies the required `HOST_CODE_PARENT_DIR` and `DOPECON_BRIDGE_TOKEN`; `HOME`, the other required variable, comes from the parent environment. This does not overturn the 006 FAIL, which applies to its own subject.

This verdict covers source, tests and plan only. It grants no live acceptance, PR readiness or risk acceptance.

## Checks I ran
All eight approved commands exited 0.

| Check | Result |
|---|---|
| Subject checker | HEAD, staged and saved diff, 23 file hashes, plan, 6 helpers and packet/binding hashes match; no unstaged tracked changes |
| `git diff --cached --check` | Clean |
| `ct validate-macro` | `STATIC_VALID`, authority `NONE` |
| `verify_contract.py` | 10 callbacks changed to async only; tool metadata identical |
| Working-memory tests | 77 passed |
| Runner write and auth tests | 118 passed |
| Runtime config tests | 3 passed |
| Build environment test | 1 passed |

I read the complete `source.diff`, the plan, all five W03 helpers and the packets and bindings. `verify_contract.py` rewrites `W01/verify_contract.json` as a side effect; the subject checker still passed afterwards. I edited no source, wrote no report files and ran nothing live.

## Findings
- **F2 (low, carried):** MCP calls now run synchronous backend work on the event loop, so a slow call stalls every request, including `/health`.
- **F3 (low, carried):** a build cache miss can resolve new dependency versions. The plan now says so, but nothing enforces or records the versions.
- **F4 (low, carried):** `start` does not check that the data mounts and anonymous volume survived container recreation.
- **F5 (low, carried):** probe gating, database attribution and disable-on-failure are manual steps.
- **F6 (low, newly recorded; also present in 006):** the build timeout is 1200s, below the canonical 1800s. A timeout would leave memory stopped, with the build receipt blocking a replay.

## Before and during rollout
- **Before the first write probe:** do the plan's manual checks (subject checker, functional, enable, mount and version receipts, zero canonical rows).
- **After `start`:** compare mounts and the volume ID with `RUNTIME_PREFLIGHT.json`.
- **After each client write:** run the exact SQLite attribution query.
- **If the build fails or times out:** do not replay. Memory may be stopped, so return to the operator.

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007",
    "repo": "dopemux-mvp",
    "pinned_sha": "041934957233427fb9b94dfbcd6dc798f069401d",
    "observed_head": "041934957233427fb9b94dfbcd6dc798f069401d",
    "head_match": true,
    "base": "041934957233427fb9b94dfbcd6dc798f069401d",
    "file_hashes": {
      ".claude/hooks/mcp_health_probe.py": "7fbed37d0d2684392cfa3bd859ff99654fb446cfe0d025dcc45b67319cc068bc",
      "services/working-memory-assistant/mcp_http.py": "93b8bfdb31b05b2eaddd5c76bbfd10d07f0417f848fbfa4e63fbf093d2b7bce8",
      "services/working-memory-assistant/tests/test_mcp_sqlite_thread_affinity.py": "8b72b3296dae1070f9d2b1a9437bdccb2d37efa6671d4f9393cdfaeeb5cd5b97",
      "src/dopemux/commands/mcp_commands.py": "8801c7cc59135638195a5c9723cdce175520ca6f0fa3e1a12037cd8abfbd8daa",
      "src/dopemux/mcp/bridge_runtime.py": "ec5dada224a13d03711446be2b11693a5f253d8a733063bb30998bcb1d5c1efa",
      "src/dopemux/mcp/conport_tenant.py": "512436b1bf47e45b4f2c44047fe783882d9832652173aced838f54c946cad86e",
      "src/dopemux/mcp/docker_runtime.py": "82e0693774ae455303bb7de2814eedbe2ad3829d7f4d538854460bc419b8a225",
      "src/dopemux/mcp/doctor.py": "7a6a5c3c3ae7049878b1a80d7e0f3116a2c199c41a13de9c382aaa9e2f83bb21",
      "src/dopemux/mcp/http_stdio_bridge.py": "f5d03903308bc92f0ccbfe3e0b75527efdd4b262db0238552629184645fa41f1",
      "src/dopemux/mcp/idle_retention.py": "f1c7e4ea3189c304629c668a494644e0f4ee4cc926a169931c599415df2e57d5",
      "src/dopemux/mcp/launcher.py": "bd137c60534ccaf7bf1545dd2ce1bedf39f1fc61f73372b5e1076376fd82deb6",
      "src/dopemux/mcp/lifecycle.py": "127835d32a67a979977b7b653322175d872a7cc916773f87fcd354b51ec8326a",
      "src/dopemux/mcp/reap.py": "e3da563d3cb1fe951ad333cb7eaea28a0103f1bad2ffbd07c9dc6c2b361facdd",
      "src/dopemux/mcp/stdio_proxy.py": "2e358b017b144de153441c81f434dbe0722061510e9028d29b2f62f91b662849",
      "tests/test_mcp_health_probe.py": "d6292675667697b5b716daa97a9c1a79bcbcdf3b971212e2414c970d1ebe50b9",
      "tests/unit/runner_memory_2a_r2_w04/conftest.py": "2fbc3ae3f06a5b9e2ff78a3119463f98da06ce0d4e784744f503808827cd577f",
      "tests/unit/test_conport_existing_tenant.py": "ad2d6c86e4fed0b259738f2cff3999684aa4603913e4bd35ddbf318ed47abc65",
      "tests/unit/test_mcp_bridge_runtime.py": "83e26b5ba1d673a842a85b99eaa23708d5161b9542ebdd73c032755580f0cde7",
      "tests/unit/test_mcp_commands_lifecycle.py": "324b2ce73b100bb4ae5831e69d7a3e2f63589f5cfdf7f43a5704897422c2eeed",
      "tests/unit/test_mcp_idle_retention.py": "e1f4918a8776c63c89e65bb50df894154ed9ad51024927a2698c00fa8e74f2c0",
      "tests/unit/test_mcp_lifecycle.py": "b19f82d48b5a10ade969db7133c950e9728f320db1e406dde7de9025e03de349",
      "tests/unit/test_mcp_runtime_launcher.py": "df6c9c69f7c4e1656d54005fda1382820447041d536cde847d5a6067d21d2d4a",
      "tests/unit/test_mcp_stdio_proxy.py": "340868e3f11b749dcb6569fe9ea9efcc50d7295305e2843e3cd396a17ef6d34f"
    },
    "staged_diff_sha256": "310dbea891f69f10f0ad47cbf73ac7bd5cd25006567fb73abe3375482b97a538",
    "plan_sha256": "c54384c23fe00a04b204fc897256816abe97035ca181a2f54597ae09c2e748e2"
  },
  "auditor": {
    "runner": "claude-code-cli",
    "model_requested": "sonnet",
    "model_observed": "UNKNOWN",
    "effort": "high",
    "independent_of_implementer": true
  },
  "checks": [
    {"id": "C1", "command_or_method": "rtk proxy .venv/bin/python proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W02/audit_subject_check.py", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor, repeated during review with the same result. status PASS, saved_diff_match and working_index_match true. Checker and freeze manifest read: also asserts plan, 6 helpers, packet/binding hashes and no unstaged tracked changes."},
    {"id": "C2", "command_or_method": "rtk proxy git diff --cached --check", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. No output."},
    {"id": "C3", "command_or_method": "rtk proxy .control-tower/bin/ct validate-macro --file task-packets/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/MACRO_PACKET.json", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. STATIC_VALID, authority NONE, errors empty."},
    {"id": "C4", "command_or_method": "rtk proxy .venv/bin/python proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W01/verify_contract.py", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. AST differs from HEAD only in 10 callbacks becoming async; full tools/list metadata identical."},
    {"id": "C5", "command_or_method": "rtk proxy .venv/bin/python -m pytest services/working-memory-assistant/tests/test_mcp_sqlite_thread_affinity.py services/working-memory-assistant/tests/test_mcp_http_endpoint.py services/working-memory-assistant/tests/unit services/working-memory-assistant/tests/test_store_fail_closed.py services/working-memory-assistant/tests/test_migration_runner_optimized.py --no-cov -q --tb=short", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. 77 passed."},
    {"id": "C6", "command_or_method": "rtk proxy .venv/bin/python -m pytest tests/unit/runner_memory_2a_r2_w01/test_mcp_writes.py tests/unit/runner_memory_2a_r2_w01/test_rest_writes.py tests/unit/runner_memory_2a_r2_w01/test_auth_identity.py --no-cov -q --tb=short", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. 118 passed."},
    {"id": "C7", "command_or_method": "rtk proxy .venv/bin/python -m pytest proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W03/test_runtime_config.py --no-cov -q --tb=short", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. 3 passed."},
    {"id": "C8", "command_or_method": "rtk proxy env MEMORY_ROLLOUT_TEST_SUBJECT=proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W03/run_runtime.py .venv/bin/python -m pytest proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W03/test_runtime_build_environment.py --no-cov -q --tb=short", "exit_code": 0, "bucket": "PASS", "evidence": "Executed by this auditor. 1 passed. Docker and process calls are mocked; the real interpolation helper is exercised."},
    {"id": "R1", "command_or_method": "Static verification of the 006 F1 correction", "exit_code": null, "bucket": "PASS", "evidence": "run_runtime.py:158 passes the canonical env, matching lifecycle.py:2766 and 2886. compose.yml requires HOST_CODE_PARENT_DIR (423), DOPECON_BRIDGE_TOKEN (489) and HOME (645). Compared with the 006 run_runtime.py by reading: differences are proof path, rollback alias, backup and temp prefixes, and the env argument. By reading, the new test would fail with env omitted; it was not run against the 006 helper."},
    {"id": "R2", "command_or_method": "Static read of the complete source.diff", "exit_code": null, "bucket": "PASS", "evidence": "No new medium or higher source defect found. The 21 earlier source/test hashes match those in the 005 auditor report."},
    {"id": "R3", "command_or_method": "Static review of adapter and thread-affinity regression test", "exit_code": null, "bucket": "PASS", "evidence": "Async callbacks keep backend SQLite access on the event-loop thread; check_same_thread, auth and payload contracts unchanged. Tests use a real SQLite file, production REST routes and lifespan, and in-process MCP HTTP transport."},
    {"id": "R4", "command_or_method": "Static review of rollout plan and the five W03 helpers", "exit_code": null, "bucket": "PASS", "evidence": "No medium or higher defect found. Gates, once-only receipts, build-only command, config compare-then-replace and probe no-replay behavior reviewed. Low gaps are F3 to F6."},
    {"id": "R5", "command_or_method": "Live rollout, helper live modes, client RPC, database attribution", "exit_code": null, "bucket": "NOT_RUN", "evidence": "Prohibited in this audit; not a required check for the source/plan verdict. Held until after it."}
  ],
  "findings": [
    {"id": "F2", "severity": "LOW", "location": "services/working-memory-assistant/mcp_http.py:140", "summary": "Synchronous backend work reached through MCP blocks the whole ASGI loop.", "evidence": "All 10 callbacks are now async around synchronous calls. A SQLite lock wait or the synchronous ADHD state hint in recap would stall other requests, including /health. Plan step 2 discloses the blocking. Carried from 006; severity unchanged."},
    {"id": "F3", "severity": "LOW", "location": "services/working-memory-assistant/Dockerfile.dope-memory:39", "summary": "Resolved dependency versions are not pinned on a build cache miss.", "evidence": "pip install .[services] follows COPY of src and tools; apt-get upgrade is at line 23. Plan step 5 discloses this and asks to record deployed versions, but no helper records or enforces them. Cache state not observed. Carried; disclosure improved."},
    {"id": "F4", "severity": "LOW", "location": "proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W03/run_runtime.py:134", "summary": "start does not verify data mounts or anonymous volume identity after recreation.", "evidence": "It checks running state, eventbus, auth mode and image only. The volume ID is asserted in backup modes (lines 100-101). The mount check is manual. Carried."},
    {"id": "F5", "severity": "LOW", "location": "proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W03/run_client_check.py:18", "summary": "Write probes, database attribution and disable-on-failure are not mechanically gated.", "evidence": "The probe checks only the audit gate file, not the frozen subject or functional and enable receipts. Readback is a substring check (line 59). Attribution and disabling have no frozen helper. App-server stderr is written under the proof tree (mode 0600). The plan's 007 paragraph makes these manual steps. Carried."},
    {"id": "F6", "severity": "LOW", "location": "proof/MACRO-DMX-CODEX-MCP-COMPOSE-20261128-007/W03/run_runtime.py:158", "summary": "The one-shot build uses a 1200s timeout, shorter than the canonical default, with no replay path.", "evidence": "docker_runtime.py:43 defaults DEFAULT_BUILD_TIMEOUT_SECS to 1800. On TimeoutExpired, private_log raises, build.json stays PREPARED_ONCE, a replay is refused and memory remains stopped. Plan step 9 discloses that a build failure may leave memory stopped. Also present in 006 but not recorded there. Static only; build duration unknown."}
  ],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "The two deployed memory_search thread-affinity failures (not re-observed)",
    "Regression tests failing against the old synchronous callbacks",
    "RUNTIME_PREFLIGHT container, image, mount, mode, attachment and fingerprint observations",
    "Applicable hooks, the explicit 23-path changed-contract check and the config and AST equality runs by the root",
    "That check_functional.py, run_client_check.py and test_runtime_config.py differ from their 006 copies only mechanically (007 versions were reviewed; 006 copies of these were not compared)",
    "The 005 audit's 1210 tests"
  ],
  "remaining_risks": [
    "F2 to F6 are open and not accepted",
    "005 low findings R005-L1 to L6 and older F2-F5 and A3/A4 remain open and unaccepted; they were not re-adjudicated",
    "New tests use in-process ASGI transport, not a real server socket",
    "Cancellation is tested only after a confirmed write, not during a transaction",
    "Populated recap and reflection generation paths have no new coverage",
    "Production lifespan does not close cached stores",
    "enable() compare-then-replace is not atomic against a non-cooperating writer",
    "Checkpoint-to-socket TOCTOU and dependence on the retained worktree and venv remain",
    "The subject checker and freeze manifest are not themselves hash-pinned by the checker",
    "ROLLOUT_PLAN.md step 7 or 8 wording still says 'in006' for the no-ConPort-write rule (cosmetic)"
  ],
  "unknowns": [
    "Provider-attested model identity",
    "Whether the live environment still matches the preflight at effect time",
    "Build cache state, build duration and resolved dependency versions in the rebuilt image",
    "Whether the already-open GUI session adopts the memory entry"
  ],
  "skip_reason": null,
  "unblock": [],
  "acceptance": "NOT_GRANTED"
}
```
