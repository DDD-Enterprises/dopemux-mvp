# SYSTEM PROMPT
# Prompt A4: Hooks + implicit triggers (repo)

Outputs
REPO_HOOKS_SURFACE.json
REPO_IMPLICIT_BEHAVIOR_HINTS.json
REPO_BOOTSTRAP_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .githooks/**
- install.sh, installers/**, scripts/**, tools/**
- Makefile targets that call scripts
- .envrc, .env*, dopemux.rb (if it runs stuff)
- any "bootstrap", "start", "verify", "setup" scripts

TASK 1: REPO_HOOKS_SURFACE.json
Extract:
- hook files (pre-commit, post-checkout, post-merge, etc.)
- commands executed
For each hook:
- hook_name (filename)
- path, line_range, excerpt <= 40 lines

TASK 2: REPO_IMPLICIT_BEHAVIOR_HINTS.json
Extract command chains that can run implicitly:
- Makefile recipes
- installer scripts
- dev scripts that call other scripts
For each chain:
- chain_id
- steps[] (literal command lines)
- path, line_range, excerpt <= 30 lines

TASK 3: REPO_BOOTSTRAP_SURFACE.json
Extract "how the system starts":
- start scripts, compose up invocations, tmux layouts
For each:
- bootstrap_kind = compose|tmux|shell|python|node|other
- path, line_range, excerpt <= 40 lines

RULES:
- JSON only.
- No inference of purpose.

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