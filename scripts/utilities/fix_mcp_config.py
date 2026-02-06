#!/usr/bin/env python3
"""Fix MCP server configurations in ~/.claude.json"""

import json
import os
from pathlib import Path

def fix_mcp_config():
    """Apply all MCP server configuration fixes"""

    config_path = Path.home() / ".claude.json"

    # Read current config
    with open(config_path) as f:
        config = json.load(f)

    # Find dopemux-mvp project
    projects = config.get("projects", {})
    dopemux_key = None
    for key in projects:
        if "dopemux-mvp" in key:
            dopemux_key = key
            break

    if not dopemux_key:
        print("❌ Could not find dopemux-mvp project in config")
        return False

    project = projects[dopemux_key]
    mcp_servers = project.get("mcpServers", {})

    print("🔧 Applying MCP server fixes...\n")

    # Fix 1: ConPort - Correct SSE endpoint
    if "conport" in mcp_servers:
        mcp_servers["conport"] = {
            "type": "sse",
            "url": "http://localhost:3004/sse",
            "env": {
                "WORKSPACE_ID": "/Users/hue/code/dopemux-mvp"
            }
        }
        print("✅ Fixed conport: SSE endpoint /mcp → /sse")

    # Fix 2: PAL - Use Docker exec
    if "pal" in mcp_servers:
        mcp_servers["pal"] = {
            "type": "stdio",
            "command": "docker",
            "args": ["exec", "-i", "dopemux-mcp-pal", "python", "/app/server.py"],
            "env": {
                "DISPLAY": ":0"
            }
        }
        print("✅ Fixed pal: system python3 → Docker exec")

    # Fix 3: Dope-Context - Use Docker exec
    if "dope-context" in mcp_servers:
        mcp_servers["dope-context"] = {
            "type": "stdio",
            "command": "docker",
            "args": ["exec", "-i", "eac0906fea92_dopemux-mcp-dope-context", "python", "/app/server.py"],
            "env": {
                "DISPLAY": ":0"
            }
        }
        print("✅ Fixed dope-context: shell script → Docker exec")

    # Fix 4: Exa - SSE to stdio
    if "exa" in mcp_servers:
        mcp_servers["exa"] = {
            "type": "stdio",
            "command": "docker",
            "args": ["exec", "-i", "dopemux-mcp-exa", "python", "/app/server.py"],
            "env": {
                "DISPLAY": ":0"
            }
        }
        print("✅ Fixed exa: SSE → stdio via Docker exec")

    # Fix 5: Desktop Commander - SSE to stdio
    if "desktop-commander" in mcp_servers:
        mcp_servers["desktop-commander"] = {
            "type": "stdio",
            "command": "docker",
            "args": ["exec", "-i", "dopemux-mcp-desktop-commander", "python", "/app/mcp_server.py"],
            "env": {
                "DISPLAY": "${DISPLAY:-:0}"
            }
        }
        print("✅ Fixed desktop-commander: SSE → stdio via Docker exec")

    # Fix 6: GPT-Researcher - SSE to stdio
    if "dopemux-mcp-gptr-mcp" in mcp_servers:
        mcp_servers["dopemux-mcp-gptr-mcp"] = {
            "type": "stdio",
            "command": "docker",
            "args": ["exec", "-i", "dopemux-mcp-gptr-mcp", "python", "/app/server.py"],
            "env": {
                "DISPLAY": ":0"
            }
        }
        print("✅ Fixed dopemux-mcp-gptr-mcp: SSE → stdio via Docker exec")

    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print("\n✅ All fixes applied successfully!")
    print(f"📝 Config updated: {config_path}")
    return True

if __name__ == "__main__":
    success = fix_mcp_config()
    exit(0 if success else 1)
