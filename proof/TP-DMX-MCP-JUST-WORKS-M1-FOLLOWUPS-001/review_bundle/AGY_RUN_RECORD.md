# AGY run record (governing auditor)

Label: **AUDITOR_WRITTEN_RAW_RETAINED**. The raw stream, stderr and the wrapper's exit line were written to
durable storage and are copied here unchanged (`AGY_OUTPUT_RAW.txt`, `AGY_STDERR.txt`,
`AUDIT_INVOCATION.txt`). The command wrote the stream as `AGY_OUTPUT_RAW.jsonl`; the bundle names it `.txt`
for the proof-only allowlist (same bytes).

| Evidence | Where | What it shows |
|---|---|---|
| Raw stream | `AGY_OUTPUT_RAW.txt` (228 JSON lines) | events: init 1, step_update 226, result 1. Step types: user_input 1, system_message 1, agent_response 224 (step indices 0-2); no tool steps. Final result: status SUCCESS, 75.2 s, 1 turn, usage input 46761, output 9014, thinking 7222, cache_read 0, total 55775 |
| Verdict | `AGY_VERDICT.json` | the JSON object in the result's `response` string, parsed unchanged |
| Exit | `AUDIT_INVOCATION.txt` | wrapper line `agy exit=0 2026-11-20T03:10:57Z` (observed, not inferred) |
| Stderr | `AGY_STDERR.txt` | empty (0 bytes) |
| CLI log | `AGY_CLI_LOG.txt` (redacted copy, see `REDACTIONS.md`; original in custody) | CLI 1.5.13, print mode, `promptLength=102839`, `model="gemini-4-argon-high"` (line 68) |
| Conversation store | custody `fe89e363-4bab-47da-88ef-05dee1a81345.db` (not committed: binary) | sha256 in `CUSTODY.md`. Rows per table: trajectory_meta 1, steps 3, gen_metadata 1, executor_metadata 1, parent_references 0, trajectory_metadata_blob 1, battle_mode_infos 0. Cells holding the whole prompt verbatim (102839 bytes): steps 1, gen_metadata 1, so the diff reached the model untruncated |

## Model identity

- Requested: `gemini-4-argon-high`. The operator chose the AGY route for this PR; the model is the one the
  operator approved for the PR #1516 AGY audit, reused here by the supervising session.
- Log: `Model ID gemini-4-argon-high not in local config, defaulting to CCPA` (line 1), then
  `Resolving model gemini-4-argon-high` (lines 89, 121) and the backend label
  "Gemini 4 Argon (High)" (lines 90, 106, 109).
- Provider-attested identity: **UNKNOWN**. Recorded as the schema family value `auditor_model: gemini`, as for
  PR #1516.

## Containment

Observed, not enforced. The CLI ran with `--sandbox` (line 74: terminal sandbox enabled), but AGY's
CLI settings grant a list of shell commands (line 71; allow=259 on line 70) and the stream's
`init` event lists 60 tools with `permission_mode: always-proceed`. The sealed dir held only the
prompt, and the stream has no tool steps.
