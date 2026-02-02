#!/bin/bash

# Dopemux Leantime Environment Setup Script
# ADHD-Optimized Development Environment Configuration

set -e

echo "🧠 Dopemux Leantime Environment Setup"
echo "======================================"

# Colors for ADHD-friendly output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="/Users/hue/code/dopemux-mvp"
ENV_FILE="$PROJECT_ROOT/.env"

echo -e "${BLUE}🔧 Loading environment variables...${NC}"

# Source the main environment file
if [ -f "$ENV_FILE" ]; then
    set -a  # automatically export all variables
    source "$ENV_FILE"
    set +a  # stop auto-export
    echo -e "${GREEN}✅ Loaded main .env file${NC}"
else
    echo -e "${RED}❌ Main .env file not found at $ENV_FILE${NC}"
    exit 1
fi

# Check Leantime Docker status
echo -e "${BLUE}🐳 Checking Leantime Docker services...${NC}"

cd "$PROJECT_ROOT/docker/leantime"

# Check if containers are running
if docker-compose ps | grep -q "leantime.*Up"; then
    echo -e "${GREEN}✅ Leantime containers are running${NC}"

    # Wait for healthy status
    echo -e "${YELLOW}⏳ Waiting for Leantime to become healthy...${NC}"
    timeout=60
    elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if docker-compose ps | grep -q "leantime.*healthy"; then
            echo -e "${GREEN}✅ Leantime is healthy!${NC}"
            break
        elif docker-compose ps | grep -q "leantime.*unhealthy"; then
            echo -e "${YELLOW}🔄 Leantime is starting up... (${elapsed}s)${NC}"
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done

    if [ $elapsed -ge $timeout ]; then
        echo -e "${YELLOW}⚠️  Leantime is taking longer than expected to start${NC}"
        echo -e "${BLUE}📋 Current status:${NC}"
        docker-compose ps
    fi
else
    echo -e "${YELLOW}🚀 Starting Leantime services...${NC}"
    docker-compose up -d

    echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
    sleep 15
fi

# Test API connection
echo -e "${BLUE}🔗 Testing Leantime API connection...${NC}"

# Test basic HTTP connection
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$LEANTIME_API_URL" || echo "000")

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ] || [ "$HTTP_STATUS" = "301" ]; then
    echo -e "${GREEN}✅ Leantime HTTP connection successful (Status: $HTTP_STATUS)${NC}"
elif [ "$HTTP_STATUS" = "000" ]; then
    echo -e "${RED}❌ Cannot connect to Leantime at $LEANTIME_API_URL${NC}"
    echo -e "${YELLOW}🔍 Checking container logs...${NC}"
    docker-compose logs leantime --tail=10
else
    echo -e "${YELLOW}⚠️  Leantime returned status $HTTP_STATUS${NC}"
    echo -e "${BLUE}ℹ️  This might be normal if Leantime needs initial setup${NC}"
fi

# Check if install page is accessible
INSTALL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$LEANTIME_API_URL/install" || echo "000")
if [ "$INSTALL_STATUS" = "200" ]; then
    echo -e "${BLUE}🔧 Leantime installation page is accessible${NC}"
    echo -e "${YELLOW}📋 You may need to complete the Leantime setup at: $LEANTIME_API_URL/install${NC}"
fi

# Export environment variables for current session
echo -e "${BLUE}📤 Exporting environment variables for MCP...${NC}"

export LEANTIME_API_URL
export LEANTIME_API_TOKEN
export DOPEMUX_INTEGRATION_KEY

echo -e "${GREEN}✅ Environment variables exported:${NC}"
echo -e "   LEANTIME_API_URL=$LEANTIME_API_URL"
echo -e "   LEANTIME_API_TOKEN=$(echo $LEANTIME_API_TOKEN | sed 's/./*/g')"
echo -e "   DOPEMUX_INTEGRATION_KEY=$(echo $DOPEMUX_INTEGRATION_KEY | sed 's/./*/g')"

# Test MCP server
echo -e "${BLUE}🤖 Testing Leantime MCP server...${NC}"

MCP_SERVER_PATH="$PROJECT_ROOT/src/integrations/leantime_mcp_server.js"

if [ -f "$MCP_SERVER_PATH" ]; then
    echo -e "${GREEN}✅ Leantime MCP server file exists${NC}"

    # Test if Node.js can load the server
    if node -c "$MCP_SERVER_PATH" 2>/dev/null; then
        echo -e "${GREEN}✅ MCP server syntax is valid${NC}"
    else
        echo -e "${RED}❌ MCP server has syntax errors${NC}"
        node -c "$MCP_SERVER_PATH"
    fi
else
    echo -e "${RED}❌ Leantime MCP server not found at $MCP_SERVER_PATH${NC}"
fi

# Check MCP configuration
echo -e "${BLUE}⚙️  Checking MCP configuration...${NC}"

MCP_CONFIG="$PROJECT_ROOT/.claude/task-master-mcp-config.json"

if [ -f "$MCP_CONFIG" ]; then
    echo -e "${GREEN}✅ MCP configuration file exists${NC}"

    # Check if leantime-mcp is configured
    if grep -q "leantime-mcp" "$MCP_CONFIG"; then
        echo -e "${GREEN}✅ Leantime MCP server is configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Leantime MCP server not found in configuration${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  MCP configuration file not found${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Leantime Environment Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Complete Leantime setup at: $LEANTIME_API_URL/install (if needed)"
echo "2. Create a project and get API credentials"
echo "3. Test MCP integration with: /mcp"
echo "4. Use Leantime tools in Claude Code"
echo ""
echo -e "${YELLOW}🧠 ADHD-Optimized Features Enabled:${NC}"
echo "• Task chunking and cognitive load tracking"
echo "• Break reminders and attention monitoring"
echo "• Context preservation across sessions"
echo "• Gentle notifications and visual feedback"
echo ""
echo -e "${BLUE}📚 Available MCP Tools:${NC}"
echo "• leantime-get-tasks - Filter tasks by attention type"
echo "• leantime-create-task - Create ADHD-optimized tasks"
echo "• leantime-update-task - Update with cognitive tracking"
echo "• leantime-track-time - Time tracking with quality metrics"
echo "• leantime-get-projects - Project management overview"

# Save environment for other scripts
echo "export LEANTIME_API_URL='$LEANTIME_API_URL'" > "$PROJECT_ROOT/.env.leantime"
echo "export LEANTIME_API_TOKEN='$LEANTIME_API_TOKEN'" >> "$PROJECT_ROOT/.env.leantime"
echo "export DOPEMUX_INTEGRATION_KEY='$DOPEMUX_INTEGRATION_KEY'" >> "$PROJECT_ROOT/.env.leantime"

echo -e "${GREEN}💾 Environment saved to .env.leantime${NC}"
echo -e "${BLUE}🔄 To reload in new shells: source .env.leantime${NC}"