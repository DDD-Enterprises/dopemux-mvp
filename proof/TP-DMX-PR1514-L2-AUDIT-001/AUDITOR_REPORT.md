# AUDITOR REPORT — PR #1514 L2 embedded audit (TP-DMX-PR1514-L2-AUDIT-001)

- **Auditor**: Grok CLI 1.0.77, `grok-4.7` (receipt grok-4.7-build), contained with `init.tools == []`; prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5), a different runner and model family
- **Audited head**: `fe6ff210c6bdf5964e16ae41d57b7f76c31ed28d` · **Base**: `589bb0519424b84338ca2fcb7ae68f8607ef8b74` (the merge-base with main)
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw Grok stream (emails redacted), stderr and wrapper exit line are in `review_bundle/`

## Why this audit

Since PR #1498 merged (2026-11-05), CI "Unit Tests" hung at its 30-minute limit on about a third of runs. The cause was
`sse_starlette.sse.AppStatus.should_exit`, a process-wide flag that a uvicorn shutdown in one runner-memory MCP test sets and
nothing clears, so every later MCP test in the same xdist worker waited for its `initialize` reply forever. `tests/conftest.py`
now clears it before each test. Separately, the routing-policy parsing test ran the real RTE wizard (a full prescan) eight
times, about 502 s of the job; it now records the parsed policy instead. The PR changes only these two test files.

## Operator approval of the audit route

