#!/bin/bash
# Dopemux Docker Network Consolidation Script
# Consolidates mcp-network and dopemux-unified-network into single dopemux-network

set -e

echo "🔧 Dopemux Network Consolidation Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running with docker access
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Cannot access Docker. Please check Docker is running.${NC}"
    exit 1
fi

echo "📊 Current network status:"
echo "-------------------------"
docker network ls | grep -E "dopemux|mcp" || echo "No dopemux networks found"
echo ""

# Create dopemux-network if it doesn't exist
echo "🔨 Creating consolidated network: dopemux-network"
if docker network inspect dopemux-network &> /dev/null; then
    echo -e "${YELLOW}⚠️  Network dopemux-network already exists${NC}"
else
    docker network create dopemux-network
    echo -e "${GREEN}✅ Created dopemux-network${NC}"
fi
echo ""

# Function to reconnect container to new network
reconnect_container() {
    local container=$1
    local old_network=$2
    
    echo "  🔄 Reconnecting ${container}..."
    
    # Connect to new network first (maintain connectivity)
    if ! docker network inspect dopemux-network --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}' | grep -q "^${container}$"; then
        docker network connect dopemux-network "${container}" 2>/dev/null || {
            echo -e "${YELLOW}    ⚠️  Could not connect ${container} (might not be running)${NC}"
            return 1
        }
    fi
    
    # Disconnect from old network
    docker network disconnect "${old_network}" "${container}" 2>/dev/null || {
        echo -e "${YELLOW}    ⚠️  Could not disconnect ${container} from ${old_network}${NC}"
    }
    
    echo -e "${GREEN}    ✅ ${container} migrated${NC}"
}

# Migrate containers from mcp-network
echo "🚚 Migrating containers from mcp-network..."
if docker network inspect mcp-network &> /dev/null; then
    containers=$(docker network inspect mcp-network --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}')
    if [ -n "$containers" ]; then
        while IFS= read -r container; do
            [ -z "$container" ] && continue
            reconnect_container "$container" "mcp-network"
        done <<< "$containers"
    else
        echo "  No containers on mcp-network"
    fi
else
    echo "  mcp-network doesn't exist"
fi
echo ""

# Migrate containers from dopemux-unified-network
echo "🚚 Migrating containers from dopemux-unified-network..."
if docker network inspect dopemux-unified-network &> /dev/null; then
    containers=$(docker network inspect dopemux-unified-network --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}')
    if [ -n "$containers" ]; then
        while IFS= read -r container; do
            [ -z "$container" ] && continue
            reconnect_container "$container" "dopemux-unified-network"
        done <<< "$containers"
    else
        echo "  No containers on dopemux-unified-network"
    fi
else
    echo "  dopemux-unified-network doesn't exist"
fi
echo ""

# Remove old networks (only if empty)
echo "🗑️  Removing old networks..."
for network in mcp-network dopemux-unified-network; do
    if docker network inspect "$network" &> /dev/null; then
        container_count=$(docker network inspect "$network" --format '{{len .Containers}}')
        if [ "$container_count" -eq 0 ]; then
            docker network rm "$network" && echo -e "${GREEN}✅ Removed $network${NC}" || echo -e "${YELLOW}⚠️  Could not remove $network${NC}"
        else
            echo -e "${YELLOW}⚠️  $network still has $container_count containers, skipping removal${NC}"
        fi
    fi
done
echo ""

echo "✅ Network consolidation complete!"
echo ""
echo "📊 Final network status:"
echo "-------------------------"
docker network ls | grep -E "dopemux|mcp" || echo "No dopemux networks found"
echo ""
echo "Containers on dopemux-network:"
docker network inspect dopemux-network --format '{{range .Containers}}  - {{.Name}}{{"\n"}}{{end}}'
echo ""
echo "🎉 Done! All containers now use dopemux-network"
echo ""
echo "⚠️  Next steps:"
echo "  1. Update docker-compose files to use 'dopemux-network'"
echo "  2. Test connectivity between services"
echo "  3. Restart services if needed: docker-compose up -d"
