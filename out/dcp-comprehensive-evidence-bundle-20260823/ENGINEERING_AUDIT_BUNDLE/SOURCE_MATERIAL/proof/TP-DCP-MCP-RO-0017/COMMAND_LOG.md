# TP-DCP-MCP-RO-0017 Command Log

Base: origin/main @ 46e8e8e69 (TP-0016 merged)

| Command | Result |
| --- | --- |
| Operator live authorization | RECEIVED (session: authorized) |
| Vendor credentials (OpenAI tunnel / Grok / Gemini) | ABSENT |
| Local live: `DCP_ACCEPTANCE_LIVE=1` `PROVIDERS=local` synthetic token | PASS suite (no secret in report) |
| `python -m dcp_facade.acceptance` | release_ready=false; live_not_run=4 (vendor + two-worktree) |
| ChatGPT tunnel / Grok / Gemini live | NOT_RUN |
| Trusted embedded audit | NOT_RUN |

Synthetic local tokens were process-env only and never committed.
