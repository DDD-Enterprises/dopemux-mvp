END_OF_SUBJECT 8b72d8c3-efb06f7c

Static audit of embedded subject at declared pin `efb06f7c5a0677d5a6103cbcb86e02d199c133ba` (base `46155cad9`, branch-authored range only). Route has no shell, no test files, no `design.md`/`plan.md` body, and no live host. Controller logs and prior verdicts are claims, not evidence. Required static checks below were read off `subject-src.diff`, the how-to, `COMMITS.txt`, and the reap/lifecycle/proxy/json sources in that diff.

**Closures**
- Codex at `30b0fdec9` F1 and F2 stay closed. `reap.py` `_reap_one` skips `state_error` and does not `rmtree` or count `reaped` unless both registry saves return clean. `lifecycle.py` `run_lifecycle(..., hold_instance_lock=True)` takes one instance lock around worktree start/restart; `launcher.py` `ensure_backend` / `ensure_orchestrator` pass `False` while they already hold instance or reserved locks. No second `launch.lock` in one stack; reserved and instance are not nested (`locks.py` order holds; inode re-check still in `_flock`).
- Codex at `3f1335e7f` F1 and F2 stay closed. `mcp_json.py` masks every `${...}` on the whole string, strips only a leading literal scheme, and fail-closes if the scheme/`//` is itself a placeholder. `stdio_proxy.py` `_session_terminated` is code `32600` and message `== "Session terminated"` only. `forward()` resends that case at most once (`MAX_SENDS_PER_REQUEST`). Any other `McpError`, including a `32600` whose text merely contains the phrase, is returned. `CONNECTION_CLOSED` is not resent. `ClosedResourceError`/`BrokenResourceError` still retry once under the “not written” comment; that does not reopen the substring bug. `_url_is_repairable` does not replace an operator URL unless it is a literal local URL with no userinfo, or exactly `_SELF_RENDERED` (literal `http(s)://localhost|127.0.0.1`, one catalog/dopemux port variable, numeric or absent default, literal remainder). Generic `${PORT:-3005}`, userinfo/host placeholders, scheme-relative templates, and credential URLs are preserved.
- Codex at `43294e99b` F1 is closed by that same predicate (item 13). Env values are not read.
- Codex at `fc591cba1` F1 and F2 are closed by item 15. `PORT_*` doctor blockers are carried. `_resolved_port_findings` blocks two selected services on one resolved port and a sidecar on a reserved singleton port, including leases `_resolve_ports` kept without allocating. `DOCKER_CONTAINER_*` is dropped only when docker is readable, evidence names a container, that container is not one of this run’s expected names, and it publishes none of the resolved ports; otherwise the finding stays (no evidence, docker down, expected name, or on-map → fail closed). A same-project no-hash / wrong-workspace container on a resolved port therefore still blocks via the kept doctor finding. `_collision_checks` still requires `project_id` plus a differing `dopemux.worktree_hash` (missing scope treated as `worktree`) and still sends other projects through `PORT_OWNED_BY_OTHER_PROJECT`. This does not start a service on a port another project holds, and it does not drop a main start/restart blocker except the stated stale-envrc container that is off the resolved map and not our expected name. That difference is intentional; I would not raise it.
- Item 16 is absent. `maybe_reap` returns when `not registry.instances()` before `plan_reap`. No `_any_marked_runtime_dir`. It cannot sweep a live worktree’s marker or run an extra unbounded pre-scan. `_dir_only_candidates` remains plan-time only, `worktree_missing` only, and skips a live `build-*.pid`.
- Item 17 record matches the code. How-to cleanup text says automatic reap sees an `instance.json` dir only while the registry lists an instance, and no run sees it while that file is missing or unreadable. `plan_reap` returns `[]` unless `parse_status == "OK"`. `mcp reap` help says nothing is planned while the registry file is missing. The open follow-up (build-only marker dirs never reach automatic reap on an empty, missing, or unreadable registry; explicit reap also plans nothing until the file exists and parses OK) is truthful there. I would not raise it. `design.md` wording was not in this embed (`NOT_RUN`).
- Item 18 does not reopen those closures. `status` with `allocate=False` is display-only. Not forwarding runner cancellation does not take the session-terminated resend path.
- Cycle-2 items 2–9 hold in this tree (SessionEnd `"timeout": 60` only; target-catalog `--repo` on init, lifecycle CLI, switch-project, repair-config; dead-attach idle age is read-only in planning; marker is identity fields, mode `0600`, under the instance lock; AGENTS.md §12.3 states the shared image key). Item 1’s test parametrization is not in this embed (`NOT_RUN`). Item 10’s design bullets are `NOT_RUN`; the how-to does document `state_error` and `instance.json`.

