# AGY run record (corroborating)

Does not govern. AGY read the same 162,933-byte prompt as Grok, so unlike PR 1498 its scope is the whole change.

| Check | Result |
|---|---|
| Result status | SUCCESS, 283 s |
| Prompt bytes (cap about 192,000) | 162,933 |
| `<truncated N bytes>` in `gen_metadata` | none |
| Delivery token at the very end, echoed | True |
| Delivery check section found in `gen_metadata` | True |
| Lines sampled across the prompt, found in `gen_metadata` | 6 of 6 |
| Input tokens | 61,987 |
| Step types | ['agent_response', 'user_input'] (2 rows in the conversation database) |
| Tools offered, tools used | 60, 0 |

Requested `gemini-4-argon-high`. Self-reported `Gemini 4 Argon (High)`. Provider-attested identity UNKNOWN.
AGY's CLI grants always-proceed permissions, so containment is observed from the stream and the database, not enforced.

Verdict PASS_WITH_RISKS, 4 findings.

## Exit code

`agy exit=137 2026-11-05T06:27:18Z`. The stream ended with status SUCCESS, but the agy process did not exit, the same hang seen on PR 1498. The wrapper's watchdog saw the result event, waited 30 s, copied the conversation database, sent SIGTERM (which agy ignored), then SIGKILL 10 s later. Exit 137 records that kill, not the audit.

Watchdog record (`AGY_WATCHDOG.txt`):

```text
result event seen at 2026-11-05T06:26:38Z
stopping pid 26898 after waited=320s seen=290 at 2026-11-05T06:27:08Z
```

`AGY_CLI_LOG.txt` lines 145-146 show the stream ending at 23:26:33 local and line 148 shows the signal at 23:27:08.
