"""Pure runtime-registry/catalog join for TP-DCP-MCP-RO-0011.

This module consumes already-loaded operational mappings. It performs no
network, socket, subprocess, Docker, lease, backend, or write operation.

The runtime registry and catalog are evidence inputs only. They do not grant
exposure consent or ownership, and a matching record never makes a service
callable. Public serialization intentionally omits operational names and all
infrastructure details.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from .resolver_core import ResolvedTarget


# Explicit operational-name translation. The facade family names remain the
# only contract-facing names; no spelling heuristic is permitted here.
FAMILY_CATALOG_MAP: dict[str, Optional[str]] = {
    "conport": "conport",
    "dope_memory": "dope-memory",
    "to_compose_rest": None,
    "to_mcp_wrapper": "task-orchestrator",
    "dope_context": "dope-context",
    "serena": "serena",
    "pal": "pal",
    "docker_mcp_gateway": "MCP_DOCKER",
    "desktop_commander": "desktop-commander",
}

# Static catalog attributes required for the two currently conditionally
# readable per-worktree services. Other families are blocked in this packet.
PER_WORKTREE_CATALOG_CONTRACT: dict[str, dict[str, str]] = {
    "conport": {
        "scope": "per-worktree",
        "identity_scope": "per-worktree",
        "management_model": "compose-service",
    },
    "dope_memory": {
        "scope": "per-worktree",
        "identity_scope": "per-worktree",
        "management_model": "compose-service",
    },
}


@dataclass(frozen=True)
class RuntimeCatalogEntry:
    """Internal joined state for one configured facade service family."""

    family: str
    catalog_name: Optional[str]
    state: str
    candidate_count: int
    callable: bool
    reason: str

    def to_public_dict(self) -> dict[str, Any]:
        """Return the redacted public capability shape."""
        return {
            "family": self.family,
            "state": self.state,
            "callable": False,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RuntimeCatalogJoin:
    """Internal aggregate result; all entries are non-callable."""

    entries: tuple[RuntimeCatalogEntry, ...]

    def to_public_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {"services": [entry.to_public_dict() for entry in self.entries]}


def _canonical_path(value: Any) -> Optional[Path]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return Path(value).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _catalog_servers(catalog: Any) -> Optional[Mapping[str, Any]]:
    if not isinstance(catalog, Mapping):
        return None
    servers = catalog.get("servers")
    return servers if isinstance(servers, Mapping) else None


def _runtime_instances(runtime_registry: Any) -> Optional[list[Mapping[str, Any]]]:
    if not isinstance(runtime_registry, Mapping):
        return None
    if runtime_registry.get("parse_status", "OK") != "OK":
        return None
    instances = runtime_registry.get("instances")
    if not isinstance(instances, list):
        return None
    return [instance for instance in instances if isinstance(instance, Mapping)]


def _catalog_matches_contract(family: str, spec: Any) -> bool:
    if not isinstance(spec, Mapping):
        return False
    expected = PER_WORKTREE_CATALOG_CONTRACT.get(family)
    if expected is None:
        return False
    return all(spec.get(key) == value for key, value in expected.items())


def _runtime_matches_target(
    instance: Mapping[str, Any],
    *,
    family: str,
    catalog_name: str,
    resolved: ResolvedTarget,
) -> bool:
    """Match evidence identity exactly; do not treat it as ownership proof."""
    if instance.get("service") != catalog_name:
        return False
    if instance.get("project_id") != resolved.target.identity_project:
        return False
    project_root = _canonical_path(instance.get("project_root"))
    worktree_root = _canonical_path(instance.get("worktree_root"))
    if project_root != resolved.project_root.resolve():
        return False
    if worktree_root != resolved.worktree_root.resolve():
        return False
    return family in PER_WORKTREE_CATALOG_CONTRACT


def _entry(
    family: str,
    *,
    catalog_name: Optional[str],
    state: str,
    candidate_count: int,
    reason: str,
) -> RuntimeCatalogEntry:
    return RuntimeCatalogEntry(
        family=family,
        catalog_name=catalog_name,
        state=state,
        candidate_count=candidate_count,
        callable=False,
        reason=reason,
    )


def _join_family(
    resolved: ResolvedTarget,
    family: str,
    catalog: Any,
    runtime_registry: Any,
) -> RuntimeCatalogEntry:
    policy = resolved.service_policies[family]
    if not policy.configured:
        return _entry(
            family,
            catalog_name=FAMILY_CATALOG_MAP.get(family),
            state="BLOCKED",
            candidate_count=0,
            reason="service policy disabled",
        )

    catalog_name = FAMILY_CATALOG_MAP.get(family)
    if catalog_name is None:
        return _entry(
            family,
            catalog_name=None,
            state="BLOCKED",
            candidate_count=0,
            reason="service family has no supported catalog binding",
        )

    if policy.chatgpt_posture.startswith("blocked"):
        return _entry(
            family,
            catalog_name=catalog_name,
            state="BLOCKED",
            candidate_count=0,
            reason="service family blocked by exposure policy",
        )

    servers = _catalog_servers(catalog)
    if servers is None:
        return _entry(
            family,
            catalog_name=catalog_name,
            state="UNKNOWN",
            candidate_count=0,
            reason="canonical catalog unavailable",
        )
    spec = servers.get(catalog_name)
    if not _catalog_matches_contract(family, spec):
        return _entry(
            family,
            catalog_name=catalog_name,
            state="BLOCKED",
            candidate_count=0,
            reason="canonical catalog policy mismatch",
        )

    instances = _runtime_instances(runtime_registry)
    if instances is None:
        return _entry(
            family,
            catalog_name=catalog_name,
            state="UNKNOWN",
            candidate_count=0,
            reason="operational runtime registry unavailable",
        )

    matches = [
        instance
        for instance in instances
        if _runtime_matches_target(
            instance,
            family=family,
            catalog_name=catalog_name,
            resolved=resolved,
        )
    ]
    if len(matches) == 0:
        return _entry(
            family,
            catalog_name=catalog_name,
            state="UNAVAILABLE",
            candidate_count=0,
            reason="no matching runtime candidate",
        )
    if len(matches) > 1:
        return _entry(
            family,
            catalog_name=catalog_name,
            state="BLOCKED",
            candidate_count=len(matches),
            reason="ambiguous runtime candidates",
        )
    return _entry(
        family,
        catalog_name=catalog_name,
        state="UNKNOWN",
        candidate_count=1,
        reason="runtime candidate joined; live verification required",
    )


def join_runtime_catalog(
    resolved: ResolvedTarget,
    catalog: Any,
    runtime_registry: Any,
) -> RuntimeCatalogJoin:
    """Join operational evidence to a previously resolved exposure target.

    The function accepts already-loaded mappings so callers control file
    authority and tests remain deterministic. It never returns a selected
    endpoint or a callable result.
    """
    entries = tuple(
        _join_family(resolved, family, catalog, runtime_registry)
        for family in sorted(resolved.service_policies)
    )
    return RuntimeCatalogJoin(entries=entries)
