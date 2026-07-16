"""DCP read-only MCP facade — v2 target-contract FastMCP server.

The external server loads only registry v2 from ``DCP_FACADE_REGISTRY_V2``.
It exposes local, read-only target evidence only; backend adapters, public
ingress, credentials, and runtime lifecycle operations are deliberately absent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
_FACADE_SRC = _HERE.parents[1]
_REPO_ROOT = _HERE.parents[4]
for _path in (str(_FACADE_SRC), str(_REPO_ROOT / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - constrained envs
    from mcp.fastmcp_stub import FastMCP  # type: ignore

from dcp_facade import tools_v2
from dcp_facade.registry_v2 import RegistryV2, load_registry_v2

mcp = FastMCP("dcp-readonly-facade")

# Reload only on process restart. The v1 registry is not imported by this server.
_REGISTRY: RegistryV2 = load_registry_v2(os.getenv("DCP_FACADE_REGISTRY_V2"))


@mcp.tool()
async def list_targets() -> dict:
    """List enabled opaque target IDs from the operator-owned v2 registry."""
    return tools_v2.list_targets(_REGISTRY)


@mcp.tool()
async def get_target_capabilities(target_id: str) -> dict:
    """Report static policy capabilities; all remain non-callable here."""
    return tools_v2.get_target_capabilities(_REGISTRY, target_id)


@mcp.tool()
async def get_target_repo_state_snapshot(target_id: str) -> dict:
    """Return a resolved target's local git state snapshot."""
    return tools_v2.get_target_repo_state_snapshot(_REGISTRY, target_id)


@mcp.tool()
async def list_target_proof_bundles(
    target_id: str, packet_id_filter: Optional[str] = None
) -> dict:
    """List bounded proof bundle metadata for a resolved target."""
    return tools_v2.list_target_proof_bundles(_REGISTRY, target_id, packet_id_filter)


@mcp.tool()
async def fetch_target_proof_bundle(target_id: str, bundle_id: str) -> dict:
    """Fetch a containment-checked proof bundle for a resolved target."""
    return tools_v2.fetch_target_proof_bundle(_REGISTRY, target_id, bundle_id)


@mcp.tool()
async def get_target_runtime_receipt(target_id: str) -> dict:
    """Return redacted, non-callable runtime catalog evidence for a target."""
    return tools_v2.get_target_runtime_receipt(_REGISTRY, target_id)


def main() -> None:
    transport = os.getenv("DCP_FACADE_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
