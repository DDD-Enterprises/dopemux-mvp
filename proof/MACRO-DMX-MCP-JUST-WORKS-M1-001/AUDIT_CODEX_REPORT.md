END_OF_PROMPT 8b72d8c3-efb06f7c

**Change Summary:** Read-only audit completed against the pinned subject. No new reportable technical findings. Verdict: **NEEDS_SUPERVISOR** under the supplied verdict table because `plan.md:17` contains an agent-directed implementation instruction. I classified it as benign template content, ignored it, and did not delegate.

**Authority Used:** Your cycle-6 audit scope and exclusions, repository instructions, and independent-audit/v1. This return does not grant acceptance or replace the governing embedded audit.

**Analysis Performed:** Read the complete branch-authored diff and supplied materials; traced credential handling, lock acquisition, lifecycle ownership, proxy retries, cleanup, and documentation. Independently verified the pinned HEAD, exact diff bytes, all 69 file hashes, and the revert’s tree identity.

**Validation Performed:**

- **PASS:** Required static reviews and the specific earlier finding closures described below.
- **FAIL:** No new subject failure established.
- **NOT_RUN:** Test suite, lint/type checks, live services, and every owner-run acceptance scenario. Recorded validation results remain author claims.

The `30b0fdec9` F1/F2, `3f1335e7f` F1/F2, `43294e99b` F1 **as specifically reported**, and `fc591cba1` F1/F2 remain closed. Item 16 is completely reverted; its implementation, tests, and affirmative design amendment are absent. Historical references correctly record the revert.

**Remaining Uncertainty / Risk:** These are bounded closures, not universal guarantees. A hand-written template matching dopemux’s allowed shape remains repairable; an allowed variable’s value can still change the expanded authority. The exact session-termination literal retains its pre-stated resend assumption. Reverting item 16 does not make existing directory discovery bounded. I would not raise these accepted residuals, the documented cleanup follow-up, or item 18 as new findings. Neither item-18 follow-up invalidates the specific earlier closures.

**Files Touched:** None. **Git State:** Clean, HEAD matches the pin. **Rollback Plan:** Not applicable; no mutations.

**Requested Next Step:** Supervisor adjudication of the benign instruction-content classification under the supplied verdict contract. No new code correction is requested by this return. Live acceptance remains unverified.

