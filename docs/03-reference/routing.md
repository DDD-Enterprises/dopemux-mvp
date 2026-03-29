---
id: routing
title: Routing
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-29'
last_review: '2026-03-29'
next_review: '2026-06-27'
prelude: Routing (reference) for dopemux documentation and developer workflows.
---
# Dopemux Alternate Routing Reference

Dopemux provides a robust multi-model routing system that allows you to use external AI models (Grok, Gemini, OpenAI) within your Claude Code sessions. This is achieved through a local proxy system using LiteLLM and the Claude Code Router (CCR).

## Routing Modes

Dopemux supports two primary routing modes:

| Mode | Description | How it works |
|------|-------------|--------------|
| `subscription` | Direct Anthropic access | Bypasses proxies, uses your Anthropic OAuth/subscription directly. |
| `api` | Global Proxy Routing | Routes through LiteLLM + CCR to allow using Grok, Gemini, and OpenAI. |

## CLI Commands

Manage your routing mode using the following commands:

### Switch to API Mode
```bash
dopemux routing api
```
- Sets global routing to `api` mode.
- Updates `~/.claude/settings.json` to point to the local proxy.
- Restarts LiteLLM and CCR services.

### Switch to Subscription Mode
```bash
dopemux routing direct
```
- Sets global routing to `subscription` mode.
- Reverts `~/.claude/settings.json` to point to the official Anthropic API.

### Check Status
```bash
dopemux routing status
```
Shows the current mode and health of background services.

### Configuration
```bash
dopemux routing config
```
Displays the current model mapping and provider definitions.

## Configuration File

Global routing is defined in `~/.dopemux/routing.yaml`.

### Key Sections:
- `mode`: `api` or `subscription`
- `providers`: Definitions for external LLM providers (Gemini, xAI, OpenAI, OpenRouter).
- `models`: Specific model IDs and token limits.
- `slots`: Mappings from Dopemux usage slots (e.g., `think`, `codex`, `arbiter`) to specific models.
- `fallbacks`: Chain of resilience for when primary models are unavailable.

## Environment Variables

API keys for external providers must be stored in `~/.dopemux/routing.env`.

```bash
# Example routing.env
GEMINI_API_KEY=your_key_here
XAI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

Use `dopemux routing sync-keys` to populate this file from your current shell environment.

## Advanced Usage

### Launching with Alternate Routing
When in `api` mode, running `dopemux start` automatically configures the environment for Claude Code to use the proxy.

### Model Slots
Dopemux exposes virtual models to Claude Code that map to your configured slots:
- `think` -> Optimized for deep reasoning (e.g., `grok-4.20-beta-reasoning`)
- `codex` -> Optimized for code generation (e.g., `grok-code-fast-1`)
- `arbiter` -> High-precision model for decision making (e.g., `gpt-5.4-pro`)
- `opus` -> Flagship creative model (e.g., `gpt-5.4-thinking`)
- `sonnet` -> Balanced performance model (e.g., `grok-4.20-multi-agent-beta`)
