---
id: README_HYBRID
title: Readme_Hybrid
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme_Hybrid (explanation) for dopemux documentation and developer workflows.
---
# Desktop Commander MCP v2.0 - Hybrid OS Support

**Cross-platform desktop automation for Claude Code with ADHD-optimized workflows**

## Overview

Desktop Commander v2.0 automatically detects your operating system and uses the appropriate automation tools:
- **macOS**: Native AppleScript + screencapture (via `uvx`)
- **Linux**: X11 tools (scrot/wmctrl/xdotool) (via Docker)

## Architecture

```
Claude Code
    ↓ (stdio MCP)
start_with_uvx.sh (macOS) OR Docker container (Linux)
    ↓
stdio_bridge.py
    ↓ (HTTP)
server.py (FastAPI with OS detection)
    ↓
macOS: osascript, screencapture
Linux: scrot, wmctrl, xdotool
```

## Available Tools

| Tool | Description | macOS Status | Linux Status |
|------|-------------|--------------|--------------|
| **screenshot** | Capture screen | ⚠️ Requires permission | ✅ Works |
| **window_list** | List open windows | ✅ Works | ✅ Works |
| **focus_window** | Focus app/window | ✅ Works | ✅ Works |
| **type_text** | Simulate keyboard | ⚠️ Requires permission | ✅ Works |

## macOS Setup (uvx-based)

### 1. Prerequisites

```bash
# uv/uvx should already be installed (part of Dopemux)
# All dependencies will be auto-installed by uvx
```

### 2. Grant Permissions (macOS only)

Desktop Commander needs permissions to automate your Mac:

**For Screenshots**:
1. System Settings → Privacy & Security → Screen Recording
1. Add your terminal app (kitty, iTerm2, Terminal.app)
1. Restart terminal

**For Keyboard Automation**:
1. System Settings → Privacy & Security → Accessibility
1. Add your terminal app
1. Restart terminal

### 3. Configuration

Already configured in `.claude.json`:
```json
"desktop-commander": {
  "type": "stdio",
  "command": "/Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander/start_with_uvx.sh",
  "args": [],
  "env": {},
  "description": "Desktop automation with native macOS support (uvx-based)"
}
```

### 4. Test

```bash
# Test directly
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander
./start_with_uvx.sh

# In another terminal, test the HTTP endpoint
curl http://localhost:3012/health

# Should return:
# {
#   "status": "healthy",
#   "server": "desktop-commander",
#   "version": "2.0.0",
#   "platform": "Darwin",
#   "macos_mode": true,
#   "linux_mode": false
# }
```

## Linux Setup (Docker-based)

### 1. Start Docker Container

```bash
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
docker-compose up -d desktop-commander
```

### 2. Configuration

Update `.claude.json` for Docker:
```json
"desktop-commander": {
  "type": "stdio",
  "command": "python3",
  "args": [
    "/Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander/stdio_bridge.py"
  ],
  "env": {}
}
```

With Docker container forwarding to port 3012.

## ADHD-Optimized Workflows

### 1. Auto-Focus After Navigation
```python
# Serena finds code
mcp__serena-v2__goto_definition(file_path="src/auth.py", line=42, column=10)

# Desktop Commander brings editor to focus
mcp__desktop-commander__focus_window(title="VS Code")
# or
mcp__desktop-commander__focus_window(title="Neovim")
```

### 2. Visual Decision Logging
```python
# Take screenshot for visual memory
mcp__desktop-commander__screenshot(filename="/tmp/architecture.png")

# Log decision with visual evidence
mcp__conport__log_decision(
    workspace_id="/Users/hue/code/dopemux-mvp",
    summary="OAuth PKCE implementation architecture",
    implementation_details="Diagram: /tmp/architecture.png",
    tags=["architecture", "visual-aid"]
)
```

### 3. Context Recovery
```python
# After interruption, restore window focus
mcp__desktop-commander__focus_window(title="Claude")

# Or focus the project you were working on
mcp__desktop-commander__focus_window(title="kitty")
```

## Troubleshooting

### macOS: "could not create image from display"
**Issue**: Screenshot permission not granted
**Fix**: System Settings → Privacy & Security → Screen Recording → Add terminal app

### macOS: "osascript is not allowed to send keystrokes"
**Issue**: Accessibility permission not granted
**Fix**: System Settings → Privacy & Security → Accessibility → Add terminal app

### macOS: "Server not responding"
**Issue**: HTTP server not running
**Fix**:
```bash
# Kill any existing servers
pkill -f "uvx.*desktop-commander"
rm /tmp/desktop-commander-uvx.pid

# Restart
./start_with_uvx.sh
```

### Linux: "Cannot open display"
**Issue**: X11 socket not mounted or DISPLAY variable not set
**Fix**: Ensure docker-compose.yml has:
```yaml
environment:
- DISPLAY=${DISPLAY:-:0}
volumes:
- /tmp/.X11-unix:/tmp/.X11-unix:rw
```

## Development

### Running Server Directly
```bash
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers/desktop-commander

# With uvx
uvx --from . desktop-commander

# Or with python directly
python3 -m server
```

### Testing Stdio Bridge
```bash
# Start server in background
uvx --from . desktop-commander &

# Test stdio bridge
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 stdio_bridge.py
```

### Testing Native macOS Commands
```bash
# Screenshot
screencapture -x /tmp/test.png

# Window list
osascript -e 'tell application "System Events" to get name of every process whose visible is true'

# Focus window
osascript -e 'tell application "Claude" to activate'

# Type text (requires Accessibility permission)
osascript -e 'tell application "System Events" to keystroke "test"'
```

## Performance

### macOS (uvx)
- **Startup**: ~2 seconds (first run), <1 second (cached)
- **Screenshot**: ~100ms (no permission), instant (with permission)
- **Window List**: ~200ms
- **Focus Window**: ~50ms ✅ **ADHD-optimized**
- **Type Text**: ~100ms

### Linux (Docker)
- **Startup**: ~5 seconds (container + dependencies)
- **Screenshot**: ~100ms
- **Window List**: ~50ms
- **Focus Window**: ~50ms
- **Type Text**: ~100ms

## Migration from Docker to uvx (macOS)

If you were using the Docker version on macOS:

1. Stop Docker container:
```bash
docker stop mcp-desktop-commander
```

1. Update `.claude.json` to use `start_with_uvx.sh`

1. Grant macOS permissions (see above)

1. Test with Claude Code

**Benefits**:
- ✅ No Docker overhead (~80% faster startup)
- ✅ Native macOS integration
- ✅ Better reliability (no X11 complexity)
- ✅ Lower memory usage

## Version History

### v2.0.0 (2025-10-19)
- ✨ Hybrid OS support with auto-detection
- ✨ Native macOS implementation (AppleScript + screencapture)
- ✨ uvx support for macOS
- ✨ Automatic server startup with stdio bridge
- ✅ Backward compatible with Docker on Linux
- 🐛 Fixed X11 display errors on macOS

### v1.0.0 (2024-10-04)
- 🎉 Initial release with Linux X11 support
- 🐳 Docker-based deployment

## License

Part of Dopemux MVP - ADHD-optimized development platform

## Support

For issues or questions:
1. Check this README
1. Review `CONNECTION_GUIDE.md` for connection patterns
1. Check `DESKTOP_COMMANDER_VALIDATION.md` for testing procedures
1. Open issue in Dopemux repository

---

**ADHD Optimization**: This tool enables sub-2-second context switching and automatic window focus, reducing the cognitive load of manual window management during development workflows.
