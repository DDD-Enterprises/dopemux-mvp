import json
from pathlib import Path

import pytest
import yaml

from dopemux.commands import mcp_commands
from dopemux.mcp import fleet_catalog


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_duplicate_yaml_keys_are_rejected(tmp_path):
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        """
version: 1
servers:
  alpha:
    scope: singleton
    transport: http
    url: http://localhost:3000/mcp
  alpha:
    scope: singleton
    transport: http
    url: http://localhost:3001/mcp
""".lstrip()
    )

    with pytest.raises(fleet_catalog.DuplicateKeyError) as excinfo:
        fleet_catalog.load_yaml_no_duplicate_keys(catalog)

    assert "alpha" in str(excinfo.value)


def test_root_catalog_defaults_render_committed_mcp_json():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    defaults = catalog["defaults"]["per_worktree"]

    expected = fleet_catalog.render_per_worktree_mcp_json(defaults, catalog)
    actual = json.loads((REPO_ROOT / ".mcp.json").read_text())

    assert actual == expected


def test_fleet_renderer_matches_existing_mcp_command_renderer():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    defaults = catalog["defaults"]["per_worktree"]

    assert fleet_catalog.render_per_worktree_mcp_json(
        defaults,
        catalog,
    ) == mcp_commands._build_local_mcp_json(defaults, catalog)


def test_singleton_fragment_matches_existing_mcp_command_renderer():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    expected = {
        name: mcp_commands._render_global_entry(name, spec)
        for name, spec in catalog["servers"].items()
        if spec["scope"] == "singleton"
    }

    assert fleet_catalog.render_singleton_mcp_servers(catalog) == expected


def test_known_tool_surfaces_include_catalog_servers_and_explicit_aliases():
    catalog = yaml.safe_load(
        """
version: 1
servers:
  pal:
    scope: singleton
    transport: http
    url: http://localhost:3003/mcp
    tool_aliases:
      - zen
  conport:
    scope: per-worktree
    transport: sse
    url_template: http://localhost:${CONPORT_MCP_PORT:-3005}/sse
    port_var: CONPORT_MCP_PORT
    default_port_base: 3005
""".lstrip()
    )

    assert fleet_catalog.known_tool_surfaces(catalog) == {"conport", "pal", "zen"}


def test_extract_mcp_tool_surfaces_includes_wildcard_references():
    assert fleet_catalog.extract_mcp_tool_surfaces(
        "`mcp__conport__*` and `mcp__task-orchestrator__get_context`"
    ) == ["conport", "task-orchestrator"]
