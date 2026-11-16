# Grok run record (governing auditor)

Label: **AUDITOR_WRITTEN_RAW_RETAINED**. The raw stream, stderr and the wrapper's exit line were written to durable storage
and are copied here (`GROK_OUTPUT_RAW.txt`, `GROK_STDERR.txt`, `AUDIT_INVOCATION.txt`).

| Evidence | Where | What it shows |
|---|---|---|
| Raw stream | `GROK_OUTPUT_RAW.txt` (JSON Lines) | `init.tools == []`, 0 tool_use blocks; result success, 425 s, reported cost USD 0.04193424 |
| Verdict | `GROK_VERDICT.json` | the JSON object in the final text block (`GROK_RESPONSE.txt`), parsed unchanged |
| Exit | `AUDIT_INVOCATION.txt` | wrapper line `grok exit=0 2026-11-16T12:11:52Z` (observed, not inferred) |

## Model identity

- Requested: `grok-4.7`; receipt model in the stream: ['grok-4.7-build'].
- Provider-attested identity beyond the receipt: **UNKNOWN**. Recorded as `auditor_model: grok-4.7`, which the schema allows for `grok-cli`.

## Containment

`--disallowed-tools` (the denylist from the PR 1509 and 1515 probes: their `init.tools` plus x_search, web_search, web_fetch and
Agent), `--deny` for the named tools, a no-tools system prompt, and a sealed dir holding only the prompt. The probe and the audit
run both report `init.tools == []`. The harness still injects a system block and home-level context, so this is containment by
an empty tool list, not by an empty context.
