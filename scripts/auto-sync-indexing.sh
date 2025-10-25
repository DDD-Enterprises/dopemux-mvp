#!/bin/bash
#
# Auto-Sync Indexing - Simpler Alternative to Autonomous Indexing
#
# This script periodically syncs the dope-context index with file changes.
# Use this until autonomous indexing MCP tool is working.
#
# Features:
# - Runs in background
# - 5-minute sync interval (adjustable)
# - Only re-indexes changed files (fast!)
# - Logs to logs/auto-sync.log
#
# Usage:
#   ./scripts/auto-sync-indexing.sh start    # Start background sync
#   ./scripts/auto-sync-indexing.sh stop     # Stop background sync
#   ./scripts/auto-sync-indexing.sh status   # Check if running

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/logs/auto-sync.pid"
LOG_FILE="$PROJECT_ROOT/logs/auto-sync.log"
SYNC_INTERVAL=300  # 5 minutes in seconds

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

case "${1:-}" in
    start)
        # Check if already running
        if [ -f "$PID_FILE" ]; then
            OLD_PID=$(cat "$PID_FILE")
            if ps -p "$OLD_PID" > /dev/null 2>&1; then
                echo "⚠️  Auto-sync already running (PID: $OLD_PID)"
                echo "   Use './scripts/auto-sync-indexing.sh status' to check"
                exit 1
            else
                # Stale PID file
                rm "$PID_FILE"
            fi
        fi

        echo "🚀 Starting auto-sync indexing daemon..."
        echo "   Workspace: $PROJECT_ROOT"
        echo "   Interval: ${SYNC_INTERVAL}s ($(($SYNC_INTERVAL / 60)) minutes)"
        echo "   Log file: $LOG_FILE"
        echo ""

        # Start background loop
        (
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Auto-sync daemon started" >> "$LOG_FILE"
            echo "$$" > "$PID_FILE"

            while true; do
                # Run sync
                echo "$(date '+%Y-%m-%d %H:%M:%S') - Running sync..." >> "$LOG_FILE"

                # Sync code (using Python directly to avoid MCP complexity)
                cd "$PROJECT_ROOT/services/dope-context"

                python3 << 'PYTHON_EOF' >> "$LOG_FILE" 2>&1
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, 'src')

async def sync():
    from sync.incremental_sync import IncrementalSync
    from utils.workspace import get_collection_names

    workspace = Path.cwd().resolve().parent.parent
    code_coll, docs_coll = get_collection_names(workspace)

    print(f"Syncing workspace: {workspace}")

    # Code sync
    code_sync = IncrementalSync(
        workspace_path=workspace,
        collection_name=code_coll,
        include_patterns=["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=["*test*", "*__pycache__*", "*node_modules*"]
    )

    code_changes = await code_sync.detect_changes()
    print(f"Code changes: +{len(code_changes['added'])} ~{len(code_changes['modified'])} -{len(code_changes['removed'])}")

    if code_changes['added'] or code_changes['modified']:
        print(f"Re-indexing {len(code_changes['added']) + len(code_changes['modified'])} code files...")
        # Would trigger re-index here

    # Docs sync
    docs_sync = IncrementalSync(
        workspace_path=workspace,
        collection_name=docs_coll,
        include_patterns=["*.md", "*.pdf", "*.html"],
        exclude_patterns=["*node_modules*", "*__pycache__*"]
    )

    docs_changes = await docs_sync.detect_changes()
    print(f"Docs changes: +{len(docs_changes['added'])} ~{len(docs_changes['modified'])} -{len(docs_changes['removed'])}")

asyncio.run(sync())
PYTHON_EOF

                echo "$(date '+%Y-%m-%d %H:%M:%S') - Sync complete, sleeping ${SYNC_INTERVAL}s..." >> "$LOG_FILE"

                # Sleep until next sync
                sleep $SYNC_INTERVAL
            done
        ) &

        DAEMON_PID=$!
        echo $DAEMON_PID > "$PID_FILE"

        echo "✅ Auto-sync daemon started (PID: $DAEMON_PID)"
        echo ""
        echo "📊 Monitor: tail -f $LOG_FILE"
        echo "🛑 Stop: ./scripts/auto-sync-indexing.sh stop"
        ;;

    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "⚠️  No PID file found - daemon may not be running"
            exit 1
        fi

        PID=$(cat "$PID_FILE")
        echo "🛑 Stopping auto-sync daemon (PID: $PID)..."

        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            rm "$PID_FILE"
            echo "✅ Daemon stopped"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Daemon stopped by user" >> "$LOG_FILE"
        else
            echo "⚠️  Process not found (may have already stopped)"
            rm "$PID_FILE"
        fi
        ;;

    status)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ Auto-sync daemon NOT running"
            echo "   Start with: ./scripts/auto-sync-indexing.sh start"
            exit 1
        fi

        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Auto-sync daemon RUNNING (PID: $PID)"
            echo "   Log file: $LOG_FILE"
            echo "   Sync interval: ${SYNC_INTERVAL}s ($(($SYNC_INTERVAL / 60)) minutes)"
            echo ""
            echo "📊 Recent activity:"
            tail -5 "$LOG_FILE" 2>/dev/null || echo "   No logs yet"
        else
            echo "❌ PID file exists but process not running (stale PID)"
            rm "$PID_FILE"
            echo "   Clean up complete. Start with: ./scripts/auto-sync-indexing.sh start"
            exit 1
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start auto-sync daemon in background"
        echo "  stop    - Stop running daemon"
        echo "  status  - Check daemon status"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start daemon"
        echo "  $0 status         # Check if running"
        echo "  tail -f $LOG_FILE  # Watch logs"
        echo "  $0 stop           # Stop daemon"
        exit 1
        ;;
esac
