END_OF_PROMPT 7f3a9c2e-eb3f0624

**FAIL — one high and two medium findings. Acceptance is NOT_GRANTED.**

**Change Summary:** Read-only audit of the supplied `5742575c4..eb3f0624b9f5ab88c8989e4e7e327a883ec56f53` materials. No changes made.

1. **F1 — High: ownership can change between verification and connection.**  
   `src/dopemux/mcp/launcher.py:534` releases the reserved-port lock before the proxy connects; `src/dopemux/mcp/stdio_proxy.py:299` opens its first session without a guard. An intervening `switch-project` can therefore make project A’s launcher connect to project B. Reconnect verification also precedes connection without protecting that interval (`stdio_proxy.py:358`). The extracted-source probe demonstrated the first-session ordering with a modeled owner switch. Live exploitation was **NOT_RUN**.

2. **F2 — Medium: first-session SIGKILL cleanup cannot reach pruning.**  
   `src/dopemux/mcp/reap.py:388` counts attachments with `prune=False`, then requires `last_detach` at line 394. If the first launcher dies without creating that marker, the existing worktree never becomes an idle candidate. Pruning that would create the marker happens only after selection. The in-memory probe returned zero candidates despite a dead attachment older than the idle threshold.

3. **F3 — Medium: automatic reap deadlines exclude blocking operations.**  
   `src/dopemux/mcp/reap.py:640` acquires an unbounded lock; `src/dopemux/mcp/locks.py:88` uses blocking `LOCK_EX`. Contention can exceed the advertised 8/45/60-second budgets. Initial Docker inspection also uses a fixed 10-second timeout (`reap.py:808`), exceeding the launcher’s entire eight-second budget. This contradicts the how-to’s deadline guarantees.

**Authority Used:** Current audit packet, supplied manifest/diff, design and amendments, plan, and deferred ledger. Historical approval and validation statements were treated as claims.

**Analysis Performed:** Production-path tracing, secret handling, lock ordering, reconnect behavior, reap safety, environment scrubbing, and how-to comparison. Two bounded workers supported documentation/test coverage, requesting `gpt-6.1-sol`/medium; observed identities and billing costs remain UNKNOWN. I independently inspected and probed all three reported defects. Full single-auditor rereading of every documentation/test line remains UNKNOWN; delegated coverage is disclosed below.

**Validation Performed:** **PASS** — 20 reconstructed new-file hashes, three supplied document hashes, 31 source-diff section matches, and syntax parsing of 16 new Python files. **FAIL** — F1–F3 contract checks. **NOT_RUN** — repository suite, live acceptance, and integration tests.

**Remaining Uncertainty / Risk:** No Git checkout, complete existing-file sources, SDK dependencies, Docker environment, or proof schema was available. Known deferrals were not promoted into new findings; none additional is raised here. Several ledger entries are truncated.

**Files Touched:** None. **Git State:** Unobserved; directory is not a Git repository. **Rollback Plan:** None required.

**Requested Next Step:** Repair F1–F3 with deterministic regression coverage, freeze a successor SHA, and rerun the independent audit. Preserve owner-run acceptance as NOT_RUN until executed.

