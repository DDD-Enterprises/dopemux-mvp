#!/usr/bin/env python3
"""
MCP Service Discovery - Auto-generate .claude.json from running containers.

This script eliminates configuration drift by querying running MCP servers
for their connection details and generating .claude.json automatically.

Usage:
    # Generate new config
    python scripts/generate-claude-config.py > .claude.json
    
    # Validate existing config
    python scripts/generate-claude-config.py --validate
    
    # Show diff without writing
    python scripts/generate-claude-config.py --diff

Requirements:
    pip install docker requests pydantic
"""

import argparse
import json
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import docker
    import requests
    from pydantic import BaseModel, Field
except ImportError:
    print("Missing dependencies. Install with:", file=sys.stderr)
    print("  pip install docker requests pydantic", file=sys.stderr)
    sys.exit(1)


class MCPConnectionInfo(BaseModel):
    """MCP server connection information from /info endpoint."""
    type: str  # "sse" or "stdio"
    url: Optional[str] = None  # For SSE
    command: Optional[str] = None  # For stdio
    args: Optional[List[str]] = None  # For stdio


class MCPServerInfo(BaseModel):
    """Complete server information from /info endpoint."""
    name: str
    version: str
    mcp: Dict[str, Any]
    health: str = "/health"
    description: str = ""


class ClaudeConfig(BaseModel):
    """Generated .claude.json structure."""
    mcpServers: Dict[str, Dict[str, Any]]


def discover_mcp_containers() -> List[tuple]:
    """
    Find all running MCP server containers.
    
    Returns:
        List of (container_name, port) tuples
    """
    client = docker.from_env()
    servers = []
    
    try:
        containers = client.containers.list()
    except docker.errors.DockerException as e:
        print(f"❌ Docker not available: {e}", file=sys.stderr)
        sys.exit(1)
    
    for container in containers:
        name = container.name
        
        # Match MCP server containers
        if any(prefix in name for prefix in ['mcp-', 'conport', 'serena', 'leantime-bridge', 'dope-context']):
            ports = container.ports
            
            # Extract primary port
            port = extract_primary_port(ports)
            if port:
                servers.append((name, port))
                print(f"🔍 Found: {name} on port {port}", file=sys.stderr)
    
    return servers


def extract_primary_port(ports: Dict) -> Optional[int]:
    """Extract the primary HTTP port from Docker container port mapping."""
    if not ports:
        return None
    
    # Prefer common MCP ports
    for port_key in ports.keys():
        port_num = int(port_key.split('/')[0])
        # conport uses 4004 for its info server
        if 3000 <= port_num <= 3020 or port_num in [4004, 4006, 8000, 8001, 8005, 8080]:
            bindings = ports[port_key]
            if bindings:
                return int(bindings[0]['HostPort'])
    
    return None


