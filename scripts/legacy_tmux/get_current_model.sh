#!/bin/bash
# Get the current LLM model being used by Claude Code Router

CCR_LOG=".dopemux/claude-code-router/A/claude-code-router.log"
CCR_CONFIG=".dopemux/claude-code-router/A/.claude-code-router/config.json"

# Check CCR config for default model
if [ -f "$CCR_CONFIG" ]; then
    DEFAULT_MODEL=$(jq -r '.Router.default // "gpt-5"' "$CCR_CONFIG" 2>/dev/null | cut -d',' -f2 | sed 's/openrouter-openai-//')
    echo "🤖${DEFAULT_MODEL:-gpt-5}"
    exit 0
fi

echo "🤖gpt-5"
