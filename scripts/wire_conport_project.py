#!/usr/bin/env python3
"""
Wire ConPort MCP Server to a project's .claude/claude_config.json.
This enables Claude Code CLI to use ConPort via the unified Docker setup.
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import shutil

def wire_conport(project_path: str, instance: str = None):
    project_root = Path(project_path).resolve()
    claude_dir = project_root / ".claude"
    config_path = claude_dir / "claude_config.json"
    
    # Ensure .claude directory exists
    if not claude_dir.exists():
        print(f"📁 Creating {claude_dir}")
        claude_dir.mkdir(parents=True, exist_ok=True)
        
    # Load existing config or create new
    config = {}
    if config_path.exists():
        print(f"📖 Reading existing config from {config_path}")
        # Backup existing config
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".json.bak_{timestamp}")
        shutil.copy2(config_path, backup_path)
        print(f"💾 Backup created: {backup_path.name}")
        
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Warning: {config_path} is invalid JSON. Starting fresh.")
            config = {}

    # Update mcpServers
    if "mcpServers" not in config:
        config["mcpServers"] = {}
        
    container_name = "mcp-conport"
    if instance and instance != "main":
        container_name = f"mcp-conport_{instance}"
        
    config["mcpServers"]["conport"] = {
        "type": "stdio",
        "command": "docker",
        "args": ["exec", "-i", container_name, "python", "conport_mcp_stdio.py"]
    }
    
    # Save updated config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        
    print(f"✅ ConPort wired successfully in {config_path}")
    print(f"   Using container: {container_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wire ConPort MCP to project config")
    parser.add_argument("--project", default=".", help="Project root path")
    parser.add_argument("--instance", help="Dopemux instance ID")
    
    args = parser.parse_args()
    
    try:
        wire_conport(args.project, args.instance)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
