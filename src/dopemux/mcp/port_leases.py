"""Operational MCP port lease registry.

Path default: ~/.dopemux/mcp/runtime/port-leases.json
Override: DOPEMUX_MCP_PORT_LEASE_REGISTRY

Operational state only — never domain truth for ConPort / dope-memory / TO.
No secrets. Atomic writes. Tests must override the registry path.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCHEMA_VERSION = "1.0"
ALLOCATOR_VERSION = "1"
REGISTRY_ENV = "DOPEMUX_MCP_PORT_LEASE_REGISTRY"
DEFAULT_RELATIVE = Path(".dopemux/mcp/runtime/port-leases.json")


class LeaseRegistryError(RuntimeError):
    """Registry load/save failure that blocks allocation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_lease_registry_path() -> Path:
    override = os.environ.get(REGISTRY_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / DEFAULT_RELATIVE).resolve()


def empty_registry() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": _utc_now(),
        "allocator_version": ALLOCATOR_VERSION,
        "leases": [],
        "reserved_ports": [],
    }


def _slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return s[:48] or "x"


def make_lease_id(
    *,
    project_slug: str,
    worktree_hash: str,
    service: str,
    port_role: str,
    port: int,
) -> str:
    return f"lease_{_slug(project_slug)}_{worktree_hash}_{_slug(service)}_{_slug(port_role)}_{port}"


@dataclass
class PortLease:
    lease_id: str
    port: int
    protocol: str = "tcp"
    bind_host: str = "127.0.0.1"
    service: str = ""
    port_role: str = "http"
    port_var: str = ""
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_root: Optional[str] = None
    worktree_root: Optional[str] = None
    project_hash: Optional[str] = None
    worktree_hash: Optional[str] = None
    instance_id: Optional[str] = None
    scope: str = "worktree"  # project|worktree|singleton
    source: str = "dopemux mcp init"
    status: str = "active"  # active|stale|released|unknown
    preferred: bool = True
    reserved: bool = False
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    last_verified_at: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "port": int(self.port),
            "protocol": self.protocol,
            "bind_host": self.bind_host,
            "service": self.service,
            "port_role": self.port_role,
            "port_var": self.port_var,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "project_root": self.project_root,
            "worktree_root": self.worktree_root,
            "project_hash": self.project_hash,
            "worktree_hash": self.worktree_hash,
            "instance_id": self.instance_id,
            "scope": self.scope,
            "source": self.source,
            "status": self.status,
            "preferred": self.preferred,
            "reserved": self.reserved,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_verified_at": self.last_verified_at,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "PortLease":
        d = dict(raw)
        return cls(
            lease_id=str(d.get("lease_id") or ""),
            port=int(d["port"]),
            protocol=str(d.get("protocol") or "tcp"),
            bind_host=str(d.get("bind_host") or "127.0.0.1"),
            service=str(d.get("service") or ""),
            port_role=str(d.get("port_role") or "http"),
            port_var=str(d.get("port_var") or ""),
            project_id=d.get("project_id"),
            workspace_id=d.get("workspace_id"),
            project_root=d.get("project_root"),
            worktree_root=d.get("worktree_root"),
            project_hash=d.get("project_hash"),
            worktree_hash=d.get("worktree_hash"),
            instance_id=d.get("instance_id"),
            scope=str(d.get("scope") or "worktree"),
            source=str(d.get("source") or "unknown"),
            status=str(d.get("status") or "unknown"),
            preferred=bool(d.get("preferred", True)),
            reserved=bool(d.get("reserved", False)),
            created_at=str(d.get("created_at") or _utc_now()),
            updated_at=str(d.get("updated_at") or _utc_now()),
            last_verified_at=d.get("last_verified_at"),
            notes=list(d.get("notes") or []),
        )


