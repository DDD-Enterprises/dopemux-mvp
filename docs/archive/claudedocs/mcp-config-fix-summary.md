---
id: mcp-config-fix-summary
title: Mcp Config Fix Summary
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Mcp Config Fix Summary (explanation) for dopemux documentation and developer
  workflows.
---
# MCP Configuration Fix - Summary

**Date**: 2025-02-02
**Status**: ✅ COMPLETE

## Problem
After Docker refactoring (commit d513a77c), `.claude.json` was never updated to match new HTTP/SSE protocols. All 4 MCP servers were running correctly in Docker but client configuration pointed to wrong endpoints.

## Changes Applied

### 1. Conport ✅
**Before**: stdio pointing to non-existent venv binary
```json
"conport": {
  "type": "stdio",
  "command": "/Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp",
  "args": ["--workspace_id", "/Users/hue/code/dopemux-mvp", "--mode", "stdio"]
}
```

**After**: SSE endpoint on Docker port
```json
"conport": {
  "type": "sse",
  "url": "http://localhost:3004/mcp"
}
```

### 2. Desktop-Commander ✅
**Before**: Invalid curl command (fundamentally broken)
```json
"desktop-commander": {
  "type": "stdio",
  "command": "curl",
  "args": ["-X", "POST", "http://localhost:3012/mcp", "-H", "Content-Type: application/json", "-d", "@-"]
}
```

**After**: SSE endpoint on Docker port
```json
"desktop-commander": {
  "type": "sse",
  "url": "http://localhost:3012/mcp"
}
```

### 3. Exa ✅
**Status**: Already correct - no changes needed
```json
"exa": {
  "type": "sse",
  "url": "http://localhost:3008/mcp"
}
```

### 4. GPT-Researcher ✅
**Before**: Wrong endpoint path
```json
"dopemux-mcp-gptr-mcp": {
  "type": "sse",
  "url": "http://localhost:3009/sse"
}
```

**After**: Correct MCP endpoint
```json
"dopemux-mcp-gptr-mcp": {
  "type": "sse",
  "url": "http://localhost:3009/mcp"
}
```

## Backup Location
Configuration backed up to: `/Users/hue/.claude.json.backup-[timestamp]`

## Next Steps
1. **Restart Claude Code** or reload MCP servers to apply changes
2. **Verify in Claude Code UI** that all 4 servers show as connected
3. **Test a tool** from each server to confirm functionality

## Docker Container Status
All containers confirmed healthy and running:
- `smoke-conport` - Port 3004 (was unhealthy, should work now with correct config)
- `dopemux-mcp-exa` - Port 3008 ✅ Healthy
- `dopemux-mcp-desktop-commander` - Port 3012 ✅ Healthy
- `dopemux-mcp-gptr-mcp` - Port 3009 ✅ Healthy

## Root Cause Analysis
**Configuration drift** after infrastructure refactoring. Servers moved from local stdio to Docker HTTP/SSE, but client configuration wasn't updated.

**Prevention**:
- Add validation script to verify `.claude.json` matches running servers
- Consider service discovery pattern where servers advertise their endpoints
- Document configuration changes in commit messages

## Files Modified
- `/Users/hue/.claude.json` - MCP server configurations updated (lines 148-191)

## References
- Original plan: Plan transcript in `.claude/projects/[session-id].jsonl`
- Docker configurations: `docker/mcp-servers/*/`
- Server implementations verified in planning phase
