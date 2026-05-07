---
id: use-gpt-researcher
title: Use GPT-Researcher for Deep Research
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-06'
last_review: '2026-05-06'
next_review: '2026-08-06'
prelude: How to use the gpt-researcher MCP server for autonomous multi-source research, with ADHD-friendly workflow recipes and the /research:* slash commands.
---
# Use GPT-Researcher for Deep Research

The `gpt-researcher` MCP server runs an autonomous research agent that coordinates multiple search engines (Tavily, Exa, Bing, DuckDuckGo, Google) to produce synthesized findings with citations. Use it when a single web search isn't enough.

**TL;DR**:
- Quick fact (< 30s) → `/research:quick "..."` or `mcp__gpt-researcher__quick_search`
- Deep dive (2–10 min) → `/research:deep "..."`, wait for the completed result, then `/research:report`
- Already running on port 3009 inside the dopemux compose stack as `dopemux-mcp-gptr-mcp`

## When to use it (vs. Exa)

| Need | Tool |
|---|---|
| Quick fact, single doc lookup, < 5s | Exa (`mcp__exa__search`) |
| Specific API or library reference | Context7 |
| Multi-source investigation, comparison, synthesis | **gpt-researcher** |
| Anything you'd otherwise spend 30+ minutes Googling | **gpt-researcher** |
| Citations + structured report | **gpt-researcher** |

## Prerequisites

1. Stack running: `docker compose -f compose.yml --env-file .env ps gptr-mcp` shows `Up ... (healthy)`.
2. API keys in `.env` (the agent fans out across providers; without keys the relevant searches just skip):
   - `OPENAI_API_KEY` — required for the LLM that synthesizes results
   - `TAVILY_API_KEY` — strongest research signal
   - `EXA_API_KEY` — neural search complement
3. Restart `gptr-mcp` after editing `.env`: `docker compose -f compose.yml up -d gptr-mcp`.

## MCP tools

All five tools are available via `mcp__gpt-researcher__<name>`:

| Tool | Purpose | Time |
|---|---|---|
| `quick_search` | Parallel multi-engine search, no synthesis | ~10–30s |
| `deep_research` | Full pipeline: search → scrape → synthesize → cite | 2–10 min |
| `write_report` | Format a previous `deep_research` result | 30–60s |
| `get_research_sources` | Pull source list from a `research_id` | < 1s |
| `get_research_context` | Pull synthesized context from a `research_id` | < 1s |

`deep_research` waits for the research run to complete, then returns a `research_id`. Save it — every other tool can refer back to the completed run later.

## Slash commands

For ADHD-friendly default flows the project ships three slash commands. Each calls the underlying MCP tool with sensible defaults and writes outputs in conventional locations.

- **`/research:quick "<query>"`** — fast lookup, prints a synthesis inline. No state saved.
- **`/research:deep "<query>"`** — runs `deep_research`, waits for completion, and saves the returned `research_id` to ConPort active context.
- **`/research:report [research_id]`** — formats a finished research session into `claudedocs/research/<slug>-<date>.md`. If you omit `research_id`, it pulls the most recent one from ConPort.

## ADHD workflow recipe

This pattern works well when you have research to do but not the focus to read 15 sources:

1. **Frame the question** in one sentence. If you can't, your task is "narrow the question," not "research it."
2. **Run**: `/research:deep "..."`. Wait for the command to return, then note the `research_id` shown in the response.
3. **Wait for completion** — this is the 2–10 minute part. Keep the session alive until the command returns; the saved ID exists only after completion.
4. **Format** the completed run with `/research:report`, or inspect raw context with `mcp__gpt-researcher__get_research_context`.
5. **Read the synthesis** first (top of the report). If it answers your question, stop. If not, scan the sources list and follow up with a focused `/research:quick` on the gap.

The `research_id` is your durable handle after `/research:deep` returns: leave the session, restart Claude Code, come back tomorrow — the report still generates from the same completed research run. If the session is interrupted before `/research:deep` returns, rerun the command because no completed ID is guaranteed to be saved yet.

## Cost & timing

- `quick_search`: ~10–30s, dominated by network. Cost: minimal (a few cents in OpenAI tokens).
- `deep_research`: 2–10 min. Cost: usually $0.10–$1.00 in OpenAI tokens depending on depth and source count.
- `write_report`: 30–60s. Cost: a few cents.

## Verification

```bash
# Container is up and healthy
docker compose -f compose.yml ps gptr-mcp

# Installed gpt-researcher is at the pinned version
docker exec dopemux-mcp-gptr-mcp pip show gpt-researcher | grep Version
# Expected: Version: 0.14.8 (or newer if Dockerfile build-arg was overridden)

# End-to-end smoke test from a Claude Code session
/research:quick "current latest stable version of fastmcp on PyPI"
```

## Troubleshooting

**Container restarts or stays unhealthy.** Check logs: `docker logs dopemux-mcp-gptr-mcp --tail 60`. Most common cause is `OPENAI_API_KEY` missing or invalid — the agent boots, but every research request fails on first LLM call.

**`/research:*` slash commands not found.** They live at `.claude/commands/research-*.md` in this repo. They surface in any Claude Code session whose cwd is the dopemux-mvp checkout.

**Research stalls forever.** Kill it: `docker exec dopemux-mcp-gptr-mcp pkill -f gpt-researcher` and start over with a narrower query. Default queries that ask for "everything about X" tend to spiral.

**Want a different upstream version of gpt-researcher.**
```bash
docker compose -f compose.yml build \
  --build-arg GPT_RESEARCHER_VERSION=<version> \
  gptr-mcp
docker compose -f compose.yml up -d gptr-mcp
```

## See also

- `~/.claude/MCP_GPTResearcher.md` — full MCP tool reference
- `~/.claude/MCP_Exa.md` — when to prefer Exa
- `.claude/commands/research-quick.md`, `research-deep.md`, `research-report.md` — slash command implementations
- `docker/mcp-servers-source/gptr-mcp/Dockerfile` — image build
