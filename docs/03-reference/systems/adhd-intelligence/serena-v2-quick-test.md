---
id: SERENA_V2_QUICK_TEST
title: Serena_V2_Quick_Test
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Serena_V2_Quick_Test (reference) for dopemux documentation and developer
  workflows.
---
# Serena v2 Quick Test Guide

After restarting Claude Code, Serena v2 will be available via stdio transport with 20 tools.

## ✅ Configuration Applied

**File**: `~/.claude.json`

```json
"serena-v2": {
  "type": "stdio",
  "command": "python3",
  "args": [
    "/Users/hue/code/dopemux-mvp/services/serena/v2/mcp_server.py"
  ],
  "env": {}
}
```

## 🧪 Quick Tests

### 1. Health Check
```
Use serena-v2 get_workspace_status
```
**Expected**: Workspace path, component status, lazy loading info

### 2. Symbol Search (Navigation Tier 1)
```
Use serena-v2 find_symbol to search for "SerenaV2MCPServer"
```
**Expected**: Max 10 results with file locations, line numbers, complexity scores

### 3. Go to Definition (Navigation Tier 1)
```
Use serena-v2 goto_definition for services/serena/v2/mcp_server.py line 350 column 15
```
**Expected**: Definition location with 7-line context (3 before, definition, 3 after)

### 4. Code Context with Complexity (Navigation Tier 1)
```
Use serena-v2 get_context for services/serena/v2/mcp_server.py line 350 with 10 context lines
```
**Expected**: 21 lines (10 before, center line, 10 after) with complexity annotation

### 5. Find References (Navigation Tier 1)
```
Use serena-v2 find_references for services/serena/v2/mcp_server.py line 314 column 10
```
**Expected**: All usage locations with 3-line context snippets

### 6. Complexity Analysis (ADHD Tier 2)
```
Use serena-v2 analyze_complexity for services/serena/v2/mcp_server.py line 350
```
**Expected**: Complexity score 0.0-1.0 with breakdown (nesting, control flow, etc.)

### 7. Focus Mode Filtering (ADHD Tier 2)
```
Use serena-v2 filter_by_focus on search results
```
**Expected**: Results filtered by current focus mode (focused/scattered/transitioning)

### 8. Next Step Suggestions (ADHD Tier 2)
```
Use serena-v2 suggest_next_step after viewing a file
```
**Expected**: Suggested next navigation steps based on context

### 9. Reading Order (ADHD Tier 2)
```
Use serena-v2 get_reading_order for a list of files
```
**Expected**: Optimal reading sequence based on complexity and dependencies

### 10. Untracked Work Detection (Feature 1)
```
Use serena-v2 detect_untracked_work
```
**Expected**: List of uncommitted changes, stashed work, untracked files

### 11. File Reading (Basic)
```
Use serena-v2 read_file for services/serena/v2/mcp_server.py
```
**Expected**: File contents with ADHD optimizations (max line length handling)

### 12. Directory Listing (Basic)
```
Use serena-v2 list_dir for services/serena/v2
```
**Expected**: Directory contents with file/directory indicators

## 📊 All 20 Tools

| Category | Count | Tools |
|----------|-------|-------|
| **Health** | 1 | get_workspace_status |
| **Navigation Tier 1** | 4 | find_symbol, goto_definition, get_context, find_references |
| **ADHD Intelligence Tier 2** | 4 | analyze_complexity, filter_by_focus, suggest_next_step, get_reading_order |
| **Advanced Tier 3** | 3 | find_relationships, get_navigation_patterns, update_focus_mode |
| **Untracked Work (Feature 1)** | 6 | detect_untracked_work, track_untracked_work, snooze_untracked_work, ignore_untracked_work, get_untracked_work_config, update_untracked_work_config |
| **Files** | 2 | read_file, list_dir |
| **TOTAL** | **20** | |

## 🎯 ADHD Features

- **Max 10 Results**: Prevents overwhelming result sets
- **Complexity Scoring**: 0.0-1.0 scale for cognitive load assessment
- **Progressive Disclosure**: Essential info first, details on request
- **Focus Modes**: focused (full nav), scattered (essentials only), transitioning (cached results)
- **Lazy Loading**: Fast startup (<100ms), components load on first use

## 🚀 Performance Targets

- **Workspace Detection**: < 50ms (actual: ~0ms)
- **Symbol Lookup**: < 50ms (LSP)
- **Navigation**: < 200ms (with caching)
- **Startup**: < 100ms (lazy loading)

## 🔧 Troubleshooting

**If tools don't appear after restart:**
1. Check MCP server list: `/mcp`
1. Look for serena-v2 in the list
1. Check if it's enabled (not disabled)
1. View logs for startup errors

**If LSP tools fail:**
- Install pylsp: `pip install python-lsp-server[all]`
- Workspace must have .git directory
- Python files must exist in workspace

**If database tools fail:**
- Graceful degradation: Tools return simplified results
- Full database functionality planned for Phase 3

## 📝 Next Steps

After verifying tools work:
1. Test complex navigation workflows
1. Try ADHD focus mode switching
1. Test untracked work detection
1. Benchmark performance against targets
1. Report any issues to ConPort via log_decision

---

**Status**: ✅ Configured (restart Claude Code to activate)
**Transport**: stdio (local Python process)
**Location**: `/Users/hue/code/dopemux-mvp/services/serena/v2/mcp_server.py`
rt Claude Code to activate)
**Transport**: stdio (local Python process)
**Location**: `/Users/hue/code/dopemux-mvp/services/serena/v2/mcp_server.py`
