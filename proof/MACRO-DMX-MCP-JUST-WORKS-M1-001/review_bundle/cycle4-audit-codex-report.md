END_OF_PROMPT 19586ec5-fc591cba

**Verdict: FAIL — two medium findings in item 14. Acceptance: NOT_GRANTED.**

**Change Summary / Analysis Performed:** Read the full branch-authored diff and supplied materials. Verified the pinned HEAD, diff bytes, and all 69 manifest hashes. Reviewed secrets handling, lock ordering, proxy reconnects, reap safety, documentation, and all 14 corrections. No delegation or mutations.

1. **F1 — Medium: retained leases bypass reserved/duplicate-port validation.**  
   `src/dopemux/mcp/lifecycle.py:1469` drops the doctor’s reserved-port and intra-config blockers, but `_resolve_ports` can retain existing leases without invoking allocation (`:437–469`). `_collision_checks` checks Docker ownership, not reserved or duplicate assignments. The later reserved-port check emits INFO (`:1059`).  
   A source-only probe preserved both ConPort and dope-memory leases on `7890`, with **zero collision findings**, with and without envrc values. Previously, the doctor findings blocked this state. Revalidate the resolved port map even when allocation is bypassed.

2. **F2 — Medium: lifecycle and launcher ownership checks still disagree.**  
   `src/dopemux/mcp/lifecycle.py:702` requires a truthy owner hash before rejecting a sibling worktree. A managed same-project ConPort container with an explicitly different workspace and **no worktree hash** falls through without a blocker, although ownership classification returns `WRONG_PROJECT`. The launcher rejects it at `src/dopemux/mcp/launcher.py:630`.  
   This is distinct from the documented compose-only and project-scoped orchestrator exceptions. Restore rejection of contradictory workspace ownership on resolved ports.

**Earlier finding closure:** Both findings from `30b0fdec9` remain closed. Both findings from `3f1335e7f` remain closed as specifically reported. Item 13 closes the generic `${PORT}` example from `43294e99b`, but does not establish universal endpoint preservation: an operator-written template using `CONPORT_MCP_PORT` is still replaceable even when its value would introduce a remote host/userinfo. That is the pre-stated residual, not a new finding.

**Validation Performed:** PASS for custody, full static review completion, targeted URL/error predicates, and `git diff --check`. FAIL for the two item-14 invariants above. Test suites, hooks, lint/type checks, and every live acceptance item are NOT_RUN by me.

**Remaining Uncertainty / Risk:** No additional finding beyond the two above. I would retain, without raising anew, the declared exact-literal resend assumption, named-port-template assumption, age-bounded build protection, and other listed deferrals. Live behavior remains unverified.

**Authority Used:** Latest audit request, repository instructions, independent-audit skill, and proof schema. This Codex return does not replace the governing embedded-audit record.

**Files Touched / Git State / Rollback Plan:** No files touched; working tree clean; HEAD matches the pin. No rollback required.

**Requested Next Step:** Correct F1/F2, add focused regression coverage, freeze the successor, and obtain the required audit against that subject.

