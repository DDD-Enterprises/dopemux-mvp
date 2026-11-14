END_OF_SUBJECT 3cb30c90-2479969f

Scope: static L3 re-audit of embedded materials for MACRO-DMX-MCP-JUST-WORKS-M1-001 at declared pin `2479969fec2ec401a9cfe3eed51570829e67b723` (base `337a226b25de353c32820e8f86fb674afbd6c25b`). Read `subject-src.diff` (final src/config/hooks vs that base), `delta-since-c6.diff`, the how-to, `mcp-command-registry.txt`, `COMMITS.txt`, `VALIDATIONS.md`, `LEDGER_SUMMARY.md`. No shell, no hash recompute, no pytest, no live Docker. Test files and `product_root()` body are absent from this packet. `plan.md:17` is a pre-existing plan-executor template, not an instruction to this auditor (operator ruling 2026-11-12); left out of `instruction_like_content`.

Checks: secrets/argv/logs, lock order, reconnect/resend, reap, how-to vs code, items 1–15 and 17–20. Live T1–T11 and `make test-fast` are NOT_RUN here (controller’s suite FAIL is a host `:7890` claim, not reproduced).

Closures (verified on the embedded final code):
- 30b0fdec9 F1 closed by item 6: `reap.py` `_reap_one` skips `state_error` and returns before `shutil.rmtree`; `reaped` is recorded only after both saves.
- 30b0fdec9 F2 closed by item 7: `run_lifecycle(..., hold_instance_lock=True)` holds `instance_lock` for the worktree half of non-dry start/restart, one acquisition across restart stop+start. `ensure_backend` / `ensure_orchestrator` pass `False` while they already hold the non-reentrant lock. Reserved `:7890` stays outside that lock.
- 3f1335e7f F1 closed by item 11 and still closed after item 13: `_placeholder_in_userinfo_or_host` masks `${...}` over the whole URL, then strips only a leading literal scheme. No leading scheme ⇒ any placeholder is not repairable.
- 3f1335e7f F2 closed by item 12: `_session_terminated` is code `32600` and message `== "Session terminated"`. Other 32600 text is returned, not resent. `forward()` resends that exact case once (`MAX_SENDS_PER_REQUEST`).
- 43294e99b F1 closed by item 13: a template is repairable only when `_self_rendered_template` matches literal `http(s)://localhost|127.0.0.1`, one catalog/dopemux port variable, numeric or absent default, literal remainder. Generic `${PORT:-3005}`, host/userinfo/scheme placeholders, remote hosts, and credential URLs are preserved. Env values are not read.
- fc591cba1 F1 closed by item 15: `PORT_*` doctor codes are not deferred; `_resolved_port_findings` blocks duplicate resolved ports and a sidecar on a reserved port, including leases `_resolve_ports` kept.
- fc591cba1 F2 closed by item 15: `_split_deferred_doctor` keeps a `DOCKER_CONTAINER_*` finding when docker is unread, evidence is empty, the container name is expected, or it publishes a resolved port. A same-project no-hash container on a resolved port stays a doctor blocker. `_collision_checks` still requires a hash for the sibling-worktree rule; that rule is defence in depth, not the backstop.
- Items 6–7, 11–15 still hold on this tree. Item 16 is absent: no `_any_marked_runtime_dir`; `maybe_reap` returns when `registry.instances()` is empty. Item 17’s design bullet and the how-to sentence (marker dirs visible to automatic reap only while the registry lists an instance; no run while the file is missing or unreadable) match that code. Item 18 does not reopen those closures. Item 20’s bullet matches `_mutable_facts` (`allocate=op in {"start","restart"}`, no dry-run input) and `_resolve_ports` (`persist=True`, `dry_run=False`, lease save). `lifecycle.py` is not in `delta-since-c6.diff`.

