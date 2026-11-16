END_OF_PROMPT a202f49c-30b0fdec

**Change Summary:** **FAIL — two medium findings.** Audited the supplied branch-authored materials for `5742575c4..30b0fdec996fcd782bf2f816900f9ff4dabd4c01`. No changes made.

**Authority Used:** Your audit contract and the independent-audit skill. Subject instructions were treated as data. No delegation.

**Analysis Performed:** Read the complete 19,517-line diff and supplied supporting documents; traced credentials, locks, reconnects, cleanup, environment scrubbing, and documented commands.

1. **F1 — Medium: reap finalizes after registry-save failure.**  
   `src/dopemux/mcp/reap.py:668` records persistence errors without signaling failure to its caller. At `:736`, `_reap_one` handles only `LockBusy`; other save failures still reach runtime-directory deletion at `:750` and `report.reaped.append` at `:756`. An in-memory probe of these exact functions confirmed both actions after an injected save error. This removes recovery artifacts despite incomplete finalization. For an existing worktree, state-only recovery is excluded at `:468`.

2. **F2 — Medium: direct lifecycle operations bypass cleanup serialization.**  
   `src/dopemux/mcp/lifecycle.py:1333` locks the explicit stop path, but restart proceeds directly to `_stop_services` at `:1336`; direct starts likewise lack the launcher’s instance-lock wrapper (`src/dopemux/mcp/launcher.py:480`). Consequently, the new automatic reaper can overlap a direct start/restart on an eligible idle instance, removing its containers, leases, or runtime files during that operation. This is a static concurrency finding; the interleaving was not exercised live.

**Validation Performed:** **PASS** — all 20 added files reconstructed from the diff matched the manifest; three supplied standalone documents matched their manifest hashes; all 16 added Python files parsed. **FAIL** — reap finalization probe and lifecycle lock-coverage review. **NOT_RUN** — repository tests, lint/type/doc validators, and every live acceptance item.

**Remaining Uncertainty / Risk:** No deferred item is promoted to a new finding. Retain the ledger’s migration/checkpoint crash window, unlocked init allocation, corrupt-registry recovery, inherited Git environment, proxy capability limitations, and timing risks. Controller results remain claims, including earlier-head live checks.

**Files Touched:** None.  
**Git State:** Materials directory has no Git repository; no staging or commits.  
**Rollback Plan:** None required for this audit.  
**Requested Next Step:** Preserve runtime state on persistence failure; serialize direct lifecycle mutations with reap without nesting the non-reentrant instance lock. Add focused failure/concurrency coverage, then provide a newly pinned subject for re-audit. Owner-run acceptance remains outstanding.

