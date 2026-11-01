# AGY run record (governing auditor, round 7)

Label: **AUDITOR_WRITTEN_RAW_RETAINED**. The raw stream, stderr and the wrapper's exit line were written to durable storage
and are copied here unchanged (`AGY_OUTPUT_RAW.txt`, `AGY_STDERR.txt`, `AUDIT_INVOCATION.txt`). The raw stream is JSON Lines;
the command wrote it as `AGY_OUTPUT_RAW.jsonl`, and the bundle names it `.txt` for the proof-only allowlist (same bytes).

| Evidence | Where | What it shows |
|---|---|---|
| Raw stream | `AGY_OUTPUT_RAW.txt` (JSON Lines) | step types ['agent_response', 'user_input'] only (no tool steps); final `result` status SUCCESS, 673 s, usage {"input_tokens": 69051, "output_tokens": 6650, "thinking_tokens": 4935, "cache_read_tokens": 0, "total_tokens": 75701} |
| Verdict | `AGY_VERDICT.json` | the JSON object in the `result.response` string, parsed unchanged |
| Exit | `AUDIT_INVOCATION.txt` | wrapper line `agy exit=0 2026-11-01T06:58:38Z` (observed, not inferred) |
| CLI log | `AGY_CLI_LOG.txt` (redacted copy, see `REDACTIONS.md`; original in custody `cli-20261031_234720.log`) | CLI 1.4.12, print mode, `promptLength=183090`, `model="gemini-4-argon-high"` (line 119) |
| Conversation store | custody `c41fdda5-e689-44ff-9abe-aac918c958ed.db` (not committed: binary) | sha256 in `CUSTODY.md` |

## Model identity

- Requested: `gemini-4-argon-high` (operator route, "Gemini 4 Argon (High)").
- Log: `Model ID gemini-4-argon-high not in local config, defaulting` (line 1), then `Resolving model gemini-4-argon-high` (line 144).
- Provider-attested identity: **UNKNOWN**. Recorded as the schema family value `auditor_model: gemini`, as for r5, r6 and PR #1447.

## Containment

Observed, not enforced: AGY's CLI settings grant a list of shell commands with `toolPermission=always-proceed` (log line 122), and the
stream's `init` event lists 60 tools with `permission_mode` `always-proceed`. The sealed dir held only
the prompt and the stream has no tool steps.
