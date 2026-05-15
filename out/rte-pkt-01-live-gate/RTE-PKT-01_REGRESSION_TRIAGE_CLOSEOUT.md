# RTE-PKT-01 Regression Triage Closeout

Generated: `2026-05-15T02:27:34.447685+00:00`

## Current Branch State

- worktree: `/Users/hue/.codex/worktrees/rte-pkt-01-live-gate`
- branch: `codex/rte-pkt-01-live-gate`
- head: `a4214ca5bf431e1b59791661e2b664a6cd24c1da`
- base comparison worktree: `/Users/hue/.codex/worktrees/rte-pkt-01-base-triage`
- base comparison head: `a4214ca5bf431e1b59791661e2b664a6cd24c1da`

```text
## codex/rte-pkt-01-live-gate
 M services/repo-truth-extractor/run_extraction_v5.py
 M services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
 M services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py
?? out/rte-pkt-01-live-gate/
?? services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py
```

## Regression Triage Table

| Test | Implementation Result | Base Result | Classification | Action |
|---|---|---|---|---|
| `services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback`<br>The intake path services/repo-truth-extractor/tests/test_run_extraction_v5_current_partition_execution.py does not exist in this checkout; rg found this test in test_run_extraction_v5_prelive_hardening.py. | FAIL exit 1; AssertionError: request_meta.escalation_trigger observed provider_failure, expected None. | FAIL exit 1 on clean detached base a4214ca5; same AssertionError: provider_failure is not None. | `BASELINE_FAILURE` | No runtime/test change in RTE-PKT-01; documented as baseline drift outside live-gate terminality scope. |
| `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai`<br>Path exists as provided. | FAIL exit 1; AssertionError: DEFAULT_TARGET_POLICY observed cost, expected balanced_openrouter. | FAIL exit 1 on clean detached base a4214ca5; same AssertionError: cost != balanced_openrouter. | `BASELINE_FAILURE` | No validator default-policy change in RTE-PKT-01; documented as baseline drift outside live-gate terminality scope. |

## Finalize Classification

`FINALIZE_LOCAL_ONLY_CONFIRMED`

Source evidence: `run_phase_R_finalize()` builds a local event store, reads pending/completed job rows, reads stored webhook payloads, parses local payload text, writes local raw artifacts, updates local async job status, and removes local pending files. Static inspection did not find provider clients, HTTP sessions, batch clients, or provider retrieval calls in this function.

- `run_extraction_v5.py:17861-17913`: event store is built from local webhook storage/migration helpers.
- `run_extraction_v5.py:18233-18261`: webhook payload is fetched from the event store, not from a provider API.
- `run_extraction_v5.py:18264-18505`: finalize reads local rows/payloads and writes local artifacts/status.

## Online Diagnostic Classification

| Flag | Classification | Source Evidence | Test Evidence |
|---|---|---|---|
| `--preflight-providers` | `PROVIDER_CONTACTING_EXPLICIT_INTENT` | `run_extraction_v5.py:6494-6524` runs provider doctor probes through `run_provider_doctor_probe()`, which calls `call_llm()` at `run_extraction_v5.py:6429-6436`; dispatch is at `run_extraction_v5.py:19868-19874`. | `test_run_extraction_v5_live_gate_terminality.py:168-207` monkeypatches `run_provider_preflight` and proves refusal before call without consent. |
| `--doctor` | `PROVIDER_CONTACTING_EXPLICIT_INTENT` | `run_extraction_v5.py:7141-7182` collects provider routes and calls `run_provider_doctor_probe()`; dispatch is at `run_extraction_v5.py:19886-19888` and `20056-20058`. | `test_run_extraction_v5_live_gate_terminality.py:170-207` monkeypatches `run_doctor_full` and proves refusal before call without consent. |
| `--doctor-auth` | `PROVIDER_CONTACTING_EXPLICIT_INTENT` | `run_extraction_v5.py:9464-9545` builds auth probe modes and calls `call_llm()`; dispatch is at `run_extraction_v5.py:19866-19867` and `20033-20034`. | `test_run_extraction_v5_live_gate_terminality.py:169-207` monkeypatches `run_auth_doctor` and proves refusal before call without consent. |
| `--gemini-list-models` | `PROVIDER_CONTACTING_EXPLICIT_INTENT` | `run_extraction_v5.py:6983-7020` resolves Gemini API key and calls `_get_http_session().get(GEMINI_MODELS_ENDPOINT, ...)`; dispatch is at `run_extraction_v5.py:19754-19755`. | `test_run_extraction_v5_live_gate_terminality.py:171-207` monkeypatches `run_gemini_list_models` and proves refusal before call without consent. |

## Validation Commands

| Command | Exit | Result | Detail |
|---|---:|---|---|
| `pwd; git rev-parse --show-toplevel; git branch --show-current || true; git rev-parse HEAD; git status --short --branch; git diff --name-only` | 0 | `PASS` | Captured implementation branch state before triage. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback -q` | 1 | `FAIL_BASELINE_COMPARISON_IMPL` | Implementation branch failure: escalation_trigger observed provider_failure, expected None. |
| `pytest services/repo-truth-extractor/tests/test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai -q` | 1 | `FAIL_BASELINE_COMPARISON_IMPL` | Implementation branch failure: DEFAULT_TARGET_POLICY observed cost, expected balanced_openrouter. |
| `git worktree add --detach /Users/hue/.codex/worktrees/rte-pkt-01-base-triage a4214ca5bf431e1b59791661e2b664a6cd24c1da` | 0 | `PASS` | Created clean detached base comparison worktree. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback -q (base worktree)` | 1 | `FAIL_BASELINE` | Clean base failure: same escalation_trigger provider_failure vs None assertion. |
| `pytest services/repo-truth-extractor/tests/test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai -q (base worktree)` | 1 | `FAIL_BASELINE` | Clean base failure: same DEFAULT_TARGET_POLICY cost vs balanced_openrouter assertion. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py -q` | 0 | `PASS` | 26 passed; warning: unknown pytest config option asyncio_mode. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py` | 0 | `PASS` | No syntax errors. |
| `git diff --check` | 0 | `PASS` | No whitespace errors. |
| `git status --short --branch` | 0 | `PASS` | Dirty state is limited to allowed runtime/test/proof outputs. |

## No Live Calls Attestation

- live extraction: NOT_RUN
- provider calls: NOT_RUN
- batch submit/poll/retrieve/cancel against a provider: NOT_RUN
- external research: NOT_RUN
- provider credentials required: NOT_RUN

## Commit Readiness

`READY_FOR_REVIEW_CLEAN` for targeted review and commit preparation. No commit was created because intake explicitly said not to commit yet.