```json
{
  "schema": "independent-audit/v1",
  "status": "FAIL",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "30b0fdec996fcd782bf2f816900f9ff4dabd4c01",
    "observed_head": null,
    "head_match": null,
    "base": "5742575c4",
    "file_hashes": {
      "subject.diff": "a0770548598397dd47690b7a5279f11a6c0b163a51fe121d215e703674e52a0c",
      "subject-src.diff": "59b1e272ed180db990b29a54fe4daf4058bd46a52efd2e13ae41ab996c41643a",
      "FILES.sha256": "c09dee96c00aef56836a3e9b08c2cc3b69f1741beeadbe02c3a04dea43a648f3",
      "COMMITS.txt": "112687da030273446a1dbccb20ee6156057919f8d513c93df4711bf363e7c4fa",
      "design.md": "2b2691fbaa781fbcdd8dccf8eea8fc4ea7611260bd034ed92b923a34f754e4a3",
      "plan.md": "4cc68c6d7bb2c5f2c849e9af5f02b8eeae76bd18f636e6c824c83e1e031ed8a6",
      "howto-mcp-setup-other-repos.md": "547e8032727b7c4b48dda2a8ea396386dd3ec4bef519dff00871a737e0200826",
      "LEDGER_SUMMARY.md": "e31da4b99b087d34b01380122eafbc3a2ce4429a0602b616e4b648b07afcdbb4",
      "VALIDATIONS.md": "e5843d6a3cba08dda4ed666a49c3ee8b43eb97d8d5108b20f2a6ccc5cdebc062"
    }
  },
  "auditor": {
    "runner": "codex",
    "model_requested": "gpt-6-astra",
    "model_observed": "UNKNOWN",
    "effort": "UNKNOWN",
    "independent_of_implementer": true
  },
  "checks": [
    {
      "id": "MATERIAL_INTEGRITY",
      "command_or_method": "Python hashlib; reconstruct added files from unified diff; compare source-diff blocks and standalone documents",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "20/20 added files match FILES.sha256. Standalone design, plan and how-to match. subject-src.diff blocks match subject.diff. Manifest has 67 entries; 46 modified-file hashes could not be independently recomputed from the supplied partial-file hunks."
    },
    {
      "id": "FULL_DIFF_READ",
      "command_or_method": "Read every subject.diff range and all supplied supporting documents",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "19,517 lines, 68 diff blocks, and 21 COMMITS.txt entries. Truncated tool-output ranges were reread."
    },
    {
      "id": "ADDED_PYTHON_SYNTAX",
      "command_or_method": "ast.parse on all added Python files reconstructed in memory",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "16 files parsed. This verifies syntax only."
    },
    {
      "id": "SECRETS_ARGV_LOG_REVIEW",
      "command_or_method": "Trace D5 storage, SQL input, gate environment delivery, compose artifacts and error redaction",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:208 creates private atomic files; :354/:368 deliver SQL on stdin; :403 constructs the SCRAM verifier; :436 redacts before truncation; :748 delivers the gate URL through a temporary env file. launcher.py:320 redacts lifecycle error tails. Reviewed lifecycle mcp.env/start-plan handling and corresponding tenant tests. PASS is limited to static review; actual PostgreSQL, Docker and process logs were not inspected."
    },
    {
      "id": "LOCK_ORDER_AND_COVERAGE",
      "command_or_method": "Trace instance, reserved-port, provision and registry lock acquisition and mutation boundaries",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "The reviewed nested order and locks.py:94 inode recheck are present. Launcher attach/start and explicit stop are protected. Direct lifecycle start/restart do not participate in the same instance-lock protocol; F2."
    },
    {
      "id": "RECONNECT_GUARD_REVIEW",
      "command_or_method": "Trace initial connection, initialization, reconnect, resend and refusal paths",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:343 guards every connection; :349 checks again after initialize before publishing the session. :459 bounds forwarding to two attempts and handles Session terminated separately from uncertain in-flight failure. :298/:377 implement the reconnect window and backoff. launcher.py:631 binds ownership checks. Corresponding tests were read, not run. This does not prove an atomic ownership guarantee across separate Docker and network observations."
    },
    {
      "id": "REAP_SAFETY_REVIEW",
      "command_or_method": "Trace label joins, exclusions, eligibility, deadlines, kill switches and state finalization",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "Scope exclusions, under-lock eligibility recheck, bounded automatic lock waits, kill-switch precedence and orchestrator exclusion are present. Persistence errors still permit runtime deletion and a reaped result; F1. Direct lifecycle concurrency remains F2."
    },
    {
      "id": "REAP_PERSISTENCE_FAILURE_PROBE",
      "command_or_method": "Execute AST-extracted _release_state and _reap_one in memory with fake lock, Docker, persistence and rmtree collaborators",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "Injected registry-save error produced errors=['test/abcd: injected registry save failure'], rmtree_called=true, candidate_reported_reaped=true. No filesystem or Docker mutations occurred. Exit 0 means the diagnostic completed, not that the invariant passed."
    },
    {
      "id": "AMBIENT_ENV_REVIEW",
      "command_or_method": "Trace default identity inputs and credential/port scrubbing through launcher, CLI and compose",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "launcher.py:274, mcp_commands.py:133 and docker_runtime.py:77 scrub the designated ambient identity/port/credential variables on the reviewed managed paths; identity defaults to git unless trust-env is explicitly used. Inherited GIT_DIR/GIT_WORK_TREE and legacy cwd-compose behavior remain listed limitations."
    },
    {
      "id": "DOCS_VS_CODE_REVIEW",
      "command_or_method": "Compare complete how-to with changed commands, renderer, tenant, proxy and reap code",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed command/flag/code mappings, envrc adoption, shared-image key, automatic-reap limits and explicit apply behavior. Codex, Copilot and mid-session worktree limitations are disclosed. No additional documentation finding is raised beyond the supplied deferred items and the implementation defects reported here. Runtime timing and client-display statements were not reproduced."
    },
    {
      "id": "DEFERRED_ITEM_DISPOSITION",
      "command_or_method": "Compare candidate findings with LEDGER_SUMMARY.md Deferred items and subsequent rulings",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "No listed deferred item is promoted to a new finding. F1 concerns non-LockBusy persistence failure after removal; F2 concerns the new reaper's interaction with direct lifecycle operations, distinct from the listed init allocator race."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_1",
      "command_or_method": "Map subdirectory-root acceptance to source and tests",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Static coverage: launcher.py:171; test_resolve_launch_root_from_subdirectory and test_resolve_target_repo_uses_git_toplevel_from_subdir. Tests not executed."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_2",
      "command_or_method": "Map symlink identity acceptance to source and tests",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Static coverage: resolved-path identity flow and test_identity_stable_across_symlinked_path. Test not executed."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_3",
      "command_or_method": "Map non-git/unmanaged refusal acceptance to source and tests",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Static coverage: launcher.py:151/:171 and refusal-without-Docker tests. Managed status is checked by entry shape, as explicitly ruled in the ledger."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_4",
      "command_or_method": "Map corrupt-registry handling to source and tests",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Static coverage: reap.plan_reap and test_plan_reap_with_corrupt_registry_is_empty; locks tests cover recovery. Silent destructive recovery remains a listed deferred risk. Tests not executed."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_5",
      "command_or_method": "Map missing-cwd/non-JSON hook handling to source and tests",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Static coverage: native_hooks.py:695 and dispatcher/main tests for missing cwd, malformed input and exit-code propagation. Tests not executed."
    },
    {
      "id": "REPOSITORY_VALIDATIONS",
      "command_or_method": "make test-fast; hooks tests; docs validators; lint, format and type checks",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Supplied directory contains audit materials, not an executable repository checkout. User explicitly excluded suite execution. VALIDATIONS.md was read only as author claims."
    },
    {
      "id": "T1",
      "command_or_method": "Fresh git worktree session in clean and polluted shells",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live runner/Docker execution. Static launcher, identity and lease tests cover constituent paths."
    },
    {
      "id": "T2",
      "command_or_method": "Claude-created worktree session",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Root-probe document is author evidence only; no runner measurement reproduced."
    },
    {
      "id": "T3",
      "command_or_method": "Concurrent Codex session",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Explicitly excluded by the supplied implementation amendment; per-worktree Codex rendering is absent from M1."
    },
    {
      "id": "T4",
      "command_or_method": "Fresh project init, tenant provisioning and connection",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Tenant code and mocked tests read; no database, filesystem-mode or live connection acceptance performed."
    },
    {
      "id": "T5",
      "command_or_method": "Legacy handmade tenant adoption with preserved data",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Legacy envrc/secrets resolution and tests read; actual tenant contents and database count not observed."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal, switch-project and old-session refusal",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Owner verdict, switch-project and first/reconnect guard tests read. No live ownership transition performed."
    },
    {
      "id": "T6b",
      "command_or_method": "Concurrent launchers with port 7890 initially free",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Reserved-port lock and under-lock start recheck inspected; real concurrent jar starts not exercised."
    },
    {
      "id": "T7",
      "command_or_method": "All hooks and DCP hard-deny in a worktree",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Dispatcher, payload-cwd and exit propagation tests read. Live hook routing and DCP enforcement not exercised."
    },
    {
      "id": "T8",
      "command_or_method": "Removed-worktree cleanup preserving main",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Reap tests and source reviewed; no live apply. F1 and F2 must be resolved before relying on cleanup acceptance."
    },
    {
      "id": "T9",
      "command_or_method": "init --force --repo worktree leaves main unchanged",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Target-selection and preservation tests read; no files generated or compared in a real checkout."
    },
    {
      "id": "T10",
      "command_or_method": "Missing-image detached build and exit within five seconds",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "launcher.py:413 uses detached Popen and typed refusal; shared image-key and build tests read. Elapsed-time and reconnect acceptance not measured."
    },
    {
      "id": "T11",
      "command_or_method": "Two launchers within 100 ms produce one start",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Instance-lock recheck and test_two_launchers_one_start read. Mock probe becomes ready immediately; real simultaneous cold-start behavior not measured."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "medium",
      "location": "src/dopemux/mcp/reap.py:736",
      "summary": "Registry persistence failure does not prevent runtime deletion or a reaped result.",
      "evidence": "_release_state appends save error strings at :668 and returns normally. _reap_one catches only LockBusy, then calls rmtree at :750 and appends the candidate to reaped at :756. The in-memory extracted-function probe independently reproduced both actions after a save error. locks.py:303 and :351 confirm real persistence failures use this error-return channel. Existing-worktree state-only recovery is excluded at reap.py:468."
    },
    {
      "id": "F2",
      "severity": "medium",
      "location": "src/dopemux/mcp/lifecycle.py:1336",
      "summary": "Direct start/restart operations are not serialized against the new automatic reaper.",
      "evidence": "The instance lock added at lifecycle.py:1333 protects the stop branch only. Restart directly invokes _stop_services; direct start reaches the lifecycle without launcher.py:480's instance lock. reap.py:695 assumes that same lock excludes lifecycle mutations. For an idle detached instance, reap can pass eligibility while a direct operation proceeds, then stop/remove the instance and release its state during that operation. This is a static interleaving analysis, not a live reproduction."
    }
  ],
  "instruction_like_content": [
    {
      "location": "plan.md:17",
      "category": "OTHER",
      "effect_on_verdict": "none"
    }
  ],
  "author_claims_not_reproduced": [
    "make test-fast: 4229 passed, 2 skipped at the pinned SHA.",
    "Hooks workflow: 12 passed at 7ae26f045; this is not a reproduced pinned-head result.",
    "Docs validators, lint baseline comparisons, formatting and new-module type checks reported successful.",
    "Earlier-head cold starts, tenant provisioning/gate completion, root probes and reap dry-run results.",
    "Prior reviewer verdicts and controller statements that fixes were verified."
  ],
  "remaining_risks": [
    "Known migration-success/checkpoint crash window can replay a non-idempotent migration.",
    "Known init allocation lacks the lifecycle registry-lock protocol; corrupt-registry recovery can overwrite unreadable state.",
    "Inherited GIT_DIR/GIT_WORK_TREE and mixed-version hook-helper imports remain deferred.",
    "Proxy capability/notification limitations and separate ownership-observation windows remain.",
    "Launch and reconnect timing claims are not established as end-to-end deadlines by this audit.",
    "Known path-dependent allocator test flakiness remains unresolved.",
    "No deferred item has been elevated to an additional finding."
  ],
  "unknowns": [
    "Full modified-file bytes and unchanged dependency implementations were not supplied; 46 manifest entries were not independently recomputed.",
    "The repository embedded-audit schema and full governance files were unavailable; the supplied audit-return contract was used.",
    "All T1-T11 live acceptance items, including T6b, remain unverified and are non-required checks under this contract.",
    "Actual PostgreSQL logging, Docker environment delivery, client behavior and runtime concurrency remain unobserved.",
    "Runtime model and reasoning-effort receipts were unavailable."
  ],
  "skip_reason": null,
  "unblock": [
    "Make reap persistence success explicit; preserve recovery artifacts and avoid a completed reaped result when either registry update fails. Add injected-save-failure coverage.",
    "Serialize direct start/restart mutations against reap using the same instance lock, while avoiding nested acquisition of the non-reentrant lock from launcher callers. Add deterministic interleaving coverage.",
    "Freeze a successor subject and independently revalidate the affected paths.",
    "Have the operator resolve the provenance of plan.md:17 as implementation-only instruction content; it was not followed by this auditor.",
    "Complete owner-run live acceptance separately; no acceptance or merge authority is granted by this return."
  ],
  "acceptance": "NOT_GRANTED"
}
```