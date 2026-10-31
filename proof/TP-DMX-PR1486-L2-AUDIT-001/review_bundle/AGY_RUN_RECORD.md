# AGY run record (governing auditor)

Label: **TRANSCRIPT_RECOVERED_NOT_AUDITOR_WRITTEN**. The raw stream (`AUDIT_OUTPUT_RAW.jsonl`), stderr and invocation file lived in the
session scratchpad and were deleted by a disk cleanup around 2026-10-30T12:29Z. What remains:

| Evidence | Where | What it shows |
|---|---|---|
| AGY conversation store | custody copy `agy/0605eb07-a5e9-40ce-a078-59ac6912f0e5.db` (sha256 `5c6ecb34feeb7f0ef5f68a1d935a4bb2f39fbf894bd3046a6756a5f5f5777e5c`, not committed: binary) | 2 steps only: user input (type 14) and agent response (type 15), both status 3; no tool steps |
| AGY CLI log | `AGY_CLI_LOG.txt` | CLI 1.4.11, print mode, model `gemini-4-argon-high`, promptLength 154340, terminal sandbox on, workspace = sealed dir |
| Session transcript | `~/.claude/projects/-Users-hue-code-dopemux-mvp/d3cf0485-7bed-42f2-bab3-e34e07536645.jsonl` | exact command (11:25:44Z), harness exit-code-0 notice (11:27:20Z), parse result (11:27:24Z): user_input 1, agent_response 245, PASS_WITH_RISKS, F-1/F-2 LOW |
| Recovered verdict | `AGY_VERDICT_RECOVERED.json` | first complete JSON object with `verdict` in the final step; the step holds it twice (streamed + final) and both decode identically |

## Model identity

- Requested: `gemini-4-argon-high` (operator-requested route).
- Client-recorded: the conversation's generation metadata names the selection "Gemini 4 Argon (High)" with
  `model_enum MODEL_PLACEHOLDER_M417`. At startup the log also says `Model ID gemini-4-argon-high not in local
  config, defaulting to CCPA` / `Model resolved via default`, then `Resolving model gemini-4-argon-high`.
- Provider-attested identity: **UNKNOWN**. Recorded as the schema's family value `auditor_model: gemini`, as for PR #1447.

## Containment

- Containment is **observed, not enforced**: AGY's CLI settings allow a list of shell commands with
  `toolPermission=always-proceed` (log line 122). The sealed dir held only the prompt, and the transcript and the
  parsed stream show no tool steps.

## Exit code

`exit_code: 0` is **inferred**: AGY emitted its final `result` event and the wrapping command exited 0. The
literal `agy exit=$?` line went to a task output file that was deleted unread.
