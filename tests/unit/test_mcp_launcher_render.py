"""Catalog `client: launcher` shape, stdio launcher render, doctor and repair parity (M1 Task 3a)."""

from __future__ import annotations

import json
from pathlib import Path

from dopemux.commands import mcp_commands
from dopemux.mcp import fleet_catalog
from dopemux.mcp.doctor import run_mcp_doctor
from dopemux.mcp.mcp_json import plan_mcp_json_repairs
from dopemux.mcp.runtime_state import build_desired_services, sidecar_url

from tests.unit.test_mcp_doctor_repo_aware import _catalog, _write_fixture_repo


def _launcher_spec(**overrides):
    spec = {
        "scope": "per-worktree",
        "transport": "sse",
        "client": "launcher",
        "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
        "port_var": "CONPORT_MCP_PORT",
        "default_port_base": 3005,
        "requires_env": [],
        "optional_env": ["GEMINI_API_KEY"],
        "description": "Knowledge graph",
    }
    spec.update(overrides)
    return spec


def _launcher_catalog():
    catalog = _catalog()
    for name in ("conport", "dope-memory", "task-orchestrator"):
        catalog["servers"][name]["client"] = "launcher"
        catalog["servers"][name]["requires_env"] = []
    return catalog


def _launcher_entry(name: str, description: str | None = None):
    entry = {
        "type": "stdio",
        "command": "${DOPEMUX_BIN:-dopemux}",
        "args": ["mcp", "launch", name],
    }
    if description:
        entry["description"] = description
    return entry


def test_render_local_entry_launcher_shape():
    entry = mcp_commands._render_local_entry("conport", _launcher_spec())

    assert entry == {
        "type": "stdio",
        "command": "${DOPEMUX_BIN:-dopemux}",
        "args": ["mcp", "launch", "conport"],
        "description": "Knowledge graph",
    }
    assert "env" not in entry


def test_render_local_entry_without_client_unchanged():
    spec = _launcher_spec()
    del spec["client"]

    entry = mcp_commands._render_local_entry("conport", spec)

    assert entry["type"] == "sse"
    assert entry["url"] == "http://localhost:${CONPORT_MCP_PORT:-3005}/sse"
    assert entry["env"] == {"GEMINI_API_KEY": "${GEMINI_API_KEY:-}"}


def test_expected_client_type_launcher_is_stdio():
    assert fleet_catalog.catalog_client_shape(_launcher_spec()) == "launcher"
    assert fleet_catalog.expected_client_type(_launcher_spec()) == "stdio"
    assert fleet_catalog.catalog_client_shape({"transport": "sse"}) == "direct"
    assert fleet_catalog.expected_client_type({"transport": "sse"}) == "sse"
    assert fleet_catalog.expected_client_type({"transport": "http", "client": "direct"}) == "http"


def test_sidecar_url_expands_port_var():
    spec = _launcher_spec()

    assert sidecar_url(spec, {"CONPORT_MCP_PORT": 3007}) == "http://localhost:3007/sse"
    assert sidecar_url(spec, {}) == "http://localhost:3005/sse"


def test_doctor_accepts_stdio_entry_for_launcher_spec(tmp_path: Path):
    repo = _write_fixture_repo(
        tmp_path,
        mcp_servers={
            "conport": _launcher_entry("conport"),
            "dope-memory": _launcher_entry("dope-memory"),
            "task-orchestrator": _launcher_entry("task-orchestrator"),
        },
    )

    report = run_mcp_doctor(
        repo,
        catalog=_launcher_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )

    codes = {(f["code"], f.get("service")) for f in report.findings}
    assert not [c for c in codes if c[0] == "TRANSPORT_MISMATCH"]
    assert ("TRANSPORT_MATCH", "conport") in codes


def test_doctor_flags_url_entry_for_launcher_spec(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)  # old URL-shaped entries

    report = run_mcp_doctor(
        repo,
        catalog=_launcher_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )

    mismatched = {f["service"] for f in report.findings if f["code"] == "TRANSPORT_MISMATCH"}
    assert mismatched == {"conport", "dope-memory", "task-orchestrator"}


def test_repair_plans_launcher_entry_from_url_entry():
    catalog = _launcher_catalog()
    old = {
        "conport": {"type": "sse", "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse"},
    }

    merged, planned, _preserved = plan_mcp_json_repairs(
        old, catalog, mcp_json_path=".mcp.json", include_defaults=False
    )

    assert merged["conport"]["type"] == "stdio"
    assert merged["conport"]["command"] == "${DOPEMUX_BIN:-dopemux}"
    assert merged["conport"]["args"] == ["mcp", "launch", "conport"]
    assert "url" not in merged["conport"]
    assert [c["service"] for c in planned] == ["conport"]
    assert planned[0]["reason"] == "TRANSPORT_MISMATCH"


def test_repair_leaves_current_launcher_entry_alone():
    catalog = _launcher_catalog()
    current = {"conport": _launcher_entry("conport")}

    merged, planned, _preserved = plan_mcp_json_repairs(
        current, catalog, mcp_json_path=".mcp.json", include_defaults=False
    )

    assert planned == []
    assert merged == current


def test_build_desired_services_uses_sidecar_url_for_launcher():
    catalog = _launcher_catalog()
    stdio_servers = {"conport": _launcher_entry("conport")}

    desired = {
        d.name: d
        for d in build_desired_services(
            catalog,
            stdio_servers,
            {},
            configured_ports={"CONPORT_MCP_PORT": 3041},
        )
    }

    assert desired["conport"].expected_urls == ["http://localhost:3041/sse"]
    assert desired["conport"].catalog_transport == "sse"
    assert desired["conport"].mcp_json_transport == "stdio"


def test_copilot_proxy_config_renders_launcher_as_command_args():
    import yaml

    catalog = fleet_catalog.load_root_catalog(Path(__file__).resolve().parents[2])
    servers = yaml.safe_load(fleet_catalog.render_copilot_proxy_config(catalog))["mcpServers"]

    assert servers["conport"] == {
        "type": "stdio",
        "command": "${DOPEMUX_BIN:-dopemux}",
        "args": ["mcp", "launch", "conport"],
    }
