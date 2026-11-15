END_OF_PROMPT a16ed92f-3f1335e7

**Change Summary:** **FAIL** — two medium findings in the pinned branch-authored range. No files changed.

**Authority Used:** Your pinned audit scope, repository instructions, independent-audit skill, and the supplied verdict contract. This return does not grant repository acceptance or constitute an accepted embedded-audit proof.

**Analysis Performed:** Read the full diff and supplied materials; traced credential handling, lifecycle locks, reconnect/replay, reaping, environment isolation, target-catalog selection, and documentation. No delegation.

**Findings**

1. **F1 — medium — `src/dopemux/mcp/mcp_json.py:140`**  
   Cycle-2 fix 3 still permits replacement of operator-selected endpoints. The function splits the authority at `/`, `?`, and `#` **before** masking complete placeholders. A delimiter inside a placeholder’s default therefore defeats host-placeholder detection.

   Independently evaluated pinned code returned `True` for:
   ```
   http://${HOST:-localhost/path}/sse
   http://${HOST:-localhost?x}/sse
   http://${HOST:-localhost#x}/sse
   ```
   `HOST` can resolve to a remote endpoint. The repair planner consequently classifies the replacement as safe and removes the URL when constructing the launcher entry (`mcp_json.py:270`, `mcp_json.py:314`).

   **Unblock:** Parse complete placeholder tokens before splitting authority components, or conservatively preserve ambiguous templates. Add preservation cases covering these delimiters.

2. **F2 — medium — `src/dopemux/mcp/stdio_proxy.py:198`**  
   Session-termination detection uses substring matching. Code `32600` with message `"Not Session terminated; write already committed"` is therefore treated as proof that the request was rejected without processing.

   The pinned `forward` body then drops the session and resends (`stdio_proxy.py:475`). An independent in-memory fixture executed the simulated operation **twice**. This contradicts the function’s explicit requirement to forward nonmatching backend errors without replay (`stdio_proxy.py:193`).

   This demonstrates the conditional replay defect; it does **not** establish that a deployed backend has emitted that message.

   **Unblock:** Restrict recognition to the canonical SDK termination signal and verify that noncanonical messages containing the phrase are returned without resending.

**Previous Codex findings:** Both findings from `30b0fdec9` are **closed on static review**:

- Previous **F1:** `reap.py:1138` returns with `state_error` before runtime-directory removal or reporting “reaped.”
- Previous **F2:** `lifecycle.py:1624` selects the worktree lock, and `lifecycle.py:1788` holds one acquisition across restart’s stop/start. Launcher callers pass `hold_instance_lock=False` at `launcher.py:502` and `launcher.py:590`.

**Validation Performed**

- **PASS:** Exact HEAD, repository and branch; all 69 manifest file hashes; exact regenerated diff; all 50 commit identities/order; pinned document copies; `git diff --check`.
- **FAIL:** Endpoint-template preservation and conservative replay recognition.
- **NOT_RUN:** Test suite, lint/type checks, pre-commit hooks, SDK integration, Docker/Postgres operations, and every live acceptance item. Controller results remain claims.

**Remaining Uncertainty / Risk:** Live behavior and actual model identity remain unverified. No additional ledger-deferred item is promoted to a finding. Existing documented limitations remain unresolved; this audit does not accept their risk.

**Files Touched:** None. **Git State:** Clean `feat/mcp-just-works-m1` at the pinned SHA. **Rollback Plan:** None required for this read-only audit. **Requested Next Step:** Correct F1/F2, validate their negative cases, and freeze a successor subject for review.

