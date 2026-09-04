"""Service lease v2: operational endpoint authority (P1 fleet control plane).

A lease is endpoint authority only, never domain truth or domain writes --
see ``docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md``
S5 and ``schemas/mcp/service-lease-v2.schema.json``. Port formulas,
filesystem paths, labels, and service-family probes never independently
prove ownership; ``ownership.py`` combines this module's verdict with
registry, probe, and storage evidence before anything becomes mutation
eligible.

Path default: ``~/.dopemux/mcp/registry/service-leases.json``
Override: ``DOPEMUX_MCP_SERVICE_LEASE_REGISTRY``
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "dopemux.mcp.service-lease.v2"
_STORE_SCHEMA_VERSION = "dopemux.mcp.service-lease-store.v1"
REGISTRY_ENV = "DOPEMUX_MCP_SERVICE_LEASE_REGISTRY"
DEFAULT_RELATIVE = Path(".dopemux/mcp/registry/service-leases.json")

SHARING_CLASSES = ("HOST_SINGLETON", "PROJECT_SCOPED", "WORKTREE_SCOPED", "RETIRED")


class ServiceLeaseError(RuntimeError):
    """Raised when a lease store cannot be loaded/mutated, or a lease
    operation would violate the sharing-class key contract. Fail closed."""


class ServiceLeaseConflict(ServiceLeaseError):
    """Raised by ``acquire`` when an active lease already exists under a
    different owner -- callers must go through ``transfer`` explicitly
    rather than silently steal ownership."""


def default_registry_path() -> Path:
    override = os.environ.get(REGISTRY_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / DEFAULT_RELATIVE).resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_lease_id() -> str:
    return f"lease_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class LeaseKey:
    """The lease lookup key. Its shape is dictated by ``sharing_class``:
    ``service_id`` alone for HOST_SINGLETON, ``project_id + service_id`` for
    PROJECT_SCOPED, ``project_id + instance_id + service_id`` for
    WORKTREE_SCOPED. RETIRED can never be leased -- constructing one raises."""

    sharing_class: str
    service_id: str
    project_id: Optional[str] = None
    instance_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.sharing_class not in SHARING_CLASSES:
            raise ServiceLeaseError(f"unknown sharing_class: {self.sharing_class!r}")
        if self.sharing_class == "RETIRED":
            raise ServiceLeaseError("RETIRED cannot own a lease")
        if not self.service_id or not self.service_id.strip():
            raise ServiceLeaseError("service_id must be non-empty")
        if self.sharing_class == "HOST_SINGLETON":
            if self.project_id is not None or self.instance_id is not None:
                raise ServiceLeaseError(
                    "HOST_SINGLETON identifies the host endpoint, not a tenant; "
                    "project_id/instance_id must be None"
                )
        elif self.sharing_class == "PROJECT_SCOPED":
            if not self.project_id:
                raise ServiceLeaseError("PROJECT_SCOPED requires project_id")
            if self.instance_id is not None:
                raise ServiceLeaseError("PROJECT_SCOPED must not carry instance_id")
        elif self.sharing_class == "WORKTREE_SCOPED":
            if not self.project_id or not self.instance_id:
                raise ServiceLeaseError("WORKTREE_SCOPED requires project_id and instance_id")

    def storage_key(self) -> str:
        parts = [self.sharing_class, self.service_id]
        if self.project_id is not None:
            parts.append(self.project_id)
        if self.instance_id is not None:
            parts.append(self.instance_id)
        return "::".join(parts)


@dataclass(frozen=True)
class ServiceLease:
    lease_id: str
    service_id: str
    sharing_class: str
    registry_generation: int
    owner_epoch: int
    endpoint: Dict[str, Any]
    owner_runtime_identity: Dict[str, str]
    status: str  # active | stale | released | unknown | conflicting
    created_at: str
    updated_at: str
    last_verified_at: str
    evidence_refs: Tuple[str, ...] = ()
    project_id: Optional[str] = None
    instance_id: Optional[str] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "lease_id": self.lease_id,
            "service_id": self.service_id,
            "sharing_class": self.sharing_class,
            "registry_generation": self.registry_generation,
            "owner_epoch": self.owner_epoch,
            "endpoint": dict(self.endpoint),
            "owner_runtime_identity": dict(self.owner_runtime_identity),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_verified_at": self.last_verified_at,
            "evidence_refs": list(self.evidence_refs),
        }
        if self.project_id is not None:
            out["project_id"] = self.project_id
        if self.instance_id is not None:
            out["instance_id"] = self.instance_id
        return out

    @classmethod
    def from_schema_dict(cls, raw: Dict[str, Any]) -> "ServiceLease":
        return cls(
            lease_id=raw["lease_id"],
            service_id=raw["service_id"],
            sharing_class=raw["sharing_class"],
            registry_generation=int(raw["registry_generation"]),
            owner_epoch=int(raw["owner_epoch"]),
            endpoint=dict(raw["endpoint"]),
            owner_runtime_identity=dict(raw["owner_runtime_identity"]),
            status=raw["status"],
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            last_verified_at=raw["last_verified_at"],
            evidence_refs=tuple(raw.get("evidence_refs") or ()),
            project_id=raw.get("project_id"),
            instance_id=raw.get("instance_id"),
        )


def _key_from_lease(lease: ServiceLease) -> LeaseKey:
    return LeaseKey(
        sharing_class=lease.sharing_class,
        service_id=lease.service_id,
        project_id=lease.project_id,
        instance_id=lease.instance_id,
    )


@dataclass
class ServiceLeaseRegistry:
    """Atomic, file-backed store of active service-lease-v2 records."""

    path: Path
    data: Dict[str, Any] = field(default_factory=lambda: {
        "schema_version": _STORE_SCHEMA_VERSION,
        "updated_at": _utc_now(),
        "leases": {},
    })
    present: bool = False
    parse_status: str = "MISSING"  # OK | ERROR | MISSING
    error: Optional[str] = None

    @classmethod
    def load(cls, path: Optional[Path] = None, *, create_missing: bool = False) -> "ServiceLeaseRegistry":
        reg_path = Path(path) if path is not None else default_registry_path()
        if not reg_path.exists():
            if create_missing:
                reg_path.parent.mkdir(parents=True, exist_ok=True)
                reg = cls(path=reg_path, present=False, parse_status="MISSING")
                reg._persist()
                reg.present = True
                reg.parse_status = "OK"
                return reg
            return cls(path=reg_path, present=False, parse_status="MISSING")

        try:
            raw = json.loads(reg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return cls(path=reg_path, present=True, parse_status="ERROR", error=str(exc))
        if not isinstance(raw, dict) or not isinstance(raw.get("leases"), dict):
            return cls(
                path=reg_path,
                present=True,
                parse_status="ERROR",
                error="service lease store malformed: expected object with a 'leases' mapping",
            )
        data = dict(raw)
        data.setdefault("schema_version", _STORE_SCHEMA_VERSION)
        data.setdefault("updated_at", _utc_now())
        return cls(path=reg_path, data=data, present=True, parse_status="OK")

    def _require_writable(self) -> None:
        if self.parse_status == "ERROR":
            raise ServiceLeaseError(
                f"Service lease store parse failed at {self.path}: {self.error}. Mutation blocked."
            )

    def _persist(self) -> None:
        self._require_writable()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = _utc_now()
        self.data.setdefault("schema_version", _STORE_SCHEMA_VERSION)
        text = json.dumps(self.data, indent=2, sort_keys=True) + "\n"
        fd, tmp_name = tempfile.mkstemp(prefix=".service-leases.", suffix=".tmp", dir=str(self.path.parent))
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

    def get(self, key: LeaseKey) -> Optional[ServiceLease]:
        raw = self.data.get("leases", {}).get(key.storage_key())
        return ServiceLease.from_schema_dict(raw) if raw is not None else None

    def find(
        self,
        *,
        service_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ServiceLease]:
        out: List[ServiceLease] = []
        for raw in self.data.get("leases", {}).values():
            lease = ServiceLease.from_schema_dict(raw)
            if service_id is not None and lease.service_id != service_id:
                continue
            if project_id is not None and lease.project_id != project_id:
                continue
            if status is not None and lease.status != status:
                continue
            out.append(lease)
        return out

    def acquire(
        self,
        key: LeaseKey,
        *,
        registry_generation: int,
        owner_runtime_identity: Dict[str, str],
        endpoint: Dict[str, Any],
        evidence_refs: Sequence[str] = (),
    ) -> ServiceLease:
        """Create a new lease, or idempotently renew one already owned by the
        same ``owner_runtime_identity``. Raises ``ServiceLeaseConflict`` if an
        active lease exists under a *different* owner -- use ``transfer`` for
        an explicit, audited ownership change instead."""

        self._require_writable()
        existing = self.get(key)
        now = _utc_now()
        if existing is not None and existing.status == "active":
            if existing.owner_runtime_identity != dict(owner_runtime_identity):
                raise ServiceLeaseConflict(
                    f"active lease for {key.storage_key()} is owned by "
                    f"{existing.owner_runtime_identity}; use transfer() to change owner"
                )
            renewed = ServiceLease(
                lease_id=existing.lease_id,
                service_id=key.service_id,
                sharing_class=key.sharing_class,
                registry_generation=registry_generation,
                owner_epoch=existing.owner_epoch,
                endpoint=dict(endpoint),
                owner_runtime_identity=dict(owner_runtime_identity),
                status="active",
                created_at=existing.created_at,
                updated_at=now,
                last_verified_at=now,
                evidence_refs=tuple(evidence_refs),
                project_id=key.project_id,
                instance_id=key.instance_id,
            )
            self.data.setdefault("leases", {})[key.storage_key()] = renewed.to_schema_dict()
            self._persist()
            return renewed

        created = ServiceLease(
            lease_id=_new_lease_id(),
            service_id=key.service_id,
            sharing_class=key.sharing_class,
            registry_generation=registry_generation,
            owner_epoch=0,
            endpoint=dict(endpoint),
            owner_runtime_identity=dict(owner_runtime_identity),
            status="active",
            created_at=now,
            updated_at=now,
            last_verified_at=now,
            evidence_refs=tuple(evidence_refs),
            project_id=key.project_id,
            instance_id=key.instance_id,
        )
        self.data.setdefault("leases", {})[key.storage_key()] = created.to_schema_dict()
        self._persist()
        return created

    def transfer(
        self,
        key: LeaseKey,
        *,
        registry_generation: int,
        new_owner_runtime_identity: Dict[str, str],
        endpoint: Dict[str, Any],
        evidence_refs: Sequence[str] = (),
    ) -> ServiceLease:
        """Explicit ownership change. Always bumps ``owner_epoch`` -- the one
        way ownership legitimately moves to a different runtime identity."""

        self._require_writable()
        existing = self.get(key)
        now = _utc_now()
        next_epoch = (existing.owner_epoch + 1) if existing is not None else 0
        transferred = ServiceLease(
            lease_id=existing.lease_id if existing is not None else _new_lease_id(),
            service_id=key.service_id,
            sharing_class=key.sharing_class,
            registry_generation=registry_generation,
            owner_epoch=next_epoch,
            endpoint=dict(endpoint),
            owner_runtime_identity=dict(new_owner_runtime_identity),
            status="active",
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
            last_verified_at=now,
            evidence_refs=tuple(evidence_refs),
            project_id=key.project_id,
            instance_id=key.instance_id,
        )
        self.data.setdefault("leases", {})[key.storage_key()] = transferred.to_schema_dict()
        self._persist()
        return transferred

    def _set_status(self, key: LeaseKey, status: str) -> Optional[ServiceLease]:
        self._require_writable()
        existing = self.get(key)
        if existing is None:
            return None
        updated = ServiceLease(
            **{
                **existing.__dict__,
                "status": status,
                "updated_at": _utc_now(),
            }
        )
        self.data.setdefault("leases", {})[key.storage_key()] = updated.to_schema_dict()
        self._persist()
        return updated

    def release(self, key: LeaseKey) -> Optional[ServiceLease]:
        return self._set_status(key, "released")

    def mark_stale(self, key: LeaseKey) -> Optional[ServiceLease]:
        return self._set_status(key, "stale")


# ---- fail-closed verification (consumed by ownership.py) ------------------

LEASE_VERDICTS = (
    "ACTIVE",
    "UNKNOWN",
    "WRONG_PROJECT",
    "WRONG_INSTANCE",
    "STALE",
    "RELEASED",
    "CONFLICTING",
)


def lease_verdict(
    lease: Optional[ServiceLease],
    *,
    key: LeaseKey,
    current_registry_generation: int,
    expected_owner_runtime_id: Optional[str] = None,
) -> str:
    """Fail-closed classification of whether ``lease`` currently authorizes
    endpoint selection for ``key``. Only "ACTIVE" does; every other verdict
    must deny mutation. Never derives ownership from port/path/label alone --
    the caller supplies ``lease`` from the registry, not from a probe."""

    if lease is None:
        return "UNKNOWN"
    if lease.sharing_class != key.sharing_class or lease.service_id != key.service_id:
        return "CONFLICTING"
    if key.sharing_class == "PROJECT_SCOPED" and lease.project_id != key.project_id:
        return "WRONG_PROJECT"
    if key.sharing_class == "WORKTREE_SCOPED":
        if lease.project_id != key.project_id:
            return "WRONG_PROJECT"
        if lease.instance_id != key.instance_id:
            return "WRONG_INSTANCE"
    if lease.status == "released":
        return "RELEASED"
    if lease.status in ("stale", "unknown", "conflicting"):
        return lease.status.upper()
    if lease.status != "active":
        return "UNKNOWN"
    if lease.registry_generation != current_registry_generation:
        return "STALE"
    if (
        expected_owner_runtime_id is not None
        and lease.owner_runtime_identity.get("runtime_id") != expected_owner_runtime_id
    ):
        return "CONFLICTING"
    return "ACTIVE"


# ---- read-only legacy migration preview ------------------------------------
#
# Reads only whatever dict list the caller supplies (e.g. from
# port_leases.PortLeaseRegistry.instances()/to_dict()) -- this module never
# imports or opens the legacy v1 registry file itself, so it cannot mutate it.

_LEGACY_SCOPE_TO_SHARING_CLASS: Dict[str, str] = {
    "singleton": "HOST_SINGLETON",
    "project": "PROJECT_SCOPED",
    "worktree": "WORKTREE_SCOPED",
}


@dataclass(frozen=True)
class MigrationPreview:
    convertible: Tuple[Dict[str, Any], ...]
    ambiguous: Tuple[Dict[str, Any], ...]
    rejected: Tuple[Dict[str, Any], ...]


def preview_legacy_migration(legacy_leases: Sequence[Dict[str, Any]]) -> MigrationPreview:
    """Classify legacy (schema 1.0) port-lease records into what a future v2
    migration *would* do -- never what it does. No file or runtime mutation;
    "convertible" candidates still require explicit registry registration
    before any v2 lease is acquired (this never fabricates a v2 project_id
    from the legacy path-hash-derived one)."""

    convertible: List[Dict[str, Any]] = []
    ambiguous: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    seen_service_scope: Dict[Tuple[str, str], int] = {}
    for raw in legacy_leases:
        service = str(raw.get("service") or "")
        scope = str(raw.get("scope") or "")
        seen_service_scope[(service, scope)] = seen_service_scope.get((service, scope), 0) + 1

    for raw in legacy_leases:
        service = str(raw.get("service") or "")
        scope = str(raw.get("scope") or "")
        status = str(raw.get("status") or "")
        entry = dict(raw)

        if status == "released":
            rejected.append({**entry, "reason": "already released; nothing to migrate"})
            continue
        if not service or not raw.get("port"):
            rejected.append({**entry, "reason": "missing service or port"})
            continue

        sharing_class = _LEGACY_SCOPE_TO_SHARING_CLASS.get(scope)
        if sharing_class is None:
            rejected.append({**entry, "reason": f"unknown legacy scope {scope!r}"})
            continue

        if sharing_class == "HOST_SINGLETON" and (raw.get("project_id") or raw.get("instance_id")):
            ambiguous.append(
                {**entry, "reason": "singleton scope carries project_id/instance_id residue"}
            )
            continue
        if sharing_class == "PROJECT_SCOPED" and not raw.get("project_id"):
            ambiguous.append({**entry, "reason": "project scope missing project_id"})
            continue
        if sharing_class == "WORKTREE_SCOPED" and not (raw.get("project_id") and raw.get("instance_id")):
            ambiguous.append({**entry, "reason": "worktree scope missing project_id/instance_id"})
            continue
        if status not in ("active", "stale", "unknown"):
            ambiguous.append({**entry, "reason": f"unrecognized status {status!r}"})
            continue
        if seen_service_scope.get((service, scope), 0) > 1:
            ambiguous.append(
                {**entry, "reason": "multiple legacy leases collide on (service, scope)"}
            )
            continue

        convertible.append({**entry, "target_sharing_class": sharing_class})

    return MigrationPreview(
        convertible=tuple(convertible),
        ambiguous=tuple(ambiguous),
        rejected=tuple(rejected),
    )
