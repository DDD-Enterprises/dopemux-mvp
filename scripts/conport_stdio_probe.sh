#!/bin/bash
# ConPort Stdio MCP Probe
# Deterministic discovery of ConPort stdio MCP interface

set -euo pipefail

PROBE_OUTPUT="/tmp/conport_stdio_probe_$$.txt"
WORKSPACE_ID="default"

# Check if conport-mcp binary exists
echo "[INFO] Checking if conport-mcp binary exists..."
if docker exec -i mcp-conport which conport-mcp >/dev/null 2>&1; then
    echo "✓ conport-mcp binary found"
else
    echo "✗ conport-mcp binary not found"
    exit 1
fi

# Test stdio mode with workspace_id
echo "[INFO] Testing ConPort stdio MCP interface..."
echo "[INFO] Starting conport-mcp in stdio mode with workspace_id=$WORKSPACE_ID"

# Start the MCP server in background and test it
(
    # Give it time to initialize
    sleep 3
    
    # Send a tools/list request
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
    
    # Wait a bit more for response
    sleep 2
) | docker exec -i mcp-conport timeout 10 conport-mcp --mode stdio --workspace_id "$WORKSPACE_ID" --no-auto-detect > "$PROBE_OUTPUT" 2>&1 &

PROBE_PID=$!

# Wait for the probe to complete
wait "$PROBE_PID" 2>/dev/null || true

# Check the output
echo "[INFO] Analyzing probe output..."

if grep -q '"tools"' "$PROBE_OUTPUT"; then
    echo "✓ ConPort stdio MCP interface is working"
    echo "✓ Tool list received"
    
    # Extract and display tool count
    TOOL_COUNT=$(grep -o '"tools"' "$PROBE_OUTPUT" | wc -l)
    echo "✓ Found $TOOL_COUNT tool definitions"
    
    # Save proof
    mkdir -p ".taskx/proof"
    cp "$PROBE_OUTPUT" ".taskx/proof/conport_stdio_probe.txt"
    echo "✓ Proof saved to .taskx/proof/conport_stdio_probe.txt"
    
    exit 0
elif grep -q '"error"' "$PROBE_OUTPUT"; then
    echo "✗ ConPort stdio MCP interface returned error"
    echo "Error details:"
    grep -A5 '"error"' "$PROBE_OUTPUT" | head -10
    
    # Save proof for debugging
    mkdir -p ".taskx/proof"
    cp "$PROBE_OUTPUT" ".taskx/proof/conport_stdio_probe_error.txt"
    
    exit 1
else
    echo "✗ ConPort stdio MCP interface did not respond as expected"
    echo "Output:"
    cat "$PROBE_OUTPUT" | head -20
    
    # Save proof for debugging
    mkdir -p ".taskx/proof"
    cp "$PROBE_OUTPUT" ".taskx/proof/conport_stdio_probe_unexpected.txt"
    
    exit 1
fi
