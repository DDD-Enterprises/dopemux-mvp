END_OF_SUBJECT a202f49c-30b0fdec

Static review of the embedded branch range `5742575c4..30b0fdec996fcd782bf2f816900f9ff4dabd4c01` (src, hooks, `.mcp.json`, catalog, how-to, ledger). No shell, so git HEAD, `FILES.sha256`, and `make test-fast` were not recomputed. Delegation is unavailable on this route.

Review focus: secrets stay off argv and out of logs (SQL on psql stdin, `CREATE ROLE` gets a SCRAM-SHA-256 verifier, gate `DATABASE_URL` goes through a 0600 `--env-file`, tails are redacted before the cut, tenant creds are compose `extra` only). Lock order is instance/reserved outside registry, `provision_lock` inside the instance lock; `_flock` re-checks `(st_dev, st_ino)` at `src/dopemux/mcp/locks.py:126-131`. Attach and full stop hold `instance_lock`. The proxy guards every session, including the first, before connect and again after `initialize`; `32600` + `Session terminated` resends once; backoff is 0.25 s doubling to 2 s for 10 s; a second drop inside 60 s ends the proxy. Reap joins on managed + `scope=worktree` + registry entry, idle requires `last_detach`, eligibility is re-checked under the instance lock, automatic locks do not block, the kill switch gates `maybe_reap` only, and `task-orchestrator` is outside `_owned_by`. Launcher and lifecycle start paths scrub `AMBIENT_SCRUB_VARS` and resolve identity from git unless `--trust-env`. The how-to matches those behaviors (launcher shape, refusal codes, reap table, SCRAM, unknown-history fail-closed, guard checkpoints, shared image tag).

Ledgered deferred items stay deferred; none of them is a new defect on this read. No medium or higher finding.

Unblock: owner live T1–T11, including `reap --apply` on the probe fixture and removal of `reap.disabled`. Optional: recompute `FILES.sha256` and re-run `make test-fast` at `30b0fdec996fcd782bf2f816900f9ff4dabd4c01`.

