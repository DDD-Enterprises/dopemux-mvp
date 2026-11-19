# AGY run record (governing auditor)

Label: **AUDITOR_WRITTEN_RAW_RETAINED**. The raw stream, stderr and the wrapper's exit line were written to durable storage
and are copied here unchanged (`AGY_OUTPUT_RAW.txt`, `AGY_STDERR.txt`, `AUDIT_INVOCATION.txt`). The raw stream is JSON Lines;
the command wrote it as `AGY_OUTPUT_RAW.jsonl`, and the bundle names it `.txt` for the proof-only allowlist (same bytes).

| Evidence | Where | What it shows |
|---|---|---|
| Raw stream | `AGY_OUTPUT_RAW.txt` (JSON Lines) | step types ['agent_response', 'system_message', 'user_input'] only (no tool steps); final `result` status SUCCESS, 44 s, usage {"input_tokens": 18215, "output_tokens": 3369, "thinking_tokens": 2565, "cache_read_tokens": 0, "total_tokens": 21584} |
| Verdict | `AGY_VERDICT.json` | the JSON object in the `result.response` string, parsed unchanged |
| Exit | `AUDIT_INVOCATION.txt` | wrapper line `agy exit=0 2026-11-16T23:35:53Z` (observed, not inferred) |
| CLI log | `AGY_CLI_LOG.txt` (redacted copy, see `REDACTIONS.md`; original in custody `cli-20261116_163505.log`) | CLI 1.5.9, print mode, `promptLength=10510`, `model="gemini-4-argon-high"` (line 65) |
| Conversation store | custody `fea26bbf-fb3a-422d-8713-69c121491877.db` (not committed: binary) | sha256 in `CUSTODY.md` |

## Model identity

- Requested: `gemini-4-argon-high` (operator route, "Gemini 4 Argon (High)").
- Log: `Model ID gemini-4-argon-high not in local config, defaulting` (line 1), then `Resolving model gemini-4-argon-high` (line 87).
- Provider-attested identity: **UNKNOWN**. Recorded as the schema family value `auditor_model: gemini`, as for PR #1515 and PR #1447.

## Containment

Observed, not enforced: AGY's CLI settings grant a list of shell commands with `toolPermission=always-proceed` (log line 68), and the
stream's `init` event lists 60 tools with `permission_mode` `always-proceed`. The sealed dir held only
the prompt and the stream has no tool steps.
