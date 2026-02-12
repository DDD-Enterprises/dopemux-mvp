#!/bin/bash

# Dopemux Docker Compose Startup Script
# Starts the complete Dopemux stack with proper cleanup

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "================================"
echo "Dopemux Stack Startup"
echo "================================"
echo ""

# Check if docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Copying .env.example to .env..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "   ✅ Created .env - PLEASE FILL IN YOUR API KEYS"
        echo ""
        read -p "Press enter after updating .env with your API keys..."
    else
        echo "   ❌ .env.example not found!"
        exit 1
    fi
fi

cd "$PROJECT_ROOT"

# Guard against legacy project namespace contamination
if docker ps --filter 'label=com.docker.compose.project=dopemux-mvp' --format '{{.ID}}' | grep -q .; then
    echo "ERROR: legacy project dopemux-mvp detected. Clean it before running."
    echo "Run: docker compose -p dopemux-mvp -f compose.yml down --remove-orphans"
    exit 1
fi

docker network inspect dopemux-network >/dev/null 2>&1 || docker network create dopemux-network

echo "📦 Starting Dopemux stack..."
echo ""

# Start with --remove-orphans to clean up old containers
docker compose -p dopemux -f compose.yml up -d --remove-orphans

echo ""
echo "✅ Stack started!"
echo ""
echo "Service Status:"
docker compose -p dopemux -f compose.yml ps

echo ""
echo "Useful commands:"
echo "  View logs:  docker compose -p dopemux -f compose.yml logs -f SERVICE_NAME"
echo "  Stop:       docker compose -p dopemux -f compose.yml down"
echo "  Rebuild:    docker compose -p dopemux -f compose.yml build --no-cache"
echo ""
