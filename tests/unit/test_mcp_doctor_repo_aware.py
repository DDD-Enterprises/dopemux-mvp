"""Unit tests for repo-aware MCP doctor (TP-DMX-MCP-RUNTIME-001)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import yaml
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp.doctor import format_human_summary, run_mcp_doctor
from dopemux.mcp.project_identity import resolve_project_identity
from dopemux.mcp.runtime_state import compose_lifecycle_diagnostics


def _catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport", "dope-memory", "task-orchestrator"]},
        "servers": {
            "pal": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3003/mcp",
            },
            "gpt-researcher": {
                "scope": "singleton",
                "transport": "stdio",
                "reserved_port": 3009,
            },
            "dope-context": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3010/mcp",
            },
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
                "requires_env": ["DOPEMUX_WORKSPACE_ID"],
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
                "requires_env": ["DOPE_MEMORY_WORKSPACE_ID", "DOPE_MEMORY_INSTANCE_ID"],
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "per-repo",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "url_template": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
                "requires_env": ["TASK_ORCHESTRATOR_PROJECT_ROOT"],
            },
        },
    }


def _write_fixture_repo(
    tmp_path: Path,
    *,
    mcp_servers: dict | None = None,
    envrc: str | None = None,
    compose: str | None = None,
) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    servers = mcp_servers or {
        "conport": {
            "type": "sse",
            "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
        },
        "dope-memory": {
            "type": "http",
            "url": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
        },
        "task-orchestrator": {
            "type": "http",
            "url": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
        },
    }
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n")
    if envrc is None:
        envrc = f"""export DOPEMUX_WORKSPACE_ID={repo}
export DOPEMUX_WORKSPACE_ROOT={repo}
export DOPEMUX_PROJECT_ROOT={repo}
export TASK_ORCHESTRATOR_PROJECT_ROOT={repo}
export DOPEMUX_INSTANCE_ID=abcd
export DOPE_MEMORY_WORKSPACE_ID=proj
export DOPE_MEMORY_INSTANCE_ID=abcd
export CONPORT_MCP_PORT=3041
export CONPORT_HTTP_PORT=3040
export CONPORT_INFO_PORT=4040
export DOPE_MEMORY_PORT=3060
export TASK_ORCHESTRATOR_HTTP_PORT=7890
"""
    (repo / ".envrc.dopemux-mcp").write_text(envrc)
    if compose is not None:
        (repo / "compose.yml").write_text(compose)
    return repo


def test_doctor_loads_envrc_and_json_keys(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    assert report.config_sources["envrc"]["present"] is True
    assert report.config_sources["envrc"]["parse_status"] == "OK"
    assert "CONPORT_MCP_PORT" in report.config_sources["envrc"]["keys_present"]
    assert report.config_sources["envrc"]["redacted"] is True
    assert report.schema_version == "1.0"
    codes = {f["code"] for f in report.findings}
    assert "ENVRC_FOUND" in codes
    assert "MCP_JSON_FOUND" in codes


def test_transport_match_and_mismatch(tmp_path: Path):
    repo = _write_fixture_repo(
        tmp_path,
        mcp_servers={
            "conport": {"type": "sse", "url": "http://localhost:${CONPORT_MCP_PORT}/sse"},
            "dope-memory": {"type": "sse", "url": "http://localhost:${DOPE_MEMORY_PORT}/mcp"},
            "task-orchestrator": {
                "type": "sse",
                "url": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT}/mcp",
            },
        },
    )
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    codes = {(f["code"], f["service"]) for f in report.findings}
    assert ("TRANSPORT_MISMATCH", "dope-memory") in codes
    assert ("TRANSPORT_MISMATCH", "task-orchestrator") in codes
    assert ("TRANSPORT_MATCH", "conport") in codes
    assert report.status == "FAIL"
    assert report.exit_code == 1


def test_compose_lifecycle_hazards_from_fixture(tmp_path: Path):
    compose = """
services:
  conport:
    container_name: ${CONPORT_CONTAINER_NAME:-mcp-conport}
    environment:
      - DOPEMUX_INSTANCE_ID=${DOPEMUX_INSTANCE_ID:-}
  dope-memory:
    volumes:
      - ./.dopemux:/data