def fetch_server_info(name: str, port: int) -> Optional[MCPServerInfo]:
    """
    Query /info endpoint to get server connection details.
    
    Args:
        name: Container name
        port: HTTP port
    
    Returns:
        MCPServerInfo or None if unavailable
    """
    url = f"http://localhost:{port}/info"
    
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        data = response.json()
        
        return MCPServerInfo(**data)
    
    except requests.RequestException as e:
        print(f"⚠️  {name}: No /info endpoint ({e})", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  {name}: Invalid /info response ({e})", file=sys.stderr)
        return None


def build_claude_config_entry(info: MCPServerInfo) -> Dict[str, Any]:
    """
    Transform /info response into .claude.json format.
    
    Args:
        info: Server info from /info endpoint
    
    Returns:
        Config entry for .claude.json
    """
    mcp = info.mcp
    connection = mcp.get('connection', {})
    protocol = mcp.get('protocol', 'sse')
    
    entry = {
        "description": info.description
    }
    
    if protocol in ['sse', 'streamablehttp']:
        entry.update({
            "type": "sse",
            "url": connection.get('url', '')
        })
    elif protocol == 'stdio':
        entry.update({
            "type": "stdio",
            "command": connection.get('command', ''),
            "args": connection.get('args', [])
        })
    
    # Preserve env vars if specified
    if 'env' in mcp:
        entry['env'] = mcp['env']
    
    return entry


def generate_config(servers: List[tuple]) -> ClaudeConfig:
    """
    Generate complete .claude.json from discovered servers.
    
    Args:
        servers: List of (name, port) tuples
    
    Returns:
        Complete Claude config
    """
    mcp_servers = {}
    
    for name, port in servers:
        info = fetch_server_info(name, port)
        
        if info:
            # Use canonical name from /info, not container name
            config_entry = build_claude_config_entry(info)
            mcp_servers[info.name] = config_entry
            print(f"✅ {info.name}: {info.mcp['protocol']} configured", file=sys.stderr)
        else:
            # Fallback: basic config without /info
            print(f"⚠️  {name}: Using fallback config", file=sys.stderr)
            mcp_servers[name.replace('mcp-', '').replace('dopemux-', '')] = {
                "type": "sse",
                "url": f"http://localhost:{port}/sse",
                "description": "Auto-discovered (no /info endpoint)"
            }
    
    return ClaudeConfig(mcpServers=mcp_servers)


def validate_config(generated: ClaudeConfig, existing_path: Path) -> bool:
    """
    Compare generated config with existing .claude.json.
    
    Returns:
        True if identical, False if drift detected
    """
    if not existing_path.exists():
        print("❌ No existing .claude.json found", file=sys.stderr)
        return False
    
    with open(existing_path) as f:
        existing = json.load(f)
    
    generated_dict = json.loads(generated.json())
    
    if existing == generated_dict:
        print("✅ Configuration validated - no drift", file=sys.stderr)
        return True
    else:
        print("❌ Configuration drift detected!", file=sys.stderr)
        print("\nMissing in current config:", file=sys.stderr)
        for name in generated_dict['mcpServers']:
            if name not in existing.get('mcpServers', {}):
                print(f"  + {name}", file=sys.stderr)
        
        print("\nExtra in current config:", file=sys.stderr)
        for name in existing.get('mcpServers', {}):
            if name not in generated_dict['mcpServers']:
                print(f"  - {name}", file=sys.stderr)
        
        return False


def show_diff(generated: ClaudeConfig, existing_path: Path):
    """Show unified diff between generated and existing config."""
    import difflib
    
    if not existing_path.exists():
        print("No existing .claude.json to compare", file=sys.stderr)
        return
    
    with open(existing_path) as f:
        existing_lines = f.readlines()
    
    generated_json = json.dumps(json.loads(generated.json()), indent=2)
    generated_lines = (generated_json + '\n').splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        existing_lines,
        generated_lines,
        fromfile='.claude.json (current)',
        tofile='.claude.json (generated)'
    )
    
    print(''.join(diff))


def main():
    parser = argparse.ArgumentParser(
        description='Auto-generate .claude.json from running MCP servers'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate existing config against running servers'
    )
    parser.add_argument(
        '--diff',
        action='store_true',
        help='Show diff between current and generated config'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Discover running servers
    print("🔍 Discovering MCP servers...", file=sys.stderr)
    servers = discover_mcp_containers()
    
    if not servers:
        print("❌ No MCP servers found. Start with: docker-compose up -d", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n📋 Found {len(servers)} servers", file=sys.stderr)
    
    # Generate config
    config = generate_config(servers)
    
    # Handle modes
    if args.validate:
        existing = Path('.claude.json')
        success = validate_config(config, existing)
        sys.exit(0 if success else 1)
    
    elif args.diff:
        existing = Path('.claude.json')
        show_diff(config, existing)
    
    else:
        # Output generated config
        output = json.dumps(json.loads(config.json()), indent=2)
        
        if args.output:
            args.output.write_text(output)
            print(f"✅ Config written to {args.output}", file=sys.stderr)
        else:
            print(output)


if __name__ == '__main__':
    main()
