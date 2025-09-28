#!/bin/bash

# Platform Evolution Shutdown Script
# Gracefully stops the distributed Claude Code agent platform

set -e

echo "🛑 Stopping Claude Code Platform Evolution..."

# Stop monitoring dashboard
stop_monitoring() {
    echo "📊 Stopping monitoring dashboard..."
    
    if [ -f ".platform-evolution-monitor.pid" ]; then
        MONITOR_PID=$(cat .platform-evolution-monitor.pid)
        if kill -0 $MONITOR_PID 2>/dev/null; then
            kill $MONITOR_PID
            echo "✅ Monitoring dashboard stopped (PID: $MONITOR_PID)"
        fi
        rm -f .platform-evolution-monitor.pid
    else
        echo "⚠️  Monitoring PID file not found"
    fi
}

# Stop agent containers
stop_agents() {
    echo "🐳 Stopping agent containers..."
    
    cd .claude/platform-evolution
    
    # Stop and remove containers
    docker-compose down
    
    echo "✅ Agent containers stopped"
}

# Clean up status files
cleanup_status() {
    echo "🧹 Cleaning up status files..."
    
    rm -f .platform-evolution-status.json
    rm -f .platform-evolution-monitor.pid
    
    echo "✅ Status files cleaned"
}

# Main execution
main() {
    echo "=================="
    echo "Platform Shutdown"
    echo "=================="
    
    stop_monitoring
    stop_agents
    cleanup_status
    
    echo ""
    echo "🎉 Platform Evolution shutdown complete!"
    echo ""
    echo "To restart the platform: ./start-platform.sh"
}

# Run main function
main "$@"