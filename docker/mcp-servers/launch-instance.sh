#!/bin/bash

# Dopemux MCP Servers - Multi-Instance Launcher
# Usage: ./launch-instance.sh [instance_name] [port_base]
# Examples:
#   ./launch-instance.sh default 3000
#   ./launch-instance.sh dev 3030
#   ./launch-instance.sh staging 3060
#   ./launch-instance.sh prod 3090

set -e

# Default values
INSTANCE_NAME=${1:-default}
PORT_BASE=${2:-3000}

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

# Create instance-specific .env file
ENV_FILE=".env.${INSTANCE_NAME}"
echo "📝 Creating environment file: $ENV_FILE"

cat > "$ENV_FILE" << EOF
# Dopemux MCP Servers - Instance: $INSTANCE_NAME
# Auto-generated on $(date)

# === INSTANCE CONFIGURATION ===
DOPEMUX_INSTANCE=$INSTANCE_NAME
PORT_BASE=$PORT_BASE

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
cd "$(dirname "\$0")/.."
echo "🚀 Starting Dopemux MCP instance: $INSTANCE_NAME"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml up -d
echo "✅ Instance $INSTANCE_NAME started on ports $PORT_BASE-$((PORT_BASE + 20))"
EOF

# Stop script
cat > "$INSTANCE_DIR/stop.sh" << EOF
#!/bin/bash
cd "$(dirname "\$0")/.."
echo "🛑 Stopping Dopemux MCP instance: $INSTANCE_NAME"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml down
echo "✅ Instance $INSTANCE_NAME stopped"
EOF

# Logs script
cat > "$INSTANCE_DIR/logs.sh" << EOF
#!/bin/bash
cd "$(dirname "\$0")/.."
echo "📊 Showing logs for Dopemux MCP instance: $INSTANCE_NAME"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml logs -f
EOF

# Status script
cat > "$INSTANCE_DIR/status.sh" << EOF
#!/bin/bash
cd "$(dirname "\$0")/.."
echo "📊 Status for Dopemux MCP instance: $INSTANCE_NAME"
docker-compose --env-file .env.${INSTANCE_NAME} -f docker-compose.multi-instance.yml ps
EOF

chmod +x "$INSTANCE_DIR"/*.sh

echo "📁 Helper scripts created in $INSTANCE_DIR/:"
echo "   start.sh  - Start the instance"
echo "   stop.sh   - Stop the instance"
echo "   logs.sh   - View logs"
echo "   status.sh - Check status"