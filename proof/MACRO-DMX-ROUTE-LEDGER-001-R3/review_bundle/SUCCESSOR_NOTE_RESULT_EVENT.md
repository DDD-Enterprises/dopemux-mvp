# Successor note: the interrupted R3 AGY run did produce a result event

Additive. No other file in this bundle is edited, so `SHA256SUMS_AGY.txt` and every hash in it still describe the files as committed. Raised by a review comment on PR 1482 and checked against the retained raw stream by the R6 coordinator.

## The evidence
`AGY_AUDIT_STREAM.txt` has three lines (its sha256 `b305fd1aa5e50990e91530db91d6ce2f9982b4561631ec2d9ece3600f0944229` is the one listed in `SHA256SUMS_AGY.txt`). Line 3 is a `result` event:

| Field | Value |
|---|---|
| `status` | `ERROR` |
| `error` / `finished_reason` | `interrupted` |
| `duration_seconds` | 60.661235 |
| `num_turns` | 1 |
| `response` | empty (0 characters) |
| `usage` | input 55,666; output 5,453; thinking 5,453; cache read 0; **total 61,119** |

## What it corrects
- `AGY_RUN_RECORD.md` lines 3 and 14 (and the stream described as "the init event, the completed user-input step and nothing else"): the third line is not only "the interruption"; it is a `result` event with the values above. There is still no `agent_response` step, no tool step and no answer text.
- `AGY_RUN_RECORD.md` line 19: "real-run tokens and cost UNKNOWN (no usage event)". The stream reports 61,119 total tokens for the real run. Cost in USD stays UNKNOWN (agy reports tokens, not dollars).
- `AGY_RUN_RECORD.md` line 23: `AGY_AUDIT_RESPONSE_RAW.txt` does not exist because the result event carries an empty `response`, not because no result event was produced.
- `AGY_TIMES.txt` line 4: "no result event, no usage figure". The result event reports `duration_seconds` 60.661235 and 61,119 total tokens; the exit code (1, "error: interrupted") and the absence of a verdict are unchanged.

## What does not change
The attempt was consumed and produced no verdict; it was stopped by the coordinator at 2026-10-30T09:34:56Z; probe tokens were 12,963 and 13,480 (26,443 together). The measured R3 AGY spend is therefore 26,443 probe tokens plus 61,119 for the interrupted real run, 87,562 tokens in all, USD UNKNOWN. The R4 records that restate the missing usage figure are corrected by `SUCCESSOR_NOTE_R3_RESULT_EVENT.md` in the R4 bundle.