```json
{
  "schema": "independent-audit/v1",
  "status": "FAIL",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "3f1335e7fdcf8165d4669195bfd521cafca13304",
    "observed_head": "3f1335e7fdcf8165d4669195bfd521cafca13304",
    "head_match": true,
    "base": "46155cad92702beba8169448f1fefe5cef45294c (merge-tree of 5742575c4 and f16e0da2c)",
    "file_hashes": {
      "subject.diff": "fb77bf887731e16edd3e060a5f1cbd86bb99462ac7b1ed0aba15c76351e29d71",
      "subject-src.diff": "1fb5d683d0e9b7c5a23a268f5a7e498911769b967df198bc9ccf1dfb685fdb54",
      "FILES.sha256": "3de6403c9ec4993051bec9b7a5a5d917b666199dee2ed1a672194a770d5a3c7a",
      "COMMITS.txt": "98f9958497d508b3834d45f9a1fc7f8101666c74fca0e3db272c470d8aa41c92",
      "design.md": "b380d466168323349b45154d2632b4638115e7e12e4ef85bf41aeaf9774558b6",
      "plan.md": "4cc68c6d7bb2c5f2c849e9af5f02b8eeae76bd18f636e6c824c83e1e031ed8a6",
      "howto-mcp-setup-other-repos.md": "002c7a0f63a6d4c93183c26d3c0c0467511260d57a50fb23b22f2f7f391be272",
      "LEDGER_SUMMARY.md": "2d538906e66d7c25d30feefb27073baa172a3910f1edfb3509c37c8ed8e159dd",
      "VALIDATIONS.md": "adac41e7375c33c0159c7807463c5a23c0440721b884dead839329fb5168fbca",
      "src/dopemux/mcp/mcp_json.py": "409ffe1a935a7c20b58699cc595c54a76fceb3d5110794f3e2a419e74eab5c02",
      "src/dopemux/mcp/stdio_proxy.py": "e5188be8e9a031bcccab808a48d301f46a5986fb716d1550912f5cf9052b3783",
      "src/dopemux/mcp/reap.py": "decea1b83c015b2f236615448dd4359bb334b2427e4000d8d73f61f59104ac48",
      "src/dopemux/mcp/lifecycle.py": "95dd7049aebc96ea5544d04df603d33249c1cc66996ebbbd88a37e73a3e9dc22",
      "src/dopemux/mcp/launcher.py": "61f208d04e0514151a00768bc31384cb6f512b99f3f47f27cfbcff72ba96fc48"
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
      "id": "C-PIN-CUSTODY",
      "command_or_method": "Read-only git identity/status checks; SHA-256 of all manifest entries against git show at the pin; regenerate branch diff; compare commit list and document aliases.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "HEAD, branch and remote match. Worktree clean. All 69 file hashes match. subject.diff matches the specified git diff byte-for-byte. COMMITS.txt matches all 50 commits in order. Design, plan and how-to aliases match pinned repository bytes."
    },
    {
      "id": "C-FULL-DIFF",
      "command_or_method": "Personally read the complete subject.diff and supplied audit materials.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Full branch-authored diff reviewed, including implementation, tests, configuration, hooks and documentation. proof/ excluded as specified. No delegated reading."
    },
    {
      "id": "C-DIFF-CHECK",
      "command_or_method": "git diff --check 46155cad92702beba8169448f1fefe5cef45294c 3f1335e7fdcf8165d4669195bfd521cafca13304 -- . ':(exclude)proof'",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "No whitespace errors reported."
    },
    {
      "id": "C-SECRETS",
      "command_or_method": "Static credential-source, argv, stdin, redaction, artifact and marker data-flow review.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:221 creates private atomic secret files; :381 sends SQL through stdin; :416 constructs SCRAM verifiers; :449 redacts before tail truncation; :831 supplies the gate URL through a private docker exec env-file. docker_runtime.py:404 filters secret-like mcp.env keys. lifecycle.py:2288 and :2483 separate operational artifacts from credential-bearing process environment. launcher.py:763 writes only fixed identity fields and a timestamp to instance.json. No new secret exposure found in the reviewed paths; live logs were not inspected."
    },
    {
      "id": "C-LOCKS",
      "command_or_method": "Static caller and lock-order trace across launcher, lifecycle, switch-project, registry persistence and reap.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "locks.py:99 checks descriptor/path inode identity after flock. The implemented rule at locks.py:8 is instance -> registry or reserved-port -> registry, with reserved-port and instance never nested. lifecycle.py:1624 separates orchestrator work from the instance-locked portion; :1643 refreshes mutable facts under the lock; :1788 holds restart stop/start together. launcher.py:869 releases attach locking before ensure_backend, and :502/:590 suppress lifecycle reacquisition. No reviewed path recursively acquires launch.lock or takes registry -> instance or instance -> reserved."
    },
    {
      "id": "C-RECONNECT",
      "command_or_method": "Static reconnect/guard/budget trace and in-memory execution of pinned AST-extracted termination predicate and forward method.",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "Guard checkpoints exist before initial connection, before reconnect and after initialize (stdio_proxy.py:343; launcher.py:644). Resend count, backoff and window controls are present. However stdio_proxy.py:198 accepts noncanonical messages containing 'Session terminated'; :475 then resends. The controlled fixture returned simulated_side_effects=2 and drops=1. See F2."
    },
    {
      "id": "C-REAP",
      "command_or_method": "Static planning, eligibility, locking, container-label join, reinspection, persistence and cleanup trace.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed managed/worktree scope and identity joins, orchestrator exclusions, dead-attach timestamps, under-lock eligibility and container-ID rechecks, bounded automatic operations, kill switches, state-only/marker-only recovery and locked/stale/registry_busy/state_error skips. reap.py:1125-1151 prevents removal or 'reaped' reporting after state-save failure. Build protection follows the amended alive-PID-within-build-budget definition, not an unlimited PID-liveness guarantee."
    },
    {
      "id": "C-IDENTITY-CATALOG",
      "command_or_method": "Static git identity, environment scrub and target-catalog caller trace.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "docker_runtime.py:53 lists identity, credential, port and container-name exports to scrub; launcher.py:283 applies the scrub with catalog port variables; mcp_commands.py:134 applies CLI scrubbing unless trust-env. Target-catalog sites are mcp_commands.py:198, :450, :2215 and :2977, plus launcher.py:860. Deferred doctor/profile and legacy cwd-compose surfaces remain outside the corrected sites."
    },
    {
      "id": "C-DOCS",
      "command_or_method": "Compare the pinned how-to and design amendments with implementation.",
      "exit_code": null,
      "bucket": "FAIL",
      "evidence": "Shared-image, target-catalog, state_error, marker, SIGKILL-idle and hook-evidence descriptions generally match the amended implementation. The conservative replay assurance in docs/02-how-to/mcp-setup-other-repos.md:354 is undermined by F2. No separate duplicate documentation finding is raised."
    },
    {
      "id": "C-PLAN-FOCUS",
      "command_or_method": "Trace plan.md:44 review-focus paths and inspect their test sources.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed git-toplevel/subdirectory normalization, resolved-path identity, non-git/unmanaged launcher refusal before Docker, corrupt-registry reap refusal, and malformed/missing-cwd hook handling. Test coverage was read as source, not executed."
    },
    {
      "id": "C-DEFERRED",
      "command_or_method": "Reconcile LEDGER_SUMMARY.md deferred entries with later amendments and pinned source.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "No additional deferred item is promoted to a finding. Historical entries superseded by later fixes were not treated as current defects. F1 and F2 are distinct from the listed accepted limitations."
    },
    {
      "id": "C2-01",
      "command_or_method": "Inspect Linux-sensitive documentation fixture path.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "tests/unit/test_docs_no_envrc_recipe.py:17 now names the tracked .claude/claude.md. Linux test execution NOT_RUN."
    },
    {
      "id": "C2-02",
      "command_or_method": "Inspect native-hooks registration branches.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "src/dopemux/cli.py:4260 sets 60 seconds; :4271 applies it to new SessionEnd hooks; :4275 fills missing timeouts in existing matching registrations. Explicit operator timeout values are preserved. Other events are unchanged."
    },
    {
      "id": "C2-03",
      "command_or_method": "Static URL-repair trace plus pure in-memory pinned-code counterexamples.",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "mcp_json.py:140-145 splits authority before masking complete placeholders. Defaults containing '/', '?' or '#' bypass host-placeholder preservation and are classified repairable. Real repair-planner execution with a controlled launcher-rendering seam removed the URL and marked the replacement safe. See F1."
    },
    {
      "id": "C2-04",
      "command_or_method": "Inspect target resolution and catalog-loading order.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "mcp_commands.py:198 lifecycle CLI, :450 switch-project, :2215 init and :2977 repair-config load the resolved target checkout's catalog. launcher.py:860 passes launch_root to catalog loading. Doctor/profile exceptions remain explicitly deferred."
    },
    {
      "id": "C2-05",
      "command_or_method": "Inspect idle planning and locked pruning.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:452 computes effective last-detach from last_detach and dead attach-record mtimes without mutation. Planning uses it; pruning and subsequent eligibility checks occur under the instance lock."
    },
    {
      "id": "C2-06-OLD-F1",
      "command_or_method": "Trace persistence-error return through cleanup.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Previous Codex F1 CLOSED on static evidence. reap.py:1125 collects save errors; :1138 records state_error and returns before :1145 rmtree and :1151 reaped append. Partial persistence remains possible and documented."
    },
    {
      "id": "C2-07-OLD-F2",
      "command_or_method": "Trace direct CLI start/restart lock scope and launcher suppression.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Previous Codex F2 CLOSED on static evidence. lifecycle.py:1275 defaults hold_instance_lock=True; :1624-1630 chooses the worktree lock; :1788-1807 encloses restart stop/start in one acquisition. launcher.py:502 and :590 pass False on already-coordinated paths. Orchestrator work remains outside the instance lock."
    },
    {
      "id": "C2-08",
      "command_or_method": "Inspect marker writer, candidate discovery and apply-time rechecks.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "launcher.py:763 writes an atomic 0600 identity-only marker and :869 invokes it under the attach lock. reap.py:544 requires a matching marker, missing worktree, absent registry/container pair, no live attachment and no live build under the amended budget definition. Marker-only candidates are never idle candidates; apply-time container reinspection prevents releasing a newly started pair."
    },
    {
      "id": "C2-09",
      "command_or_method": "Inspect corrected shared-image documentation.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "AGENTS.md:310-314 now describes sharing by service, dopemux checkout path and Dockerfile version; the stale per-worktree-build sentence is removed."
    },
    {
      "id": "C2-10",
      "command_or_method": "Compare cycle amendments and how-to text with pinned runtime.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "design.md:300 onward records persistence, locking, dead-attach and marker changes with later supersessions. design.md:304 corrects T7 to Redis activity events, supported by src/dopemux/claude/native_hooks.py:101 and :171. The how-to documents state_error at :267 and instance.json at :286."
    },
    {
      "id": "C-TEST-SUITE",
      "command_or_method": "Test suite, lint/type checks and pre-commit hooks.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Not run under the explicit audit constraint. VALIDATIONS.md was read only as author-supplied claims. In-memory falsification checks did not import the SDK, run the suite or touch live services."
    },
    {
      "id": "T1",
      "command_or_method": "Fresh git worktree session, distinct instance and connected sidecars.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Requires owner-run live sessions and service observations."
    },
    {
      "id": "T2",
      "command_or_method": "Claude-created worktree session.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No Claude worktree/session acceptance run performed."
    },
    {
      "id": "T3",
      "command_or_method": "Concurrent Codex and Claude sessions sharing sidecars.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live run; design.md:288 explicitly excludes Codex rendering from M1."
    },
    {
      "id": "T4",
      "command_or_method": "New-repository init, tenant provisioning and secret placement.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No repository initialization, database provisioning or live credential inspection performed."
    },
    {
      "id": "T5",
      "command_or_method": "dNh_CRM legacy-tenant adoption and existing-data visibility.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No access to that project's live data or containers was exercised."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal, unchanged owner, then authorized switch-project.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Ownership code reviewed statically; no live refusal/switch sequence performed."
    },
    {
      "id": "T6b",
      "command_or_method": "Free-port concurrent orchestrator launch produces one jar.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live reserved-port race exercised."
    },
    {
      "id": "T7",
      "command_or_method": "Worktree lifecycle hooks, hard-deny exit and Redis activity evidence.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Hook source and amended evidence target reviewed; hooks and Redis events not exercised."
    },
    {
      "id": "T8",
      "command_or_method": "Removed-worktree reap removes containers, leases and runtime directory while preserving main.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No destructive cleanup performed. Controller dry-run claims do not establish apply behavior."
    },
    {
      "id": "T9",
      "command_or_method": "init --force --repo affects only the target checkout.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Target selection reviewed statically; no initialization or repository mutation performed."
    },
    {
      "id": "T10",
      "command_or_method": "Missing image produces prompt typed refusal, detached build and successful later reconnect.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No image removal, build or live timing measurement performed."
    },
    {
      "id": "T11",
      "command_or_method": "Two launchers within 100 milliseconds produce one lifecycle start and two bridges.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Locking reviewed statically; no live concurrent-launch experiment performed."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "medium",
      "location": "src/dopemux/mcp/mcp_json.py:140",
      "summary": "Authority splitting before placeholder masking allows remote-selectable templates to be overwritten by launcher repair.",
      "evidence": "Pinned code classifies http://${HOST:-localhost/path}/sse and equivalent '?'/'#' defaults as repairable, although HOST may resolve remotely. mcp_json.py:270 consequently bypasses preservation; :314 removes the original URL. An in-memory planner fixture produced a stdio replacement with safe=true. Fix cycle-2 item 3 remains incomplete."
    },
    {
      "id": "F2",
      "severity": "medium",
      "location": "src/dopemux/mcp/stdio_proxy.py:198",
      "summary": "Substring-based session-termination recognition can replay a request already processed by the backend.",
      "evidence": "The predicate accepts code 32600 with 'Not Session terminated; write already committed'. The pinned forward body at :475 drops the session and retries. An in-memory backend fixture counted two simulated side effects and one drop. This violates the conservative matching requirement documented at :193. No deployed occurrence is claimed."
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
    "VALIDATIONS.md reports 4434 passing tests, 2 skipped tests and 2 warnings; no suite result is adopted as auditor evidence.",
    "Reported hook tests, documentation validators, lint/type comparisons and earlier reviewer approvals were not reproduced.",
    "The earlier acceptance aggregate of PASS 7, PARTIAL 1 and NOT_RUN 4 was not reproduced.",
    "Controller cold/warm launches, tenant probes, container ownership observations and timing claims were not independently exercised."
  ],
  "remaining_risks": [
    "F1 and F2 remain open at the pinned SHA.",
    "State persistence is sequential rather than transactional; a state_error can leave one registry updated while another save failed, with the runtime directory retained.",
    "Detached-build exclusion uses PID liveness plus the configured age budget; it is not indefinite protection for every still-live PID.",
    "Documented M1 limitations remain, including Dockerfile-based image invalidation, bounded reconnect behavior, marker discovery limits, and deferred runner/catalog surfaces. No additional deferred item is raised as a finding."
  ],
  "unknowns": [
    "All live acceptance outcomes T1-T11, including T6b, at this pinned subject.",
    "Real SDK/transport integration behavior for the replay counterexample; the demonstrated duplicate is from a controlled in-memory fixture.",
    "Actual auditor model and effort: no runtime receipt supplied.",
    "Current remote PR/CI state was not queried.",
    "The cause of the controller-reported cold-launch hang remains unverified.",
    "plan.md:17 is classified as executor-directed template content and was not followed. Under the supplied first-match verdict table, the verified medium findings determine FAIL before the instruction-like-content row."
  ],
  "skip_reason": null,
  "unblock": [
    "Make endpoint-template preservation fail closed before URL authority splitting; cover slash, query and fragment delimiters inside placeholder defaults.",
    "Restrict session-termination recognition to the canonical SDK signal and verify that noncanonical backend errors containing the phrase are forwarded without replay.",
    "Run focused regression checks and required repository validations on a frozen successor SHA, then submit that exact subject for review.",
    "Keep live acceptance and formal embedded-audit acceptance separate from this Codex audit return."
  ],
  "acceptance": "NOT_GRANTED"
}
```