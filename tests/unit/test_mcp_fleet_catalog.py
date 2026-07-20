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
        "opencode/opencode.managed.jsonc",
        "copilot/mcp-proxy-config.copilot.yaml",
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
    assert outputs["opencode/opencode.managed.jsonc"] == fleet_catalog.render_opencode_managed_preview(
        catalog
    )
    assert outputs["copilot/mcp-proxy-config.copilot.yaml"] == fleet_catalog.render_copilot_proxy_config(
        catalog
    )
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


# ---------------------------------------------------------------------------
# MCPINT-FND-CODEGEN-005 — opencode / copilot / codex apply-target renderers
# ---------------------------------------------------------------------------


def test_codex_fragment_excludes_codex_none_matrix_rows():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "codex-full": {
                "scope": "singleton",
                "transport": "http",
                "lifecycle": "active",
                "url": "http://localhost:1111/mcp",
                "agents": {"claude": "full", "codex": "full-sequenced"},
            },
            "codex-none": {
                "scope": "singleton",
                "transport": "stdio",
                "lifecycle": "active",
                "command": "docker",
                "args": ["mcp", "gateway", "run"],
                "agents": {"claude": "full", "codex": "none"},
            },
            "codex-read-plane": {
                "scope": "singleton",
                "transport": "http",
                "lifecycle": "active",
                "url": "http://localhost:2222/mcp",
                "agents": {"codex": "read-plane"},
            },
        },
    }

    fragment = fleet_catalog.render_codex_config_fragment(catalog)

    assert '[mcp_servers."codex-full"]' in fragment
    assert "codex-none" not in fragment
    assert "codex-read-plane" not in fragment


def test_codex_fragment_excludes_mcp_docker_via_real_catalog_matrix():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    fragment = fleet_catalog.render_codex_config_fragment(catalog)

    assert "MCP_DOCKER" not in fragment
    assert '[mcp_servers."pal-stdio"]' in fragment


def test_opencode_renderer_honors_read_safe_direct_rule():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    servers = fleet_catalog.render_opencode_mcp_servers(catalog)

    assert set(servers) == {"pal-stdio"}
    entry = servers["pal-stdio"]
    assert entry["type"] == "local"
    assert entry["command"] == [
        "docker", "exec", "-i", "mcp-pal-stdio", "/app/.venv/bin/python", "server.py",
    ]
    assert entry["environment"] == {
        "GEMINI_API_KEY": "{env:GEMINI_API_KEY}",
        "OPENAI_API_KEY": "{env:OPENAI_API_KEY}",
    }


def test_opencode_managed_section_names_deferred_facade_servers():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    section = "\n".join(fleet_catalog.render_opencode_managed_section_lines(catalog))

    assert fleet_catalog.OPENCODE_MANAGED_BEGIN in section
    assert fleet_catalog.OPENCODE_MANAGED_END in section
    assert "MCPINT-IMP-FACADE-001" in section
    assert "dcp-readonly-facade" in section
    # Deferred read-plane servers are named in comments, never given endpoints.
    assert "conport" in section
    assert '"conport"' not in section


def test_opencode_jsonc_merge_preserves_non_managed_keys_and_replaces_mcp():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    existing = "\n".join(
        [
            "{",
            '  "$schema": "https://opencode.ai/config.json",',
            "  // user comment that only applies to instructions",
            '  "instructions": ["AGENTS.md"],',
            '  "mcp": {',
            '    "pal": {"type": "local", "command": ["sh", "-lc", "legacy"], "enabled": true}',
            "  },",
            '  "permission": {"pal_*": "ask"}',
            "}",
        ]
    )

    merged = fleet_catalog.render_opencode_jsonc(existing, catalog)
    data = json.loads(fleet_catalog._strip_jsonc_comments(merged))

    assert data["$schema"] == "https://opencode.ai/config.json"
    assert data["instructions"] == ["AGENTS.md"]
    assert data["permission"] == {"pal_*": "ask"}
    assert data["mcp"] == fleet_catalog.render_opencode_mcp_servers(catalog)
    assert fleet_catalog.OPENCODE_MANAGED_BEGIN in merged
    assert fleet_catalog.OPENCODE_MANAGED_END in merged
    # Key order: managed section stays where `mcp` was — before `permission`.
    assert merged.index('"instructions"') < merged.index('"mcp"') < merged.index('"permission"')
    # Idempotent: re-merging the merged output changes nothing.
    assert fleet_catalog.render_opencode_jsonc(merged, catalog) == merged


def test_opencode_jsonc_merge_from_scratch_is_valid_jsonc():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    merged = fleet_catalog.render_opencode_jsonc(None, catalog)
    data = json.loads(fleet_catalog._strip_jsonc_comments(merged))

    assert data == {"mcp": fleet_catalog.render_opencode_mcp_servers(catalog)}


def test_opencode_jsonc_merge_rejects_unparseable_input():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    with pytest.raises(fleet_catalog.MCPFleetCatalogError, match="not parseable"):
        fleet_catalog.render_opencode_jsonc("{ not json", catalog)


def test_copilot_proxy_config_renders_catalog_transports_and_env():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    rendered = fleet_catalog.render_copilot_proxy_config(catalog)
    servers = yaml.safe_load(rendered)["mcpServers"]

    assert servers["conport"] == {
        "type": "sse",
        "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
    }
    assert servers["pal-stdio"]["command"] == "docker"
    assert servers["pal-stdio"]["env"] == {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
    }
    assert "dcp-readonly-facade" not in servers
    assert "dcp-readonly-facade" in rendered  # named in the deferred header comment
    assert "MCPINT-IMP-FACADE-001" in rendered


def test_codex_merge_appends_managed_region_preserving_existing_keys():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    existing = "\n".join(
        [
            'model = "gpt-5.5"',
            'approval_policy = "on-request"',
            "",
            "[agents]",
            "max_threads = 4",
        ]
    )

    merged = fleet_catalog.merge_codex_config_toml(existing, catalog)
    parsed = tomllib.loads(merged)

    assert parsed["model"] == "gpt-5.5"
    assert parsed["agents"]["max_threads"] == 4
    assert "pal-stdio" in parsed["mcp_servers"]
    assert fleet_catalog.CODEX_MANAGED_BEGIN in merged
    assert fleet_catalog.CODEX_MANAGED_END in merged
    # Idempotent: merging the merged output replaces the region in place.
    assert fleet_catalog.merge_codex_config_toml(merged, catalog) == merged


def test_codex_merge_refuses_hand_authored_mcp_servers_tables():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    existing = '[mcp_servers."rogue"]\ncommand = "python"\n'

    with pytest.raises(fleet_catalog.MCPFleetCatalogError, match="hand-authored"):
        fleet_catalog.merge_codex_config_toml(existing, catalog)
