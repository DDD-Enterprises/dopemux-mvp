"""Host-side auditor route registry and capability probe layer.

Selects the highest-priority auditor CLI that is actually present on the
host PATH.  Default registry: claude-audit (primary), gemini-audit (fallback).
Codex is explicitly forbidden as a formal auditor.

Usage:
    from scripts.audit.auditor_router import default_routes, select_route

    route = select_route(default_routes())
    if route is None:
        raise RuntimeError("No audit CLI available on this host")
"""
from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from scripts.audit.route_schema import AuditRoute

# Path to the PAL clink client config directory — used by default_routes().
_CLINK_CONF_DIR = (
    Path(__file__).resolve().parents[2]
    / "docker/mcp-servers-source/pal/pal-mcp-server/conf/cli_clients"
)

# Ordered list of clink config names to load as the default route registry.
# claude-audit is primary (priority 0); gemini-audit is fallback (priority 1).
_DEFAULT_ROUTE_NAMES: tuple[str, ...] = ("claude-audit", "gemini-audit")


def load_route_from_clink_config(
    path: Path,
    *,
    priority: int = 0,
    role: str = "codereviewer",
) -> AuditRoute:
    """Load an AuditRoute from a PAL clink config JSON file.

    Args:
        path:     Absolute path to a clink config JSON file.
        priority: Route priority (lower = higher preference).
        role:     PAL clink role to activate (must exist in config's roles block).

    Raises:
        ValueError:  If the config names a forbidden auditor (e.g. codex).
        FileNotFoundError: If the path does not exist.
        KeyError: If required fields are missing from the config.
    """
    data: dict = json.loads(path.read_text(encoding="utf-8"))
    cli_name: str = data["name"]
    roles: dict = data.get("roles") or {}
    if role not in roles:
        raise KeyError(
            f"role {role!r} not found in {path.name}; available: {sorted(roles.keys())}"
        )
    # Forbidden-name validation is performed inside AuditRoute.__post_init__.
    return AuditRoute(
        cli_name=cli_name,
        command=data["command"],
        priority=priority,
        additional_args=list(data.get("additional_args") or []),
        env=dict(data.get("env") or {}),
        role=role,
    )


def default_routes(
    conf_dir: Path = _CLINK_CONF_DIR,
) -> list[AuditRoute]:
    """Return the default ordered route list loaded from PAL clink configs.

    Loads claude-audit (priority 0) and gemini-audit (priority 1) when their
    config files exist.  Missing config files are silently skipped so the
    router degrades gracefully when only one tool is configured.

    Args:
        conf_dir: Directory containing PAL clink config JSON files.

    Returns:
        List of AuditRoute objects sorted by ascending priority.
    """
    routes: list[AuditRoute] = []
    for idx, name in enumerate(_DEFAULT_ROUTE_NAMES):
        cfg_path = conf_dir / f"{name}.json"
        if cfg_path.exists():
            routes.append(load_route_from_clink_config(cfg_path, priority=idx))
    return sorted(routes, key=lambda r: r.priority)


def probe_capability(
    route: AuditRoute,
    *,
    which_fn: Callable[[str], Optional[str]] = shutil.which,
) -> bool:
    """Return True if route's CLI command is available on the host PATH.

    Args:
        route:    The route to probe.
        which_fn: Callable with shutil.which's signature; injectable for tests.
    """
    return which_fn(route.command) is not None


def select_route(
    routes: list[AuditRoute],
    *,
    which_fn: Callable[[str], Optional[str]] = shutil.which,
) -> AuditRoute | None:
    """Return the highest-priority available route, or None if none are usable.

    Iterates routes in ascending priority order.  Returns the first route
    whose command is present on PATH according to which_fn.

    Args:
        routes:   Candidate routes (need not be pre-sorted).
        which_fn: Capability probe; injectable for tests.

    Returns:
        Best available AuditRoute, or None.
    """
    for route in sorted(routes, key=lambda r: r.priority):
        if probe_capability(route, which_fn=which_fn):
            return route
    return None
