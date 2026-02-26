#!/bin/bash
# Dopemux Setup Script - Complete Installation and Startup

set -e  # Exit on any error

echo "🚀 Dopemux Setup Script"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prereq() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed. Please install Docker first."
        exit 1
    fi
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
check_prereq

# Step 2: Start Docker services
echo "Step 2: Starting Docker services..."
docker-compose -f docker-compose.master.yml up -d || {
    log_error "Failed to start Docker services. Trying unified compose..."
    docker-compose -f compose.yml up -d
}

# Wait for services to start
echo "Step 3: Waiting for services to start..."
sleep 30

# Step 3: Initialize ConPort
echo "Step 4: Initializing ConPort..."
mcp__conport__get_active_context --workspace_id "$(pwd)" || {
    log_warn "ConPort initialization warning - continuing anyway"
}

# Step 4: Start ADHD Engine (if not running)
echo "Step 5: Starting ADHD Engine..."
if ! curl -f http://localhost:8095/health > /dev/null 2>&1; then
    cd services/adhd_engine/services/adhd_engine
    ADHD_ENGINE_API_KEY=test-key-123 ALLOWED_ORIGINS=http://localhost:3000 nohup python -m uvicorn main:app --host 0.0.0.0 --port 8095 > /dev/null 2>&1 &
    cd - >/dev/null
    sleep 5
else
    log_info "ADHD Engine already running"
fi

# Step 5: Index Dope-Context (if needed)
echo "Step 6: Indexing Dope-Context..."
mcp__dope-context__index_workspace --workspace_path "$(pwd)" || {
    log_warn "Dope-Context indexing warning - continuing anyway"
}

# Step 6: Start Claude Code Router (if needed)
echo "Step 7: Starting Claude Code Router..."
if ! command -v claude-code-router &> /dev/null; then
    log_error "Claude Code Router not found. Please install with ./scripts/install_claude_code_router.sh"
    exit 1
fi

# Step 7: Create session focus
echo "Step 8: Setting initial session focus..."
mcp__conport__update_active_context \
    --workspace_id "$(pwd)" \
    --patch_content "{
        \"current_focus\": \"Dopemux setup complete\",
        \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
    }"

echo "✅ Dopemux setup complete!"
echo ""
echo "Next steps:"
echo "1. Run 'dopemux start' to launch your development session"
echo "2. Check status with 'dopemux status'"
echo "3. Your statusline should show: dopemux-mvp main | 📊 Dopemux setup complete [0m] | ..."

echo ""
echo "If you encounter issues, run: dopemux doctor"
