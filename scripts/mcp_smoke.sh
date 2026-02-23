#!/bin/bash
# MCP Smoke Test
# Runtime proof that MCP servers are working correctly

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        MCP Smoke Test - Runtime Verification              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Dope-Context MCP endpoint
echo "🔹 Test 1: Dope-Context MCP endpoint (http://localhost:3010/mcp)"
if curl -fsS -X POST http://localhost:3010/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"type":"list_tools"}' > /tmp/mcp_smoke_dopec.txt 2>&1; then
    if grep -q '"tools"' /tmp/mcp_smoke_dopec.txt; then
        TOOL_COUNT=$(grep -o '"name"' /tmp/mcp_smoke_dopec.txt | wc -l)
        echo "  ✅ Dope-Context MCP working - $TOOL_COUNT tools available"
    else
        echo "  ❌ Dope-Context MCP returned unexpected response"
        cat /tmp/mcp_smoke_dopec.txt | head -5
        exit 1
    fi
else
    echo "  ❌ Dope-Context MCP endpoint not reachable"
    exit 1
fi

# Test 2: Dope-Memory MCP stdio adapter
echo "🔹 Test 2: Dope-Memory MCP stdio adapter"
if echo '{"jsonrpc":"2.0","id":1,"method":"list_tools","params":{}}' | \
     python /Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py > /tmp/mcp_smoke_dopem.txt 2>&1; then
    if grep -q '"tools"' /tmp/mcp_smoke_dopem.txt; then
        TOOL_COUNT=$(grep -o '"name"' /tmp/mcp_smoke_dopem.txt | wc -l)
        echo "  ✅ Dope-Memory MCP adapter working - $TOOL_COUNT tools available"
    else
        echo "  ❌ Dope-Memory MCP adapter returned unexpected response"
        cat /tmp/mcp_smoke_dopem.txt | head -5
        exit 1
    fi
else
    echo "  ❌ Dope-Memory MCP adapter failed to start"
    exit 1
fi

# Test 3: Dope-Memory REST endpoint (direct)
echo "🔹 Test 3: Dope-Memory REST endpoint (http://localhost:8096/health)"
if curl -fsS http://localhost:8096/health > /tmp/mcp_smoke_dopem_rest.txt 2>&1; then
    if grep -q '"status"' /tmp/mcp_smoke_dopem_rest.txt; then
        echo "  ✅ Dope-Memory REST endpoint healthy"
    else
        echo "  ❌ Dope-Memory REST endpoint returned unexpected response"
        cat /tmp/mcp_smoke_dopem_rest.txt | head -5
        exit 1
    fi
else
    echo "  ❌ Dope-Memory REST endpoint not reachable"
    exit 1
fi

# Test 4: ConPort HTTP enhanced server (status check)
echo "🔹 Test 4: ConPort HTTP enhanced server (http://localhost:3004/mcp)"
if curl -fsS -X POST http://localhost:3004/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"type":"list_tools"}' > /tmp/mcp_smoke_conport.txt 2>&1; then
    if grep -q '"status"' /tmp/mcp_smoke_conport.txt; then
        echo "  ✅ ConPort HTTP enhanced server responding (not MCP tool server)"
    else
        echo "  ❌ ConPort HTTP endpoint returned unexpected response"
        cat /tmp/mcp_smoke_conport.txt | head -5
        exit 1
    fi
else
    echo "  ❌ ConPort HTTP endpoint not reachable"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ All MCP smoke tests passed!                            ║"
echo "║                                                             ║"
echo "║  Proven MCP servers:                                       ║"
echo "║    • Dope-Context (http://localhost:3010/mcp)               ║"
echo "║    • Dope-Memory (stdio adapter)                            ║"
echo "║                                                             ║"
echo "║  Non-MCP services (require wrappers):                     ║"
echo "║    • ConPort (http://localhost:3004 - enhanced server)      ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Save proof
mkdir -p ".taskx/proof"
echo "MCP Smoke Test Results - $(date)" > ".taskx/proof/mcp_smoke_test.txt"
echo "=================================" >> ".taskx/proof/mcp_smoke_test.txt"
echo "" >> ".taskx/proof/mcp_smoke_test.txt"
echo "Dope-Context MCP: PASS" >> ".taskx/proof/mcp_smoke_test.txt"
echo "Dope-Memory MCP: PASS" >> ".taskx/proof/mcp_smoke_test.txt"
echo "Dope-Memory REST: PASS" >> ".taskx/proof/mcp_smoke_test.txt"
echo "ConPort HTTP: PASS (not MCP)" >> ".taskx/proof/mcp_smoke_test.txt"

echo "✅ Proof saved to .taskx/proof/mcp_smoke_test.txt"
