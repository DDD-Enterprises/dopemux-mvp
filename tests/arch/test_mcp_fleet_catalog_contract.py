import json
import re
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp import fleet_catalog


REPO_ROOT = Path(__file__).resolve().parents[2]


def _reserved_singleton_catalog() -> dict:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["task-orchestrator"]},
        "servers": {
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "single_active_project",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "url_template": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
                "port_policy": "reserved_singleton",
                "reserved_port": 7890,
            }
        },
    }


def test_root_catalog_conforms_to_schema():
    schema = fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog.schema.json")
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    jsonschema.validate(catalog, schema)


def test_schema_accepts_reserved_singleton_runtime_metadata():
    schema = fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog.schema.json")

    jsonschema.validate(_reserved_singleton_catalog(), schema)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state_scope", "global-mutable"),
        ("port_policy", "dynamic-rebind"),
    ],
)
def test_schema_rejects_unknown_reserved_singleton_metadata(field, value):
    schema = fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog.schema.json")
    catalog = _reserved_singleton_catalog()
    catalog["servers"]["task-orchestrator"][field] = value

    with pytest.raises(jsonschema.ValidationError):
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


def test_personality_contract_requires_presence_of_all_personality_fields_on_every_server():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    del catalog["servers"]["serena"]["identity_scope"]

    errors = fleet_catalog.validate_catalog_personality_contract(catalog)

    assert any(
        "serena: missing required personality field(s)" in error and "identity_scope" in error
        for error in errors
    )


def test_all_catalog_servers_carry_full_personality_metadata():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    errors = fleet_catalog.validate_catalog_personality_contract(catalog)

    assert errors == []


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


def test_dead_fleet_service_names_are_not_compose_services():
    compose = fleet_catalog.load_compose(REPO_ROOT)
    services = set(compose.get("services") or {})

    # Kill-list: dead service directories that must never become startable via
    # compose. These exist on disk (services/mcp-integration-bridge, etc.) but
    # must not be wired into compose.yml. `exa`/`mcp-exa` was retired by
    # ADR-223 (PR #1002 audit found zero client consumers and a broken exec
    # target); it must never come back as a compose service without a fresh
    # catalog entry + wiring + a superseding ADR.
    dead_service_names = {"mcp-integration-bridge", "mcp-client", "router", "exa", "mcp-exa"}
    assert dead_service_names.isdisjoint(services)

    # Positive control: known-live compose services must actually be present,
    # otherwise the assertion above would be vacuous.
    assert {"dopecon-bridge", "task-orchestrator", "conport"}.issubset(services)


def test_generated_fleet_outputs_never_reference_dead_service_paths_or_scripts():
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    outputs = fleet_catalog.generate_fleet_output_files(catalog)
    combined = "\n".join(outputs.values())

    dead_references = [
        "services/mcp-integration-bridge",
        "services/mcp-client",
        "services/router",
        "services/serena/v2/mcp_server.py",
        "services/dope-context/src/mcp/simple_server.py",
        "wire_claude_mcp.py",
        "manage-mcp-servers.sh",
        "conport-wrapper.sh",
        "serena-wrapper.sh",
    ]
    found = [ref for ref in dead_references if ref in combined]

    assert found == []


def test_mcp_integration_bridge_dockerfile_does_not_exist():
    assert not (REPO_ROOT / "services/mcp-integration-bridge/Dockerfile").exists()


def test_exa_mcp_server_source_does_not_exist():
    """exa was retired by ADR-223: source tree must stay deleted."""
    assert not (REPO_ROOT / "docker/mcp-servers-source/exa").exists()
    assert not (REPO_ROOT / "docker/mcp-servers/exa").exists()


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


def test_unknown_conport_command_tool_is_reported(tmp_path):
    command_dir = tmp_path / "commands"
    command_dir.mkdir()
    (command_dir / "bad.md").write_text("Call `mcp__conport__missing_tool`.\n")
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    unknown = fleet_catalog.find_unknown_command_tool_surfaces(command_dir, catalog)

    assert unknown == [f"{command_dir / 'bad.md'}:1:conport:missing_tool"]


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