```json
{
  "schema": "independent-audit/v1",
  "status": "FAIL",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "eb3f0624b9f5ab88c8989e4e7e327a883ec56f53",
    "observed_head": null,
    "head_match": null,
    "base": "5742575c4",
    "file_hashes": {
      "subject.diff": "7a6820b68e9a2876469ec3324e053bb85ea571a9e91925573e6717612633d1e5",
      "FILES.sha256": "38352595ffa2515dd34b813506eb10bf5d401821001b9d08ec3d7ff2ea6f6f98",
      "claudedocs/mcp-just-works-design-2026-11-05.md": "5c5946a418173d23b11e5a18dfdfa5fa6662a3a25e8c127e9a7b79e9cef7e2f0",
      "claudedocs/mcp-just-works-m1-plan-2026-11-05.md": "cd7804a25026bb9328d8b64988d8adba6e15ebc1b9b7992eb84e12f07cb038a6",
      "docs/02-how-to/mcp-setup-other-repos.md": "661ebd9f758483a2bb4ab5d1a2c5292ee592188cd4f55065bc4f4d18bf6243a6",
      "src/dopemux/mcp/conport_tenant.py": "5ae27b50dd30551897cfbf2a0ec4f6f99fe105f0fe6a0567664ed7ef959ec0a8",
      "src/dopemux/mcp/launcher.py": "1b87c82b5be0aa1804ce9c072391624644e44e162b7d5fbcbbac870722a7881b",
      "src/dopemux/mcp/locks.py": "57c3682425d4b1551bb8912f1a99a879b26451276b11c2e05d2a28911320e4c6",
      "src/dopemux/mcp/reap.py": "75341bf039bce7f5be5a668e565d953c293fca7459829ae7b014ce4a41671261",
      "src/dopemux/mcp/stdio_proxy.py": "d95e1c5506862b21e5cac2452b85a1e21780de13457bc17a5f6cc23a9e0fe4b0"
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
      "id": "BUNDLE_INTEGRITY",
      "command_or_method": "Read-only Python reconstruction, SHA-256 comparison, source-diff section comparison, and final digest recheck",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "68 diff sections, 18581 lines, 67 manifest entries, 19 listed commits. All 20 added files reconstructed from subject.diff matched FILES.sha256. Supplied design.md, plan.md and how-to matched their manifest entries. All 31 subject-src.diff sections exactly matched subject.diff. Bundle digests remained unchanged. This pins supplied bytes, not independently observed Git history."
    },
    {
      "id": "REQUIRED_FULL_DIFF_SELF_READ",
      "command_or_method": "Principal review plus two bounded audit-support workers",
      "exit_code": null,
      "bucket": "UNKNOWN",
      "evidence": "Combined audit coverage read all diff sections. Principal directly read all production-code changes, the how-to, ledger, validation claims and finding-specific tests, but did not personally reread every remaining documentation/test line. Delegated coverage is not promoted to a complete single-auditor self-read PASS."
    },
    {
      "id": "NEW_PYTHON_SYNTAX",
      "command_or_method": "ast.parse on reconstructed added Python files",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "All 16 added Python files parsed. No imports of subject modules, bytecode writes, test execution or integration behavior were implied."
    },
    {
      "id": "REQUIRED_SECRETS_ARGV_LOG_REVIEW",
      "command_or_method": "Trace conport_tenant, lifecycle tenant wiring, init, compose environment and error-output handling in supplied diff",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Available code uses atomic 0600 secrets, repr-hidden password, SQL stdin, a SCRAM verifier in CREATE ROLE, a 0600 temporary gate env-file removed in finally, and redaction before error-tail truncation. Tenant credentials are injected into compose execution after runtime artifacts are planned. No new secret disclosure was established in the supplied changes. Sealed gate/server logging and omitted unchanged serializers remain unverified."
    },
    {
      "id": "REQUIRED_LOCK_ORDER_REVIEW",
      "command_or_method": "Trace instance, registry, provision and reserved-port acquisition and release",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Observed instance-before-registry and reserved-before-registry ordering; inode comparison follows flock acquisition; attach is written under instance_lock; explicit stop takes instance_lock around stopping and state release. The separate deadline defect is F3. Known deferred init lease-write locking was not re-reported."
    },
    {
      "id": "REQUIRED_RECONNECT_GUARD_REVIEW",
      "command_or_method": "Source trace plus in-memory execution of extracted ensure_orchestrator and _BackendLink.run with modeled ownership change",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "Probe recorded reserved-lock release, modeled owner switch A to B, then first session attempt observing B with zero prior guard calls. Source sends at most twice, recognizes Session terminated, and includes reconnect backoff/window controls, but ownership is not protected through connection establishment. See F1."
    },
    {
      "id": "REQUIRED_REAP_SAFETY_REVIEW",
      "command_or_method": "Trace labels, registry join, exclusions, attachments, state release, kill switches and deadlines; extracted-source probes",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "Label/registry joins, scope exclusions, kill-switch-first automatic entry and service-specific state release are present. A dead first attachment with no last_detach produced zero candidates; direct pruning alone produced the missing marker. A modeled contended instance lock advanced beyond the eight-second deadline before returning. See F2 and F3."
    },
    {
      "id": "REQUIRED_HOWTO_TRUTHFULNESS",
      "command_or_method": "Compare complete supplied how-to against changed runtime code",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "docs/02-how-to/mcp-setup-other-repos.md:229 describes bounded automatic reap and subsequent text says every Docker call is cut to remaining time. Blocking locks and the fixed initial inspection timeout contradict that guarantee. SIGKILL-pruning documentation also lacks a reachable automatic path when no detach marker exists."
    },
    {
      "id": "AMBIENT_ENVIRONMENT_REVIEW",
      "command_or_method": "Trace git-only identity, trust-env options, launcher scrub, CLI scrub and compose interpolation",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "runtime_state.resolve_identity_view uses an empty override mapping by default; project_identity no longer implicitly reads os.environ. docker_runtime.AMBIENT_SCRUB_VARS includes specified identity, port, container-name and CONPORT_DB credential variables. Launcher and lifecycle compose paths apply scrubbing. Known GIT_DIR/GIT_WORK_TREE inheritance and legacy cwd-compose behavior remain disclosed deferrals."
    },
    {
      "id": "DEFERRED_ITEMS_REVIEW",
      "command_or_method": "Compare candidate findings with LEDGER_SUMMARY.md Deferred items and implementation amendments",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "No additional known deferral is promoted to a finding. F1 identifies an unprotected ownership interval; F2 identifies unreachable automatic pruning after the claimed signal-cleanup fix; F3 identifies unbounded operations outside deadline enforcement. Truncated ledger entries limit knowledge of omitted detail."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_1",
      "command_or_method": "Static subdirectory root-resolution trace",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Implicit lifecycle cwd and launcher root use git rev-parse --show-toplevel. Test mappings: tests/unit/test_mcp_identity_git_only.py:136 and tests/unit/test_mcp_launcher.py:226. Tests were not executed."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_2",
      "command_or_method": "Static canonical-path review and test mapping",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Changed root-resolution paths use Path.resolve. Symlink identity coverage is authored at tests/unit/test_mcp_identity_git_only.py:99. Actual symlink/git behavior was not executed here."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_3",
      "command_or_method": "Trace launcher refusal before attach, reap and lifecycle",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "resolve_launch_root rejects non-git roots and missing/non-launcher service entries before Docker paths. Tests map to tests/unit/test_mcp_launcher.py:234 and :248. Managed-entry recognition is the ledger-approved shape check."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_4",
      "command_or_method": "Review changed registry recovery, backend discovery and reap planning",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "find_backend rejects non-OK registry status; plan_reap immediately returns an empty plan for it; locked_reload_and_save contains recovery logic. Authored coverage includes tests/unit/test_mcp_reap.py:256. Silent recovery is an existing listed deferral; unchanged registry loader implementation was not supplied."
    },
    {
      "id": "PLAN_REVIEW_FOCUS_5",
      "command_or_method": "Trace hook input parsing and cwd selection",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "native_hooks.main exits success for invalid JSON/non-dict input and uses payload cwd when valid, otherwise the existing default. Test mappings: tests/unit/test_native_hooks_dispatcher.py:247 and :253. Dispatcher exit-code coverage is at :179."
    },
    {
      "id": "REPOSITORY_VALIDATIONS",
      "command_or_method": "make test-fast; hooks workflow tests; docs validators; lint, format and type checks",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No repository checkout or test environment is present; pytest, anyio and mcp are unavailable in the inspected Python environment. VALIDATIONS.md was read only as author claims."
    },
    {
      "id": "T1",
      "command_or_method": "Owner-run fresh git worktree session, clean and contaminated environments",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live runner/Docker environment. Static mapping: launcher ensure_backend and tests/unit/test_mcp_launcher.py:267/:278; git identity tests. Earlier-head connection claims were not reproduced."
    },
    {
      "id": "T2",
      "command_or_method": "Owner-run Claude-created worktree session",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No Claude session/worktree execution. Root-probe artifact is an author claim; mid-session reconnect cwd remains explicitly unmeasured."
    },
    {
      "id": "T3",
      "command_or_method": "Concurrent Codex and Claude sessions in one worktree",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Design amendment explicitly excludes Codex rendering from M1. No Codex runtime acceptance was exercised."
    },
    {
      "id": "T4",
      "command_or_method": "Fresh-project init, tenant authentication, connection and on-disk permissions",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live Postgres/Docker. Static mapping: conport_tenant resolution/provisioning and tests/unit/test_mcp_conport_tenant.py:247/:430/:901."
    },
    {
      "id": "T5",
      "command_or_method": "Adopt an existing hand-made tenant and verify existing data",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No existing tenant or data access. Static adoption mappings: tests/unit/test_mcp_conport_tenant.py:200 and :486."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal, switch-project and old-session refusal",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live switch. Static refusal tests exist at tests/unit/test_mcp_launcher.py:422/:444; switch-project tests are supplied. F1 demonstrates that the source does not close every ownership-change interval."
    },
    {
      "id": "T6b",
      "command_or_method": "Free reserved port and concurrent orchestrator launch",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live port or process contention. Static mapping: ensure_orchestrator reserved lock and tests/unit/test_mcp_launcher.py:464."
    },
    {
      "id": "T7",
      "command_or_method": "Real lifecycle hooks and DCP hard-deny behavior in linked worktree",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Dispatcher and adapter changes reviewed; authored tests cover interpreter selection and payload cwd. Real hook_status output, helper imports and hard-deny integration were not exercised."
    },
    {
      "id": "T8",
      "command_or_method": "Remove worktree, reap containers and leases, preserve main",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live removal/reap. Static mappings: tests/unit/test_mcp_reap.py:193/:332/:673/:726. F2 and F3 remain failures in related cleanup paths."
    },
    {
      "id": "T9",
      "command_or_method": "init --force --repo worktree leaves main unchanged",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No filesystem mutation permitted. Static target and preservation mappings: tests/unit/test_mcp_identity_git_only.py:204/:220."
    },
    {
      "id": "T10",
      "command_or_method": "Missing image produces detached build and refusal within five seconds, then reconnects",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Detached Popen, per-service PID files and shared image tags are present. Tests map to tests/unit/test_mcp_launcher.py:318/:951/:1053. Wall-clock refusal and eventual connection were not measured."
    },
    {
      "id": "T11",
      "command_or_method": "Launch two clients within 100ms; exactly one start and both bridge",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Instance-lock double-check is present; authored coverage is tests/unit/test_mcp_launcher.py:354. Real concurrent startup and bridging were not executed."
    },
    {
      "id": "OPERATOR_PROOF_SCHEMA",
      "command_or_method": "Inspect availability of schemas/proof/embedded_audit.schema.json",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Schema is absent from the supplied directory. Audit return follows the requested independent-audit/v1 contract; operator-filed proof was not validated."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "high",
      "location": "src/dopemux/mcp/stdio_proxy.py:299",
      "summary": "Backend ownership verification is not protected through connection establishment.",
      "evidence": "ensure_orchestrator returns from reserved_port_lock at launcher.py:534 before launch invokes run_proxy at :766. _BackendLink.run first calls _session_once without a guard. A supported switch-project between those steps can replace A with B, allowing A's initial session to connect to B. Reconnect similarly separates _guard_allows at stdio_proxy.py:358 from _session_once at :360 without the reserved lock. An extracted-source probe observed owner B at the first session attempt with zero prior guard calls after a modeled switch. tests/unit/test_mcp_stdio_proxy.py:640 explicitly expects no initial guard; launcher.py test :1179 fixes the first fake connection to A and does not cover this interval. This violates design A1 despite the amendment documenting first-session exclusion. Live integration NOT_RUN."
    },
    {
      "id": "F2",
      "severity": "medium",
      "location": "src/dopemux/mcp/reap.py:388",
      "summary": "A dead first launcher with no last_detach marker never reaches automatic idle cleanup.",
      "evidence": "plan_reap calls live_attachments(prune=False), then _last_detach_age at :394. Missing marker returns None at :318, so the existing worktree is excluded. Marker creation at :200 occurs only during pruning, normally reached in _reap_one after selection. An extracted-source probe with a dead 3600-second-old attachment and existing worktree produced no candidate and no marker; directly invoking pruning produced the marker. Tests :935 onward exercise the helper, not automatic selection. Cleanup remains blocked until another operation writes a marker or the worktree disappears."
    },
    {
      "id": "F3",
      "severity": "medium",
      "location": "src/dopemux/mcp/reap.py:640",
      "summary": "Automatic reap deadlines do not bound lock acquisition or initial Docker inspection.",
      "evidence": "_reap_one enters instance_lock before further deadline checks; locks.py:88 performs blocking flock(LOCK_EX) without a timeout. Concurrent explicit and automatic reaps can contend on the same candidate and exceed the automatic budget. Extracted-source execution with a modeled delayed lock crossed deadline 8 before returning attached. Separately, maybe_reap at :808 uses fixed _HOOK_DOCKER_TIMEOUT_S=10 even for launcher deadline_s=8. The how-to's bounded deadlines and remaining-time Docker guarantees therefore do not hold."
    }
  ],
  "instruction_like_content": [
    {
      "location": "claudedocs/mcp-just-works-m1-plan-2026-11-05.md:17",
      "category": "OTHER",
      "effect_on_verdict": "none"
    },
    {
      "location": "claudedocs/mcp-just-works-m1-plan-2026-11-05.md:31",
      "category": "OTHER",
      "effect_on_verdict": "none"
    },
    {
      "location": "claudedocs/mcp-just-works-m1-plan-2026-11-05.md:32",
      "category": "OTHER",
      "effect_on_verdict": "none"
    },
    {
      "location": "LEDGER_SUMMARY.md:36",
      "category": "OTHER",
      "effect_on_verdict": "none"
    },
    {
      "location": "LEDGER_SUMMARY.md:37",
      "category": "OTHER",
      "effect_on_verdict": "none"
    }
  ],
  "author_claims_not_reproduced": [
    "VALIDATIONS.md: make test-fast reported 4211 passed, 2 skipped at the pinned SHA.",
    "VALIDATIONS.md: hooks workflow reported 12 passed at 7ae26f045, with the file claimed unchanged at the pin.",
    "VALIDATIONS.md: docs validators, lint diffs, formatting and new-module typing reported clean.",
    "Earlier-head live launcher, tenant/gate and reap dry-run results were not reproduced.",
    "Controller and internal-review completion, approval, clean-tree and fixed-finding statements were not treated as audit evidence.",
    "Owner confirmation of post-approval design amendments was asserted by the ledger but not independently established."
  ],
  "remaining_risks": [
    "F1 permits a cross-project connection under an ownership-change interleaving; no live exploit was executed.",
    "F2 can retain idle sidecars and leases after an abrupt first-session death.",
    "F3 can stall launcher or hook execution beyond documented budgets.",
    "Known deferrals remain: init lease-write locking, inherited Git environment, mixed-version hook helpers, migration/state-write interruption handling, and documented M1 client limitations. No additional finding is raised for these.",
    "The reported allocator flake remains an unreproduced author claim."
  ],
  "unknowns": [
    "Observed Git HEAD, branch, commit ancestry and the complete hashes of existing files not supplied in full.",
    "Full single-auditor rereading of all documentation/test lines; complete combined coverage included delegated readers.",
    "All owner-run T1-T11 acceptance, including T6b, remains NOT_RUN.",
    "Actual Docker, MCP SDK, PostgreSQL authentication, server logging and sealed migration-gate behavior.",
    "Full unchanged registry loaders, serializers and other consumers omitted from diff context.",
    "Operator proof-schema compliance; schema was not supplied.",
    "Details omitted by truncated ledger entries.",
    "Worker execution identities and billing costs. Two workers requested gpt-6.1-sol at medium effort; no runtime receipts or model escalations were observed."
  ],
  "skip_reason": null,
  "unblock": [
    "Protect initial and reconnect ownership verification through session establishment; add deterministic tests that switch ownership in both intervals and prove the foreign backend receives no request.",
    "Make dead-attachment recovery reachable before idle-candidate exclusion while retaining read-only dry-run behavior and fail-closed idle handling; test the actual automatic entry point with no last_detach.",
    "Bound lock acquisition and initial inspection by remaining automatic-reap time; test contention against explicit reap and inspection exceeding the launcher budget.",
    "Update how-to guarantees to match enforced behavior.",
    "Freeze a corrected successor SHA, provide complete audit inputs and executable validation context, and rerun the independent audit including the outstanding full self-read.",
    "Run owner acceptance separately; do not promote historical claims or these extracted-source probes into live PASS results."
  ],
  "acceptance": "NOT_GRANTED"
}
```