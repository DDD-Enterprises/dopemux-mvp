"""
Claude-Code-Tools Integration Setup

Configures and initializes Claude-Code-Tools integration for Dopemux.
"""

import logging
from pathlib import Path

from ..cli import cli
from ..adhd.context_manager import ContextManager
from ..tmux.controller import TmuxController

from .integration import initialize_integration
from .cli import register_commands


def setup_claude_tools_integration(context_manager: ContextManager,
                                  tmux_controller: Optional[TmuxController] = None):
    """
    Setup Claude-Code-Tools integration.

    Args:
        context_manager: Dopemux context manager
        tmux_controller: Optional TmuxController instance
    """
    # Initialize integration
    integration = initialize_integration(context_manager, tmux_controller)

    # Register CLI commands
    register_commands(cli)

    logging.info("Claude-Code-Tools integration setup complete")
    return integration