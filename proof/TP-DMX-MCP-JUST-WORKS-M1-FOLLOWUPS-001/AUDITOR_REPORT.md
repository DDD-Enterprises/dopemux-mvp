# AUDITOR REPORT — PR #1521 L2 embedded audit (TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001)

- **Verdict:** PASS, no findings, 3 low risks
- **Auditor:** AGY CLI 1.5.13, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`)
- **Implementer:** Codex (requested `gpt-6.1-sol`) wrote most of the diff; a Claude Code session (`claude-fable-5-2`) finished it after the owner's reroute. Neither audited.
- **Audited head:** `cf3b262a75efe9e2f4edc50af1b67ae50e4a8bdf`
- **Base:** `ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7` (main, the merge-base)
- **Validation inside the audit:** NOT_RUN
- **Containment:** stream step types `agent_response`, `system_message`, `user_input` only; no tool steps
- **Instruction-like scan (trusted scanner):** detected=false, matches=0
- **Evidence label:** AUDITOR_WRITTEN_RAW_RETAINED. The raw AGY stream, stderr and wrapper exit line are in `review_bundle/`.

## Why this audit

The packet puts this change in risk lane L2 and requires an independent audit before merge. The diff
closes the four follow-ups left open when PR #1503 merged: status lease ports (A), dry-run leases (B),
expired build PIDs (C) and proxy cancel forwarding (D). It touches 11 files; the
40 files under `proof/` were left out of the audit prompt (`EXCLUDED_PROOF_FILES.txt`).

The diff has two authors. Codex handed the work back with 15 failing tests, the owner rerouted it to the
Claude Code supervisor session, and that session fixed the tests, corrected the dry-run lease planning and
the build-PID identity handling, and merged main. Neither Codex nor Claude may audit it.

## Operator approval of the audit route

The supervisor asked three questions at the draft-PR stop: whether to regenerate the proof bundle,
which route should run the independent audit, and whether to bring the branch up to date with main.
The owner answered "1 yes, 2 agy, 3 yes" at 2026-11-20T03:00:37.260Z (Claude Code session `a905a5d7-d220-4b74-9092-015deba24b0b`).

The owner named the route, not a model. The session used `gemini-4-argon-high`, the model the owner approved for
the PR #1516 audit. That choice is the session's and is listed under remaining risks.

## Auditor return (verbatim JSON)

```json
{
  "status": "OK",
  "verdict": "PASS",
  "findings": [],
  "risks": [
    {
      "severity": "low",
      "path": "src/dopemux/mcp/stdio_proxy.py",
      "lines": "475-488",
      "summary": "Relies on MCP Python SDK private attribute ClientSession._request_id to capture the backend request ID before send_request awaits.",
      "mitigation": "Explicitly permitted by packet step S5; fails closed with McpError(INTERNAL_ERROR) if _request_id is missing or non-int, and is pinned by test_m1_followup_sdk_request_id_contract_fails_closed_if_missing."
    },
    {
      "severity": "low",
      "path": "src/dopemux/mcp/launcher.py",
      "lines": "440-457",
      "summary": "Synchronous termination loop in _live_build_pid can block up to 4.0s (2.0s SIGTERM wait + 2.0s SIGKILL wait) when reaping an expired build that ignores SIGTERM.",
      "mitigation": "Bounded to 4.0s total and only triggers when a build exceeds DOPEMUX_MCP_BUILD_TIMEOUT_SECS (default 1800s)."
    },
    {
      "severity": "low",
      "path": "src/dopemux/mcp/launcher.py",
      "lines": "399-418",
      "summary": "_build_process_identity is duplicated across launcher.py and reap.py to avoid circular imports.",
      "mitigation": "Required by packet invariant C; parity between both modules is directly tested by test_m1_followup_build_stale_identity_never_signalled and test_m1_followup_expiry_signal_rules_and_reaper_agreement."
    }
  ],
  "rationale": "Audited PR #1521 at head SHA cf3b262a75efe9e2f4edc50af1b67ae50e4a8bdf against base SHA ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7 for DDD-Enterprises/dopemux-mvp. All 11 changed files fall within the packet commit.allowlist and no sealed paths were touched. (A) In src/dopemux/mcp/lifecycle.py (_resolve_ports), read-only calls (allocate=False) now overlay active worktree leases onto extracted envrc ports while excluding task-orchestrator, preserving unleased envrc values, and avoiding any registry writes or lock creation. (B) Dry-run start/restart threads dry_run=True from run_lifecycle through _mutable_facts into _resolve_ports and allocate_ports using nullcontext() instead of registry_lock, persist=False, and an in-memory planned_leases registry for downstream preflight validation so on-disk lease files remain absent or byte-identical. (C) src/dopemux/mcp/launcher.py and src/dopemux/mcp/reap.py record and verify JSON process identity (pid, create_time, pgid == pid, non-zombie) via psutil before considering a build live or signalling it; legacy one-line, malformed, unverified, or mismatched records are treated as stale without signalling, and expired verified builds are terminated via os.killpg (SIGTERM then SIGKILL after a 2.0s wait) while retaining ownership if termination fails. (D) src/dopemux/mcp/stdio_proxy.py captures the backend session's request ID prior to send_request, fails closed if the SDK attribute contract is absent, and forwards notifications/cancelled under a shielded 0.25s timeout only when cancelled by the runner while the session is live and not closing. Comprehensive hermetic unit tests cover all four fixes and failure modes.",
  "inspected_paths": [
    "claudedocs/mcp-just-works-design-2026-11-05.md",
    "src/dopemux/mcp/launcher.py",
    "src/dopemux/mcp/lifecycle.py",
    "src/dopemux/mcp/reap.py",
    "src/dopemux/mcp/stdio_proxy.py",
    "task-packets/TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001.json",
    "task-packets/TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001.md",
    "tests/unit/test_mcp_launcher.py",
    "tests/unit/test_mcp_lifecycle_ports_from_leases.py",
    "tests/unit/test_mcp_reap.py",
    "tests/unit/test_mcp_stdio_proxy.py"
  ],
  "evidence_refs": [
    "repo:DDD-Enterprises/dopemux-mvp#1521",
    "base_sha:ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7",
    "head_sha:cf3b262a75efe9e2f4edc50af1b67ae50e4a8bdf",
    "src/dopemux/mcp/lifecycle.py:383-531 (_resolve_ports allocate=False lease preference and dry_run in-memory planning)",
    "src/dopemux/mcp/lifecycle.py:1053-1156 (_mutable_facts dry_run propagation and planned_leases inspection)",
    "src/dopemux/mcp/lifecycle.py:1661-1667 (run_lifecycle facts_kw dry_run forwarding)",
    "src/dopemux/mcp/launcher.py:399-468 (_build_process_identity, _live_build_pid process-group termination, _write_build_pid atomic JSON record)",
    "src/dopemux/mcp/reap.py:504-553 (_build_process_identity and _live_build identity parity with launcher)",
    "src/dopemux/mcp/stdio_proxy.py:122-123,283,472-519,640-651 (CANCEL_CLEANUP_TIMEOUT_S, closing flag, backend_id capture, shielded CancelledNotification forwarding)",
    "tests/unit/test_mcp_lifecycle_ports_from_leases.py:131-180,520-610,974-988,1131-1297 (rewritten dry-run tests and M1 follow-up A/B regression tests)",
    "tests/unit/test_mcp_launcher.py:102-114,334-349,1126-1140,1597-1771 (M1 follow-up C synthetic process table and signal verification tests)",
    "tests/unit/test_mcp_reap.py:47-59,1645-1673,1713-1719,2043-2056,2413-2423 (M1 follow-up C reaper liveness and negative PID tests)",
    "tests/unit/test_mcp_stdio_proxy.py:969-1156 (M1 follow-up D in-memory SDK session cancellation forwarding and contract tests)"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings

None.

## Auditor risks

| # | Severity | Location | Risk | Auditor's mitigation note |
|---|---|---|---|---|
| 1 | low | `src/dopemux/mcp/stdio_proxy.py` 475-488 | Relies on MCP Python SDK private attribute ClientSession.\_request\_id to capture the backend request ID before send\_request awaits. | Explicitly permitted by packet step S5; fails closed with McpError(INTERNAL\_ERROR) if \_request\_id is missing or non-int, and is pinned by test\_m1\_followup\_sdk\_request\_id\_contract\_fails\_closed\_if\_missing. |
| 2 | low | `src/dopemux/mcp/launcher.py` 440-457 | Synchronous termination loop in \_live\_build\_pid can block up to 4.0s (2.0s SIGTERM wait + 2.0s SIGKILL wait) when reaping an expired build that ignores SIGTERM. | Bounded to 4.0s total and only triggers when a build exceeds DOPEMUX\_MCP\_BUILD\_TIMEOUT\_SECS (default 1800s). |
| 3 | low | `src/dopemux/mcp/launcher.py` 399-418 | \_build\_process\_identity is duplicated across launcher.py and reap.py to avoid circular imports. | Required by packet invariant C; parity between both modules is directly tested by test\_m1\_followup\_build\_stale\_identity\_never\_signalled and test\_m1\_followup\_expiry\_signal\_rules\_and\_reaper\_agreement. |

## Corroboration

None. One auditor ran, once.

## Validation

The audit session ran no validation. Local results, verbatim from `review_bundle/LOCAL_VALIDATION.txt`:

```text
MCP lifecycle follow-ups: local validation at cf3b262a75efe9e2f4edc50af1b67ae50e4a8bdf (2026-11-20T03:18:26Z), Python 3.12.13
Five touched test files (test_mcp_lifecycle_ports_from_leases, test_mcp_launcher, test_mcp_reap, test_mcp_stdio_proxy, test_mcp_lifecycle):
358 passed in 17.66s
pytest exit=0

Same five test files (byte-identical to cf3b262a7) against src/ and compose.yml from the base ba5c3e07b
(standalone tree outside the worktree, 2026-11-20T03:30:11Z..03:30:31Z; counts from the JUnit report):
207 passed, 41 failed, 110 errors (358 collected)
pytest exit=1
imported: <standalone tree>/src/dopemux/mcp/{reap,lifecycle,launcher,stdio_proxy}.py (each cmp-identical to the base blob)

Per file on base:
  test_mcp_lifecycle                     85 passed
  test_mcp_lifecycle_ports_from_leases   35 passed, 11 failed
  test_mcp_launcher                      47 passed, 25 failed
  test_mcp_stdio_proxy                   40 passed,  5 failed
  test_mcp_reap                          110 errors (fixture setup)

How to read the base result:
- All 110 errors and 14 of the 41 failures are AttributeError: the base has no
  _build_process_identity in reap.py / launcher.py, which the new fixtures and tests call.
  They show the tests need code added by this PR; they are not behavioural assertions.
- 3 failures are the missing stdio_proxy cancel-cleanup constant (same kind).
- The remaining 24 failures are behavioural assertions failing on base: dry-run persisting
  leases, stale envrc ports not re-leased, _resolve_ports lacking dry_run, expired build not
  signalled / bare-PID build file, cancel not forwarded with the backend request id.

Discarded attempts (not evidence):
- 03:26:12Z run reported "358 passed" for base. It imported the worktree's own src, because
  tests/conftest.py inserts <repo>/src at sys.path[0]. Invalid; superseded by the run above.
- A second attempt collected nothing (git archive aborted on a path absent at head) and
  resolved dopemux through the venv's editable install to another worktree. Invalid.
- A third run in the standalone tree without compose.yml gave 48 failed / 110 errors; 9 of
  those failures were the product-root lookup, an artefact of the tree. Superseded.

Full unit suite: last run on the merge commit 29fb004ee174c27ff6358ba9d0052b9667050594 (make test-fast, finished
2026-11-20T03:03:45Z): 4532 passed, 29 skipped, exit 0. cf3b262a7 adds only files under proof/
to that commit, so the suite was not rerun at cf3b262a7.

Not run here: live Docker start/stop, a real MCP client cancel against a running backend.
```

CI on the audited head, captured 2026-11-20T03:51:07Z (`review_bundle/CI_EVIDENCE.json`):
2 FAILURE, 3 SKIPPED, 20 SUCCESS. The checks that did not pass:

| Check | State | Link |
|---|---|---|
| PR Steward / final readiness | FAILURE | https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/44665683197 |
| independent embedded audit | FAILURE | https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/44665623560/job/136054059369 |

Both are the audit gates. They fail until the signed proof for this audit is on the branch.

## Run facts

| Item | Value |
|---|---|
| Launched | 2026-11-20T03:09:39Z |
| Wrapper end | 2026-11-20T03:10:57Z, exit 0 |
| Conversation | `fe89e363-4bab-47da-88ef-05dee1a81345` |
| Result | SUCCESS, 1 turn, 75.2 s |
| Tokens | input 46761, output 9014, thinking 7222 |
| Prompt sha256 | `d6d65522314d8846b2d0e8d183894fb69cb201faa5cc634c3ba1a87c4a0500f0` |
| Diff sha256 | `dd6c0a94fa4d58516be334d32470332e6d687acf864020b40302a8755d816a7a` |
| Raw stream sha256 | `bc08de6c2c94acb2eaa79c953c06bd733a6da0cb17e9c7e6be2d54d1d6dafcb6` |

## Remaining risks

1. Validation was not run inside the sealed audit session (validation_status=NOT_RUN). The session had no repository and took no tool steps; it read the diff in the prompt. Local results are in review_bundle/LOCAL_VALIDATION.txt.
2. The auditor was not asked about the reversed test expectation by name. The prompt carries the diff without the proof files, so REROUTE_TO_CLAUDE_RESULT.md, which flags the reversal, was not in front of it. test_dead_or_stale_build_pid_does_not_block_a_reap now asserts that a live build older than DOPEMUX_MCP_BUILD_TIMEOUT_SECS does not block a reap. The auditor described fix C's termination of expired verified builds and returned PASS, but did not comment on that test change specifically. OPERATOR: decision pending on whether that is enough.
3. One auditor governs and there is no corroborating second audit. The PR #1516 packet carried a Grok corroboration; this one does not.
4. The diff has two authors, Codex and a Claude Code session. Independence rests on the auditor's model family (google-gemini) differing from both. All three model identities are requested or self-reported; none is provider-attested.
5. The owner chose the route (agy) and did not name a model. The session used gemini-4-argon-high, the model the owner approved for the PR #1516 audit.
6. AGY ran with tool permissions on always-proceed. Containment rests on the sealed directory and on the observed absence of tool steps in the stream, not on an enforced sandbox.
7. The audited head contains a merge of main. Earlier audited PRs were linear, and whether PR Steward accepts this shape is unknown until it runs on the signed proof.
8. Process identity, clocks and signals in the build-PID tests are synthetic. No real over-budget build was terminated, and no real MCP client cancel was sent to a running backend.
9. The raw AGY stream and the AGY CLI log contain the operator's home directory path, as in earlier bundles. Only the account email address was redacted (REDACTIONS.md).

The 3 auditor risks above are also carried in `PROOF.json`.