Cycle 7: conflict resolutions keep M1 text. §12.6 matches `mcp-command-registry.txt` (`switch-project` implemented; `reconcile` only under `leases` / `registry` / `control-plane`; `adopt`/`migrate` absent). Container count text is 2N; serena is one dopemux-mvp container. `product_root()` and the how-to “Restoring Postgres” / `--no-deps` sentences are not in the embedded source, so they stay UNKNOWN, not findings. Delta src hunks in `mcp_commands.py`, `doctor.py`, and `fleet_catalog.py` are upstream merge content. Branch-authored cycle-7 text beyond the doc resolutions is the design follow-up bullet.

Findings: none at medium or above.

Item 20, if it were in scope, would be medium: `--dry-run` help says plan-only and no registry writes, while start/restart dry-run still releases and persists leases. It stays an owner-accepted follow-up (test-locked since `40ea89c24`), not a finding. Other pre-stated residuals (port-var expansion, exact-32600 resend, `ClosedResourceError`/`BrokenResourceError` continue in `forward()`, age-bounded `_live_build`, items 17–18, legacy `up|down|logs`, gate temp env file on SIGKILL, doctor `--repo` catalog) would not be re-raised.

Unblock: none on this packet. Acceptance stays NOT_GRANTED. Follow-ups 17, 18, and 20 stay outside the packet.

