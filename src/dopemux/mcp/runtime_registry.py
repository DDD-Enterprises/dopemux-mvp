"""Operational MCP runtime registry (read/write).

Path default: ~/.dopemux/mcp/runtime/instances.json
Override: DOPEMUX_MCP_RUNTIME_REGISTRY

Registry is operational state only — never domain truth for ConPort,
dope-memory, or task-orchestrator.
"""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Sequence

SCHEMA_VERSION = "1.0"
REGISTRY_ENV = "DOPEMUX_MCP_RUNTIME_REGISTRY"
DEFAULT_RELATIVE = Path(".dopemux/mcp/runtime/instances.json")


class RegistryError(RuntimeError):
    """Registry load/save failure that must block mutations."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_registry_path() -> Path:
    override = os.environ.get(REGISTRY_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / DEFAULT_RELATIVE).resolve()


def empty_registry() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": _utc_now(),
        "instances": [],
    }


@dataclass
class RuntimeRegistry:
    """In-memory registry with atomic persistence."""

    path: Path
    data: Dict[str, Any] = field(default_factory=empty_registry)
    present: bool = False
    parse_status: str = "MISSING"  # OK | ERROR | MISSING
    error: Optional[str] = None

    @classmethod
    def load(cls, path: Optional[Path] = None, *, create_missing: bool = False) -> "RuntimeRegistry":
        reg_path = path or default_registry_path()
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
        if "instances" not in raw or not isinstance(raw.get("instances"), list):
            return cls(
                path=reg_path,
                data=empty_registry(),
                present=True,
                parse_status="ERROR",
                error="registry missing instances list",
            )
        # Preserve unknown top-level fields
        data = dict(raw)
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("updated_at", _utc_now())
        return cls(path=reg_path, data=data, present=True, parse_status="OK")

    def require_writable(self) -> None:
        if self.parse_status == "ERROR":
            raise RegistryError(
                f"Registry parse failed at {self.path}: {self.error}. "
                "Inspect the file; lifecycle mutation is blocked."
            )

    def instances(self) -> List[Dict[str, Any]]:
        return list(self.data.get("instances") or [])

    def find(
        self,
        *,
        project_id: Optional[str] = None,
        worktree_root: Optional[str] = None,
        service: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        out = []
        for inst in self.instances():
            if instance_id and inst.get("instance_id") != instance_id:
                continue
            if project_id and inst.get("project_id") != project_id:
                continue
            if worktree_root and str(inst.get("worktree_root") or "").rstrip("/") != str(
                worktree_root
            ).rstrip("/"):
                continue
            if service and inst.get("service") != service:
                continue
            out.append(inst)
        return out

    def upsert_instance(self, instance: Dict[str, Any]) -> None:
        self.require_writable()
        iid = instance.get("instance_id")
        if not iid:
            raise RegistryError("instance_id required")
        instances = list(self.data.get("instances") or [])
        replaced = False
        for i, existing in enumerate(instances):
            if existing.get("instance_id") == iid:
                merged = dict(existing)
                merged.update(instance)
                # Preserve unknown keys from existing that we didn't touch
                instances[i] = merged
                replaced = True
                break
        if not replaced:
            instances.append(dict(instance))
        self.data["instances"] = instances
        self.data["updated_at"] = _utc_now()

    def mark_stopped(
        self,
        *,
        project_id: str,
        service: Optional[str] = None,
        worktree_root: Optional[str] = None,
    ) -> int:
        self.require_writable()
        count = 0
        now = _utc_now()
        for inst in self.instances():
            if inst.get("project_id") != project_id:
                continue
            if worktree_root and str(inst.get("worktree_root") or "").rstrip("/") != str(
                worktree_root
            ).rstrip("/"):
                continue
            if service and inst.get("service") != service:
                continue
            inst["status"] = "stopped"
            inst["updated_at"] = now
            count += 1
        self.data["updated_at"] = now
        return count

    def prune_stale_dry_run(self, known_instance_ids: Sequence[str]) -> List[str]:
        """Return instance_ids that would be pruned (dry-run only)."""
        known = set(known_instance_ids)
        return [
            str(i.get("instance_id"))
            for i in self.instances()
            if i.get("instance_id") and i.get("instance_id") not in known
        ]

    def find_stale_running(self, running_container_names: Collection[str]) -> List[Dict[str, Any]]:
        """Return `running` instances none of whose containers are currently running.

        An instance with no recorded container_names counts as stale. Read-only.
        """
        running = set(running_container_names)
        stale: List[Dict[str, Any]] = []
        for inst in self.instances():
            if inst.get("status") != "running":
                continue
            names = inst.get("container_names") or []
            if not any(name in running for name in names):
                stale.append(inst)
        return stale

    def reconcile_stale_running(
        self,
        running_container_names: Collection[str],
        *,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Mark stale `running` instances as `stopped` (never deletes entries).

        Dry-run (or nothing stale) writes nothing. Otherwise the registry file is
        copied to `<path>.backup-<UTC stamp>` before the atomic save. Callers must
        not run this concurrently with other lifecycle commands: save() rewrites
        the whole file without a cross-process lock.
        """
        self.require_writable()
        stale = self.find_stale_running(running_container_names)
        plan: Dict[str, Any] = {
            "dry_run": dry_run,
            "stale_count": len(stale),
            "stale": [
                {
                    "instance_id": inst.get("instance_id"),
                    "service": inst.get("service"),
                    "project_root": inst.get("project_root"),
                    "worktree_root": inst.get("worktree_root"),
                    "container_names": list(inst.get("container_names") or []),
                    "updated_at": inst.get("updated_at"),
                }
                for inst in stale
            ],
            "backup_path": None,
            "applied": False,
        }
        if dry_run or not stale:
            return plan

        if self.path.exists():
            stamp = _utc_now().replace(":", "").replace("-", "")
            backup = self.path.with_suffix(self.path.suffix + f".backup-{stamp}")
            backup.write_bytes(self.path.read_bytes())
            plan["backup_path"] = str(backup)

        now = _utc_now()
        for inst in stale:
            inst["status"] = "stopped"
            inst["updated_at"] = now
            inst["last_probe"] = {
                "status": "NOT_RUNNING",
                "checked_at": now,
                "source": "mcp registry reconcile",
            }
        self.save()
        plan["applied"] = True
        return plan

    def save(self) -> None:
        self.require_writable()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = deepcopy(self.data)
        payload["updated_at"] = _utc_now()
        payload.setdefault("schema_version", SCHEMA_VERSION)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        fd, tmp_name = tempfile.mkstemp(
            prefix=".instances.",
            suffix=".tmp",
            dir=str(self.path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        self.data = payload
        self.present = True
        self.parse_status = "OK"
        self.error = None

    def to_report_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "present": self.present,
            "parse_status": self.parse_status,
            "error": self.error,
            "instances": self.instances(),
        }


def build_instance_record(
    *,
    instance_id: str,
    project_id: str,
    workspace_id: str,
    project_root: str,
    worktree_root: str,
    worktree_hash: str,
    project_hash: str,
    service: str,
    scope: str,
    status: str,
    ports: Dict[str, int],
    urls: Dict[str, str],
    container_names: List[str],
    compose_project_name: str,
    labels: Dict[str, str],
    last_start: Optional[Dict[str, Any]] = None,
    last_probe: Optional[Dict[str, Any]] = None,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    now = _utc_now()
    return {
        "instance_id": instance_id,
        "project_id": project_id,
        "workspace_id": workspace_id,
        "project_root": project_root,
        "worktree_root": worktree_root,
        "worktree_hash": worktree_hash,
        "project_hash": project_hash,
        "service": service,
        "scope": scope,
        "status": status,
        "ports": dict(ports),
        "urls": dict(urls),
        "container_names": list(container_names),
        "compose_project_name": compose_project_name,
        "labels": dict(labels),
        "created_at": created_at or now,
        "updated_at": now,
        "last_start": last_start or {},
        "last_probe": last_probe or {},
    }
