# SYSTEM PROMPT\n# Prompt A5: Compose + service graph (repo)

Outputs
REPO_COMPOSE_SERVICE_GRAPH.json
REPO_ENV_WIRING.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- compose.yml
- docker-compose*.yml
- compose/**

TASK 1: REPO_COMPOSE_SERVICE_GRAPH.json
Parse compose files and emit:
- services[]:
  - name
  - image/build (literal)
  - depends_on
  - ports
  - volumes
  - environment_keys[] (keys only; redact values)
  - command/entrypoint (literal)
  - networks
  - profiles
- file_sources[]: list of compose files used

TASK 2: REPO_ENV_WIRING.json
Extract:
- env files referenced
- environment variables used in compose as ${VAR}
Emit:
- var_name
- path, line_range, excerpt <= 6 lines
- used_in_service if parseable

RULES:
- JSON only.
- Redact suspicious values.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/.claude/llms.md ---\n# LLM Configuration - Python Project

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