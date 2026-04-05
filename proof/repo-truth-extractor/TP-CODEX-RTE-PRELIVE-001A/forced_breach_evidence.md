# Forced breach evidence

## Test

- name: `test_forced_breach_blocks_all_later_batch_watch_calls`
- file: `services/repo-truth-extractor/tests/test_spend_ledger.py`

## Scenario

- cap: `0.00001`
- mode: batch watch
- job 1 result carries enough usage to breach the cap
- job 2 is queued behind job 1 in the batch job index

## Assertions proved

- breach occurs
- first partition output is written:
  - `A1__A_P0001.json` exists
- later billable work does not start:
  - `A1__A_P0002.json` does not exist
  - `fake_client.polled == ["job-1"]`
  - `fake_client.fetched == ["job-1"]`
  - `fake_client.post_breach_call_count == 0`

## Interpretation

This is the required no-post-breach-call proof for TP-001A:

- the current allowed work completes cleanly enough to persist its output
- the later queued billable call is never polled or fetched after the breach
