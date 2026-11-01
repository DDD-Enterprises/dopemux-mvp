# Successor note: R3's interrupted AGY run has a measured usage figure (corrects the R4 records)

Additive. It lives in the R6 bundle, not in the R4 bundle: the local acceptance engine admits only `proof/pr_merge/embedded-audit/pr-1482/` and `proof/MACRO-DMX-ROUTE-LEDGER-001-R6/` as changes after the audited head, so the R3 and R4 bundles stay byte-identical to the audited head. No file of the R4 bundle is edited. R4's `ALLOWANCES.json` is hash-pinned by that round's macro packet and listed in its `SHA256SUMS_PACKAGE.txt`, and it is byte-identical to the issuance snapshot under `task-packets/`, so it stays as issued; this note is the correction. Raised by review comments on PR 1482 and checked against the retained R3 stream by the R6 coordinator. The R3 side is in `SUCCESSOR_NOTE_R3_RESULT_EVENT.md` in this same directory.

## The fact
Line 3 of `proof/MACRO-DMX-ROUTE-LEDGER-001-R3/review_bundle/AGY_AUDIT_STREAM.txt` is a `result` event: status `ERROR`, `error` and `finished_reason` `interrupted`, `duration_seconds` 60.661235, empty `response`, `usage` input 55,666, output 5,453, thinking 5,453, **total 61,119**. No verdict was produced; USD cost is UNKNOWN.

## What it corrects in the R4 bundle (`proof/MACRO-DMX-ROUTE-LEDGER-001-R4/review_bundle/`)
| Place | As written | Corrected |
|---|---|---|
| `ALLOWANCES.json` `basis` (R3 sunk cost) | "about 26k AGY probe tokens, the AGY real run stopped without a usage figure" | R3 AGY sunk spend: 26,443 probe tokens (12,963 + 13,480) plus 61,119 tokens for the interrupted real run, 87,562 in all; USD UNKNOWN. These are R3 sunk cost, separate from R4's budget, which is unchanged. The later sentence "The AGY run is UNMEASURED at issuance" described R4's own run and stays true. |
| `ALLOWANCE_LEDGER.json` `r3_sunk_cost_not_counted.agy_real_run` | "stopped, no usage figure" | "stopped with a result event: status ERROR (interrupted), 60.66 s, 61,119 tokens, no verdict"; add the 61,119 to `agy_probe_tokens` 26,443 for 87,562 tokens. Not counted against R4's caps, as before. |
| `SUPERSEDED_R3_NOTE.md` R3 W03 row | "no response, no result event, no verdict" | no response and no verdict, as written; but there WAS a result event (status ERROR, interrupted, 61,119 tokens). |

## What does not change
The R4 allowance caps, the R4 ledger's measured values for R4's own workstreams, the R3 outcome (one attempt consumed, no verdict, stopped by the coordinator at 2026-10-30T09:34:56Z), and the reason R3 was superseded.
