#!/bin/bash

set -e

# P2: Unified project name for all Dopemux compose stacks
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dopemux}"

# Usage: ./start-all-mcp-servers.sh [--workspace /path/to/workspace]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse arguments
WORKSPACE_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace|-w)
            WORKSPACE_PATH="$2"
            shift 2
            ;;
        --help|-h)
            cat << 'HELP'
Usage: ./start-all-mcp-servers.sh [OPTIONS]

OPTIONS:
    --workspace, -w PATH    Set workspace path for MCP servers
    --help, -h             Show this help message

EXAMPLES:
    ./start-all-mcp-servers.sh                    # Use current workspace
    ./start-all-mcp-servers.sh -w ~/code/project  # Specific workspace

ENVIRONMENT VARIABLES:
    DEFAULT_WORKSPACE_PATH    Fallback workspace if not specified
    WORKSPACE_PATHS          Additional workspaces to monitor
HELP
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine workspace
if [ -n "$WORKSPACE_PATH" ]; then
    export DOPEMUX_WORKSPACE_ID="$WORKSPACE_PATH"
    echo "📁 Using explicit workspace: $WORKSPACE_PATH"
elif [ -n "$DEFAULT_WORKSPACE_PATH" ]; then
    export DOPEMUX_WORKSPACE_ID="$DEFAULT_WORKSPACE_PATH"
    echo "📁 Using default workspace: $DEFAULT_WORKSPACE_PATH"
else
    export DOPEMUX_WORKSPACE_ID="$(pwd)"
    echo "📁 Using current directory as workspace: $(pwd)"
fi

# Load workspace environment
WORKSPACE_ENV_PATH="$(python3 "$PROJECT_ROOT/scripts/workspace_env_path.py" 2>/dev/null || true)"
if [ -n "$WORKSPACE_ENV_PATH" ] && [ -f "$WORKSPACE_ENV_PATH" ]; then
  echo "📦 Loading workspace environment from $WORKSPACE_ENV_PATH"
  # shellcheck source=/dev/null
  source "$WORKSPACE_ENV_PATH"
else
  echo "⚠️  Workspace env file not found; using current settings"
fi

echo "🚀 Starting all Dopemux MCP servers..."
echo "=========================================="

# Compose validation fails if an `env_file` path is missing, even when the
# service can run with inherited environment variables. Create placeholders for
# optional local env files to keep startup resilient.
ensure_optional_env_file() {
  local env_path="$1"
  if [ -f "$env_path" ]; then
    return 0
  fi
  mkdir -p "$(dirname "$env_path")"
  : > "$env_path"
  echo "⚠️  Created placeholder env file: $env_path"
}

ensure_optional_env_file "./task-master-ai/.env"
ensure_optional_env_file "./task-orchestrator/.env"

# Only create leantime-bridge env if using linked mode
if [ "${ENABLE_LEANTIME:-0}" = "1" ]; then
  ensure_optional_env_file "./leantime-bridge/.env"
fi

# P0: Validate docker-compose.yml before proceeding
echo "🔍 Validating docker-compose.yml..."
if ! docker compose config >/dev/null 2>&1; then
  echo "❌ docker-compose.yml invalid; refusing to start MCP servers"
  echo "   Run 'docker compose config' to see validation errors"
  exit 1
fi
echo "✅ docker-compose.yml is valid"
echo ""

# Validate environment
echo "📋 Checking server configurations..."
for server_dir in */; do
    if [ -f "$server_dir/.env" ]; then
        echo "✅ Found configuration for ${server_dir%/}"
    elif [ -d "$server_dir" ]; then
        echo "⚠️  ${server_dir%/} - using environment variables"
    fi
done

echo ""
echo "🔧 Checking required environment variables..."

# Check for critical API keys
missing_keys=()
[ -z "$OPENAI_API_KEY" ] && missing_keys+=("OPENAI_API_KEY")
[ -z "$EXA_API_KEY" ] && missing_keys+=("EXA_API_KEY")

