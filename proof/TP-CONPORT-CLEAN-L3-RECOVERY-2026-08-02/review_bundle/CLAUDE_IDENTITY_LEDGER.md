# Claude Code formal auditor identity — PR #1188

| Field | Value |
|---|---|
| implementer | grok-4.5 |
| auditor independence | Claude Code CLI session ≠ implementer |
| runner / version | Claude Code CLI **2.1.220** |
| requested model | `sonnet` (`--model sonnet`) |
| configured / harness | sonnet (cli flag) |
| response_claimed | Sonnet (report: Claude Code CLI / Sonnet) |
| auth method | claude.ai OAuth (auth status loggedIn=true) |
| api provider | firstParty (Anthropic) |
| provider_attested | Anthropic first-party via Claude Code OAuth (houston@krohman.org org) |
| proxy_reported | N/A (first-party; not LiteLLM proxy) |
| content_head_audited | `95bdf0015730ab3087cf71e07eca2d4425b214ac` |
| verdict | PASS_WITH_RISKS |

Codex path previously BLOCKED_AUDITOR_IDENTITY (provider_attested UNKNOWN).
Supervisor-compatible Tier-1 route: Claude Code CLI per docs/ops/embedded-audit.md.
