#!/usr/bin/env bash
set -euo pipefail

echo "🔒 TP-DEV Tool Validation Gate"
echo "================================"
echo

# Absolute paths for reliability
CURL=/usr/bin/curl
JQ=/usr/bin/jq
SED=/bin/sed

# Check if required tools exist
echo "📋 Checking required tools..."
for tool in "$CURL" "$JQ" "$SED"; do
  if [ ! -x "$tool" ]; then
    echo "❌ Missing required tool: $tool"
    exit 1
  fi
done
echo "✅ All required tools available"
echo

# Discover Serena tools via MCP
echo "🔍 Discovering Serena tools via MCP..."
SERENA_TOOLS_FILE=".taskx/proof/serena_tools_live.txt"

# Initialize and get session ID
RESPONSE=$($CURL -sS -i \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0.1"}}}' \
  http://localhost:3006/mcp 2>&1)

SID=$(echo "$RESPONSE" | grep -i "mcp-session-id:" | awk '{print $2}' | tr -d '\r' || echo "")

if [ -z "$SID" ]; then
  echo "❌ Failed to get MCP session ID from Serena"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Got session ID: $SID"

# Get tools list
TOOLS_RESPONSE=$($CURL -sS \
  -H 'Content-Type: application/json' \
  -H "Mcp-Session-Id: $SID" \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  http://localhost:3006/mcp)

# Extract tool names and sort
echo "$TOOLS_RESPONSE" | $JQ -r '.result.tools[].name' | sort > "$SERENA_TOOLS_FILE"

echo "✅ Serena tools discovered and saved to $SERENA_TOOLS_FILE"
TOOL_COUNT=$(wc -l < "$SERENA_TOOLS_FILE")
echo "   Found $TOOL_COUNT tools"
echo

# Extract Serena tools from tp-dev.toml
echo "📋 Extracting Serena tools from tp-dev.toml..."
CONFIG_FILE="~/.vibe/agents/tp-dev.toml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Config file not found: $CONFIG_FILE"
  exit 1
fi

# Extract the Serena section (after the comment line)
SERENA_SECTION=$(awk '/# Serena tools/,/^]/' "$CONFIG_FILE" | grep '"' | sed 's/"//g' | sed 's/,//g' | sed 's/^\s*//g' | sed 's/\s*$//g' | sort)

echo "$SERENA_SECTION" > .taskx/proof/serena_tools_config.txt
CONFIG_COUNT=$(echo "$SERENA_SECTION" | wc -l)
echo "✅ Found $CONFIG_COUNT Serena tools in config"
echo

# Compare
echo "🔍 Comparing discovered vs configured tools..."
DIFF_OUTPUT=$(diff "$SERENA_TOOLS_FILE" .taskx/proof/serena_tools_config.txt || true)

if [ -z "$DIFF_OUTPUT" ]; then
  echo "✅ Perfect match! Serena tools are synchronized."
  exit 0
else
  echo "❌ Mismatch detected!"
  echo "$DIFF_OUTPUT"
  echo
  echo "📊 Summary:"
  echo "   Discovered: $TOOL_COUNT tools"
  echo "   Configured: $CONFIG_COUNT tools"
  exit 1
fi