if [ ${#missing_keys[@]} -gt 0 ]; then
    echo "⚠️  Warning: Missing API keys: ${missing_keys[*]}"
    echo "   Some servers may not function properly"
fi

echo ""
echo "🔨 Preparing Docker prerequisites..."

# Ensure external networks exist
ensure_network() {
  local net="$1"
  if ! docker network inspect "$net" >/dev/null 2>&1; then
    echo "🌐 Creating network: $net"
    docker network create "$net" >/dev/null
  else
    echo "✅ Network exists: $net"
  fi
}

ensure_network mcp-network
ensure_network dopemux-unified-network

# Only create leantime-net if Leantime integration is enabled
if [ "${ENABLE_LEANTIME:-0}" = "1" ]; then
  ensure_network leantime-net
else
  echo "ℹ️  Skipping leantime-net creation (set ENABLE_LEANTIME=1 to enable)"
fi

# Ensure external volumes exist
ensure_volume() {
  local vol="$1"
  if ! docker volume inspect "$vol" >/dev/null 2>&1; then
    echo "💾 Creating volume: $vol"
    docker volume create "$vol" >/dev/null
  else
    echo "✅ Volume exists: $vol"
  fi
}

ensure_volume mcp_logs
ensure_volume mcp_cache

# P1: Start Leantime if enabled
if [ "${ENABLE_LEANTIME:-0}" = "1" ]; then
  echo ""
  echo "🏗️  Starting Leantime stack (ENABLE_LEANTIME=1)..."
  if [ -f ../leantime/docker-compose.yml ]; then
    (cd ../leantime && docker compose up -d --build)
    echo "✅ Leantime stack started"
  else
    echo "⚠️  Leantime compose file not found at ../leantime/docker-compose.yml"
  fi
else
  echo ""
  echo "ℹ️  Skipping Leantime startup (set ENABLE_LEANTIME=1 to enable)"
fi

check_leantime_health() {
  local url="${LEANTIME_HEALTH_URL:-http://localhost:8080/index.php}"
  local expect="${LEANTIME_HEALTH_EXPECT:-Dopemux plugin register.php loaded successfully}"
  echo "🩺 Checking Leantime health at ${url} (expecting '${expect}') ..."
  for attempt in {1..10}; do
    if response=$(curl -fsS --max-time 5 "$url" 2>/dev/null); then
      if [[ "$response" == *"$expect"* ]]; then
        echo "✅ Leantime responded with expected content"
        return 0
      fi
      echo "   response received but missing expected content; retrying in 3s"
    else
      echo "   attempt ${attempt} failed; retrying in 3s"
    fi
    sleep 3
  done
  echo "❌ Leantime health check failed after 10 attempts"
  return 1
}

echo ""
echo "🔨 Building and starting containers (idempotent)..."

# Helper: start a service safely, avoiding container-name conflicts
safe_up() {
  local service="$1"; shift
  local cname="$1"; shift
  
  # Check if service exists in docker-compose first
  if ! docker compose config --services 2>/dev/null | grep -q "^${service}$"; then
    echo "ℹ️  ${service} not in docker-compose.yml (skipping)"
    return 0
  fi
  
  if docker ps -a --format '{{.Names}}' | grep -q "^${cname}$"; then
    if [ "$(docker inspect -f '{{.State.Running}}' "${cname}")" != "true" ]; then
      echo "▶️  Starting existing container ${cname}"
      docker start "${cname}" >/dev/null || true
    else
      echo "✅ ${cname} already running"
    fi
  else
    echo "🚀 Creating ${cname} via docker-compose (${service})"
    # Prefer using existing local images first (offline-friendly), then fallback to build
    if docker-compose up -d --no-build "${service}" 2>/dev/null; then
      echo "✅ Started ${cname} using cached image"
    else
      echo "🧱 Cached image not found; building ${cname}"
      # P0: Don't swallow failures for critical services
      docker-compose up -d --build "${service}"
    fi
  fi
}

SUFFIX="${DOPEMUX_INSTANCE_ID:+_}${DOPEMUX_INSTANCE_ID}"

# Start infrastructure first (vector database for dope-context)
echo "🗄️  Starting infrastructure..."
# Databases/caches first - only if they exist in docker-compose
if docker compose config --services | grep -q "^redis-primary$"; then
  safe_up redis-primary dopemux-redis-primary
else
  echo "ℹ️  redis-primary not in compose (should be started via smoke/master stack)"
fi

if docker compose config --services | grep -q "^dopemux-postgres-age$"; then
  safe_up dopemux-postgres-age dopemux-postgres-age
else
  echo "ℹ️  postgres not in MCP compose (should be started via smoke/master stack)"
fi

if docker compose config --services | grep -q "^qdrant$"; then
  safe_up qdrant mcp-qdrant
else
  echo "ℹ️  qdrant not in MCP compose (should be started via smoke/master stack)"
  # Check if qdrant is already running elsewhere
  if docker ps --format '{{.Names}}' | grep -q "qdrant"; then
    echo "✅ Qdrant already running (external)"
  else
    echo "⚠️  Qdrant not found - dope-context may not work"
  fi
fi

echo "⏳ Waiting for infrastructure to be ready..."
sleep 5

# Initialize ConPort schema on first run (idempotent)
ensure_conport_schema() {
  local pgc="dopemux-postgres-age"
  local sql="./conport/schema.sql"
  if ! docker inspect "$pgc" >/dev/null 2>&1; then
    echo "ℹ️  Skipping schema init: $pgc not running"
    return
  fi
  # Wait for Postgres to be healthy
  for i in {1..15}; do
    if [ "$(docker inspect -f '{{.State.Health.Status}}' "$pgc" 2>/dev/null || echo unknown)" = "healthy" ]; then
      break
    fi
    sleep 2
  done
  # Check if primary table exists
  local exists
  exists=$(docker exec -e PGPASSWORD=dopemux_age_dev_password "$pgc" \
    psql -U dopemux_age -d dopemux_knowledge_graph -tAc "SELECT to_regclass('public.workspace_contexts');" 2>/dev/null | tr -d '[:space:]') || true
  if [ -z "$exists" ] || [ "$exists" = "" ] || [ "$exists" = "null" ]; then
    echo "🧩 Applying ConPort schema (first run)"
    if [ -f "$sql" ]; then
      docker cp "$sql" "$pgc":/tmp/conport_schema.sql
      if docker exec -e PGPASSWORD=dopemux_age_dev_password -i "$pgc" \
        psql -U dopemux_age -d dopemux_knowledge_graph -v ON_ERROR_STOP=1 -f /tmp/conport_schema.sql; then
        echo "✅ ConPort schema applied"
      else
        echo "⚠️  Failed to apply ConPort schema (continuing)"
      fi
    else
      echo "ℹ️  Schema file not found: $sql"
    fi
  else
    echo "✅ ConPort schema already present"
  fi
}

ensure_conport_schema

# Fast per-instance mode: only bring up ConPort/Serena for this instance
if [ "${DOPEMUX_FAST_ONLY:-0}" = "1" ] && [ -n "${DOPEMUX_INSTANCE_ID:-}" ]; then
  echo "⚡ Fast per-instance start: starting only ConPort/Serena for instance ${DOPEMUX_INSTANCE_ID}"
  safe_up conport "mcp-conport${SUFFIX}"
  safe_up serena "mcp-serena${SUFFIX}"
  echo "\n== Fast start status =="
  docker-compose ps | grep -E "mcp-(conport|serena)" || true
  echo "\n✅ Fast per-instance start completed."
  exit 0
fi

# Start critical path servers (staggered for ADHD optimizations)
echo "⚡ Starting critical path servers..."
safe_up pal dopemux-mcp-pal
safe_up pal dopemux-mcp-pal  # pal is the zen/code analysis server
safe_up litellm dopemux-mcp-litellm

echo "⏳ Waiting for critical servers to stabilize..."
sleep 10

# Start workflow servers
echo "🔄 Starting workflow servers..."
# dope-context (formerly conport for this stack)
safe_up dope-context dopemux-mcp-dope-context

# ConPort dashboard & API
safe_up conport mcp-conport
# serena
safe_up serena dopemux-mcp-serena

echo "⏳ Waiting for workflow servers to stabilize..."
sleep 10

# Start plane coordinator unless explicitly disabled
if [ "${DOPEMUX_START_PLANE_COORDINATOR:-1}" = "1" ]; then
  safe_up plane-coordinator dopemux-mcp-plane-coordinator
else
  echo "• Skipping Plane Coordinator (set DOPEMUX_START_PLANE_COORDINATOR=1 to enable)"
fi

# Optional: Task Orchestrator (stdio MCP; disabled by default to avoid restart loops)
if [ "${DOPEMUX_START_TASK_ORCHESTRATOR:-0}" = "1" ]; then
  echo "🧭 Starting Task Orchestrator (manual profile)"
  # Requires compose profile; best-effort start
  if docker compose -f ./docker-compose.yml --profile manual up -d --no-build task-orchestrator 2>/dev/null; then
    echo "✅ Task Orchestrator up"
  else
    echo "ℹ️  Task Orchestrator not started (profile/manual)"
  fi
else
  echo "• Skipping Task Orchestrator (set DOPEMUX_START_TASK_ORCHESTRATOR=1 to enable)"
fi

# Start research + quality & utility servers
echo "🧠 Starting research + quality & utility servers..."
safe_up gptr-mcp dopemux-mcp-gptr-mcp
# Only start dopemux-gpt-researcher if exists
safe_up dopemux-gpt-researcher dopemux-gpt-researcher
safe_up exa dopemux-mcp-exa
safe_up desktop-commander dopemux-mcp-desktop-commander
if [ "${ENABLE_LEANTIME:-0}" = "1" ]; then
  safe_up leantime-bridge dopemux-mcp-leantime-bridge
else
  echo "• Skipping Leantime Bridge (set ENABLE_LEANTIME=1 to enable)"
fi

echo ""
echo "⏳ Final startup wait..."
sleep 5

# Only check Leantime health if explicitly enabled
if [ "${ENABLE_LEANTIME:-0}" = "1" ]; then
  if ! check_leantime_health; then
    echo "⚠️  Leantime did not pass health checks. Set LEANTIME_HEALTH_URL/LEANTIME_HEALTH_EXPECT to override." >&2
    echo "   Continuing with MCP servers anyway..."
  fi
else
  echo "ℹ️  Skipping Leantime health check (ENABLE_LEANTIME=0)"
fi

echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "🔁 Ensuring LiteLLM has latest config..."

ensure_litellm_config_applied() {
  local config="../../litellm.config.yaml"
  local cname="dopemux-mcp-litellm"
  if [ ! -f "$config" ]; then
    echo "ℹ️  Skipping: $config not found"
    return
  fi
  if ! docker inspect "$cname" >/dev/null 2>&1; then
    echo "ℹ️  Skipping: container $cname not found"
    return
  fi
  local started
  started=$(docker inspect -f '{{.State.StartedAt}}' "$cname" 2>/dev/null || true)
  if [ -z "$started" ]; then
    echo "ℹ️  Skipping: could not determine container start time"
    return
  fi

  local verdict
  verdict=$(python3 - "$config" "$started" <<'PY'
import os, sys, re, datetime
cfg = sys.argv[1]
started = sys.argv[2].strip()
ts_file = os.path.getmtime(cfg)
def parse_iso(s: str) -> float:
    # Normalize RFC3339 to Python ISO
    s = s.replace('Z', '+00:00')
    # Trim fractional seconds to microseconds (max 6 digits)
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)
    try:
        dt = datetime.datetime.fromisoformat(s)
        return dt.timestamp()
    except Exception:
        return 0.0
ts_started = parse_iso(started)
print('RELOAD' if ts_started and ts_file > ts_started else 'OK')
PY
  )

  if [ "$verdict" = "RELOAD" ]; then
    echo "🔄 Restarting $cname (config updated)"
    docker-compose restart litellm || docker restart "$cname" || true
  else
    echo "✅ LiteLLM config is up to date"
  fi
}

ensure_litellm_config_applied

echo ""
echo "🏥 Health check summary:"
echo "========================"

# Health check each critical server
servers=("pal:3003" "litellm:4000" "conport:3004" "serena:3006" "dope-context:3010" "plane-coordinator:8090")
for server in "${servers[@]}"; do
    name="${server%:*}"
    port="${server#*:}"

  if [ "$name" = "litellm" ]; then
    # LiteLLM requires auth header; use repo master key
    if curl -sf -H "Authorization: Bearer <REDACTED_LITELLM_MASTER_KEY>" "http://localhost:$port/health" &>/dev/null; then
      echo "✅ $name - Healthy"
    else
      echo "❌ $name - Unhealthy (port $port)"
    fi
  elif curl -sf "http://localhost:$port/health" &>/dev/null; then
    echo "✅ $name - Healthy"
  else
    echo "❌ $name - Unhealthy (port $port)"
  fi
done

echo ""
echo "🔎 Research servers:"
research_servers=("gptr-mcp:3009")
for server in "${research_servers[@]}"; do
    name="${server%:*}"
    port="${server#*:}"
    if curl -sf "http://localhost:$port/health" &>/dev/null; then
        echo "✅ $name - Healthy"
    else
        echo "❌ $name - Unhealthy (port $port)"
    fi
done

echo ""
echo "✅ All MCP servers started successfully!"
echo ""
echo "📋 Management commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop all:  docker-compose down"
echo "   Restart:   ./start-all-mcp-servers.sh"
echo ""
echo "🔍 Server endpoints:"
echo ""
echo "📚 Critical Path Servers:"
echo "   ConPort:      http://localhost:3004"
echo "   PAL (apilookup): http://localhost:3003"
echo "   LiteLLM:      http://localhost:4000"
echo ""
echo "🔄 Workflow Servers:"
echo "   Dope-Context: http://localhost:3010"
echo "   Serena:       http://localhost:3006"
echo "   Plane Coord:  http://localhost:8090"
echo ""
echo "🔧 Quality & Utility Servers:"
echo "   GPT Research: http://localhost:3009"
echo "   Exa:          http://localhost:3008"
echo "   Desktop Cmd:  http://localhost:3012"
echo ""
echo "📋 PM Integration:"
echo "   Leantime:     http://localhost:8080 (external)"
echo "   LT Bridge:    http://localhost:3015"
echo ""
echo "🎯 Ready for MCP operations!"
