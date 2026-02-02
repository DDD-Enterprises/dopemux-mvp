#!/bin/bash

# Start Dopemux CLI Dashboard (React Ink)

echo "🎯 Starting Dopemux CLI Dashboard"
echo "=================================="
echo ""

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

# Navigate to dashboard directory
cd dashboard/cli-dashboard

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build TypeScript if not built
if [ ! -d "dist" ]; then
    echo "🔨 Building dashboard..."
    npm run build
fi

echo ""
echo "🚀 Starting CLI Dashboard..."
echo ""
echo "Controls:"
echo "  [1-4] Switch views"
echo "  [C]   Clear events"
echo "  [Q]   Quit"
echo ""

# Run the dashboard
npm run start