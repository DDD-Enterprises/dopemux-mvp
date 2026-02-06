#!/usr/bin/env python3
"""
Unit tests for Dopemux role catalog and activation logic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pytest
from rich.console import Console

from dopemux.roles.catalog import (
    activate_role,
    available_roles,
    resolve_role,
    RoleNotFoundError,
)
from dopemux.config.manager import MCPServerConfig, DopemuxConfig


@dataclass
class DummyConfigManager:
    """Minimal config manager stub for role activation tests."""

    _config: DopemuxConfig

    def load_config(self) -> DopemuxConfig:
        return self._config


def _build_dummy_config(servers: Optional[list[str]] = None) -> DummyConfigManager:
    """Create a dummy config manager with specific MCP servers."""
    servers = servers or ["conport", "serena", "pal", "zen", "exa"]
    config = DopemuxConfig()
    config.mcp_servers = {
        name: MCPServerConfig(
            enabled=True,
            command=name,
            args=[],
            env={},
        )
        for name in servers
    }
    return DummyConfigManager(config)


def test_available_roles_includes_core_personas():
    roles = available_roles()
    assert "quickfix" in roles
    assert "act" in roles
    assert "plan" in roles
    assert "research" in roles
    assert "all" in roles
    assert "developer" in roles
    assert "architect" in roles
    assert "reviewer" in roles
    assert "debugger" in roles
    assert "ops" in roles


def test_resolve_role_supports_aliases():
    assert resolve_role("Developer").key == "developer"
    assert resolve_role("planner").key == "plan"
    assert resolve_role("researcher").key == "research"
    assert resolve_role("orchestrator").key == "plan"


def test_activate_role_quickfix_filters_servers(monkeypatch):
    cfg_manager = _build_dummy_config()
    console = Console(record=True)

    activation = activate_role("quickfix", cfg_manager, console)

    assert activation.resolved_key == "quickfix"
    assert set(activation.enabled_servers) == {"conport", "pal", "serena"}
    disabled = {
        name
        for name, cfg in cfg_manager.load_config().mcp_servers.items()
        if not cfg.enabled
    }
    assert disabled >= {"zen", "exa"}
    assert os.environ.get("DOPEMUX_AGENT_ROLE") == "quickfix"


def test_activate_role_all_leaves_servers_enabled(monkeypatch):
    cfg_manager = _build_dummy_config()
    console = Console(record=True)

    activation = activate_role("all", cfg_manager, console)

    assert activation.resolved_key == "all"
    disabled = {
        name
        for name, cfg in cfg_manager.load_config().mcp_servers.items()
        if not cfg.enabled
    }
    assert not disabled
    assert set(activation.enabled_servers) == set(cfg_manager.load_config().mcp_servers.keys())


def test_activate_role_rejects_unknown_role():
    cfg_manager = _build_dummy_config()
    with pytest.raises(RoleNotFoundError):
        activate_role("unknown-role", cfg_manager)
