"""Safe .mcp.json load/merge helpers for config repair.

Only catalog-owned per-worktree services may be modified. Unknown and custom
entries are always preserved. Never mutates global (~/.claude.json) config.
"""

from __future__ import annotations

import json
import re
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


_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1"})
_PLACEHOLDER = re.compile(r"\$\{[^}:$]*(?::-([^}$]*))?\}")
_LITERAL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://")

#: The only port variables dopemux has rendered into a ``url_template``.
_DOPEMUX_PORT_VARS = frozenset(
    {"CONPORT_MCP_PORT", "DOPE_MEMORY_PORT", "TASK_ORCHESTRATOR_HTTP_PORT"}
)
_PLACEHOLDER_NAME = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")
#: Exactly the shape dopemux renders: literal http(s) scheme, literal local host,
#: one port variable (numeric or absent default), then a literal remainder.
_SELF_RENDERED = re.compile(
    r"https?://(?:localhost|127\.0\.0\.1)"
    r":\$\{([A-Z][A-Z0-9_]*)(?::-[0-9]+)?\}(?:[/?#][^${}\s]*)?"
)


def _placeholder_in_userinfo_or_host(url: str) -> bool:
    """True when a ``${...}`` placeholder sits in the userinfo or host position.

    That is the userinfo or host of a URL that starts with a literal ``scheme://``,
    or anywhere in a URL that does not (such a URL is never repairable).

    A host or userinfo placeholder is operator-selected whatever its default
    (``${HOST:-localhost}`` resolves to a remote host when ``HOST`` is set), so
    it never proves the endpoint local. Placeholders in the port, path or query
    are not considered here when the URL starts with a literal scheme.

    Placeholders are masked over the whole URL before the authority is split:
    a default may itself contain ``/``, ``?``, ``#``, ``@``, ``:`` or ``://``
    (``http://${HOST:-localhost/x}/sse``), and splitting first would end the
    authority inside the placeholder.

    Only a literal scheme at the very start is stripped. When a placeholder
    supplies the scheme, the ``//`` or the whole base
    (``${BASE:-http://localhost}/sse``, ``${S:-http}://localhost/sse``), a later
    ``://`` in the path or query is not the authority, so such URLs fail closed:
    the function returns True and they are never repairable.
    """
    # Mask each placeholder as one opaque character so a delimiter inside
    # ``${PORT:-3005}`` is neither the port separator nor the end of the authority.
    masked = _PLACEHOLDER.sub("\x00", url)
    scheme = _LITERAL_SCHEME.match(masked)
    if scheme is None:
        return "\x00" in masked
    authority = masked[scheme.end() :]
    for sep in ("/", "?", "#"):
        authority = authority.split(sep, 1)[0]
    userinfo, _, hostport = authority.rpartition("@")
    if "\x00" in userinfo:
        return True
    if hostport.startswith("["):
        host = hostport.split("]", 1)[0]
    else:
        host = hostport.split(":", 1)[0]
    return "\x00" in host


def _catalog_port_vars(catalog: Mapping[str, Any]) -> frozenset[str]:
    """Variable names used in the catalog's ``url``/``url_template`` values."""
    names: set[str] = set()
    for spec in (catalog.get("servers") or {}).values():
        if not isinstance(spec, Mapping):
            continue
        for key in ("url", "url_template"):
            value = spec.get(key)
            if isinstance(value, str):
                names.update(_PLACEHOLDER_NAME.findall(value))
    return frozenset(names)


def _self_rendered_template(url: str, port_vars: frozenset[str]) -> bool:
    """True when ``url`` has exactly the shape dopemux renders into a ``.mcp.json``.

    That is a literal ``http(s)://``, a literal ``localhost`` or ``127.0.0.1``,
    and one port variable named in ``port_vars`` as the only placeholder, with a
    numeric or absent default, then a literal remainder. A variable's value is
    unknown at repair time, so only this provenance is judged, never the value.
    """
    match = _SELF_RENDERED.fullmatch(url)
    return match is not None and match.group(1) in port_vars


def _url_is_repairable(
    url: Optional[str], port_vars: Optional[frozenset[str]] = None
) -> bool:
    """True when the catalog may replace ``url``.

    That is when it is missing; or a literal URL on localhost/127.0.0.1 with no
    credentials; or a templated URL of exactly the shape dopemux renders itself
    (literal http(s) scheme, literal local host, one of dopemux's own port
    variables as the only placeholder in the port position, numeric or absent
    default, literal remainder). Any other template is operator-authored and
    preserved. Environment values are never inspected: a variable's value is
    unknown at repair time, so only the template's provenance is judged.
    """
    if not url or not isinstance(url, str):
        return True  # missing → can set template
    if "${" in url:
        return not _placeholder_in_userinfo_or_host(url) and _self_rendered_template(
            url, port_vars or _DOPEMUX_PORT_VARS
        )
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return False
    if any(ch in parsed.netloc for ch in "${}"):
        return False  # malformed placeholder characters: not provably local
    if host and host not in _LOCAL_HOSTS:
        return False
    # userinfo credentials → never rewrite
    if parsed.username or parsed.password or "@" in parsed.netloc:
        return False
    return True


def _catalog_is_launcher(catalog: Mapping[str, Any], name: str) -> bool:
    # Lazy: fleet_catalog imports the CLI module, which this planner avoids at import time.
    from .fleet_catalog import catalog_client_shape

    return catalog_client_shape((catalog.get("servers") or {}).get(name) or {}) == "launcher"


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

        # Operator-authored or non-local URL: preserve the URL, only repair type if safe
        current_url = current.get("url")
        url_ok = _url_is_repairable(
            current_url if isinstance(current_url, str) else None,
            _DOPEMUX_PORT_VARS | _catalog_port_vars(catalog),
        )

        is_launcher = _catalog_is_launcher(catalog, name)
        if is_launcher and current_url and not url_ok:
            # An operator-authored or non-local URL is not ours to replace.
            preserved.append(
                {
                    "path": mcp_json_path,
                    "service": name,
                    "reason": (
                        "operator URL preserved "
                        "(not a literal local URL and not a dopemux-rendered template)"
                    ),
                }
            )
            continue

        new_entry = dict(current)
        change_reasons: List[str] = []

        desired_type = desired.get("type")
        if desired_type and current.get("type") != desired_type:
            new_entry["type"] = desired_type
            change_reasons.append("TRANSPORT_MISMATCH")

        if url_ok and desired.get("url") and current.get("url") != desired.get("url"):
            new_entry["url"] = desired["url"]
            change_reasons.append("URL_MISMATCH")
        elif not url_ok and desired.get("url") and current.get("url") != desired.get("url"):
            # Explicitly do not change operator-authored or non-local URLs
            preserved.append(
                {
                    "path": mcp_json_path,
                    "service": name,
                    "reason": (
                        "operator URL preserved "
                        "(not a literal local URL and not a dopemux-rendered template)"
                    ),
                }
            )

        # Align env / command / args only when present in desired catalog entry
        for key in ("env", "command", "args"):
            if key in desired and current.get(key) != desired.get(key):
                # Only patch if current is missing or clearly wrong for catalog-owned
                if key not in current or current.get(key) != desired.get(key):
                    new_entry[key] = desired[key]
                    if "CATALOG_FIELD_DRIFT" not in change_reasons:
                        change_reasons.append("CATALOG_FIELD_DRIFT")

        # A launcher entry carries no endpoint or env of its own: drop leftovers
        # from the old URL shape instead of keeping them next to the command.
        if is_launcher:
            for stale in ("url", "env"):
                if stale in new_entry and stale not in desired:
                    del new_entry[stale]
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
