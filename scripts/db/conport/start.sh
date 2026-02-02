#!/bin/bash
# ConPort Local Service Startup Script
# ADHD-optimized session memory management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONPORT_DIR="$PROJECT_ROOT/services/conport"
WORKSPACE_ID="$PROJECT_ROOT"

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

# Function to check if ConPort is already running
check_running() {
    if pgrep -f "conport-mcp" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to find available port
find_available_port() {
    local port=3004
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        ((port++))
        if [ $port -gt 3010 ]; then
            log_error "No available ports found between 3004-3010"
            exit 1
        fi
    done
    echo $port
}

# Main startup function
start_conport() {
    log_info "🚀 Starting ConPort MCP server..."

    # Check if already running
    if check_running; then
        log_warn "ConPort is already running!"
        return 0
    fi

    # Ensure we're in the ConPort directory
    cd "$CONPORT_DIR"

    # Activate virtual environment
    if [ ! -f "venv/bin/activate" ]; then
        log_error "Virtual environment not found! Run installation first."
        exit 1
    fi

    source venv/bin/activate

    # Find available port
    PORT=$(find_available_port)
    log_info "Using port: $PORT"

    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/.conport/logs"

    # Configure data paths to use existing data
    LOG_FILE="$PROJECT_ROOT/.conport/logs/conport.log"
    DB_PATH="$PROJECT_ROOT/context_portal/context.db"

    log_info "📂 Workspace: $WORKSPACE_ID"
    log_info "📝 Log file: $LOG_FILE"
    log_info "🗄️  Database: $DB_PATH"

    # Start ConPort in background with nohup
    nohup conport-mcp \
        --mode http \
        --host 127.0.0.1 \
        --port "$PORT" \
        --workspace_id "$WORKSPACE_ID" \
        --log-file "$LOG_FILE" \
        --db-path "$DB_PATH" \
        --log-level INFO \
        > "$PROJECT_ROOT/.conport/logs/startup.log" 2>&1 &

    local pid=$!
    echo $pid > "$PROJECT_ROOT/.conport/conport.pid"

    # Wait a moment and check if it started successfully
    sleep 2

    if check_running; then
        log_info "✅ ConPort started successfully!"
        log_info "🌐 Server: http://127.0.0.1:$PORT"
        log_info "🆔 PID: $pid"
        log_info "📋 For ADHD session continuity, ConPort will preserve:"
        log_info "   • Active context and decisions"
        log_info "   • Progress tracking and milestones"
        log_info "   • Project knowledge graph"

        # Store the port for other scripts
        echo $PORT > "$PROJECT_ROOT/.conport/port"

        return 0
    else
        log_error "❌ Failed to start ConPort! Check logs:"
        log_error "   Startup: $PROJECT_ROOT/.conport/logs/startup.log"
        log_error "   Service: $LOG_FILE"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            CUSTOM_PORT="$2"
            shift 2
            ;;
        --workspace)
            WORKSPACE_ID="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--port PORT] [--workspace WORKSPACE_ID]"
            echo ""
            echo "Start ConPort MCP server for ADHD session memory"
            echo ""
            echo "Options:"
            echo "  --port PORT          Custom port (default: auto-detect 3004+)"
            echo "  --workspace ID       Custom workspace ID (default: project root)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Override port if specified
if [ -n "$CUSTOM_PORT" ]; then
    find_available_port() {
        echo $CUSTOM_PORT
    }
fi

# Start the service
start_conport