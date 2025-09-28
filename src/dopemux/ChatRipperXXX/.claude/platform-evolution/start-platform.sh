#!/bin/bash

# Platform Evolution Startup Script
# Deploys the distributed Claude Code agent platform with Context7-first enforcement

set -e

echo "🚀 Starting Claude Code Platform Evolution..."

# Check dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required but not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is required but not installed"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        echo "⚠️  Creating .env template..."
        cat > .env << EOF
# MCP Server API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here

# Context7 Configuration
CONTEXT7_API_KEY=your_context7_key
CONTEXT7_ENDPOINT=https://api.context7.com

# Platform Configuration
PLATFORM_MODE=distributed
CONTEXT7_ENFORCER_ENABLED=true
MONITORING_ENABLED=true
TOKEN_BUDGET_LIMIT=25000

# Agent Cluster Configuration
RESEARCH_AGENTS_COUNT=2
IMPLEMENTATION_AGENTS_COUNT=3
QUALITY_AGENTS_COUNT=2
COORDINATION_AGENTS_COUNT=1
EOF
        echo "📝 Please configure .env with your API keys before proceeding"
        exit 1
    fi
    
    echo "✅ Dependencies check passed"
}

# Initialize Context7 integration
init_context7() {
    echo "🔧 Initializing Context7 integration..."
    
    # Validate Context7 availability
    python3 .claude/platform-evolution/context7-enforcer.py --validate
    
    if [ $? -ne 0 ]; then
        echo "❌ Context7 validation failed - platform cannot start without Context7"
        exit 1
    fi
    
    echo "✅ Context7 integration validated"
}

# Start monitoring dashboard
start_monitoring() {
    echo "📊 Starting monitoring dashboard..."
    
    # Start monitoring in background
    python3 .claude/platform-evolution/monitoring-dashboard.py &
    MONITOR_PID=$!
    echo $MONITOR_PID > .platform-evolution-monitor.pid
    
    echo "✅ Monitoring dashboard started (PID: $MONITOR_PID)"
    echo "📊 Dashboard available at http://localhost:8080"
}

# Deploy agent containers
deploy_agents() {
    echo "🐳 Deploying agent containers..."
    
    cd .claude/platform-evolution
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    # Wait for agents to be ready
    echo "⏳ Waiting for agents to initialize..."
    sleep 30
    
    # Verify agent health
    docker-compose ps
    
    echo "✅ Agent containers deployed"
}

# Setup architecture orchestrator
setup_orchestrator() {
    echo "🎼 Setting up architecture orchestrator..."
    
    # Initialize orchestrator
    python3 .claude/platform-evolution/architecture-orchestrator.py --init
    
    echo "✅ Architecture orchestrator ready"
}

# Create platform status file
create_status() {
    cat > .platform-evolution-status.json << EOF
{
    "platform_mode": "distributed",
    "context7_enforced": true,
    "monitoring_enabled": true,
    "agents_deployed": true,
    "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "dashboard_url": "http://localhost:8080",
    "architecture_orchestrator": "active"
}
EOF
    echo "📋 Platform status created"
}

# Main execution
main() {
    echo "=================="
    echo "Platform Evolution"
    echo "=================="
    
    check_dependencies
    init_context7
    start_monitoring
    deploy_agents
    setup_orchestrator
    create_status
    
    echo ""
    echo "🎉 Platform Evolution deployment complete!"
    echo ""
    echo "Next steps:"
    echo "1. Visit monitoring dashboard: http://localhost:8080"
    echo "2. Use 'claude' command with distributed agent support"
    echo "3. All code operations will enforce Context7 integration"
    echo ""
    echo "To stop the platform: ./stop-platform.sh"
}

# Run main function
main "$@"