#!/bin/bash

# Dopemux Docker Cleanup & Recovery Script
# Removes orphan containers and prepares for fresh start

set -e

echo "================================"
echo "Dopemux Docker System Cleanup"
echo "================================"
echo ""

# Check if docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

echo "📊 Current Docker Status:"
echo "  Containers:"
docker ps -a --format "table {{.Status}}\t{{.Names}}" | sort | uniq -c | tail -5
echo ""

read -p "🗑️  Remove all exited containers? (y/N): " -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing exited containers..."
    REMOVED=$(docker container prune -f --filter "status=exited" 2>&1 | grep -o "[0-9]* container" || echo "0 containers")
    echo "✅ Removed $REMOVED"
    echo ""
fi

read -p "🗑️  Remove unused images (not in use by containers)? (y/N): " -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing dangling images..."
    REMOVED=$(docker image prune -f 2>&1 | grep -o "[0-9]* image" || echo "0 images")
    echo "✅ Removed $REMOVED"
    echo ""
fi

read -p "🗑️  Remove unused volumes? (y/N): " -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing unused volumes..."
    REMOVED=$(docker volume prune -f 2>&1 | grep -o "[0-9]* volume" || echo "0 volumes")
    echo "✅ Removed $REMOVED"
    echo ""
fi

echo "================================"
echo "Post-Cleanup Docker Status:"
echo "================================"
echo ""
echo "$(docker ps -a | wc -l) total containers (including running)"
echo "$(docker images -q | wc -l) total images"
echo ""

echo "✅ Cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in your API keys"
echo "  2. Review the DOCKER_AUDIT_REPORT.md for recommended fixes"
echo "  3. Test startup with: docker compose -f compose.yml up -d --remove-orphans"