```json
{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "observed_head": "",
    "head_match": false,
    "base": "5742575c4",
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
      "command_or_method": "Read embedded subject-src.diff (src, hooks, settings, .mcp.json, catalog, schemas) for 5742575c4..30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "D1 launcher entries in .mcp.json and mcp-proxy-config.copilot.yaml; D2 launch/stdio_proxy; D3 git-only identity unless --trust-env; D4 shared dopemux-<svc>:<key> and build-<svc>.pid; D6 hook cwd dispatch and payload cwd; D9/D10 launch, reap, switch-project, init --repo."
    },
    {
      "id": "C-SECRETS",
      "command_or_method": "Static review of conport_tenant.py, launcher._lifecycle_error/_known_secrets, docker_runtime.run_cmd input_text, lifecycle up_env vs mcp.env/plan",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "psql_command argv is docker exec -i psql only; SQL is input_text. scram_sha256_verifier is what CREATE ROLE sends; plaintext stays in secrets.env mode 0600. adopt_with_gate writes DATABASE_URL to a 0600 temp file and passes --env-file. _redacted_tail redacts secrets and URL passwords before the length cut. Tenant CONPORT_DB_* are extra= on the compose up environment after scrub_ambient, and are absent from the start identity map used for artifacts. Init prints the source word."
    },
    {
      "id": "C-LOCKS",
      "command_or_method": "Static review of locks.py, launcher.launch/ensure_*, lifecycle stop and _to_start_gate, switch-project, reap._reap_one",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Documented order holds: instance_lock and reserved_port_lock outside registry_lock; provision_lock inside the instance lock and not around registry_lock. reserved_port_lock is re-entrant per thread. _flock at locks.py:126-131 retries unless the fd inode matches the path. launch() writes the attach record under instance_lock and drops it before ensure_* and maybe_reap. mcp stop holds instance_lock across stop, lease release, and rmtree. Automatic reap uses blocking=False and skips LockBusy."
    },
    {
      "id": "C-RECONNECT",
      "command_or_method": "Static review of stdio_proxy._BackendLink (_guarded_session, _session_once, _reconnect, forward) and launcher.reconnect_guard",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Every session, including the first, runs the guard before connect and again after initialize, before the session is published or on_started runs. ProxyRefused and any other guard error fail closed. 32600 and message containing 'Session terminated' drop the session and resend that request once (MAX_SENDS_PER_REQUEST=2); CONNECTION_CLOSED in flight is not replayed. Backoff 0.25s doubling, cap 2s, budget 10s. A second drop inside RECONNECT_WINDOW_S=60 ends the proxy. A free port passes; a foreign owner raises."
    },
    {
      "id": "C-REAP",
      "command_or_method": "Static review of reap.py plan_reap/apply_reap/maybe_reap and native_hooks._best_effort_reap",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Candidates need dopemux.managed, scope=worktree, a safe worktree hash, and one registry worktree root. Idle requires last_detach age >= 1200s; a missing file is never idle. _reap_one re-checks live attachments and _still_eligible under the instance lock. Deadlines cap docker calls at min(cmd_timeout, time left). maybe_reap returns None when reap.disabled or DOPEMUX_MCP_REAP is 0/off/false; CLI --apply still runs. State-only candidates clear empty-service rows; _owned_by never selects task-orchestrator. Hook failures are swallowed. Launcher limits are 1 candidate, stop 2s, cmd 3s, deadline 8s; SessionEnd passes throttle 0, 1 candidate, deadline 45s, stop 3s, cmd 10s."
    },
    {
      "id": "C-DOCS",
      "command_or_method": "Compare docs/02-how-to/mcp-setup-other-repos.md (embedded) to launcher, reap, stdio_proxy, conport_tenant, mcp_commands, .mcp.json",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Launcher JSON shape, git-only identity, --trust-env command list (launch has no flag), shared image tag and force-rebuild recipe, refusal table, switch-project lock story, reap budget table, kill switch, SCRAM and CONPORT_TENANT_UNKNOWN_HISTORY, two guard checkpoints, resend-once versus in-flight no-retry, and 60s reconnect window match the code. settings.json gains timeout 60 on one hook entry; the event name is outside the hunk (see unknowns)."
    },
    {
      "id": "C-TESTS",
      "command_or_method": "make test-fast and tests/unit/test_mcp_*.py",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Tests are outside this route's embedded diff and this auditor has no shell. VALIDATIONS.md claims 4229 passed at the pin; that claim was not reproduced."
    },
    {
      "id": "C-HASHES",
      "command_or_method": "Recompute FILES.sha256 and git rev-parse HEAD",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No file access. observed_head is empty and head_match is false. The audit subject is the embedded diff labeled with the pin."
    },
    {
      "id": "C-LINT",
      "command_or_method": "ruff/flake8/black/mypy/docs validators cited in VALIDATIONS.md",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Controller/implementer logs were not re-executed."
    },
    {
      "id": "C-T1-T11",
      "command_or_method": "Owner live acceptance T1–T11 (cold launch, switch-project, tenant gate, reap --apply, EnterWorktree, legacy envrc)",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No host, docker, or Claude session. Ledger live notes are earlier SHAs and are not this auditor's evidence. Design T1–T11 are owner-run and are not required checks for this route."
    }
  ],
  "findings": [],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "make test-fast: 4229 passed, 2 skipped, exit 0 at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "hooks workflow 12 passed; docs validators rc=0; ruff/flake8/black/isort/mypy gates PASS",
    "FILES.sha256 manifest",
    "Live launcher, tenant provision, and reap --dry-run results (recorded at earlier SHAs)",
    "Prior audit-fix verification notes in LEDGER_SUMMARY.md"
  ],
  "remaining_risks": [
    "A second backend drop inside one 60s proxy lifetime window exits 1 and needs /mcp reconnect (documented M1 limit).",
    "SIGKILL before detach leaves no last_detach; idle reap waits for a later prune or worktree_missing (documented).",
    "Legacy dopemux mcp up|down|logs without --repo still uses the shell environment (documented transitional path).",
    "plan_reap seen_pairs treats any managed container with that project_id and worktree_hash as present, including non-worktree scope, so state-only lease cleanup waits while such a container exists.",
    "adopt_with_gate's 0600 DATABASE_URL temp file remains if the process is killed before finally.",
    "Known flaky test_sequential_single_service_allocations_never_share_a_port (~1/30) per VALIDATIONS.md."
  ],
  "unknowns": [
    "git HEAD and FILES.sha256 were not recomputed (head_match false).",
    "Which settings.json hook event received timeout 60 is above the diff hunk; the how-to attributes it to SessionEnd.",
    "plan.md and design.md were not embedded. LEDGER_SUMMARY cuts off at a prior return's instruction_like citation (plan.md:17); that span was not re-read.",
    "Owner live T1–T11, including reap --apply, EnterWorktree, and legacy-envrc adoption.",
    "Whether task-orchestrator containers carry dopemux.worktree_hash (label writer not in the changed hunks), which decides how often the seen_pairs residual matters."
  ],
  "skip_reason": null,
  "unblock": [
    "Owner runs live T1–T11 at 30b0fdec996fcd782bf2f816900f9ff4dabd4c01, including reap --apply on the leftover tenant-probe fixture, then removes ~/.dopemux/mcp/runtime/reap.disabled.",
    "Recompute FILES.sha256 and re-run make test-fast at the pin if the packet must show auditor-observed hashes and the unit gate."
  ],
  "acceptance": "NOT_GRANTED"
}
```