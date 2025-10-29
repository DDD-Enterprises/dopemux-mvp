#!/bin/bash
# Configure Leantime MCP Bridge with API Key

set -e

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
if [[ ! $API_KEY =~ ^lt_[a-zA-Z0-9]+_[a-zA-Z0-9]+$ ]]; then
    echo "❌ Invalid API key format!"
    echo ""
    echo "Expected format: lt_<user_id>_<secret>"
    echo "Example: lt_abc123def456_xyz789ghi012..."
    echo ""
    exit 1
fi

echo "✓ API key format validated"
echo ""

# Update .env file
ENV_FILE="docker/mcp-servers/leantime-bridge/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Config file not found: $ENV_FILE"
    exit 1
fi

# Backup existing config
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✓ Created backup of existing config"

# Update API token
if grep -q "^LEANTIME_API_TOKEN=" "$ENV_FILE"; then
    # Replace existing token
    sed -i.tmp "s|^LEANTIME_API_TOKEN=.*|LEANTIME_API_TOKEN=$API_KEY|" "$ENV_FILE"
    rm -f "${ENV_FILE}.tmp"
    echo "✓ Updated LEANTIME_API_TOKEN in $ENV_FILE"
else
    # Add new token
    echo "" >> "$ENV_FILE"
    echo "# API Token (added $(date))" >> "$ENV_FILE"
    echo "LEANTIME_API_TOKEN=$API_KEY" >> "$ENV_FILE"
    echo "✓ Added LEANTIME_API_TOKEN to $ENV_FILE"
fi

echo ""

# Restart bridge
echo "Restarting Leantime MCP Bridge..."
docker-compose -f docker/mcp-servers/docker-compose.yml restart leantime-bridge

echo ""
echo "✓ Bridge restarted"
echo ""

# Wait for service to be ready
echo "Waiting for service to be ready..."
sleep 5

# Test the connection
echo "Testing API connection..."
docker exec mcp-leantime-bridge python -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from leantime_bridge.http_server import LeantimeClient, LEANTIME_API_URL, LEANTIME_API_TOKEN

async def test():
    print(f'Testing: {LEANTIME_API_URL}/api/jsonrpc')
    async with LeantimeClient(LEANTIME_API_URL, LEANTIME_API_TOKEN) as client:
        try:
            result = await client.call_api('leantime.rpc.projects.getProjects')
            print('✅ API connection successful!')
            print(f'Projects available: {len(result) if isinstance(result, list) else 1}')
            return True
        except Exception as e:
            print(f'❌ Connection failed: {e}')
            return False

success = asyncio.run(test())
sys.exit(0 if success else 1)
" 2>&1

TEST_RESULT=$?

echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo "════════════════════════════════════════════════════════════"
    echo "  ✅ CONFIGURATION SUCCESSFUL!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "The Leantime MCP Bridge is now connected and working."
    echo ""
    echo "Next steps:"
    echo "  1. Test the integration:"
    echo "     cd docker/mcp-servers/leantime-bridge"
    echo "     python test_http_server.py"
    echo ""
    echo "  2. Use in Claude:"
    echo "     Ask Claude to list Leantime projects or create tasks"
    echo ""
    echo "  3. Check logs:"
    echo "     docker logs mcp-leantime-bridge"
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
    echo "  4. Check bridge logs: docker logs mcp-leantime-bridge"
    echo ""
fi
