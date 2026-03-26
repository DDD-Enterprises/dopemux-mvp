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
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console

@click.group()
def dev():
    """
    🔧 Contributor Flight-Deck: Development & hot reload

    Engages development mode for daemon contributors. This mode auto-detects 
    local checkouts of ritual daemons (Zen, ConPort, Serena) and directs the 
    cockpit to use these local artifacts instead of production versions.

    Ritual Capabilities:
    - Hot Reload: Direct synchronization between local source and active cockpit.
    - Isolated Persistence: Directs telemetry to the development database (isolated).
    - Local Checkouts: Auto-maps ~/code/zen-mcp-server, ~/code/conport-mcp, etc.
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
