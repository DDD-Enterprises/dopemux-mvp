---
id: claude-oauth-setup
title: Claude Oauth Setup
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
author: '@hu3mann'
date: '2026-02-05'
prelude: Claude Oauth Setup (explanation) for dopemux documentation and developer
  workflows.
---
# Claude Code OAuth Setup & Troubleshooting

## Overview

Dopemux now uses **Claude Pro Max OAuth authentication** by default instead of API key authentication. This provides a better user experience and avoids API rate limits.

## First-Time Setup

When you run `dopemux start` for the first time, you'll see:

```
⎿  API Error: 401 Invalid API key · Please run /login
```

**This is expected!** Here's how to fix it:

### Step 1: Authenticate with Claude

Inside Claude Code, run:

```
/login
```

This will:
1. Open your browser to Claude's authentication page
1. Ask you to sign in with your Claude Pro Max account
1. Save the OAuth token for future sessions

### Step 2: Restart Claude Code

After authenticating, restart Claude Code:

```bash
# Stop Claude Code (Ctrl+C in the terminal where it's running)
# Then restart:
dopemux start
```

## How It Works

### OAuth-First Architecture

```
┌──────────────┐
│  Claude Code │ ──OAuth──> Anthropic API (Claude Pro Max)
└──────────────┘
       │
       │ (MCP servers get fallback keys)
       v
┌──────────────────────┐
│  MCP Servers         │ ──API Keys──> OpenAI, XAI, etc.
│  - ConPort           │
│  - Zen               │
│  - Serena            │
└──────────────────────┘
```

**Key Points**:

1. **Claude Code uses OAuth** - No ANTHROPIC_API_KEY needed in subprocess
1. **MCP servers use API keys** - For fallback when Pro Max hits limits
1. **No routing layer** - LiteLLM/CCR disabled by default

### Why This Design?

**Previous Design (deprecated)**:
```
Claude Code → CCR → LiteLLM → Anthropic API
```
Problems:
- Complex routing layer
- 401 errors with OAuth
- Unnecessary for Pro Max users

**New Design**:
```
Claude Code → Anthropic API (direct, OAuth)
MCP Servers → Various APIs (with keys)
```
Benefits:
- Simpler architecture
- No 401 errors
- Better performance

## Troubleshooting

### "401 Invalid API key" after OAuth setup

**Cause**: Claude Code might have cached the old API key authentication state.

**Fix**:
```bash
# Clear Claude Code cache
rm -rf ~/.claude/cache
rm -rf ~/.config/Claude\ Code/Cache

# Restart and re-authenticate
dopemux start
# Then run /login inside Claude Code
```

### "ConPort unavailable" error

**Cause**: Database connection issue (network isolation).

**Fix**: Already fixed in recent commits. The postgres-age container is now connected to the unified network.

```bash
# Verify ConPort is running
docker ps --filter "name=mcp-conport"

# Should show: Up X seconds (healthy)
```

### LiteLLM/CCR still starting

**Cause**: Old behavior where `--claude-router` defaulted to `true`.

**Fix**: Already fixed in recent commits. Default is now `false`.

To explicitly disable (if you have an older version):
```bash
dopemux start --no-claude-router
```

## Advanced: Using API Key Instead of OAuth

If you prefer API key authentication (not recommended):

```bash
# Set the API key
export ANTHROPIC_API_KEY=your-key-here

# Start with routing enabled
dopemux start --claude-router
```

This will:
1. Enable LiteLLM proxy
1. Start Claude Code Router
1. Route API calls through the proxy chain

**Note**: This is deprecated and not recommended for Claude Pro Max users.

## Environment Variables

### Required (None!)

With OAuth, no API keys are required for Claude Code itself.

### Optional (for MCP fallback)

```bash
OPENAI_API_KEY=sk-...        # For Zen MCP fallback
EXA_API_KEY=...              # For Exa web search
XAI_API_KEY=...              # For xAI Grok fallback
GROQ_API_KEY=...             # For Groq fallback
```

These are ONLY used by MCP servers when Claude Pro Max hits rate limits.

## Code References

- **Launcher**: `src/dopemux/claude/launcher.py:268-284` - Removes ANTHROPIC_API_KEY from Claude Code subprocess
- **CLI**: `src/dopemux/cli.py:180` - CCR default changed to `False`
- **ConPort Fix**: Network bridge between containers

## Summary

✅ **What Changed**:
- OAuth-first authentication
- No routing layer by default
- ConPort database connectivity fixed

❌ **What to Avoid**:
- Don't set ANTHROPIC_API_KEY for Claude Code (it's ignored)
- Don't use `--claude-router` unless you have a specific need
- Don't worry about LiteLLM container - it's for MCP servers only

💡 **Quick Start**:
```bash
dopemux start
# Inside Claude Code:
/login
# Authenticate in browser
# Done!
```
