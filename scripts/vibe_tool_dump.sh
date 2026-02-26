#!/bin/bash

# vibe_tool_dump.sh - Capture Vibe tool registry from session logs
# Output: .taskx/proof/vibe_tools.txt

set -e

# Create proof directory
mkdir -p .taskx/proof

# Find the most recent session log directory
SESSION_DIR=$(ls -td ~/.vibe/logs/session/session_* | head -1)
echo "Using session directory: $SESSION_DIR"

# Check for meta.json file first (primary source for tool registry)
META_FILE="$SESSION_DIR/meta.json"
if [ -f "$META_FILE" ]; then
    echo "Using meta file: $META_FILE"
    LOG_FILE="$META_FILE"
else
    # Fall back to other log files
    LOG_FILE=$(ls -t "$SESSION_DIR"/*.log "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
    if [ -z "$LOG_FILE" ]; then
        echo "ERROR: No log files found in $SESSION_DIR"
        exit 1
    fi
    echo "Using log file: $LOG_FILE"
fi

# Extract tool names from the log file
echo "=== Vibe Tool Registry Dump ===" > .taskx/proof/vibe_tools.txt
echo "Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> .taskx/proof/vibe_tools.txt
echo "Source: $LOG_FILE" >> .taskx/proof/vibe_tools.txt
echo "" >> .taskx/proof/vibe_tools.txt

# If we have a meta.json file, extract tool names from tools_available section
if [ "$LOG_FILE" = "$META_FILE" ]; then
    # Extract all tool names from the tools_available array
    grep -o '"name": "[^"]*"' "$LOG_FILE" | cut -d'"' -f4 | sort | uniq >> .taskx/proof/vibe_tools.txt
else
    # Fall back to pattern matching for other log files
    # Pattern 1: Look for tool definitions or registrations
    grep -o '"[^"]*"' "$LOG_FILE" | grep -E '(pal_|zen_|conport_|serena_|dope_context_|mcp__)' | sort | uniq >> .taskx/proof/vibe_tools.txt

    # Pattern 2: Look for tool calls
    grep -o '\b[a-zA-Z0-9_]*_' "$LOG_FILE" | grep -E '(pal_|zen_|conport_|serena_|dope_context_|mcp__)' | sort | uniq >> .taskx/proof/vibe_tools.txt

    # Pattern 3: Look for tool listings
    grep -A 50 -B 5 "Available tools" "$LOG_FILE" | grep -o '[a-zA-Z0-9_]*_' | grep -E '(pal_|zen_|conport_|serena_|dope_context_|mcp__)' | sort | uniq >> .taskx/proof/vibe_tools.txt

    # Pattern 4: Look for tool names in JSON format (for .jsonl files)
    if [[ "$LOG_FILE" == *.jsonl ]]; then
        grep -o '"tool_name"[^,]*"[^"]*"' "$LOG_FILE" | grep -o '"[^"]*"$' | tr -d '"' | grep -E '(pal_|zen_|conport_|serena_|dope_context_|mcp__)' | sort | uniq >> .taskx/proof/vibe_tools.txt
    fi
fi

# Clean up and deduplicate
sort .taskx/proof/vibe_tools.txt | uniq > .taskx/proof/vibe_tools.txt.tmp
mv .taskx/proof/vibe_tools.txt.tmp .taskx/proof/vibe_tools.txt

echo "Tool dump completed. Output: .taskx/proof/vibe_tools.txt"
