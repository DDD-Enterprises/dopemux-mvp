#!/bin/bash
# Configure Leantime MCP Bridge with API Key

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -z "$1" ]; then
    echo "Usage: $0 <api-key>"
    echo ""
    echo "Example:"
    echo "  $0 lt_abc123def456_xyz789ghi012..."
    echo ""
    exit 1
fi

API_KEY="$1"

echo "════════════════════════════════════════════════════════════"
echo "  Configuring Leantime MCP Bridge"
echo "════════════════════════════════════════════════════════════"
echo ""

# Validate API key format
# Key format is lt_<api-user-without-underscore>_<secret-without-underscore>
if [[ ! $API_KEY =~ ^lt_[^_]+_[A-Za-z0-9]+$ ]]; then
    echo "❌ Invalid API key format!"
    echo ""
    echo "Expected format: lt_<api_user>_<secret>"
    echo "Example: lt_abc123def456_xyz789ghi012abcdef..."
    echo ""
    exit 1
fi

echo "✓ API key format validated"
echo ""

# Update bridge env file
BRIDGE_ENV_FILE="${PROJECT_ROOT}/docker/mcp-servers/leantime-bridge/.env"
# Update root compose env file (compose variable expansion source)
ROOT_ENV_FILE="${PROJECT_ROOT}/.env"

if [ ! -f "$BRIDGE_ENV_FILE" ]; then
    echo "❌ Config file not found: $BRIDGE_ENV_FILE"
    exit 1
fi

cp "$BRIDGE_ENV_FILE" "${BRIDGE_ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

if grep -q "^LEANTIME_API_TOKEN=" "$BRIDGE_ENV_FILE"; then
    sed -i.bak "s|^LEANTIME_API_TOKEN=.*|LEANTIME_API_TOKEN=$API_KEY|" "$BRIDGE_ENV_FILE"
else
    echo "LEANTIME_API_TOKEN=$API_KEY" >> "$BRIDGE_ENV_FILE"
fi

if grep -q "^LEANTIME_TOKEN=" "$BRIDGE_ENV_FILE"; then
    sed -i.bak "s|^LEANTIME_TOKEN=.*|LEANTIME_TOKEN=$API_KEY|" "$BRIDGE_ENV_FILE"
else
    echo "LEANTIME_TOKEN=$API_KEY" >> "$BRIDGE_ENV_FILE"
fi

rm -f "${BRIDGE_ENV_FILE}.bak"
echo "✓ Updated bridge env file: $BRIDGE_ENV_FILE"

if [ -f "$ROOT_ENV_FILE" ]; then
    if grep -q "^LEANTIME_API_TOKEN=" "$ROOT_ENV_FILE"; then
        sed -i.bak "s|^LEANTIME_API_TOKEN=.*|LEANTIME_API_TOKEN=$API_KEY|" "$ROOT_ENV_FILE"
    else
        echo "LEANTIME_API_TOKEN=$API_KEY" >> "$ROOT_ENV_FILE"
    fi

    if grep -q "^LEANTIME_TOKEN=" "$ROOT_ENV_FILE"; then
        sed -i.bak "s|^LEANTIME_TOKEN=.*|LEANTIME_TOKEN=$API_KEY|" "$ROOT_ENV_FILE"
    else
        echo "LEANTIME_TOKEN=$API_KEY" >> "$ROOT_ENV_FILE"
    fi

    rm -f "${ROOT_ENV_FILE}.bak"
    echo "✓ Updated root env file: $ROOT_ENV_FILE"
fi

echo ""

# Restart bridge
echo "Restarting Leantime MCP Bridge..."
(
    cd "$PROJECT_ROOT"
    docker compose up -d --force-recreate leantime-bridge
)

echo ""
echo "✓ Bridge restarted"
echo ""

# Wait for service to be ready
echo "Waiting for service to be ready..."
sleep 5

# Test the connection
echo "Testing API connection..."
DEEP_HEALTH="$(docker exec dopemux-mcp-leantime-bridge sh -lc "curl -s http://127.0.0.1:3015/health?deep=1")"
PROJECT_LIST="$(docker exec dopemux-mcp-leantime-bridge sh -lc "curl -s -X POST http://127.0.0.1:3015/api/tools/list_projects -H 'Content-Type: application/json' -d '{}'")"

echo ""

if echo "$DEEP_HEALTH" | grep -q '"status":"ok"'; then
    echo "════════════════════════════════════════════════════════════"
    echo "  ✅ CONFIGURATION SUCCESSFUL!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "The Leantime MCP Bridge is now connected and working."
    echo ""
    echo "Next steps:"
    echo "  1. Test the integration:"
    echo "     cd docker/mcp-servers/leantime-bridge"
    echo "     pytest -q --no-cov docker/mcp-servers/leantime-bridge/test_contract_api_tools.py"
    echo ""
    echo "  2. Use in Claude:"
    echo "     Ask Claude to list Leantime projects or create tasks"
    echo ""
    echo "  3. Check logs:"
    echo "     docker logs dopemux-mcp-leantime-bridge"
    echo ""
    echo "Deep health:"
    echo "$DEEP_HEALTH"
    echo ""
    echo "list_projects sample:"
    echo "$PROJECT_LIST"
    echo ""
else
    echo "════════════════════════════════════════════════════════════"
    echo "  ⚠️  CONFIGURATION COMPLETE BUT CONNECTION FAILED"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "The API key has been configured, but the test connection failed."
    echo ""
    echo "Possible causes:"
    echo "  - API key is not yet active in Leantime"
    echo "  - Leantime service is still starting up"
    echo "  - Network connectivity issues"
    echo ""
    echo "Try:"
    echo "  1. Wait a few minutes and test again"
    echo "  2. Check Leantime logs: docker logs leantime"
    echo "  3. Verify API key in Leantime web UI"
    echo "  4. Check bridge logs: docker logs dopemux-mcp-leantime-bridge"
    echo ""
    echo "Deep health:"
    echo "$DEEP_HEALTH"
    echo ""
    echo "list_projects sample:"
    echo "$PROJECT_LIST"
    echo ""
fi
