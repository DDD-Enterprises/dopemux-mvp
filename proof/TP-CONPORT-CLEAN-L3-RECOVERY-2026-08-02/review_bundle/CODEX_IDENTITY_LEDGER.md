# Codex identity ledger (PR #1188 preflight)

| Field | Value |
|---|---|
| implementer | grok-4.5 (this session) |
| auditor independence | Codex CLI is not implementer |
| runner / version | OpenAI Codex CLI **0.146.0** |
| requested model | `gpt-5.6-terra` (`codex exec -m gpt-5.6-terra`) |
| configured default (config.toml) | `gpt-5.6-luna` (overridden by -m) |
| response_claimed model | `gpt-5.6-terra` (banner `model: gpt-5.6-terra`) |
| proxy_reported provider | `openai` (banner `provider: openai`) |
| session_id | `019fc54c-21ce-7b41-a850-b4194aedaf01` |
| **provider_attested** | **UNKNOWN** |
| #1187 UNKNOWN exception transfers? | **NO** |

## Stop condition

Supervisor: if provider-attested remains UNKNOWN → `BLOCKED_AUDITOR_IDENTITY`.

Do not treat proxy `provider: openai` or session id as provider attestation.

## Probe raw excerpt

```
Reading additional input from stdin...
OpenAI Codex v0.146.0
--------
workdir: /Users/hue/code/dopemux-mvp/.worktrees/TP-CONPORT-CLEAN-L3-REPAIR
model: gpt-5.6-terra
provider: openai
approval: on-request
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 019fc54c-21ce-7b41-a850-b4194aedaf01
--------
user
Reply with only the word PONG and nothing else.
warning: Under-development features enabled: chronicle. Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in /Users/hue/.codex/config.toml.
warning: Skill descriptions were shortened to fit the 2% skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.
hook: SessionStart
hook: SessionStart Completed
codex
PONG
```
