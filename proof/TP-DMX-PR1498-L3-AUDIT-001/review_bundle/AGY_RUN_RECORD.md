# AGY run record (corroborating, partial scope)

Does not govern. 13 of 172 changed files, chosen for risk (`AGY_FOCUSED_FILES.txt`). Code outside those files was not visible to AGY.

| Check | Result |
|---|---|
| Result status | SUCCESS, 426 s |
| Prompt bytes (cap about 192,000) | 178,662 |
| `<truncated N bytes>` in `gen_metadata` | none |
| Delivery token at the very end, echoed | True |
| Delivery check section found in `gen_metadata` | True |
| Lines sampled across the prompt, found in `gen_metadata` | 6 of 6 |
| Input tokens | 63,655 |
| Step types | ['agent_response', 'user_input'] (2 rows in the conversation database) |
| Tools offered, tools used | 60, 0 |

Requested `gemini-4-argon-high`. Self-reported `Gemini 4 Argon (High)`. Provider-attested identity UNKNOWN.
AGY's CLI grants always-proceed shell permissions, so containment is observed from the stream, not enforced.

Verdict PASS_WITH_RISKS, 6 findings. Q3 and Q5 are UNKNOWN because the code that answers them was outside AGY's input.

## Exit code

`agy exit=137 2026-11-04T23:17:05Z`. The CLI stream ended at 13:37:41Z with status SUCCESS, but the agy process did not exit and --print-timeout did not stop it. It ignored SIGTERM at 23:15:22Z and was killed with SIGKILL at about 23:17:05Z, so exit 137 records that kill, not the audit.

The raw stream, the conversation database and `AGY_CLI_LOG.txt` (lines 146-148 and 372 show the stream ending and the signal) are unchanged by that kill: the database was last written at 13:38Z and was copied to custody before it.