# ---------------------------------------------------------------------------
# MCPINT-FND-CATALOG-001 — catalog completion, schema repair, transport truth
# ---------------------------------------------------------------------------


def _schema():
    return fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog.schema.json")


def _catalog_with_server(spec):
    return {"version": 1, "defaults": {"per_worktree": []}, "servers": {"probe": spec}}


def _valid_http_server(**overrides):
    spec = {
        "scope": "singleton",
        "transport": "http",
        "plane": "research",
        "authority_role": "web-search",
        "lifecycle": "active",
        "management_model": "compose-service",
        "identity_scope": "singleton",
        "follow_on_decision": "none",
        "url": "http://localhost:3999/mcp",
    }
    spec.update(overrides)
    return spec


def test_schema_still_rejects_unknown_server_fields():
    spec = _valid_http_server(bogus_field="nope")

    with pytest.raises(jsonschema.ValidationError, match="bogus_field"):
        jsonschema.validate(_catalog_with_server(spec), _schema())


def test_schema_admits_reserved_singleton_port_policy_and_rejects_unknown_values():
    jsonschema.validate(
        _catalog_with_server(_valid_http_server(port_policy="reserved_singleton")),
        _schema(),
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _catalog_with_server(_valid_http_server(port_policy="first_come_first_served")),
            _schema(),
        )


def test_schema_agents_matrix_is_closed():
    schema = _schema()

    jsonschema.validate(
        _catalog_with_server(_valid_http_server(agents="none")),
        schema,
    )
    jsonschema.validate(
        _catalog_with_server(
            _valid_http_server(agents={"claude": "full", "codex": "full-sequenced"})
        ),
        schema,
    )

    with pytest.raises(jsonschema.ValidationError):
        # Empty object must not satisfy the matrix branch.
        jsonschema.validate(_catalog_with_server(_valid_http_server(agents={})), schema)
    with pytest.raises(jsonschema.ValidationError):
        # Unknown agent key.
        jsonschema.validate(
            _catalog_with_server(_valid_http_server(agents={"cursor": "full"})),
            schema,
        )
    with pytest.raises(jsonschema.ValidationError):
        # Value outside the exposure enum.
        jsonschema.validate(
            _catalog_with_server(_valid_http_server(agents={"claude": "sometimes"})),
            schema,
        )
    with pytest.raises(jsonschema.ValidationError):
        # Only the exact sentinel string is admitted.
        jsonschema.validate(
            _catalog_with_server(_valid_http_server(agents="NONE")),
            schema,
        )


def test_schema_planned_active_http_entry_may_omit_url_but_active_may_not():
    schema = _schema()
    planned = _valid_http_server(lifecycle="planned-active")
    del planned["url"]

    jsonschema.validate(_catalog_with_server(planned), schema)

    active_without_url = _valid_http_server()
    del active_without_url["url"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_catalog_with_server(active_without_url), schema)


def test_schema_external_transport_requires_managed_and_forbids_endpoints():
    schema = _schema()
    external = {
        "scope": "singleton",
        "transport": "external",
        "managed": False,
        "plane": "research",
        "authority_role": "docs-lookup",
        "lifecycle": "operator-managed",
        "management_model": "external",
        "identity_scope": "external-provider",
        "follow_on_decision": "none",
    }

    jsonschema.validate(_catalog_with_server(dict(external)), schema)

    missing_managed = dict(external)
    del missing_managed["managed"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_catalog_with_server(missing_managed), schema)

    with_url = dict(external, url="http://localhost:1234/mcp")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_catalog_with_server(with_url), schema)

    with_command = dict(external, command="npx")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_catalog_with_server(with_command), schema)


