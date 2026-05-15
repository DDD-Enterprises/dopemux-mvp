# RTE-PKT-08 Remaining Unknowns

## LIVE_VALIDATION_REQUIRED

- Live xAI/OpenAI-compatible batch submit behavior remains unproven.
- Live polling behavior remains unproven.
- Live result retrieval behavior remains unproven.
- Live cancellation behavior remains unproven.
- Actual provider output JSONL and error JSONL shape remains unproven because no downloaded artifacts were found locally and none were retrieved.
- Provider pagination/completeness behavior remains unproven.
- Remote file lifecycle, deletion, retention, and ZDR behavior remain unproven.

## ACCEPTED_WITH_RISK

- Static fixture parsers prove local behavior against synthetic OpenAI-compatible row shapes only.
- `output_file_id` and `error_file_id` are preserved when metadata is present, but this does not prove providers always return those fields.
- Existing local RTE-PKT-07 proof artifacts were not found under `out/`; provider metadata acceptance basis remains conversation-supplied context for this packet.

## MISSING

- Downloaded `*_output.jsonl` artifacts: none found.
- Downloaded `*_error.jsonl` artifacts: none found.

## Governance Conflict

Repo `AGENTS.md` requires a local task packet file and schema validation. The active packet forbids additional task packets and restricts writes outside code/tests/proof output. This run preserved the active packet boundary and did not write `task-packets/`.
