import json
import tomllib
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

    expected = mcp_commands._build_global_mcp_servers(catalog)

    assert fleet_catalog.render_singleton_mcp_servers(catalog) == expected


def test_global_command_renderer_excludes_decision_required_singletons():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    servers = mcp_commands._build_global_mcp_servers(catalog)

    assert {"desktop-commander"}.isdisjoint(servers)
    assert servers == fleet_catalog.render_singleton_mcp_servers(catalog)


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


def test_generate_fleet_output_files_are_deterministic_and_catalog_backed():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    outputs = fleet_catalog.generate_fleet_output_files(catalog)

    assert list(outputs) == [
        "local/.mcp.json",
        "claude/mcpServers.json",
        "codex/config.toml",
        "health/mcp-health-probes.json",
        "docs/mcp-fleet.md",
    ]
    assert json.loads(outputs["local/.mcp.json"]) == fleet_catalog.render_per_worktree_mcp_json(
        catalog["defaults"]["per_worktree"],
        catalog,
    )
    assert json.loads(outputs["claude/mcpServers.json"]) == {
        "mcpServers": fleet_catalog.render_singleton_mcp_servers(catalog)
    }
    assert outputs == fleet_catalog.generate_fleet_output_files(catalog)


def test_codex_fragment_renders_stdio_and_streamable_http_servers():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "stdio-one": {
                "scope": "singleton",
                "transport": "stdio",
                "command": "docker",
                "args": ["exec", "-i", "stdio-one", "server"],
                "requires_env": ["TOKEN"],
                "optional_env": ["TOKEN", "OPTIONAL_TOKEN"],
            },
            "http-one": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:1234/mcp",
                "requires_env": ["HTTP_TOKEN"],
            },
            "sse-one": {
                "scope": "singleton",
                "transport": "sse",
                "url": "http://localhost:5678/sse",
            },
        },
    }

    fragment = fleet_catalog.render_codex_config_fragment(catalog)

    assert '[mcp_servers."stdio-one"]' in fragment
    assert 'command = "docker"' in fragment
    assert 'args = ["exec", "-i", "stdio-one", "server"]' in fragment
    assert 'env_vars = ["OPTIONAL_TOKEN", "TOKEN"]' in fragment
    assert fragment.count('"TOKEN"') == 1
    assert "${TOKEN:-}" not in fragment
    assert '[mcp_servers."http-one"]' in fragment
    assert 'url = "http://localhost:1234/mcp"' in fragment
    assert "HTTP_TOKEN" not in tomllib.loads(fragment)["mcp_servers"]["http-one"]
    assert "sse-one" not in fragment


def test_health_probe_list_uses_catalog_urls_and_compose_services():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "http-one": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:1234/mcp",
                "docker_compose_service": "http-one",
            },
            "local-one": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${LOCAL_ONE_PORT:-4321}/sse",
                "port_var": "LOCAL_ONE_PORT",
                "default_port_base": 4321,
            },
        },
    }

    assert fleet_catalog.render_health_probe_list(catalog) == [
        {
            "authority_role": None,
            "docker_compose_service": "http-one",
            "follow_on_decision": None,
            "identity_scope": None,
            "lifecycle": None,
            "management_model": None,
            "name": "http-one",
            "plane": None,
            "scope": "singleton",
            "transport": "http",
            "url": "http://localhost:1234/mcp",
        },
        {
            "authority_role": None,
            "docker_compose_service": None,
            "follow_on_decision": None,
            "identity_scope": None,
            "lifecycle": None,
            "management_model": None,
            "name": "local-one",
            "plane": None,
            "scope": "per-worktree",
            "transport": "sse",
            "url": "http://localhost:${LOCAL_ONE_PORT:-4321}/sse",
        },
    ]


def test_health_probe_list_carries_personality_metadata():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    probes = {
        probe["name"]: probe
        for probe in fleet_catalog.render_health_probe_list(catalog)
    }

    assert probes["conport"]["authority_role"] == "structured-context-authority"
    assert probes["task-orchestrator"]["identity_scope"] == "per-repo"
    assert probes["desktop-commander"]["lifecycle"] == "decision-required"


def test_mcp_doctrine_doc_carries_decision_gated_servers():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    doc = fleet_catalog.render_mcp_doctrine_doc(catalog)

    assert "`desktop-commander` | automation | desktop-automation | decision-required" in doc


def _non_startable_variants_catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "startable-http": {
                "scope": "singleton",
                "transport": "http",
                "lifecycle": "active",
                "url": "http://localhost:1111/mcp",
            },
            "agents-none-sse": {
                "scope": "singleton",
                "transport": "sse",
                "lifecycle": "active",
                "agents": "none",
                "url": "http://localhost:2222/sse",
            },
            "agents-none-http": {
                "scope": "singleton",
                "transport": "http",
                "lifecycle": "active",
                "agents": "none",
                "url": "http://localhost:2223/mcp",
            },
            "planned-http": {
                "scope": "singleton",
                "transport": "http",
                "lifecycle": "planned-active",
            },
            "external-unmanaged": {
                "scope": "singleton",
                "transport": "external",
                "managed": False,
                "lifecycle": "operator-managed",
            },
        },
    }


def test_global_renderer_excludes_agents_none_planned_active_and_unmanaged():
    servers = mcp_commands._build_global_mcp_servers(_non_startable_variants_catalog())

    assert set(servers) == {"startable-http"}


def test_codex_fragment_excludes_agents_none_planned_active_and_unmanaged():
    fragment = fleet_catalog.render_codex_config_fragment(_non_startable_variants_catalog())

    assert '[mcp_servers."startable-http"]' in fragment
    assert "agents-none-http" not in fragment
    assert "planned-http" not in fragment
    assert "external-unmanaged" not in fragment
