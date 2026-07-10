"""Exposure target registry v2 loader + validator (TP-DCP-MCP-RO-0010).

Registry v2 evolves the v1 project-keyed registry (``registry.py``) into the
ADR-DCP-MCP-RO-0009 opaque-``target_id`` contract: ``target_id`` is the ONLY
caller-facing handle, service families are limited to the exact 9 ADR-0009
families (the bare name ``task-orchestrator`` is forbidden), and every
service family carries a static ``(resolution_class, chatgpt_posture)`` pair
from the ADR's policy table rather than a caller-visible free-form profile.

Loading is **fail-closed**, mirroring ``registry.py``: a malformed target
entry is dropped (recorded in ``warnings``) rather than exposed loosely;
``enabled`` defaults to ``False``. A v1-shaped document (``projects`` /
``project_id``) is NEVER silently coerced into v2 — it fails closed with an
actionable migration warning (see ``docs/03-reference/dcp/chatgpt-mcp-readonly/
REGISTRY_V2_CONTRACT.md``).

This module is pure: it makes no outbound network calls, opens no listening
or connecting ports, spawns no external processes, and inspects no container
runtime. ``load_registry_v2`` performs a single read-only file read.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

# Exactly the 9 ADR-DCP-MCP-RO-0009 service families. The bare unqualified
# name "task-orchestrator" is FORBIDDEN in registry v2 (ADR §"Required
# Service Families"); to_mcp_wrapper / to_compose_rest are its two split
# family identifiers.
ALLOWED_SERVICE_FAMILIES: tuple[str, ...] = (
    "conport",
    "dope_memory",
    "to_compose_rest",
    "to_mcp_wrapper",
    "dope_context",
    "serena",
    "pal",
    "docker_mcp_gateway",
    "desktop_commander",
)

# Names that must never be accepted as a service family key, even though they
# resemble a legitimate family (ADR §"Required Service Families").
FORBIDDEN_FAMILY_NAMES: tuple[str, ...] = ("task-orchestrator",)

# Static per-family policy table: family -> (resolution_class, chatgpt_posture).
# Sourced verbatim from ADR-DCP-MCP-RO-0009 §"Required Resolution Classes".
# This table is DATA ONLY — it encodes no live/callable knowledge (that
# remains UNKNOWN in this packet; see capability.py).
FAMILY_POLICY_TABLE: dict[str, tuple[str, str]] = {
    "conport": ("per_worktree_runtime", "conditional_read_only"),
    "dope_memory": ("per_worktree_runtime", "conditional_read_only"),
    "to_compose_rest": ("host_singleton_project_routed", "conditional_get_only"),
    "to_mcp_wrapper": ("host_singleton_single_active_project", "blocked"),
    "dope_context": ("singleton_per_call_workspace", "blocked_until_read_bridge"),
    "serena": ("singleton_per_call_workspace", "blocked_until_inventory"),
    "pal": ("host_singleton", "blocked"),
    "docker_mcp_gateway": ("host_singleton", "blocked"),
    "desktop_commander": ("host_singleton", "blocked"),
}

# Default (and, in this packet, only supported) worktree exposure binding
# mode (ADR §"Default Worktree Exposure Policy"). A target binds to exactly
# one operator-approved workspace; other values are rejected fail-closed.
DEFAULT_BINDING_MODE = "PRIMARY_CHECKOUT_ONLY"

ENV_REGISTRY_PATH = "DCP_FACADE_REGISTRY_V2"
DEFAULT_REGISTRY_PATH = "~/.dopemux/dcp-facade-registry-v2.yaml"


@dataclass(frozen=True)
class ServicePolicy:
    """A service family bound to its static ADR policy plus registry consent.

    ``configured`` is True iff the family is declared in the target's
    ``service_policies`` AND that entry declares ``enabled: true`` — i.e.
    "configured" per the ADR's capability-state separation. It never implies
    discovered/live/callable (see capability.py).
    """

    family: str
    configured: bool
    resolution_class: str
    chatgpt_posture: str


@dataclass(frozen=True)
class ExposureTarget:
    target_id: str
    workspace_path: str
    enabled: bool
    binding_mode: str
    identity_project: str
    identity_owner: Optional[str]
    service_policies: dict[str, ServicePolicy] = field(default_factory=dict)


@dataclass
class RegistryV2:
    targets: dict[str, ExposureTarget] = field(default_factory=dict)
    approved_roots: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generation: str = ""

    def get(self, target_id: str) -> Optional[ExposureTarget]:
        return self.targets.get(target_id)

    def enabled_targets(self) -> list[ExposureTarget]:
        return [t for t in self.targets.values() if t.enabled]


def resolve_registry_path(explicit: Optional[str] = None) -> Path:
    """Resolve the registry v2 file path: explicit arg > env > default (~)."""
    raw = explicit or os.getenv(ENV_REGISTRY_PATH) or DEFAULT_REGISTRY_PATH
    return Path(raw).expanduser()


def _generation(doc: Any) -> str:
    """Deterministic content-hash generation id — NO timestamps/randomness."""
    canonical = json.dumps(doc, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _coerce_service_policies(
    raw: Any,
) -> tuple[Optional[dict[str, ServicePolicy]], Optional[str]]:
    """Validate a target's raw ``service_policies`` mapping.

    Returns (policies, None) or (None, reason). An absent/empty mapping is
    valid (a target may declare no families). Any forbidden or unknown
    family name, or a malformed per-family entry, invalidates the WHOLE
    target (fail-closed at the target level, not a silent per-family drop).
    """
    if raw is None:
        return {}, None
    if not isinstance(raw, dict):
        return None, "service_policies must be a mapping"

    result: dict[str, ServicePolicy] = {}
    for family, policy_raw in raw.items():
        if not isinstance(family, str):
            return None, f"service family key must be a string: {family!r}"
        if family in FORBIDDEN_FAMILY_NAMES:
            return None, f"forbidden service family 'task-orchestrator': {family!r}"
        if family not in ALLOWED_SERVICE_FAMILIES:
            return None, f"unknown service family: {family!r}"
        if policy_raw is None:
            policy_raw = {}
        if not isinstance(policy_raw, dict):
            return None, f"service_policies[{family}] must be a mapping"
        enabled = policy_raw.get("enabled", False)
        if not isinstance(enabled, bool):
            return None, f"service_policies[{family}].enabled must be a boolean"
        resolution_class, chatgpt_posture = FAMILY_POLICY_TABLE[family]
        result[family] = ServicePolicy(
            family=family,
            configured=enabled,
            resolution_class=resolution_class,
            chatgpt_posture=chatgpt_posture,
        )
    return result, None


def _coerce_target(raw: Any) -> tuple[Optional[ExposureTarget], Optional[str]]:
    """Validate one raw v2 target entry. Returns (target, None) or (None, reason)."""
    if not isinstance(raw, dict):
        return None, f"entry is not a mapping: {raw!r}"

    tid = raw.get("target_id")
    if not isinstance(tid, str) or not tid:
        return None, f"missing/invalid target_id: {raw!r}"

    workspace_path = raw.get("workspace_path")
    if not isinstance(workspace_path, str) or not workspace_path:
        return None, f"[{tid}] missing/invalid workspace_path"

    binding_mode = raw.get("binding_mode", DEFAULT_BINDING_MODE)
    if not isinstance(binding_mode, str) or binding_mode != DEFAULT_BINDING_MODE:
        return None, f"[{tid}] unsupported binding_mode: {binding_mode!r}"

    identity = raw.get("identity")
    if not isinstance(identity, dict):
        return None, f"[{tid}] missing identity block"
    identity_project = identity.get("project")
    if not isinstance(identity_project, str) or not identity_project:
        return None, f"[{tid}] identity.project is required"
    identity_owner = identity.get("owner")
    if identity_owner is not None and not isinstance(identity_owner, str):
        return None, f"[{tid}] identity.owner must be a string when present"

    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        return None, f"[{tid}] enabled must be a boolean"

    policies, reason = _coerce_service_policies(raw.get("service_policies"))
    if reason is not None:
        return None, f"[{tid}] {reason}"

    return (
        ExposureTarget(
            target_id=tid,
            workspace_path=workspace_path,
            enabled=enabled,
            binding_mode=binding_mode,
            identity_project=identity_project,
            identity_owner=identity_owner,
            service_policies=policies or {},
        ),
        None,
    )


def parse_registry_v2(doc: Any) -> RegistryV2:
    """Build a RegistryV2 from an already-parsed YAML document (fail-closed).

    A v1-shaped document (top-level ``projects`` list, no ``targets`` key) is
    NEVER silently coerced: it fails closed with an actionable migration
    warning pointing at ``target_id``/registry v2.
    """
    reg = RegistryV2()
    if not isinstance(doc, dict):
        reg.warnings.append("registry root is not a mapping; treating as empty")
        reg.generation = _generation(doc if isinstance(doc, (dict, list)) else None)
        return reg

    if "targets" not in doc and "projects" in doc:
        reg.warnings.append(
            "registry appears to be v1-shaped (top-level 'projects' with "
            "'project_id' entries); registry v2 requires 'targets' with "
            "'target_id' entries — migrate before loading (see "
            "docs/03-reference/dcp/chatgpt-mcp-readonly/REGISTRY_V2_CONTRACT.md); "
            "registry NOT loaded (fail-closed)"
        )
        reg.generation = _generation(doc)
        return reg

    roots = doc.get("approved_roots", []) or []
    if isinstance(roots, list):
        reg.approved_roots = [str(r) for r in roots if isinstance(r, str)]
    else:
        reg.warnings.append("approved_roots is not a list; ignored")

    targets = doc.get("targets", []) or []
    if not isinstance(targets, list):
        reg.warnings.append("targets is not a list; treating as empty")
        targets = []

    for raw in targets:
        target, reason = _coerce_target(raw)
        if target is None:
            reg.warnings.append(f"dropped target entry ({reason})")
            continue
        if target.target_id in reg.targets:
            reg.warnings.append(
                f"duplicate target_id {target.target_id}; later entry dropped"
            )
            continue
        reg.targets[target.target_id] = target

    reg.generation = _generation(doc)
    return reg


def load_registry_v2(path: Optional[str] = None) -> RegistryV2:
    """Load + validate the registry v2 file from disk (read-only).

    A missing file yields an empty registry with a recorded warning — the
    same fail-closed behavior as ``registry.load_registry``.
    """
    p = resolve_registry_path(path)
    if not p.is_file():
        reg = RegistryV2()
        reg.warnings.append(f"registry file not found: {p}")
        reg.generation = _generation(None)
        return reg
    with p.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return parse_registry_v2(doc)
