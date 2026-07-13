# Authentication And Terms Matrix

| Tool | Installation | Auth mode | Plan usage confidence | Live status | Evidence and reason |
| --- | --- | --- | --- | --- | --- |
| mechanical | OBSERVED installed | `MECHANICAL` | HIGH | NOT_APPLICABLE | Local Git/Python validators; no model route. |
| grok_build | OBSERVED `grok 0.2.99` | `UNKNOWN` | UNKNOWN | NOT_RUN | Operator allowlist maps `grok` to `grok_build`; absent known API-key environment variables do not prove plan billing or configuration isolation. |
| agy | OBSERVED `agy 1.1.1` | `UNKNOWN` | UNKNOWN | NOT_RUN | Operator-approved for consideration; no safe proof of plan billing, structured output, or complete disablement. |
| gemini_cli | OBSERVED `gemini 0.46.0` | `UNKNOWN` | UNKNOWN | NOT_RUN | Headless and plan-mode flags are observed, but current billing/auth route is unproven. |
| codex | OBSERVED `codex-cli 0.144.1` | `UNKNOWN` | UNKNOWN | NOT_RUN | `exec`, model, sandbox, and approval flags are observed; plan versus API route is unproven. |
| claude_code | OBSERVED `Claude Code 2.1.207` | `UNKNOWN` | UNKNOWN | NOT_RUN | Safe-mode and no-tools controls are observed; subscription/OAuth versus API route is unproven. |
| opencode | OBSERVED `opencode 1.17.13` | `UNKNOWN` | UNKNOWN | NOT_RUN | The configured upstream provider and auth route were not inspected. |
| openrouter | NO_DEDICATED_CLI_OBSERVED | `UNKNOWN` | UNKNOWN | FORBIDDEN | API fallback is static-only. `OPENROUTER_API_KEY` was absent in the boolean-only static receipt; no service call was made. |

Terms, automation rights, dedicated-account portability, and provider retention
posture are `UNKNOWN` unless explicitly represented in tracked local policy. They
require bounded vendor research in the later synthesis, not inference here.
