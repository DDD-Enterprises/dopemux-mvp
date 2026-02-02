#!/bin/bash
set -e

echo "🌉 Starting ConPort Event Bridge..."
echo ""

# Check if Redis is running
if ! docker ps | grep -q dopemux-redis-events; then
    echo "❌ Error: dopemux-redis-events is not running"
    echo "   Start it first with: docker-compose -f docker/docker-compose.event-bus.yml up -d"
    exit 1
fi

# Check if context.db exists
if [ ! -f "context_portal/context.db" ]; then
    echo "⚠️  Warning: context_portal/context.db not found"
    echo "   The Event Bridge will wait for the database to be created"
fi

# Build and start the Event Bridge
cd docker
docker-compose -f docker-compose.conport-bridge.yml up --build -d

echo ""
echo "✅ ConPort Event Bridge started!"
echo ""
echo "📊 Check logs:"
echo "   docker logs -f conport-event-bridge"
echo ""
echo "📈 Check health:"
echo "   docker ps --filter name=conport-event-bridge"
echo ""
echo "🔍 Check Redis events:"
echo "   docker exec -it dopemux-redis-events redis-cli XRANGE conport:events - + COUNT 10"
echo ""