"merge it" 2026-11-16T03:12:37Z, then the route "Grok audit, then merge" 2026-11-16T03:22:20Z, and "yes" to marking the PR ready
2026-11-16T09:30:04Z (Claude Code session c311455f). Recorded per docs/ops/embedded-audit.md "Packet-specific supervisor-approved
fallback auditors": approval, bounded input, no-secret constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "COMPLETE",
  "verdict": "PASS_WITH_RISKS",
  "findings": [],
  "risks": [
    {
      "severity": "medium",
      "summary": "Shutdown latch reset covers only AppStatus.should_exit. sse-starlette builds that cancel EventSourceResponse when the shared AppStatus.should_exit_event is already set will still end the stream immediately, so the runner-memory MCP initialize hang can remain. The two flags can also disagree after this assignment. Pinned sse-starlette and the EventSourceResponse shutdown condition are outside the diff.",
      "evidence": "tests/conftest.py adds _reset_sse_starlette_shutdown_latch, which sets sse.AppStatus.should_exit = False when sys.modules already contains sse_starlette.sse and does not replace should_exit_event."
    },
    {
      "severity": "medium",
      "summary": "WizardRunner is replaced on the dopemux.ux.wizard module object. A command that already bound WizardRunner by from-import keeps the real class, so the prescan cost returns and received stays empty until its equality assertion fails. The rte wizard call site is outside the diff.",
      "evidence": "tests/unit/test_rte_routing_policy_choice_consistency.py monkeypatch.setattr(wizard_package, \"WizardRunner\", RecordingWizard) after import dopemux.ux.wizard as wizard_package, then asserts received == list(ROUTING_POLICY_CHOICES)."
    },
    {
      "severity": "low",
      "summary": "The new fixture calls sys.modules. This hunk does not add an import, so the suite depends on an existing module-level sys binding in tests/conftest.py. A missing binding raises NameError from an autouse fixture on every test.",
      "evidence": "tests/conftest.py hunk uses sys.modules.get(\"sse_starlette.sse\") with no import line in the diff."
    },
    {
      "severity": "low",
      "summary": "exit_code == 0 now requires the command to construct the stub and return success. Work that errors before WizardRunner(...) fails the test. A single test that stops uvicorn and starts it again still observes a latch set during that test, because the fixture clears only at setup.",
      "evidence": "test_rte_wizard_accepts_every_canonical_routing_policy_value asserts result.exit_code == 0 inside the policy loop; the conftest fixture assigns should_exit = False only at fixture entry."
    }
  ],
  "rationale": "Trusted binding is DDD-Enterprises/dopemux-mvp PR 1514, head fe6ff210c6bdf5964e16ae41d57b7f76c31ed28d, base 589bb0519424b84338ca2fcb7ae68f8607ef8b74. Candidate metadata names the same two paths. Tools were disabled, so git, GitHub, workflow, and test commands were not run. The diff is test-only. The autouse fixture clears sse_starlette.sse.AppStatus.should_exit when that module is already loaded, which is a direct mitigation for a process-wide uvicorn shutdown flag leaking across later tests in one xdist worker. It does not import sse_starlette. The routing-policy test still invokes dopemux_cli.cli through CliRunner for every ROUTING_POLICY_CHOICES value, rejects the Click invalid-value string, requires exit code 0, and requires the stub to record each policy once in order. A missed patch cannot pass silently, because only RecordingWizard appends to received. Candidate comments about a 502s prescan and the CI hang were treated as data and were not measured. Instruction-like scan summary reports detected false and match_count 0; the diff comments do not redefine the audit.",
  "inspected_paths": [
    "tests/conftest.py",
    "tests/unit/test_rte_routing_policy_choice_consistency.py"
  ],
  "evidence_refs": [
    "trusted head fe6ff210c6bdf5964e16ae41d57b7f76c31ed28d",
    "trusted base 589bb0519424b84338ca2fcb7ae68f8607ef8b74",
    "tests/conftest.py:_reset_sse_starlette_shutdown_latch sets AppStatus.should_exit = False via sys.modules.get(\"sse_starlette.sse\")",
    "tests/unit/test_rte_routing_policy_choice_consistency.py:RecordingWizard plus assert received == list(ROUTING_POLICY_CHOICES) and exit_code == 0",
    "candidate changed_files: tests/conftest.py, tests/unit/test_rte_routing_policy_choice_consistency.py",
    "instruction_like_scan_summary detected false, match_count 0"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| none | | | |

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | PASS |
| 🧪 Unit Tests | PASS |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local run 1: CI fast unit gate selection (tests/unit + voice/brand tests, -n auto, main .venv + PYTHONPATH=src) | FAIL |
| local run 2: CI fast unit gate selection (tests/unit + voice/brand tests, -n auto, main .venv + PYTHONPATH=src) | PASS |
| local: isolated re-run of run 1's one failure | PASS |
| audit: validation inside the sealed Grok session | NOT_RUN |

The embedded-audit gate, recheck and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit session (validation_status=NOT_RUN). CI Unit Tests passed in 5 of 5 attempts on the PR (4530 passed each, per the implementing session). Local run 1 at the audited head stopped at one failure, test_extract_local_smoke.py::test_extract_pipeline_auto_embeddings_skip_without_credentials, which passed when re-run alone and in local run 2 (3853 passed, 0 failed); the PR does not touch it, so it is recorded as an order-dependent flake outside this PR, not fixed here. The local venv lacks fastmcp, so 11 w12 MCP tests skip locally; CI runs them.
- Grok risk (medium): Shutdown latch reset covers only AppStatus.should_exit. sse-starlette builds that cancel EventSourceResponse when the shared AppStatus.should_exit_event is already set will still end the stream immediately, so the runner-memory MCP initialize hang can remain. The two flags can also disagree after this assignment. Pinned sse-starlette and the EventSourceResponse shutdown condition are outside the diff.
- Grok risk (medium): WizardRunner is replaced on the dopemux.ux.wizard module object. A command that already bound WizardRunner by from-import keeps the real class, so the prescan cost returns and received stays empty until its equality assertion fails. The rte wizard call site is outside the diff.
- Grok risk (low): The new fixture calls sys.modules. This hunk does not add an import, so the suite depends on an existing module-level sys binding in tests/conftest.py. A missing binding raises NameError from an autouse fixture on every test.
- Grok risk (low): exit_code == 0 now requires the command to construct the stub and return success. Work that errors before WizardRunner(...) fails the test. A single test that stops uvicorn and starts it again still observes a latch set during that test, because the fixture clears only at setup.
- Supervisor check of Grok risk 1 (should_exit_event): not reachable with the pinned sse-starlette 3.3.4 (uv.lock). That version has no should_exit_event; AppStatus.should_exit (sse.py:137) is the only process-wide latch, and the per-response anyio events are created and discarded per call (sse.py:351-360). It would matter only after an sse-starlette upgrade that adds another latch.
- Supervisor check of Grok risk 2 (from-import bypass): not reachable today. The rte wizard command imports WizardRunner inside its function at call time (src/dopemux/commands/audit_commands.py:116), so the module-attribute patch applies; the test's received == ROUTING_POLICY_CHOICES assertion would fail loudly otherwise, and it passes in CI and locally.
- Supervisor check of Grok risk 3 (missing sys import): not reachable. tests/conftest.py imports sys at line 3.
- Grok risk 4 is an accurate description of the design: the latch is cleared at fixture setup only, so a single test that stops and restarts uvicorn would still see a latch set inside that test. The supervisor did not check whether any test does this.
- Audit scope: the whole PR diff, merge-base 589bb0519 to fe6ff210c; main has since moved without touching this PR's two files.
- Auditor model identity: requested grok-4.7; receipt grok-4.7-build; provider-attested identity beyond the receipt UNKNOWN.
- No second auditor ran: the operator chose a Grok audit only.
- Copilot and Codex (advisory) reviewed the audited head on GitHub with no findings and no review threads; they are not embedded auditors.
