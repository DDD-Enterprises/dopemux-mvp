#!/bin/bash

# Dopemux MCP Servers - Multi-Instance Launcher with Git Worktrees
# Usage: ./launch-instance.sh [instance_name] [port_base] [branch]
# Examples:
#   ./launch-instance.sh default 3000 main
#   ./launch-instance.sh dev 3030 feature/new-ui
#   ./launch-instance.sh staging 3060 develop
#   ./launch-instance.sh prod 3090 release/v1.2.0

set -e

# Default values
INSTANCE_NAME=${1:-default}
PORT_BASE=${2:-3000}
BRANCH=${3:-main}

# Get the project root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKTREE_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)/dopemux-instances"

echo "🔍 Project root: $PROJECT_ROOT"
echo "🌳 Worktree root: $WORKTREE_ROOT"

# Create worktree root directory if it doesn't exist
mkdir -p "$WORKTREE_ROOT"

# Define worktree path for this instance
WORKTREE_PATH="$WORKTREE_ROOT/$INSTANCE_NAME"

# Setup git worktree for this instance
echo "🌳 Setting up git worktree for instance '$INSTANCE_NAME' on branch '$BRANCH'..."

# Check if worktree already exists
if [ -d "$WORKTREE_PATH" ]; then
    echo "✅ Worktree already exists at $WORKTREE_PATH"
    # Check if it's on the correct branch
    cd "$WORKTREE_PATH"
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        echo "🔄 Switching from '$CURRENT_BRANCH' to '$BRANCH'..."
        git checkout "$BRANCH" || git checkout -b "$BRANCH"
    fi
else
    echo "🔨 Creating new worktree..."
    cd "$PROJECT_ROOT"

    # Check if branch exists locally
    if git branch --list "$BRANCH" | grep -q "$BRANCH"; then
        echo "✅ Branch '$BRANCH' exists locally"
        git worktree add "$WORKTREE_PATH" "$BRANCH"
    else
        echo "🔍 Branch '$BRANCH' not found locally, checking remote..."
        # Fetch latest from remote
        git fetch origin

        # Check if branch exists on remote
        if git branch -r --list "origin/$BRANCH" | grep -q "origin/$BRANCH"; then
            echo "✅ Branch '$BRANCH' found on remote, creating local tracking branch"
            git worktree add "$WORKTREE_PATH" -b "$BRANCH" "origin/$BRANCH"
        else
            echo "🔨 Creating new branch '$BRANCH' from current branch"
            git worktree add "$WORKTREE_PATH" -b "$BRANCH"
        fi
    fi
fi

# Validate port base (must be multiple of 30 to avoid conflicts)
if ! (( PORT_BASE % 30 == 0 )); then
    echo "⚠️  Warning: PORT_BASE should be a multiple of 30 to avoid conflicts"
    echo "   Recommended values: 3000, 3030, 3060, 3090, 3120, etc."
fi

# Check if port range is available
echo "🔍 Checking port availability for instance '$INSTANCE_NAME' (ports $PORT_BASE-$((PORT_BASE + 20)))..."

USED_PORTS=()
for port in $(seq $PORT_BASE $((PORT_BASE + 20))); do
    if lsof -i :$port >/dev/null 2>&1; then
        USED_PORTS+=($port)
    fi
done

