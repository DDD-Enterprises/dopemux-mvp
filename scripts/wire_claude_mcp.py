#!/usr/bin/env python3
"""
Wire Dopemux MCP servers into Claude Desktop global config.

Targets (global):
  - mas-sequential-thinking (stdio via docker exec)
  - zen (stdio via docker exec)
  - context7 (stdio via docker exec)
  - serena (SSE http://127.0.0.1:3006/sse)
  - exa (SSE http://127.0.0.1:3008/sse)
  - leantime-bridge (SSE http://127.0.0.1:3015/sse)
  - task-orchestrator (stdio via docker exec)
  - gptr-researcher-stdio (stdio via docker exec)

Excluded (project-specific):
  - conport

Creates/updates Claude Desktop config file and preserves existing keys.
Backs up existing config next to it with a .bak timestamp suffix.
"""

import json
import os
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path


def detect_claude_config_path() -> Path:
    home = Path.home()
    system = platform.system()
    # Claude Desktop default locations
    candidates = []
    if system == "Darwin":
        candidates.append(home / "Library/Application Support/Claude/claude_desktop_config.json")
    elif system == "Windows":
        appdata = os.getenv("APPDATA") or str(home / "AppData/Roaming")
        candidates.append(Path(appdata) / "Claude/claude_desktop_config.json")
    else:
        # Linux
        candidates.append(home / ".claude/claude_config.json")

    for p in candidates:
        parent = p.parent
        parent.mkdir(parents=True, exist_ok=True)
        return p
    # Fallback to mac-style path
    return home / "Library/Application Support/Claude/claude_desktop_config.json"


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def build_mcp_servers(env: dict) -> dict:
    # Read sensitive values used by some servers (optional)
    context7_api_key = env.get("CONTEXT7_API_KEY", "")
    context7_endpoint = env.get("CONTEXT7_ENDPOINT", "")

    servers = {
        "mas-sequential-thinking": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "exec", "-i", "mcp-mas-sequential-thinking",
                "mcp-server-mas-sequential-thinking"
            ],
            "env": {}
        },
        "zen": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "exec", "-i", "mcp-zen",
                "python", "server.py"
            ],
            "env": {}
        },
        "context7": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "exec", "-i", "mcp-context7",
                "npx", "-y", "@upstash/context7-mcp"
            ],
            "env": {
                **({"CONTEXT7_API_KEY": context7_api_key} if context7_api_key else {}),
                **({"CONTEXT7_ENDPOINT": context7_endpoint} if context7_endpoint else {}),
            },
        },
        "serena": {
            "type": "sse",
            "url": "http://127.0.0.1:3006/sse"
        },
        "exa": {
            "type": "sse",
            "url": "http://127.0.0.1:3008/sse"
        },
        "leantime-bridge": {
            "type": "sse",
            "url": "http://127.0.0.1:3015/sse"
        },
        "task-orchestrator": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "exec", "-i", "mcp-task-orchestrator",
                "gradle", "run", "--args=--transport=stdio --port=3014"
            ],
            "env": {}
        },
        "gptr-researcher-stdio": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "exec", "-i", "mcp-gptr-stdio",
                "python", "/app/scripts/gpt-researcher/mcp_server.py"
            ],
            "env": {}
        },
        "ddg-mcp": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "exec", "-i", "dope-decision-graph-bridge",
                "python", "/app/ddg_mcp_stdio.py"
            ],
            "env": {
                "BRIDGE_URL": "http://localhost:3016"
            }
        }
    }
    return servers


def main():
    config_path = detect_claude_config_path()
    existing = {}
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text())
        except Exception:
            existing = {}

    # Ensure base structure
    if not isinstance(existing, dict):
        existing = {}
    if not isinstance(existing.get("mcpServers"), dict):
        existing["mcpServers"] = {}

    # Build server entries using repo .env if present
    repo_env_path = Path(__file__).resolve().parents[1] / ".env"
    env = os.environ.copy()
    if repo_env_path.exists():
        try:
            for line in repo_env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip())
        except Exception:
            pass

    servers = build_mcp_servers(env)

    merged = deep_merge(existing, {"mcpServers": servers})

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if config_path.exists():
        backup_path = config_path.with_suffix(f".json.bak_{ts}")
        try:
            shutil.copy2(config_path, backup_path)
        except Exception:
            pass

    # Write
    config_path.write_text(json.dumps(merged, indent=2))
    print(f"✅ Updated Claude config: {config_path}")
    print("Added/updated MCP servers:")
    for name in servers.keys():
        print(f"  - {name}")


if __name__ == "__main__":
    main()
