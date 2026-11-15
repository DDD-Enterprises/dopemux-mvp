END_OF_PROMPT f6570e69-3bf5d4f2

**Change Summary:** Audit only. **FAIL — two medium findings.** Acceptance remains **NOT_GRANTED**.

**Authority Used:** Your pinned scope, supplied design/plan and audit contract, and the independent-audit skill. No delegation or network access.

**Analysis Performed:** Read all 19,071 lines of `subject.diff`, the supplied documents, tests, ledger and validation claims. Traced credentials, locks, reconnects, cleanup and environment handling.

1. **F1 — medium: reap uses stale eligibility.**  
   `src/dopemux/mcp/reap.py:658` rechecks attachments, then immediately stops containers. It does not recheck the missing-worktree or 20-minute-idle condition established at lines 399–407. Moreover, that attachment check can itself refresh `last_detach` while pruning a recent dead attachment (lines 203–211). Cleanup still proceeds. A launcher attaching and detaching between planning and application produces the same problem.

2. **F2 — medium: automatic reap still has unbounded registry waits.**  
   `src/dopemux/mcp/reap.py:629` calls `save_state_locked`, which reaches blocking `registry_lock` → `_flock` (`locks.py:245`, `:165`, `:78`). Neither the automatic nonblocking setting nor the deadline reaches these acquisitions. A contended registry lock can therefore stall launcher cleanup beyond its eight-second budget. The how-to’s “Automatic runs never wait” statement is unsupported.

The initial-session and post-initialize ownership guards are present. I did not re-report the ledger’s deferred items or elevate an additional deferred item on the supplied evidence.

**Validation Performed:**

- **PASS:** Diff structure; manifest path coverage; 20 reconstructed added-file hashes; three supplied document hashes; source-diff consistency; syntax parsing of 16 complete new Python files.
- **FAIL:** Reap eligibility preservation and bounded cleanup.
- **NOT_RUN:** Repository tests, lint/type/docs validators and every live acceptance item. An isolated, in-memory extracted-function probe confirmed the two problematic control-flow paths; it did not exercise Docker or real lock contention.

**Remaining Uncertainty / Risk:** Actual HEAD/ancestry, complete modified-file hashes, runtime behavior and author-reported results remain unverified. Several ledger entries are truncated.

**Files Touched:** None. **Git State:** Packet directory is not a Git repository; `git status` exited 128. **Rollback Plan:** No audit changes to roll back.

**Requested Next Step:** Revalidate reap eligibility under the instance lock after pruning; make registry finalization deadline-aware and recoverable. Add focused regression checks, freeze the corrected subject and rerun the independent audit.

