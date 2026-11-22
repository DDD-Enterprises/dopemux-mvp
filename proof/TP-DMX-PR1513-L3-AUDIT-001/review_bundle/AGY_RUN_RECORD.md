# AGY run record (corroborating)

Does not govern. AGY read the same 187,822-byte prompt as Grok, so its scope is the whole change.

| Check | Result |
|---|---|
| Result status | SUCCESS, 201 s |
| Prompt bytes (AGY keeps about 192,000) | 187,822 |
| `<truncated N bytes>` in `gen_metadata` | none |
| Delivery token at the very end, echoed | True |
| Delivery check section and token found in `gen_metadata` | True |
| Lines sampled across the prompt, found in `gen_metadata` | 7 of 7 (last plain line: True) |
| Input tokens | 77,568 |
| Step types | ['agent_response', 'system_message', 'user_input'] (3 rows in the conversation database) |
| Tools offered, tools used | 60, 0 |

Requested `gemini-4-argon-high`. Self-reported `Gemini 4 Argon (High)`. Provider-attested identity UNKNOWN.
AGY's CLI grants always-proceed permissions, so containment is observed from the stream and the database, not enforced.
Wrapper: `agy exit=0 2026-11-20T04:53:49Z`. The wrapper's own status was 1 because its last line printed a watchdog file that did not exist; the audit exited 0.

Verdict PASS_WITH_RISKS, 5 findings.
