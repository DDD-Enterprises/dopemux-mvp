END_OF_PROMPT 4ed10054-43294e99

**Verdict: FAIL — one new medium finding. Acceptance NOT_GRANTED.**

**Change Summary / Authority Used:** Read-only audit of `43294e99bd1982a9867a7e5d15edf919e9faaf26` against the supplied synthetic base, excluding `proof/`. I used the pinned source, supplied materials, repository instructions, and your verdict contract. No delegation or edits.

**Analysis Performed:** Read the full diff and traced secrets handling, lifecycle and reaper locks, reconnects, ownership guards, configuration repair, and documentation. Both findings from `30b0fdec9` are **closed by static inspection**. Both reported findings from `3f1335e7f` are also **closed as specifically reported**; the broader endpoint-preservation guarantee still has the following hole.

**F1 — medium — `src/dopemux/mcp/mcp_json.py:170`**

A placeholder syntactically occupying the port position can still select a remote, credential-bearing authority when expanded:

```text
Stored URL:       http://localhost:${PORT:-3005}/sse
Operator PORT:    3005@remote.example
Expanded URL:     http://localhost:3005@remote.example/sse
Expanded host:    remote.example
```

The pinned predicate returns **True** for the stored URL and **False** for the expanded literal. It evaluates the default rather than establishing that substitutions remain port-valued (`mcp_json.py:186`). Consequently, the planner bypasses preservation at `:291` and removes the URL while converting the entry to a launcher at `:332`.

I reproduced these predicate results using AST-selected pure functions from the pinned file and Python’s URL parser. This establishes the classification defect; I did not change configuration or observe an actual remote endpoint being replaced.

**Validation Performed:** **PASS:** exact diff comparison, all 69 listed file hashes, all 52 commit-list entries, supplied source-document copies, clean Git status, and `git diff --check`. **FAIL:** endpoint-preservation probe above. **NOT_RUN:** test suite, hooks execution, lint/type/format tools, and every live acceptance item.

**Remaining Uncertainty / Risk:** Exact matching fixes the replay substring bug, but an identical backend-originated `32600 / "Session terminated"` error remains indistinguishable from the SDK-generated error and would trigger a resend. I found no such producer in the searched pinned backend sources; this remains a conditional risk, not an observed duplicate write. Reaper build protection is age-bounded, and automatic registry acquisition permits a bounded wait; the unqualified “never while a build runs” and “never wait” descriptions require those qualifications.

**Files Touched / Git State / Rollback Plan:** None. Local HEAD and branch match the subject; worktree is clean. No rollback is needed.

**Requested Next Step:** Fix F1 by preserving unresolved authority substitutions unless their resolved values are demonstrably constrained to ports. Add a regression covering the example above, preserve the intended catalog migration behavior explicitly, then re-freeze for review. This return does not grant formal embedded-audit acceptance.

