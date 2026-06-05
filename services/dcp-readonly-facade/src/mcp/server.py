"""DCP read-only MCP evidence facade — FastMCP server (Phase 1 scaffold).

Thin wiring layer: each MCP tool delegates to the pure ``dcp_facade.tools``
functions, which return canonical envelopes. The registry is loaded once from
``$DCP_FACADE_REGISTRY`` (or the default path). Loopback-only binding is the
operator's responsibility per SECURITY_MODEL.md; this scaffold defaults to
stdio transport.

Run locally:  python -m src.mcp.server   (from services/dcp-readonly-facade)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Make the facade package and repo `src` (for dopemux) importable when run
# directly (mirrors the services/dope-context bootstrap pattern).
_HERE = Path(__file__).resolve()
_FACADE_SRC = _HERE.parents[1]            # services/dcp-readonly-facade/src
_REPO_ROOT = _HERE.parents[4]             # repo root
for _p in (str(_FACADE_SRC), str(_REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - constrained envs
    from mcp.fastmcp_stub import FastMCP  # type: ignore

from dcp_facade import tools
from dcp_facade.registry import Registry, load_registry

mcp = FastMCP("dcp-readonly-facade")

# Registry is loaded once at import; reloaded only on process restart.
_REGISTRY: Registry = load_registry(os.getenv("DCP_FACADE_REGISTRY"))


@mcp.tool()
async def list_projects() -> dict:
    """List the projects the facade exposes (enabled registry entries only)."""
    return tools.list_projects(_REGISTRY)


@mcp.tool()
async def get_project_capabilities(project_id: str) -> dict:
    """Report which backends are configured for a project."""
    return tools.get_project_capabilities(_REGISTRY, project_id)


@mcp.tool()
async def get_repo_state_snapshot(project_id: str) -> dict:
    """Return the project's git branch/head/dirty snapshot (read-only)."""
    return tools.get_repo_state_snapshot(_REGISTRY, project_id)


@mcp.tool()
async def list_proof_bundles(project_id: str, packet_id_filter: Optional[str] = None) -> dict:
    """List proof bundles under the project's proof/ directory.

    ``packet_id_filter`` is an optional literal substring of the bundle id
    (not a regex). Results are capped at 20.
    """
    return tools.list_proof_bundles(_REGISTRY, project_id, packet_id_filter)


@mcp.tool()
async def fetch_proof_bundle(project_id: str, bundle_id: str) -> dict:
    """Fetch a single proof bundle's files (containment + symlink safe)."""
    return tools.fetch_proof_bundle(_REGISTRY, project_id, bundle_id)


def main() -> None:
    transport = os.getenv("DCP_FACADE_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
