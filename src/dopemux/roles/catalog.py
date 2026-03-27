"""
Role catalog and activation helpers for Dopemux.

Provides a bridge between the historical MetaMCP role design and the newer
profile-based configuration system. Each role definition captures the intended
tool surface, ADHD attention state, and MetaMCP namespace so callers can apply
consistent behaviour across the CLI, tmux layouts, and Claude launcher.
"""

from __future__ import annotations
import logging


import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

from rich.console import Console

from ..config import ConfigManager
from ..voice import inject_voice_header, validate_or_fallback


logger = logging.getLogger(__name__)

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
    voice_header: Optional[str] = None

    def __post_init__(self) -> None:
        """Attach a validated Dopemux voice header to every role definition."""
        if self.voice_header:
            return
        object.__setattr__(
            self,
            "voice_header",
            build_role_voice_header(self.label, self.description, self.attention_state),
        )


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


def build_role_voice_header(label: str, description: str, attention_state: str) -> str:
    """Create a voice-safe role header for downstream prompt injection."""
    base_brief = (
        f"{label} mode. Mission: {description} "
        f"Attention profile: {attention_state}. Keep the server surface explicit."
    )
    fallback = (
        "[LIVE] Role brief blocked by the Dopemux voice gate. "
        "FACT: role metadata is available. UNKNOWN: safe role framing. "
        "TODO: restate the mission, attention profile, and server surface."
    )
    return validate_or_fallback(
        inject_voice_header(base_brief, surface="role"),
        surface="role",
        fallback=fallback,
    )


ROLE_CATALOG: Dict[str, RoleSpec] = {
    # ADHD scattered: quick wins only
    "quickfix": RoleSpec(
        key="quickfix",
        label="Quickfix",
        description="5-15 minute wins, minimal cognitive load.",
        attention_state="scattered",
        required_servers=["dopemux-conport", "dopemux-serena", "dopemux-pal"],
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
        required_servers=["dopemux-conport", "dopemux-serena", "dopemux-zen"],
        optional_servers=["dopemux-pal", "dopemux-desktop-commander"],
        metamcp_namespace="dopemux-act",
        profile_name="act",
    ),
    # Planning / architecture
    "plan": RoleSpec(
        key="plan",
        label="Plan",
        description="Strategic planning, architecture, ADR authoring.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-zen"],
        optional_servers=[
            "dopemux-pal",
            "dopemux-gpt-researcher",
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
        required_servers=["dopemux-conport", "dopemux-zen", "dopemux-pal"],
        optional_servers=[
            "dopemux-serena",
            "dopemux-gpt-researcher",
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
        required_servers=["dopemux-conport", "dopemux-serena", "dopemux-zen"],
        optional_servers=["dopemux-pal", "dopemux-desktop-commander"],
        metamcp_namespace="dopemux-act",
        profile_name="developer",
    ),
    "architect": RoleSpec(
        key="architect",
        label="Architect",
        description="High-level planning, architecture, and ADR authoring.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-zen", "dopemux-pal"],
        optional_servers=["dopemux-gpt-researcher", "dopemux-serena"],
        metamcp_namespace="dopemux-plan",
        profile_name="architect",
    ),
    "reviewer": RoleSpec(
        key="reviewer",
        label="Reviewer",
        description="Code review and decision verification workflows.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-serena", "dopemux-zen"],
        optional_servers=["dopemux-pal", "dopemux-gpt-researcher"],
        metamcp_namespace="dopemux-plan",
        profile_name="reviewer",
    ),
    "debugger": RoleSpec(
        key="debugger",
        label="Debugger",
        description="Targeted debugging and incident reproduction.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-serena", "dopemux-zen"],
        optional_servers=["dopemux-desktop-commander", "dopemux-pal"],
        metamcp_namespace="dopemux-act",
        profile_name="debugger",
    ),
    "ops": RoleSpec(
        key="ops",
        label="Ops",
        description="Operations, deployment, and runbook execution.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-desktop-commander"],
        optional_servers=["dopemux-zen", "dopemux-pal", "dopemux-serena"],
        metamcp_namespace="dopemux-act",
        profile_name="ops",
    ),
    "workflow-manager": RoleSpec(
        key="workflow-manager",
        label="Workflow Manager",
        description="Manager lane for phase-gated workflow orchestration and validation.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-serena", "dopemux-zen"],
        optional_servers=["dopemux-pal", "dopemux-desktop-commander"],
        metamcp_namespace="dopemux-workflow-manager",
        profile_name="workflow-manager",
        notes="Coordinates workflow state, delegates executor work, and validates checkpoints.",
    ),
    "workflow-executor": RoleSpec(
        key="workflow-executor",
        label="Workflow Executor",
        description="Executor lane for isolated workflow implementation tasks.",
        attention_state="focused",
        required_servers=["dopemux-conport", "dopemux-serena"],
        optional_servers=["dopemux-pal", "dopemux-zen", "dopemux-desktop-commander"],
        metamcp_namespace="dopemux-workflow-executor",
        profile_name="workflow-executor",
        notes="Executes one workflow task inside an isolated worktree or instance.",
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
    "manager": "workflow-manager",
    "executor": "workflow-executor",
    "workflow": "workflow-manager",
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

    # Always require dopemux-conport to preserve core memory functionality
    required.add("dopemux-conport")

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
    if spec.voice_header:
        os.environ["DOPEMUX_ROLE_VOICE_HEADER"] = spec.voice_header
    else:
        os.environ.pop("DOPEMUX_ROLE_VOICE_HEADER", None)

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
            f"[warning]⚠ Missing required MCP servers for role '{spec.label}': "
            f"{', '.join(activation.missing_required)}[/warning]"
        )
    if console and activation.missing_optional:
        console.print(
            f"[text.dim]ℹ Optional MCP servers unavailable for this role: "
            f"{', '.join(activation.missing_optional)}[/text.dim]"
        )

    return activation
