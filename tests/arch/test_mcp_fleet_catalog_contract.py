import json
import re
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp import fleet_catalog


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_root_catalog_conforms_to_schema():
    schema = fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog.schema.json")
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    jsonschema.validate(catalog, schema)


def test_bundled_default_catalog_stays_in_sync_with_root_catalog():
    schema = fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog.schema.json")
    root_catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    bundled_catalog = fleet_catalog.load_yaml_no_duplicate_keys(
        REPO_ROOT / "src/dopemux/mcp/default_catalog.yaml"
    )

    jsonschema.validate(bundled_catalog, schema)
    assert bundled_catalog == root_catalog
    assert fleet_catalog.validate_catalog_compose_alignment_data(
        bundled_catalog,
        fleet_catalog.load_compose(REPO_ROOT),
    ) == []


def test_root_catalog_defaults_are_declared_per_worktree_servers():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    servers = catalog["servers"]

    invalid = [
        name
        for name in catalog["defaults"]["per_worktree"]
        if name not in servers or servers[name].get("scope") != "per-worktree"
    ]

    assert invalid == []


def test_catalog_compose_service_and_port_alignment():
    errors = fleet_catalog.validate_catalog_compose_alignment(REPO_ROOT)

    assert errors == []


def test_required_server_personalities_are_static_contract():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    errors = fleet_catalog.validate_catalog_personality_contract(catalog)

    assert errors == []


def test_personality_contract_catches_authority_role_drift():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    catalog["servers"]["dope-context"]["authority_role"] = "structured-context-authority"

    errors = fleet_catalog.validate_catalog_personality_contract(catalog)

    assert any("dope-context: authority_role" in error for error in errors)


def test_decision_required_servers_must_name_follow_on_decision():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    catalog["servers"]["temporary-search"] = {
        "scope": "singleton",
        "transport": "http",
        "plane": "research",
        "authority_role": "web-search",
        "lifecycle": "decision-required",
        "management_model": "compose-service",
        "identity_scope": "external-provider",
        "follow_on_decision": "none",
        "url": "http://localhost:3999/mcp",
    }

    errors = fleet_catalog.validate_catalog_personality_contract(catalog)

    assert any("temporary-search: decision-required lifecycle" in error for error in errors)


def test_legacy_registry_has_unique_keys_and_compose_health_contracts():
    errors = fleet_catalog.validate_legacy_registry_contract(REPO_ROOT)

    assert errors == []


def test_generated_mcp_json_parity_is_checked_against_catalog_renderer():
    errors = fleet_catalog.validate_generated_mcp_json_parity(REPO_ROOT)

    assert errors == []


def test_decision_required_servers_are_quarantined_from_startable_generated_configs():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    outputs = fleet_catalog.generate_fleet_output_files(catalog)
    decision_required = {
        name
        for name, spec in catalog["servers"].items()
        if spec.get("lifecycle") == "decision-required"
    }

    local_servers = set(json.loads(outputs["local/.mcp.json"])["mcpServers"])
    claude_servers = set(json.loads(outputs["claude/mcpServers.json"])["mcpServers"])
    codex_servers = set(
        re.findall(r'^\[mcp_servers\."([^"]+)"\]$', outputs["codex/config.toml"], re.MULTILINE)
    )

    # exa retired 2026-07-04 (wire-or-retire → retire); desktop-commander
    # remains the only decision-gated server.
    assert decision_required >= {"desktop-commander"}
    assert local_servers.isdisjoint(decision_required)
    assert claude_servers.isdisjoint(decision_required)
    assert codex_servers.isdisjoint(decision_required)
    assert fleet_catalog.validate_decision_required_generated_config_quarantine(
        catalog,
        outputs,
    ) == []


def test_decision_required_quarantine_gate_reports_generated_config_drift():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": ["quarantined-local"]},
        "servers": {
            "active-stdio": {
                "scope": "singleton",
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"],
                "lifecycle": "active",
            },
            "quarantined-stdio": {
                "scope": "singleton",
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"],
                "lifecycle": "decision-required",
                "follow_on_decision": "wire-or-retire",
            },
            "quarantined-local": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:3999/mcp",
                "lifecycle": "decision-required",
                "follow_on_decision": "delete-or-host-run",
            },
        },
    }
    outputs = {
        "local/.mcp.json": json.dumps({"mcpServers": {"quarantined-local": {}}}),
        "claude/mcpServers.json": json.dumps({"mcpServers": {"quarantined-stdio": {}}}),
        "codex/config.toml": '[mcp_servers."quarantined-stdio"]\ncommand = "python"\n',
    }

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        catalog,
        outputs,
    )

    assert errors == [
        "defaults.per_worktree includes decision-required server `quarantined-local`",
        "local/.mcp.json includes decision-required server `quarantined-local`",
        "claude/mcpServers.json includes decision-required server `quarantined-stdio`",
        "codex/config.toml includes decision-required server `quarantined-stdio`",
    ]


