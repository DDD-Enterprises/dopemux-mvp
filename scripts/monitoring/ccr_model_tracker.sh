#!/bin/bash
# Track and display the current Claude Code Router + LiteLLM model in use

MODE="icon"
if [ $# -gt 0 ]; then
    case "$1" in
        --statusline)
            MODE="statusline"
            shift
            ;;
        --route)
            MODE="route"
            shift
            ;;
        --resolved)
            MODE="resolved"
            shift
            ;;
    esac
fi

INSTANCE_ID="${DOPEMUX_INSTANCE_ID:-A}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

STATE_FILE="/tmp/dopemux_current_model.txt"
CCR_CONFIG="$PROJECT_ROOT/.dopemux/claude-code-router/$INSTANCE_ID/.claude-code-router/config.json"
LITELLM_CONFIG="$PROJECT_ROOT/.dopemux/litellm/$INSTANCE_ID/litellm.config.yaml"

strip_prefix() {
    local value="$1"
    value="${value#litellm,}"
    value="${value#openrouter-openai-}"
    value="${value#openrouter-xai-}"
    value="${value#openrouter-google-}"
    value="${value#openrouter-meta-}"
    value="${value#openrouter-}"
    echo "$value"
}

humanize_resolved() {
    local value="$1"
    value="${value#openrouter/}"
    echo "$value"
}

get_route_model() {
    local raw_route
    if [ -f "$CCR_CONFIG" ]; then
        raw_route=$(jq -r '.Router.default // empty' "$CCR_CONFIG" 2>/dev/null)
        if [ -n "$raw_route" ] && [ "$raw_route" != "null" ]; then
            if [[ "$raw_route" == *","* ]]; then
                raw_route="${raw_route#*,}"
            fi
            echo "$raw_route"
            return
        fi
    fi
    echo "openrouter-openai-gpt-5"
}

resolve_litellm_target() {
    local route="$1"
    if [ -z "$route" ] || [ ! -f "$LITELLM_CONFIG" ]; then
        echo "$route"
        return
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo "$route"
        return
    fi

    ROUTE_ALIAS="$route" LITELLM_CONFIG_PATH="$LITELLM_CONFIG" python3 <<'PY' 2>/dev/null
import os
import sys

alias = os.environ.get("ROUTE_ALIAS", "").strip()
config_path = os.environ.get("LITELLM_CONFIG_PATH", "")
if not alias or not config_path:
    sys.exit(0)

try:
    import yaml  # type: ignore
except Exception:
    sys.exit(0)

try:
    with open(config_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
except Exception:
    sys.exit(0)

model_entries = {}
for entry in data.get("model_list", []) or []:
    if isinstance(entry, dict):
        name = entry.get("model_name")
        params = entry.get("litellm_params") or {}
        target = params.get("model")
        if name and target:
            model_entries[name] = target

alias_map = ((data.get("litellm_settings") or {}).get("model_alias_map") or {})
target = alias
seen = set()

while True:
    if target in model_entries:
        sys.stdout.write(model_entries[target])
        break
    if target in seen:
        sys.stdout.write(target)
        break
    seen.add(target)
    mapped = alias_map.get(target)
    if not mapped:
        sys.stdout.write(target)
        break
    target = mapped
PY
    local status=$?
    if [ $status -ne 0 ]; then
        echo "$route"
        return
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
        *) echo "🤖$(echo "$model" | cut -c1-3 | tr '[:lower:]' '[:upper:]')" ;;
    esac
}

