#!/bin/bash
# MCP Proxy Setup and Management Script
# Quick setup and troubleshooting for Docker MCP servers with Claude Code

set -euo pipefail

# Configuration
PROXY_PORT=8080
PROXY_HOST="127.0.0.1"
CONFIG_FILE="mcp-proxy-config.json"
LOG_FILE="mcp-proxy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if mcp-proxy is installed
check_mcp_proxy() {
    if command -v mcp-proxy &> /dev/null; then
        log_success "mcp-proxy is installed"
        mcp-proxy --version
    else
        log_error "mcp-proxy not found. Installing..."
        uv tool install mcp-proxy
        log_success "mcp-proxy installed successfully"
    fi
}

# Check Docker containers
check_containers() {
    log_info "Checking Docker containers..."

    local containers=("mcp-mas-sequential-thinking" "mcp-claude-context" "mcp-exa" "mcp-zen" "mcp-serena")
    local running_containers=()

    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_success "Container ${container} is running"
            running_containers+=("$container")
        else
            log_warning "Container ${container} is not running"
        fi
    done

    if [ ${#running_containers[@]} -eq 0 ]; then
        log_error "No MCP containers are running"
        return 1
    fi

    return 0
}

# Test Docker exec commands
test_docker_exec() {
    log_info "Testing Docker exec commands..."

    # Test mas-sequential-thinking
    if docker ps --format '{{.Names}}' | grep -q "^mcp-mas-sequential-thinking$"; then
        log_info "Testing mcp-mas-sequential-thinking..."
        if timeout 5 docker exec mcp-mas-sequential-thinking which mcp-server-mas-sequential-thinking &>/dev/null; then
            log_success "mcp-server-mas-sequential-thinking executable found"
        else
            log_error "mcp-server-mas-sequential-thinking executable not found or not accessible"
        fi
    fi

    # Test context7
    if docker ps --format '{{.Names}}' | grep -q "^mcp-claude-context$"; then
        log_info "Testing mcp-claude-context..."
        if timeout 5 docker exec mcp-claude-context which node &>/dev/null; then
            log_success "Node.js found in mcp-claude-context"
        else
            log_error "Node.js not found in mcp-claude-context"
        fi
    fi
}

# Generate proxy configuration
generate_config() {
    log_info "Generating proxy configuration..."

    cat > "$CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "mas-sequential-thinking": {
      "command": "docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking"
    },
    "exa": {
      "command": "docker exec -i mcp-exa python server.py"
    },
    "zen": {
      "command": "docker exec -i mcp-zen python -m zen_mcp_server"
    },
    "serena": {
      "command": "docker exec -i mcp-serena python server.py"
    }
  }
}
EOF

    log_success "Configuration file created: $CONFIG_FILE"
}

# Start proxy server
start_proxy() {
    local mode="${1:-individual}"

    log_info "Starting MCP proxy server..."

    # Kill existing proxy if running
    if pgrep -f "mcp-proxy" > /dev/null; then
        log_warning "Stopping existing proxy..."
        pkill -f "mcp-proxy" || true
        sleep 2
    fi

    if [ "$mode" = "config" ]; then
        # Use configuration file
        log_info "Starting proxy with configuration file..."
        nohup mcp-proxy \
            --named-server-config "$CONFIG_FILE" \
            --port "$PROXY_PORT" \
            --allow-origin '*' \
            > "$LOG_FILE" 2>&1 &
    else
        # Use individual servers (more reliable)
        log_info "Starting proxy with individual server configuration..."
        nohup mcp-proxy \
            --named-server mas-sequential-thinking 'docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking' \
            --port "$PROXY_PORT" \
            --allow-origin '*' \
            > "$LOG_FILE" 2>&1 &
    fi

    local proxy_pid=$!
    echo $proxy_pid > mcp-proxy.pid

    # Wait for proxy to start
    sleep 3

    if pgrep -f "mcp-proxy" > /dev/null; then
        log_success "MCP proxy started successfully (PID: $proxy_pid)"
        log_info "Proxy running on http://${PROXY_HOST}:${PROXY_PORT}"
        log_info "Log file: $LOG_FILE"
    else
        log_error "Failed to start MCP proxy"
        cat "$LOG_FILE"
        return 1
    fi
}

# Test proxy endpoints
test_proxy() {
    log_info "Testing proxy endpoints..."

    local endpoints=(
        "mas-sequential-thinking"
        "exa"
        "zen"
        "serena"
    )

    for endpoint in "${endpoints[@]}"; do
        local url="http://${PROXY_HOST}:${PROXY_PORT}/servers/${endpoint}/sse"
        log_info "Testing $url"

        if curl -s --max-time 5 "$url" > /dev/null; then
            log_success "Endpoint $endpoint is accessible"
        else
            log_warning "Endpoint $endpoint is not accessible"
        fi
    done
}