def test_decision_required_quarantine_gate_reads_list_shaped_mcp_servers():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "quarantined-stdio": {
                "scope": "singleton",
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"],
                "lifecycle": "decision-required",
                "follow_on_decision": "wire-or-retire",
            },
        },
    }
    outputs = {
        "local/.mcp.json": json.dumps({"mcpServers": []}),
        "claude/mcpServers.json": json.dumps(
            {"mcpServers": [{"name": "quarantined-stdio"}]}
        ),
        "codex/config.toml": "",
    }

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        catalog,
        outputs,
    )

    assert errors == [
        "claude/mcpServers.json includes decision-required server `quarantined-stdio`"
    ]


def test_decision_required_quarantine_gate_validates_provided_empty_outputs():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": ["quarantined-local"]},
        "servers": {
            "quarantined-local": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:3999/mcp",
                "lifecycle": "decision-required",
                "follow_on_decision": "delete-or-host-run",
            },
        },
    }

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        catalog,
        {},
    )

    assert errors == ["defaults.per_worktree includes decision-required server `quarantined-local`"]


def test_claude_command_tool_surfaces_are_catalog_known_or_explicit_aliases():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    command_dir = REPO_ROOT / ".claude/commands"

    unknown = fleet_catalog.find_unknown_command_tool_surfaces(command_dir, catalog)

    assert unknown == []


def test_unknown_command_tool_surfaces_are_reported(tmp_path):
    command_dir = tmp_path / "commands"
    command_dir.mkdir()
    (command_dir / "bad.md").write_text("Call `mcp__missing-server__do_work`.\n")
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    unknown = fleet_catalog.find_unknown_command_tool_surfaces(command_dir, catalog)

    assert unknown == [f"{command_dir / 'bad.md'}:1:missing-server"]


def test_mcp_tool_surface_regex_rejects_partial_mentions():
    matches = fleet_catalog.extract_mcp_tool_surfaces(
        "mcp__conport__ok mcp__dope-memory__* mcp__bad mcp____x"
    )

    assert matches == ["conport", "dope-memory"]


def test_no_duplicate_catalog_server_names_in_sample_fixture(tmp_path):
    duplicate = tmp_path / "legacy.yaml"
    duplicate.write_text(
        """
servers:
  one:
    transport: http
  one:
    transport: stdio
""".lstrip()
    )

    with pytest.raises(fleet_catalog.DuplicateKeyError):
        fleet_catalog.load_yaml_no_duplicate_keys(duplicate)


def test_catalog_contract_finds_docker_exec_container_drift(tmp_path):
    compose = {
        "services": {
            "exa": {
                "container_name": "mcp-exa",
                "ports": ["${EXA_PORT:-3011}:3011"],
                "healthcheck": {"test": ["CMD", "true"]},
            }
        }
    }
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "exa": {
                "scope": "singleton",
                "transport": "stdio",
                "command": "docker",
                "args": ["exec", "-i", "mcp-litellm", "python", "/app/exa_server.py"],
                "docker_compose_service": "exa",
            }
        },
    }

    errors = fleet_catalog.validate_catalog_compose_alignment_data(catalog, compose)

    assert re.search(r"exa.*mcp-litellm.*mcp-exa", "\n".join(errors))


def test_catalog_contract_parses_docker_exec_options_with_values():
    compose = {
        "services": {
            "exa": {
                "container_name": "mcp-exa",
                "ports": ["${EXA_PORT:-3011}:3011"],
                "healthcheck": {"test": ["CMD", "true"]},
            }
        }
    }
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "exa": {
                "scope": "singleton",
                "transport": "stdio",
                "command": "docker",
                "args": [
                    "exec",
                    "-i",
                    "-e",
                    "MCP_RUN_MODE=stdio",
                    "--user",
                    "1000:1000",
                    "--workdir=/app",
                    "mcp-exa",
                    "python",
                    "/app/exa_server.py",
                ],
                "docker_compose_service": "exa",
            }
        },
    }

    errors = fleet_catalog.validate_catalog_compose_alignment_data(catalog, compose)

    assert errors == []