print_statusline_model() {
    local route_label="$1"
    local resolved_full="$2"

    # Map to user-friendly model names for statusline
    local user_friendly_model
    case "$resolved_full" in
        "openrouter/openai/gpt-5") user_friendly_model="GPT-5" ;;
        "openrouter/openai/gpt-5-pro") user_friendly_model="GPT-5 Pro" ;;
        "openrouter/openai/gpt-5-codex") user_friendly_model="GPT-5 Codex" ;;
        "openrouter/openai/gpt-5-mini") user_friendly_model="GPT-5 Mini" ;;
        "xai/grok-code-fast-1") user_friendly_model="Grok Code Fast" ;;
        "xai/grok-4-fast") user_friendly_model="Grok 4 Fast" ;;
        "xai/grok-4-fast-reasoning") user_friendly_model="Grok 4 Reasoning" ;;
        "openrouter/google/gemini-2.0-flash-exp") user_friendly_model="Gemini Flash" ;;
        "openrouter/meta-llama/llama-3.1-405b-instruct") user_friendly_model="Llama 3.1 405B" ;;
        *) user_friendly_model="$resolved_full" ;;  # Fallback to full name
    esac

    echo "$user_friendly_model"
}

# Get the current route from CCR config
route_model_raw=$(get_route_model)

# Check CCR logs for recent routing decisions to show actual active model
log_file="$PROJECT_ROOT/.dopemux/claude-code-router/$INSTANCE_ID/.claude-code-router/claude-code-router.log"
actual_route="$route_model_raw"

if [ -f "$log_file" ]; then
    # Check for recent routing decisions (within last 10 minutes)
    # Look for various routing patterns in logs
    recent_logs=$(tail -100 "$log_file" 2>/dev/null | grep -E "(Using|Routing|Model)" | tail -10)

    # Check for long context usage (fix timestamp parsing)
    recent_long_context=$(echo "$recent_logs" | grep -E "Using long context model" | tail -1)
    if [ -n "$recent_long_context" ]; then
        # Extract timestamp: [2025-11-04T04:08:42.426Z] Using long context...
        log_timestamp=$(echo "$recent_long_context" | sed 's/.*\[\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}T[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\).*/\1/')
        if [ -n "$log_timestamp" ]; then
            # Parse timestamp (macOS date -j compatible)
            log_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$log_timestamp" +%s 2>/dev/null || echo "0")
            current_epoch=$(date +%s)
            time_diff=$((current_epoch - log_epoch))

            # If long context was used within last 10 minutes, show longContext route
            if [ "$time_diff" -lt 600 ]; then
                actual_route="litellm,openrouter-openai-gpt-5"
            fi
        fi
    fi

    # Check for other routing patterns (background, think, webSearch)
    # Look for patterns that might indicate different routing
    recent_background=$(echo "$recent_logs" | grep -E "(background|async)" | tail -1)
    if [ -n "$recent_background" ]; then
        # If background routing was detected recently
        actual_route="litellm,openrouter-xai-grok-4-fast"
    fi

    recent_think=$(echo "$recent_logs" | grep -E "(think|reasoning|analysis)" | tail -1)
    if [ -n "$recent_think" ]; then
        # If think routing was detected recently
        actual_route="litellm,openrouter-openai-gpt-5-codex"
    fi

    # For now, let's also check if there are any recent requests at all
    # If there are recent logs but no long context, stick with default
    recent_any=$(tail -20 "$log_file" 2>/dev/null | grep "$(date +%Y-%m-%d)" | head -1)
    if [ -z "$recent_any" ]; then
        # No recent activity, use default route
        actual_route="$route_model_raw"
    fi
fi

# Resolve to actual LiteLLM target model (this is what the user wants to see)
resolved_model_full=$(resolve_litellm_target "$actual_route")
[ -z "$resolved_model_full" ] && resolved_model_full="$actual_route"

# For display, show the actual target model that LiteLLM uses
route_model_display=$(strip_prefix "$actual_route")

# Cache latest detected model for other integrations (VS Code, etc.)
if [ -n "$route_model_display" ]; then
    echo "$route_model_display" > "$STATE_FILE"
fi

case "$MODE" in
    statusline)
        print_statusline_model "$route_model_display" "$resolved_model_full"
        ;;
    route)
        echo "$route_model_display"
        ;;
    resolved)
        humanize_resolved "$resolved_model_full"
        ;;
    *)
        format_model_name "$route_model_display"
        ;;
esac
