"""Registry-authoritative execution identity resolution (P1 fleet control plane).

Canonical ``project_id``/``workspace_id``/``instance_id`` come only from an
``IdentityRegistry`` record reached through an EVIDENCE_ONLY alias match
and/or an explicit claim verified against that registry. Locator inputs
(path, cwd, env, port, container, MCP session/clientInfo) never become
authority on their own -- see
``docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`` S2
and ``schemas/mcp/resolved-execution-identity.schema.json``.

Stale-generation enforcement for a *specific* mutation (lease acquisition,
materialization) lives at that consumer's layer, which binds and rechecks
``registry_generation`` -- see ``service_leases.py``. This resolver only
reports the registry's current generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from dopemux.mcp.identity_registry import (
    PATH_ALIAS_KINDS,
    IdentityRegistry,
    normalize_path_alias_value,
)

SCHEMA_VERSION = "dopemux.mcp.resolved-execution-identity.v1"


@dataclass(frozen=True)
class IdentityClaim:
    """An execution context's explicit assertion of its registered identity.

    A claim is never authoritative by itself: ``resolve_execution_identity``
    verifies every level against the registry, and against any cwd-derived
    alias evidence, before returning VERIFIED.
    """

    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    instance_id: Optional[str] = None


@dataclass(frozen=True)
class ResolvedExecutionIdentity:
    resolution_status: str  # VERIFIED | CONFLICTING | UNKNOWN
    mutable_routing_allowed: bool
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    instance_id: Optional[str] = None
    actor_id: Optional[str] = None
    client_id: Optional[str] = None
    registry_generation: Optional[int] = None
    aliases: List[Dict[str, str]] = field(default_factory=list)

    def to_schema_dict(self) -> Dict[str, Any]:
        """Render exactly the shape required by
        ``schemas/mcp/resolved-execution-identity.schema.json``."""

        return {
            "schema_version": SCHEMA_VERSION,
            "resolution_status": self.resolution_status,
            "mutable_routing_allowed": self.mutable_routing_allowed,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "instance_id": self.instance_id,
            "actor_id": self.actor_id,
            "client_id": self.client_id,
            "registry_generation": self.registry_generation,
            "aliases": list(self.aliases),
        }


def _denied(
    *,
    status: str,
    actor_id: Optional[str],
    client_id: Optional[str],
    aliases: Optional[List[Dict[str, str]]] = None,
) -> ResolvedExecutionIdentity:
    return ResolvedExecutionIdentity(
        resolution_status=status,
        mutable_routing_allowed=False,
        actor_id=actor_id or None,
        client_id=client_id or None,
        aliases=list(aliases or []),
    )


def resolve_execution_identity(
    *,
    cwd: Path,
    registry: IdentityRegistry,
    actor_id: str,
    client_id: str,
    claim: Optional[IdentityClaim] = None,
) -> ResolvedExecutionIdentity:
    """Resolve the caller's execution identity.

    Fails closed to UNKNOWN when no evidence and no claim resolve to a full
    project/workspace/instance chain, and to CONFLICTING when evidence and/or
    claim disagree with the registry or with each other. Never derives an ID
    from ``cwd`` -- it only looks up whether ``cwd`` was previously registered
    as an EVIDENCE_ONLY alias.
    """

    if not actor_id or not actor_id.strip() or not client_id or not client_id.strip():
        return _denied(status="UNKNOWN", actor_id=actor_id, client_id=client_id)

    # Normalize the same way path-kind aliases are normalized on registration
    # (identity_registry._normalize_alias) so a relative cwd, a trailing
    # slash, or a symlinked directory still matches its registered alias.
    cwd_str = normalize_path_alias_value(str(cwd))
    evidence_aliases: List[Dict[str, str]] = [
        {"kind": "cwd", "value": cwd_str, "role": "EVIDENCE_ONLY"}
    ]

    matches: List[Dict[str, Optional[str]]] = []
    for kind in PATH_ALIAS_KINDS:
        matches.extend(registry.find_alias_matches(kind=kind, value=cwd_str))
    matched_project_ids = {m["project_id"] for m in matches}

    if claim is not None and claim.project_id is not None:
        project = registry.get_project(claim.project_id)
        if project is None:
            return _denied(status="CONFLICTING", actor_id=actor_id, client_id=client_id, aliases=evidence_aliases)

        if claim.workspace_id is not None:
            workspace = registry.get_workspace(claim.project_id, claim.workspace_id)
            if workspace is None:
                return _denied(
                    status="CONFLICTING", actor_id=actor_id, client_id=client_id, aliases=evidence_aliases
                )
            if claim.instance_id is not None:
                instance = registry.get_instance(claim.project_id, claim.workspace_id, claim.instance_id)
                if instance is None:
                    return _denied(
                        status="CONFLICTING",
                        actor_id=actor_id,
                        client_id=client_id,
                        aliases=evidence_aliases,
                    )

        if matched_project_ids and matched_project_ids != {claim.project_id}:
            # cwd evidence points at a different project than the claim asserts.
            return _denied(status="CONFLICTING", actor_id=actor_id, client_id=client_id, aliases=evidence_aliases)

        if claim.workspace_id is not None and claim.instance_id is not None:
            return ResolvedExecutionIdentity(
                resolution_status="VERIFIED",
                mutable_routing_allowed=True,
                project_id=claim.project_id,
                workspace_id=claim.workspace_id,
                instance_id=claim.instance_id,
                actor_id=actor_id,
                client_id=client_id,
                registry_generation=registry.generation,
                aliases=evidence_aliases,
            )
        # Claim is structurally valid but not specific enough (missing
        # workspace/instance) to stand alone -- fall through to cwd evidence.

    if len(matched_project_ids) > 1:
        return _denied(status="CONFLICTING", actor_id=actor_id, client_id=client_id, aliases=evidence_aliases)
    if len(matched_project_ids) == 0:
        return _denied(status="UNKNOWN", actor_id=actor_id, client_id=client_id, aliases=evidence_aliases)

    # Exactly one project agrees; VERIFIED still requires an instance-level match.
    instance_matches = [m for m in matches if m["instance_id"] is not None]
    distinct_instances = {(m["project_id"], m["workspace_id"], m["instance_id"]) for m in instance_matches}
    if len(distinct_instances) != 1:
        return _denied(status="UNKNOWN", actor_id=actor_id, client_id=client_id, aliases=evidence_aliases)

    project_id, workspace_id, instance_id = next(iter(distinct_instances))
    return ResolvedExecutionIdentity(
        resolution_status="VERIFIED",
        mutable_routing_allowed=True,
        project_id=project_id,
        workspace_id=workspace_id,
        instance_id=instance_id,
        actor_id=actor_id,
        client_id=client_id,
        registry_generation=registry.generation,
        aliases=evidence_aliases,
    )
