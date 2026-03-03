"""
Port Configuration Utilities for Dopemux.

Centralized port configuration with environment variable overrides
for testing and multi-instance deployments.
"""

import os
from typing import Optional


def get_conport_port(instance_id: Optional[str] = None) -> int:
    """
    Get ConPort HTTP API port with environment variable override.

    Args:
        instance_id: Optional instance ID (A-E) for multi-instance deployments

    Returns:
        Port number for ConPort HTTP API

    Environment:
        DOPEMUX_CONPORT_PORT: Override default port (3004)
        DOPEMUX_PORT_BASE: Base port for instance A (overrides 3000)

    Examples:
        # Default (instance A):
        port = get_conport_port()  # Returns 3004 (or 3007 for ConPort MCP)

        # With environment override:
        os.environ['DOPEMUX_CONPORT_PORT'] = '4004'
        port = get_conport_port()  # Returns 4004

        # Multi-instance (instance B on port base 3030):
        port = get_conport_port('B')  # Returns 3037 (3030 + 7)
    """
    # Check for explicit port override first
    env_port = os.environ.get('DOPEMUX_CONPORT_PORT')
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass  # Fall through to default logic

    # Multi-instance support: Calculate from instance ID
    if instance_id and instance_id != 'A':
        from pathlib import Path
        from .instance_manager import InstanceManager
        # Port bases: A=3000, B=3030, C=3060, D=3090, E=3120
        manager = InstanceManager(workspace_root=Path.cwd())  # Just for ID mapping
        port_base = manager._instance_id_to_port(instance_id)
        return port_base + 4  # ConPort offset is +4

    # Default: Instance A ConPort on port 3004
    # (DopeconBridge at 3016, ConPort MCP at 3005, HTTP API at 3004)
    return 3004


def get_conport_url(instance_id: Optional[str] = None) -> str:
    """
    Get full ConPort HTTP API URL.

    Args:
        instance_id: Optional instance ID (A-E)

    Returns:
        Full HTTP URL to ConPort API

    Example:
        url = get_conport_url()  # "http://localhost:3004"
    """
    port = get_conport_port(instance_id)
    return f"http://localhost:{port}"
