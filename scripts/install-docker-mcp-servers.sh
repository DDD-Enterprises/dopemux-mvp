#!/bin/bash

# === Dopemux Docker MCP Servers Installation Script ===
# Installs and configures Docker-based MCP servers for enhanced functionality

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_MCP_DIR="$PROJECT_ROOT/docker/mcp-servers"

echo "🚀 Dopemux Docker MCP Servers Installation"
echo "=========================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment variables
validate_env_var() {
    local var_name="$1"
    local var_value="${!var_name}"

    if [ -z "$var_value" ]; then
        echo "⚠️  Warning: $var_name is not set"
        return 1
    else
        echo "✅ $var_name is configured"
        return 0
    fi
}

# Function to install a Docker MCP server
install_docker_mcp_server() {
    local server_name="$1"
    local repo_url="$2"
    local provider="$3"
    local model="$4"
    # Optional git ref (branch, tag, or SHA) to pin the checkout. Defaults to "main".
    # SECURITY/SUPPLY-CHAIN TODO: "main" is a moving branch HEAD — pin a verified tag or
    # commit SHA here (or pass it as $5 / a $REF env var) once a known-good revision of the
    # upstream repo has been audited, so installs become reproducible and tamper-evident.
    local ref="${5:-${MCP_SERVER_REF:-main}}"

    echo "📦 Installing $server_name..."

    local server_dir="$DOCKER_MCP_DIR/$server_name"

    # Create server directory if it doesn't exist
    mkdir -p "$server_dir"
    cd "$server_dir"

    # Clone or update repository
    if [ -d ".git" ]; then
        echo "🔄 Updating existing $server_name repository (ref: $ref)..."
        git fetch --all --tags
        git checkout "$ref"
        # Only fast-forward when tracking a branch; tags/SHAs have no upstream to pull.
        git pull --ff-only 2>/dev/null || true
    else
        echo "📥 Cloning $server_name repository (ref: $ref)..."
        git clone "$repo_url" .
        git checkout "$ref"
    fi

    if [ "$ref" = "main" ] || [ "$ref" = "master" ]; then
        echo "⚠️  WARNING: $server_name is pinned to moving branch '$ref' (unpinned HEAD)."
        echo "    Builds are NOT reproducible. Pin a tag/SHA via MCP_SERVER_REF to harden."
    fi

    # Create environment configuration
    echo "⚙️ Configuring $server_name environment..."

    cat > .env << EOF
# === $server_name MCP Server Configuration ===
LLM_PROVIDER=$provider

# === API Keys ===
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
GITHUB_TOKEN=${GITHUB_TOKEN:-}
EXA_API_KEY=${EXA_API_KEY:-}

# === Model Configuration ===
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_TEAM_MODEL_ID=$model
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_AGENT_MODEL_ID=$model

# === ADHD Optimizations ===
ENABLE_CONTEXT_PRESERVATION=true
ENABLE_GENTLE_GUIDANCE=true
MAX_THINKING_STEPS=10

# === Docker Configuration ===
MCP_SERVER_PORT=3001
EOF

    # Restrict the .env (contains API keys/tokens) to the owner only — it was world-readable.
    chmod 600 .env

    # Fix Dockerfile if needed (for src/ layout)
    if [ -f "Dockerfile" ] && grep -q "COPY main.py" Dockerfile; then
        echo "🔧 Fixing Dockerfile for src/ layout..."
        sed -i.bak 's/COPY main.py .*/COPY src\/ .\/src\//' Dockerfile
        rm -f Dockerfile.bak
    fi

    echo "✅ $server_name configured successfully"
    echo ""
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create Docker MCP servers directory
echo "📁 Setting up Docker MCP servers directory..."
mkdir -p "$DOCKER_MCP_DIR"
echo "✅ Directory created: $DOCKER_MCP_DIR"
echo ""

# Check environment variables
echo "🔍 Checking environment configuration..."
env_valid=true

# Check for at least one provider API key
if ! validate_env_var "DEEPSEEK_API_KEY" && ! validate_env_var "OPENAI_API_KEY" && ! validate_env_var "GITHUB_TOKEN"; then
    echo "❌ No LLM provider API keys found. You need at least one of:"
    echo "   - DEEPSEEK_API_KEY (recommended)"
    echo "   - OPENAI_API_KEY"
    echo "   - GITHUB_TOKEN"
    env_valid=false
fi

validate_env_var "EXA_API_KEY" || true

if [ "$env_valid" = false ]; then
    echo ""
    echo "🛑 Missing required environment variables. Please set them and run again."
    echo "   Example: export DEEPSEEK_API_KEY='your_key_here'"
    exit 1
fi

echo ""

# Install Docker MCP servers
echo "🔧 Installing Docker MCP Servers..."
echo ""

# Configure primary provider based on available keys
if [ -n "$DEEPSEEK_API_KEY" ]; then
    PROVIDER="deepseek"
    MODEL="deepseek-reasoner"
    echo "🧠 Using DeepSeek provider with reasoning model"
elif [ -n "$GITHUB_TOKEN" ]; then
    PROVIDER="github"
    MODEL="gpt-4o"
    echo "🧠 Using GitHub Models provider"
elif [ -n "$OPENAI_API_KEY" ]; then
    PROVIDER="openai"
    MODEL="gpt-4o"
    echo "🧠 Using OpenAI provider"
fi

echo ""

# Install mas-sequential-thinking server
install_docker_mcp_server \
    "mcp-server-mas-sequential-thinking" \
    "https://github.com/FradSer/mcp-server-mas-sequential-thinking.git" \
    "$PROVIDER" \
    "$MODEL"

# Create master Docker Compose file
echo "📝 Creating master Docker Compose configuration..."

cat > "$DOCKER_MCP_DIR/docker-compose.yml" << 'EOF'
services:
  mas-sequential-thinking:
    build:
      context: ./mcp-server-mas-sequential-thinking
      dockerfile: Dockerfile
    container_name: mcp-mas-sequential-thinking
    restart: unless-stopped
    networks:
      - mcp-network
    env_file:
      - ./mcp-server-mas-sequential-thinking/.env
    ports:
      - "3001:3001"
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      timeout: 10s
      retries: 3
      interval: 30s
      start_period: 30s
    volumes:
      - mcp_logs:/app/logs
      - mcp_cache:/app/cache

networks:
  mcp-network:
    driver: bridge
    name: mcp-network
  leantime-net:
    external: true

volumes:
  mcp_logs:
    driver: local
  mcp_cache:
    driver: local
EOF

# Create management scripts
echo "🛠️ Creating management scripts..."

# Create start script
cat > "$DOCKER_MCP_DIR/start-all-mcp-servers.sh" << 'EOF'
#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting all Dopemux MCP servers..."

# Validate environment
for server_dir in */; do
    if [ -f "$server_dir/.env" ]; then
        echo "✅ Found configuration for ${server_dir%/}"
    fi
done

echo ""
echo "🔨 Building and starting containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "✅ All MCP servers started successfully!"
echo ""
echo "📋 Management commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop all:  docker-compose down"
echo "   Restart:   ./start-all-mcp-servers.sh"
EOF

chmod +x "$DOCKER_MCP_DIR/start-all-mcp-servers.sh"

# Create stop script
cat > "$DOCKER_MCP_DIR/stop-all-mcp-servers.sh" << 'EOF'
#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping all Dopemux MCP servers..."
docker-compose down

echo "✅ All MCP servers stopped"
EOF

chmod +x "$DOCKER_MCP_DIR/stop-all-mcp-servers.sh"

# Create logs script
cat > "$DOCKER_MCP_DIR/view-logs.sh" << 'EOF'
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -n "$1" ]; then
    echo "📋 Viewing logs for $1..."
    docker-compose logs -f "$1"
else
    echo "📋 Viewing logs for all MCP servers..."
    docker-compose logs -f
fi
EOF

chmod +x "$DOCKER_MCP_DIR/view-logs.sh"

echo "✅ Management scripts created"
echo ""

# Test the installation
echo "🧪 Testing installation..."
cd "$DOCKER_MCP_DIR"

if ./start-all-mcp-servers.sh; then
    echo "✅ Test successful - MCP servers are running"

    echo ""
    echo "📊 Final status check..."
    sleep 3
    docker-compose ps

else
    echo "❌ Test failed - check the logs for issues"
    echo "   Debug: docker-compose logs"
fi

echo ""
echo "🎉 Docker MCP Servers installation complete!"
echo ""
echo "📋 Quick Start:"
echo "   Start:    $DOCKER_MCP_DIR/start-all-mcp-servers.sh"
echo "   Stop:     $DOCKER_MCP_DIR/stop-all-mcp-servers.sh"
echo "   Logs:     $DOCKER_MCP_DIR/view-logs.sh"
echo ""
echo "🔧 Configuration files:"
echo "   Docker:   $DOCKER_MCP_DIR/docker-compose.yml"
echo "   Env:      $DOCKER_MCP_DIR/*/".env""
echo ""