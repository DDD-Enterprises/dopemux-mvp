"""Safe .mcp.json load/merge helpers for config repair.

Only catalog-owned per-worktree services may be modified. Unknown and custom
entries are always preserved. Never mutates global (~/.claude.json) config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.parse import urlparse

PROJECT_MCP_FILENAME = ".mcp.json"

# Functional fields compared/repaired for catalog-owned HTTP/SSE entries.
_FUNCTIONAL_KEYS = ("type", "url", "command", "args", "env")


def is_catalog_owned(name: str, catalog: Mapping[str, Any]) -> bool:
    """True when the service is a catalog per-worktree entry managed by init/repair."""
    spec = (catalog.get("servers") or {}).get(name)
    if not isinstance(spec, dict):
        return False
    if spec.get("scope") != "per-worktree":
        return False
    # Explicit external/manual markers (if present) are not rewritten.
    if spec.get("management_model") in {"external", "manual"}:
        return False
    if spec.get("lifecycle") == "decision-required":
        return False
    return True


def catalog_owned_names(catalog: Mapping[str, Any]) -> List[str]:
    """Stable ordered list of catalog-owned per-worktree service names."""
    names: List[str] = []
    defaults = list((catalog.get("defaults") or {}).get("per_worktree") or [])
    for name in defaults:
        if is_catalog_owned(str(name), catalog) and name not in names:
            names.append(str(name))
    for name, spec in (catalog.get("servers") or {}).items():
        if is_catalog_owned(str(name), catalog) and name not in names:
            names.append(str(name))
    return names


def load_mcp_json_document(path: Path | str | None) -> Dict[str, Any]:
    """Load .mcp.json for repair planning.

    Returns keys: path, present, parse_status, servers, error, raw_document.
    """
    if path is None:
        return {
            "path": None,
            "present": False,
            "parse_status": "MISSING",
            "servers": {},
            "error": None,
            "raw_document": {},
        }
    mcp_path = Path(path).expanduser()
    if not mcp_path.exists():
        return {
            "path": str(mcp_path),
            "present": False,
            "parse_status": "MISSING",
            "servers": {},
            "error": None,
            "raw_document": {},
        }
    try:
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "path": str(mcp_path),
            "present": True,
            "parse_status": "ERROR",
            "servers": {},
            "error": str(exc),
            "raw_document": {},
        }
    if not isinstance(data, dict):
        return {
            "path": str(mcp_path),
            "present": True,
            "parse_status": "ERROR",
            "servers": {},
            "error": "root is not a JSON object",
            "raw_document": {},
        }
    servers = data.get("mcpServers") or {}
    if not isinstance(servers, dict):
        return {
            "path": str(mcp_path),
            "present": True,
            "parse_status": "ERROR",
            "servers": {},
            "error": "mcpServers is not a mapping",
            "raw_document": data,
        }
    return {
        "path": str(mcp_path),
        "present": True,
        "parse_status": "OK",
        "servers": dict(servers),
        "error": None,
        "raw_document": data,
    }


def _functional_subset(entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: entry[k] for k in _FUNCTIONAL_KEYS if k in entry}


def _url_is_repairable(url: Optional[str]) -> bool:
    if not url or not isinstance(url, str):
        return True  # missing → can set template
    if "${" in url:
        # Template placeholders are always candidate for catalog template replace
        # when host is local or still a placeholder.
        return True
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return False
    host = (parsed.hostname or "").lower()
    if host and host not in {"localhost", "127.0.0.1"}:
        return False
    # userinfo credentials → never rewrite
    if parsed.username or parsed.password:
        return False
    if "@" in url.split("://", 1)[-1].split("/", 1)[0]:
        return False
    return True


def render_catalog_entry(
    name: str,
    catalog: Mapping[str, Any],
    *,
    render_fn: Any = None,
) -> Dict[str, Any]:
    """Render desired catalog-owned entry.

    ``render_fn`` defaults to lazy import of mcp_commands._render_local_entry
    so tests can inject a pure renderer without loading the CLI module.
    """
    spec = (catalog.get("servers") or {})[name]
    if render_fn is not None:
        return dict(render_fn(name, spec))
    from dopemux.commands.mcp_commands import _render_local_entry

    return dict(_render_local_entry(name, spec))


def plan_mcp_json_repairs(
    existing_servers: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    mcp_json_path: str,
    include_defaults: bool = True,
    render_fn: Any = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Plan catalog-owned repairs while preserving unknown entries.

    Returns (merged_servers, planned_changes, preserved_entries).
    """
    merged: Dict[str, Any] = {str(k): dict(v) if isinstance(v, dict) else v for k, v in existing_servers.items()}
    planned: List[Dict[str, Any]] = []
    preserved: List[Dict[str, Any]] = []

    # Preserve unknown / non-catalog-owned first (record for report).
    for name, entry in existing_servers.items():
        if not is_catalog_owned(str(name), catalog):
            preserved.append(
                {
                    "path": mcp_json_path,
                    "service": str(name),
                    "reason": "not catalog-owned",
                }
            )

    # Names to ensure: existing catalog-owned + defaults (when include_defaults).
    targets: List[str] = []
    for name in existing_servers:
        if is_catalog_owned(str(name), catalog) and name not in targets:
            targets.append(str(name))
    if include_defaults:
        for name in (catalog.get("defaults") or {}).get("per_worktree") or []:
            if is_catalog_owned(str(name), catalog) and name not in targets:
                targets.append(str(name))

    for name in sorted(targets):  # deterministic planned_changes order
        desired = render_catalog_entry(name, catalog, render_fn=render_fn)
        current = existing_servers.get(name)
        if not isinstance(current, dict):
            # Create missing catalog-owned entry
            merged[name] = desired
            planned.append(
                {
                    "path": mcp_json_path,
                    "kind": "create" if not existing_servers else "json_patch",
                    "reason": "MISSING_CATALOG_ENTRY",
                    "service": name,
                    "before": None,
                    "after": _functional_subset(desired),
                    "safe": True,
                }
            )
            continue

        # Non-localhost / credential URLs: never silently repair. The current
        # target may live in a flat `url` field (pre-proxy shape) or be
        # embedded in `args[-1]` of an already-migrated stdio+mcp-proxy entry
        # (see mcp_commands._render_local_entry) — check both, since `desired`
        # no longer carries a `url` key at all for http/sse-owned catalog
        # entries once they're proxy-rendered, so a plain `desired.get("url")`
        # guard would never fire post-migration.
        current_url = current.get("url")
        if not isinstance(current_url, str):
            current_args = current.get("args")
            if (
                current.get("command") == "uvx"
                and isinstance(current_args, list)
                and "mcp-proxy" in current_args
                and current_args
            ):
                current_url = current_args[-1]
        url_ok = _url_is_repairable(current_url if isinstance(current_url, str) else None)

        desired_args = desired.get("args")
        catalog_renders_proxy_url = (
            desired.get("command") == "uvx" and isinstance(desired_args, list) and "mcp-proxy" in desired_args
        )
        if not url_ok and isinstance(current_url, str) and catalog_renders_proxy_url:
            preserved.append(
                {
                    "path": mcp_json_path,
                    "service": name,
                    "reason": "non-localhost or credential URL preserved",
                }
            )
            merged[name] = dict(current)
            continue

        new_entry = dict(current)
        change_reasons: List[str] = []

        desired_type = desired.get("type")
        if desired_type and current.get("type") != desired_type:
            new_entry["type"] = desired_type
            change_reasons.append("TRANSPORT_MISMATCH")

        # Align env / command / args only when present in desired catalog entry
        for key in ("env", "command", "args"):
            if key in desired and current.get(key) != desired.get(key):
                # Only patch if current is missing or clearly wrong for catalog-owned
                if key not in current or current.get(key) != desired.get(key):
                    new_entry[key] = desired[key]
                    if "CATALOG_FIELD_DRIFT" not in change_reasons:
                        change_reasons.append("CATALOG_FIELD_DRIFT")

        # Catalog now renders http/sse transports as a stdio+command entry
        # (mcp-proxy wraps the URL into `args`). When the desired entry has no
        # `url` key but the current one does, the old `url` is dead weight left
        # over from the pre-proxy shape — drop it so repaired entries don't carry
        # a stale, unused field alongside `command`/`args`.
        if "url" not in desired and "url" in new_entry:
            del new_entry["url"]
            if "CATALOG_FIELD_DRIFT" not in change_reasons:
                change_reasons.append("CATALOG_FIELD_DRIFT")

        # Preserve description if user has one and desired also has one: prefer catalog
        if "description" in desired:
            new_entry["description"] = desired["description"]

        if _functional_subset(new_entry) != _functional_subset(current) or change_reasons:
            if not change_reasons:
                continue
            merged[name] = new_entry
            # One planned change per primary reason (deterministic)
            primary = change_reasons[0]
            reason_code = {
                "TRANSPORT_MISMATCH": "TRANSPORT_MISMATCH",
                "URL_MISMATCH": "URL_MISMATCH",
                "CATALOG_FIELD_DRIFT": "CATALOG_FIELD_DRIFT",
            }.get(primary, primary)
            planned.append(
                {
                    "path": mcp_json_path,
                    "kind": "json_patch",
                    "reason": reason_code,
                    "service": name,
                    "before": _functional_subset(current),
                    "after": _functional_subset(new_entry),
                    "safe": True,
                }
            )
        else:
            merged[name] = dict(current)

    return merged, planned, preserved


def dump_mcp_json(servers: Mapping[str, Any], *, other_keys: Optional[Mapping[str, Any]] = None) -> str:
    """Deterministic pretty JSON for .mcp.json (stable key ordering)."""
    ordered_servers = {k: servers[k] for k in sorted(servers.keys())}
    doc: Dict[str, Any] = {}
    if other_keys:
        for k in sorted(other_keys.keys()):
            if k == "mcpServers":
                continue
            doc[k] = other_keys[k]
    doc["mcpServers"] = ordered_servers
    return json.dumps(doc, indent=2, sort_keys=False) + "\n"


def write_mcp_json(path: Path, servers: Mapping[str, Any], *, other_keys: Optional[Mapping[str, Any]] = None) -> None:
    """Atomic write of .mcp.json."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dump_mcp_json(servers, other_keys=other_keys)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
