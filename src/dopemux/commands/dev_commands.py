"""
Dev Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
def dev():
    """
    🔧 Development mode (for contributors)

    Auto-detects local checkouts of MCP servers (Zen, ConPort, etc.)
    and uses them instead of production versions. Enables hot reload
    and test database isolation.

    Components checked:
    - ~/code/zen-mcp-server (Zen MCP development)
    - ~/code/conport-mcp (ConPort development)
    - ~/code/serena-lsp (Serena development)
    """
    pass


# Import and register dev commands
try:
    from ..dev_commands import dev_status, dev_enable, dev_paths

    dev.add_command(dev_status, "status")
    dev.add_command(dev_enable, "enable")
    dev.add_command(dev_paths, "paths")

except ImportError:
    pass  # Dev commands not available
