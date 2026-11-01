# W05 return — TP-DMX-RUNNERMEM2A-R2-W05-HTTP-CALLERS-001

**Child status:** READY_FOR_AUDIT. **Team lead disposition:** committed as `302675efa` after a diff check; no correction round. The blockers for `enforce` below go to the operator. Audit: NOT_RUN (held for J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W05_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 243 assistant turns (harness record) |
| Duration / tokens / tool uses | 1,265 s / 296,809 / 152 (caps 120 min / 1.5M / 300) |
| Attempts | 1 |
| advisor calls / subagents | 0 / 0 (structural count: Bash 84, Read 15, Write 7, Edit 45, SubagentHandback 1) |
| Keychain, Docker or `dopemux mcp` commands | 0 |
| Process deviations | One debug script written to the session scratchpad with a heredoc, and a scratchpad venv built from the frozen lock. Both are outside the repo and were disclosed. One `cd /dev/null`, a no-op. |

## Write surface

18 paths: 11 callers plus `tests/unit/runner_memory_2a_r2_w05/`. All are inside the W05 write_surface. The only red-lane files are the two ADR-227-exempt `services/dopecon-bridge/` files.

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| `pytest tests/unit/runner_memory_2a_r2_w05/` | 0 | PASS: 63 passed |
| Existing caller suites (`tests/unit/pm`, `tests/unit/dopemux/pm`, instance state, recovery, start, profile, decisions, PM source events, orchestrator memory writers), run with W05's `keychain_guard_plugin` | 0 | PASS: 220 passed |
| pyflakes on the 11 callers, before and after | — | PASS: no new findings (14 before, 13 after; one unused import removed) |
| `git diff --check`, pre-commit (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child) | 1 | recorded: 20 failed, 43 passed (the 43 are behaviour-unchanged checks) |
| dopecon-bridge client test (services venv, child only) | 0 | PASS per child: 65 passed |
| Existing caller suites without the guard | — | NOT_RUN: they would read the real keychain (see open item 1) |

## Per caller

| Caller | Runs on | Principal |
|---|---|---|
| `src/dopemux/pm/adapters/dope_memory.py` | host | internal:cli |
| `src/dopemux/tools/conport_client.py` | host | internal:cli |
| `src/dopemux/instance_state.py` | host | internal:cli |
| `src/dopemux/profile_analytics.py` | host | internal:cli |
| `src/dopemux/commands/decisions_commands.py` | host | internal:cli |
| `src/dopemux/adhd/rte_adapter.py` | host (also copied into images; no container caller found) | internal:adhd |
| `services/adhd_engine/conport_client.py` | container (no importer found) | internal:adhd |
| `services/claude_brain/brain_manager.py` | container (cannot import today; pre-existing) | internal:brain |
| `services/dopecon-bridge/dopecon_bridge/clients.py` | container | internal:dopecon |
| `services/dopecon-bridge/ddg_mcp_stdio.py` | container (cannot import with mcp 1.29; pre-existing) | internal:dopecon |
| `scripts/proof_conport_mcp.py` | host, in-process with mocks; not an HTTP writer | internal:cli (nominal) |

How the callers behave:
- Tokens are fetched on writes only. Without a token, the request goes out exactly as before, and only the principal name is logged.
- Ids come from the caller, the constructor or the envrc env. A caller's value is never replaced, and no id is invented: a missing id gets the server's 400.

## Open items for the operator (before either server goes to `enforce`)

1. **Tests read the real keychain once tokens are issued.**
   - Existing caller tests do not stub `get_token`. Today no items exist, so a read finds nothing and the old behaviour continues.
   - After `dopemux auth issue <principal> --apply` on this Mac, those test runs would read real tokens.
   - Fakes without a `headers` argument would then also fail.
   - Fix: make W05's `keychain_guard_plugin` an autouse guard in `tests/conftest.py`. That file is outside every R2 write surface, so it needs operator scope.
   - This must land before tokens are issued.
2. **Container callers cannot present a token.** The adhd_engine, claude_brain and dopecon-bridge images have no `/usr/bin/security`, so `get_token` raises and the callers stay `unverified`. This is the same gap as W02's proxy fallback (`PROXY_TOKEN_PROVIDER = lambda: None`). Options:
   - a host-side proxy;
   - a token mounted into the container read-only;
   - moving those writes to the host.

   This is an operator decision.
3. **Container ids are unknown.**
   - The compose entries for dopecon-bridge and adhd-engine set no `DOPEMUX_WORKSPACE_ID` or `DOPEMUX_INSTANCE_ID`.
   - The bridge defaults to a hardcoded `/Users/hue/code/dopemux-mvp` (`config.py:70`).
   - Once the new images run, those writes get 400 whatever the auth mode. Fixing it is a compose change.
4. **Bridge progress writes lose `instance_id`.** `ProgressRequest` (`services/dopecon-bridge/.../routes.py:112-122`) has no `instance_id` field. That file is red lane and not exempt.
5. **Other writers still open:**
   - `services/task-orchestrator` (non-goal)
   - `pm/adapters/conport.py`, which works only if `CONPORT_URL` points at the bridge, and sends `workspace_id: "default"`
   - `services/dope-memory/mcp_stdio_adapter.py`, a stale adapter still listed in `config/runtime_authority_manifest.json`
   - the bridge's `update_context` PATCH, which ConPort answers with 405
   - W02's proxy fallback
6. **Host callers need the envrc env loaded** (for example through direnv). Without it `instance_id` is omitted and the server returns 400.
7. **Deploy order.** The new images reject writes without ids, so the images must not run before this change.
8. **No token caching.** Each write spawns `security`, with a 10 s timeout if the keychain is locked.
9. **Helper code is repeated in each caller** because the write surface had no shared module. `dopemux.auth.bearer_headers(principal)` would remove the copies; that is a later cleanup.
