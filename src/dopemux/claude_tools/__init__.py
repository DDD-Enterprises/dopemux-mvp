"""
Claude-Code-Tools Integration for Dopemux

This module integrates Claude-Code-Tools functionality into Dopemux,
providing enhanced terminal automation, safety hooks, and session management.

Components:
- tmux_cli: Programmatic tmux control for AI agents
- safety_hooks: Command interception and safety enforcement
- session_manager: Enhanced session search and resume
- env_safe: Secure environment variable inspection
"""

__version__ = "0.1.0"
__all__ = ["tmux_cli", "safety_hooks", "session_manager", "env_safe"]