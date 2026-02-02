#!/bin/bash

# Start Dopemux Coordination Dashboard

echo "🚀 Starting Dopemux Coordination Dashboard"
echo "========================================="

# Check if Redis is running
if ! docker ps | grep -q dopemux-redis-events; then
    echo "⚠️  Redis event bus not running. Starting it now..."
    docker-compose -f docker/docker-compose.event-bus.yml up -d
    sleep 3
fi

# Check Redis connection
if nc -z localhost 6379; then
    echo "✅ Redis is running on port 6379"
else
    echo "❌ Redis is not accessible on port 6379"
    echo "Please ensure Redis is running:"
    echo "docker-compose -f docker/docker-compose.event-bus.yml up -d"
    exit 1
fi

# Install dependencies if needed
if ! python -c "import aiohttp" 2>/dev/null; then
    echo "📦 Installing required dependencies..."
    pip install aiohttp aiohttp-cors
fi

# Start the dashboard
echo ""
echo "📊 Starting dashboard server..."
echo "Dashboard URL: http://localhost:8090"
echo "Redis Commander: http://localhost:8081"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python dashboard/coordination_dashboard.py