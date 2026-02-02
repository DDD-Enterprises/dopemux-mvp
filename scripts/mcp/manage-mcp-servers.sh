#!/bin/bash

# === Dopemux MCP Servers Management Script ===
# Unified management interface for all MCP servers (NPM and Docker)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_MCP_DIR="$PROJECT_ROOT/docker/mcp-servers"
CONFIG_FILE="$DOCKER_MCP_DIR/mcp-config.yaml"

# Function to show usage
show_usage() {
    echo "Dopemux MCP Servers Management"
    echo "============================="
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  install           Install all MCP servers (NPM + Docker)"
    echo "  start             Start all MCP servers"
    echo "  stop              Stop all MCP servers"
    echo "  restart           Restart all MCP servers"
    echo "  status            Show status of all MCP servers"
    echo "  logs [server]     View logs (all servers or specific server)"
    echo "  config            Show current configuration"
    echo "  health            Check health of all services"
    echo "  update            Update all MCP servers"
    echo "  clean             Clean up unused containers and volumes"
    echo ""
    echo "Docker-specific commands:"
    echo "  build             Rebuild all Docker containers"
    echo "  shell <server>    Open shell in container"
    echo ""
    echo "Examples:"
    echo "  $0 install               # Install all MCP servers"
    echo "  $0 start                 # Start all servers"
    echo "  $0 logs mas-sequential   # View logs for specific server"
    echo "  $0 status                # Check status"
    echo ""
}

# Function to check if Docker is available and running
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "❌ Docker not found. Please install Docker first."
        return 1
    fi

    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker daemon not running. Please start Docker first."
        return 1
    fi

    return 0
}

# Function to install all MCP servers
install_servers() {
    echo "🚀 Installing all Dopemux MCP servers..."
    echo ""

    # Install NPM-based servers
    if [[ -f "$SCRIPT_DIR/install-mcp-servers.sh" ]]; then
        echo "📦 Installing NPM-based MCP servers..."
        bash "$SCRIPT_DIR/install-mcp-servers.sh"
    else
        echo "⚠️ NPM installer not found, skipping NPM servers"
    fi

    echo ""
    echo "✅ Installation complete!"
}

# Function to start all MCP servers
start_servers() {
    echo "🚀 Starting all MCP servers..."

    # Start Docker-based servers
    if check_docker && [[ -d "$DOCKER_MCP_DIR" ]]; then
        echo "🐳 Starting Docker MCP servers..."
        cd "$DOCKER_MCP_DIR"
        if [[ -f "start-all-mcp-servers.sh" ]]; then
            ./start-all-mcp-servers.sh
        else
            docker-compose up -d
        fi
    else
        echo "⚠️ Docker MCP servers not available"
    fi

    echo ""
    echo "✅ All available MCP servers started!"
}

# Function to stop all MCP servers
stop_servers() {
    echo "🛑 Stopping all MCP servers..."

    # Stop Docker-based servers
    if check_docker && [[ -d "$DOCKER_MCP_DIR" ]]; then
        echo "🐳 Stopping Docker MCP servers..."
        cd "$DOCKER_MCP_DIR"
        if [[ -f "stop-all-mcp-servers.sh" ]]; then
            ./stop-all-mcp-servers.sh
        else
            docker-compose down
        fi
    fi

    echo "✅ All MCP servers stopped!"
}

# Function to show status
show_status() {
    echo "📊 MCP Servers Status"
    echo "===================="
    echo ""

    # Docker servers status
    if check_docker && [[ -d "$DOCKER_MCP_DIR" ]]; then
        echo "🐳 Docker MCP Servers:"
        cd "$DOCKER_MCP_DIR"
        if docker-compose ps 2>/dev/null | grep -q "Up"; then
            docker-compose ps
        else
            echo "   No Docker MCP servers running"
        fi
    else
        echo "🐳 Docker MCP Servers: Not available"
    fi

    echo ""

    # NPM servers status (basic check)
    echo "📦 NPM MCP Servers:"
    if command -v context7-mcp >/dev/null 2>&1; then
        echo "   ✅ context7-mcp: Available"
    else
        echo "   ❌ context7-mcp: Not found"
    fi

    if npm list -g exa-mcp >/dev/null 2>&1; then
        echo "   ✅ exa-mcp: Available"
    else
        echo "   ❌ exa-mcp: Not found"
    fi
}

