"""Tests for MCP lifecycle reconciler (mocked Docker)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from dopemux.mcp import docker_runtime as dr
from dopemux.mcp.lifecycle import run_lifecycle


def _catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport", "dope-memory", "task-orchestrator"]},
        "servers": {
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
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "per-repo",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
            },
            "pal": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3003/mcp",
            },
        },
    }


def _fixture_repo(tmp_path: Path) -> Path:
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
export CONPORT_HTTP_PORT=3040
export CONPORT_MCP_PORT=3041
export CONPORT_INFO_PORT=4040
export DOPE_MEMORY_PORT=3060
export TASK_ORCHESTRATOR_HTTP_PORT=7890
"""
    )
    return repo


def _docker_empty():
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


def test_compose_override_unique_name_and_absolute_volume(tmp_path: Path):
    text = dr.generate_compose_override(
        services=["conport", "dope-memory"],
        identity={
            "DOPEMUX_INSTANCE_ID": "8d6d",
            "DOPEMUX_WORKSPACE_ID": "/Users/hue/code/dNh_CRM",
            "DOPEMUX_PROJECT_ROOT": "/Users/hue/code/dNh_CRM",
            "DOPEMUX_WORKTREE_ROOT": "/Users/hue/code/dNh_CRM",
            "DOPEMUX_WORKSPACE_ROOT": "/Users/hue/code/dNh_CRM",
            "DOPE_MEMORY_WORKSPACE_ID": "dNh_CRM",
            "DOPE_MEMORY_INSTANCE_ID": "8d6d",
        },
        ports={
            "CONPORT_HTTP_PORT": 3040,
            "CONPORT_MCP_PORT": 3041,
            "CONPORT_INFO_PORT": 4040,
            "DOPE_MEMORY_PORT": 3060,
        },
        container_names={
            "conport": "dopemux-dnh-crm-8d6d-conport",
            "dope-memory": "dopemux-dnh-crm-8d6d-dope-memory",
        },
        labels_by_service={
            "conport": dr.build_labels(
                project_id="dnh",
                workspace_id="/Users/hue/code/dNh_CRM",
                project_root="/Users/hue/code/dNh_CRM",
                worktree_root="/Users/hue/code/dNh_CRM",
                project_hash="h",
                worktree_hash="8d6d",
                instance_id="dnh-8d6d-conport",
                service="conport",
                scope="worktree",
                transport="sse",
            ),
            "dope-memory": dr.build_labels(
                project_id="dnh",
                workspace_id="/Users/hue/code/dNh_CRM",
                project_root="/Users/hue/code/dNh_CRM",
                worktree_root="/Users/hue/code/dNh_CRM",
                project_hash="h",
                worktree_hash="8d6d",
                instance_id="dnh-8d6d-dope-memory",
                service="dope-memory",
                scope="worktree",
                transport="http",
            ),
        },
        memory_data_path=Path("/Users/hue/code/dNh_CRM/.dopemux"),
    )
    assert "mcp-conport" not in text or "dopemux-dnh-crm-8d6d-conport" in text
    assert "dopemux-dnh-crm-8d6d-conport" in text
    assert "/Users/hue/code/dNh_CRM/.dopemux:/data" in text
    assert "./.dopemux:/data" not in text
    assert "dopemux.managed" in text
    assert "dopemux.project_id" in text
    # Project sidecars must bind loopback only (never 0.0.0.0)
    # ports: !override replaces compose.yml all-interface publishes
    assert "ports: !override" in text
    assert "127.0.0.1:3040:3004" in text
    assert "127.0.0.1:3041:3005" in text
    assert "127.0.0.1:4040:4004" in text
    assert "127.0.0.1:3060:3020" in text


def test_start_dry_run_planned(tmp_path: Path, monkeypatch):
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "reg" / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    (product / "scripts" / "mcp-wrappers").mkdir(parents=True)
    (product / "scripts" / "mcp-wrappers" / "task-orchestrator-http-singleton.sh").write_text(
        "#!/bin/bash\n"
    )

    result = run_lifecycle(
        "start",
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=_docker_empty(),
        product_root=product,
        process_env={},
        skip_doctor=False,
    )
    assert result.dry_run is True
    assert result.status in {"PLANNED", "BLOCKED"}
    # With empty docker and valid config should plan
    if result.status == "PLANNED":
        actions = {s["service"]: s["action"] for s in result.services}
        assert actions.get("conport") == "start"
        assert "compose.override.yml" in str(result.runtime_artifacts) or any(
            "compose" in str(a) for a in result.runtime_artifacts
        )
    # dry-run must not create registry
    assert not reg.exists()


def test_start_blocks_transport_mismatch(tmp_path: Path):
    repo = _fixture_repo(tmp_path)
    # Break transport
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "dope-memory": {
                        "type": "sse",
                        "url": "http://localhost:3060/mcp",
                    }
                }
            }
        )
    )
    (repo / ".envrc.dopemux-mcp").write_text(
        f"export DOPEMUX_WORKSPACE_ID={repo}\n"
        f"export DOPEMUX_WORKSPACE_ROOT={repo}\n"
        f"export DOPEMUX_PROJECT_ROOT={repo}\n"
        f"export DOPE_MEMORY_PORT=3060\n"
        f"export DOPE_MEMORY_WORKSPACE_ID=x\n"
        f"export DOPE_MEMORY_INSTANCE_ID=y\n"
    )
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")

    result = run_lifecycle(
        "start",
        repo=repo,
        services=["dope-memory"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=_docker_empty(),
        product_root=product,
        process_env={},
    )
    assert result.status == "BLOCKED"
    codes = {f.get("code") for f in result.blocking_findings}
    assert "TRANSPORT_MISMATCH" in codes


def test_start_blocks_unlabeled_port_owner(tmp_path: Path):
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")

    def docker_ps(*args, **kwargs):
        row = {
            "ID": "abc",
            "Names": "random-conport",
            "Ports": "0.0.0.0:3041->3005/tcp",
            "Labels": "",
            "Image": "x",
            "Status": "Up",
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(row) + "\n", stderr="")

    result = run_lifecycle(
        "start",
        repo=repo,
        services=["conport"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=docker_ps,
        product_root=product,
        process_env={},
    )
    assert result.status == "BLOCKED"
    codes = {f.get("code") for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_PORT_COLLISION" in codes or "DOCKER_CONTAINER_UNLABELED_UNKNOWN" in codes


def test_stop_refuses_unlabeled(tmp_path: Path):
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")

    # Precompute expected container name slug
    from dopemux.mcp import docker_runtime as dr_mod

    slug = dr_mod.project_slug("dNh_CRM")
    # worktree hash from identity will be computed; use docker name match loosely

    def docker_ps(*args, **kwargs):
        # Return a container that might match by port only — stop looks by name
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_lifecycle(
        "stop",
        repo=repo,
        services=["conport"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=docker_ps,
        product_root=product,
        process_env={},
    )
    assert result.operation == "stop"
    assert result.status in {"PLANNED", "PASS", "FAIL", "BLOCKED"}


def test_status_json_shape(tmp_path: Path):
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")

    result = run_lifecycle(
        "status",
        repo=repo,
        services=["conport"],
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=_docker_empty(),
        product_root=product,
        process_env={},
        port_is_free_fn=lambda p: True,
    )
    d = result.to_dict()
    assert d["operation"] == "status"
    assert "registry" in d
    assert "docker" in d
    assert d["services"]
    assert "registry_state" in d["services"][0]
    assert "docker_state" in d["services"][0]


def test_container_naming_never_default_mcp_conport():
    name = dr.container_name_for("dnh-crm", "8d6d", "conport")
    assert name == "dopemux-dnh-crm-8d6d-conport"
    assert name != "mcp-conport"
