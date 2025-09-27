#!/bin/bash
# ConPort Service Restart Script
# Stop and start ConPort MCP server with validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[ConPort]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[ConPort]${NC} $1"
}

log_error() {
    echo -e "${RED}[ConPort]${NC} $1"
}

# Function to restart ConPort
restart_conport() {
    log_info "🔄 Restarting ConPort MCP server..."

    # Check current status
    local current_status=$("$SCRIPT_DIR/status.sh" --quick 2>/dev/null || echo "unknown")
    if [[ "$current_status" == "healthy:"* ]]; then
        local port=${current_status#healthy:}
        log_info "Currently running healthy on port $port"
    elif [[ "$current_status" == "unhealthy:"* ]]; then
        local port=${current_status#unhealthy:}
        log_warn "Currently running but unhealthy on port $port"
    elif [[ "$current_status" == "running:"* ]]; then
        log_warn "Currently running but status unclear"
    else
        log_info "Currently stopped"
    fi

    # Stop the service
    log_info "📴 Stopping ConPort..."
    if "$SCRIPT_DIR/stop.sh"; then
        log_info "✅ Stop completed"
    else
        log_error "⚠️  Stop had issues, continuing with restart..."
    fi

    # Brief pause to ensure clean shutdown
    sleep 2

    # Start the service
    log_info "🚀 Starting ConPort..."
    if "$SCRIPT_DIR/start.sh" "$@"; then
        log_info "✅ Start completed"

        # Wait a moment for startup
        sleep 3

        # Verify it's running properly
        local new_status=$("$SCRIPT_DIR/status.sh" --quick 2>/dev/null || echo "unknown")
        if [[ "$new_status" == "healthy:"* ]]; then
            local new_port=${new_status#healthy:}
            log_info "🎉 Restart successful! ConPort is healthy on port $new_port"
            log_info "💭 ADHD session memory is ready for continuous context preservation"
            return 0
        else
            log_error "❌ Restart completed but service is not healthy"
            log_error "Status: $new_status"
            log_error "Check logs with: scripts/conport/status.sh"
            return 1
        fi
    else
        log_error "❌ Start failed during restart"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 [start.sh options...]"
            echo ""
            echo "Restart ConPort MCP server with validation"
            echo ""
            echo "This script will:"
            echo "  1. Stop the current service gracefully"
            echo "  2. Wait for clean shutdown"
            echo "  3. Start the service with provided options"
            echo "  4. Validate the service is healthy"
            echo ""
            echo "Any additional arguments are passed to start.sh"
            echo "See 'scripts/conport/start.sh --help' for start options"
            exit 0
            ;;
        *)
            # Pass through all other arguments to start.sh
            break
            ;;
    esac
done

# Restart with any additional arguments passed to start.sh
restart_conport "$@"