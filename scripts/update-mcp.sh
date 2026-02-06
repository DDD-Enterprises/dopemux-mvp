#!/bin/bash
# MCP Server Update Script
# Usage: ./scripts/update-mcp.sh <server-name>
# Usage: ./scripts/update-mcp.sh --all
#
# Examples:
#   ./scripts/update-mcp.sh pal
#   ./scripts/update-mcp.sh --all

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

MCP_SERVER=$1
PROJECT_ROOT="/Users/hue/code/dopemux-mvp"
DOCKER_COMPOSE_DIR="${PROJECT_ROOT}/docker/mcp-servers"

# Function to update PAL MCP
update_pal() {
    echo -e "${GREEN}🔄 Updating PAL MCP...${NC}"

    cd "${PROJECT_ROOT}/docker/mcp-servers/pal/pal-mcp-server" || exit 1

    # Clone latest from upstream
    echo "📥 Fetching latest version from GitHub..."
    rm -rf /tmp/pal-mcp-temp
    git clone --depth 1 https://github.com/BeehiveInnovations/pal-mcp-server.git /tmp/pal-mcp-temp

    # Backup current config if it exists
    if [ -f ".env" ]; then
        echo "💾 Backing up .env file..."
        cp .env /tmp/pal-mcp-env-backup
    fi

    # Copy new files
    echo "📋 Copying updated files..."
    cp -r /tmp/pal-mcp-temp/* .

    # Restore config if it existed
    if [ -f "/tmp/pal-mcp-env-backup" ]; then
        echo "♻️  Restoring .env file..."
        cp /tmp/pal-mcp-env-backup .env
        rm /tmp/pal-mcp-env-backup
    fi

    # Clean Python cache
    echo "🧹 Cleaning Python cache..."
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # Rebuild Docker container
    echo "🏗️  Rebuilding Docker container..."
    cd "${DOCKER_COMPOSE_DIR}" || exit 1
    docker-compose stop pal
    docker-compose rm -f pal
    docker-compose build --no-cache pal
    docker-compose up -d pal

    # Wait for container to be healthy
    echo "⏳ Waiting for container to be healthy..."
    sleep 5

    # Verify update
    echo "✅ Verifying update..."
    NEW_VERSION=$(docker exec mcp-pal python -c "from config import __version__; print(__version__)" 2>/dev/null || echo "Unknown")

    echo -e "${GREEN}✅ PAL MCP updated successfully!${NC}"
    echo "   New version: ${NEW_VERSION}"
    echo ""
    echo -e "${YELLOW}⚠️  Important: Restart Claude Code to use the new version${NC}"
}

# Function to update ConPort MCP (local service)
update_conport() {
    echo -e "${GREEN}🔄 Updating ConPort MCP...${NC}"

    cd "${PROJECT_ROOT}/services/conport" || exit 1

    # Activate venv and reinstall
    echo "📦 Reinstalling ConPort..."
    source venv/bin/activate
    pip install --upgrade -e .

    echo -e "${GREEN}✅ ConPort MCP updated successfully!${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Important: Restart Claude Code to use the new version${NC}"
}

# Function to update Serena MCP (local Docker service)
update_serena() {
    echo -e "${GREEN}🔄 Updating Serena MCP...${NC}"

    cd "${PROJECT_ROOT}/services/serena" || exit 1

    # Rebuild Docker container
    echo "🏗️  Rebuilding Docker container..."
    cd "${PROJECT_ROOT}/services" || exit 1
    docker-compose stop serena
    docker-compose rm -f serena
    docker-compose build --no-cache serena
    docker-compose up -d serena

    echo -e "${GREEN}✅ Serena MCP updated successfully!${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Important: Restart Claude Code to use the new version${NC}"
}

# Main logic
if [ -z "$MCP_SERVER" ]; then
    echo -e "${RED}❌ Error: No server specified${NC}"
    echo ""
    echo "Usage: ./scripts/update-mcp.sh <server-name>"
    echo "   or: ./scripts/update-mcp.sh --all"
    echo ""
    echo "Available servers: pal, conport, serena"
    exit 1
fi

case "$MCP_SERVER" in
    pal)
        update_pal
        ;;
    conport)
        update_conport
        ;;
    serena)
        update_serena
        ;;
    --all)
        echo -e "${GREEN}📦 Updating all MCP servers...${NC}"
        echo ""
        update_pal
        echo ""
        update_conport
        echo ""
        update_serena
        echo ""
        echo -e "${GREEN}✅ All MCP servers updated!${NC}"
        echo -e "${YELLOW}⚠️  Important: Restart Claude Code to use the new versions${NC}"
        ;;
    *)
        echo -e "${RED}❌ Error: Unknown server '${MCP_SERVER}'${NC}"
        echo ""
        echo "Available servers: pal, conport, serena"
        echo "Or use --all to update all servers"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Update complete!${NC}"
