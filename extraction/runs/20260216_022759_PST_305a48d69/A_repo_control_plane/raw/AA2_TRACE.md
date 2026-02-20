# SYSTEM PROMPT
# Prompt A2: MCP proxy + server definitions (repo)

Outputs
REPO_MCP_PROXY_SURFACE.json
REPO_MCP_SERVER_DEFS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- mcp-proxy-config*.yaml/json
- start-mcp-servers.sh
- docs/archive/mcp-servers/** (index only, do not infer)
- any compose files referencing mcp
- config files mentioning mcp in REPO_CONTROL_INVENTORY

TASK 1: REPO_MCP_PROXY_SURFACE.json
Extract:
- proxy config sections (servers, routes, env, auth, allowlists)
- path, line_range, excerpt <= 40 lines per section
Also emit:
- server_ids: literal keys/names if parseable

TASK 2: REPO_MCP_SERVER_DEFS.json
Extract server launch definitions:
- command + args
- env vars set for each server
- working dirs if specified
For each server:
- server_name
- command
- args[]
- env_kv[] (key only; redact values if sensitive)
- path, line_range, excerpt <= 20 lines

RULES:
- Redact secrets: if a value looks like key/token, output "***REDACTED***"
- JSON only.

# USER CONTEXT

--- FILE: /Users/hue/code/dopemux-mvp/.claude/llms.md ---
# LLM Configuration - Python Project

Multi-model AI configuration optimized for python development with ADHD accommodations.

## Model Selection for Python

### Primary Models

- **Code Generation**: Claude Sonnet 4, DeepSeek Chat
- **Architecture**: Claude Opus 4.1, O3-Pro
- **Quick Fixes**: Gemini 2.5 Flash, GPT-5 Mini
- **Documentation**: Claude Opus 4.1, GPT-4.1


### Attention-Based Routing
- **Focused**: Use comprehensive models (Opus 4.1, O3-Pro)
- **Scattered**: Use fast models (Gemini 2.5 Flash, GPT-5 Mini)
- **Hyperfocus**: Use code-focused models (Sonnet 4, Grok Code Fast)

## Project-Specific Adaptations

### Python Optimizations

- Pythonic code patterns and idioms
- Type hints and mypy compatibility
- PEP compliance and best practices
- pytest testing patterns


### Response Formatting
- Code examples in python syntax
- Framework-specific patterns
- Best practices for python ecosystem
- ADHD-friendly explanations

## MCP Server Integration

### Active Servers

- **mas-sequential-thinking**: Complex reasoning for architecture
- **pal**: API/SDK documentation via apilookup
- **claude-context**: Python documentation and semantic code search
- **conport**: Decision tracking and architecture memory
- **morphllm-fast-apply**: Code transformations


### Cost Optimization
- Prefer faster models for simple queries
- Use premium models for complex architecture decisions
- Cache responses for repeated patterns
- Smart fallback chains

---

**Focus**: python development efficiency with ADHD support
**Strategy**: Context-aware model routing
**Goal**: Optimal AI assistance without cognitive overload


--- FILE: /Users/hue/code/dopemux-mvp/.claude/AGENT_ARCHITECTURE.md ---
# Dopemux Agent Architecture (Revised)

**Version**: 2.0.0
**Date**: 2025-10-04
**Status**: Validated design ready for implementation
**Revision**: Corrected persona understanding from investigation

---

## Executive Summary

**Total Agen... [truncated for trace]