**DMX-CI-INTEGRATION-R1: static source audit (no tools, nothing run)**

**Verdict: NEEDS_SUPERVISOR.** I found no medium, high or critical defect. Check 5 is UNKNOWN because the packet has no document that discloses the retained failures. Acceptance is NOT_GRANTED.

**Subject:** the observed head matches the pinned SHA. The packet has no per-file hashes, only the manifest hash. Model identity observed is UNKNOWN, since no receipt was supplied.

**Check 1: no automatic API-backed call from PR lifecycle events (PASS, static)**
- `gemini-dispatch.yml` subscribes `pull_request` only to `opened`. The `dispatch` condition no longer admits `pull_request`, and the PR-opened to `review` mapping is removed.
  - Because `dispatch` is skipped on PRs, the `review`, `triage`, `invoke` and `plan-execute` jobs are skipped with it.
  - `fallthrough` does not fire on a PR, since `failure()` is false and the command output is empty.
  - `ready_for_review` is not subscribed at all.
- A command in a PR body is not admitted. Only `issue_comment`, `pull_request_review_comment` and `pull_request_review` events with a trusted author association and a leading `@gemini-cli` reach `dispatch`. That is the retained explicit-command path.
- `gemini-scheduled-triage.yml`: the `triage` job is gated off for `pull_request*` and `merge_group` events. `label` needs `triage`, so it is skipped too.
- `ci-complete.yml` and `security-review.yml`: the Claude action is gated off for `pull_request*` and `merge_group`. Non-PR runs keep the credential guard.
- The tests evaluate the real `if` expressions across action, draft, fork, key and body variants. They follow reusable-workflow jobs only if `dispatch` actually passes the admission check.

**Check 2: no new route, permission expansion or security bypass (PASS, static)**
- The permission blocks shown are unchanged.
- On PRs and merge groups, the security summary steps `exit 1` and report `NOT_RUN`/pending, so Security Review stays blocking.
- The `ci-summary` PR gate still requires the same eight deterministic jobs.
- The author's claim that the other `ci-complete` jobs are unchanged cannot be verified from this packet.
- `embedded-audit` is unchanged and contains no provider action.

**Check 3: five-path reconciliation (PASS for the shown units)**
- `store.py`: it keeps `write_principal` and `principal_self_asserted` and adds the corrected fields. These are keyword-only, so call order is not an issue. Keyed first-write-wins, including legacy ids, is preserved.
- `dope_memory_main.py`: `MemoryCorrectRequest` keeps the optional main write-id fields and adds `extra: forbid`.
- REST `memory_correct` keeps `write_principal=identity.principal`.
- `mcp_http.py`: all conflicted tools are now `async` and keep the main identity semantics (read defaults versus bound-workspace writes). The correction tool calls `_authorize_write` and passes the principal, and the five-path edits stay consistent with that.
- The transport test exercises SQLite thread affinity indirectly. A sync tool would run on a worker thread against a connection created on the loop thread.
- I did not see `insert_work_log_entry`, `VALID_CORRECTION_TYPES` imports, or `PRINCIPAL_HOOKS`. Those are inherited and not verified here.

**Check 4: fixtures and tests (PASS, static)**
- The transport test builds an enforce-mode `AuthGate` with a hashed token file and a bound workspace, then asserts the stored principal is `runner:codex`. It also asserts a 401 for a bad token and a 400 for a mismatched workspace.
- It also asserts no appended rows on rejection.
- The capture-client fixture adds the principal columns and asserts `("internal:cli", 1)`. Source behavior is not weakened.

**Check 5: scope and docs disclosure (UNKNOWN)**
- The how-to doc accurately states that retained explicit commands, issue triage, scheduled triage and non-PR security can still use API credentials. It states no fallback, route, permission or automatic ready promotion was added.
- No packet document discloses the retained failures, which are the 12-vs-13 job-count test failure and the four Ruff F findings. They appear only in the author-report prose. Draft-only authority is likewise not shown in a document.

**Findings (low):**
1. `docs/02-how-to/subscription-only-pr-review.md:17-19`: the claim that the "existing PR Steward recheck reuses exact-head audit evidence" is unverifiable from the packet.
2. `ci-complete.yml:622-628`: on PRs `security` always fails, so the next-steps text always prints "Fix required checks first" even when the PR Gate is CLEAR. This is misleading wording, not a gate defect.
3. `gemini-scheduled-triage.yml:20-22`: the shared concurrency group with `cancel-in-progress` lets a trivial PR validation run cancel an in-progress scheduled triage run. This was already present.

