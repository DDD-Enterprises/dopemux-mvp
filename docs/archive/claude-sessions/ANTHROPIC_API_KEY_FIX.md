---
id: ANTHROPIC_API_KEY_FIX
title: Anthropic_Api_Key_Fix
type: historical
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# API Key and Model Priority Fixes

**Date**: 2025-10-15
**Issue**: 401 Authentication errors + incorrect model routing

## Changes Made

### 1. Fixed ANTHROPIC_API_KEY Environment ✅
**File**: `src/dopemux/claude/launcher.py:195`

Added `ANTHROPIC_API_KEY` to Claude Code's main environment.

**Why**: Previously only MCP servers had the API key, not Claude Code itself.

### 2. Configured LiteLLM Priority Routing ✅
**File**: `litellm.config.yaml`

- Changed routing from `simple-shuffle` to `usage-based-routing-v2`
- Added RPM priorities: Claude Sonnet 4.5 (10K) → GPT-5 (500) → Grok-4 (60)
- Configured 3 retries on rate limits before fallback

### 3. Fixed Claude Code Router Model Priority ✅
**File**: `src/dopemux/cli.py:421`

Changed models to: `["claude-sonnet-4.5", "openai-gpt-5", "xai-grok-4"]`

## Testing

Restart Dopemux to test:
```bash
dopemux start --litellm --claude-router
```

## Expected Behavior

- ✅ No 401 errors
- ✅ Claude Sonnet 4.5 (Pro Max) used by default
- ✅ Auto fallback on rate limits
