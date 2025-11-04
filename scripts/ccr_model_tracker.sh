#!/bin/bash
# Track and display the current Claude Code Router model in use

STATE_FILE="/tmp/dopemux_current_model.txt"
CCR_CONFIG=".dopemux/claude-code-router/A/.claude-code-router/config.json"

get_default_model() {
    if [ -f "$CCR_CONFIG" ]; then
        jq -r '.Router.default // "litellm,openrouter-openai-gpt-5"' "$CCR_CONFIG" 2>/dev/null | \
            cut -d',' -f2 | \
            sed 's/openrouter-openai-//' | \
            sed 's/openrouter-xai-//' | \
            sed 's/openrouter-//'
    else
        echo "gpt-5"
    fi
}

format_model_name() {
    local model="$1"
    case "$model" in
        gpt-5-pro) echo "🧠PRO" ;;
        gpt-5-codex) echo "💻CDX" ;;
        gpt-5-mini) echo "⚡MIN" ;;
        gpt-5) echo "🤖GP5" ;;
        grok-4-fast) echo "🚀GRK" ;;
        grok-code-fast) echo "⚡GRC" ;;
        grok-4-fast-reasoning) echo "🧠GRR" ;;
        gemini-2-flash|gemini-2.0-flash-exp) echo "✨GEM" ;;
        llama-3.1-405b*) echo "🦙LMA" ;;
        claude-sonnet-4.5) echo "🎭CL4" ;;
        *) echo "🤖$(echo $model | cut -c1-3 | tr '[:lower:]' '[:upper:]')" ;;
    esac
}

MODEL=$(get_default_model)
echo "$MODEL" > "$STATE_FILE"
format_model_name "$MODEL"
