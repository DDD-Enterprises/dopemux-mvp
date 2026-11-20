# AGY run record (governing auditor)

Label: **AUDITOR_WRITTEN_RAW_RETAINED**. The raw stream, stderr and the wrapper's exit line were written to durable storage
and are copied here unchanged (`AGY_OUTPUT_RAW.txt`, `AGY_STDERR.txt`, `AUDIT_INVOCATION.txt`). The raw stream is JSON Lines;
the command wrote it as `AGY_OUTPUT_RAW.jsonl`, and the bundle names it `.txt` for the proof-only allowlist (same bytes).

| Evidence | Where | What it shows |
|---|---|---|
| Raw stream | `AGY_OUTPUT_RAW.txt` (JSON Lines) | step types ['agent_response', 'system_message', 'user_input'] only (no tool steps); final `result` status SUCCESS, 80 s, usage {"input_tokens": 43437, "output_tokens": 4160, "thinking_tokens": 2930, "cache_read_tokens": 0, "total_tokens": 47597} |
| Verdict | `AGY_VERDICT.json` | the JSON object in the `result.response` string, parsed unchanged |
| Exit | `AUDIT_INVOCATION.txt` | wrapper line `agy exit=0 2026-11-20T04:09:27Z` (observed, not inferred) |
| CLI log | `AGY_CLI_LOG.txt` (redacted copy, see `REDACTIONS.md`; original in custody `cli-20261119_210803.log`) | CLI 1.5.13, print mode, `promptLength=83011`, `model="gemini-4-argon-high"` (line 66). The prompt file is 83012 bytes and ends with one newline, which the shell substitution drops, so the whole prompt was sent. The log names this run's conversation id |
| Conversation store | custody `e16290c6-dd8a-4697-9c13-914f5dca4b2a.db` (not committed: binary) | sha256 in `CUSTODY.md` |

## Model identity

- Requested: `gemini-4-argon-high` (operator route, "Gemini 4 Argon (High)").
- Log: `Model ID gemini-4-argon-high not in local config, defaulting` (line 1), then `Resolving model gemini-4-argon-high` (line 90).
- Provider-attested identity: **UNKNOWN**. Recorded as the schema family value `auditor_model: gemini`, as for PR #1516 and PR #1447.

## Containment

Observed, not enforced: AGY's CLI settings grant a list of shell commands with `toolPermission=always-proceed` (log line 72), and the
stream's `init` event lists 60 tools with `permission_mode` `always-proceed`. The sealed dir held only
the prompt and the stream has no tool steps.
