"""Public v2 tools for the DCP read-only MCP facade.

This module is the external contract boundary. It resolves only opaque
``target_id`` values through registry v2, performs local filesystem evidence
reads, and never selects an endpoint or invokes a backend adapter. Runtime
catalog evidence remains advisory and is always serialized as non-callable.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from . import envelope as E
from .capability import capability_report
from .gitstate import repo_state
from .proofs import MAX_BUNDLES, fetch_bundle, list_bundles
from .redaction import redact_value
from .registry_v2 import RegistryV2
from .resolver_core import ResolvedTarget, resolve_target
from .runtime_catalog_join import join_runtime_catalog

_MAX_FILTER_LEN = 128
_TARGET_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
# Locator-shaped values can match the opaque charset (e.g. "3020", "127.0.0.1")
# but must not be accepted or echoed at the public boundary.
_ALL_DIGITS = re.compile(r"^\d+$")
# Full IPv4 and shortened numeric-dotted forms (e.g. "127.1") that some
# resolvers expand to addresses.
_NUMERIC_DOTTED = re.compile(r"^\d+(?:\.\d+)+$")
_RUNTIME_REGISTRY_ENV = "DOPEMUX_MCP_RUNTIME_REGISTRY"
_CATALOG_ENV = "DCP_FACADE_MCP_CATALOG"

_TARGET_ENVELOPE_FIELDS = (
    "target_id",
    "branch",
    "head_sha",
    "dirty",
    "source_system",
    "authority_label",
    "untrusted",
    "status",
    "freshness",
    "limitations",
    "warnings",
    "redactions",
    "blocked_reasons",
    "data",
)


def _is_opaque_target_id(value: object) -> bool:
    """Accept only bounded opaque identifiers at the public boundary.

    Port-like all-digit values and numeric-dotted locator values are rejected
    even though they match the opaque charset, so they cannot be echoed on
    unknown-target block paths.
    """
    if not isinstance(value, str) or not _TARGET_ID_PATTERN.fullmatch(value):
        return False
    if _ALL_DIGITS.fullmatch(value) or _NUMERIC_DOTTED.fullmatch(value):
        return False
    redacted, categories = redact_value(value, [])
    return not categories and redacted == value


def _build_envelope(
    *,
    target_id: Optional[str],
    status: str,
    source_system: str,
    authority_label: str,
    data: Any = None,
    branch: Optional[str] = None,
    head_sha: Optional[str] = None,
    dirty: Optional[bool] = None,
    freshness: Optional[str] = None,
    untrusted: bool = True,
    limitations: Optional[list[str]] = None,
    warnings: Optional[list[str]] = None,
    redactions: Optional[list[str]] = None,
    blocked_reasons: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Build the v2 target envelope without carrying a v1 project_id field."""
    values = {
        "target_id": target_id,
        "branch": branch,
        "head_sha": head_sha,
        "dirty": dirty,
        "source_system": source_system,
        "authority_label": authority_label,
        "untrusted": untrusted,
        "status": status,
        "freshness": freshness,
        "limitations": list(limitations or []),
        "warnings": list(warnings or []),
        "redactions": list(redactions or []),
        "blocked_reasons": list(blocked_reasons or []),
        "data": data,
    }
    return {field: values[field] for field in _TARGET_ENVELOPE_FIELDS}


def _blocked(target_id: Optional[str], reason: str) -> dict[str, Any]:
    return _build_envelope(
        target_id=target_id,
        status=E.BLOCKED,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FACADE,
        data=None,
        blocked_reasons=[reason],
    )


def _resolve(registry: RegistryV2, target_id: object) -> tuple[Optional[ResolvedTarget], dict | None]:
    """Resolve a public target without reflecting unsafe caller input."""
    if not _is_opaque_target_id(target_id):
        return None, _blocked(None, "target_id is required or invalid")

    resolved, reason = resolve_target(registry, target_id)
    if resolved is not None:
        return resolved, None
    if reason and reason.startswith("target disabled"):
        public_reason = "target disabled"
    elif reason and reason.startswith("unknown target"):
        public_reason = "target is not authorized"
    else:
        public_reason = "target resolution blocked"
    return None, _blocked(target_id, public_reason)


def _redact(data: Any, resolved: ResolvedTarget) -> tuple[Any, list[str]]:
    return redact_value(data, [str(resolved.workspace), str(resolved.project_root), str(resolved.worktree_root)])


