# Desktop-Commander MCP - Connection Guide

**Date**: 2025-10-20
**Status**: ✅ Connected and Validated
**Bridge**: stdio_bridge.py (HTTP → stdio adapter)

## 🎯 Summary

Desktop-Commander MCP server is now fully connected to Claude Code and ready for use.

**Available Tools**:
- ✅ `screenshot` - Take screenshots of the desktop
- ✅ `window_list` - List all open windows
- ✅ `focus_window` - Focus a specific window by title
- ✅ `type_text` - Type text using desktop automation

---

## 🔧 Architecture

Desktop-Commander uses a **dual-layer architecture**:

### Layer 1: HTTP Server (Port 3012)
- FastAPI-based HTTP server
- Runs in Docker container: `mcp-desktop-commander`
- Provides desktop automation via system tools (scrot, wmctrl, xdotool)
- Token-safe: Returns file paths (not base64 data) ✅

### Layer 2: Stdio Bridge
- Python script: `stdio_bridge.py`
- Converts Claude Code stdio MCP protocol → HTTP requests
- Forwards to localhost:3012/mcp endpoint
- Returns responses in JSON-RPC format

```
Claude Code
    ↓ (stdio MCP)
stdio_bridge.py
    ↓ (HTTP)
Desktop-Commander HTTP Server (port 3012)
    ↓
System Tools (scrot, wmctrl, xdotool)
```

---

## 📋 Configuration

### .claude.json Entry
```json
{
  "mcpServers": {
    "desktop-commander": {
      "type": "stdio",
      "command": "python3",
      "args": [
        "/Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander/stdio_bridge.py"
      ],
      "env": {}
    }
  }
}
```

### Prerequisites
- ✅ Desktop-Commander Docker container running (port 3012)
- ✅ Python 3.11+ with aiohttp installed
- ✅ stdio_bridge.py executable

---

## 🧪 Validation

### Test 1: HTTP Server Health
```bash
curl http://localhost:3012/health
# Expected: {"status":"healthy","server":"desktop-commander"}
```

### Test 2: HTTP MCP Protocol
```bash
curl -X POST http://localhost:3012/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list", "params": {}}'
# Expected: {"result": {"tools": [...]}, "error": null}
```

### Test 3: Stdio Bridge
```bash
python3 test_stdio_bridge.py
# Expected: ✅ ALL TESTS PASSED!
```

All tests passing ✅

---

## 🖥️ Usage Examples

### Take Screenshot
```python
# Via MCP call
mcp__desktop-commander__screenshot(filename="/tmp/my-screenshot.png")

# Returns:
{
  "success": True,
  "filename": "/tmp/my-screenshot.png",
  "message": "Screenshot saved to /tmp/my-screenshot.png"
}
```

**Token-Safe**: Returns filename path only (~12 tokens), not base64 data ✅

### List Windows
```python
mcp__desktop-commander__window_list()

# Returns:
{
  "success": True,
  "windows": [
    {"id": "0x01", "desktop": "0", "client": "hostname", "title": "VS Code"},
    {"id": "0x02", "desktop": "0", "client": "hostname", "title": "Terminal"}
  ]
}
```

### Focus Window
```python
mcp__desktop-commander__focus_window(title="VS Code")

# Returns:
{
  "success": True,
  "message": "Focused window with title: VS Code"
}
```

### Type Text
```python
mcp__desktop-commander__type_text(text="Hello from Desktop-Commander!")

# Returns:
{
  "success": True,
  "message": "Typed: Hello from Desktop-Commander!..."
}
```

---

## 🧠 ADHD Benefits

### Visual Context Preservation
- **Screenshots saved to disk** (not in-memory)
- **Persistent beyond MCP session** (can review later)
- **File path returns** (simple, low cognitive load)

### Window Management
- **Automated window switching** (reduces manual context switching)
- **Window list** (visual overview of open contexts)
- **Quick refocus** (get back to coding after interruption)

### Automation
- **Reduce repetitive actions** (screenshot, window switching)
- **Lower activation energy** (one command vs multiple clicks)
- **Consistency** (same workflow every time)

---

## 🎯 Token Budget Compliance

Desktop-Commander was **validated safe** in the MCP token limit audit.

**Typical Response Sizes**:
- `screenshot`: 30 tokens (filename path only) ✅
- `window_list`: 100-500 tokens (10-50 windows) ✅
- `focus_window`: 20 tokens (success message) ✅
- `type_text`: 30 tokens (confirmation) ✅

**All responses < 600 tokens** (6% of 9K budget) ✅

**Why Safe**: Returns file paths instead of base64-encoded image data
- ❌ Base64 screenshot: 168K tokens (16.8× over limit)
- ✅ File path: 12 tokens (0.001× of limit)

See: `DESKTOP_COMMANDER_VALIDATION.md` for full analysis

---

## 🐛 Troubleshooting

### Issue: stdio_bridge.py fails to start
**Solution**: Check Python dependencies
```bash
pip install aiohttp
# Or use venv:
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander
python3 -m venv venv
source venv/bin/activate
pip install aiohttp
```

### Issue: HTTP server not responding
**Solution**: Check Docker container status
```bash
docker ps | grep desktop-commander
# Should show: mcp-desktop-commander (Up, healthy)

# If not running:
docker start mcp-desktop-commander
```

### Issue: Tools not showing in Claude Code
**Solution**: Restart Claude Code to reload .claude.json
1. Close Claude Code
2. Reopen project
3. Check MCP servers loaded

### Issue: Permission denied on stdio_bridge.py
**Solution**: Make executable
```bash
chmod +x /Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander/stdio_bridge.py
```

---

## 📚 Related Documentation

- **Token Limit Validation**: `DESKTOP_COMMANDER_VALIDATION.md`
- **MCP Audit**: `/Users/hue/code/dopemux-mvp/MCP_TOKEN_LIMIT_AUDIT.md`
- **Test Suite**: `test_stdio_bridge.py`
- **Server Implementation**: `server.py`
- **Stdio Bridge**: `stdio_bridge.py`

---

## 🎉 Summary

✅ **Desktop-Commander connected successfully**
✅ **Stdio bridge validated** (test_stdio_bridge.py passing)
✅ **4 tools available** (screenshot, window_list, focus_window, type_text)
✅ **Token-safe** (file path pattern, < 600 tokens per response)
✅ **ADHD-optimized** (visual persistence, automation, low cognitive load)
✅ **Production ready** (health checks passing, container stable)

**Status**: 🟢 **READY FOR USE**

---

## 🚀 Next Steps

Desktop-Commander is ready! You can now use it in your workflows:

1. **Visual Memory Aids**: Take screenshots during decision-making
   ```python
   mcp__desktop-commander__screenshot(filename="/tmp/architecture-decision.png")
   ```

2. **Auto Window Switching**: After code navigation, auto-focus editor
   ```python
   # After finding code in Serena
   mcp__desktop-commander__focus_window(title="VS Code")
   ```

3. **Workflow Automation**: Combine with other MCP tools
   ```python
   # Research → Screenshot → Log Decision
   research = mcp__gpt-researcher__deep_research(topic="...")
   mcp__desktop-commander__screenshot(filename="/tmp/research.png")
   mcp__conport__log_decision(
       summary="Research findings",
       implementation_details="Screenshot: /tmp/research.png"
   )
   ```

**Desktop-Commander is your ADHD-optimized desktop automation companion!** 🖥️✨