```json
{
  "schema": "independent-audit/v1",
  "status": "FAIL",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "3bf5d4f26deb3368e965b86599a2a05520a1e59b",
    "observed_head": null,
    "head_match": null,
    "base": "5742575c4",
    "file_hashes": {
      "subject.diff": "572d939e6230868c99327fc96f33aa990aeec473f1f350a76dc950506c46beb3",
      "subject-src.diff": "d88f6d9aa5ff871f17575db8b80d19822672dd7da999adfc2a58c83a0762f556",
      "FILES.sha256": "58828bbb834dec6c274748d980bded83d9712d5f86fc20f4ff158fb4bbb396bb",
      "COMMITS.txt": "7d3164001818a3de017ae02ac59d7dc9c4bfa84417b7bb87580677ca37f911f7",
      "LEDGER_SUMMARY.md": "c801917580093be91db71921dd3a8a3c306624867803c5f0c0dfa419d04276d0",
      "VALIDATIONS.md": "b397b713e6e811d7c2c1b3b3a357bbbe2005e53711bcee830e9dd543eee2dbfd",
      "claudedocs/mcp-just-works-design-2026-11-05.md": "191267cf6ea7a272164d553f1ad48e097212170d089efeb6d9ac1cde3e275d4c",
      "claudedocs/mcp-just-works-m1-plan-2026-11-05.md": "3925ed00306b3a44d60c6f8e4afbebfac6122c63a147d839622547a309b7d607",
      "claudedocs/mcp-launch-root-probe-2026-11-05.md": "f0107cde23f1655e0b1b62f9e32dffbc61e82c93aaec17bcd6131ff725978782",
      "docs/02-how-to/mcp-setup-other-repos.md": "bcbdc732da1508e5a78fe1abb9b743b4a3afca126644ea57895b03b62d2fdc40",
      "docs/05-audit-reports/dopemux-multi-project-multi-worktree-readiness-2026-11-04.md": "93f67cda7f77b07f5976a449189c84480af0842666f71d3cb1251b0206493106",
      "src/dopemux/mcp/conport_tenant.py": "5ae27b50dd30551897cfbf2a0ec4f6f99fe105f0fe6a0567664ed7ef959ec0a8",
      "src/dopemux/mcp/launcher.py": "7eff6236db4b7bf7704c265d212fdb8518b89edc3aea0fad1f5c3f3ff84deb52",
      "src/dopemux/mcp/locks.py": "97f24e35f3b36d8c1a44d1cd4983a573037cc62fb9adf54a78ad9cea8c90c85b",
      "src/dopemux/mcp/reap.py": "2476f443868f9878b425dff8ff45f081acc1422d289d106b2fbafeb7b0b355b6",
      "src/dopemux/mcp/stdio_proxy.py": "e5188be8e9a031bcccab808a48d301f46a5986fb716d1550912f5cf9052b3783",
      "tests/unit/test_docs_no_envrc_recipe.py": "26d5c67fc1e698e24d898e8e7b70fb3f560e3883f2857b286767622448e2e5af",
      "tests/unit/test_mcp_conport_tenant.py": "c0e468f4b02c93ad67205d23888034c9ad278ebfc8fb0c8e1541d2813c75192d",
      "tests/unit/test_mcp_identity_git_only.py": "79be954be951abb02208c666d832967eb510f5bf3700f02b6384e988fcf65160",
      "tests/unit/test_mcp_launcher.py": "0b483cdac39f1279a71a7c4f550b61bb0f9fd2d0db78094f0d7b7b3e14050923",
      "tests/unit/test_mcp_launcher_render.py": "d821b655d6eb4e6e764651fca51a8cbc2bc633c58165e55b29557d85fec05923",
      "tests/unit/test_mcp_lifecycle_ports_from_leases.py": "77deaa9a1d578acadee43e1fa059fddacee67d79738a60471432a8742df501da",
      "tests/unit/test_mcp_locks.py": "fe03f4da82ff8c4e82fdf3f89ebf533b1f67da9e637542de975dd5eaf7bfccc8",
      "tests/unit/test_mcp_reap.py": "b575ca7f6b2a1d8990290b19c1d3b1b21ca8e0eaeffeeaab088670c8aaa945d2",
      "tests/unit/test_mcp_stdio_proxy.py": "986cf2236353503d95a84f6eae3056367043d5397f1e0f2e171c994860dc2cfb",
      "tests/unit/test_mcp_switch_project.py": "ed004622baac644233eb8bf1b288a284c098e1b3865b0a99e469d8bd7a3bfb9c",
      "tests/unit/test_native_hooks_dispatcher.py": "2368f87e1191e27248d19aeac0a83230b9fb1fa0cdecf147ebba99cc1951f536"
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
      "id": "STATIC_FULL_DIFF",
      "command_or_method": "Personally read subject.diff in full, supplied documents, ledger, validations and changed tests; compare subject-src.diff blocks.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "19,071 lines and 68 file blocks reviewed. All 31 source-diff blocks are identical to their full-diff counterparts. No delegation."
    },
    {
      "id": "PACKET_INTEGRITY",
      "command_or_method": "Read-only Python reconstruction, SHA-256 comparison, unified-hunk count validation and manifest path comparison.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "20 complete added files match FILES.sha256. Standalone design, plan and how-to match their manifest hashes. Design and plan also equal reconstructed diff content. No hunk count or manifest path mismatch; 67 surviving paths plus deletion of .claude/WORKTREE_MCP_SETUP.md."
    },
    {
      "id": "SYNTAX",
      "command_or_method": "ast.parse on all complete newly added Python files reconstructed in memory.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "16 files parsed. This verifies syntax only, not imports, types or behavior."
    },
    {
      "id": "RF1_SECRETS_STATIC",
      "command_or_method": "Trace branch-authored credential construction, SQL delivery, gate execution, redaction and persistence arguments.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:152 excludes password from repr; :207 writes private secret files; :367 sends SQL through stdin; :431 redacts before truncation; :619 includes password and generated SCRAM verifier in hidden values; :734 sends the gate URL through a temporary env file. Lifecycle overlays credentials into compose-up environment rather than argv, mcp.env or plan arguments. No branch-authored direct secret-print path identified. Actual process/server logs and unchanged serializer behavior were not executed."
    },
    {
      "id": "RF2_LOCK_ORDER_STATIC",
      "command_or_method": "Trace nested lock acquisition, attach/start/stop boundaries and inode validation.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "locks.py:8 documents ordering; :99-108 rechecks descriptor/path inode after flock. launcher.py:449 rechecks backend under instance lock; :760-761 attaches under that lock. Stop encloses stopping and release in the instance lock. Reserved-port paths acquire registry locks inside reserved locks. No reverse nesting identified in the supplied changes. Boundedness is separately FAIL under RF4."
    },
    {
      "id": "RF3_RECONNECT_STATIC",
      "command_or_method": "Trace first session, reconnect, post-initialize ownership checks and request replay classification.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:309 and :343 guard the initial session; :363 checks ownership again before publishing session at :367. Reconnect uses the same guarded path. :459 forwards with a bounded resend; ambiguous in-flight connection loss is not replayed. Session-terminated handling, backoff and per-window reconnect accounting are present. launcher.py:600 supplies label-based ownership refusal. Corresponding tests were read, not run."
    },
    {
      "id": "RF4_REAP_SAFETY_STATIC",
      "command_or_method": "Trace candidate eligibility, labels/scopes, state-only cleanup, locking, deadlines, kill switches and registry finalization.",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "F1: reap.py:658-667 does not revalidate eligibility after attachment pruning. F2: :629 invokes blocking registry persistence without the deadline. Label joins, scope exclusions, kill-switch-first automatic path, per-service release and orchestrator exclusion are present, but do not repair these failures."
    },
    {
      "id": "REAP_CONTROL_FLOW_PROBE",
      "command_or_method": "Execute AST-extracted _reap_one, _stop_and_remove, _release_state and registry-lock helpers with all filesystem mutations, locks and Docker replaced by in-memory fakes.",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "With refreshed detach age simulated as 1 second, _reap_one still issued stop/rm and reported reaped. With automatic instance locking set nonblocking and the deadline expiring after rm, both registry acquisitions still requested blocking=True. Probe exit 0 means both defect assertions reproduced; this was not a repository test or real contention test."
    },
    {
      "id": "RF5_AMBIENT_ENV_STATIC",
      "command_or_method": "Trace git identity and explicit environment scrub across launch, lifecycle and compose/build calls.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "launcher.py:170 resolves git checkout; :273 uses the shared scrub set. docker_runtime.py:51 names identity, tenant credentials, ports and dope-memory identity variables; :107 removes them before explicit overlays. New launch/build/lifecycle paths opt into scrubbing. Legacy cwd-compose and intentionally retained host variables remain outside this guarantee."
    },
    {
      "id": "RF6_DEFERRED_ITEMS",
      "command_or_method": "Compare concerns against LEDGER_SUMMARY.md:58-123 and final code.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Known deferrals were not repeated as findings. No additional deferred item elevated on supplied evidence. F2 identifies the remaining registry-lock wait, distinct from the repaired instance-lock and initial-inspection paths. Some ledger entries are truncated, limiting historical adjudication certainty."
    },
    {
      "id": "DOCS_VS_CODE",
      "command_or_method": "Read complete how-to and compare claims against branch code and amendments.",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "docs/02-how-to/mcp-setup-other-repos.md cleanup section promises bounded automatic runs that never wait; F2 contradicts that. Launcher entries, refusal codes, shared Dockerfile-based image tags, kill switches and Codex/EnterWorktree limitations otherwise have corresponding implementation or explicit qualification."
    },
    {
      "id": "D1_D4_D6_D9_STATIC",
      "command_or_method": "Trace launcher rendering, image-missing branch, hook dispatcher and command wiring.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Launcher rendering uses command plus mcp launch arguments. launcher.py:382 starts a detached build and typed refusal, with per-runtime/service PID guards. docker_runtime.py:503 derives shared service image tags. .claude/hooks/run_native_hooks.sh:14-25 selects checkout hooks/interpreter; native_hooks.py:708 honors payload cwd. Commands and corresponding tests are present. Runtime success and timing are not asserted."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_1",
      "command_or_method": "Map checkout-subdirectory identity requirement to implementation and tests.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "launcher.resolve_launch_root and tests test_resolve_target_repo_uses_git_toplevel_from_subdir/test_resolve_launch_root_from_subdirectory reviewed. Tests cannot run in this packet-only sandbox. Explicit --repo subdirectory behavior remains a listed deferral."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_2",
      "command_or_method": "Map symlink identity requirement to path normalization and test.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Identity resolution changes and test_identity_stable_across_symlinked_path reviewed; filesystem integration test not executed."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_3",
      "command_or_method": "Map outside-git/unmanaged-config refusal to launcher validation and tests.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Root/config validation precedes attach/reap/backend work. Named refusal tests reviewed. Test execution unavailable; recognition checks launcher shape, not arbitrary hand-written-file provenance."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_4",
      "command_or_method": "Map corrupt-registry behavior to loaders, reap planning and tests.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Reap planning rejects unreadable registry state; cleanup save helper preserves corrupt files. Start-path recovered-empty overwrite is already deferred. Named tests reviewed, not executed."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_5",
      "command_or_method": "Map malformed/missing-cwd hook payload behavior to main and tests.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "native_hooks.py:701 catches malformed input; :708-710 passes None for missing cwd, invoking normal adapter fallback. Tests reviewed, not executed. Missing cwd alone does not establish unconditional exit 0 for every valid policy event."
    },
    {
      "id": "REPOSITORY_VALIDATIONS",
      "command_or_method": "make test-fast; hooks workflow pytest; docs validators; lint, format and type checks.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "User-provided packet-only read-only environment lacks the checkout/test environment. VALIDATIONS.md was treated solely as author claims."
    },
    {
      "id": "T1",
      "command_or_method": "Fresh git worktree session connects with correct identity.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Owner-run live acceptance unavailable. Launcher, identity and lifecycle tests provide static coverage only."
    },
    {
      "id": "T2",
      "command_or_method": "Claude-created worktree session.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No runner session available. Mid-session EnterWorktree reconnect cwd is explicitly unmeasured in supplied documentation."
    },
    {
      "id": "T3",
      "command_or_method": "Concurrent Codex session in the same worktree.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Amendment design.md:288 excludes Codex rendering from M1; no Codex activation evidence reproduced."
    },
    {
      "id": "T4",
      "command_or_method": "Fresh project init, tenant provisioning, private credentials and session connection.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Provisioning, SCRAM, private-file and gate tests reviewed. No live Postgres, Docker, credential-file or session inspection."
    },
    {
      "id": "T5",
      "command_or_method": "Adopt existing dNh_CRM tenant without creating another database.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Legacy envrc adoption and main-checkout fallback tests reviewed; existing data and database counts not inspected."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal and explicit project switch.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Ownership guards and switch-project tests reviewed, including refusal after owner change. No live switch or runner error display verified."
    },
    {
      "id": "T6b",
      "command_or_method": "Free reserved port starts one orchestrator under concurrent launch.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Reserved-port serialization and free-port test paths reviewed; live concurrent starts unavailable."
    },
    {
      "id": "T7",
      "command_or_method": "Worktree hook execution and red-lane denial.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Dispatcher and payload-cwd tests reviewed. No live hook_status.json or policy denial exercised."
    },
    {
      "id": "T8",
      "command_or_method": "Removed-worktree reap preserves main sidecars and releases state.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Owner-run destructive acceptance unavailable. Static cleanup review found F1 and F2."
    },
    {
      "id": "T9",
      "command_or_method": "init --force --repo worktree leaves main unchanged.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Target-path wiring and identity/init tests reviewed; no real worktree/main mutation comparison."
    },
    {
      "id": "T10",
      "command_or_method": "Missing image produces detached build refusal within five seconds and later reconnects.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Detached build, typed refusal and PID-guard tests reviewed. Timing, actual build and reconnect not measured."
    },
    {
      "id": "T11",
      "command_or_method": "Two launchers within 100 ms produce one start and two working bridges.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "test_two_launchers_one_start and instance-lock recheck read. No live race or two-client bridging run."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "medium",
      "location": "src/dopemux/mcp/reap.py:658",
      "summary": "Reap applies stale idle/missing-worktree eligibility after acquiring the instance lock.",
      "evidence": "plan_reap evaluates attachment count without pruning and the missing/idle predicate at lines 399-407. _reap_one only rechecks live attachments at 658 before stop/rm at 661. live_attachments defaults to pruning and advances last_detach from recent dead records at 203-211, but eligibility is never recalculated. An intervening attach/detach or recreated worktree similarly invalidates the plan. The extracted-function probe simulated a refreshed one-second detach age and still observed stop/rm and reaped."
    },
    {
      "id": "F2",
      "severity": "medium",
      "location": "src/dopemux/mcp/reap.py:629",
      "summary": "Automatic reap deadlines do not bound registry-lock acquisition.",
      "evidence": "_release_state calls save_state_locked without deadline/nonblocking controls. locks.py:286 calls locked_reload_and_save; :245 enters registry_lock; :165 invokes _flock with default blocking=True at :78. _reap_one calls this finalization at :682 even after Docker consumed the remaining deadline. The extracted-function probe observed two blocking registry acquisitions with blocking_lock=False and an expired deadline. Real lock contention was not exercised."
    }
  ],
  "instruction_like_content": [
    {
      "location": "plan.md:17",
      "category": "OTHER",
      "effect_on_verdict": "none"
    },
    {
      "location": "LEDGER_SUMMARY.md:141",
      "category": "OTHER",
      "effect_on_verdict": "none"
    }
  ],
  "author_claims_not_reproduced": [
    "VALIDATIONS.md claims make test-fast: 4221 passed, 2 skipped at the pinned SHA.",
    "Hooks workflow claim is 12 passed at 7ae26f045, not an independently reproduced result at the pinned SHA.",
    "Docs validators, differential lint, formatting and five-module mypy results were not reproduced.",
    "Lint comparison uses reported base 583720375 rather than the requested branch-authored diff base.",
    "Earlier-head live cold launch, tenant provisioning/gate and reap dry-run claims were not reproduced.",
    "Prior reviewers' approval, fix verification and live observations were not adopted as auditor evidence.",
    "COMMITS.txt's 20-commit branch history and association of packet contents with the actual Git SHA were not independently verified against Git objects."
  ],
  "remaining_risks": [
    "Listed migration replay, corrupt-registry recovery, init/start lease race and other deferred limitations remain; they were not re-reported as new findings.",
    "The accepted residual ownership-check timing window remains; initial and post-initialize guards reduce it but do not make Docker ownership and request delivery atomic.",
    "Slow-readiness and pending tenant-gate recovery were statically traced but not exercised end to end.",
    "Backend protocol behavior, secret handling by external processes and actual filesystem permissions require runtime verification.",
    "The supplied known flaky allocation test remains an unverified author-reported risk."
  ],
  "unknowns": [
    "No Git checkout or observed HEAD; head_match is null rather than fabricated.",
    "Hashes identify audited packet content. Full contents of the remaining modified files were unavailable, so their manifest hashes were not independently verified.",
    "The repository embedded audit schema and validator were not supplied; this return follows the user's independent-audit/v1 contract.",
    "All T1-T11 live acceptance items, including T6b, remain NOT_RUN and are not required static audit checks.",
    "Several ledger entries are truncated, preventing full recovery of prior adjudication details.",
    "Runtime model and reasoning-effort receipts are unavailable."
  ],
  "skip_reason": null,
  "unblock": [
    "Re-evaluate the current missing-worktree/idle predicate under the instance lock after pruning attachments; skip candidates whose eligibility changed.",
    "Propagate bounded or nonblocking registry acquisition through automatic cleanup finalization, preserving recoverable state when finalization cannot complete.",
    "Add focused checks for refreshed last_detach, recreated worktree, registry-lock contention and deadline expiry during finalization.",
    "Correct the how-to's unconditional bounded/nonwaiting cleanup claim unless the complete path enforces it.",
    "Freeze corrected files at a successor SHA, provide the full checkout or complete relevant source files, and rerun independent static review and repository validation.",
    "Keep owner live acceptance separate and NOT_GRANTED until its checks are actually performed."
  ],
  "acceptance": "NOT_GRANTED"
}
```