def _load_yaml_mapping(path: Path) -> Optional[dict[str, Any]]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError, UnicodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _load_runtime_registry() -> tuple[dict[str, Any], bool]:
    raw_path = os.getenv(_RUNTIME_REGISTRY_ENV)
    path = (
        Path(raw_path).expanduser()
        if raw_path
        else Path.home() / ".dopemux" / "mcp" / "runtime" / "instances.json"
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {"parse_status": "MISSING", "instances": []}, False
    if not isinstance(payload, dict) or not isinstance(payload.get("instances"), list):
        return {"parse_status": "ERROR", "instances": []}, False
    clean = dict(payload)
    clean["parse_status"] = "OK"
    return clean, True


def _load_catalog(resolved: ResolvedTarget) -> tuple[dict[str, Any], bool]:
    raw_path = os.getenv(_CATALOG_ENV)
    path = Path(raw_path).expanduser() if raw_path else resolved.project_root / "mcp_catalog.yaml"
    catalog = _load_yaml_mapping(path)
    if catalog is None or not isinstance(catalog.get("servers"), dict):
        return {}, False
    return catalog, True


def list_targets(registry: RegistryV2) -> dict[str, Any]:
    """List enabled opaque target IDs without exposing workspace metadata."""
    targets = [
        {"target_id": target.target_id}
        for target in sorted(registry.enabled_targets(), key=lambda item: item.target_id)
        if _is_opaque_target_id(target.target_id)
    ]
    return _build_envelope(
        target_id=None,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FACADE,
        data={"registry_generation": registry.generation, "targets": targets},
        untrusted=False,
    )


def get_target_capabilities(registry: RegistryV2, target_id: object) -> dict[str, Any]:
    """Report static policy capabilities; none are live or callable here."""
    resolved, blocked = _resolve(registry, target_id)
    if blocked is not None:
        return blocked
    assert resolved is not None
    data, redactions = _redact(
        {
            "target_id": resolved.target.target_id,
            "capabilities": capability_report(resolved),
        },
        resolved,
    )
    return _build_envelope(
        target_id=resolved.target.target_id,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FACADE,
        data=data,
        untrusted=False,
        redactions=redactions,
    )


def get_target_repo_state_snapshot(registry: RegistryV2, target_id: object) -> dict[str, Any]:
    """Return a target workspace's read-only git state snapshot."""
    resolved, blocked = _resolve(registry, target_id)
    if blocked is not None:
        return blocked
    assert resolved is not None
    state = repo_state(resolved.workspace)
    status = E.OK if state["head_sha"] is not None else E.PARTIAL
    limitations = [] if status == E.OK else ["git state unavailable"]
    warnings = ["dirty worktree"] if state["dirty"] else []
    data, redactions = _redact(
        {"branch": state["branch"], "head_sha": state["head_sha"], "dirty": state["dirty"]},
        resolved,
    )
    return _build_envelope(
        target_id=resolved.target.target_id,
        status=status,
        source_system=E.SOURCE_GIT,
        authority_label=E.AUTHORITY_GIT,
        data=data,
        branch=state["branch"],
        head_sha=state["head_sha"],
        dirty=state["dirty"],
        limitations=limitations,
        warnings=warnings,
        redactions=redactions,
    )


def list_target_proof_bundles(
    registry: RegistryV2, target_id: object, packet_id_filter: Optional[str] = None
) -> dict[str, Any]:
    """List bounded proof bundle metadata under a resolved target workspace."""
    resolved, blocked = _resolve(registry, target_id)
    if blocked is not None:
        return blocked
    assert resolved is not None
    if packet_id_filter is not None and (
        not isinstance(packet_id_filter, str) or len(packet_id_filter) > _MAX_FILTER_LEN
    ):
        return _blocked(resolved.target.target_id, "invalid packet_id_filter")
    bundles, truncated = list_bundles(resolved.workspace, packet_id_filter, cap=MAX_BUNDLES)
    data, redactions = _redact({"bundles": bundles}, resolved)
    limitations = [f"results capped at {MAX_BUNDLES}"] if truncated else []
    return _build_envelope(
        target_id=resolved.target.target_id,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FS,
        data=data,
        limitations=limitations,
        redactions=redactions,
    )


def fetch_target_proof_bundle(registry: RegistryV2, target_id: object, bundle_id: object) -> dict[str, Any]:
    """Fetch a containment-checked proof bundle for a resolved target."""
    resolved, blocked = _resolve(registry, target_id)
    if blocked is not None:
        return blocked
    assert resolved is not None
    head_sha = repo_state(resolved.workspace)["head_sha"]
    data, reason, warnings = fetch_bundle(resolved.workspace, bundle_id, current_head=head_sha)
    if reason is not None:
        return _blocked(resolved.target.target_id, reason)
    clean, redactions = _redact(data, resolved)
    return _build_envelope(
        target_id=resolved.target.target_id,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FS,
        data=clean,
        head_sha=head_sha,
        warnings=warnings,
        redactions=redactions,
    )


def get_target_runtime_receipt(registry: RegistryV2, target_id: object) -> dict[str, Any]:
    """Join local runtime evidence without selecting a callable backend."""
    resolved, blocked = _resolve(registry, target_id)
    if blocked is not None:
        return blocked
    assert resolved is not None
    catalog, catalog_available = _load_catalog(resolved)
    runtime_registry, runtime_available = _load_runtime_registry()
    receipt = join_runtime_catalog(resolved, catalog, runtime_registry).to_public_dict()
    data, redactions = _redact(receipt, resolved)
    limitations: list[str] = []
    if not catalog_available:
        limitations.append("canonical catalog unavailable")
    if not runtime_available:
        limitations.append("operational runtime registry unavailable")
    return _build_envelope(
        target_id=resolved.target.target_id,
        status=E.OK if not limitations else E.PARTIAL,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_DERIVED,
        data=data,
        limitations=limitations,
        redactions=redactions,
    )
