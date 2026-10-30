"""Decision-required quarantine gate coverage for profile outputs (ADR-MCPINT-001 §12.5).

Pure-function tests use the ``outputs`` injection point of
``validate_decision_required_generated_config_quarantine``; the CLI test
monkeypatches generation so no real catalog, repo, or network is touched.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp import fleet_catalog, profile_policy


def _catalog() -> dict:
    return {
        "version": 1,
        "defaults": {"per_worktree": []},
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
        "profiles": {"default": {"description": "test", "servers": ["active-stdio"]}},
    }


def _profile_outputs(mcp_servers: dict, local_servers: dict) -> dict[str, str]:
    return {
        "profiles/default/inventory.json": json.dumps({"profile": "default"}),
        "profiles/default/.mcp.json": json.dumps({"mcpServers": local_servers}),
        "profiles/default/mcpServers.json": json.dumps(
            {"profile": "default", "mcpServers": mcp_servers}
        ),
    }


def test_profile_mcp_servers_output_with_decision_required_server_is_an_error():
    outputs = _profile_outputs({"active-stdio": {}, "quarantined-stdio": {}}, {})

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        _catalog(), outputs
    )

    assert errors == [
        "profiles/default/mcpServers.json includes decision-required server `quarantined-stdio`"
    ]


def test_profile_local_mcp_json_output_with_decision_required_server_is_an_error():
    outputs = _profile_outputs({"active-stdio": {}}, {"quarantined-local": {}})

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        _catalog(), outputs
    )

    assert errors == [
        "profiles/default/.mcp.json includes decision-required server `quarantined-local`"
    ]


def test_clean_profile_outputs_produce_no_errors():
    outputs = _profile_outputs({"active-stdio": {}}, {})

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        _catalog(), outputs
    )

    assert errors == []


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("mcpServers: [unterminated", id="unparseable-yaml"),
        pytest.param("- just\n- a\n- list\n", id="non-dict-top-level"),
    ],
)
def test_copilot_output_shape_problems_are_errors_not_exceptions(payload):
    outputs = {"copilot/mcp-proxy-config.copilot.yaml": payload}

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        _catalog(), outputs
    )

    assert len(errors) == 1
    assert errors[0].startswith("copilot/mcp-proxy-config.copilot.yaml ")


def test_opencode_list_shaped_mcp_is_an_error_not_a_type_error():
    outputs = {
        "opencode/opencode.managed.jsonc": json.dumps(
            {"mcp": [{"name": "quarantined-stdio"}]}
        ),
    }

    errors = fleet_catalog.validate_decision_required_generated_config_quarantine(
        _catalog(), outputs
    )

    assert len(errors) == 1
    assert errors[0].startswith("opencode/opencode.managed.jsonc ")
    assert "includes decision-required" not in errors[0]


def test_generate_profile_cli_fails_closed_before_writing_quarantined_output(
    tmp_path, monkeypatch
):
    catalog = _catalog()
    output_dir = tmp_path / "out"
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    quarantined_outputs = _profile_outputs(
        {"active-stdio": {}, "quarantined-stdio": {}}, {"quarantined-local": {}}
    )

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(repo_dir)
    )
    monkeypatch.setattr(
        profile_policy, "resolve_default_profile", lambda _catalog, name: name
    )
    monkeypatch.setattr(
        fleet_catalog,
        "generate_profile_output_files",
        lambda _catalog, _profile, *, repo_root=None: dict(quarantined_outputs),
    )

    result = CliRunner().invoke(
        mcp_commands.mcp_generate_cmd,
        ["--profile", "default", "--apply", "--output-dir", str(output_dir)],
    )

    assert result.exit_code != 0, result.output
    assert "profiles/default/mcpServers.json" in result.output
    assert "quarantined-stdio" in result.output
    assert "profiles/default/.mcp.json" in result.output
    assert "quarantined-local" in result.output
    assert not output_dir.exists() or not any(output_dir.rglob("*"))
    assert not any(repo_dir.iterdir())
