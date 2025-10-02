#!/bin/bash
# MetaMCP Phase 1A Configuration Script
# Automatically configures MetaMCP with 4 working servers and 2 role modes

set -e

METAMCP_API="http://localhost:12009"
METAMCP_UI="http://localhost:12008"

echo "=========================================="
echo "MetaMCP Phase 1A Configuration"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if MetaMCP is running
echo "Checking MetaMCP status..."
if ! curl -s -f "$METAMCP_API/api/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ MetaMCP is not responding at $METAMCP_API${NC}"
    echo "Please ensure MetaMCP is running with: docker-compose -f metamcp/docker-compose.yml ps"
    exit 1
fi
echo -e "${GREEN}✅ MetaMCP is running${NC}"
echo ""

# Function to create MCP server
create_mcp_server() {
    local NAME=$1
    local PORT=$2

    echo "Creating MCP server: $NAME (port $PORT)..."

    RESPONSE=$(curl -s -X POST "$METAMCP_API/trpc/mcpServers.create" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$NAME\",
            \"type\": \"STDIO\",
            \"command\": \"curl\",
            \"args\": [\"-X\", \"POST\", \"http://localhost:$PORT/mcp\", \"-H\", \"Content-Type: application/json\", \"-d\", \"@-\"],
            \"env\": {}
        }" 2>&1)

    if echo "$RESPONSE" | grep -q "error\|Error\|ERROR"; then
        echo -e "${YELLOW}⚠️  $NAME may already exist or error occurred${NC}"
        echo "$RESPONSE" | head -5
    else
        echo -e "${GREEN}✅ Created $NAME${NC}"
    fi
}

# Function to create namespace
create_namespace() {
    local NAME=$1
    local DESCRIPTION=$2
    shift 2
    local SERVERS=("$@")

    echo "Creating namespace: $NAME..."

    # Build servers array for JSON
    SERVERS_JSON=$(printf ',"%s"' "${SERVERS[@]}")
    SERVERS_JSON="[${SERVERS_JSON:1}]"

    RESPONSE=$(curl -s -X POST "$METAMCP_API/trpc/namespaces.create" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$NAME\",
            \"description\": \"$DESCRIPTION\",
            \"serverNames\": $SERVERS_JSON
        }" 2>&1)

    if echo "$RESPONSE" | grep -q "error\|Error\|ERROR"; then
        echo -e "${YELLOW}⚠️  $NAME may already exist or error occurred${NC}"
    else
        echo -e "${GREEN}✅ Created namespace $NAME${NC}"
    fi
}

# Function to create endpoint
create_endpoint() {
    local ENDPOINT_ID=$1
    local NAMESPACE_NAME=$2

    echo "Creating endpoint: $ENDPOINT_ID..."

    RESPONSE=$(curl -s -X POST "$METAMCP_API/trpc/endpoints.create" \
        -H "Content-Type: application/json" \
        -d "{
            \"endpointId\": \"$ENDPOINT_ID\",
            \"namespaceName\": \"$NAMESPACE_NAME\",
            \"transport\": \"SSE\",
            \"authType\": \"API_KEY\"
        }" 2>&1)

    if echo "$RESPONSE" | grep -q "error\|Error\|ERROR"; then
        echo -e "${YELLOW}⚠️  $ENDPOINT_ID may already exist or error occurred${NC}"
        echo "$RESPONSE" | head -5
    else
        # Try to extract API key from response
        API_KEY=$(echo "$RESPONSE" | grep -o '"apiKey":"[^"]*' | cut -d'"' -f4)
        if [ -n "$API_KEY" ]; then
            echo -e "${GREEN}✅ Created endpoint $ENDPOINT_ID${NC}"
            echo -e "${YELLOW}📋 API Key: $API_KEY${NC}"
            echo ""
            echo "SAVE THIS KEY! Add to ~/.claude/metamcp-keys.env:"
            echo "${ENDPOINT_ID^^}_API_KEY=$API_KEY"
            echo ""
        else
            echo -e "${GREEN}✅ Endpoint created (check Web UI for API key)${NC}"
        fi
    fi
}

echo "=========================================="
echo "Step 1: Creating MCP Servers"
echo "=========================================="
echo ""

create_mcp_server "conport" "3004"
create_mcp_server "context7" "3002"
create_mcp_server "zen" "3003"
create_mcp_server "serena" "3006"

echo ""
echo "=========================================="
echo "Step 2: Creating Namespaces"
echo "=========================================="
echo ""

create_namespace "dopemux-quickfix" \
    "ADHD-optimized quick wins mode (3 tools, minimal cognitive load)" \
    "conport" "serena" "context7"

create_namespace "dopemux-act" \
    "Implementation mode with code navigation and debugging (4 tools)" \
    "conport" "serena" "context7" "zen"

echo ""
echo "=========================================="
echo "Step 3: Creating Endpoints"
echo "=========================================="
echo ""

echo -e "${YELLOW}⚠️  NOTE: API key generation may require authentication.${NC}"
echo -e "${YELLOW}If this fails, please create endpoints manually via Web UI:${NC}"
echo -e "${YELLOW}$METAMCP_UI${NC}"
echo ""

create_endpoint "quickfix-endpoint" "dopemux-quickfix"
create_endpoint "act-endpoint" "dopemux-act"

echo ""
echo "=========================================="
echo "Configuration Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Phase 1A Setup Complete${NC}"
echo ""
echo "Next Steps:"
echo "1. If API keys weren't shown above, visit: $METAMCP_UI"
echo "   - Go to 'Endpoints' and copy the API keys"
echo ""
echo "2. Save your API keys to: ~/.claude/metamcp-keys.env"
echo "   Format:"
echo "   QUICKFIX_API_KEY=your-key-here"
echo "   ACT_API_KEY=your-key-here"
echo ""
echo "3. Run the next script to generate Claude configs:"
echo "   ./scripts/generate-claude-configs.sh"
echo ""
echo "4. Test your endpoints in MetaMCP Inspector:"
echo "   $METAMCP_UI/inspector"
echo ""
