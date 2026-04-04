# TP-CODEX-RTE-PRELIVE-001 Implementer Report

## Scope completed

- upgraded `spend_ledger.py` to persist model-aware totals, provider totals, and fallback counters while remaining backward-compatible with older ledger files
- added runtime helpers in `run_extraction_v5.py` for:
  - projected pre-call cap checks
  - runtime accumulation
  - submit-time reservation for batch and async lanes
  - persisted `cost_aborted` run state
- instrumented verified billable paths in the v5 runtime and utility probe surfaces
- added `services/repo-truth-extractor/tests/test_spend_ledger.py`
- updated operator docs for `--max-cost-usd`, ledger location, reservation semantics, and abort behavior

## Runtime behavior now enforced

- every verified billable call path enters the spend ledger before additional billable work can continue
- `--max-cost-usd` now blocks both:
  - projected pre-call or pre-submit work
  - post-response over-cap states after accumulation
- live runs with a cost cap force single-worker partition execution so stop-on-breach remains deterministic
- cost abort writes `COST_ABORT.json` and updates manifest, coverage, resume, proof, and dashboard artifacts

## Validation summary

- `pytest services/repo-truth-extractor/tests/ -v`
  - `505 passed`
- `pytest -k "spend or cost or breach" -v`
  - `6 passed, 5 skipped`
- `python services/repo-truth-extractor/extraction_hygiene.py scan`
  - pass with one warning and zero errors
- `python scripts/repo_truth_extractor_promptset_audit_v4.py`
  - pass
- `python services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - fails `NO_GO` for environment/readiness reasons outside this packet's code change:
    - missing `XAI_API_KEY`
    - PAL validation unavailable
    - online preflight skipped

## Remaining drift / uncertainty

- `validate_pre_live_gate_v25.py` still reports pre-existing S-phase stale artifact-map findings and environment readiness blockers
- S_INT now uses the cost-enforcement helpers, but its top-level flow still exits directly instead of writing the full v5 run-artifact bundle because that flow does not currently build the normal run directory contract before execution
- provider-billing truth remains external; the ledger is still a conservative internal estimate, not authoritative billing
