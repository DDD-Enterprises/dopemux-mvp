# Phase Readiness Checklist — TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001

## Pre-Flight

- [x] `git status --porcelain` clean before work began
- [x] All changes on `main` branch
- [x] `pytest services/repo-truth-extractor/tests/ -q` passes (266 tests)
- [x] `pytest test_tp_rtx_v5_phase_recovery_hardening.py -v` passes (23 tests)

## Code Changes Completed

- [x] `artifacts.yaml`: `allow_empty_array_fields` added to REPOCTRL_QA, HOMECTRL_QA, CLI_COMMAND_SURFACE
- [x] `phase_contract_map.py`: `allow_empty_array_fields` read and propagated into artifact_payload
- [x] `structured_output_contracts.py`: `normalize_required_array_fields()` added
- [x] `structured_output_contracts.py`: `describe_contract_failure()` skips `[]` for fields in `allow_empty_array_fields`
- [x] `run_extraction_v5.py`: `normalize_required_array_fields` imported
- [x] `run_extraction_v5.py`: `validate_success_partition_output()` demotes `failure_type_request_meta` to warning
- [x] `run_extraction_v5.py`: pre-gate normalization added before `artifacts_pass_contract_gate()`

## Test Coverage

- [x] T1: H9 regression — issues: [], None, "", missing, ["actual issue"]
- [x] T2: Resume — (a) valid + request_meta failure → SKIP, (b) empty artifacts → RERUN, (c) clean → SKIP, (d) corrupted → RERUN
- [x] T3: Phase A — subcommands: [], ["sub1"], None, "", missing
- [x] T4: Cross-phase — REPOCTRL_QA normalization + contract_map assertions for all 3 artifacts

## Known Remaining Work

### A99 / A_P0017 (Non-Actionable)
- Already fixed by `8b0c30ebc`. No further action required.

### Repair Path Normalization
- The plan specifies "Apply same normalization call in the repair path before re-running
  contract gate on repair output."
- The repair path (lines 9668–9890 in `run_extraction_v5.py`) also calls
  `artifacts_pass_contract_gate()` after repair responses.
- This hardening is deferred — the pre-gate normalization in `validate_success_partition_output()`
  covers the resume path. The repair path can be hardened in a follow-up ticket if H9 repair
  loops persist.

### ROOT_CAUSE_SUMMARY.md — Version Mismatch
- Documented above. The v3 path convention for run artifacts is intentional. No code change needed.

## Remaining Phases

Once rerun completes per RERUN_PLAN.md:
- Phase A steps after A12: Verify CLI surface complete
- Phase H steps after H9: Verify home control surface QA complete
- Run final coverage check: `COVERAGE_ROLLUP.json` should show `status: PASS`
