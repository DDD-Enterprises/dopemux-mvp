# SYSTEM PROMPT\n# Prompt A3: Router + provider ladders (repo)

Outputs
REPO_ROUTER_SURFACE.json
REPO_PROVIDER_LADDER_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .claude.json, .claude/**, .dopemux/**, dopemux.toml
- any "router" configs, "provider" configs, "model" lists
- litellm.config* (also covered in A6 but extract routing bits here too)

TASK 1: REPO_ROUTER_SURFACE.json
Extract any configuration that appears to route requests:
- provider selection rules
- trust levels
- project allowlists
- model settings (name, reasoning effort)
For each block:
- path, line_range, excerpt <= 40 lines
- detected_keys[] (keys only)

TASK 2: REPO_PROVIDER_LADDER_HINTS.json
Extract literal ordered lists of providers/models/fallbacks:
- arrays or bullet lists of providers/models
- environment variables controlling provider
For each ladder:
- ladder_id
- ordered_items[] (literal strings)
- path, line_range, excerpt <= 20 lines

RULES:
- No claims about which is used at runtime.
- JSON only.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/.claude/llms.md ---\n# LLM Configuration - Python Project

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
\n\n--- FILE: /Users/hue/code/dopemux-mvp/.claude/AGENT_ARCHITECTURE.md ---\n# Dopemux Agent Architecture (Revised)

**Version**: 2.0.0
**Date**: 2025-10-04
**Status**: Validated design ready for implementation
**Revision**: Corrected persona understanding from investigation

---

## Executive Summary

**Total... [truncated for trace]