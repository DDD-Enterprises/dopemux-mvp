---
id: INTEGRATION_SERVICES_MASTER_HISTORY
title: Integration Services Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Integration Services Master History (explanation) for dopemux documentation
  and developer workflows.
---
# Integration Services: Master History & Feature Catalog

**Services**: `slack-integration`, `leantime-bridge`, `litellm`, `pal`, `exa`
**Role**: External World Connectors
**Status**:
*   LiteLLM: Critical Infrastructure (Production)
*   Leantime Bridge: Production
*   Slack Notifier: Production
*   Exa: Production
*   PAL: Maintenance Mode

---

## 1. Executive Summary

The **Integration Services** connect Dopemux to the outside world—chat platforms (Slack/Discord), project management (Leantime), AI providers (LiteLLM), and the web (Exa). They handle the "dirty work" of API keys, rate limits, and protocol translation, exposing clean MCP interfaces to the rest of the system.

**Key Feature**: "ADHD Transparency" — The system handles the complexity of 5 different AI providers (via LiteLLM) and Project Management updates (via Leantime) so the user just focuses on *doing*.

---

## 2. Feature Catalog

### 💬 Slack/Discord Notifier (`services/slack-integration`)
*   **Daily Summaries**: Posts end-of-day reports on "Hyperfocus Protections" and "Break Compliance".
*   **Team Visibility**: Lets teammates know when you are in "Deep Work" status.
*   **Unified Logic**: Same code serves both Slack and Discord (via `notifier.py`).

### 📅 Leantime Bridge (`docker/mcp-servers/leantime-bridge`)
*   **PM Integration**: Two-way sync with Leantime Project Management.
*   **Service Discovery**: Implements `/info` endpoint (ADR-208) for auto-configuration.
*   **Task Management**: Create/Update tasks directly from Claude/Zen.

### 🤖 LiteLLM Proxy (`docker/mcp-servers/litellm`)
*   **Unified Interface**: OpenAI-compatible endpoint for *all* models (Grok, Gemini, Claude).
*   **Cost & Fallback**: Routes simple queries to cheap models; auto-retries on API failures.
*   **Chain**: `gpt-5` -> `gpt-5-mini` -> `grok-4`.

### 🧠 Exa Search (`docker/mcp-servers/exa`)
*   **Neural Search**: "Find me Python code for OAuth" (Semantic) vs "OAuth Python" (Keyword).
*   **Research Automation**: Used by `dopemux-gpt-researcher`.

### 🛠️ PAL (Platform Abstraction Layer) (`docker/mcp-servers/pal`)
*   **Zen Bridge**: Adapts the `zen` rust CLI to MCP.
*   **Fix History**: Patched to support custom CLI configs (ADR-Fix-Zen-CLI).

---

## 3. Architecture Deep Dive

### The External Loop
```
[User] -> [Slack Notifier] --(posts)--> [Team Channel]
               ^
               | (metrics)
        [ADHD Engine]
               |
[Agents] --> [LiteLLM] --> [OpenAI/Anthropic/xAI]
   |
   +-------> [Leantime Bridge] --> [Leantime PM]
   |
   +-------> [Exa] --> [The Web]
```

---

## 4. Validated Status (Audit Results)

**✅ Operational:**
*   **LiteLLM**: Serving traffic on port 4000. Fallbacks configured.
*   **Leantime Bridge**: `/info` endpoint active.
*   **Exa**: Functional.

**🔧 Maintenance:**
*   **PAL**: Required manual patching (`PAL_FIX.md`) to work with recent `clink` updates.

---

*Sources: `slack-integration/notifier.py`, `leantime-bridge/README.md`, `litellm/README.md`, `exa/README.md`, `PAL_FIX.md`.*