```json
{
  "schema": "independent-audit/v1",
  "status": "FAIL",
  "subject": {
    "packet_id": "MACRO-DMX-MCP-JUST-WORKS-M1-001",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "fc591cba1f5f8fe7d2b59e30564aeb47793ac66e",
    "observed_head": "fc591cba1f5f8fe7d2b59e30564aeb47793ac66e",
    "head_match": true,
    "base": "46155cad92702beba8169448f1fefe5cef45294c (merge-tree of 5742575c4 and f16e0da2c)",
    "file_hashes": {
      "FILES.sha256": "40407efcd3561877684be7e56c72731acb0e914fa6010a64474738e79911f988",
      "subject.diff": "df21bd5671e657fd11073dde7861758dd058fb06d61eb69f42c5a1918e388be3",
      "src/dopemux/mcp/conport_tenant.py": "a7fb56c42a1bde7b46be074e52761ecd34c8396772dc7eb2d0cb9242f3df3869",
      "src/dopemux/mcp/launcher.py": "61f208d04e0514151a00768bc31384cb6f512b99f3f47f27cfbcff72ba96fc48",
      "src/dopemux/mcp/lifecycle.py": "b7180b57f347fec0c8d1513e376e63b3470b230b88cc8c881e9d50565c553f98",
      "src/dopemux/mcp/locks.py": "fe21d11eefc78c48743f093f16b6c7f371fb4f4f853a86e644ca0ab9f3b7a122",
      "src/dopemux/mcp/mcp_json.py": "d02edde613d8b2e206cbf81ce7e1f60df7222360bf0ae73c32f83b037872487e",
      "src/dopemux/mcp/reap.py": "decea1b83c015b2f236615448dd4359bb334b2427e4000d8d73f61f59104ac48",
      "src/dopemux/mcp/stdio_proxy.py": "5b133779afaa0a441b5ff96f24886eaa474035650f20cfd3a2dbc49474c848ad",
      "docs/02-how-to/mcp-setup-other-repos.md": "002c7a0f63a6d4c93183c26d3c0c0467511260d57a50fb23b22f2f7f391be272"
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
      "command_or_method": "Read-only git identity/status checks; compare subject.diff with the specified git diff; hash pinned blobs against FILES.sha256; count branch-authored commits.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "HEAD matches; expected repository and branch observed; working tree clean. Diff bytes match. All 69 manifest entries match pinned blobs; deletion checked separately. Branch-authored commit count is 54."
    },
    {
      "id": "C-DIFF",
      "command_or_method": "Read all 25953 lines of subject.diff and all supplied materials; trace changed code into relevant callers and consumers.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Full branch-authored range reviewed, excluding proof as instructed. D1-D10 examined. This bucket records coverage, not an overall correctness verdict."
    },
    {
      "id": "C-SECRETS",
      "command_or_method": "Static review of credential creation, persistence, subprocess boundaries, redaction and runtime artifacts.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "conport_tenant.py:221,243 uses private atomic secret files; :367,381 supplies SQL through stdin; :416,735 uses SCRAM verifiers; :449 redacts before truncation; :822 uses a private docker exec --env-file rather than a URL in argv. Reviewed compose-only credential delivery, mcp.env/start-plan construction and launcher error scrubbing. launcher.py:741,763 writes only identity fields and a timestamp to instance.json. No introduced secret-output path identified; live server logging was not verified."
    },
    {
      "id": "C-LOCKS",
      "command_or_method": "Trace instance, reserved-port, registry and provisioning lock call paths.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "locks.py:99,129 rechecks inode identity after acquisition. lifecycle.py:1627,1863,1944 serializes worktree start/restart and refreshes mutable facts under the lock; orchestrator work is outside that instance lock. launcher.py:502,590 disables nested instance acquisition. Attach/marker writes occur under the instance lock. No new registry-to-instance or instance-to-reserved acquisition found."
    },
    {
      "id": "C-RECONNECT",
      "command_or_method": "Static proxy/guard and installed SDK source review; source-only exact-error predicate probe.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "stdio_proxy.py:348,368 guards before each connection and after initialize; :384 implements bounded backoff; :325 enforces the reconnect window. :481 requires code 32600 and exact message equality. Substring and wrong-code probes returned false. Generic connection-closed errors are not resent. Installed streamable_http.py:519 contains the expected literal. No additional processed-request replay path identified beyond the declared exact-literal assumption; integration fault injection was NOT_RUN."
    },
    {
      "id": "C-REAP",
      "command_or_method": "Static planning/application trace, including label joins, predicates, lock boundaries, persistence and cleanup ordering.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "reap.py:432,452 derives idle eligibility without planning writes; :538 restricts marker-only candidates; :934 re-inspects container IDs; :1048 rechecks eligibility under lock. :1136 and :1142 retain runtime state on registry_busy/state_error before :1145 removes the directory. Scope exclusions, kill switches, bounded automatic waits, stale/locked skips and orchestrator exclusions verified. Build protection remains age-bounded as declared."
    },
    {
      "id": "C-IDENTITY-CATALOG",
      "command_or_method": "Static identity, environment scrubbing and target-catalog call-site review.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "runtime_state.py:109 defaults trust_env false; launcher.py:283 and docker_runtime.py:50,108 scrub ambient identity/port/credential inputs on the reviewed launch paths. mcp_commands.py:197,450,2215,2977 selects the target catalog for lifecycle, switch-project, init and repair-config. Explicit subdirectories normalize to their checkout root. Deferred doctor/profile and GIT_* limitations are retained."
    },
    {
      "id": "C-DOCS",
      "command_or_method": "Compare the how-to with implementation and read append-only design/plan corrections.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Reviewed launcher setup, shared-image key, refusal codes, envrc/trust-env behavior, reap skips and markers, tenant handling and M1 limitations. Historical statements were evaluated with their superseding amendments. The item-14 design claim of ownership parity is contradicted by F2; post-allocation coverage is incomplete under F1."
    },
    {
      "id": "FIX-01",
      "command_or_method": "Inspect tests/unit/test_docs_no_envrc_recipe.py:15 and tracked path casing.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Parameter names .claude/claude.md, matching the tracked file. Linux suite execution NOT_RUN."
    },
    {
      "id": "FIX-02",
      "command_or_method": "Inspect src/dopemux/cli.py:4256-4284.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "New SessionEnd entries receive timeout 60; existing matching registrations missing timeout gain it. Existing explicit timeout values are preserved. Other events are unchanged."
    },
    {
      "id": "FIX-03",
      "command_or_method": "Inspect mcp_json.py:134-228 and execute extracted URL predicates with in-memory strings.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Host/userinfo templates, literal remote URLs and credential-bearing literal URLs are preserved. The earlier permissive template behavior is superseded by item 13."
    },
    {
      "id": "FIX-04",
      "command_or_method": "Trace target normalization and catalog loading in mcp_commands.py.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Lifecycle :197-198, switch-project :450, init :2215 and repair-config :2977-2978 use the target catalog. Lifecycle receives the normalized target root."
    },
    {
      "id": "FIX-05",
      "command_or_method": "Inspect reap.py:243,432,452.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Planning derives an effective detach time from dead attach records without pruning them. Application prunes/rechecks under the instance lock."
    },
    {
      "id": "FIX-06",
      "command_or_method": "Trace reap.py:1009-1151.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Persistence errors produce state_error and return before rmtree or reporting reaped. Codex F1 from 30b0fdec9 is closed."
    },
    {
      "id": "FIX-07",
      "command_or_method": "Trace lifecycle.py:1332,1627,1863,1944 and launcher.py:502,590.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Direct worktree start/restart is serialized with reaping; restart uses one instance-lock acquisition across its worktree stop/start. Launcher callers avoid reacquiring their held lock. Codex F2 from 30b0fdec9 is closed."
    },
    {
      "id": "FIX-08",
      "command_or_method": "Inspect launcher.py:741,763,867 and reap.py:484,504,538,656.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Private identity-only marker is written at attachment under the instance lock. Marker-only missing-worktree directories can be planned, never merely idle, subject to registry/readability and documented live-build protection."
    },
    {
      "id": "FIX-09",
      "command_or_method": "Compare AGENTS.md:310-313 with docker_runtime.py:489-505.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Shared image wording matches the checkout-path plus Dockerfile-content key."
    },
    {
      "id": "FIX-10",
      "command_or_method": "Read design.md amendments and compare how-to reap wording with implementation.",
      "exit_code": null,
      "bucket": "PASS",
      "evidence": "Amendments cover dead attachments, persistence failure, lifecycle locking, marker-only cleanup and T7 Redis activity events. How-to :267 documents state_error; :286 documents instance.json."
    },
    {
      "id": "FIX-11",
      "command_or_method": "Inspect mcp_json.py:134-173; source-only probes of delimiter/default, base, scheme and userinfo templates.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Whole-string masking precedes authority splitting; only a leading literal scheme is stripped. Reported HOST/BASE/SCHEME/userinfo cases and scheme-relative templates are not repairable. Codex F1 from 3f1335e7f remains closed."
    },
    {
      "id": "FIX-12",
      "command_or_method": "Inspect stdio_proxy.py:191-205 and :463-499; source-only error predicate probes; read installed SDK emitter.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Only code 32600 plus exactly Session terminated matches. Not Session terminated; write already committed does not match. Codex F2 from 3f1335e7f remains closed. The declared exact-literal backend-error ambiguity remains."
    },
    {
      "id": "FIX-13",
      "command_or_method": "Inspect mcp_json.py:125-228 and planner integration; execute extracted predicates without reading environment values.",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "Generic PORT, host/path placeholders, templated schemes/bases and nonnumeric defaults are preserved. Dopemux-named port templates remain repairable. Codex F1 from 43294e99b is closed for its generic PORT example, not as a universal guarantee for operator-authored templates. Substituting 3005@remote.example into CONPORT_MCP_PORT still yields remote.example with userinfo; this is the declared residual."
    },
    {
      "id": "FIX-14",
      "command_or_method": "Trace doctor filtering, retained-lease resolution and post-allocation checks; execute AST-extracted pinned functions with in-memory registry/container fixtures.",
      "exit_code": 0,
      "bucket": "FAIL",
      "evidence": "Retained CONPORT_MCP_PORT=7890 and DOPE_MEMORY_PORT=7890 returned unchanged with zero collision findings, both with matching envrc and without envrc. A managed same-project conport owner with a foreign workspace and no hash classified WRONG_PROJECT but produced zero collision findings. Adding a sibling hash produced DOCKER_CONTAINER_PORT_COLLISION; changing project_id produced PORT_OWNED_BY_OTHER_PROJECT. A stale envrc owner absent from resolved ports is correctly excluded from collision checks, but the replacement coverage is incomplete."
    },
    {
      "id": "C-DIFF-CHECK",
      "command_or_method": "git diff --check 46155cad92702beba8169448f1fefe5cef45294c fc591cba1f5f8fe7d2b59e30564aeb47793ac66e -- . ':(exclude)proof'",
      "exit_code": 0,
      "bucket": "PASS",
      "evidence": "No whitespace errors reported."
    },
    {
      "id": "C-SUITES",
      "command_or_method": "Unit/integration suites, hooks workflow, lint, type checks, docs validators and pre-commit hooks.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Not run under the user's read-only audit/test-suite restriction. VALIDATIONS.md was read only as an author claim."
    },
    {
      "id": "T1",
      "command_or_method": "Fresh git worktree live launch and identity check.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live acceptance execution authorized for this audit."
    },
    {
      "id": "T2",
      "command_or_method": "Claude-created worktree live session.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live runner/worktree session exercised."
    },
    {
      "id": "T3",
      "command_or_method": "Concurrent Codex session and shared sidecars.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Not exercised; amendments explicitly exclude Codex config rendering from M1."
    },
    {
      "id": "T4",
      "command_or_method": "New-repository init, tenant provisioning and connection.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live PostgreSQL/Docker mutations performed."
    },
    {
      "id": "T5",
      "command_or_method": "Legacy dNh_CRM tenant adoption and data visibility.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No access to another project's live tenant exercised."
    },
    {
      "id": "T6",
      "command_or_method": "Foreign orchestrator refusal and explicit project switch.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Static ownership gates reviewed; no live refusal/switch performed."
    },
    {
      "id": "T6b",
      "command_or_method": "Concurrent orchestrator cold start on empty port 7890.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No live process/container start performed."
    },
    {
      "id": "T7",
      "command_or_method": "Live lifecycle hooks, hard-deny behavior and activity-event evidence.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Dispatcher and event paths reviewed statically; hooks were not invoked."
    },
    {
      "id": "T8",
      "command_or_method": "Removed-worktree reap, lease release and preservation of main.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Neither live dry-run nor apply executed by this auditor."
    },
    {
      "id": "T9",
      "command_or_method": "init --force --repo worktree leaves main unchanged.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Target resolution reviewed statically; no init mutation performed."
    },
    {
      "id": "T10",
      "command_or_method": "Missing-image detached build and later reconnect.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "No images removed/built; startup timing unverified."
    },
    {
      "id": "T11",
      "command_or_method": "Two launchers within 100 ms produce one lifecycle start.",
      "exit_code": null,
      "bucket": "NOT_RUN",
      "evidence": "Lock paths reviewed; live concurrency/timing not exercised."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "medium",
      "location": "src/dopemux/mcp/lifecycle.py:1469",
      "summary": "Doctor reserved-port and duplicate-port blockers are discarded without equivalent validation of retained leases.",
      "evidence": "_resolve_ports at :437-469 can return matching active leases without allocator validation. _collision_checks at :570 checks Docker owners only. The reserved-port branch at :1059 emits INFO. Extracted pinned functions preserved both selected services on reserved port 7890 and returned no collision findings. Thus item 14 removes a prior fail-closed check for still-invalid resolved ports."
    },
    {
      "id": "F2",
      "severity": "medium",
      "location": "src/dopemux/mcp/lifecycle.py:702",
      "summary": "A same-project sidecar with contradictory workspace ownership but no worktree hash passes lifecycle checks that the launcher rejects.",
      "evidence": "The new sibling check requires owner_hash to be truthy; the subsequent WRONG_PROJECT fallback applies only without project_id. A managed conport fixture with project_id=p, scope=worktree, workspace_id=/audit/sibling, no worktree_hash and resolved port 3105 classified WRONG_PROJECT yet yielded no collision finding. launcher.py:630 rejects its missing hash. Before item 14, doctor's DOCKER_CONTAINER_WRONG_PROJECT blocked this overlapping-port case."
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
    "VALIDATIONS.md: 4500 unit tests passed, two skipped, and 12 hooks workflow tests passed at the pin.",
    "Reported lint/type/format baselines, documentation validators, CI results and PR-bot receipts.",
    "Earlier independent auditor verdicts and controller/implementer reproduction claims.",
    "Acceptance at 30b0fdec9: seven PASS, one PARTIAL and four NOT_RUN.",
    "Cycle-2 cold/warm launch and reap smoke results; no equivalent live run was performed by this auditor."
  ],
  "remaining_risks": [
    "Exact code 32600 plus message Session terminated is not authenticated as SDK-generated; a backend returning it after processing can still cause one resend. Retained as the pre-stated residual, not a new finding.",
    "Allowed dopemux-named port templates establish shape, not provenance or resolved destination. Operator-authored identical templates can still be replaced despite remote/userinfo-bearing expansion.",
    "Detached-build protection is age-bounded; an old live build is not protected indefinitely. Retained as the declared residual.",
    "The documented M1 limitations and deferred items remain; none is elevated anew in this return.",
    "Static secret review does not establish live PostgreSQL logging, filesystem permissions on the host, or runtime absence of leakage."
  ],
  "unknowns": [
    "Observed model identity and reasoning effort: no runtime receipt available.",
    "All live acceptance outcomes at the pinned SHA.",
    "Full integration behavior of the two reproduced source-level gaps; no Docker startup was attempted.",
    "VALIDATIONS.md inconsistently describes T8 as repeated at this SHA while its smoke row says the run was at 3f1335e7f. Pinned live T8 evidence remains unverified.",
    "Some historical ledger entries are intrinsically truncated; omitted historical detail was not inferred.",
    "This Codex audit return does not establish formal embedded-audit acceptance or PR readiness."
  ],
  "skip_reason": null,
  "unblock": [
    "Validate reserved-port and intra-config uniqueness invariants against the final resolved port map, including retained leases that bypass allocation.",
    "Make sidecar lifecycle ownership checks reject contradictory workspace identity when the worktree hash is missing, preserving only explicitly authorized compatibility exceptions.",
    "Add focused regressions for retained duplicate/reserved leases and a same-project, foreign-workspace sidecar without a hash; retain controls for stale-port re-leasing and the project-scoped orchestrator.",
    "Freeze the corrected subject and obtain the required independent audit and owner acceptance evidence."
  ],
  "acceptance": "NOT_GRANTED"
}
```