def test_catalog_completion_adds_missing_running_and_external_servers():
    servers = fleet_catalog.load_root_catalog(REPO_ROOT)["servers"]

    assert servers["leantime-bridge"]["agents"] == "none"
    assert servers["leantime-bridge"]["plane"] == "pm"
    assert servers["dcp-readonly-facade"]["lifecycle"] == "planned-active"
    assert "url" not in servers["dcp-readonly-facade"]
    for name in ("mcp-registry", "scheduled-tasks", "context7"):
        assert servers[name]["managed"] is False
        assert servers[name]["transport"] == "external"


def test_catalog_pal_entry_is_health_only_and_quarantined():
    """Transport truth, P0 claim 11: :3003/mcp does not exist; /health does."""
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    pal = catalog["servers"]["pal"]

    assert pal["lifecycle"] == "decision-required"
    assert pal["follow_on_decision"] == "wire-or-retire"
    assert pal["url"].endswith("/health")
    assert "/mcp" not in pal["url"]
    assert fleet_catalog.validate_catalog_personality_contract(catalog) == []


def test_catalog_gpt_researcher_notes_non_contractual_messages_surface():
    """Transport truth, P0 claim 12 (GPTR-TRANSPORT-TRUTH)."""
    gptr = fleet_catalog.load_root_catalog(REPO_ROOT)["servers"]["gpt-researcher"]

    assert gptr["transport"] == "stdio"
    surfaces = gptr.get("aux_surfaces") or []
    assert any(
        surface["url"] == "http://localhost:3009/messages"
        and surface["contractual"] is False
        for surface in surfaces
    )


def test_catalog_marks_conport_admin_tools_operator_only():
    conport = fleet_catalog.load_root_catalog(REPO_ROOT)["servers"]["conport"]

    assert conport["admin_tools"] == ["fork_instance", "promote", "promote_all"]


def test_catalog_tools_pointers_resolve_into_committed_snapshot():
    snapshot = json.loads((REPO_ROOT / "mcp_tool_surfaces.json").read_text(encoding="utf-8"))
    snapshot_servers = set(snapshot["servers"])
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)

    for name, spec in catalog["servers"].items():
        pointer = spec.get("tools")
        if pointer is None:
            continue
        assert pointer["snapshot_key"] in snapshot_servers, (
            f"{name}: tools.snapshot_key `{pointer['snapshot_key']}` not in mcp_tool_surfaces.json"
        )
        assert pointer["schema_version"] == snapshot["schema_version"], (
            f"{name}: tools.schema_version {pointer['schema_version']} != "
            f"snapshot schema_version {snapshot['schema_version']}"
        )


def test_generated_outputs_exclude_non_agent_surfaces():
    """agents:none / planned-active / managed:false entries never become startable."""
    catalog = fleet_catalog.load_root_catalog(REPO_ROOT)
    outputs = fleet_catalog.generate_fleet_output_files(catalog)

    excluded = {
        "pal",
        "leantime-bridge",
        "dcp-readonly-facade",
        "mcp-registry",
        "scheduled-tasks",
        "context7",
        "desktop-commander",
    }
    local_servers = set(json.loads(outputs["local/.mcp.json"])["mcpServers"])
    claude_servers = set(json.loads(outputs["claude/mcpServers.json"])["mcpServers"])
    codex_servers = set(
        re.findall(r'^\[mcp_servers\."([^"]+)"\]$', outputs["codex/config.toml"], re.MULTILINE)
    )

    assert local_servers.isdisjoint(excluded)
    assert claude_servers.isdisjoint(excluded)
    assert codex_servers.isdisjoint(excluded)
    # Positive control: real agent surfaces still render.
    assert {"gpt-researcher", "pal-stdio", "serena", "dope-context"} <= claude_servers


def test_legacy_registry_is_marked_deprecated():
    header = (REPO_ROOT / "src/dopemux/mcp/registry.yaml").read_text(encoding="utf-8")

    assert header.startswith("# DEPRECATED")
    assert "mcp_catalog.yaml" in header