"""
    diag = compose_lifecycle_diagnostics(None)  # convention path
    codes = {f["code"] for f in diag["findings"]}
    assert "COMPOSE_REQUIRED_IN_CWD" in codes
    assert "COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK" in codes
    assert "COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK" in codes
    assert "DUAL_ALLOCATION_BRAINS" in codes
    assert "INSTANCE_OVERLAY_NOT_WIRED_TO_INIT" in codes

    path = tmp_path / "compose.yml"
    path.write_text(compose)
    diag2 = compose_lifecycle_diagnostics(path)
    assert any("mcp-conport" in r for r in diag2["fixed_container_name_risks"])
    assert any(".dopemux" in r for r in diag2["relative_volume_risks"])


def test_compose_no_hazard_minimal():
    # Even empty compose still flags dual allocator / cwd requirement (architectural)
    diag = compose_lifecycle_diagnostics(None)
    assert diag["compose_required_in_cwd"] is True


def test_global_local_duplicate_and_dead(tmp_path: Path, monkeypatch):
    repo = _write_fixture_repo(tmp_path)
    global_path = tmp_path / "claude.json"
    global_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "conport": {
                        "type": "sse",
                        "url": "http://localhost:3039/sse",
                    },
                    "pal": {
                        "type": "http",
                        "url": "http://localhost:3003/mcp",
                    },
                }
            }
        )
    )
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        global_claude_path=global_path,
        skip_docker=True,
        skip_port_probe=False,
        port_is_free_fn=lambda port: True,  # nothing listening
        process_env={},
    )
    codes = {f["code"] for f in report.findings}
    assert "GLOBAL_LOCAL_DUPLICATE" in codes
    assert "GLOBAL_SERVICE_DEAD" in codes


def test_global_malformed(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)
    global_path = tmp_path / "claude.json"
    global_path.write_text("{not json")
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        global_claude_path=global_path,
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    assert report.config_sources["global_claude"]["parse_status"] == "ERROR"


def test_docker_wrong_project_fail(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)

    def fake_run(*args, **kwargs):
        row = {
            "ID": "deadbeef",
            "Names": "mcp-conport",
            "Ports": "0.0.0.0:3041->3005/tcp",
            "Labels": "dopemux.project_root=/other/project,dopemux.workspace_id=/other/project",
            "Image": "x",
            "Status": "Up",
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(row) + "\n", stderr="")

    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        docker_runner=fake_run,
        skip_port_probe=True,
        process_env={},
    )
    assert any(f["code"] == "DOCKER_CONTAINER_WRONG_PROJECT" for f in report.findings)
    assert report.status == "FAIL"


def test_docker_unlabeled_unknown(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)

    def fake_run(*args, **kwargs):
        row = {
            "ID": "deadbeef",
            "Names": "mcp-conport",
            "Ports": "0.0.0.0:3041->3005/tcp",
            "Labels": "",
            "Image": "x",
            "Status": "Up",
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(row) + "\n", stderr="")

    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        docker_runner=fake_run,
        skip_port_probe=True,
        process_env={},
    )
    assert any(f["code"] == "DOCKER_CONTAINER_UNLABELED_UNKNOWN" for f in report.findings)
    # Must not greenwash ownership
    assert report.status in {"UNKNOWN", "PASS_WITH_WARNINGS", "FAIL"}


def test_listening_port_not_pass_without_identity(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=False,
        port_is_free_fn=lambda port: False,  # all listening
        process_env={},
    )
    codes = {f["code"] for f in report.findings}
    assert "PORT_LISTENING" in codes
    assert "PORT_OWNERSHIP_UNKNOWN" in codes
    assert report.status != "PASS"


def test_project_identity_nested_and_override(tmp_path: Path):
    # Nested directory inside a fake git root via resolve_project_identity overrides
    root = tmp_path / "wt"
    root.mkdir()
    nested = root / "src"
    nested.mkdir()
    identity = resolve_project_identity(
        cwd=nested,
        env={
            "DOPEMUX_WORKSPACE_ROOT": str(root),
            "DOPEMUX_PROJECT_ROOT": str(root),
        },
    )
    assert identity.worktree_root == root.resolve()
    assert identity.project_root == root.resolve()


def test_cli_doctor_repo_json(tmp_path: Path, monkeypatch):
    repo = _write_fixture_repo(tmp_path)
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(mcp_commands, "_catalog_path", lambda: None)

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["doctor", "--repo", str(repo), "--json", "--skip-docker"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "1.0"
    assert "findings" in payload
    assert "port_diagnostics" in payload
    assert "compose_lifecycle_diagnostics" in payload
    assert payload["config_sources"]["envrc"]["redacted"] is True


def test_cli_doctor_repo_human(tmp_path: Path, monkeypatch):
    repo = _write_fixture_repo(
        tmp_path,
        mcp_servers={
            "dope-memory": {"type": "sse", "url": "http://localhost:3060/mcp"},
        },
    )
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(mcp_commands, "_catalog_path", lambda: None)
    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["doctor", "--repo", str(repo), "--skip-docker"],
    )
    assert "MCP Doctor" in result.output
    assert "TRANSPORT_MISMATCH" in result.output or "FAIL" in result.output


def test_format_human_summary_compact(tmp_path: Path):
    repo = _write_fixture_repo(
        tmp_path,
        mcp_servers={
            "dope-memory": {"type": "sse", "url": "http://localhost:3060/mcp"},
        },
    )
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    text = format_human_summary(report)
    assert text.startswith("MCP Doctor")
    assert "Next action:" in text
    # Max 5 top findings lines + headers
    finding_lines = [ln for ln in text.splitlines() if ln[:1].isdigit() and ". " in ln]
    assert len(finding_lines) <= 5


def test_json_deterministic_key_presence(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    d = report.to_dict()
    for key in (
        "schema_version",
        "status",
        "repo_arg",
        "project_identity",
        "config_sources",
        "desired_services",
        "actual_services",
        "port_diagnostics",
        "compose_lifecycle_diagnostics",
        "findings",
        "unknowns",
        "recommended_next_actions",
    ):
        assert key in d
    # Deterministic serialization (sorted keys)
    a = report.to_json()
    b = report.to_json()
    assert a == b


def test_root_catalog_transports_match_expected():
    """Catalog truth for core services (not hardcoded in doctor)."""
    root = Path(__file__).resolve().parents[2]
    catalog = yaml.safe_load((root / "mcp_catalog.yaml").read_text())
    servers = catalog["servers"]
    assert servers["conport"]["transport"] == "sse"
    assert servers["dope-memory"]["transport"] == "http"
    assert servers["task-orchestrator"]["transport"] == "http"