# Function to view logs
view_logs() {
    local server_name="$1"

    if [[ -n "$server_name" ]]; then
        echo "📋 Viewing logs for $server_name..."
        cd "$DOCKER_MCP_DIR"
        docker-compose logs -f "$server_name"
    else
        echo "📋 Viewing logs for all MCP servers..."
        cd "$DOCKER_MCP_DIR"
        docker-compose logs -f
    fi
}

# Function to show configuration
show_config() {
    echo "⚙️ MCP Servers Configuration"
    echo "============================"
    echo ""

    if [[ -f "$CONFIG_FILE" ]]; then
        echo "📄 Configuration file: $CONFIG_FILE"
        echo ""
        cat "$CONFIG_FILE"
    else
        echo "❌ Configuration file not found: $CONFIG_FILE"
    fi
}

# Function to check health
check_health() {
    echo "🏥 Health Check"
    echo "==============="
    echo ""

    # Check Docker servers health
    if check_docker && [[ -d "$DOCKER_MCP_DIR" ]]; then
        cd "$DOCKER_MCP_DIR"
        echo "🐳 Docker MCP Servers Health:"

        # Check if containers are running
        if docker-compose ps | grep -q "Up"; then
            echo "✅ Containers are running"

            # Check individual service health
            for service in $(docker-compose config --services); do
                if docker-compose ps "$service" | grep -q "healthy\|Up"; then
                    echo "   ✅ $service: Healthy"
                else
                    echo "   ❌ $service: Unhealthy"
                fi
            done
        else
            echo "❌ No containers running"
        fi
    fi

    echo ""

    # Check environment variables
    echo "🔐 Environment Variables:"
    for var in DEEPSEEK_API_KEY OPENAI_API_KEY GITHUB_TOKEN EXA_API_KEY; do
        if [[ -n "${!var}" ]]; then
            echo "   ✅ $var: Set"
        else
            echo "   ⚠️ $var: Not set"
        fi
    done
}

# Function to update servers
update_servers() {
    echo "🔄 Updating MCP servers..."

    # Update Docker servers
    if check_docker && [[ -d "$DOCKER_MCP_DIR" ]]; then
        echo "🐳 Updating Docker MCP servers..."
        cd "$DOCKER_MCP_DIR"

        # Pull latest images and rebuild
        docker-compose pull
        docker-compose up -d --build

        echo "✅ Docker servers updated"
    fi

    # Update NPM servers
    echo "📦 Updating NPM MCP servers..."
    npm update -g context7-mcp exa-mcp morphllm-fast-apply-mcp 2>/dev/null || echo "⚠️ Some NPM updates may have failed"

    echo "✅ Update complete!"
}

# Function to clean up
clean_up() {
    echo "🧹 Cleaning up MCP servers..."

    if check_docker; then
        echo "🐳 Cleaning Docker resources..."
        docker system prune -f
        docker volume prune -f

        echo "✅ Cleanup complete"
    fi
}

# Function to open shell in container
open_shell() {
    local server_name="$1"

    if [[ -z "$server_name" ]]; then
        echo "❌ Please specify a server name"
        echo "Available servers:"
        cd "$DOCKER_MCP_DIR"
        docker-compose config --services
        return 1
    fi

    echo "🐚 Opening shell in $server_name..."
    cd "$DOCKER_MCP_DIR"
    docker-compose exec "$server_name" /bin/sh
}

# Main command handling
case "${1:-}" in
    "install")
        install_servers
        ;;
    "start")
        start_servers
        ;;
    "stop")
        stop_servers
        ;;
    "restart")
        stop_servers
        sleep 2
        start_servers
        ;;
    "status")
        show_status
        ;;
    "logs")
        view_logs "$2"
        ;;
    "config")
        show_config
        ;;
    "health")
        check_health
        ;;
    "update")
        update_servers
        ;;
    "clean")
        clean_up
        ;;
    "build")
        if check_docker && [[ -d "$DOCKER_MCP_DIR" ]]; then
            cd "$DOCKER_MCP_DIR"
            docker-compose build --no-cache
        fi
        ;;
    "shell")
        open_shell "$2"
        ;;
    "help"|"-h"|"--help"|"")
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac