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
from dopemux.mcp.runtime_state import (
    build_desired_services,
    compose_lifecycle_diagnostics,
    resolve_identity_view,
)


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
    diag = compose_lifecycle_diagnostics(None)  # convention path (no compose file)
    codes = {f["code"] for f in diag["findings"]}
    assert "COMPOSE_REQUIRED_IN_CWD" in codes
    assert "COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK" in codes
    assert "COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK" in codes
    assert "DUAL_ALLOCATION_BRAINS" in codes
    assert "INSTANCE_OVERLAY_NOT_WIRED_TO_INIT" in codes
    # Missing compose must not hard-FAIL on convention-only fixed-name / volume risks.
    by_code = {f["code"]: f for f in diag["findings"]}
    assert by_code["COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK"]["severity"] == "WARN"
    assert by_code["COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK"]["severity"] == "WARN"

    path = tmp_path / "compose.yml"
    path.write_text(compose)
    diag2 = compose_lifecycle_diagnostics(path)
    assert any("mcp-conport" in r for r in diag2["fixed_container_name_risks"])
    assert any(".dopemux" in r for r in diag2["relative_volume_risks"])
    by_code2 = {f["code"]: f for f in diag2["findings"]}
    assert by_code2["COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK"]["severity"] == "FAIL"
    assert by_code2["COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK"]["severity"] == "FAIL"
    assert any(
        "DOPEMUX_WORKSPACE_ID" in r for r in diag2["identity_env_risks"]
    )


def test_build_desired_services_unions_catalog_defaults():
    catalog = _catalog()
    # Only conport in mcp.json — defaults still include dope-memory + task-orchestrator
    desired = build_desired_services(
        catalog,
        {"conport": {"type": "sse", "url": "http://localhost:3005/sse"}},
        {"CONPORT_MCP_PORT": "3005", "DOPE_MEMORY_PORT": "3020"},
    )
    names = {s.name for s in desired}
    assert "conport" in names
    assert "dope-memory" in names
    assert "task-orchestrator" in names


def test_resolve_identity_forces_repo_over_ambient(tmp_path: Path):
    target = tmp_path / "target-repo"
    target.mkdir()
    (target / ".git").mkdir()
    foreign = tmp_path / "foreign-repo"
    foreign.mkdir()
    (foreign / ".git").mkdir()

    view = resolve_identity_view(
        target,
        envrc_values={
            "DOPEMUX_WORKSPACE_ROOT": str(foreign),
            "DOPEMUX_PROJECT_ROOT": str(foreign),
            "TASK_ORCHESTRATOR_PROJECT_ROOT": str(foreign),
        },
    )
    assert view.worktree_root == str(target.resolve())
    assert any("forced identity" in e for e in view.evidence)


def test_doctor_ignores_foreign_cwd_compose(tmp_path: Path, monkeypatch):
    repo = _write_fixture_repo(tmp_path)
    foreign = tmp_path / "dopemux-mvp"
    foreign.mkdir()
    (foreign / "compose.yml").write_text(
        """
services:
  conport:
    container_name: ${CONPORT_CONTAINER_NAME:-mcp-conport}
  dope-memory:
    volumes:
      - ./.dopemux:/data
"""
    )
    monkeypatch.chdir(foreign)
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    compose_name = [
        f
        for f in report.findings
        if f["code"] == "COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK"
    ]
    assert compose_name
    assert all(f["severity"] != "FAIL" for f in compose_name)
    assert report.compose_lifecycle_diagnostics.get("compose_present") is False


def test_doctor_formula_reserved_does_not_fail_remapped_dnh(tmp_path: Path):
    """dNh_CRM-shaped remapped envrc must not doctor-FAIL on hash-formula reserved ports."""
    repo = tmp_path / "dNh_CRM"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
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
            }
        )
    )
    (repo / ".envrc.dopemux-mcp").write_text(
        f"""export DOPEMUX_WORKSPACE_ID={repo}
export DOPEMUX_WORKSPACE_ROOT={repo}
export DOPEMUX_PROJECT_ROOT={repo}
export TASK_ORCHESTRATOR_PROJECT_ROOT={repo}
export DOPEMUX_INSTANCE_ID=8d6d
export DOPE_MEMORY_WORKSPACE_ID=dNh_CRM
export DOPE_MEMORY_INSTANCE_ID=8d6d
export CONPORT_MCP_PORT=3041
export CONPORT_HTTP_PORT=3040
export CONPORT_INFO_PORT=4040
export DOPE_MEMORY_PORT=3024
export TASK_ORCHESTRATOR_HTTP_PORT=7890
"""
    )
    report = run_mcp_doctor(
        repo,
        catalog=_catalog(),
        skip_docker=True,
        skip_port_probe=True,
        process_env={},
    )
    reserved = [f for f in report.findings if f["code"] == "PORT_RESERVED_COLLISION"]
    assert not any(f["severity"] == "FAIL" for f in reserved)
    assert report.status != "FAIL"


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


