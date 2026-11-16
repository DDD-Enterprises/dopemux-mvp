END_OF_SUBJECT a16ed92f-3f1335e7

Independent L3 re-audit of the embedded pin `3f1335e7fdcf8165d4669195bfd521cafca13304` (base `46155cad92702beba8169448f1fefe5cef45294c`). No shell, no network, no hash recompute. Subject read: `subject-src.diff` (src, hooks, settings, catalog, `.mcp.json`), `howto-mcp-setup-other-repos.md`, `COMMITS.txt`, `FILES.sha256` (not recomputed), `VALIDATIONS.md` and `LEDGER_SUMMARY.md` as claims only. Tests, `design.md`, and the proof tree are not in this route.

Codex F1 at `30b0fdec9` is closed. Codex F2 at `30b0fdec9` is closed for reapable worktree services.

Cycle-2 items: (1) test path `.claude/claude.md` — NOT_RUN (test diff withheld). (2) Closed: `src/dopemux/cli.py` `native_hooks_register` sets SessionEnd `"timeout": 60` on new hooks and heals an existing matching command that lacks `timeout`; other events unchanged. `.claude/settings.json` adds one `"timeout": 60` (hunk at line 109). (3) Closed: `src/dopemux/mcp/mcp_json.py:114` `_placeholder_in_userinfo_or_host` plus `_url_is_repairable` — a `${...}` in userinfo or host is never repairable, whatever the default; other placeholders are neutralized before the host/userinfo check; remote hosts and userinfo are preserved. (4) Closed: `init`, `_run_lifecycle_cli` (catalog and `run_lifecycle(repo=target_root)`), `switch-project`, and `repair-config` load the target checkout via `_load_catalog` / `_git_toplevel`. `doctor --repo` still calls bare `_load_catalog()`; that gap is already deferred — not re-raised. (5) Closed: `reap.py` `_effective_last_detach` is read-only; `plan_reap` uses `live_attachments(..., prune=False)`; pruning and `last_detach` stamping happen only in `live_attachments(prune=True)` under the instance lock. (6) F1 closed: `_reap_one` on registry/lease save errors `skip(..., "state_error")` and returns before `shutil.rmtree` and before `report.reaped`. Same for `registry_busy`. (7) F2 closed: `run_lifecycle(..., hold_instance_lock=True)` holds `instance_lock` for worktree-scoped start and for one acquisition across that restart’s worktree stop+start. Orchestrator-only selection does not take `launch.lock` (`worktree_part` empty), so `switch-project`’s reserved `:7890` lock is not nested with it. `launcher.py` `ensure_backend` and `ensure_orchestrator` pass `hold_instance_lock=False`. (8) Closed: `launcher.py` `_write_instance_marker` writes `instance.json` (project_id, worktree_hash, worktree_root, project_root, written_at, mode 0600) under the instance lock; `reap.py` `_dir_only_candidates` is `worktree_missing` only, and `_live_build` excludes every candidate kind in `plan_reap` and `_still_eligible`. (9) Closed on the worktree `AGENTS.md` text in this message (§12.3 shared image per service and Dockerfile version). The AGENTS.md hunk is not in `subject-src.diff`. (10) How-to reap section matches `state_error`, `registry_busy`, dead-attach idle, and `instance.json`. `design.md` amendments NOT_RUN (file not in this route).

Review focus: secrets stay off argv (psql stdin, gate URL only in a 0600 `--env-file`, SCRAM verifier in `CREATE ROLE`, `_redacted_tail` before truncate, `instance.json` identity-only, tenant password not in `mcp.env` / plan). Lock order holds: inode re-check in `locks.py` `_flock`; instance outside registry and outside `provision_lock`; reserved and instance are not nested; `launch.lock` is not taken twice in one hold (launcher releases it before `ensure_*` and before `maybe_reap`). Reconnect: 32600 plus `Session terminated` resends once (`MAX_SENDS_PER_REQUEST`); guard runs before every connect and after every `initialize`, first session included. Reap: label join includes `dopemux.scope=worktree`, orchestrator not marked stopped, deadlines and kill switch as documented. Ambient scrub is `AMBIENT_SCRUB_VARS` unless `--trust-env`; `launch` has no `--trust-env`.

No medium or higher defect verified in the embedded code. Deferred ledger items not re-raised.

