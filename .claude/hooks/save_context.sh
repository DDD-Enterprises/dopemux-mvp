#!/bin/bash
# Claude Code Stop Hook - Context Saver
#
# Triggered when Claude stops working.
# Auto-saves context to enable seamless session continuation.
#
# NOTE: Requires services/adhd-engine running on port 8080.
# If not running, hook fails gracefully (backgrounded curl with timeout).
# This is expected and OK—hook errors are harmless.

ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:8080/api/v1}"

# Get open files from environment (if available)
OPEN_FILES="${CLAUDE_OPEN_FILES:-[]}"

# Save context (non-blocking)
curl -s --connect-timeout 2 \
    -X POST "$ADHD_ENGINE_URL/save-context" \
    -H "Content-Type: application/json" \
    -d "{\"reason\":\"claude_session_stopped\",\"files\":$OPEN_FILES,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
    >/dev/null 2>&1 &

exit 0