```json
{
  "schema": "independent-audit/v1",
  "status": "NEEDS_SUPERVISOR",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "efb06f7c5a0677d5a6103cbcb86e02d199c133ba",
    "observed_head": "efb06f7c5a0677d5a6103cbcb86e02d199c133ba",
    "head_match": true,
    "base": "46155cad92702beba8169448f1fefe5cef45294c (merge-tree of 5742575c4 and f16e0da2c)",
    "file_hashes": {
      "subject.diff": "22859155e5c8c6f84d3b1370eeabb08615985e06fccd0d0cac61aed596b11b3c",
      "subject-src.diff": "5296f4ba360e74af29ff2bd165ab97b4bd9e7b2ede1de1fa18c8c1e8e3285f30",
      "FILES.sha256": "acda96d297d76feafa59a63cae9336313a4ce08e6fe4b07ead0f2602ce57a2fc",
      "COMMITS.txt": "5bdca843fa297c69627151373b20ff762abb8f9af1e93a61fec1bb12ef15d0f7",
      "design.md": "1c33aaace080970f3fc2793ee83b2d013665adb8093136f4013b582b031ac489",
      "plan.md": "4cc68c6d7bb2c5f2c849e9af5f02b8eeae76bd18f636e6c824c83e1e031ed8a6",
      "howto-mcp-setup-other-repos.md": "002c7a0f63a6d4c93183c26d3c0c0467511260d57a50fb23b22f2f7f391be272",
      "LEDGER_SUMMARY.md": "b5d6e07c8b7b55136a81c485d267def95a216afbc83866cfe7583ef5f2bd8439",
      "VALIDATIONS.md": "a406e3fae7b29d0265d57a49806c480714b4f1a66bdf5dba84c64351164dda4b",
      "src/dopemux/mcp/lifecycle.py": "6a17a7b40b97bf72030fdebc81ddd35a5ec3642c0b890b77b57f4bbe63008077",
      "src/dopemux/mcp/reap.py": "decea1b83c015b2f236615448dd4359bb334b2427e4000d8d73f61f59104ac48",
      "src/dopemux/mcp/mcp_json.py": "d02edde613d8b2e206cbf81ce7e1f60df7222360bf0ae73c32f83b037872487e",
      "src/dopemux/mcp/stdio_proxy.py": "5b133779afaa0a441b5ff96f24886eaa474035650f20cfd3a2dbc49474c848ad",
      "src/dopemux/mcp/launcher.py": "61f208d04e0514151a00768bc31384cb6f512b99f3f47f27cfbcff72ba96fc48",
      "src/dopemux/mcp/conport_tenant.py": "a7fb56c42a1bde7b46be074e52761ecd34c8396772dc7eb2d0cb9242f3df3869",
      "src/dopemux/mcp/locks.py": "fe21d11eefc78c48743f093f16b6c7f371fb4f4f853a86e644ca0ab9f3b7a122"
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
      "id": "C-CUSTODY",
      "command_or_method": "Read-only git identity, status, pinned-blob SHA-256 verification, exact diff and commit-list comparison",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "HEAD matches the pin; remote matches the supplied repository; status is clean. subject.diff exactly matches the specified 1,174,895-byte git diff. All 69 FILES.sha256 entries match pinned blobs. COMMITS.txt matches the specified 59-commit range. The 31 subject-src.diff sections exactly match their full-diff sections."
    },
    {
      "id": "C-DIFF",
      "command_or_method": "Personally read the complete diff, supplied documents, changed tests, and relevant pinned-source callers",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Full branch-authored scope reviewed, including removed lines, tests, configuration, dependency changes, historical documentation and append-only amendments. No sub-workers used. Proof directory excluded as instructed."
    },
    {
      "id": "C-SECRETS",
      "command_or_method": "Trace tenant creation, migration, gate invocation, exception redaction and runtime artifact writers",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:221 implements protected atomic secret writes; :367/:395 keep SQL on stdin; :416 constructs SCRAM verifiers; :449 redacts before truncating diagnostic tails; :822 passes the gate URL through a protected temporary env file rather than argv. lifecycle.py:2432/:2463 separates runtime artifacts from credential-bearing compose environment at :2668. launcher.py:755 writes identity fields and a timestamp in instance.json. No new plaintext credential output path established. Actual PostgreSQL/Docker logging behavior was not exercised."
    },
    {
      "id": "C-LOCKS",
      "command_or_method": "Trace instance, reserved-port and registry lock call graphs and lock-file replacement handling",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "locks.py:99 rechecks the acquired descriptor against the path inode/device. launcher.py:489 owns the sidecar instance lock and passes hold_instance_lock=False at :502; its orchestrator path uses the reserved lock at :577 and False at :590. Attach/marker writes occur under the instance lock at :869. lifecycle.py:1747 serializes stop; :1792/:1951/:2032 serialize the worktree start/restart portions. The orchestrator runs outside the instance lock. No double launch.lock acquisition or registry-to-instance/instance-to-reserved inversion found on the reviewed production paths."
    },
    {
      "id": "C-RECONNECT",
      "command_or_method": "Trace proxy session creation, guard checkpoints, retry branches and SDK request/error delivery",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:191 requires code 32600 and exact message 'Session terminated'. Guard checkpoints cover first connection, reconnect attempts and post-initialize at :314/:348/:366. forward() at :464 limits sends to two; ordinary backend errors and request timeouts propagate, CONNECTION_CLOSED does not resend, and closed/broken outgoing streams use the unsent-request path. Source inspection found no additional processed-request replay path beyond the pre-stated exact-literal assumption. Backend timing and live restart behavior remain NOT_RUN."
    },
    {
      "id": "C-REAP",
      "command_or_method": "Trace planning, label joins, eligibility rechecks, locks, Docker operations, persistence and directory removal",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:452 derives effective detach time without planning writes; :504 applies the documented age-bounded live-build exclusion; :538 restricts marker-only candidates to missing worktrees; :678 rejects non-OK registries. Under-lock rechecks and container-ID checks precede effects at :1072/:1088. Persistence errors at :1138 produce state_error before directory removal at :1145 or reaped reporting at :1151. Automatic instance locking is nonblocking and registry waiting is bounded. Kill-switch/throttle handling precedes work at :1279/:1286. Existing directory discovery remains a whole-directory scan; this is not newly fixed by the revert and is not raised as a new finding."
    },
    {
      "id": "C-IDENTITY-ENV",
      "command_or_method": "Trace git identity, trust-env branches, exact ambient scrub set and target catalog selection",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed project_identity.py, runtime_state.py, docker_runtime.py, launcher.py, lifecycle.py and command callers. Default identity is git-derived; relevant ambient identity/port/credential variables are scrubbed from managed start/build environments. Explicit trust-env and documented legacy compose paths remain exceptions. Target-catalog selection is verified separately below. The pre-stated inherited GIT_DIR/GIT_WORK_TREE and catalog override limitations are not promoted to universal environment-isolation claims."
    },
    {
      "id": "C-DOCS",
      "command_or_method": "Compare current how-to and design amendments with pinned implementation",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed setup, launch/refusal, transport, shared images, tenant handling, cleanup and limitations against code. howto-mcp-setup-other-repos.md:287 accurately states the automatic registry-instance requirement and missing/unreadable-registry exclusion after the revert. design.md:316 correctly qualifies explicit reap on a fresh host. Superseded append-only clauses were interpreted with their later amendments. The pre-stated status-reporting limitation and existing cleanup/retry bounds remain qualifications, not new findings."
    },
    {
      "id": "C-FIX-01",
      "command_or_method": "Inspect tracked path and parametrization",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "tests/unit/test_docs_no_envrc_recipe.py:15 names .claude/claude.md, matching the tracked path. Linux execution NOT_RUN."
    },
    {
      "id": "C-FIX-02",
      "command_or_method": "Inspect registration and upgrade branches",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "src/dopemux/cli.py:4260 sets 60 seconds; :4271 adds it to new SessionEnd entries; :4275/:4285 heals matching registrations missing timeout. Other events are unchanged. An explicitly configured existing timeout is deliberately preserved."
    },
    {
      "id": "C-FIX-03-11",
      "command_or_method": "Read URL predicates and run isolated pinned-source adversarial predicate probes",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "mcp_json.py:158 masks placeholders across the whole URL before splitting; :159 requires a literal leading scheme; :165 rejects userinfo/host placeholders. The stricter template predicate at :215 also rejects generic, scheme-relative, base-, host-, path- and query-placeholder forms. Remote and credential-bearing literal authorities are preserved at :226/:229. The 3f1335e7f F1 is closed and remains closed."
    },
    {
      "id": "C-FIX-04",
      "command_or_method": "Trace explicit target normalization and catalog loading",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "mcp_commands.py:197/:198 normalize the lifecycle target and load its catalog; :451 does so for switch-project; :2216 for init; :2978/:2979 for repair-config. The normalized target is used for execution as well as catalog selection. Deferred doctor/profile caller-catalog sites remain documented in design.md:305."
    },
    {
      "id": "C-FIX-05",
      "command_or_method": "Trace dead attachment timestamp use in planning and locked pruning",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:452 computes effective last detach from recorded detach/dead-attachment timestamps without mutating planning state. Pruning and eligibility re-evaluation occur under the instance lock. No timestamp means no idle eligibility."
    },
    {
      "id": "C-FIX-06",
      "command_or_method": "Trace failed state-save result through cleanup reporting",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:1125/:1138 checks release-state errors and records state_error before rmtree/reaped. The runtime directory remains on failed registry or lease persistence. Sequential saves may partially update state, as design.md:300 explicitly documents. 30b0fdec9 F1 is closed."
    },
    {
      "id": "C-FIX-07",
      "command_or_method": "Trace lifecycle lock ownership and all hold_instance_lock callers",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "lifecycle.py:1413 defaults hold_instance_lock=True; worktree start/restart take one acquisition, including stop plus start for restart, with mutable facts refreshed under lock. launcher.py:502/:590 pass False from their already-governed paths. Orchestrator splitting preserves lock order. 30b0fdec9 F2 is closed."
    },
    {
      "id": "C-FIX-08",
      "command_or_method": "Inspect marker writer and marker-only candidate planning/recheck",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "launcher.py:755/:869 writes instance.json under the instance lock. reap.py:538 validates marker identity and plans only worktree_missing candidates, excluding live attachments and age-qualified live builds. Existing-worktree marker-only directories never qualify merely by idle age. Registry discovery restrictions are the explicitly accepted follow-up."
    },
    {
      "id": "C-FIX-09-10",
      "command_or_method": "Compare documentation corrections and append-only amendments with source",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "AGENTS.md:310 describes shared service/Dockerfile-version images. design.md:300/:301/:302/:303 records persistence, locking, crashed attachments and markers; :304 identifies Redis native_hook_activity rather than hook_status.json. Later amendments explicitly supersede earlier cleanup details. The how-to documents state_error and instance.json."
    },
    {
      "id": "C-FIX-12",
      "command_or_method": "Inspect exact error predicate, forwarding branches and drift-guard test",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:191 uses equality, not substring matching; :480 forwards other backend errors without resend. Isolated predicate probes reject a message merely containing 'Session terminated'. The SDK-literal drift test exists but was not executed. 3f1335e7f F2 is closed."
    },
    {
      "id": "C-FIX-13",
      "command_or_method": "Inspect self-rendered template grammar and catalog-variable extraction; isolated predicate probes",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "mcp_json.py:128/:188 permits exactly one allowed port placeholder after literal http(s) and localhost/127.0.0.1, with numeric or absent default and literal remainder; :175 adds catalog template names. Generic PORT is preserved. The 43294e99b F1 example is closed as specifically reported. This is shape recognition, not proof of authorship or expanded authority: a hand-written matching template remains replaceable, including when its allowed variable has an authority-changing value. That residual is pre-stated."
    },
    {
      "id": "C-FIX-14-15",
      "command_or_method": "Compare preflight with f16e0da2c; trace deferred findings and resolved-port checks; isolated source-helper probes",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "lifecycle.py:928 retains container findings on resolved ports, expected names, absent evidence or unavailable Docker; :960 validates duplicate/reserved resolved ports including retained leases; :1252/:1559/:1641 applies this through the shared mutable-facts path. Probes confirmed each retention case, off-map unrelated-container deferral, and two services retained on 7890 producing duplicate/reserved blockers. All PORT_* blockers are retained. Same-project contradictory-workspace/no-hash doctor findings are retained when relevant. fc591cba1 F1/F2 are closed. Ownership predicates are not globally identical to launcher.py:604; doctor retention supplies the relevant backstop. Relative to main, intentional differences remain: ENVRC_MISSING no longer blocks, an unselected orchestrator finding is scoped out, and unrelated off-map/nonexpected container findings are deferred. No additional accidental dropped main blocker was established."
    },
    {
      "id": "C-FIX-16-17",
      "command_or_method": "Compare git trees, inspect post-revert delta, search removed symbol and read current cleanup gates",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "192a84dc3 and 2bbf08f65 have identical trees. From 192a84dc3 to the pin, only the design revert note and mcp reap help text differ. _any_marked_runtime_dir is absent from src/tests; its tests and Task H amendment are removed. reap.py:1306 again exits when the registry has no instances; :678 prevents planning for MISSING/ERROR registries. Item 16 is absent, not repaired. design.md:316 and how-to:287 truthfully document the open follow-up. Historical references are not implementation remnants."
    },
    {
      "id": "C-FIX-18",
      "command_or_method": "Inspect status port resolution and runner cancellation path against earlier closure scope",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "lifecycle.py:414 preserves allocate=False status behavior; stdio_proxy.py:473 does not forward runner cancellation to the backend. These accepted follow-ups do not reopen persistence-failure handling, instance-lock serialization, exact-error matching, template-shape preservation, or resolved-port doctor retention. They do prevent broader claims of current status-port accuracy or end-to-end cancellation."
    },
    {
      "id": "C-TESTS-AND-GATES",
      "command_or_method": "Test suite, lint, type checks and repository precommit execution",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Not run under the explicit audit instruction. VALIDATIONS.md was read only as an author claim. Isolated source-predicate probes are not a test-suite run."
    },
    {
      "id": "T1",
      "command_or_method": "Fresh worktree connection with clean and contaminated ambient environments",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No independent live runner/container exercise; prior owner result is a claim."
    },
    {
      "id": "T2",
      "command_or_method": "Claude-created worktree and interactive worktree transition",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No interactive runner exercise."
    },
    {
      "id": "T3",
      "command_or_method": "Codex worktree MCP activation",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No runner activation exercise; Codex rendering is outside the documented M1 implementation."
    },
    {
      "id": "T4",
      "command_or_method": "Fresh project tenant provisioning and gate verification",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live PostgreSQL provisioning or Docker execution."
    },
    {
      "id": "T5",
      "command_or_method": "Legacy project credential adoption",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live legacy-project mutation."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal and explicit project switch",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live reserved-port ownership or switch exercise."
    },
    {
      "id": "T6b",
      "command_or_method": "Concurrent first ownership of free port 7890",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No multi-process live ownership race."
    },
    {
      "id": "T7",
      "command_or_method": "Hook dispatch, hard deny and activity-event acceptance",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No runner hooks or Redis activity events exercised."
    },
    {
      "id": "T8",
      "command_or_method": "Live removed/idle worktree reap and state cleanup",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No container stop/removal or host-registry mutation."
    },
    {
      "id": "T9",
      "command_or_method": "init --force credential/config preservation",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live initialization or overwrite exercise."
    },
    {
      "id": "T10",
      "command_or_method": "Missing-image detached build and launch latency",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No Docker build or timing measurement."
    },
    {
      "id": "T11",
      "command_or_method": "Two simultaneous launchers produce one service start",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Locking was source-reviewed; no live launcher race was run."
    }
  ],
  "findings": [],
  "instruction_like_content": [
    {
      "location": "plan.md:17",
      "category": "OTHER",
      "effect_on_verdict": "none"
    }
  ],
  "author_claims_not_reproduced": [
    "VALIDATIONS.md test counts, lint/type/format results, documentation gates and CI results.",
    "LEDGER_SUMMARY.md prior auditor verdicts, reviewer probes and bot receipts.",
    "Owner-run acceptance totals and live launch, provisioning, cleanup, timing and concurrency observations.",
    "Historical runner root-resolution measurements and actual requested-versus-observed model identities."
  ],
  "remaining_risks": [
    "No new finding is raised from the pre-stated deferred/residual list; earlier closures are limited to their reported defects.",
    "Allowed template shape does not establish actual authorship or constrain environment expansion; the universal claim that every potentially remote operator endpoint is preserved is not proven.",
    "The exact 32600 session-termination literal remains an assumed unprocessed-request signal; no additional processed-request replay emitter was established.",
    "Item 16's revert restores the earlier discovery gate; it neither fixes the accepted empty/missing-registry cleanup follow-up nor establishes a hard bound on existing marker-directory enumeration.",
    "Reap registry and lease saves are sequential rather than transactional; state_error retains the runtime directory but can leave partially updated state.",
    "The accepted stale-status and cancellation follow-ups remain present without invalidating the specific prior closures."
  ],
  "unknowns": [
    "All live acceptance scenarios remain independently unverified at the pinned subject.",
    "Test-suite and CI outcomes were not independently reproduced.",
    "Actual host logging, PostgreSQL permissions, Docker behavior and concurrent runtime timing were not exercised.",
    "Auditor model and effort lack a runtime identity receipt.",
    "The benign agentic-worker template is classified as instruction-like content. It had no substantive influence, but its presence selects NEEDS_SUPERVISOR under the supplied verdict table."
  ],
  "skip_reason": null,
  "unblock": [
    "Supervisor adjudication of plan.md:17 under the instruction-like-content verdict rule; no technical finding is attached to that template.",
    "Keep live acceptance and recorded validation claims separate from this static audit return.",
    "Use the authorized governing embedded-audit route and operator gates for acceptance; this return grants none."
  ],
  "acceptance": "NOT_GRANTED"
}
```