# Rerun Plan — TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001

## Prerequisites

1. Verify tests pass:
   ```bash
   pytest -q services/repo-truth-extractor/tests/test_tp_rtx_v5_phase_recovery_hardening.py
   # Expected: 23 passed
   ```

2. Ensure `FULL_RUN` run directory exists:
   ```bash
   ls extraction/repo-truth-extractor/v3/runs/FULL_RUN/
   ```

## Phase A Rerun Sequence

### A12 — CLI_COMMAND_SURFACE.json (subcommands fix)

After the `allow_empty_array_fields: [subcommands]` fix in `artifacts.yaml`, partitions
that previously failed with `contract_empty_key:subcommands` should resume as SKIP.

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --phases A \
  --steps A12 \
  --resume \
  --run-id FULL_RUN \
  --run-root extraction/repo-truth-extractor/v3/runs
```

### A99 — REPOCTRL_QA.json (issues/status fix)

After the `allow_empty_array_fields: [issues, status]` fix, A99 QA partitions with
`issues: []` should resume as SKIP.

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --phases A \
  --steps A99 \
  --resume \
  --run-id FULL_RUN \
  --run-root extraction/repo-truth-extractor/v3/runs
```

## Phase H Rerun Sequence

### H9 — HOMECTRL_QA.json (issues/status fix + request_meta resume fix)

H9 partitions affected by both the contract gate failure and the resume short-circuit.
After this fix, partitions with `failure_type` in `request_meta` but valid artifacts
will resume as SKIP rather than RERUN.

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --phases H \
  --steps H9 \
  --resume \
  --run-id FULL_RUN \
  --run-root extraction/repo-truth-extractor/v3/runs
```

## Expected Outcome

- Previously failing partitions with `issues: []` or `subcommands: []` → SKIP
- Previously rerun-looping H9 partitions with `failure_type` in `request_meta`
  + valid artifacts → SKIP
- Net: fewer RERUN decisions, faster phase completion

## Verification

After rerun, check coverage:
```bash
cat extraction/repo-truth-extractor/v3/runs/FULL_RUN/qa/COVERAGE_ROLLUP.json | \
  python -m json.tool | grep -E '"status"|"failed"'
```
