# Auditor Report — TP-DMX-MERGE-INTEGRITY-0001

## Status

`FAILED` for the historical exact-head audit receipt; `BLOCKED` for the rebased successor until a new receipt exists.

## Observed receipt

- Audit workflow run `29210810173` verified trusted source and selected the candidate head, but the PAL runner crashed before emitting an executed audit result.
- The emitted artifact `8265092641` is diagnostic evidence only: `executed=false` and nested audit status `SKIPPED`.
- PR Steward run `29210832105` correctly failed closed and did not emit a final readiness artifact.

## Current boundary

PR #1044 repaired the trusted runner import path on `main`. Historical AGY audits and the repaired runtime are not final-head evidence for this candidate. The required independent auditor verdict is `NOT_RUN` until trusted `embedded-audit` completes on the final pushed head.
