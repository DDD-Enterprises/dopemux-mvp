#!/bin/bash
# Test script for Serena v2 MCP tools
# Run this after restarting Claude Code to verify all 20 tools are available

echo "🔍 Testing Serena v2 MCP Tools"
echo "================================"
echo ""

# Test 1: Health check
echo "1️⃣  Health Check (get_workspace_status)"
echo "   Tests: Workspace detection, component status"
echo ""

# Test 2: Navigation Tier 1
echo "2️⃣  Navigation Tier 1 (4 tools)"
echo "   • find_symbol - Search for functions/classes by name"
echo "   • goto_definition - Jump from usage to definition"
echo "   • get_context - Get code with complexity scoring"
echo "   • find_references - Find all usages of a symbol"
echo ""

# Test 3: ADHD Intelligence Tier 2
echo "3️⃣  ADHD Intelligence Tier 2 (4 tools)"
echo "   • analyze_complexity - Get complexity score for code"
echo "   • filter_by_focus - Filter results by focus mode"
echo "   • suggest_next_step - Get navigation suggestions"
echo "   • get_reading_order - Optimal order for reading code"
echo ""

# Test 4: Advanced Tier 3
echo "4️⃣  Advanced Tier 3 (3 tools)"
echo "   • find_relationships - Find code relationships"
echo "   • get_navigation_patterns - Common navigation patterns"
echo "   • update_focus_mode - Switch focus modes (focused/scattered/transitioning)"
echo ""

# Test 5: Untracked Work Detection (Feature 1)
echo "5️⃣  Untracked Work Detection (6 tools)"
echo "   • detect_untracked_work - Find uncommitted work"
echo "   • track_untracked_work - Start tracking work"
echo "   • snooze_untracked_work - Snooze reminder"
echo "   • ignore_untracked_work - Ignore permanently"
echo "   • get_untracked_work_config - View settings"
echo "   • update_untracked_work_config - Update settings"
echo ""

# Test 6: File operations
echo "6️⃣  File Operations (2 tools)"
echo "   • read_file - Read file with ADHD optimizations"
echo "   • list_dir - List directory contents"
echo ""

echo "================================"
echo "Total: 20 tools available"
echo ""
echo "💡 Test Commands (copy-paste these into Claude Code):"
echo ""
echo "# Test health check"
echo "Use serena-v2 get_workspace_status tool"
echo ""
echo "# Test find_symbol"
echo "Find all 'SerenaV2MCPServer' symbols in the codebase"
echo ""
echo "# Test complexity analysis"
echo "Analyze complexity of services/serena/v2/mcp_server.py at line 350"
echo ""
echo "# Test untracked work detection"
echo "Detect any uncommitted work in the repository"
echo ""
echo "# Test file reading with ADHD optimizations"
echo "Read services/serena/v2/mcp_server.py with complexity annotations"
echo ""
