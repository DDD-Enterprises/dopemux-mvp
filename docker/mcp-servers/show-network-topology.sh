#!/bin/bash
# Show current network topology for MCP services

echo "=== Dopemux MCP Network Topology ==="
echo ""

# Check if networks exist
echo "📡 External Networks:"
for net in dopemux-network leantime-net; do
    if docker network inspect "$net" >/dev/null 2>&1; then
        count=$(docker network inspect "$net" --format '{{len .Containers}}')
        echo "   ✅ $net ($count containers)"
    else
        echo "   ❌ $net (not created)"
    fi
done
echo ""

# Show services by network
echo "🔗 Services on dopemux-network:"
if docker network inspect dopemux-network >/dev/null 2>&1; then
    docker network inspect dopemux-network --format '{{range .Containers}}  - {{.Name}}{{"\n"}}{{end}}' | sort
else
    echo "   (network not found)"
fi
echo ""

echo "🔗 Services on leantime-net:"
if docker network inspect leantime-net >/dev/null 2>&1; then
    docker network inspect leantime-net --format '{{range .Containers}}  - {{.Name}}{{"\n"}}{{end}}' | sort
else
    echo "   (network not found)"
fi
echo ""

# Show Docker Compose projects
echo "📦 Docker Compose Projects:"
docker compose ls 2>/dev/null || echo "   (docker compose ls not available)"
echo ""

# Show any duplicate instances
echo "🔍 Checking for duplicate services (redis, postgres):"
docker ps --format '{{.Names}}' | grep -E 'redis|postgres' | sort || echo "   (no matches)"
echo ""

echo "✅ Topology scan complete"
