"""Registry-issued MCP project/workspace/instance identity (P1 fleet control plane).

Path default: ``~/.dopemux/mcp/registry/identity.json``
Override: ``DOPEMUX_MCP_IDENTITY_REGISTRY``

Canonical ``project_id``/``workspace_id``/``instance_id`` are issued only by
explicit ``register_project``/``register_workspace``/``register_instance`` calls.
Filesystem path, git common-dir, origin, cwd, environment, port, container,
MCP session/process identity, and clientInfo are never authoritative and never
auto-create a record here -- see ``identity.py``'s resolver and
``docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`` S2.

This registry is operational control-plane authority only. It does not become
ConPort, dope-memory, Task Orchestrator, Leantime, DCP, or repository domain
authority.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "dopemux.mcp.identity-registry.v1"
REGISTRY_ENV = "DOPEMUX_MCP_IDENTITY_REGISTRY"
DEFAULT_RELATIVE = Path(".dopemux/mcp/registry/identity.json")


class IdentityRegistryError(RuntimeError):
    """Raised when the identity registry cannot be loaded, is corrupt, or a
    mutation would violate registry invariants. Callers must treat this as a
    fail-closed signal, never a reason to synthesize an identity."""


def default_registry_path() -> Path:
    override = os.environ.get(REGISTRY_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / DEFAULT_RELATIVE).resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _empty_registry() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generation": 0,
        "updated_at": _utc_now(),
        "projects": {},
    }


def _normalize_alias(kind: str, value: str) -> Dict[str, str]:
    if not kind or not kind.strip():
        raise IdentityRegistryError("alias kind must be non-empty")
    if not value or not value.strip():
        raise IdentityRegistryError("alias value must be non-empty")
    return {"kind": kind, "value": value}


@dataclass
class IdentityRegistry:
    """In-memory identity registry with atomic, generation-versioned persistence.

    Generation increments by one on every successful mutation (register_*,
    add_alias). Downstream consumers (service leases, ownership evidence) bind
    the generation they resolved against and must reject a mismatch as stale.
    """

    path: Path
    data: Dict[str, Any] = field(default_factory=_empty_registry)
    present: bool = False
    parse_status: str = "MISSING"  # OK | ERROR | MISSING
    error: Optional[str] = None

    # ---- loading -----------------------------------------------------

    @classmethod
    def load(cls, path: Optional[Path] = None, *, create_missing: bool = False) -> "IdentityRegistry":
        """Load the registry. Production ``load(create_missing=False)`` is
        read-only when the file is absent -- it never bootstraps a registry
        from path/env evidence. Tests must inject ``tmp_path`` explicitly and
        never touch the real home registry."""

        reg_path = Path(path) if path is not None else default_registry_path()
        if not reg_path.exists():
            if create_missing:
                reg_path.parent.mkdir(parents=True, exist_ok=True)
                reg = cls(path=reg_path, data=_empty_registry(), present=False, parse_status="MISSING")
                reg._persist()
                reg.present = True
                reg.parse_status = "OK"
                return reg
            return cls(path=reg_path, data=_empty_registry(), present=False, parse_status="MISSING")

        try:
            raw = json.loads(reg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return cls(path=reg_path, data=_empty_registry(), present=True, parse_status="ERROR", error=str(exc))

        if not isinstance(raw, dict) or not isinstance(raw.get("projects"), dict):
            return cls(
                path=reg_path,
                data=_empty_registry(),
                present=True,
                parse_status="ERROR",
                error="identity registry root malformed: expected object with a 'projects' mapping",
            )
        data = dict(raw)
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("generation", 0)
        data.setdefault("updated_at", _utc_now())
        return cls(path=reg_path, data=data, present=True, parse_status="OK")

    def _require_writable(self) -> None:
        if self.parse_status == "ERROR":
            raise IdentityRegistryError(
                f"Identity registry parse failed at {self.path}: {self.error}. "
                "Mutation is blocked; inspect or relocate the file rather than overwrite it."
            )

    # ---- persistence -------------------------------------------------

    def _persist(self) -> None:
        """Atomic write: temp file in the same directory, fsync, os.replace,
        parent-directory fsync. Does not touch ``generation`` -- callers bump
        it before calling this."""

        self._require_writable()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = _utc_now()
        self.data.setdefault("schema_version", SCHEMA_VERSION)
        text = json.dumps(self.data, indent=2, sort_keys=True) + "\n"
        fd, tmp_name = tempfile.mkstemp(prefix=".identity.", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
            dir_fd = os.open(str(self.path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        self.present = True
        self.parse_status = "OK"
        self.error = None

    def _bump_and_persist(self) -> None:
        self.data["generation"] = int(self.data.get("generation", 0)) + 1
        self._persist()

    @property
    def generation(self) -> int:
        return int(self.data.get("generation", 0))

    # ---- registration (the only way an ID is ever issued) -------------

    def register_project(self, *, aliases: List[Dict[str, str]]) -> str:
        self._require_writable()
        project_id = _new_id("prj")
        self.data["projects"][project_id] = {
            "project_id": project_id,
            "aliases": [_normalize_alias(a["kind"], a["value"]) for a in aliases],
            "workspaces": {},
        }
        self._bump_and_persist()
        return project_id

    def register_workspace(self, *, project_id: str, aliases: List[Dict[str, str]]) -> str:
        self._require_writable()
        project = self.data["projects"].get(project_id)
        if project is None:
            raise IdentityRegistryError(f"unknown project_id: {project_id}")
        workspace_id = _new_id("ws")
        project["workspaces"][workspace_id] = {
            "workspace_id": workspace_id,
            "aliases": [_normalize_alias(a["kind"], a["value"]) for a in aliases],
            "instances": {},
        }
        self._bump_and_persist()
        return workspace_id

    def register_instance(self, *, project_id: str, workspace_id: str, aliases: List[Dict[str, str]]) -> str:
        self._require_writable()
        project = self.data["projects"].get(project_id)
        if project is None:
            raise IdentityRegistryError(f"unknown project_id: {project_id}")
        workspace = project["workspaces"].get(workspace_id)
        if workspace is None:
            raise IdentityRegistryError(f"unknown workspace_id: {workspace_id} for project {project_id}")
        instance_id = _new_id("inst")
        workspace["instances"][instance_id] = {
            "instance_id": instance_id,
            "aliases": [_normalize_alias(a["kind"], a["value"]) for a in aliases],
        }
        self._bump_and_persist()
        return instance_id

    def add_alias(
        self,
        *,
        kind: str,
        value: str,
        project_id: str,
        workspace_id: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> None:
        """Attach an additional EVIDENCE_ONLY alias to an already-registered
        record, e.g. after a worktree relocation. Never creates a new record
        and never overwrites the target's persistent ID."""

        self._require_writable()
        project = self.data["projects"].get(project_id)
        if project is None:
            raise IdentityRegistryError(f"unknown project_id: {project_id}")
        alias = _normalize_alias(kind, value)

        if workspace_id is None and instance_id is None:
            project["aliases"].append(alias)
            self._bump_and_persist()
            return

        workspace = project["workspaces"].get(workspace_id) if workspace_id else None
        if workspace_id is not None and workspace is None:
            raise IdentityRegistryError(f"unknown workspace_id: {workspace_id} for project {project_id}")

        if instance_id is None:
            workspace["aliases"].append(alias)
            self._bump_and_persist()
            return

        if workspace is None:
            raise IdentityRegistryError("instance-level alias requires workspace_id")
        instance = workspace["instances"].get(instance_id)
        if instance is None:
            raise IdentityRegistryError(f"unknown instance_id: {instance_id}")
        instance["aliases"].append(alias)
        self._bump_and_persist()

    # ---- read-only lookups (consumed by identity.py's resolver) -------

    def find_alias_matches(self, *, kind: str, value: str) -> List[Dict[str, Optional[str]]]:
        """Every registered record whose alias matches ``(kind, value)``
        exactly. Each match reports ``project_id`` and, when the alias was
        registered at that granularity, ``workspace_id``/``instance_id``.
        Matches spanning more than one distinct ``project_id`` are an alias
        collision the caller must treat as CONFLICTING, never as a tie-break."""

        matches: List[Dict[str, Optional[str]]] = []
        for project_id, project in self.data.get("projects", {}).items():
            for alias in project.get("aliases", []):
                if alias.get("kind") == kind and alias.get("value") == value:
                    matches.append({"project_id": project_id, "workspace_id": None, "instance_id": None})
            for workspace_id, workspace in project.get("workspaces", {}).items():
                for alias in workspace.get("aliases", []):
                    if alias.get("kind") == kind and alias.get("value") == value:
                        matches.append(
                            {"project_id": project_id, "workspace_id": workspace_id, "instance_id": None}
                        )
                for instance_id, instance in workspace.get("instances", {}).items():
                    for alias in instance.get("aliases", []):
                        if alias.get("kind") == kind and alias.get("value") == value:
                            matches.append(
                                {
                                    "project_id": project_id,
                                    "workspace_id": workspace_id,
                                    "instance_id": instance_id,
                                }
                            )
        return matches

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.data.get("projects", {}).get(project_id)

    def get_workspace(self, project_id: str, workspace_id: str) -> Optional[Dict[str, Any]]:
        project = self.get_project(project_id)
        if project is None:
            return None
        return project.get("workspaces", {}).get(workspace_id)

    def get_instance(self, project_id: str, workspace_id: str, instance_id: str) -> Optional[Dict[str, Any]]:
        workspace = self.get_workspace(project_id, workspace_id)
        if workspace is None:
            return None
        return workspace.get("instances", {}).get(instance_id)
