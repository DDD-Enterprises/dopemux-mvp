# Phase H: Home Control Plane Scan

## H: Home Control Plane Scan (Tier 0)

Output files
	•	H1_HOME_CONFIG.json
	•	H2_HOME_MCP_ROUTER.json
	•	H3_HOME_LITELLM.json
	•	H4_HOME_HOOKS.json

ROLE: Local Environment Analyst. JSON only. No code generation.

TARGET: User's home directory configuration.
- ~/.dopemux/**
- ~/.config/dopemux/**

SCOPE:
- ~/.dopemux/config.yaml
- ~/.dopemux/profiles/**
- ~/.config/dopemux/litellm.config.yaml
- ~/.config/dopemux/mcp-router-config.yaml
- ~/.claude/claude_config.json

OUTPUT 1: H1_HOME_CONFIG.json
General user preferences, profiles, and environment overrides.

OUTPUT 2: H2_HOME_MCP_ROUTER.json
Router configuration, active servers, upstream providers.

OUTPUT 3: H3_HOME_LITELLM.json
LiteLLM configuration, models, API keys (masked), database settings.

OUTPUT 4: H4_HOME_HOOKS.json
Active hooks configuration, adaptive security settings.

RULES:
- Scan for user-specific overrides.
- Identify active profiles.
- Mask all API keys (replace with "sk-***").
- Do not read unrelated files in home directory.