def test_docker_peer_conport_non_overlapping_port_is_info(tmp_path: Path):
    """Foreign labelled ConPort on a different port is peer, not ownership FAIL."""
    repo = _write_fixture_repo(tmp_path)

    def fake_run(*args, **kwargs):
        row = {
            "ID": "peerconport",
            "Names": "dopemux-other-proj-aaaa-conport",
            "Ports": "127.0.0.1:3111->3005/tcp",
            "Labels": (
                "dopemux.project_root=/other/project,"
                "dopemux.workspace_id=/other/project,"
                "dopemux.project_id=other-proj"
            ),
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
    peer = [
        f
        for f in report.findings
        if f["code"] == "DOCKER_PEER_PROJECT_INSTANCE" and f["service"] == "conport"
    ]
    assert peer, report.findings
    assert peer[0]["severity"] == "INFO"
    assert not any(
        f["code"] == "DOCKER_CONTAINER_WRONG_PROJECT" and f["service"] == "conport"
        for f in report.findings
    )
    # Peer classification itself must not contribute a FAIL; ambient lease/compose
    # findings may still fail overall status in shared-host fixtures.
    assert not any(
        f["severity"] == "FAIL"
        and f["code"] in {
            "DOCKER_CONTAINER_WRONG_PROJECT",
            "DOCKER_PEER_PROJECT_INSTANCE",
            "DOCKER_PEER_INSTANCE_UNLABELED",
        }
        and f.get("service") == "conport"
        for f in report.findings
    )


def test_docker_peer_dope_memory_non_overlapping_port_is_info(tmp_path: Path):
    """Foreign labelled dope-memory on a different port is peer, not ownership FAIL."""
    repo = _write_fixture_repo(tmp_path)

    def fake_run(*args, **kwargs):
        row = {
            "ID": "peermem",
            "Names": "dopemux-dnh-crm-8d6d-dope-memory",
            "Ports": "127.0.0.1:3020->3020/tcp",
            "Labels": (
                "dopemux.project_root=/other/project,"
                "dopemux.workspace_id=/other/project,"
                "dopemux.project_id=dnh-crm"
            ),
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
    peer = [
        f
        for f in report.findings
        if f["code"] == "DOCKER_PEER_PROJECT_INSTANCE" and f["service"] == "dope-memory"
    ]
    assert peer, report.findings
    assert peer[0]["severity"] == "INFO"
    assert not any(
        f["code"] == "DOCKER_CONTAINER_WRONG_PROJECT" and f["service"] == "dope-memory"
        for f in report.findings
    )


def test_docker_peer_unlabeled_non_overlapping_is_warn(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)

    def fake_run(*args, **kwargs):
        row = {
            "ID": "peerunlab",
            "Names": "mcp-conport-other",
            "Ports": "127.0.0.1:3999->3005/tcp",
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
    peer = [
        f
        for f in report.findings
        if f["code"] == "DOCKER_PEER_INSTANCE_UNLABELED" and f["service"] == "conport"
    ]
    assert peer, report.findings
    assert peer[0]["severity"] == "WARN"
    assert not any(
        f["code"] == "DOCKER_CONTAINER_UNLABELED_UNKNOWN" and f["service"] == "conport"
        for f in report.findings
    )


def test_docker_exact_expected_container_wrong_project_blocks(tmp_path: Path):
    """Exact lifecycle name with foreign labels remains FAIL even without port overlap."""
    from dopemux.mcp import docker_runtime as dr
    from dopemux.mcp.port_diagnostics import instance_id_for_path
    from dopemux.mcp.doctor import _expected_container_name_for_service
    from dopemux.mcp.runtime_state import resolve_identity_view
    from dopemux.mcp.envrc import load_envrc

    repo = _write_fixture_repo(tmp_path)
    envrc = load_envrc(repo / ".envrc.dopemux-mcp")
    identity = resolve_identity_view(repo, envrc_values=envrc.values)
    expected = _expected_container_name_for_service(
        "conport",
        project_root=identity.project_root,
        worktree_hash=identity.worktree_hash or instance_id_for_path(str(repo)),
        project_id=identity.project_id,
        repo_path=repo,
    )
    assert expected
    # Sanity: name uses lifecycle contract
    assert expected == dr.container_name_for(
        dr.project_slug(repo.name),
        identity.worktree_hash or instance_id_for_path(str(repo)),
        "conport",
    )

    def fake_run(*args, **kwargs):
        row = {
            "ID": "exactwrong",
            "Names": expected,
            "Ports": "127.0.0.1:3998->3005/tcp",
            "Labels": (
                "dopemux.project_root=/other/project,"
                "dopemux.workspace_id=/other/project,"
                "dopemux.project_id=other"
            ),
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
    assert any(
        f["code"] == "DOCKER_CONTAINER_WRONG_PROJECT" and f["service"] == "conport"
        for f in report.findings
    )
    assert report.status == "FAIL"


def test_docker_exact_expected_container_unlabeled_fail_closed(tmp_path: Path):
    from dopemux.mcp.doctor import _expected_container_name_for_service
    from dopemux.mcp.envrc import load_envrc
    from dopemux.mcp.port_diagnostics import instance_id_for_path
    from dopemux.mcp.runtime_state import resolve_identity_view

    repo = _write_fixture_repo(tmp_path)
    envrc = load_envrc(repo / ".envrc.dopemux-mcp")
    identity = resolve_identity_view(repo, envrc_values=envrc.values)
    expected = _expected_container_name_for_service(
        "conport",
        project_root=identity.project_root,
        worktree_hash=identity.worktree_hash or instance_id_for_path(str(repo)),
        project_id=identity.project_id,
        repo_path=repo,
    )
    assert expected

    def fake_run(*args, **kwargs):
        row = {
            "ID": "exactunlab",
            "Names": expected,
            "Ports": "127.0.0.1:3997->3005/tcp",
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
    assert any(
        f["code"] == "DOCKER_CONTAINER_UNLABELED_UNKNOWN" and f["service"] == "conport"
        for f in report.findings
    )


def test_docker_task_orchestrator_wrong_project_on_7890_blocks(tmp_path: Path):
    repo = _write_fixture_repo(tmp_path)

    def fake_run(*args, **kwargs):
        row = {
            "ID": "toforeign",
            "Names": "task-orchestrator-other-deadbeef",
            "Ports": "127.0.0.1:7890->7890/tcp",
            "Labels": (
                "dopemux.project_root=/other/project,"
                "dopemux.workspace_id=/other/project,"
                "dopemux.project_id=other-proj,"
                "dopemux.managed=true,"
                "dopemux.service=task-orchestrator"
            ),
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
    codes = {f["code"] for f in report.findings if f.get("service") == "task-orchestrator"}
    # Port-overlap foreign holder must remain a hard ownership/runtime conflict.
    assert (
        "DOCKER_CONTAINER_WRONG_PROJECT" in codes
        or "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME" in codes
        or any(
            f["code"] == "DOCKER_CONTAINER_PORT_COLLISION"
            and f.get("service") == "task-orchestrator"
            for f in report.findings
        )
    ), report.findings
    assert "DOCKER_PEER_PROJECT_INSTANCE" not in {
        f["code"] for f in report.findings if f.get("service") == "task-orchestrator"
    }


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


def test_build_desired_services_includes_catalog_defaults_when_mcp_json_present():
    """Doctor coverage must not drop catalog defaults just because .mcp.json exists."""
    catalog = _catalog()
    mcp_servers = {
        "conport": {"type": "sse", "url": "http://localhost:${CONPORT_MCP_PORT}/sse"},
    }
    desired = build_desired_services(
        catalog,
        mcp_servers,
        {"CONPORT_MCP_PORT": "3041", "DOPE_MEMORY_PORT": "3020"},
    )
    names = [d.name for d in desired]
    assert "conport" in names
    assert "dope-memory" in names
    assert "task-orchestrator" in names
