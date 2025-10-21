#!/usr/bin/env python3
"""
Create/Update project-level Claude MCP config for ConPort with multi-worktree support.

Writes .claude/claude_config.json in the current repository with a `conport`
entry that uses docker exec stdio into the ConPort container. The container
name is derived from DOPEMUX_INSTANCE_ID to support parallel worktrees.

Instance detection:
  - --instance: explicit instance id (e.g., feature-auth)
  - env DOPEMUX_INSTANCE_ID
  - git branch name (sanitized)
  - folder basename

Workspace id:
  - env DOPEMUX_WORKSPACE_ID
  - repo root path (absolute)
"""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional


def git_branch(cwd: Path) -> Optional[str]:
    try:
        out = subprocess.check_output([
            "git", "rev-parse", "--abbrev-ref", "HEAD"
        ], cwd=str(cwd), stderr=subprocess.DEVNULL, text=True).strip()
        if out:
            # Sanitize to simple id
            return re.sub(r"[^a-zA-Z0-9_.-]", "-", out)
    except Exception:
        pass
    return None


def detect_instance_id(cwd: Path) -> str:
    # Priority: env → git branch → folder name
    env_id = os.getenv("DOPEMUX_INSTANCE_ID")
    if env_id:
        return env_id
    br = git_branch(cwd)
    if br and br not in ("HEAD",):
        return br
    return cwd.name


def detect_workspace_id(cwd: Path) -> str:
    env_ws = os.getenv("DOPEMUX_WORKSPACE_ID")
    if env_ws:
        return env_ws
    # Use repo root; if in a subdir, traverse up to git root
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=str(cwd), text=True).strip()
        return root
    except Exception:
        return str(cwd)


def write_project_config(project_root: Path, instance_id: Optional[str], workspace_id: str) -> Path:
    claude_dir = project_root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = claude_dir / "claude_config.json"

    # Load existing project config
    existing = {}
    if cfg_path.exists():
        try:
            existing = json.loads(cfg_path.read_text())
        except Exception:
            existing = {}
    if not isinstance(existing, dict):
        existing = {}
    if not isinstance(existing.get("mcpServers"), dict):
        existing["mcpServers"] = {}

    # Container name follows compose naming: mcp-conport[_<instance>]
    container = "mcp-conport" + (f"_{instance_id}" if instance_id else "")

    # Build conport stdio server entry (docker exec)
    conport_entry = {
        "type": "stdio",
        "command": "docker",
        "args": [
            "exec", "-i", container,
            # Use uvx to run conport MCP in stdio mode inside the container
            "uvx", "--from", "context-portal-mcp", "conport-mcp"
        ],
        "env": {
            # Ensure per-worktree isolation on both sides
            "DOPEMUX_INSTANCE_ID": instance_id or "",
            "DOPEMUX_WORKSPACE_ID": workspace_id
        }
    }

    existing["mcpServers"]["conport"] = conport_entry

    # Also add an admin MCP for instance management
    admin_entry = {
        "type": "stdio",
        "command": "docker",
        "args": [
            "exec", "-i", container,
            "python", "/app/conport_mcp_stdio.py"
        ],
        "env": {
            "CONPORT_URL": "http://localhost:3004"
        }
    }
    existing["mcpServers"]["conport-admin"] = admin_entry
    cfg_path.write_text(json.dumps(existing, indent=2))
    return cfg_path


def main():
    ap = argparse.ArgumentParser(description="Wire project-level ConPort for Claude MCP with worktree support")
    ap.add_argument("--project", help="Path to project root (defaults to CWD)")
    ap.add_argument("--instance", help="Explicit instance id (e.g., feature-auth)")
    args = ap.parse_args()

    project_root = Path(args.project).resolve() if args.project else Path.cwd().resolve()
    instance_id = args.instance or detect_instance_id(project_root)
    workspace_id = detect_workspace_id(project_root)

    cfg_path = write_project_config(project_root, instance_id, workspace_id)
    print("✅ Project ConPort wired for Claude MCP")
    print(f"  Config: {cfg_path}")
    print(f"  Instance: {instance_id}")
    print(f"  Workspace: {workspace_id}")
    print("  Server name: conport (stdio via docker exec)")
    print("  Container target:", "mcp-conport" + (f"_{instance_id}" if instance_id else ""))


if __name__ == "__main__":
    main()
