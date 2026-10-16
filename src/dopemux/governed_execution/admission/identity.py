"""Typed admission scope using the existing authoritative MCP identity resolver."""

from dataclasses import dataclass, fields
import math
from pathlib import Path

from dopemux.mcp.identity import IdentityClaim, resolve_execution_identity
from dopemux.mcp.identity_registry import IdentityRegistry


class AdmissionError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(detail)


@dataclass(frozen=True)
class ExpectedScope:
    project_id: str
    workspace_id: str
    instance_id: str
    worktree: str
    actor_id: str
    client_id: str
    macro_id: str
    packet_id: str
    subject_digest: str
    effects: tuple[str, ...]
    resources: tuple[str, ...]
    route_refs: tuple[str, ...]
    active_seconds: float
    wall_seconds: float
    spend_limit_micros: int
    max_attempts: int
    repair_limit: int
    max_parallel: int
    delegation_depth: int
    expires_at: float
    policy_digest: str
    trust_digest: str
    schema_set_digest: str

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in {"effects", "resources", "route_refs"}:
                if (
                    not isinstance(value, tuple)
                    or not value
                    or any(not isinstance(x, str) or not x for x in value)
                    or len(value) != len(set(value))
                ):
                    raise AdmissionError("E_SCHEMA", "Invalid scope references")
            elif field.name in {"active_seconds", "wall_seconds", "expires_at"}:
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    raise AdmissionError("E_SCHEMA", "Invalid scope clock")
            elif field.name in {
                "spend_limit_micros",
                "max_attempts",
                "repair_limit",
                "max_parallel",
                "delegation_depth",
            }:
                if type(value) is not int or value < 0:
                    raise AdmissionError("E_SCHEMA", "Invalid scope count")
            elif not isinstance(value, str) or not value.strip():
                raise AdmissionError("E_SCHEMA", "Missing scope identity")
        if self.active_seconds > self.wall_seconds or not 1 <= self.max_parallel <= 2:
            raise AdmissionError("E_SCOPE", "Invalid inherited time or parallel envelope")
        if not 1 <= self.max_attempts <= 256 or self.repair_limit > 2 or self.delegation_depth > 16:
            raise AdmissionError("E_SCOPE", "Scope parser ceiling exceeded")
        for name in ("subject_digest", "policy_digest", "trust_digest", "schema_set_digest"):
            value = getattr(self, name)
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise AdmissionError("E_SCHEMA", "Invalid exact digest")

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or set(data) != {f.name for f in fields(cls)}:
            raise AdmissionError("E_SCHEMA", "Unknown or missing scope fields")
        values = dict(data)
        for name in ("effects", "resources", "route_refs"):
            if not isinstance(values[name], (list, tuple)):
                raise AdmissionError("E_SCHEMA", "Expected scope reference array")
            values[name] = tuple(values[name])
        return cls(**values)

    def require_within(self, parent, depth_limit):
        identities = (
            "project_id",
            "workspace_id",
            "instance_id",
            "worktree",
            "actor_id",
            "client_id",
            "macro_id",
            "packet_id",
            "subject_digest",
            "policy_digest",
            "trust_digest",
            "schema_set_digest",
        )
        if any(getattr(self, key) != getattr(parent, key) for key in identities):
            raise AdmissionError("E_SCOPE", "Exact owner identity/subject does not match")
        for key in ("effects", "resources", "route_refs"):
            if not set(getattr(self, key)) <= set(getattr(parent, key)):
                raise AdmissionError("E_SCOPE", "Delegation widens " + key)
        for key in (
            "active_seconds",
            "wall_seconds",
            "expires_at",
            "spend_limit_micros",
            "max_attempts",
            "repair_limit",
            "max_parallel",
        ):
            if getattr(self, key) > getattr(parent, key):
                raise AdmissionError("E_SCOPE", "Delegation widens " + key)
        if self.delegation_depth < parent.delegation_depth or self.delegation_depth > depth_limit:
            raise AdmissionError("E_SCOPE", "Delegation depth exceeded")


def resolve_bound_identity(scope, registry_path, generation):
    root = Path(scope.worktree)
    if not root.is_absolute() or root.resolve() != root or not root.is_dir():
        raise AdmissionError("E_CUSTODY", "Noncanonical or missing worktree")
    registry = IdentityRegistry.load(registry_path, create_missing=False)
    if not registry.present or registry.parse_status != "OK":
        raise AdmissionError("E_IDENTITY", "Existing identity registry unavailable")
    result = resolve_execution_identity(
        cwd=root,
        registry=registry,
        actor_id=scope.actor_id,
        client_id=scope.client_id,
        claim=IdentityClaim(
            project_id=scope.project_id,
            workspace_id=scope.workspace_id,
            instance_id=scope.instance_id,
        ),
    )
    if result.resolution_status != "VERIFIED" or not result.mutable_routing_allowed:
        raise AdmissionError("E_IDENTITY", "Native identity resolution did not verify")
    if result.registry_generation != generation:
        raise AdmissionError("E_STALE", "Native identity generation changed")
    return result