Unblock (owner, not code): live T2, T3, T5, T6b, and T8 `--apply` at this SHA; Copilot/Codex review of `3f1335e7` was not in the materials.

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "3f1335e7fdcf8165d4669195bfd521cafca13304",
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
    {
      "id": "C-DIFF",
      "command_or_method": "Read embedded subject-src.diff in full (src, config, hooks, settings, .mcp.json). Tests and other docs withheld by this route.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Launcher .mcp.json shape, lifecycle, locks, reap, proxy, tenant, and CLI --repo paths are in the diff. D1–D8 code claims match that text."
    },
    {
      "id": "C-SECRETS",
      "command_or_method": "Static review of argv, stdin, logs, mcp.env, start plan, findings, instance.json",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py: psql SQL on stdin; adopt_with_gate writes DATABASE_URL to a 0600 temp file and passes docker exec --env-file; CREATE ROLE uses scram_sha256_verifier; redacted_tail runs before truncation. launcher.py _write_instance_marker writes only INSTANCE_MARKER_FIELDS plus written_at. Tenant password is not copied into the mcp.env identity block."
    },
    {
      "id": "C-LOCKS",
      "command_or_method": "Static lock-order review of locks.py, launcher.py, lifecycle.py, reap.py, switch-project",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "locks.py _flock re-checks (st_dev, st_ino) after LOCK_EX. instance_lock is outside registry_lock and provision_lock. reserved_port_lock and instance_lock are not nested. Launcher holds launch.lock only for attach plus instance.json, then releases before maybe_reap and ensure_*. ensure_* passes hold_instance_lock=False. switch-project holds reserved :7890 around an orchestrator-only run_lifecycle, which does not take launch.lock."
    },
    {
      "id": "C-RECONNECT",
      "command_or_method": "Static review of stdio_proxy.py session restart and launcher reconnect_guard",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "32600 and 'Session terminated' drop the session and resend that request once. In-flight CONNECTION_CLOSED is not retried. _guarded_session runs the guard before connect; _session_once runs it again after initialize before the session is handed out, including the first session. Backoff 0.25s doubling to 2s for up to 10s. Second drop inside RECONNECT_WINDOW_S=60 ends the proxy."
    },
    {
      "id": "C-REAP",
      "command_or_method": "Static review of reap.py plan_reap, _reap_one, maybe_reap versus the how-to",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Join requires dopemux.managed, dopemux.scope=worktree, project id, and worktree hash plus a registry entry. Idle uses dead attach mtimes without planning writes. state_error and registry_busy keep the runtime dir and are not reaped. Live build-<service>.pid excludes every candidate kind. Dir-only marker candidates are worktree_missing only. Automatic paths use non-blocking instance locks, bounded docker calls, and the kill switch. Task-orchestrator is not marked stopped by reap."
    },
    {
      "id": "C-DOCS",
      "command_or_method": "How-to mcp-setup-other-repos.md compared with the embedded code",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Launcher shape, refusal codes, shared image tag, switch-project, reap budgets, state_error, instance.json, SIGKILL idle rule, SCRAM, unknown-history fail-closed, env-file informational rule, and reconnect guard wording match the code. Legacy up/down/logs without --repo are documented as still using the shell environment."
    },
    {
      "id": "C-CYCLE2",
      "command_or_method": "Verify cycle-2 items 2–10 against subject-src.diff, how-to, and injected worktree AGENTS.md",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Items 2–8 closed in code. Item 9: stale per-worktree image sentence is absent from the worktree AGENTS.md §12.3 text in this message. Item 10 how-to half closed. Item 1 (test param) and design.md amendments are separate NOT_RUN checks."
    },
    {
      "id": "C-CYCLE2-TESTS-DESIGN",
      "command_or_method": "tests/unit/test_docs_no_envrc_recipe.py and claudedocs design amendments",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "This route withheld tests and design.md. Cannot confirm the .claude/claude.md parameter or append-only design amendments from the embedded text."
    },
    {
      "id": "C-HASHES-TESTS-LINT",
      "command_or_method": "Recompute FILES.sha256; re-run make test-fast, hooks pytest, ruff, flake8, mypy",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No shell on this route. VALIDATIONS.md numbers are author claims, not this audit's evidence."
    },
    {
      "id": "C-ACCEPTANCE-LIVE",
      "command_or_method": "Design §6 T1–T11 and live launch/reap at 3f1335e7",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Owner-run live checks are outside this static route. Prior acceptance at 30b0fdec9 was not re-executed here."
    }
  ],
  "findings": [],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "VALIDATIONS.md make test-fast 4434 passed at this SHA",
    "VALIDATIONS.md hooks workflow 12 passed, ruff/flake8/mypy/black touched-line gates",
    "VALIDATIONS.md live smoke: cold launch exit 0, instance.json mode 0600, reap dry-run worktree_missing",
    "Acceptance at 30b0fdec9: PASS 7, PARTIAL 1, NOT_RUN 4",
    "FILES.sha256 (not recomputed)",
    "PR bot re-review found no remaining defect on the frozen head"
  ],
  "remaining_risks": [
    "A second backend drop inside the 60s reconnect window ends the proxy (exit 1); the first failed connect also consumes that window.",
    "SIGKILL leaves a dead attach record; idle is measured from that mtime, which is not refreshed while the process lived.",
    "Legacy dopemux mcp up|down|logs without --repo still uses the shell environment.",
    "adopt_with_gate's 0600 env file remains if the process is killed before finally.",
    "Image key is product path plus Dockerfile bytes; sidecar source edits need docker image rm.",
    "maybe_reap returns before plan_reap when the runtime registry lists no instances, so marker-only dirs wait for an explicit reap or a non-empty registry (how-to states this).",
    "doctor --repo and profile doctor/show still use the caller catalog (ledger-deferred)."
  ],
  "unknowns": [
    "Live git HEAD was not read; audit subject is the embedded bundle labeled 3f1335e7.",
    "model_observed and effort have no runtime receipt.",
    "T1–T11 and bot review of the final head were not run here.",
    "Whether _start_services skips compose up after a failed _prebuild_images result was not isolated as its own hunk; a failed up still fail-closes the service if that short-circuit is absent.",
    "PortLeaseRegistry.identity_matches body is not in subject-src.diff (port_leases.py not in FILES.sha256); reap calls it."
  ],
  "skip_reason": null,
  "unblock": [
    "No code defect verified that blocks this static pass.",
    "Owner still runs live T2, T3, T5, T6b, and T8 --apply at this SHA.",
    "Owner may request Copilot and Codex review of 3f1335e7; that review was not in the materials."
  ],
  "acceptance": "NOT_GRANTED"
}
```