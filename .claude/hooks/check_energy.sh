#!/bin/bash
# Claude Code PreToolUse Hook - Energy Check
#
# Checks ADHD state before complex tool execution.
# Warns if attempting complex operations during low energy.

ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:8080/api/v1}"

# Read tool name from environment (set by Claude Code)
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"

# Complex tools that need energy check
COMPLEX_TOOLS="thinkdeep|morph|batch_edit|refactor|deep_research"

# Check if this is a complex tool
if [[ "$TOOL_NAME" =~ ($COMPLEX_TOOLS) ]]; then
    # Get ADHD state
    STATE=$(curl -s --connect-timeout 1 "$ADHD_ENGINE_URL/state" 2>/dev/null)
    
    if [[ -n "$STATE" ]]; then
        ENERGY=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('energy_level','unknown'))" 2>/dev/null)
        
        if [[ "$ENERGY" == "low" ]]; then
            # Output warning but allow
            echo '{"decision":"allow","reason":"⚠️ Low energy detected. Consider simpler approach or break first."}' 
            exit 0
        fi
    fi
fi

# Allow the tool
echo '{"decision":"allow"}'
exit 0