**Instruction-like content:** none directed at the auditor.

```json
{
  "schema": "independent-audit/v1",
  "status": "NEEDS_SUPERVISOR",
  "subject": {
    "packet_id": "DMX-CI-INTEGRATION-R1",
    "repo": "DDD-Enterprises/dopemux-mvp",
    "pinned_sha": "39617b3891fc15c74278aafeb1a31ff5c324a86c",
    "observed_head": "39617b3891fc15c74278aafeb1a31ff5c324a86c",
    "head_match": true,
    "base": "583720375df69fbe50f7b8a6b199eaf026f46fb5",
    "file_hashes": {"subject_manifest_sha256": "4ba3ce1f7f7169ba856d1d974eccaa31e9394d4bf031a1ac17e3bc61ee4aeb49", "per_file": "not supplied in packet"}
  },
  "auditor": {
    "runner": "claude-agent-sdk single response, no tools",
    "model_requested": "claude-sonnet-5-5",
    "model_observed": "UNKNOWN",
    "effort": "low",
    "independent_of_implementer": true
  },
  "checks": [
    {"id": "C1", "command_or_method": "static read of workflow triggers, job if-expressions and policy tests", "exit_code": null, "bucket": "PASS", "evidence": "dispatch no longer admits pull_request; PR-opened to review mapping removed; scheduled triage gated off for pull_request*/merge_group; Claude security step gated off for PR/merge_group; tests evaluate the real expressions across variants"},
    {"id": "C2", "command_or_method": "static read of permissions, security summaries and the ci-summary gate", "exit_code": null, "bucket": "PASS", "evidence": "permissions unchanged in the shown files; security steps exit 1 with NOT_RUN/pending on PR and merge_group; PR gate still requires the same eight deterministic jobs; other ci-complete jobs rely on author equality claim"},
    {"id": "C3", "command_or_method": "static read of conflict resolutions and named units", "exit_code": null, "bucket": "PASS", "evidence": "main bound-workspace/default-instance/principal semantics kept; frozen correction payload, extra=forbid and keyed replay kept; all conflicted MCP tools async; inherited helpers not seen"},
    {"id": "C4", "command_or_method": "static read of the transport, adapter and capture fixtures", "exit_code": null, "bucket": "PASS", "evidence": "enforce-mode AuthGate with hashed token file, principal runner:codex asserted, 401/400/422 and no-append rejections asserted; capture fixture asserts internal:cli self-asserted"},
    {"id": "C5", "command_or_method": "read of docs and scope disclosure", "exit_code": null, "bucket": "UNKNOWN", "evidence": "how-to doc discloses retained API routes and no new route/permission; retained 12-vs-13 and Ruff F failures and draft-only authority are not disclosed in any supplied document"}
  ],
  "findings": [
    {"id": "F1", "severity": "low", "location": "docs/02-how-to/subscription-only-pr-review.md:17", "summary": "PR Steward reuse claim unverifiable from packet", "evidence": "Steward behavior is not in the supplied sources"},
    {"id": "F2", "severity": "low", "location": ".github/workflows/ci-complete.yml:622", "summary": "On PRs the summary always prints the fix-required-checks text even when the PR Gate is CLEAR", "evidence": "security always fails on PR, so the success branch is unreachable"},
    {"id": "F3", "severity": "low", "location": ".github/workflows/gemini-scheduled-triage.yml:20", "summary": "PR validation shares the cancel-in-progress concurrency group with scheduled runs and can cancel them", "evidence": "group is the workflow name only"}
  ],
  "instruction_like_content": [],
  "author_claims_not_reproduced": ["598 integration tests PASS", "306 policy tests PASS", "worker suite 454 PASS/1 FAIL (12-vs-13) reproduced on main", "four Ruff F findings in main", "precommit/schema/diff/source-identity PASS", "Claude Max login, credits and auto-reload OFF, Q control PASS", "other ci-complete jobs equal main"],
  "remaining_risks": ["explicit trusted @gemini-cli comment/review commands, issue triage and non-PR runs can still use API credentials", "async tools block the event loop on sync SQLite by design", "inherited components not re-audited"],
  "unknowns": ["retained-failure and draft-only disclosure document", "inherited insert_work_log_entry, VALID_CORRECTION_TYPES and PRINCIPAL_HOOKS definitions", "hosted CI and branch protection state", "model identity"],
  "skip_reason": null,
  "unblock": ["supply the scope/PR document that discloses the retained test and Ruff failures and draft-only authority, or accept the UNKNOWN for check 5"],
  "acceptance": "NOT_GRANTED"
}
```