**Review focus.** Secrets: SCRAM verifier, psql stdin, gate URL via `0600` `--env-file`, redact-before-truncate, `instance.json` has no env. No password on stdout in the paths read. Locks, reconnect guard (before every connect, including the first, and after every `initialize`), and reap label/scope/idle/deadline/kill-switch/`state_error` rules match the claims. Ambient `DOPEMUX_*` / port / `CONPORT_DB_*` scrub holds unless `--trust-env`; `launch` has no such flag. Deferred ledger items: I would not raise any.

**Acceptance T1–T11:** `NOT_RUN` here. The owner log at `30b0fdec9` is not this SHA and was not re-executed.

No new defect. Residuals below are pre-stated; they keep this at `PASS_WITH_RISKS`, not `PASS`. `plan.md:17` is the repo’s plan-executor header, not an instruction to this auditor, and its body was not embedded; not recorded as instruction-like.

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "efb06f7c5a0677d5a6103cbcb86e02d199c133ba",
    "observed_head": "",
    "head_match": true,
    "base": "46155cad92702beba8169448f1fefe5cef45294c (merge-tree of 5742575c4 and f16e0da2c)",
    "file_hashes": {}
  },
  "auditor": {
    "runner": "grok",
    "model_requested": "grok-4.7",
    "model_observed": "UNKNOWN",
    "effort": "UNKNOWN",
    "independent_of_implementer": true
  },
  "checks": [
    {"id": "C-DIFF", "command_or_method": "Read embedded subject-src.diff (src, hooks, settings, catalog, schemas, pyproject) plus COMMITS.txt; tests and design.md/plan.md not in this route", "exit_code": null, "bucket": "PASS", "evidence": "Cycle-6 tree matches items 1-15 and 17; item 16 symbols absent; maybe_reap returns before plan_reap when instances() is empty"},
    {"id": "C-SECRETS", "command_or_method": "Static review of conport_tenant.py, launcher.py _lifecycle_error/_write_instance_marker, adopt_with_gate, redacted_tail", "exit_code": null, "bucket": "PASS", "evidence": "Password repr=False; CREATE ROLE gets SCRAM verifier; SQL on stdin; gate URL in 0600 env-file not argv; tails redacted before cut; instance.json is project_id, worktree_hash, worktree_root, project_root, written_at at 0600"},
    {"id": "C-LOCKS", "command_or_method": "Static review of locks.py, launcher.py launch/ensure_*, lifecycle.py run_lifecycle split, mcp_commands.py switch-project", "exit_code": null, "bucket": "PASS", "evidence": "Order instance|reserved outside registry; instance outside provision; reserved and instance never nested; flock re-checks st_dev/st_ino; launcher passes hold_instance_lock=False; CLI default True for worktree start/restart/stop"},
    {"id": "C-RECONNECT", "command_or_method": "Static review of stdio_proxy.py _session_terminated/forward/_guarded_session and launcher.py reconnect_guard", "exit_code": null, "bucket": "PASS", "evidence": "Guard before connect and after initialize on every session including the first; resend only on exact 32600 Session terminated, once; other 32600 returned"},
    {"id": "C-REAP", "command_or_method": "Static review of reap.py plan_reap/_reap_one/maybe_reap and native_hooks budgets", "exit_code": null, "bucket": "PASS", "evidence": "Label+scope+registry join; idle uses dead attach mtimes without planning writes; state_error/registry_busy keep the runtime dir; live build excludes all kinds; orchestrator not marked stopped; automatic path does not reach marker-only dirs when the registry lists no instance"},
    {"id": "C-DOCS", "command_or_method": "Compare howto-mcp-setup-other-repos.md cleanup, sidecar-restart, and image sections to reap.py, stdio_proxy.py, launcher.py, cli.py", "exit_code": null, "bucket": "PASS", "evidence": "How-to automatic-reap/marker/missing-registry paragraph matches reverted maybe_reap and plan_reap non-OK short-circuit; SessionEnd timeout 60 and reap budgets match native_hooks.py and LAUNCH_REAP_LIMITS; state_error documented"},
    {"id": "C-CYCLE2-15-17", "command_or_method": "Trace items 2-9, 11-15, 17 at the embedded sources; item 16 absence", "exit_code": null, "bucket": "PASS", "evidence": "Prior codex F1/F2 at 30b0fdec9, 3f1335e7f, and fc591cba1, and F1 at 43294e99b, remain closed in this tree; Task H code is not present"},
    {"id": "C-ITEM1-TEST", "command_or_method": "tests/unit/test_docs_no_envrc_recipe.py parametrization", "exit_code": null, "bucket": "NOT_RUN", "evidence": "Test file not in this route's embed; cannot confirm .claude/claude.md vs CLAUDE.md"},
    {"id": "C-DESIGN-BULLET", "command_or_method": "claudedocs/mcp-just-works-design-2026-11-05.md Task H revert bullet", "exit_code": null, "bucket": "NOT_RUN", "evidence": "design.md body not embedded; how-to and mcp reap help text were checked instead"},
    {"id": "C-TESTS-LINT-HASH", "command_or_method": "make test-fast, mypy/ruff, FILES.sha256 recompute, git rev-parse", "exit_code": null, "bucket": "NOT_RUN", "evidence": "No shell on this route; VALIDATIONS.md numbers are controller claims"},
    {"id": "C-LIVE-T1-T11", "command_or_method": "Owner acceptance T1-T11 and cold launch smoke at efb06f7c", "exit_code": null, "bucket": "NOT_RUN", "evidence": "Not required for this static audit; recorded owner run is at 30b0fdec9, not this SHA"}
  ],
  "findings": [],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "make test-fast 4509 passed at efb06f7c",
    "hooks workflow 12 passed, docs validators rc=0, ruff/flake8/mypy/black deltas",
    "Codex connector clean receipt on efb06f7c5",
    "FILES.sha256 (not recomputed)",
    "design.md revert bullet text at fbbe95a59/efb06f7c5",
    "acceptance T1-T11 at 30b0fdec9 and live smoke at 3f1335e7f",
    "installed MCP SDK still contains the literal Session terminated"
  ],
  "remaining_risks": [
    "A dopemux port variable whose runtime value is not a port (for example 3005@remote.example) can move the host when the client expands a repaired template; repair judges the template, not the value",
    "One resend still happens if a backend returns exactly 32600 and Session terminated after processing the request",
    "ClosedResourceError/BrokenResourceError in forward() is retried once on the next session",
    "_live_build treats a build pid older than the build budget as stale",
    "Automatic reap does not clean launcher-marked runtime dirs while the registry lists no instance or the registry file is missing or unreadable; explicit reap also plans nothing until that file exists and parses OK (owner-accepted follow-up)",
    "dopemux mcp status uses _resolve_ports(allocate=False) and can show stale envrc ports after a re-lease (item 18, code unchanged since cycle 2)",
    "Runner cancellation of an in-flight tool call is not forwarded to the backend (item 18)",
    "Legacy mcp up/down/logs without --repo still use the shell environment",
    "Gate temp env file can remain if the process is killed before adopt_with_gate's finally",
    "doctor --repo and profile doctor/show still load the caller catalog (deferred)"
  ],
  "unknowns": [
    "model_observed and effort: no runtime receipt",
    "git HEAD was not observed; pin is the embedded bundle's declared SHA",
    "design.md amendment wording",
    "item 1 test source",
    "whether every DOCKER_CONTAINER_* doctor finding puts the container name in evidence[0] (item 15 relies on that contract)",
    "live T1-T11 and cold launch at this SHA"
  ],
  "skip_reason": null,
  "unblock": [],
  "acceptance": "NOT_GRANTED"
}
```