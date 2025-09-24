"""
Configuration management for Dopemux.

Handles YAML/TOML configuration files, user preferences, and default settings
for ADHD accommodations.
"""

from .manager import ConfigManager

__all__ = ["ConfigManager"]
