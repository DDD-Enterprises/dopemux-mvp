#!/bin/bash
# Statusline Debug Script
# Tests each component of the statusline to identify failures

echo "=== Dopemux Statusline Diagnostic ==="
echo ""

# 1. Check workspace
WORKSPACE="/Users/hue/code/dopemux-mvp"
echo "1. Workspace: $WORKSPACE"
if [ -d "$WORKSPACE" ]; then
    echo "   ✅ Directory exists"
else
    echo "   ❌ Directory not found"
fi
echo ""

# 2. Check ConPort database
CONPORT_DB="$WORKSPACE/context_portal/context.db"
echo "2. ConPort Database: $CONPORT_DB"
if [ -f "$CONPORT_DB" ]; then
    echo "   ✅ Database file exists"

    # Test query
    if command -v sqlite3 >/dev/null 2>&1; then
        echo "   ✅ sqlite3 available"

        result=$(sqlite3 "$CONPORT_DB" "SELECT content FROM active_context LIMIT 1" 2>&1)
        if [ $? -eq 0 ]; then
            echo "   ✅ Query successful"

            # Extract current_focus
            focus=$(echo "$result" | jq -r '.current_focus // "ERROR"' 2>/dev/null)
            if [ -n "$focus" ] && [ "$focus" != "ERROR" ]; then
                echo "   ✅ Focus extracted: ${focus:0:50}..."
            else
                echo "   ⚠️  Focus extraction failed"
                echo "   Raw result: ${result:0:100}..."
            fi
        else
            echo "   ❌ Query failed: $result"
        fi
    else
        echo "   ❌ sqlite3 not installed"
    fi
else
    echo "   ❌ Database file not found"
fi
echo ""

# 3. Check ConPort container
echo "3. ConPort Container"
container_status=$(docker ps --filter "name=conport" --format "{{.Status}}" 2>/dev/null)
if [ -n "$container_status" ]; then
    echo "   ✅ Container running: $container_status"
else
    echo "   ❌ Container not found"
fi
echo ""

# 4. Check Serena v2
echo "4. Serena v2 Container"
serena_status=$(docker ps --filter "name=serena" --format "{{.Status}}" 2>/dev/null)
if [ -n "$serena_status" ]; then
    echo "   ✅ Container running: $serena_status"
else
    echo "   ❌ Container not found"
fi
echo ""

# 5. Check dope-context (Qdrant)
echo "5. dope-context (Qdrant)"
qdrant_status=$(docker ps --filter "name=qdrant" --format "{{.Status}}" 2>/dev/null)
if [ -n "$qdrant_status" ]; then
    echo "   ✅ Container running: $qdrant_status"

    # Test HTTP endpoint
    if curl -s http://localhost:6333/healthz >/dev/null 2>&1; then
        echo "   ✅ HTTP health check passed"
    else
        echo "   ⚠️  HTTP health check failed"
    fi
else
    echo "   ❌ Container not found"
fi
echo ""

# 6. Check ADHD Engine
echo "6. ADHD Engine"
if curl -s http://localhost:8095/health >/dev/null 2>&1; then
    echo "   ✅ ADHD Engine responding"
else
    echo "   ❌ ADHD Engine not responding"
fi
echo ""

# 7. Test actual statusline script
echo "7. Statusline Script Test"
STATUSLINE_SCRIPT="$WORKSPACE/.claude/statusline.sh"
if [ -f "$STATUSLINE_SCRIPT" ]; then
    echo "   ✅ Script exists: $STATUSLINE_SCRIPT"

    # Create mock input for testing
    mock_input='{
      "workspace": {"current_dir": "/Users/hue/code/dopemux-mvp"},
      "model": {"display_name": "Sonnet 4.5", "id": "claude-sonnet-4-5"},
      "context": {"used": 110000, "total": 200000},
      "transcript_path": "/tmp/fake-transcript.jsonl"
    }'

    echo "   Testing with mock input..."
    output=$(echo "$mock_input" | bash "$STATUSLINE_SCRIPT" 2>&1)

    if [ $? -eq 0 ]; then
        echo "   ✅ Script executed successfully"
        echo "   Output: $output"
    else
        echo "   ❌ Script execution failed"
        echo "   Error: $output"
    fi
else
    echo "   ❌ Script not found"
fi
echo ""

# 8. Summary
echo "=== Summary ==="
echo "Run this script to diagnose statusline issues."
echo "If all checks pass but statusline shows ⚠️, check Claude Code configuration."
echo ""
echo "To configure statusline in Claude Code:"
echo "1. Open Claude Code settings"
echo "2. Add to config:"
echo '   "statusline": {'
echo '     "command": "bash /Users/hue/code/dopemux-mvp/.claude/statusline.sh"'
echo '   }'
echo ""
