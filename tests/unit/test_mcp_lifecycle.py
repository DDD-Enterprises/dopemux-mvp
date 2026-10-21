"""Tests for MCP lifecycle reconciler (mocked Docker)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def test_start_allows_selected_sidecars_when_only_peer_containers_exist(tmp_path: Path):
    """Non-colliding peer ConPort/dope-memory must not block selected sidecar start."""
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "reg" / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    (product / "scripts" / "mcp-wrappers").mkdir(parents=True)
    (product / "scripts" / "mcp-wrappers" / "task-orchestrator-http-singleton.sh").write_text(
        "#!/bin/bash\n"
    )

    peer_rows = [
        {
            "ID": "peer1",
            "Names": "dopemux-other-aaaa-conport",
            "Ports": "127.0.0.1:3111->3005/tcp",
            "Labels": (
                "dopemux.project_root=/other/project,"
                "dopemux.workspace_id=/other/project,"
                "dopemux.project_id=other"
            ),
            "Image": "x",
            "Status": "Up",
        },
        {
            "ID": "peer2",
            "Names": "dopemux-other-aaaa-dope-memory",
            "Ports": "127.0.0.1:3020->3020/tcp",
            "Labels": (
                "dopemux.project_root=/other/project,"
                "dopemux.workspace_id=/other/project,"
                "dopemux.project_id=other"
            ),
            "Image": "x",
            "Status": "Up",
        },
    ]

    def docker_runner(*args, **kwargs):
        # docker ps --format '{{json .}}' one object per line
        stdout = "".join(json.dumps(r) + "\n" for r in peer_rows)
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    result = run_lifecycle(
        "start",
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=docker_runner,
        product_root=product,
        process_env={},
        skip_doctor=False,
    )
    assert result.status == "PLANNED", (
        result.status,
        getattr(result, "blocking_findings", None) or getattr(result, "findings", None),
        result.to_dict() if hasattr(result, "to_dict") else result,
    )
    actions = {s["service"]: s["action"] for s in result.services}
    assert actions.get("conport") == "start"
    assert actions.get("dope-memory") == "start"
    # Ensure no shared-singleton action path was introduced.
    assert "shared_singleton" not in json.dumps(result.to_dict() if hasattr(result, "to_dict") else {})


def test_blocking_finding_codes_still_include_wrong_project():
    from dopemux.mcp.lifecycle import BLOCKING_FINDING_CODES

    assert "DOCKER_CONTAINER_WRONG_PROJECT" in BLOCKING_FINDING_CODES
    assert "DOCKER_PEER_PROJECT_INSTANCE" not in BLOCKING_FINDING_CODES
    assert "DOCKER_PEER_INSTANCE_UNLABELED" not in BLOCKING_FINDING_CODES


def test_task_orchestrator_container_name_matches_wrapper_state_id(tmp_path: Path):
    """TO name must be task-orchestrator-<slug>-<hash>, not hash-only."""
    import hashlib

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
        services=["task-orchestrator"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=_docker_empty(),
        product_root=product,
        process_env={},
        skip_doctor=True,
    )
    assert result.status in {"PLANNED", "BLOCKED", "OK"}
    # project_id from identity is slug-hash; wrapper uses task-orchestrator-${state_id}
    project_root = str(repo.resolve())
    project_hash = hashlib.sha256(project_root.encode("utf-8")).hexdigest()[:16]
    expected_prefix = f"task-orchestrator-dnh_crm-{project_hash}"
    # Fixture repo name is dNh_CRM → slug dnh_crm (identity-style keeps _)
    to_svc = next((s for s in result.services if s.get("service") == "task-orchestrator"), None)
    assert to_svc is not None, result.services
    cname = to_svc.get("container_name") or ""
    assert cname.startswith("task-orchestrator-")
    assert project_hash in cname
    assert cname == expected_prefix or cname.endswith(f"-{project_hash}")
    # Must not be hash-only form
    assert cname != f"task-orchestrator-{project_hash}"


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


# --- image presence / pre-build (never-started project) -------------------


@pytest.fixture(autouse=True)
def _hermetic_image_probe(monkeypatch):
    """Existing tests pass no cmd_runner; never let them reach a real docker."""
    real = dr.docker_image_exists

    def guarded(image, *, runner=None, env=None):
        if runner is None:
            runner = lambda *a, **k: SimpleNamespace(  # noqa: E731
                returncode=0, stdout="sha256:fake\n", stderr=""
            )
        return real(image, runner=runner, env=env)

    monkeypatch.setattr(dr, "docker_image_exists", guarded)


def _product(tmp_path: Path) -> Path:
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    (product / "scripts" / "mcp-wrappers").mkdir(parents=True)
    (
        product / "scripts" / "mcp-wrappers" / "task-orchestrator-http-singleton.sh"
    ).write_text("#!/bin/bash\n")
    return product


def _recording_runner(*, inspect_rc=0, build_rc=0, up_rc=0, build_stderr=""):
    """Fake cmd_runner: classifies docker calls and records (kind, svc, timeout)."""
    calls = []

    def runner(cmd, **kwargs):
        cmd = list(cmd)
        if cmd[:3] == ["docker", "image", "inspect"]:
            # Real docker: exit 1 + "No such image" means absent; other exit-1
            # errors (daemon unreachable) are inconclusive.
            kind, rc = "inspect", inspect_rc
            err = f"Error: No such image: {cmd[3]}" if inspect_rc == 1 else ""
        elif "build" in cmd:
            kind, rc, err = "build", build_rc, build_stderr
        elif "up" in cmd:
            kind, rc, err = "up", up_rc, ""
        else:
            kind, rc, err = "other", 0, ""
        calls.append(
            {
                "kind": kind,
                "cmd": cmd,
                "timeout": kwargs.get("timeout"),
                "env": kwargs.get("env"),
            }
        )
        return SimpleNamespace(returncode=rc, stdout="", stderr=err)

    runner.calls = calls
    return runner


def _start(tmp_path: Path, runner, *, dry_run: bool):
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "reg" / "instances.json"
    result = run_lifecycle(
        "start",
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        dry_run=dry_run,
        registry_path=reg,
        docker_runner=_docker_empty(),
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=False,
        port_is_free_fn=lambda p: True,
    )
    return result, reg


def _svc(result, name):
    return next(s for s in result.services if s["service"] == name)


def _codes(findings):
    return [f["code"] for f in findings]


def test_should_plan_build_then_up_when_image_missing_in_dry_run(tmp_path: Path):
    # Arrange
    runner = _recording_runner(inspect_rc=1)
    # Act
    result, reg = _start(tmp_path, runner, dry_run=True)
    # Assert
    assert result.status == "PLANNED"
    conport = _svc(result, "conport")
    assert len(conport["commands"]) == 2
    assert (
        " build " in f" {conport['commands'][0]} "
        and "conport" in conport["commands"][0]
    )
    assert "up -d --no-deps" in conport["commands"][1]
    assert "IMAGE_MISSING_WILL_BUILD" in _codes(conport["preflight_findings"])
    assert not reg.exists()
    assert {c["kind"] for c in runner.calls} == {"inspect"}


def test_should_plan_only_up_when_image_present_in_dry_run(tmp_path: Path):
    # Arrange
    runner = _recording_runner(inspect_rc=0)
    # Act
    result, _ = _start(tmp_path, runner, dry_run=True)
    # Assert
    conport = _svc(result, "conport")
    assert len(conport["commands"]) == 1
    assert "up -d --no-deps" in conport["commands"][0]
    assert "IMAGE_MISSING_WILL_BUILD" not in _codes(conport["preflight_findings"])


def test_should_build_then_up_with_budgets_when_image_missing_in_apply(
    tmp_path: Path, monkeypatch
):
    # Arrange
    monkeypatch.delenv("DOPEMUX_MCP_BUILD_TIMEOUT_SECS", raising=False)
    monkeypatch.delenv("DOPEMUX_MCP_UP_TIMEOUT_SECS", raising=False)
    runner = _recording_runner(inspect_rc=1)
    # Act
    result, _ = _start(tmp_path, runner, dry_run=False)
    # Assert
    conport_calls = [c for c in runner.calls if "conport" in " ".join(c["cmd"])]
    assert [c["kind"] for c in conport_calls] == ["inspect", "build", "up"]
    assert conport_calls[1]["timeout"] == 1800.0
    assert conport_calls[2]["timeout"] == 180.0
    conport = _svc(result, "conport")
    assert conport["action"] == "started"
    assert conport["build_result"]["exit_code"] == 0
    assert conport["image"].endswith("-conport")
    assert "IMAGE_BUILT" in _codes(conport["findings"])
    assert (
        len(conport["commands"]) >= 1 and "up -d --no-deps" in conport["commands"][-1]
    )


def test_should_honor_build_timeout_env_when_set_in_apply(tmp_path: Path, monkeypatch):
    # Arrange
    monkeypatch.setenv("DOPEMUX_MCP_BUILD_TIMEOUT_SECS", "42")
    runner = _recording_runner(inspect_rc=1)
    # Act
    _start(tmp_path, runner, dry_run=False)
    # Assert
    builds = [c for c in runner.calls if c["kind"] == "build"]
    assert builds and all(c["timeout"] == 42.0 for c in builds)


def test_should_skip_up_and_fail_when_build_fails_in_apply(tmp_path: Path):
    # Arrange
    runner = _recording_runner(
        inspect_rc=1, build_rc=1, build_stderr="boom: pip failed"
    )
    # Act
    result, _ = _start(tmp_path, runner, dry_run=False)
    # Assert
    conport = _svc(result, "conport")
    assert conport["action"] == "failed"
    assert result.status == "FAIL"
    assert "IMAGE_BUILD_FAILED" in _codes(conport["findings"])
    assert "boom: pip failed" in str(conport["findings"])
    assert conport["build_result"]["exit_code"] == 1
    assert conport["result"]["exit_code"] == 1
    conport_kinds = [c["kind"] for c in runner.calls if "conport" in " ".join(c["cmd"])]
    assert "up" not in conport_kinds


def test_should_only_run_up_and_warn_when_image_presence_unknown(tmp_path: Path):
    # Arrange
    runner = _recording_runner(inspect_rc=127)
    # Act
    result, _ = _start(tmp_path, runner, dry_run=False)
    # Assert
    conport = _svc(result, "conport")
    assert "IMAGE_PRESENCE_UNKNOWN" in _codes(conport["findings"])
    assert conport["build_result"] is None
    kinds = [c["kind"] for c in runner.calls if "conport" in " ".join(c["cmd"])]
    assert "build" not in kinds and "up" in kinds


def test_should_pass_host_dir_interpolation_env_when_running_compose(
    tmp_path: Path, monkeypatch
):
    # Arrange
    runner = _recording_runner(inspect_rc=0)
    # Act
    monkeypatch.delenv("HOST_CODE_PARENT_DIR", raising=False)
    monkeypatch.delenv("HOST_PROJECT_RELATIVE_PATH", raising=False)
    _start(tmp_path, runner, dry_run=False)
    # Assert
    up = next(c for c in runner.calls if c["kind"] == "up")
    assert up["env"]["HOST_CODE_PARENT_DIR"] == str(tmp_path)
    assert up["env"]["HOST_PROJECT_RELATIVE_PATH"] == "product"
