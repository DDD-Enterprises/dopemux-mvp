---
id: mcp-troubleshooting
title: MCP Server Troubleshooting
type: how-to
owner: claude-code-framework
date: 2026-02-21
---

# MCP Server Troubleshooting Guide

## Quick Diagnosis

If you see `Failed to reconnect to [server-name]` errors:

1. **Check Docker containers are running**:
   ```bash
   docker ps | grep dopemux-mcp
   ```
   Should see: `dopemux-mcp-conport`, `dopemux-mcp-serena`, `dopemux-mcp-dope-context`, etc.

2. **Check Claude Code config**:
   ```bash
   cat ~/.claude.json | jq '.projects["/Users/hue/code/dopemux-mvp"].mcpServers'
   ```

3. **Test individual server**:
   ```bash
   /Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/conport-wrapper.sh list-resources
   ```

---

## Common Issues & Fixes

### Issue: "Failed to reconnect to conport"

**Root Cause**: Docker container name mismatch or container not running

**Fix**:
```bash
# 1. Verify container is running
docker ps | grep conport

# 2. Check if it's the new prefixed name
docker ps | grep dopemux-mcp-conport

# 3. Start the stack if needed
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
docker-compose up -d
```

**Why This Happens**:
- Commit d51bff7b5 renamed containers to `dopemux-mcp-*` prefix
- If `.claude.json` references old names (`mcp-conport`), connections fail
- Solution: Use wrapper scripts (they auto-detect container names)

---

### Issue: "Failed to reconnect to dope-context"

**Root Cause**: Docker-based service not running or image unavailable

**Fix**:
```bash
# Start the Dope-Context container
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
docker-compose up dopemux-mcp-dope-context -d

# Verify it's running
docker ps | grep dope-context

# Check logs if it's failing
docker logs dopemux-mcp-dope-context
```

---

### Issue: "Failed to reconnect to serena-v2"

**Root Cause**: HTTP endpoint not responding (container not running or HTTP server down)

**Fix**:
```bash
# Verify Serena is running
docker ps | grep serena

# Check if port 3006 is responding
curl -s http://localhost:3006/mcp | jq . || echo "Not responding"

# Start it if needed
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
docker-compose up dopemux-mcp-serena -d

# Wait 5 seconds for startup
sleep 5

# Verify response
curl http://localhost:3006/mcp
```

---

## Prevention: Use Wrapper Scripts

The `.claude.json` for `/Users/hue/code/dopemux-mvp` should use **wrapper scripts**, not hardcoded container names:

```json
{
  "conport": {
    "type": "stdio",
    "command": "/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/conport-wrapper.sh",
    "args": [],
    "env": { "DOPEMUX_WORKSPACE_ID": "/Users/hue/code/dopemux-mvp" }
  }
}
```

**Why Wrappers Are Better**:
- ✅ Auto-detect container names (handles renames)
- ✅ Clear error messages with suggestions
- ✅ Fallback to alternative container names
- ✅ Resilient to future refactorings

---

## The Proper Architecture

```
User code calls MCP server
        ↓
.claude.json specifies HOW to launch
        ↓
    Three options:
    1. Wrapper script (RECOMMENDED)
    2. Docker command (brittle)
    3. HTTP endpoint (only for remote services)
        ↓
    Wrapper script:
    - Detects workspace
    - Finds container (tries multiple names)
    - Passes through stdio
    - Handles errors gracefully
```

---

## Creating New MCP Wrappers

When adding a new MCP server:

1. **Create wrapper** at `scripts/mcp-wrappers/{server}-wrapper.sh`
2. **Make executable**: `chmod +x scripts/mcp-wrappers/{server}-wrapper.sh`
3. **Use in .claude.json**:
   ```json
   {
     "your-server": {
       "type": "stdio",
       "command": "/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/your-server-wrapper.sh",
       "args": [],
       "env": { "DISPLAY": ":0" }
     }
   }
   ```

**Template**:
```bash
#!/usr/bin/env bash
set -euo pipefail

# Helper functions
detect_workspace() {
  if [[ -n "${DOPEMUX_WORKSPACE_ID:-}" ]]; then
    printf '%s\n' "${DOPEMUX_WORKSPACE_ID}"
    return
  fi

  if command -v git >/dev/null 2>&1; then
    git rev-parse --show-toplevel 2>/dev/null || pwd
  else
    pwd
  fi
}

find_container() {
  local pattern="$1"
  docker ps --format "table {{.Names}}" | grep "$pattern" | head -1 || return 1
}

# Main logic
workspace_id="$(detect_workspace)"
export DOPEMUX_WORKSPACE_ID="$workspace_id"

# Find and execute
container_name="$(find_container "your-server-pattern")" || {
  echo "❌ Container not found" >&2
  exit 1
}

exec docker exec -i -e DOPEMUX_WORKSPACE_ID="$workspace_id" \
  "$container_name" python /app/server.py "$@"
```

---

## Why This Happened (Post-Mortem)

1. **2026-02-21**: Commit d51bff7b5 refactored to namespace MCP containers with `dopemux-` prefix
2. **Issue**: `.claude.json` config file wasn't updated to match new container names
3. **Effect**: All hardcoded docker references broke simultaneously
4. **Solution**: Implemented resilient wrapper scripts that abstract container names
5. **Result**: Future container renames won't break configuration

---

## Related Documentation

- [MCP Servers Overview](../01-reference/mcp-servers.md)
- [Docker Configuration](../01-reference/docker-setup.md)
- [Dopemux Architecture](../01-reference/architecture.md)

---

**Last Updated**: 2026-02-21
**Status**: ✅ Current (Wrapper scripts implemented)
**Maintainer**: Claude Code Framework