# Configure Claude Code
configure_claude() {
    log_info "Configuring Claude Code..."

    # Remove old configurations
    claude mcp remove mas-sequential-thinking 2>/dev/null || true
    claude mcp remove context7 2>/dev/null || true
    claude mcp remove exa 2>/dev/null || true

    # Add proxy configurations
    log_info "Adding proxy servers to Claude Code..."

    claude mcp add -t sse mas-sequential-thinking-proxy "http://${PROXY_HOST}:${PROXY_PORT}/servers/mas-sequential-thinking/sse"
    log_success "Added mas-sequential-thinking-proxy"

    # Test if other servers are running before adding them
    if docker ps --format '{{.Names}}' | grep -q "^mcp-exa$"; then
        claude mcp add -t sse exa-proxy "http://${PROXY_HOST}:${PROXY_PORT}/servers/exa/sse"
        log_success "Added exa-proxy"
    fi

    if docker ps --format '{{.Names}}' | grep -q "^mcp-zen$"; then
        claude mcp add -t sse zen-proxy "http://${PROXY_HOST}:${PROXY_PORT}/servers/zen/sse"
        log_success "Added zen-proxy"
    fi

    if docker ps --format '{{.Names}}' | grep -q "^mcp-serena$"; then
        claude mcp add -t sse serena-proxy "http://${PROXY_HOST}:${PROXY_PORT}/servers/serena/sse"
        log_success "Added serena-proxy"
    fi
}

# Test Claude Code connections
test_claude() {
    log_info "Testing Claude Code connections..."
    claude mcp list
}

# Stop proxy
stop_proxy() {
    log_info "Stopping MCP proxy..."

    if [ -f mcp-proxy.pid ]; then
        local pid=$(cat mcp-proxy.pid)
        if kill "$pid" 2>/dev/null; then
            log_success "Proxy stopped (PID: $pid)"
        else
            log_warning "Failed to stop proxy with PID: $pid"
        fi
        rm -f mcp-proxy.pid
    fi

    # Fallback: kill by name
    if pgrep -f "mcp-proxy" > /dev/null; then
        pkill -f "mcp-proxy"
        log_success "Proxy processes killed"
    fi
}

# Show status
show_status() {
    log_info "MCP Proxy Status:"

    # Check proxy process
    if pgrep -f "mcp-proxy" > /dev/null; then
        log_success "Proxy is running"
        ps aux | grep mcp-proxy | grep -v grep
    else
        log_warning "Proxy is not running"
    fi

    # Check containers
    echo
    log_info "Docker containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep mcp || log_warning "No MCP containers running"

    # Check Claude Code configuration
    echo
    log_info "Claude Code MCP servers:"
    claude mcp list | grep -E "(proxy|Connected|Failed)" || true
}

# Show logs
show_logs() {
    local lines="${1:-50}"

    if [ -f "$LOG_FILE" ]; then
        log_info "Last $lines lines of proxy log:"
        tail -n "$lines" "$LOG_FILE"
    else
        log_warning "Log file not found: $LOG_FILE"
    fi
}

# Main function
main() {
    local command="${1:-help}"

    case "$command" in
        "install")
            check_mcp_proxy
            ;;
        "check")
            check_containers
            test_docker_exec
            ;;
        "config")
            generate_config
            ;;
        "start")
            local mode="${2:-individual}"
            check_containers || exit 1
            start_proxy "$mode"
            ;;
        "test")
            test_proxy
            ;;
        "claude")
            configure_claude
            ;;
        "setup")
            check_mcp_proxy
            check_containers || exit 1
            generate_config
            start_proxy individual
            sleep 5
            configure_claude
            test_claude
            ;;
        "stop")
            stop_proxy
            ;;
        "restart")
            stop_proxy
            sleep 2
            start_proxy individual
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-50}"
            ;;
        "help")
            cat << EOF
MCP Proxy Setup and Management Script

Usage: $0 <command> [options]

Commands:
  install     Install mcp-proxy
  check       Check Docker containers and commands
  config      Generate proxy configuration file
  start       Start proxy server [individual|config]
  test        Test proxy endpoints
  claude      Configure Claude Code with proxy servers
  setup       Full setup (install, check, start, configure)
  stop        Stop proxy server
  restart     Restart proxy server
  status      Show proxy and container status
  logs        Show proxy logs [number_of_lines]
  help        Show this help message

Examples:
  $0 setup                    # Complete setup
  $0 start individual         # Start with individual servers
  $0 start config            # Start with config file
  $0 logs 100                # Show last 100 log lines
  $0 status                  # Show current status

EOF
            ;;
        *)
            log_error "Unknown command: $command"
            main help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"