@dataclass
class PortLeaseRegistry:
    """In-memory lease registry with atomic persistence."""

    path: Path
    data: Dict[str, Any] = field(default_factory=empty_registry)
    present: bool = False
    parse_status: str = "MISSING"  # OK | ERROR | MISSING
    error: Optional[str] = None

    @classmethod
    def load(cls, path: Optional[Path] = None, *, create_missing: bool = False) -> "PortLeaseRegistry":
        reg_path = path or default_lease_registry_path()
        if not reg_path.exists():
            if create_missing:
                reg_path.parent.mkdir(parents=True, exist_ok=True)
                reg = cls(path=reg_path, data=empty_registry(), present=False, parse_status="MISSING")
                reg.save()
                reg.present = True
                reg.parse_status = "OK"
                return reg
            return cls(path=reg_path, data=empty_registry(), present=False, parse_status="MISSING")

        try:
            raw = json.loads(reg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return cls(
                path=reg_path,
                data=empty_registry(),
                present=True,
                parse_status="ERROR",
                error=str(exc),
            )
        if not isinstance(raw, dict):
            return cls(
                path=reg_path,
                data=empty_registry(),
                present=True,
                parse_status="ERROR",
                error="registry root is not an object",
            )
        leases = raw.get("leases")
        if leases is None:
            leases = []
        if not isinstance(leases, list):
            return cls(
                path=reg_path,
                data=empty_registry(),
                present=True,
                parse_status="ERROR",
                error="registry leases is not a list",
            )
        data = dict(raw)
        data["leases"] = leases
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("allocator_version", ALLOCATOR_VERSION)
        data.setdefault("reserved_ports", [])
        data.setdefault("updated_at", _utc_now())
        return cls(path=reg_path, data=data, present=True, parse_status="OK")

    def require_writable(self) -> None:
        if self.parse_status == "ERROR":
            raise LeaseRegistryError(
                f"Lease registry parse failed at {self.path}: {self.error}. "
                "Allocation is blocked."
            )

    def leases(self) -> List[Dict[str, Any]]:
        return list(self.data.get("leases") or [])

    def active_leases(self) -> List[Dict[str, Any]]:
        return [L for L in self.leases() if L.get("status") == "active"]

    def reserved_ports(self) -> List[Dict[str, Any]]:
        return list(self.data.get("reserved_ports") or [])

    def set_reserved_from_catalog(self, reserved: Dict[int, str], *, source: str = "catalog") -> None:
        self.data["reserved_ports"] = [
            {"port": int(p), "service": name, "source": source, "reason": "singleton"}
            for p, name in sorted(reserved.items())
        ]

    def find_active_by_port(self, port: int) -> Optional[Dict[str, Any]]:
        for L in self.active_leases():
            if int(L.get("port") or 0) == int(port):
                return L
        return None

    def find_active_for_identity(
        self,
        *,
        service: str,
        port_role: str,
        worktree_root: Optional[str] = None,
        project_root: Optional[str] = None,
        worktree_hash: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        for L in self.active_leases():
            if L.get("service") != service or L.get("port_role") != port_role:
                continue
            if worktree_hash and L.get("worktree_hash") == worktree_hash:
                return L
            if worktree_root and L.get("worktree_root") == worktree_root:
                return L
            if project_root and L.get("project_root") == project_root and L.get("scope") == "project":
                return L
        return None

    def identity_matches(
        self,
        lease: Dict[str, Any],
        *,
        worktree_root: Optional[str],
        project_root: Optional[str],
        worktree_hash: Optional[str],
        project_id: Optional[str] = None,
    ) -> bool:
        # Project-scoped leases (e.g. task-orchestrator) are shared across worktrees
        # of the same project root.
        if lease.get("scope") == "project":
            if project_root and lease.get("project_root"):
                return lease.get("project_root") == project_root
            if project_id and lease.get("project_id"):
                return lease.get("project_id") == project_id
            return False

        if worktree_hash and lease.get("worktree_hash") and lease.get("worktree_hash") != worktree_hash:
            return False
        if worktree_root and lease.get("worktree_root") and lease.get("worktree_root") != worktree_root:
            return False
        if project_id and lease.get("project_id") and lease.get("project_id") != project_id:
            if worktree_root and lease.get("worktree_root") == worktree_root:
                return True
            return False
        return True

    def upsert_lease(self, lease: PortLease | Dict[str, Any]) -> Dict[str, Any]:
        entry = lease.to_dict() if isinstance(lease, PortLease) else dict(lease)
        entry["updated_at"] = _utc_now()
        leases = self.leases()
        out: List[Dict[str, Any]] = []
        replaced = False
        for L in leases:
            same_id = L.get("lease_id") and L.get("lease_id") == entry.get("lease_id")
            same_slot = (
                L.get("service") == entry.get("service")
                and L.get("port_role") == entry.get("port_role")
                and L.get("worktree_root") == entry.get("worktree_root")
                and L.get("status") == "active"
            )
            if same_id or same_slot:
                if not replaced:
                    # preserve created_at
                    entry.setdefault("created_at", L.get("created_at") or _utc_now())
                    out.append(entry)
                    replaced = True
                # drop old
                continue
            out.append(L)
        if not replaced:
            entry.setdefault("created_at", _utc_now())
            out.append(entry)
        self.data["leases"] = out
        self.data["updated_at"] = _utc_now()
        return entry

    def mark_released(
        self,
        *,
        service: Optional[str] = None,
        worktree_root: Optional[str] = None,
        port: Optional[int] = None,
        lease_id: Optional[str] = None,
    ) -> int:
        count = 0
        now = _utc_now()
        for L in self.leases():
            match = False
            if lease_id and L.get("lease_id") == lease_id:
                match = True
            if port is not None and int(L.get("port") or 0) == int(port):
                match = True
            if service and worktree_root:
                if L.get("service") == service and L.get("worktree_root") == worktree_root:
                    match = True
            if match and L.get("status") == "active":
                L["status"] = "released"
                L["updated_at"] = now
                count += 1
        if count:
            self.data["updated_at"] = now
        return count

    def mark_stale(self, lease_id: str) -> bool:
        for L in self.leases():
            if L.get("lease_id") == lease_id and L.get("status") == "active":
                L["status"] = "stale"
                L["updated_at"] = _utc_now()
                self.data["updated_at"] = _utc_now()
                return True
        return False

    def active_ports(self) -> Dict[int, Dict[str, Any]]:
        return {int(L["port"]): L for L in self.active_leases() if L.get("port") is not None}

    def save(self) -> None:
        self.require_writable()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = _utc_now()
        payload = json.dumps(self.data, indent=2, sort_keys=False) + "\n"
        # Atomic write via same-dir tempfile
        fd, tmp_name = tempfile.mkstemp(prefix=".port-leases.", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        self.present = True
        self.parse_status = "OK"

    def to_report_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "present": self.present,
            "parse_status": self.parse_status,
            "error": self.error,
            "active_lease_count": len(self.active_leases()),
            "lease_count": len(self.leases()),
            "allocator_version": self.data.get("allocator_version"),
            "schema_version": self.data.get("schema_version"),
        }
