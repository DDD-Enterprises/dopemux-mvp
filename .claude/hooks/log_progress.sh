#!/bin/bash
# Claude Code PostToolUse Hook - Progress Logger
#
# Logs tool usage to ADHD Engine for pattern detection.
# Tracks progress and can detect overwhelm from rapid tool usage.

ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:8080/api/v1}"

# Read tool info from environment
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
TOOL_SUCCESS="${CLAUDE_TOOL_SUCCESS:-true}"

# Log progress (non-blocking, fire and forget)
curl -s --connect-timeout 1 \
    -X POST "$ADHD_ENGINE_URL/record-progress" \
    -H "Content-Type: application/json" \
    -d "{\"tool\":\"$TOOL_NAME\",\"success\":$TOOL_SUCCESS,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
    >/dev/null 2>&1 &

# Always allow (this is post-execution)
exit 0