```json
{
  "schema": "independent-audit/v1",
  "status": "FAIL",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "43294e99bd1982a9867a7e5d15edf919e9faaf26",
    "observed_head": "43294e99bd1982a9867a7e5d15edf919e9faaf26",
    "head_match": true,
    "base": "46155cad92702beba8169448f1fefe5cef45294c (merge-tree of 5742575c4 and f16e0da2c)",
    "file_hashes": {
      "subject.diff": "20c8aacaf5098847dc03d3872d654d6bdff72d53c7067c7757eeaf920078fdd7",
      "FILES.sha256": "b13f6e135181bb81cdb41efa64b437312ebf62c73ed5c538715beaa950f0ddf4",
      "COMMITS.txt": "94a3f6f94f97ce346c0a0b775d151386666c3588522db08709cbc86717a57195",
      "src/dopemux/mcp/mcp_json.py": "911cfd3912ef4b9269e6e5ae97ad1deefa0d3665b8db9000f1cb443a6f0e8a6d",
      "src/dopemux/mcp/stdio_proxy.py": "5b133779afaa0a441b5ff96f24886eaa474035650f20cfd3a2dbc49474c848ad",
      "src/dopemux/mcp/reap.py": "decea1b83c015b2f236615448dd4359bb334b2427e4000d8d73f61f59104ac48",
      "src/dopemux/mcp/launcher.py": "61f208d04e0514151a00768bc31384cb6f512b99f3f47f27cfbcff72ba96fc48",
      "src/dopemux/mcp/lifecycle.py": "95dd7049aebc96ea5544d04df603d33249c1cc66996ebbbd88a37e73a3e9dc22"
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
      "id": "CUSTODY",
      "command_or_method": "Read-only Git identity, byte comparisons, SHA-256 verification and commit-list comparison",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Local origin matches the stated repository. subject.diff exactly equals the prescribed Git diff. All 69 FILES.sha256 entries match pinned blobs. COMMITS.txt exactly matches the 52 branch-authored commits. design.md, plan.md and the how-to match their pinned source bytes."
    },
    {
      "id": "FULL_DIFF",
      "command_or_method": "Read subject.diff in full and inspect relevant pinned callers and consumers",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed all 25390 lines, including source, configuration, hooks, documentation, tests and lockfile changes. Historical reports and validation records were treated as claims."
    },
    {
      "id": "SECRETS_STATIC",
      "command_or_method": "Trace credential creation, subprocess arguments, stdin, artifacts and error output",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:221 creates private atomic files; :367 and :381 keep SQL on stdin; :416 constructs SCRAM verifiers; :437 and :449 redact before truncation; :822 uses a private temporary docker exec --env-file. docker_runtime.py:410 filters secret-bearing environment fields; :725 writes runtime artifacts. lifecycle.py:2483 confines tenant credentials to compose execution. launcher.py:329 scrubs refusal text; :741 and :763 restrict instance.json to identity and timestamp. Static inspection only."
    },
    {
      "id": "LOCKS_STATIC",
      "command_or_method": "Trace lock acquisitions through launcher, lifecycle, switching, reaping and registry persistence",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "locks.py:99 rechecks device/inode after flock acquisition. Its :15 rule keeps reserved-port and instance locks unnested. lifecycle.py:1584 serializes worktree operations; launcher.py:502 and :590 disable duplicate lifecycle instance locking. Reap takes instance before registry at reap.py:1072 and :1036. No reviewed path acquires registry then instance, instance then reserved, or launch.lock twice."
    },
    {
      "id": "RECONNECT_STATIC",
      "command_or_method": "Trace guards, session handoff, retry predicates, in-flight cancellation and reconnect budgets",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:350 checks ownership before connecting and :368 checks again after initialize before exposing the session. :382 implements bounded backoff. :464 caps sends; ordinary backend errors propagate, CONNECTION_CLOSED and cancelled in-flight requests are not resent. Exact-signature provenance remains a residual risk; this is not a universal exactly-once guarantee."
    },
    {
      "id": "REAP_STATIC",
      "command_or_method": "Trace candidate construction, under-lock revalidation, Docker inspection, state release and directory deletion",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:656 joins managed worktree containers to registry identity; :538 handles marker-only missing worktrees; :406 rechecks eligibility; :934 reinspects the pair; :1136 and :1142 preserve runtime directories on registry_busy/state_error. :852 excludes orchestrator state. Automatic kill-switch and bounded paths are at :290 and :1247. Build exclusion at :504 is explicitly age-bounded, not unconditional protection of every living build process."
    },
    {
      "id": "IDENTITY_ENV_STATIC",
      "command_or_method": "Trace git identity, ambient scrubbing and target-catalog selection",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "runtime_state.py:109 requires trust_env for environment participation. docker_runtime.py:53 defines the shared scrub set; launcher.py:283 additionally scrubs catalog port variables. Target catalog sites are mcp_commands.py:198, :450, :2215 and :2977. Deferred doctor/profile catalog behavior and legacy cwd-compose commands remain outside this claim."
    },
    {
      "id": "DOCS_STATIC",
      "command_or_method": "Compare the complete supplied how-to and append-only amendments with pinned implementation",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Core launcher, tenant, state_error, marker, target-repo, shared-image and rollback descriptions align with the reviewed paths. Qualifications: automatic registry waits are bounded rather than absent; live-build protection expires with the build budget; Codex rendering and Copilot operation are not verified. External runner behavior and timing statements remain author claims."
    },
    {
      "id": "DEFERRED_REVIEW",
      "command_or_method": "Compare candidate concerns with LEDGER_SUMMARY.md deferred items and rulings",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "No listed deferred item is re-raised as a finding. F1 concerns unresolved authority substitution during endpoint replacement, distinct from the reported delimiter-masking cases."
    },
    {
      "id": "FIX_01",
      "command_or_method": "Inspect documentation-test parameter",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "tests/unit/test_docs_no_envrc_recipe.py:15 names .claude/claude.md with the tracked casing. Linux test execution NOT_RUN."
    },
    {
      "id": "FIX_02",
      "command_or_method": "Inspect native-hooks registration branches",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "src/dopemux/cli.py:4260 sets 60 seconds; :4271 adds it to new SessionEnd hooks; :4275 repairs existing matching hooks missing timeout. Explicit operator timeout values are preserved, and other events receive no added timeout."
    },
    {
      "id": "FIX_03",
      "command_or_method": "Inspect URL preservation policy and probe unresolved authority substitution",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "mcp_json.py:174 removes the former blanket template bypass and protects literal remote/userinfo endpoints. However, :170 excludes port-position placeholders from the operator-selection guard, and :186 substitutes their defaults. F1 demonstrates that an operator-selected remote endpoint can still be replaced."
    },
    {
      "id": "FIX_04",
      "command_or_method": "Inspect --repo resolution before catalog loading",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "mcp_commands.py:198 loads the lifecycle target catalog, :450 the switch-project target, :2215 the init target, and :2977 the repair-config target. The separately deferred doctor/profile sites are not represented as fixed."
    },
    {
      "id": "FIX_05",
      "command_or_method": "Trace dead-attachment idle calculation and pruning",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:452 computes the newest last_detach/dead-record mtime without writes. Pruning is performed on the locked apply path. The recorded attach time is a surrogate for an unknown crash time, as documented."
    },
    {
      "id": "FIX_06_30b0fdec9_F1",
      "command_or_method": "Trace failed registry/lease persistence through reap reporting and cleanup",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "CLOSED by static inspection. reap.py:1009 returns persistence errors; :1138 records state_error and returns before rmtree at :1145 or reaped.append at :1151. Partial cross-file persistence remains documented."
    },
    {
      "id": "FIX_07_30b0fdec9_F2",
      "command_or_method": "Trace CLI start/restart serialization and launcher bypass",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "CLOSED by static inspection. lifecycle.py:1275 defaults hold_instance_lock=True; :1584 protects worktree service operations and the restart stop/start sequence, with mutable-fact refresh. Orchestrator work is split outside that lock. launcher.py:502 and :590 pass False to avoid duplicate or inverted locking."
    },
    {
      "id": "FIX_08",
      "command_or_method": "Trace marker writing and marker-only candidate planning/apply",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "launcher.py:741 defines identity-only fields; :763 writes the marker atomically with mode 0600; :869 holds the instance lock at attach. reap.py:538 admits marker-only worktree_missing candidates, not idle-only directories. :504 excludes live builds within the configured build budget; :934 reinspects containers before release."
    },
    {
      "id": "FIX_09",
      "command_or_method": "Inspect AGENTS image wording against image-key implementation",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "AGENTS.md:310 states the shared service/Dockerfile image rule and checkout-path contribution, replacing the per-worktree build claim."
    },
    {
      "id": "FIX_10",
      "command_or_method": "Inspect amendments, reap documentation and hook activity writer",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "claudedocs/mcp-just-works-design-2026-11-05.md:300-304 records state-error, locking, crashed-attachment, marker and T7 amendments. native_hooks.py:101 defines native_hook_activity; :147 gates event emission. The how-to documents state_error and instance.json. No live Redis evidence was reproduced."
    },
    {
      "id": "FIX_11_3f1335e7f_F1",
      "command_or_method": "Inspect full-URL masking and anchored scheme handling; run isolated pure-predicate probes",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "CLOSED for the reported delimiter/scheme cases. mcp_json.py:157 masks before splitting; :158 requires a literal leading scheme; :159 rejects templated no-literal-scheme forms; :162 splits only afterward. Probed host-default delimiter, templated base with later ://, templated scheme and scheme-relative URLs all return False. Scheme-relative rejection is conservative and intentional. New F1 is a different unresolved-value case."
    },
    {
      "id": "FIX_12_3f1335e7f_F2",
      "command_or_method": "Inspect exact predicate, forwarding branch and regression/drift-guard assertions",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "CLOSED for the reported substring bug. stdio_proxy.py:202 requires code 32600 and exactly Session terminated; :488 propagates nonmatching backend errors. tests/unit/test_mcp_stdio_proxy.py:518 asserts the committed-write lookalike is sent once; :531 contains the SDK literal drift guard. Tests were read, not run. The drift guard checks source substrings and may skip when the module is unavailable."
    },
    {
      "id": "ENDPOINT_SUBSTITUTION_PROBE",
      "command_or_method": "AST-select pinned pure URL predicates; evaluate stored template and a synthetic expanded literal with urllib.parse",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "http://localhost:${PORT:-3005}/sse is repairable=True. Substituting PORT=3005@remote.example yields hostname remote.example and literal repairable=False. The planner uses the former classification at mcp_json.py:288 and deletes the URL at :335. No project imports, filesystem writes, network calls or test-suite execution."
    },
    {
      "id": "FINAL_GIT_CHECK",
      "command_or_method": "git diff --check 46155cad92702beba8169448f1fefe5cef45294c 43294e99bd1982a9867a7e5d15edf919e9faaf26 -- . ':(exclude)proof'; git status --short",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Both commands produced no findings; worktree remained clean."
    },
    {
      "id": "TESTS_AND_TOOL_GATES",
      "command_or_method": "Test suite, hooks workflow, lint, type checking, formatting and executable documentation validators",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Not executed under the supplied read-only audit scope. VALIDATIONS.md results are author claims, not reproduced checks."
    },
    {
      "id": "T1",
      "command_or_method": "Fresh git worktree session, clean and polluted environments",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Requires owner-host runner and Docker execution; static launcher/identity paths reviewed only."
    },
    {
      "id": "T2",
      "command_or_method": "Claude-created worktree session",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live Claude worktree creation or child-cwd measurement."
    },
    {
      "id": "T3",
      "command_or_method": "Concurrent Codex worktree session",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Codex rendering is explicitly outside M1; no runtime qualification performed."
    },
    {
      "id": "T4",
      "command_or_method": "New project init, tenant provisioning and isolation",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live Postgres, Docker, credential creation or tenant-isolation exercise."
    },
    {
      "id": "T5",
      "command_or_method": "Existing dNh_CRM tenant adoption and data preservation",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No access to or inspection of the live tenant or its data."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal and explicit project switch",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Owner-verdict and switch paths reviewed statically; no live container identity or takeover exercise."
    },
    {
      "id": "T6b",
      "command_or_method": "Free reserved port and concurrent orchestrator launches",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Reserved-lock path reviewed; no live launch race."
    },
    {
      "id": "T7",
      "command_or_method": "Native hooks, red-lane denial and Redis activity evidence",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Dispatcher and event paths reviewed; hooks and Redis were not executed or queried."
    },
    {
      "id": "T8",
      "command_or_method": "Removed-worktree cleanup with reap --apply",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Planner and apply paths reviewed; no live stop, remove, lease release or directory cleanup."
    },
    {
      "id": "T9",
      "command_or_method": "init --force --repo target isolation",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Target-root and catalog flow reviewed; no configuration-writing command executed."
    },
    {
      "id": "T10",
      "command_or_method": "Missing-image detached build and reconnect timing",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Build/refusal code reviewed; no image deletion, build or timing measurement."
    },
    {
      "id": "T11",
      "command_or_method": "Two launchers within 100 ms, exactly one start",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Instance-lock serialization reviewed; no concurrent live launch experiment."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "medium",
      "location": "src/dopemux/mcp/mcp_json.py:170",
      "summary": "An unresolved port-position placeholder can select a remote authority, yet configuration repair treats its local default as authority to replace the endpoint.",
      "evidence": "The pinned pure predicate returns True for http://localhost:${PORT:-3005}/sse. With operator PORT=3005@remote.example, string expansion yields http://localhost:3005@remote.example/sse, whose hostname is remote.example and whose literal predicate result is False. Lines 170 and 186 respectively exclude this placeholder from host protection and evaluate its default. plan_mcp_json_repairs uses that classification at line 288, bypasses preservation at line 291 and removes the URL at lines 332-337. The predicate discrepancy was reproduced locally without project imports or writes; the planner consequence was traced statically."
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
    "VALIDATIONS.md: make test-fast reported 4476 passed and 2 skipped at the pinned SHA.",
    "VALIDATIONS.md: hooks workflow reported 12 passed; documentation, lint, type and formatting comparisons reported no new gated failures.",
    "VALIDATIONS.md and LEDGER_SUMMARY.md: earlier live acceptance reported PASS 7, PARTIAL 1 and NOT_RUN 4; these results were not independently reproduced.",
    "Controller records of live smoke, Docker ownership, image builds, hook events, tenant behavior and runner cwd behavior.",
    "PR #1503 CI, review-bot receipts, prior independent-route verdicts and remote publication state."
  ],
  "remaining_risks": [
    "An actual backend error with exactly code 32600 and message Session terminated is indistinguishable from the SDK-generated error and triggers resend. No such producer was found in the searched pinned backend sources; actual duplicate processing was not demonstrated.",
    "Permitted port-template substitutions are not constrained to numeric ports by the repair predicate; F1 prevents accepting the broader operator-endpoint preservation claim.",
    "Build exclusion uses PID liveness plus build-file age within build_timeout_secs. A still-running process older than that budget is not protected by _live_build.",
    "Automatic instance locking is nonblocking, but registry persistence may wait up to the smaller of two seconds and the remaining deadline.",
    "Registry and lease saves are sequential, not a cross-file transaction. state_error preserves recovery artifacts but can leave a partial update.",
    "The SDK drift guard is a source-substring assertion, not a behavioral or provenance guarantee.",
    "Existing deferred constraints, including shared Redis isolation, image keys excluding sidecar source changes, Codex rendering, Copilot qualification and post-check ownership races, remain unchanged."
  ],
  "unknowns": [
    "All owner-host acceptance outcomes at the pinned SHA.",
    "Runtime auditor model and effort; no identifying runtime receipt was available.",
    "Current remote PR head, CI, reviews and acceptance state; observed_head is the local pinned checkout.",
    "Whether a deployed backend can emit the exact retry-triggering error after processing a request.",
    "Actual client environment values and expansion during operator use; F1 uses an explicit synthetic operator value.",
    "Live filesystem permissions, credential exposure, Docker labels, service health and timing were not measured."
  ],
  "skip_reason": null,
  "unblock": [
    "Preserve unresolved authority placeholders unless their resolved substitutions are proven to remain port-valued; do not use a local default alone as proof of a local operator-selected endpoint.",
    "Add regression coverage for the F1 template and remote-authority substitution, while explicitly preserving or revising the intended catalog migration behavior.",
    "Run the focused configuration-repair validations, freeze the resulting substantive head and obtain the required independent review through the governing route.",
    "Treat plan.md:17 as executor-template data; it was recorded but not followed, and it did not cause this FAIL verdict."
  ],
  "acceptance": "NOT_GRANTED"
}
```