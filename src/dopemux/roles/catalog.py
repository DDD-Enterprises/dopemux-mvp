"""
Role catalog and activation helpers for Dopemux.

Provides a bridge between the historical MetaMCP role design and the newer
profile-based configuration system. Each role definition captures the intended
tool surface, ADHD attention state, and MetaMCP namespace so callers can apply
consistent behaviour across the CLI, tmux layouts, and Claude launcher.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

from rich.console import Console

from ..config import ConfigManager


class RoleNotFoundError(ValueError):
    """Raised when a requested role is not defined in the catalog."""


@dataclass(frozen=True)
class RoleSpec:
    """Static description of a Dopemux role/persona."""

    key: str
    label: str
    description: str
    attention_state: str
    required_servers: List[str] = field(default_factory=list)
    optional_servers: List[str] = field(default_factory=list)
    metamcp_namespace: Optional[str] = None
    profile_name: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class RoleActivationResult:
    """Result of applying a role to the current session."""

    spec: RoleSpec
    resolved_key: str
    alias_used: Optional[str]
    enabled_servers: List[str]
    disabled_servers: List[str]
    missing_required: List[str]
    missing_optional: List[str]


ROLE_CATALOG: Dict[str, RoleSpec] = {
    # ADHD scattered: quick wins only
    "quickfix": RoleSpec(
        key="quickfix",
        label="Quickfix",
        description="5-15 minute wins, minimal cognitive load.",
        attention_state="scattered",
        required_servers=["conport", "serena", "context7"],
        optional_servers=[],
        metamcp_namespace="dopemux-quickfix",
        profile_name="quickfix",
    ),
    # Implementation / coding
    "act": RoleSpec(
        key="act",
        label="Act",
        description="Implementation, debugging, refactoring workflows.",
        attention_state="focused",
        required_servers=["conport", "serena", "zen"],
        optional_servers=["context7", "desktop-commander"],
        metamcp_namespace="dopemux-act",
        profile_name="act",
    ),
    # Planning / architecture
    "plan": RoleSpec(
        key="plan",
        label="Plan",
        description="Strategic planning, architecture, ADR authoring.",
        attention_state="focused",
        required_servers=["conport", "zen"],
        optional_servers=[
            "context7",
            "mas-sequential-thinking",
            "gptr-mcp",
            "exa",
        ],
        metamcp_namespace="dopemux-plan",
        profile_name="plan",
    ),
    # Deep research / investigation
    "research": RoleSpec(
        key="research",
        label="Research",
        description="Deep investigation, learning frameworks, exploration.",
        attention_state="focused",
        required_servers=["conport", "zen", "context7"],
        optional_servers=[
            "serena",
            "gptr-mcp",
            "exa",
        ],
        metamcp_namespace="dopemux-research",
        profile_name="research",
    ),
    # Full tool surface (exploration/mixed)
    "all": RoleSpec(
        key="all",
        label="All Tools",
        description="Full flexibility when you need every MCP server.",
        attention_state="variable",
        required_servers=[],
        optional_servers=[],
        metamcp_namespace="dopemux-all",
        profile_name="all",
    ),
    "developer": RoleSpec(
        key="developer",
        label="Developer",
        description="Core implementation and code authoring workflows.",
        attention_state="focused",
        required_servers=["conport", "serena", "zen"],
        optional_servers=["context7", "desktop-commander"],
        metamcp_namespace="dopemux-act",
        profile_name="developer",
    ),
    "architect": RoleSpec(
        key="architect",
        label="Architect",
        description="High-level planning, architecture, and ADR authoring.",
        attention_state="focused",
        required_servers=["conport", "zen", "context7"],
        optional_servers=["mas-sequential-thinking", "gptr-mcp", "exa", "serena"],
        metamcp_namespace="dopemux-plan",
        profile_name="architect",
    ),
    "reviewer": RoleSpec(
        key="reviewer",
        label="Reviewer",
        description="Code review and decision verification workflows.",
        attention_state="focused",
        required_servers=["conport", "serena", "zen"],
        optional_servers=["context7", "gptr-mcp"],
        metamcp_namespace="dopemux-plan",
        profile_name="reviewer",
    ),
    "debugger": RoleSpec(
        key="debugger",
        label="Debugger",
        description="Targeted debugging and incident reproduction.",
        attention_state="focused",
        required_servers=["conport", "serena", "zen"],
        optional_servers=["desktop-commander", "context7"],
        metamcp_namespace="dopemux-act",
        profile_name="debugger",
    ),
    "ops": RoleSpec(
        key="ops",
        label="Ops",
        description="Operations, deployment, and runbook execution.",
        attention_state="focused",
        required_servers=["conport", "desktop-commander"],
        optional_servers=["zen", "context7", "serena"],
        metamcp_namespace="dopemux-act",
        profile_name="ops",
    ),
}

# Aliases map common terminology to canonical roles
ROLE_ALIASES: Dict[str, str] = {
    # MetaMCP namespaces
    "dopemux-quickfix": "quickfix",
    "dopemux-act": "act",
    "dopemux-plan": "plan",
    "dopemux-research": "research",
    "dopemux-all": "all",
    # Human-friendly names
    "dev": "developer",
    "implementation": "developer",
    "coder": "developer",
    "planner": "plan",
    "strategist": "plan",
    "researcher": "research",
    "investigator": "research",
    "explorer": "research",
    # tmux agent roles
    "orchestrator": "plan",
    "agent": "act",
    "secondary": "quickfix",
}


def available_roles() -> List[str]:
    """Return canonical role keys in sorted order."""
    return sorted(ROLE_CATALOG.keys())


def resolve_role(role_name: str) -> RoleSpec:
    """Resolve a role or alias to its RoleSpec."""
    if not role_name:
        raise RoleNotFoundError("Role not specified")

    role_key = role_name.strip().lower()
    if role_key in ROLE_CATALOG:
        return ROLE_CATALOG[role_key]

    if role_key in ROLE_ALIASES:
        alias_key = ROLE_ALIASES[role_key]
        if alias_key in ROLE_CATALOG:
            return ROLE_CATALOG[alias_key]

    # Accept underscores/hyphen equivalence
    normalized = role_key.replace("_", "-")
    if normalized in ROLE_CATALOG:
        return ROLE_CATALOG[normalized]
    if normalized in ROLE_ALIASES:
        alias_key = ROLE_ALIASES[normalized]
        if alias_key in ROLE_CATALOG:
            return ROLE_CATALOG[alias_key]

    raise RoleNotFoundError(role_name)


def _apply_role_to_config(
    config_manager: ConfigManager,
    spec: RoleSpec,
) -> RoleActivationResult:
    """Apply role-specific MCP filtering to the cached Dopemux config."""
    config = config_manager.load_config()

    available_servers: Set[str] = set(config.mcp_servers.keys())

    required = set(spec.required_servers or [])
    optional = set(spec.optional_servers or [])

    # Always require conport to preserve core memory functionality
    required.add("conport")

    missing_required = sorted(s for s in required if s not in available_servers)
    missing_optional = sorted(s for s in optional if s not in available_servers)

    if spec.key == "all":
        enable_set = available_servers
    else:
        enable_set = (required & available_servers) | (optional & available_servers)

    previously_enabled = {
        name for name, server in config.mcp_servers.items() if server.enabled
    }

    for name, server in config.mcp_servers.items():
        server.enabled = name in enable_set if spec.key != "all" else True

    disabled = (
        sorted(previously_enabled - enable_set) if spec.key != "all" else []
    )
    enabled = sorted(enable_set if enable_set else [])

    return RoleActivationResult(
        spec=spec,
        resolved_key=spec.key,
        alias_used=None,
        enabled_servers=enabled,
        disabled_servers=disabled,
        missing_required=missing_required,
        missing_optional=missing_optional,
    )


def activate_role(
    role_name: str,
    config_manager: ConfigManager,
    console: Optional[Console] = None,
) -> RoleActivationResult:
    """
    Activate a role for the current Dopemux session.

    Sets environment variables, filters MCP servers, and returns the activation
    summary so callers can surface friendly messaging.
    """
    alias_used: Optional[str] = None
    try:
        spec = resolve_role(role_name)
    except RoleNotFoundError as exc:
        raise RoleNotFoundError(str(exc)) from exc

    canonical_key = spec.key
    if role_name.strip().lower() != canonical_key:
        alias_used = role_name.strip()

    activation = _apply_role_to_config(config_manager, spec)
    activation.alias_used = alias_used

    # Environment variables for downstream components
    os.environ["DOPEMUX_AGENT_ROLE"] = canonical_key
    os.environ["DOPEMUX_ACTIVE_ROLE"] = spec.label
    os.environ["DOPEMUX_ROLE_ATTENTION_STATE"] = spec.attention_state
    os.environ["DOPEMUX_ROLE_DESCRIPTION"] = spec.description

    if spec.profile_name:
        os.environ["DOPEMUX_ACTIVE_PROFILE"] = spec.profile_name
    else:
        os.environ.pop("DOPEMUX_ACTIVE_PROFILE", None)

    if spec.metamcp_namespace:
        os.environ["DOPEMUX_METAMCP_NAMESPACE"] = spec.metamcp_namespace
    else:
        os.environ.pop("DOPEMUX_METAMCP_NAMESPACE", None)

    # Provide gentle feedback if a role requires servers that are missing
    if console and activation.missing_required:
        console.print(
            f"[yellow]⚠ Missing required MCP servers for role '{spec.label}': "
            f"{', '.join(activation.missing_required)}[/yellow]"
        )
    if console and activation.missing_optional:
        console.print(
            f"[dim]ℹ Optional MCP servers unavailable for this role: "
            f"{', '.join(activation.missing_optional)}[/dim]"
        )

    return activation
