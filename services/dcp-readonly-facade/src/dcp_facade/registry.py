"""Project registry loader + validator.

The registry is the facade's trust boundary (see
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md).
It maps a caller-facing ``project_id`` to a workspace path, an exposure switch,
an identity block (matched against the workspace ``.repo_id``), and per-backend
service profiles.

Loading is **fail-closed**: a malformed project entry is dropped (recorded in
``warnings``) rather than exposed loosely; ``enabled`` defaults to ``False``.
No secrets are read from or written to the repo by this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

KNOWN_PROFILES = ("conport", "dope_memory", "dope_context", "task_orchestrator")

ENV_REGISTRY_PATH = "DCP_FACADE_REGISTRY"
DEFAULT_REGISTRY_PATH = "~/.dopemux/dcp-facade-registry.yaml"


@dataclass(frozen=True)
class Project:
    project_id: str
    workspace_path: str
    enabled: bool
    identity_project: str
    identity_owner: Optional[str]
    service_profiles: dict[str, Any] = field(default_factory=dict)

    def configured_capabilities(self) -> dict[str, bool]:
        """Which known backends have a profile configured (not reachability)."""
        return {name: name in self.service_profiles for name in KNOWN_PROFILES}


@dataclass
class Registry:
    projects: dict[str, Project] = field(default_factory=dict)
    approved_roots: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def get(self, project_id: str) -> Optional[Project]:
        return self.projects.get(project_id)

    def enabled_projects(self) -> list[Project]:
        return [p for p in self.projects.values() if p.enabled]


def resolve_registry_path(explicit: Optional[str] = None) -> Path:
    """Resolve the registry file path: explicit arg > env > default (~)."""
    raw = explicit or os.getenv(ENV_REGISTRY_PATH) or DEFAULT_REGISTRY_PATH
    return Path(raw).expanduser()


def _coerce_project(raw: Any) -> tuple[Optional[Project], Optional[str]]:
    """Validate one raw entry. Returns (project, None) or (None, reason)."""
    if not isinstance(raw, dict):
        return None, f"entry is not a mapping: {raw!r}"
    pid = raw.get("project_id")
    if not isinstance(pid, str) or not pid:
        return None, f"missing/invalid project_id: {raw!r}"
    workspace_path = raw.get("workspace_path")
    if not isinstance(workspace_path, str) or not workspace_path:
        return None, f"[{pid}] missing/invalid workspace_path"
    identity = raw.get("identity")
    if not isinstance(identity, dict):
        return None, f"[{pid}] missing identity block"
    identity_project = identity.get("project")
    if not isinstance(identity_project, str) or not identity_project:
        return None, f"[{pid}] identity.project is required"
    identity_owner = identity.get("owner")
    if identity_owner is not None and not isinstance(identity_owner, str):
        return None, f"[{pid}] identity.owner must be a string when present"
    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        return None, f"[{pid}] enabled must be a boolean"
    profiles = raw.get("service_profiles", {}) or {}
    if not isinstance(profiles, dict):
        return None, f"[{pid}] service_profiles must be a mapping"
    return (
        Project(
            project_id=pid,
            workspace_path=workspace_path,
            enabled=enabled,
            identity_project=identity_project,
            identity_owner=identity_owner,
            service_profiles=profiles,
        ),
        None,
    )


def parse_registry(doc: Any) -> Registry:
    """Build a Registry from an already-parsed YAML document (fail-closed)."""
    reg = Registry()
    if not isinstance(doc, dict):
        reg.warnings.append("registry root is not a mapping; treating as empty")
        return reg
    roots = doc.get("approved_roots", []) or []
    if isinstance(roots, list):
        reg.approved_roots = [str(r) for r in roots if isinstance(r, str)]
    else:
        reg.warnings.append("approved_roots is not a list; ignored")
    projects = doc.get("projects", []) or []
    if not isinstance(projects, list):
        reg.warnings.append("projects is not a list; treating as empty")
        projects = []
    for raw in projects:
        project, reason = _coerce_project(raw)
        if project is None:
            reg.warnings.append(f"dropped project entry ({reason})")
            continue
        if project.project_id in reg.projects:
            reg.warnings.append(f"duplicate project_id {project.project_id}; later entry dropped")
            continue
        reg.projects[project.project_id] = project
    return reg


def load_registry(path: Optional[str] = None) -> Registry:
    """Load + validate the registry from disk (read-only). Missing file → empty."""
    p = resolve_registry_path(path)
    if not p.is_file():
        reg = Registry()
        reg.warnings.append(f"registry file not found: {p}")
        return reg
    with p.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return parse_registry(doc)
