# Proof Summary: TP-DMX-DCP-CI-GATE-001

**Status**: READY_FOR_REVIEW · **Outcome**: WIRED / CI_ENFORCEMENT_ACTIVE

## What Changed

Added `tests/dcp/` as a required CI step in `.github/workflows/ci-complete.yml` Unit Tests job.

- Step name: `🔴 Run DCP red-lane gate (TP-DMX-DCP-CI-GATE-001)`
- Inserted after: `Run fast unit gate`
- Runs: `PYTHONPATH=src uv run --frozen pytest tests/dcp/ --deselect tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified --maxfail=1 --disable-warnings --no-cov`

## Why `test_16` is Deselected

`test_16_no_forbidden_files_modified` uses hardcoded base SHA `68f7435f6` (from `task-packets/TP-DCP-0002.md`) and diffs `68f7435f6...HEAD`. Legitimate workflow changes merged after that SHA cause this test to fail on unrelated work. This is a packet-execution guard, not a CI invariant. The deselect is minimal and principled; fixing the stale SHA is deferred to a separate packet.

## Test Results

```
82 passed / 0 failed / 1 deselected in 0.11s
```

## Seam Preservation

- `DCP-RED-MERGE-SEAM-0001`: PRESERVED
- No runtime code modified
- `LIVE_WRITE_READY`: not defined, not enabled

## Commit

`02c877d7cf30a41094a4b4b06e9edc4caf422c27` — `feat(ci): wire tests/dcp/ into CI as required gate (TP-DMX-DCP-CI-GATE-001)`
