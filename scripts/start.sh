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

# Guard against task-orchestrator containers from non-canonical compose projects.
# Those containers can auto-restart and appear outside the dopemux project group.
ROGUE_TASK_ROWS="$(docker ps -a \
  --filter 'label=com.docker.compose.service=task-orchestrator' \
  --format '{{.ID}}|{{.Names}}|{{.Label "com.docker.compose.project"}}' \
  | awk -F'|' '$3 != "dopemux"')"

if [ -n "$ROGUE_TASK_ROWS" ]; then
    echo "⚠️  Found task-orchestrator containers outside project 'dopemux'. Cleaning them up..."
    echo "$ROGUE_TASK_ROWS" | while IFS='|' read -r cid cname project; do
        project_label="${project:-unknown}"
        echo "   - $cname (project: $project_label)"
    done

    # Stop each non-canonical compose project cleanly when label is available.
    echo "$ROGUE_TASK_ROWS" | awk -F'|' '$3 != "" {print $3}' | sort -u | while IFS= read -r project; do
        [ -z "$project" ] && continue
        docker compose -p "$project" down --remove-orphans >/dev/null 2>&1 || true
    done

    # Force-remove remaining rogue containers to prevent restart loops.
    echo "$ROGUE_TASK_ROWS" | while IFS='|' read -r cid _ _; do
        [ -z "$cid" ] && continue
        docker rm -f "$cid" >/dev/null 2>&1 || true
    done

    echo "✅ Rogue task-orchestrator containers removed"
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