{
  "schema": "independent-audit/v1",
  "status": "PASS_WITH_RISKS",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "2479969fec2ec401a9cfe3eed51570829e67b723",
    "observed_head": "",
    "head_match": true,
    "base": "337a226b25de353c32820e8f86fb674afbd6c25b (merge-tree of 5742575c4 and 264c97b23ec1b3e007e62079d4f6d2632ad71775)",
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
      "command_or_method": "static read of embedded subject-src.diff and delta-since-c6.diff",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Final src/config/hooks diff and cycle-7 delta read. Test diffs and full design body are not in this packet."
    },
    {
      "id": "C-SECRETS",
      "command_or_method": "static review of conport_tenant.py, launcher.py, lifecycle.py, reap.py instance.json",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "SQL on psql stdin; gate URL via 0600 docker exec --env-file; SCRAM verifier in CREATE ROLE; redacted_tail before error tails; mcp.env/start-plan omit the tenant password; instance.json is identity fields plus written_at, mode 0600."
    },
    {
      "id": "C-LOCKS",
      "command_or_method": "static review of locks.py, lifecycle.py hold_instance_lock, launcher.py, switch-project",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Order is instance or reserved outside registry; those two are not nested. _flock re-checks st_dev/st_ino. launch.lock is taken once per hold. Launcher passes hold_instance_lock=False under its own instance lock."
    },
    {
      "id": "C-RECONNECT",
      "command_or_method": "static review of stdio_proxy.py forward/_session_terminated and launcher.reconnect_guard",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Guard runs before every connect and after initialize, first session included. Resend is exact 32600 'Session terminated' once. Other messages return. Backoff 0.25s doubling, cap 2s, wait 10s, window 60s."
    },
    {
      "id": "C-REAP",
      "command_or_method": "static review of reap.py plan_reap/_reap_one/maybe_reap",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Label join plus registry entry; idle uses dead attach mtimes without planning writes; state_error/registry_busy keep the runtime dir; live build excludes candidates; maybe_reap returns when the registry lists no instance. Task H helper is absent."
    },
    {
      "id": "C-DOCS",
      "command_or_method": "how-to and AGENTS.md §12.6 versus embedded code and mcp-command-registry.txt",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Launcher shape, git-only identity, refusal exit 3, shared image tag, reap budgets, state_error, marker/registry wording, and the §12.6 verb table match the code and registry. product_root() alias and Restoring Postgres were not in the embedded source."
    },
    {
      "id": "C-CYCLE2",
      "command_or_method": "items 1-10 on embedded code and delta",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Items 2-9 verified in cli.py, mcp_json.py, mcp_commands.py, reap.py, lifecycle.py, launcher.py, AGENTS.md delta. Item 1 test file and item 10 full design body are not embedded."
    },
    {
      "id": "C-CYCLE3-5",
      "command_or_method": "items 11-15 and revert item 17 on embedded code",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "URL predicate, exact session literal, doctor deferral plus resolved-port validation, and the Task H revert all match the claims. Earlier closures still hold."
    },
    {
      "id": "C-CYCLE7",
      "command_or_method": "delta-since-c6.diff versus registry and M1 modules",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Docs resolutions keep M1 text and match the registry. lifecycle/launcher/reap/stdio_proxy/mcp_json are absent from the cycle-7 delta. Design bullet 20 matches _resolve_ports persist path."
    },
    {
      "id": "C-TESTS",
      "command_or_method": "make test-fast and unit diffs",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No shell. Controller VALIDATIONS claims exit 1 (1 failed, 4517 passed) as a host :7890 flake. Test sources were not embedded."
    },
    {
      "id": "C-HASHES",
      "command_or_method": "recompute FILES.sha256",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No file access. Controller hash list not treated as proof."
    },
    {
      "id": "C-LIVE",
      "command_or_method": "acceptance T1-T11 and cold launch at this SHA",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Owner-run items. VALIDATIONS marks them NOT_RUN at this SHA."
    }
  ],
  "findings": [],
  "instruction_like_content": [],
  "author_claims_not_reproduced": [
    "make test-fast exit 1 at 2479969fec2ec401a9cfe3eed51570829e67b723 (host :7890 claim)",
    "tests/unit/test_docs_no_envrc_recipe.py parametrizes .claude/claude.md (file not embedded)",
    "tests/unit/test_mcp_doctor_repo_aware.py has 36 test functions (only the added test is in the delta)",
    "product_root() honors DOPEMUX_MVP_ROOT and DOPEMUX_PRODUCT_ROOT (function body not in the diff)",
    "how-to Restoring Postgres service/volume and sidecar --no-deps (compose source not embedded)",
    "SDK 1.29 drift-guard test for the Session terminated literal (test file not embedded)",
    "FILES.sha256 and live T1-T11 at this SHA"
  ],
  "remaining_risks": [
    "A dopemux port variable expanded to a non-port value can move the host; repair judges the template only (pre-stated).",
    "A backend that returns exactly 32600 and 'Session terminated' after processing still gets one resend (pre-stated).",
    "forward() continues on ClosedResourceError/BrokenResourceError and can send the request again (pre-stated).",
    "_live_build treats a build pid older than the build budget as finished (pre-stated).",
    "Automatic reap does not see launcher-marked dirs while the runtime registry lists no instance, and plan_reap plans nothing while that file is missing or unreadable (item 17, documented).",
    "dopemux mcp status uses _resolve_ports(allocate=False) and can report stale envrc ports (item 18).",
    "Runner cancellation of an in-flight proxied call is not forwarded (item 18).",
    "start --dry-run and restart --dry-run persist and can release port leases (item 20). Out of packet; would be medium in a follow-up because the CLI help says no registry writes.",
    "Legacy dopemux mcp up|down|logs without --repo still uses the shell environment (documented).",
    "Gate temp env file remains if the process is killed before adopt_with_gate's finally (pre-stated).",
    "doctor --repo and profile --repo still load the caller catalog (ledger-deferred)."
  ],
  "unknowns": [
    "Live git HEAD was not observed; pin is the embedded packet.",
    "model_observed and effort have no runtime receipt.",
    "product_root() alias and Restoring Postgres were not checked against source.",
    "Item 1 test parametrization and the 36-function doctor count were not counted.",
    "embedded_audit.schema.json grok-cli/grok-4.7 enum is upstream #1507 and not in the subject diff.",
    "Controller lint/mypy/CCAR results were not re-run."
  ],
  "skip_reason": null,
  "unblock": [],
  "acceptance": "NOT_GRANTED"
}