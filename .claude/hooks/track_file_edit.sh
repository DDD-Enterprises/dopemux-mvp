#!/bin/bash
# PreToolUse hook to track file edits.
# Called with: $1=tool_name, $2=JSON_args

TOOL_NAME=$1
ARGS=$2
ORCHESTRATOR_URL="http://localhost:3009"

# Only track edits for relevant tools
if [[ "$TOOL_NAME" == "write_file" || "$TOOL_NAME" == "replace" || "$TOOL_NAME" == "edit_file" ]]; then
    # Extract file path from JSON args (rough extraction for bash)
    FILE_PATH=$(echo "$ARGS" | grep -o '"file_path": *"[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -n "$FILE_PATH" ]; then
        # Call track_edit tool via REST
        curl -s -X POST "$ORCHESTRATOR_URL/api/tools/track_edit" \
             -H "Content-Type: application/json" \
             -d "{\"file_path\": \"$FILE_PATH\"}" > /dev/null
    fi
fi
