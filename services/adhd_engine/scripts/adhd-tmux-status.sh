#!/bin/bash
# ADHD Tmux Status Script
# Fetches current ADHD state and formats for tmux status-right
#
# Usage in .tmux.conf:
#   set -g status-right "#(~/.dopemux/adhd-tmux-status.sh)"
#
# Environment variables:
#   ADHD_ENGINE_URL - API URL (default: http://localhost:3333)
#   ADHD_TMUX_EMOJI - Use emoji (default: true, set to "false" for text)

ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:3333}"
ADHD_TMUX_EMOJI="${ADHD_TMUX_EMOJI:-true}"

# Fetch state with timeout
STATE=$(curl -s --connect-timeout 1 --max-time 2 \
    "${ADHD_ENGINE_URL}/api/v1/state?user_id=default" 2>/dev/null)

if [ -z "$STATE" ] || [ "$STATE" = "null" ]; then
    # Service unavailable
    if [ "$ADHD_TMUX_EMOJI" = "true" ]; then
        echo "🔌 ADHD offline"
    else
        echo "[ADHD: offline]"
    fi
    exit 0
fi

# Parse JSON (using jq if available, fallback to grep)
if command -v jq &> /dev/null; then
    ENERGY=$(echo "$STATE" | jq -r '.energy // "unknown"')
    ATTENTION=$(echo "$STATE" | jq -r '.attention // "unknown"')
    SESSION_MIN=$(echo "$STATE" | jq -r '.session_minutes // 0')
else
    # Fallback parsing with grep/sed
    ENERGY=$(echo "$STATE" | grep -o '"energy":"[^"]*"' | cut -d'"' -f4)
    ATTENTION=$(echo "$STATE" | grep -o '"attention":"[^"]*"' | cut -d'"' -f4)
    SESSION_MIN=$(echo "$STATE" | grep -o '"session_minutes":[0-9]*' | cut -d':' -f2)
    [ -z "$ENERGY" ] && ENERGY="unknown"
    [ -z "$ATTENTION" ] && ATTENTION="unknown"
    [ -z "$SESSION_MIN" ] && SESSION_MIN="0"
fi

# Format output
if [ "$ADHD_TMUX_EMOJI" = "true" ]; then
    # Emoji-based format
    case "$ENERGY" in
        "high")   E_ICON="⚡" ;;
        "medium") E_ICON="🔋" ;;
        "low")    E_ICON="🪫" ;;
        *)        E_ICON="❓" ;;
    esac
    
    case "$ATTENTION" in
        "hyperfocus")   A_ICON="🔥" ;;
        "focused")      A_ICON="🎯" ;;
        "distracted")   A_ICON="🌊" ;;
        "fatigued")     A_ICON="😴" ;;
        "overwhelmed")  A_ICON="😰" ;;
        *)              A_ICON="🧠" ;;
    esac
    
    # Add session time if > 30 min
    if [ "$SESSION_MIN" -ge 90 ]; then
        TIME_ICON="⏰"  # Warning: long session
    elif [ "$SESSION_MIN" -ge 30 ]; then
        TIME_ICON="⏱️"  # Good session
    else
        TIME_ICON=""
    fi
    
    echo "${E_ICON}${A_ICON}${TIME_ICON}"
else
    # Text-based format
    echo "[${ENERGY:0:1}/${ATTENTION:0:1}]"
fi