if [ ${#USED_PORTS[@]} -gt 0 ]; then
    echo "❌ Error: The following ports are already in use: ${USED_PORTS[*]}"
    echo "   Please choose a different PORT_BASE or stop conflicting services"
    exit 1
fi

echo "✅ Port range $PORT_BASE-$((PORT_BASE + 20)) is available"

# Change to the instance worktree directory
cd "$WORKTREE_PATH/docker/mcp-servers"

# Create instance-specific .env file in the worktree
ENV_FILE=".env.${INSTANCE_NAME}"
echo "📝 Creating environment file: $WORKTREE_PATH/docker/mcp-servers/$ENV_FILE"

cat > "$ENV_FILE" << EOF
# Dopemux MCP Servers - Instance: $INSTANCE_NAME
# Auto-generated on $(date)

# === INSTANCE CONFIGURATION ===
DOPEMUX_INSTANCE=$INSTANCE_NAME
PORT_BASE=$PORT_BASE
WORKTREE_PATH=$WORKTREE_PATH
BRANCH=$BRANCH

# === CONTAINER & NETWORK NAMES ===
CONTAINER_PREFIX=mcp-${INSTANCE_NAME}
NETWORK_NAME=mcp-network-${INSTANCE_NAME}
NETWORK_SUBNET=172.$((20 + (PORT_BASE - 3000) / 30)).0.0/16
VOLUME_PREFIX=mcp_${INSTANCE_NAME}

# === API KEYS (EDIT THESE!) ===
CONTEXT7_API_KEY=your_context7_key
CONTEXT7_ENDPOINT=https://api.context7.com
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
VOYAGEAI_API_KEY=your_voyageai_key
EXA_API_KEY=your_exa_key

# === PORT MAPPINGS (Auto-calculated) ===
# MAS Sequential Thinking: $((PORT_BASE + 1))
# Context7: $((PORT_BASE + 2))
# Zen: $((PORT_BASE + 3))
# ConPort: $((PORT_BASE + 4))
# Task Master AI: $((PORT_BASE + 5))
# Serena: $((PORT_BASE + 6))
# Claude Context: $((PORT_BASE + 7))
# Exa: $((PORT_BASE + 8))
# MorphLLM: $((PORT_BASE + 11))
# Desktop Commander: $((PORT_BASE + 12))
# Minio Console: $((PORT_BASE + 15))
# Minio API: $((PORT_BASE + 16))
# Milvus: $((PORT_BASE + 17))
# Milvus WebUI: $((PORT_BASE + 18))
EOF

echo "⚙️  Environment file created. Please edit $ENV_FILE to add your API keys."
echo ""
echo "📋 Instance Configuration Summary:"
echo "   Instance Name: $INSTANCE_NAME"
echo "   Port Range: $PORT_BASE-$((PORT_BASE + 20))"
echo "   Network: mcp-network-${INSTANCE_NAME}"
echo "   Containers: mcp-${INSTANCE_NAME}-*"
echo "   Volumes: mcp_${INSTANCE_NAME}_*"
echo ""
echo "🚀 To launch this instance:"
echo "   1. Edit $ENV_FILE and add your API keys"
echo "   2. Run: docker-compose --env-file $ENV_FILE -f docker-compose.multi-instance.yml up -d"
echo ""
echo "🛑 To stop this instance:"
echo "   docker-compose --env-file $ENV_FILE -f docker-compose.multi-instance.yml down"
echo ""
echo "📊 To view logs:"
echo "   docker-compose --env-file $ENV_FILE -f docker-compose.multi-instance.yml logs -f"

# Create helper scripts for this instance
INSTANCE_DIR="instance-${INSTANCE_NAME}"
mkdir -p "$INSTANCE_DIR"

# Start script
cat > "$INSTANCE_DIR/start.sh" << EOF
#!/bin/bash
cd "$WORKTREE_PATH/docker/mcp-servers"
echo "🚀 Starting Dopemux MCP instance: $INSTANCE_NAME"
echo "📁 Working from: $WORKTREE_PATH"
echo "🌳 Branch: $BRANCH"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml up -d
echo "✅ Instance $INSTANCE_NAME started on ports $PORT_BASE-$((PORT_BASE + 20))"
echo "💻 Claude Code working directory: $WORKTREE_PATH"
EOF

# Stop script
cat > "$INSTANCE_DIR/stop.sh" << EOF
#!/bin/bash
cd "$WORKTREE_PATH/docker/mcp-servers"
echo "🛑 Stopping Dopemux MCP instance: $INSTANCE_NAME"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml down
echo "✅ Instance $INSTANCE_NAME stopped"
EOF

# Logs script
cat > "$INSTANCE_DIR/logs.sh" << EOF
#!/bin/bash
cd "$WORKTREE_PATH/docker/mcp-servers"
echo "📊 Showing logs for Dopemux MCP instance: $INSTANCE_NAME"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml logs -f
EOF

# Status script
cat > "$INSTANCE_DIR/status.sh" << EOF
#!/bin/bash
cd "$WORKTREE_PATH/docker/mcp-servers"
echo "📊 Status for Dopemux MCP instance: $INSTANCE_NAME"
echo "📁 Working from: $WORKTREE_PATH"
echo "🌳 Branch: $BRANCH"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml ps
EOF

# Open worktree script
cat > "$INSTANCE_DIR/open.sh" << EOF
#!/bin/bash
echo "📁 Opening worktree for instance: $INSTANCE_NAME"
echo "🌳 Branch: $BRANCH"
echo "💻 Path: $WORKTREE_PATH"
if command -v code &> /dev/null; then
    echo "🚀 Opening in VS Code..."
    code "$WORKTREE_PATH"
elif command -v claude &> /dev/null; then
    echo "🚀 Opening in Claude Code..."
    cd "$WORKTREE_PATH" && claude
else
    echo "💡 Navigate to: $WORKTREE_PATH"
fi
EOF

chmod +x "$INSTANCE_DIR"/*.sh

echo "📁 Helper scripts created in $INSTANCE_DIR/:"
echo "   start.sh  - Start the instance"
echo "   stop.sh   - Stop the instance"
echo "   logs.sh   - View logs"
echo "   status.sh - Check status"