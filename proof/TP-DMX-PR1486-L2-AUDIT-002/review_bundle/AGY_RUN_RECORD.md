# AGY run record (governing auditor, round 6)

Label: **AUDITOR_WRITTEN_RAW_RETAINED**. The raw stream, stderr and the wrapper's exit line were written to durable storage
and are copied here unchanged (`AGY_OUTPUT_RAW.jsonl`, `AGY_STDERR.txt`, `AUDIT_INVOCATION.txt`).

| Evidence | Where | What it shows |
|---|---|---|
| Raw stream | `AGY_OUTPUT_RAW.jsonl` | step types ['agent_response', 'user_input'] only (no tool steps); final `result` status SUCCESS, 297 s, usage {"input_tokens": 65184, "output_tokens": 5700, "thinking_tokens": 3808, "cache_read_tokens": 0, "total_tokens": 70884} |
| Verdict | `AGY_VERDICT.json` | the JSON object in the `result.response` string, parsed unchanged |
| Exit | `AUDIT_INVOCATION.txt` | wrapper line `agy exit=0 2026-11-01T03:27:49Z` (observed, not inferred) |
| CLI log | `AGY_CLI_LOG.txt` (redacted copy, see `REDACTIONS.md`; original in custody `agy/cli-20261031_202247.log`) | CLI 1.4.12, print mode, `promptLength=169875`, `model="gemini-4-argon-high"`, terminal sandbox on |
| Conversation store | custody `agy/d2d128f6-9db9-466a-913b-536140a5ce4f.db` (not committed: binary) | sha256 in `CUSTODY.md` |

## Model identity

- Requested: `gemini-4-argon-high` (operator route, listed by `agy models` as "Gemini 4 Argon (High)" on 2026-11-01).
- Log: `Model ID gemini-4-argon-high not in local config, defaulting to CCPA` (line 1), then `Resolving model gemini-4-argon-high` (line 144).
- Provider-attested identity: **UNKNOWN**. Recorded as the schema family value `auditor_model: gemini`, as for r5 and PR #1447.

## Containment

Observed, not enforced: AGY's CLI settings grant a list of shell commands with `toolPermission=always-proceed` (log line 110), and the
stream's `init` event lists 60 tools with `permission_mode` `always-proceed`. The sealed dir held only
the prompt and the stream has no tool steps.
