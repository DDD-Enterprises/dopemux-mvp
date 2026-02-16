# SYSTEM PROMPT
# Prompt A0: Repo control inventory + partition plan (mandatory)

Outputs
REPO_CONTROL_INVENTORY.json
REPO_CONTROL_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.
TARGET ROOT: dopemux-mvp repo working tree.

INCLUDE PATHS:
- .claude/**, .claude.json, .claude.json.template
- .dopemux/**, dopemux.toml, dopemux.rb
- .githooks/**, .git/hooks/** (if tracked), scripts/**, tools/**
- compose/**, compose.yml, docker-compose*.yml, docker/**, Dockerfile*
- AGENTS.md, CLAUDE.md, claude.md, README.md, QUICK_START.md, INSTALL.md
- litellm.config*, mcp-proxy-config*.y*ml/json, start-mcp-servers.sh
- .taskx/**, .taskx-pin, .taskxroot, .taskx_venv (just names)
- config/**, profiles/**, installers/**, install.sh, Makefile
- .github/** (workflow files)
- tmux-dopemux-orchestrator.yaml, .tmux.conf

OUTPUT 1: REPO_CONTROL_INVENTORY.json
For each included file:
- path
- size_bytes
- last_modified (if available)
- sha256 (if available)
- file_kind by extension (md|json|yaml|toml|sh|py|rb|other)
- first_nonempty_line (scan first 80 lines)
- contains_tokens[]: list of matched tokens from:
  ["mcp","litellm","router","provider","model","taskx","hook","compose","docker","tmux","agent","instruction","server","proxy","env","dotenv"]

OUTPUT 2: REPO_CONTROL_PARTITION_PLAN.json
Create deterministic partitions with explicit path lists:
A1_INSTRUCTIONS
A2_MCP_PROXY_AND_SERVERS
A3_ROUTER_PROVIDER_LADDERS
A4_HOOKS_AND_IMPLICIT_TRIGGERS
A5_COMPOSE_AND_SERVICE_GRAPH
A6_LITELLM_CONFIG_AND_LOGGING
A7_TASKX_REPO_SURFACE
A8_CI_AND_GATES

RULES:
- Partitioning is by path heuristics only.
- No interpretation.
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