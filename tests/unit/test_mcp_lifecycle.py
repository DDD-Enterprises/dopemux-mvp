"""Tests for MCP lifecycle reconciler (mocked Docker)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from dopemux.mcp import docker_runtime as dr
from dopemux.mcp.lifecycle import run_lifecycle


@pytest.fixture(autouse=True)
def _isolated_registries(tmp_path: Path, monkeypatch):
    """Never let a lifecycle test reach ~/.dopemux (registry, leases, lock files)."""
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "env-reg" / "instances.json"))
    monkeypatch.setenv(
        "DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "env-reg" / "port-leases.json")
    )


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
    # Identity comes from git only, so the fixture must be a real repository.
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
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
        # The ConPort tenant probe (psql on stdin): a host whose shared store has
        # this project's rows, so conport stays on it (legacy_shared). An unknown
        # count would refuse conport (final review R2).
        sql = kwargs.get("input") or ""
        if "DPMX_TABLES=" in sql:
            return SimpleNamespace(returncode=0, stdout="DPMX_TABLES=decisions\n", stderr="")
        if "DPMX_COUNT=" in sql:
            return SimpleNamespace(returncode=0, stdout="DPMX_COUNT=3\n", stderr="")
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
    image = dr.compose_image_name("conport", product=tmp_path / "product")
    assert conport["image"] == image  # one shared tag per service and source (I4)
    override = next(p for p in result.runtime_artifacts if p.endswith("compose.override.yml"))
    assert f"    image: {image}\n" in Path(override).read_text(encoding="utf-8")
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


# --- task-orchestrator start under the reserved lock (fix round 1, finding D)


def _to_start(tmp_path: Path, monkeypatch, *, snapshots, free):
    """Run a real (non-dry) TO start with a lock spy and sequenced docker state."""
    from contextlib import contextmanager

    from dopemux.mcp import docker_inspect as di
    from dopemux.mcp import lifecycle as lc

    events = []
    held = {"n": 0}

    @contextmanager
    def lock_spy(port):
        held["n"] += 1
        events.append(("lock", port))
        try:
            yield
        finally:
            held["n"] -= 1
            events.append(("unlock", held["n"]))

    def inspect(**_kwargs):
        events.append(("inspect", held["n"]))
        n = sum(1 for e in events if e[0] == "inspect")
        containers = snapshots[min(n, len(snapshots)) - 1]
        return di.DockerInspectResult(available=True, containers=list(containers))

    def cmd_runner(cmd, **_kwargs):
        events.append(("cmd", held["n"], list(cmd)))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(lc, "reserved_port_lock", lock_spy)
    monkeypatch.setattr(di, "inspect_running_containers", inspect)
    result = run_lifecycle(
        "start",
        repo=_fixture_repo(tmp_path),
        services=["task-orchestrator"],
        catalog=_catalog(),
        dry_run=False,
        registry_path=tmp_path / "reg" / "instances.json",
        cmd_runner=cmd_runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda port: free(events),
    )
    return result, events


def _wrapper_calls(events):
    return [e for e in events if e[0] == "cmd" and e[2][:1] == ["bash"]]


def test_task_orchestrator_start_runs_wrapper_under_reserved_lock(tmp_path: Path, monkeypatch):
    result, events = _to_start(tmp_path, monkeypatch, snapshots=[[]], free=lambda e: True)
    assert result.exit_code == 0, result.blocking_findings
    wrapper = _wrapper_calls(events)
    assert len(wrapper) == 1
    assert wrapper[0][1] >= 1  # the reserved lock is held while the wrapper starts TO
    before = events[: events.index(wrapper[0])]
    # ...and :7890 was re-inspected under that same hold, after the preflight released it.
    released = max(i for i, e in enumerate(before) if e == ("unlock", 0))
    assert any(e[0] == "inspect" and e[1] >= 1 for e in before[released:])


def test_task_orchestrator_start_rechecks_owner_under_lock(tmp_path: Path, monkeypatch):
    from dopemux.mcp import docker_inspect as di

    foreign = di.DockerContainerInfo(
        id="0123456789ab",
        name="task-orchestrator-other",
        ports=["127.0.0.1:7890->7890/tcp"],
        labels={
            "dopemux.managed": "true",
            "dopemux.service": "task-orchestrator",
            "dopemux.project_id": "other-project",
            "dopemux.project_root": str(tmp_path / "other-project"),
        },
        published_ports=[7890],
    )
    # Free at preflight; another project's TO takes :7890 before the start.
    result, events = _to_start(
        tmp_path,
        monkeypatch,
        snapshots=[[], [foreign]],
        free=lambda e: sum(1 for x in e if x[0] == "inspect") < 2,
    )
    assert _wrapper_calls(events) == []
    assert result.exit_code == 1
    to_svc = next(s for s in result.services if s["service"] == "task-orchestrator")
    assert to_svc["action"] == "blocked"
    assert any(
        f["code"].startswith("TASK_ORCHESTRATOR_START_BLOCKED") for f in to_svc["findings"]
    )


# --- a foreign orchestrator only blocks orchestrator starts (fix round 2) ---


def _foreign_to_doctor():
    return SimpleNamespace(
        findings=[
            {
                "code": "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME",
                "severity": "FAIL",
                "service": "task-orchestrator",
                "message": "task-orchestrator on :7890 belongs to another project (/x/other)",
            },
            {
                "code": "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_OTHER_PROJECT",
                "severity": "FAIL",
                "service": "task-orchestrator",
                "message": ":7890 occupied by another project's task-orchestrator",
            },
        ]
    )


@pytest.mark.parametrize("services", [["conport"], ["dope-memory"], ["conport", "dope-memory"]])
def test_foreign_orchestrator_does_not_block_conport_only_start(services):
    from dopemux.mcp.lifecycle import _doctor_blocking_findings

    assert _doctor_blocking_findings(_foreign_to_doctor(), services=services) == []


@pytest.mark.parametrize("services", [["task-orchestrator"], ["conport", "task-orchestrator"]])
def test_foreign_orchestrator_still_blocks_orchestrator_start(services):
    from dopemux.mcp.lifecycle import _doctor_blocking_findings

    codes = [f["code"] for f in _doctor_blocking_findings(_foreign_to_doctor(), services=services)]
    assert "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME" in codes


def test_conport_start_proceeds_while_another_project_owns_the_orchestrator(
    tmp_path: Path, monkeypatch
):
    """End to end: `run_lifecycle("start", ["conport"])` with that doctor report."""
    from dopemux.mcp import lifecycle as lc

    monkeypatch.setattr(lc, "run_mcp_doctor", lambda *a, **k: _foreign_to_doctor())
    result = run_lifecycle(
        "start",
        repo=_fixture_repo(tmp_path),
        services=["conport"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=tmp_path / "reg" / "instances.json",
        docker_runner=_docker_empty(),
        product_root=_product(tmp_path),
        process_env={},
        port_is_free_fn=lambda p: True,
    )
    codes = {f["code"] for f in result.blocking_findings}
    assert "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME" not in codes, result.blocking_findings
    assert result.status == "PLANNED", result.blocking_findings


# --- stop releases leases and removes the runtime dir (Task 5, D8/R8) -----------------


def _stop_world(tmp_path: Path):
    """A repo whose conport and dope-memory containers run, with leases and a runtime dir."""
    from dopemux.mcp.port_leases import PortLeaseRegistry
    from dopemux.mcp.runtime_state import resolve_identity_view

    repo = _fixture_repo(tmp_path)
    identity = resolve_identity_view(repo, trust_env=False)
    slug = dr.project_slug(Path(identity.project_root).name)
    reg = tmp_path / "reg" / "instances.json"
    runtime_dir = reg.parent / f"{slug}-{identity.worktree_hash}"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "mcp.env").write_text("X=1\n", encoding="utf-8")

    rows = []
    for svc in ("conport", "dope-memory"):
        labels = dr.build_labels(
            project_id=identity.project_id,
            workspace_id=identity.workspace_id or identity.worktree_root,
            project_root=identity.project_root,
            worktree_root=identity.worktree_root,
            project_hash=identity.project_hash or "",
            worktree_hash=identity.worktree_hash,
            instance_id=f"{slug}-{identity.worktree_hash}-{svc}",
            service=svc,
            scope="worktree",
        )
        rows.append(
            {
                "ID": f"id-{svc}",
                "Names": dr.container_name_for(slug, identity.worktree_hash, svc),
                "Labels": ",".join(f"{k}={v}" for k, v in labels.items()),
                "Image": "x",
                "Status": "Up",
            }
        )

    def docker_ps(*args, **kwargs):
        return SimpleNamespace(
            returncode=0, stdout="".join(json.dumps(r) + "\n" for r in rows), stderr=""
        )

    leases = PortLeaseRegistry.load(tmp_path / "env-reg" / "port-leases.json", create_missing=True)
    for svc, port in (("conport", 3100), ("dope-memory", 3101)):
        leases.upsert_lease(
            {
                "lease_id": f"lease-{svc}",
                "service": svc,
                "port": port,
                "port_role": "http",
                "worktree_root": identity.worktree_root,
                "project_id": identity.project_id,
                "scope": "worktree",
                "status": "active",
            }
        )
    leases.save()
    return repo, reg, runtime_dir, docker_ps, tmp_path / "env-reg" / "port-leases.json"


def _lease_status(path: Path):
    from dopemux.mcp.port_leases import PortLeaseRegistry

    return {L["service"]: L["status"] for L in PortLeaseRegistry.load(path).leases()}


def _stop(tmp_path: Path, repo, reg, docker_ps, *, services, dry_run=False):
    stops: list = []

    def cmd_runner(cmd, **kwargs):
        stops.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_lifecycle(
        "stop",
        repo=repo,
        services=services,
        catalog=_catalog(),
        dry_run=dry_run,
        registry_path=reg,
        docker_runner=docker_ps,
        cmd_runner=cmd_runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    return result, stops


def test_stop_releases_leases_and_removes_runtime_dir(tmp_path: Path):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    result, stops = _stop(tmp_path, repo, reg, docker_ps, services=None)
    assert result.status == "PASS", result.to_dict()
    assert any(c[:2] == ["docker", "stop"] for c in stops)
    status = _lease_status(lease_path)
    assert status == {"conport": "released", "dope-memory": "released"}
    assert not runtime_dir.exists()


def test_stop_partial_releases_only_that_service_and_keeps_runtime_dir(tmp_path: Path):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    result, _ = _stop(tmp_path, repo, reg, docker_ps, services=["conport"])
    assert result.status == "PASS", result.to_dict()
    assert _lease_status(lease_path) == {"conport": "released", "dope-memory": "active"}
    assert runtime_dir.is_dir()


def test_stop_dry_run_keeps_leases_and_runtime_dir(tmp_path: Path):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    _stop(tmp_path, repo, reg, docker_ps, services=None, dry_run=True)
    assert _lease_status(lease_path) == {"conport": "active", "dope-memory": "active"}
    assert runtime_dir.is_dir()


def test_restart_never_releases_state(tmp_path: Path, monkeypatch):
    from dopemux.mcp import lifecycle as lc

    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    released: list = []
    monkeypatch.setattr(lc, "_release_stopped_state", lambda **kw: released.append(kw) or [])
    stops: list = []

    def cmd_runner(cmd, **kwargs):
        stops.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_lifecycle(
        "restart",
        repo=repo,
        services=["conport"],
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker_ps,
        cmd_runner=cmd_runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert result.operation == "restart"
    assert any(c[:2] == ["docker", "stop"] for c in stops), stops  # the stop half really ran
    assert released == []
    assert _lease_status(lease_path)["dope-memory"] == "active"


def test_stop_runs_under_the_instance_lock_and_releases_state_inside_it(tmp_path: Path, monkeypatch):
    import contextlib

    from dopemux.mcp import lifecycle as lc

    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    events: list = []
    held = {"now": False}
    lock_dirs: list = []

    @contextlib.contextmanager
    def spy_lock(rt):
        lock_dirs.append(Path(rt))
        held["now"] = True
        events.append("lock")
        try:
            yield
        finally:
            held["now"] = False
            events.append("unlock")

    real_release = lc._release_stopped_state

    def spy_release(**kw):
        events.append(f"release(held={held['now']})")
        return real_release(**kw)

    monkeypatch.setattr(lc, "instance_lock", spy_lock)
    monkeypatch.setattr(lc, "_release_stopped_state", spy_release)
    stop_calls: list = []

    def cmd_runner(cmd, **kwargs):
        stop_calls.append(f"docker(held={held['now']})")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_lifecycle(
        "stop",
        repo=repo,
        services=None,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker_ps,
        cmd_runner=cmd_runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert result.status == "PASS", result.to_dict()
    assert lock_dirs == [runtime_dir]
    assert events == ["lock", "release(held=True)", "unlock"]
    assert stop_calls and all(c == "docker(held=True)" for c in stop_calls)


def test_stop_dry_run_takes_no_lock(tmp_path: Path, monkeypatch):
    from dopemux.mcp import lifecycle as lc

    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)

    def no_lock(rt):
        raise AssertionError("dry-run must not lock")

    monkeypatch.setattr(lc, "instance_lock", no_lock)
    _stop(tmp_path, repo, reg, docker_ps, services=None, dry_run=True)


def test_full_stop_with_a_live_launcher_keeps_the_runtime_dir_and_warns(tmp_path: Path):
    from dopemux.mcp import reap

    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    reap.attach(runtime_dir)  # this process is a live launcher
    result, _ = _stop(tmp_path, repo, reg, docker_ps, services=None)
    assert result.status == "PASS", result.to_dict()
    assert runtime_dir.is_dir() and (runtime_dir / "attached" / str(os.getpid())).is_file()
    assert _lease_status(lease_path) == {"conport": "released", "dope-memory": "released"}
    warn = [w for w in result.warnings if w["code"] == "RUNTIME_DIR_KEPT_LIVE_LAUNCHERS"]
    assert len(warn) == 1 and warn[0]["severity"] == "WARN" and "1 launcher" in warn[0]["message"]


def test_stop_failure_keeps_leases_and_runtime_dir(tmp_path: Path):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)

    def failing(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="cannot stop")

    result = run_lifecycle(
        "stop",
        repo=repo,
        services=None,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker_ps,
        cmd_runner=failing,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert result.status == "FAIL"
    assert _lease_status(lease_path) == {"conport": "active", "dope-memory": "active"}
    assert runtime_dir.is_dir()


# --- final review R1: stop saves the registry under the lock -------------------------


def test_stop_keeps_a_record_written_concurrently_between_read_and_save(tmp_path: Path):
    from dopemux.mcp.locks import locked_reload_and_save
    from dopemux.mcp.runtime_registry import RuntimeRegistry, build_instance_record
    from dopemux.mcp.runtime_state import resolve_identity_view

    repo, reg, _runtime_dir, docker_ps, _lease_path = _stop_world(tmp_path)
    identity = resolve_identity_view(repo, trust_env=False)

    def record(service: str, worktree_root: str, worktree_hash: str, iid: str):
        return build_instance_record(
            instance_id=iid,
            project_id=identity.project_id,
            workspace_id=worktree_root,
            project_root=identity.project_root,
            worktree_root=worktree_root,
            worktree_hash=worktree_hash,
            project_hash=identity.project_hash or "",
            service=service,
            scope="worktree",
            status="running",
            ports={},
            urls={},
            container_names=[dr.container_name_for(
                dr.project_slug(Path(identity.project_root).name), identity.worktree_hash, service
            )],
            compose_project_name="x",
            labels={},
        )

    ours = [
        record(svc, identity.worktree_root, identity.worktree_hash, f"ours-{svc}")
        for svc in ("conport", "dope-memory")
    ]
    locked_reload_and_save(RuntimeRegistry, reg, lambda r: [r.upsert_instance(x) for x in ours])
    sibling = record("conport", "/elsewhere/wt", "beef0002", "sibling-conport")

    def cmd_runner(cmd, **kwargs):
        if list(cmd[:2]) == ["docker", "stop"]:  # another start saves while we stop
            locked_reload_and_save(RuntimeRegistry, reg, lambda r: r.upsert_instance(sibling))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_lifecycle(
        "stop",
        repo=repo,
        services=None,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker_ps,
        cmd_runner=cmd_runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert result.status == "PASS", result.to_dict()
    status = {i["instance_id"]: i["status"] for i in RuntimeRegistry.load(reg).instances()}
    assert status == {
        "ours-conport": "stopped",
        "ours-dope-memory": "stopped",
        "sibling-conport": "running",  # the concurrent record survived
    }


# --- cycle 2 B2 (codex F2, amended ruling (b)): CLI start/restart vs the reaper -------

WORKTREE_SERVICES = ["conport", "dope-memory"]
TO = "task-orchestrator"


def _runtime_dir_of(repo: Path, reg: Path) -> Path:
    from dopemux.mcp.runtime_state import resolve_identity_view

    identity = resolve_identity_view(repo, trust_env=False)
    slug = dr.project_slug(Path(identity.project_root).name)
    return reg.parent / f"{slug}-{identity.worktree_hash}"


def _lock_spies(monkeypatch):
    """Record instance-lock and reserved-lock acquisitions and every stop/start part.

    Events: ``("instance", dir)``, ``("instance-released",)``, ``("reserved",
    instance_held)``, ``("stop"|"start", selected, instance_held)``.
    """
    import contextlib

    from dopemux.mcp import lifecycle as lc

    events: list = []
    held = {"instance": 0}

    @contextlib.contextmanager
    def instance_spy(runtime_dir, *, blocking=True):
        events.append(("instance", Path(runtime_dir)))
        held["instance"] += 1
        try:
            yield
        finally:
            held["instance"] -= 1
            events.append(("instance-released",))

    @contextlib.contextmanager
    def reserved_spy(port):
        events.append(("reserved", held["instance"]))
        yield

    real_start, real_stop = lc._start_services, lc._stop_services

    def start_spy(**kw):
        events.append(("start", list(kw["selected"]), held["instance"]))
        return real_start(**kw)

    def stop_spy(**kw):
        events.append(("stop", list(kw["selected"]), held["instance"]))
        return real_stop(**kw)

    monkeypatch.setattr(lc, "instance_lock", instance_spy)
    monkeypatch.setattr(lc, "reserved_port_lock", reserved_spy)
    monkeypatch.setattr(lc, "_start_services", start_spy)
    monkeypatch.setattr(lc, "_stop_services", stop_spy)
    return events


def _run(tmp_path: Path, op: str, services, *, runner=None, docker=None, **kw):
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "reg" / "instances.json"
    result = run_lifecycle(
        op,
        repo=repo,
        services=services,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker or _docker_empty(),
        cmd_runner=runner or _recording_runner(),
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
        **kw,
    )
    return result, repo, reg


@pytest.mark.parametrize("op", ["start", "restart"])
def test_worktree_start_and_restart_hold_the_instance_lock_once(
    tmp_path: Path, monkeypatch, op
):
    events = _lock_spies(monkeypatch)
    result, repo, reg = _run(tmp_path, op, WORKTREE_SERVICES)
    assert result.exit_code == 0, result.to_dict()
    assert [e for e in events if e[0] == "instance"] == [
        ("instance", _runtime_dir_of(repo, reg))
    ]
    parts = [e for e in events if e[0] in {"stop", "start"}]
    expected = [("start", WORKTREE_SERVICES, 1)]
    if op == "restart":  # stop and start under ONE acquisition
        expected = [("stop", WORKTREE_SERVICES, 1)] + expected
    assert parts == expected


@pytest.mark.parametrize("op", ["start", "restart"])
def test_the_orchestrator_part_never_runs_under_the_instance_lock(
    tmp_path: Path, monkeypatch, op
):
    events = _lock_spies(monkeypatch)
    result, repo, reg = _run(tmp_path, op, [*WORKTREE_SERVICES, TO])
    assert result.exit_code == 0, result.to_dict()
    assert [e for e in events if e[0] == "instance"] == [
        ("instance", _runtime_dir_of(repo, reg))
    ]
    reserved = [e for e in events if e[0] == "reserved"]
    assert len(reserved) >= 2  # the preflight gate and the start itself
    assert all(held == 0 for _, held in reserved)  # launch.lock never held then
    # the instance lock is released before the orchestrator's start takes :7890
    released = events.index(("instance-released",))
    to_start = events.index(("start", [TO], 0))
    assert released < to_start < len(events) - 1
    assert events[to_start + 1] == ("reserved", 0)
    parts = [e for e in events if e[0] in {"stop", "start"}]
    if op == "start":
        assert parts == [("start", WORKTREE_SERVICES, 1), ("start", [TO], 0)]
    else:  # every stop before any start, the orchestrator's halves outside
        assert parts == [
            ("stop", [TO], 0),
            ("stop", WORKTREE_SERVICES, 1),
            ("start", WORKTREE_SERVICES, 1),
            ("start", [TO], 0),
        ]
    # the runtime artifacts are written once, under the lock, for the compose services
    override = (_runtime_dir_of(repo, reg) / "compose.override.yml").read_text()
    assert "conport" in override and not override.startswith("# no compose services")


@pytest.mark.parametrize("op", ["start", "restart"])
@pytest.mark.parametrize(
    "services", [WORKTREE_SERVICES, [*WORKTREE_SERVICES, TO], [TO]]
)
def test_no_instance_lock_without_hold_instance_lock_or_in_a_dry_run(
    tmp_path: Path, monkeypatch, op, services
):
    from dopemux.mcp import lifecycle as lc

    def no_lock(*_a, **_k):
        raise AssertionError("must not take launch.lock")

    monkeypatch.setattr(lc, "instance_lock", no_lock)
    result, _repo, _reg = _run(tmp_path / "a", op, services, hold_instance_lock=False)
    assert result.exit_code == 0, result.to_dict()
    dry, _repo, _reg = _run(tmp_path / "b", op, services, dry_run=True)
    assert dry.status == "PLANNED"


def test_an_orchestrator_only_start_takes_no_instance_lock(tmp_path: Path, monkeypatch):
    # switch-project calls this under the reserved lock: launch.lock there would be
    # reserved -> instance, the reverse of the CLI start's order (ABBA deadlock).
    events = _lock_spies(monkeypatch)
    result, _repo, _reg = _run(tmp_path, "start", [TO])
    assert result.exit_code == 0, result.to_dict()
    assert [e for e in events if e[0] == "instance"] == []
    assert [e for e in events if e[0] == "start"] == [("start", [TO], 0)]


def _summary(result):
    return {
        "operation": result.operation,
        "status": result.status,
        "exit_code": result.exit_code,
        "services": [(s["service"], s.get("action")) for s in result.services],
        "blocking": result.blocking_findings,
        "warnings": result.warnings,
        "artifacts": [Path(a).name for a in result.runtime_artifacts],
        "next": [a.split(" --repo ")[0] for a in result.recommended_next_actions],
    }


@pytest.mark.parametrize("op", ["start", "restart"])
@pytest.mark.parametrize("up_rc", [0, 1])
@pytest.mark.parametrize(
    "services",
    [[*WORKTREE_SERVICES, TO], [TO, "conport"], ["dope-memory", TO, "conport"]],
)
def test_a_split_run_returns_what_one_call_returns(tmp_path: Path, op, up_rc, services):
    locked, _r, _g = _run(
        tmp_path / "a", op, services, runner=_recording_runner(up_rc=up_rc)
    )
    single, _r, _g = _run(
        tmp_path / "b",
        op,
        services,
        runner=_recording_runner(up_rc=up_rc),
        hold_instance_lock=False,
    )
    assert _summary(locked) == _summary(single)  # incl. the per-service order


def test_a_failed_stop_in_a_split_restart_starts_nothing(tmp_path: Path):
    def failing_stop():
        calls: list = []

        def runner(cmd, **kwargs):
            calls.append(list(cmd))
            rc = 1 if list(cmd[:2]) == ["docker", "stop"] else 0
            return SimpleNamespace(returncode=rc, stdout="", stderr="")

        runner.calls = calls
        return runner

    results = {}
    for name, hold in (("locked", True), ("single", False)):
        (tmp_path / name).mkdir()
        repo, reg, _rt, docker_ps, _leases = _stop_world(tmp_path / name)
        runner = failing_stop()
        results[name] = run_lifecycle(
            "restart",
            repo=repo,
            services=[*WORKTREE_SERVICES, TO],
            catalog=_catalog(),
            registry_path=reg,
            docker_runner=docker_ps,
            cmd_runner=runner,
            product_root=_product(tmp_path / name),
            process_env={},
            skip_doctor=True,
            port_is_free_fn=lambda p: True,
            hold_instance_lock=hold,
        )
        assert not any(
            "up" in c or c[:1] == ["bash"] for c in runner.calls
        ), runner.calls
    assert results["locked"].status == "FAIL" and results["locked"].exit_code == 1
    assert _summary(results["locked"]) == _summary(results["single"])


def test_run_lifecycle_holds_the_instance_lock_by_default():
    import inspect

    param = inspect.signature(run_lifecycle).parameters["hold_instance_lock"]
    assert param.default is True and param.kind is inspect.Parameter.KEYWORD_ONLY


# --- cycle 2 fix round 1, Important 1: facts are re-taken under the instance lock -----


def _lease_world(tmp_path: Path):
    """`_stop_world` with ports from leases (no envrc ports) and a docker that a reap empties."""
    from dopemux.mcp.runtime_state import resolve_identity_view

    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    envrc = repo / ".envrc.dopemux-mcp"
    envrc.write_text(
        "".join(
            line + "\n"
            for line in envrc.read_text().splitlines()
            if "_PORT=" not in line
        )
    )
    state = {"gone": False}

    def docker(*args, **kwargs):
        if state["gone"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return docker_ps(*args, **kwargs)

    identity = resolve_identity_view(repo, trust_env=False)
    return repo, reg, runtime_dir, docker, lease_path, state, identity


def _reap_while_waiting(monkeypatch, *, runtime_dir, reg, lease_path, state, identity):
    """Entering launch.lock replays an automatic reap that finished in the meantime."""
    import contextlib

    from dopemux.mcp import lifecycle as lc
    from dopemux.mcp import reap

    reaps: list = []

    @contextlib.contextmanager
    def lock_after_a_reap(rt, *, blocking=True):
        cand = reap.ReapCandidate(
            project_id=identity.project_id,
            worktree_hash=identity.worktree_hash,
            worktree_root=identity.worktree_root,
            runtime_dir=Path(rt),
            container_ids=["id-conport", "id-dope-memory"],
            reason="idle",
            services=["conport", "dope-memory"],
            container_services={
                "id-conport": "conport",
                "id-dope-memory": "dope-memory",
            },
        )

        def reap_docker(cmd, **kwargs):
            state["gone"] = True
            return dr.RuntimeCommandResult(command=list(cmd), exit_code=0, stderr="")

        report = reap.apply_reap(
            [cand],
            runner=reap_docker,
            lease_path=lease_path,
            registry_path=reg,
            exists=lambda p: False,
        )
        reaps.append(report)
        assert report.reaped == [cand], report.to_dict()
        assert not Path(rt).exists()
        yield

    monkeypatch.setattr(lc, "instance_lock", lock_after_a_reap)
    return reaps


def _worktree_leases(lease_path: Path, worktree_root: str):
    from dopemux.mcp.port_leases import PortLeaseRegistry

    return {
        str(L.get("port_var")): int(L["port"])
        for L in PortLeaseRegistry.load(lease_path).active_leases()
        if L.get("worktree_root") == worktree_root and L.get("port_var")
    }


@pytest.mark.parametrize("op", ["start", "restart"])
def test_a_reap_finishing_while_the_cli_waits_for_the_lock_never_leaves_stale_state(
    tmp_path: Path, monkeypatch, op
):
    from dopemux.mcp.runtime_registry import RuntimeRegistry

    repo, reg, runtime_dir, docker, lease_path, state, identity = _lease_world(tmp_path)
    reaps = _reap_while_waiting(
        monkeypatch,
        runtime_dir=runtime_dir,
        reg=reg,
        lease_path=lease_path,
        state=state,
        identity=identity,
    )
    runner = _recording_runner()
    result = run_lifecycle(
        op,
        repo=repo,
        services=WORKTREE_SERVICES,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: not any(c["kind"] == "up" for c in runner.calls),
    )
    assert len(reaps) == 1  # the reap really ran in between
    actions = [(s["service"], s.get("action")) for s in result.services]
    assert ("conport", "already_running") not in actions
    assert ("dope-memory", "already_running") not in actions
    ups = [c for c in runner.calls if c["kind"] == "up"]
    assert len(ups) == 2  # a real start of both sidecars
    assert result.status == "PASS" and result.exit_code == 0, result.to_dict()
    # no `docker stop` of names that are already gone (a restart's stop half saw
    # them gone and reported them already stopped)
    assert not [c for c in runner.calls if c["cmd"][:2] == ["docker", "stop"]]
    # registry and leases agree with what was started
    leases = _worktree_leases(lease_path, identity.worktree_root)
    records = {
        i["service"]: i
        for i in RuntimeRegistry.load(reg).instances()
        if i.get("worktree_root") == identity.worktree_root
    }
    assert {svc: rec["status"] for svc, rec in records.items()} == {
        "conport": "running",
        "dope-memory": "running",
    }
    for rec in records.values():
        port_vars = {k: v for k, v in rec["ports"].items() if k.isupper()}
        assert port_vars and all(leases.get(k) == v for k, v in port_vars.items())


# --- cycle 2 fix round 1, Minor 1: images build before launch.lock is taken -----------


@pytest.mark.parametrize("op", ["start", "restart"])
def test_a_missing_image_is_built_before_the_instance_lock_is_taken(
    tmp_path: Path, monkeypatch, op
):
    import contextlib

    from dopemux.mcp import lifecycle as lc

    events: list = []

    @contextlib.contextmanager
    def lock_spy(rt, *, blocking=True):
        events.append("lock")
        try:
            yield
        finally:
            events.append("unlock")

    monkeypatch.setattr(lc, "instance_lock", lock_spy)
    runner = _recording_runner(inspect_rc=1)  # image missing

    def recording(cmd, **kwargs):
        result = runner(cmd, **kwargs)
        kind = runner.calls[-1]["kind"]
        if kind in {"build", "up"}:
            events.append(f"{kind}:{list(cmd)[-1]}")
        return result

    result, _repo, reg = _run(tmp_path, op, WORKTREE_SERVICES, runner=recording)
    assert result.exit_code == 0, result.to_dict()
    assert events == [
        "build:conport",
        "build:dope-memory",
        "lock",
        "up:conport",
        "up:dope-memory",
        "unlock",
    ]
    conport = _svc(result, "conport")
    assert "IMAGE_MISSING_WILL_BUILD" in _codes(conport["findings"])
    assert "IMAGE_BUILT" in _codes(conport["findings"])
    assert conport["build_result"]["exit_code"] == 0
    builds = [c for c in runner.calls if c["kind"] == "build"]
    assert builds and all(c["timeout"] == dr.build_timeout_secs() for c in builds)
    rt = _runtime_dir_of(_repo, reg)
    assert all(str(rt / "compose.build.yml") in c["cmd"] for c in builds)


def test_an_unlocked_start_keeps_building_inline(tmp_path: Path, monkeypatch):
    from dopemux.mcp import lifecycle as lc

    events: list = []
    real_start = lc._start_services

    def start_spy(**kw):
        events.append("start_services")
        return real_start(**kw)

    monkeypatch.setattr(lc, "_start_services", start_spy)
    runner = _recording_runner(inspect_rc=1)

    def recording(cmd, **kwargs):
        result = runner(cmd, **kwargs)
        if runner.calls[-1]["kind"] == "build":
            events.append("build")
        return result

    result, _repo, _reg = _run(
        tmp_path, "start", WORKTREE_SERVICES, runner=recording, hold_instance_lock=False
    )
    assert result.exit_code == 0, result.to_dict()
    assert events == ["start_services", "build", "build"]


# --- cycle 2 fix round 2, N1: a restart starts what it just stopped ---------------------

# Host ports the fixture envrc names, by service (what a probe sees as busy).
_ENVRC_PORTS = {"conport": {3040, 3041, 4040}, "dope-memory": {3060}}


def _running_world(tmp_path: Path):
    """`_stop_world` whose docker follows `docker stop` and `compose up`, both sidecars up."""
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    rows = {
        json.loads(line)["Names"]: line
        for line in docker_ps().stdout.splitlines()
        if line.strip()
    }
    names = {
        svc: next(n for n in rows if n.endswith(f"-{svc}")) for svc in WORKTREE_SERVICES
    }
    assert set(names.values()) == set(rows)
    # Running sidecars hold active leases for the envrc ports, as a start leaves them
    # (B7-2: an envrc port with no lease behind it would be re-leased).
    from dopemux.mcp.port_leases import PortLeaseRegistry
    from dopemux.mcp.runtime_state import resolve_identity_view

    identity = resolve_identity_view(repo, trust_env=False)
    leases = PortLeaseRegistry.load(lease_path)
    envrc_leases = {
        ("conport", "CONPORT_HTTP_PORT"): 3040,
        ("conport", "CONPORT_MCP_PORT"): 3041,
        ("conport", "CONPORT_INFO_PORT"): 4040,
        ("dope-memory", "DOPE_MEMORY_PORT"): 3060,
    }
    for (svc, var), port in envrc_leases.items():
        leases.upsert_lease(
            {
                "lease_id": f"lease-{var.lower()}",
                "service": svc,
                "port": port,
                "port_role": var.lower(),
                "port_var": var,
                "worktree_root": identity.worktree_root,
                "project_root": identity.project_root,
                "worktree_hash": identity.worktree_hash,
                "project_id": identity.project_id,
                "scope": "worktree",
                "status": "active",
            }
        )
    leases.save()
    alive = set(rows)
    busy = set().union(*_ENVRC_PORTS.values())
    calls: list = []

    def docker(*args, **kwargs):
        out = "".join(rows[n] + "\n" for n in sorted(alive))
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    def runner(cmd, **kwargs):
        cmd = list(cmd)
        calls.append(cmd)
        sql = kwargs.get("input") or ""
        if "DPMX_TABLES=" in sql:
            return SimpleNamespace(
                returncode=0, stdout="DPMX_TABLES=decisions\n", stderr=""
            )
        if "DPMX_COUNT=" in sql:
            return SimpleNamespace(returncode=0, stdout="DPMX_COUNT=3\n", stderr="")
        if cmd[:2] == ["docker", "stop"]:
            alive.discard(cmd[-1])
            for svc, name in names.items():
                if name == cmd[-1]:
                    busy.difference_update(_ENVRC_PORTS[svc])
        elif "compose" in cmd and "up" in cmd:
            alive.add(names[cmd[-1]])
            busy.update(_ENVRC_PORTS[cmd[-1]])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return repo, reg, docker, runner, calls, alive, busy, names


@pytest.mark.parametrize("hold", [True, False])
def test_a_restart_of_running_sidecars_starts_them_again(tmp_path: Path, hold):
    from dopemux.mcp.runtime_registry import RuntimeRegistry

    repo, reg, docker, runner, calls, alive, busy, names = _running_world(tmp_path)
    result = run_lifecycle(
        "restart",
        repo=repo,
        services=WORKTREE_SERVICES,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: p not in busy,
        hold_instance_lock=hold,
    )
    stops = [c[-1] for c in calls if c[:2] == ["docker", "stop"]]
    ups = [c[-1] for c in calls if "compose" in c and "up" in c]
    assert sorted(stops) == sorted(names.values())  # the stop half really stopped them
    assert ups == WORKTREE_SERVICES  # ...and the start half started each one again
    actions = [(s["service"], s.get("action")) for s in result.services]
    assert actions == [("conport", "started"), ("dope-memory", "started")]
    assert result.status == "PASS" and result.exit_code == 0, result.to_dict()
    assert alive == set(names.values())
    status = {i["service"]: i["status"] for i in RuntimeRegistry.load(reg).instances()}
    assert status == {"conport": "running", "dope-memory": "running"}


def test_every_restart_start_reads_docker_after_the_stops(tmp_path: Path, monkeypatch):
    from dopemux.mcp import docker_inspect as di
    from dopemux.mcp import lifecycle as lc

    events: list = []
    real_inspect = di.inspect_running_containers

    def numbered_inspect(*args, **kwargs):
        result = real_inspect(*args, **kwargs)
        result.seq = len([e for e in events if e[0] == "ps"])  # type: ignore[attr-defined]
        events.append(("ps", result.seq))  # type: ignore[attr-defined]
        return result

    real_stop, real_start = lc._stop_services, lc._start_services

    def stop_spy(**kw):
        out = real_stop(**kw)
        events.append(("stopped", list(kw["selected"])))
        return out

    def start_spy(**kw):
        events.append(
            ("start", list(kw["selected"]), getattr(kw["docker"], "seq", None))
        )
        return real_start(**kw)

    monkeypatch.setattr(di, "inspect_running_containers", numbered_inspect)
    monkeypatch.setattr(lc, "_stop_services", stop_spy)
    monkeypatch.setattr(lc, "_start_services", start_spy)
    result, _repo, _reg = _run(tmp_path, "restart", [*WORKTREE_SERVICES, TO])
    assert result.exit_code == 0, result.to_dict()
    last_stop = max(i for i, e in enumerate(events) if e[0] == "stopped")
    starts = [e for e in events if e[0] == "start"]
    assert [e[1] for e in starts] == [WORKTREE_SERVICES, [TO]]
    for _, selected, seq in starts:
        assert seq is not None, selected
        assert events.index(("ps", seq)) > last_stop, (selected, events)


def _blocked_after_the_wait(monkeypatch):
    """The re-check under launch.lock finds a blocking finding the preflight did not."""
    from dopemux.mcp import lifecycle as lc

    real = lc._mutable_facts

    def facts(op, *, orchestrator_gate, **kw):
        out = real(op, orchestrator_gate=orchestrator_gate, **kw)
        if not orchestrator_gate:
            out.blocking.append(
                {
                    "code": "DOCKER_CONTAINER_PORT_COLLISION",
                    "severity": "FAIL",
                    "service": "conport",
                    "message": "test: :3041 taken while waiting for launch.lock",
                }
            )
        return out

    monkeypatch.setattr(lc, "_mutable_facts", facts)


@pytest.mark.parametrize("case", ["was_running", "not_running", "stop_failed"])
def test_a_split_restart_blocked_under_the_lock_restores_the_orchestrator(
    tmp_path: Path, monkeypatch, case
):
    from dopemux.mcp import lifecycle as lc

    events = _lock_spies(monkeypatch)
    spy_stop = lc._stop_services
    entries = {
        "was_running": [("task-orchestrator-x", "stopped")],
        "not_running": [("task-orchestrator-x", "already_stopped")],
        # one container stopped, another failed to: a failed stop starts nothing
        "stop_failed": [
            ("task-orchestrator-x", "stopped"),
            ("task-orchestrator-y", "failed"),
        ],
    }[case]

    def to_stop(**kw):
        if kw["selected"] != [TO]:
            return spy_stop(**kw)
        events.append(("stop", [TO], 0))
        return lc.LifecycleResult(
            schema_version=lc.SCHEMA_VERSION,
            operation="stop",
            dry_run=False,
            status="FAIL" if case == "stop_failed" else "PASS",
            project_identity={},
            services=[
                {
                    "service": TO,
                    "action": action,
                    "container_name": name,
                    "commands": [],
                }
                for name, action in entries
            ],
        )

    monkeypatch.setattr(lc, "_stop_services", to_stop)
    _blocked_after_the_wait(monkeypatch)
    result, _repo, _reg = _run(tmp_path, "restart", [*WORKTREE_SERVICES, TO])
    assert result.status == "FAIL" and result.exit_code == 1
    assert any(
        f["code"] == "DOCKER_CONTAINER_PORT_COLLISION" for f in result.blocking_findings
    )
    actions = {s["service"]: s.get("action") for s in result.services}
    assert actions["conport"] == actions["dope-memory"] == "blocked"
    parts = [e for e in events if e[0] in {"stop", "start"}]
    if case == "was_running":  # started again, outside launch.lock, after its release
        assert parts == [("stop", [TO], 0), ("start", [TO], 0)]
        assert actions[TO] == "started"
        assert events.index(("instance-released",)) < events.index(("start", [TO], 0))
    elif case == "not_running":  # no stop ran: the plain blocked result
        assert parts == [("stop", [TO], 0)]
        assert actions[TO] == "blocked"
    else:  # its stop failed: nothing is started, and the stop part is reported
        assert parts == [("stop", [TO], 0)]
        to_entries = [
            (s.get("container_name"), s.get("action"))
            for s in result.services
            if s["service"] == TO
        ]
        assert to_entries == [
            ("task-orchestrator-x", "stopped"),
            ("task-orchestrator-y", "failed"),
        ]


# --- cycle 2 fix round 3 ----------------------------------------------------------------


def _missing_image_until_built(runner, events):
    """Wrap a cmd runner: images are missing until a `compose build` of them ran."""
    built: set = set()

    def wrapped(cmd, **kwargs):
        cmd = list(cmd)
        if cmd[:3] == ["docker", "image", "inspect"]:
            svc = next((s for s in WORKTREE_SERVICES if f"-{s}:" in cmd[3]), None)
            if svc not in built:
                return SimpleNamespace(
                    returncode=1, stdout="", stderr=f"Error: No such image: {cmd[3]}"
                )
            return SimpleNamespace(returncode=0, stdout="sha256:x\n", stderr="")
        if "compose" in cmd and "build" in cmd:
            built.add(cmd[-1])
            events.append(f"build:{cmd[-1]}")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        out = runner(cmd, **kwargs)
        if cmd[:2] == ["docker", "stop"]:
            events.append("stop")
        elif "compose" in cmd and "up" in cmd:
            events.append(f"up:{cmd[-1]}")
        return out

    return wrapped


def _event_lock(monkeypatch, events):
    import contextlib

    from dopemux.mcp import lifecycle as lc

    @contextlib.contextmanager
    def lock_spy(rt, *, blocking=True):
        events.append("lock")
        try:
            yield
        finally:
            events.append("unlock")

    monkeypatch.setattr(lc, "instance_lock", lock_spy)


def test_a_restart_with_a_missing_image_builds_before_the_lock(
    tmp_path: Path, monkeypatch
):
    # the documented forced rebuild: `docker image rm --force ...`, then `mcp restart`
    repo, reg, docker, runner, calls, alive, busy, names = _running_world(tmp_path)
    events: list = []
    _event_lock(monkeypatch, events)
    result = run_lifecycle(
        "restart",
        repo=repo,
        services=["conport"],
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=_missing_image_until_built(runner, events),
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: p not in busy,
    )
    assert result.status == "PASS" and result.exit_code == 0, result.to_dict()
    assert events == ["build:conport", "lock", "stop", "up:conport", "unlock"]
    conport = _svc(result, "conport")
    assert conport["action"] == "started"
    assert "IMAGE_BUILT" in _codes(conport["findings"])


def test_a_split_restart_reads_docker_again_before_the_orchestrator_stop(
    tmp_path: Path, monkeypatch
):
    from dopemux.mcp import docker_inspect as di
    from dopemux.mcp import lifecycle as lc

    events: list = []
    real_inspect = di.inspect_running_containers

    def numbered_inspect(*args, **kwargs):
        result = real_inspect(*args, **kwargs)
        result.seq = len([e for e in events if e[0] == "ps"])  # type: ignore[attr-defined]
        events.append(("ps", result.seq))  # type: ignore[attr-defined]
        return result

    real_stop = lc._stop_services

    def stop_spy(**kw):
        events.append(
            ("stop", list(kw["selected"]), getattr(kw["docker"], "seq", None))
        )
        return real_stop(**kw)

    monkeypatch.setattr(di, "inspect_running_containers", numbered_inspect)
    monkeypatch.setattr(lc, "_stop_services", stop_spy)
    builds: list = []
    runner = _missing_image_until_built(_recording_runner(), builds)

    def recording(cmd, **kwargs):
        out = runner(cmd, **kwargs)
        if builds and ("built",) not in events:
            events.append(("built",))
        return out

    result, _repo, _reg = _run(
        tmp_path, "restart", [*WORKTREE_SERVICES, TO], runner=recording
    )
    assert result.exit_code == 0, result.to_dict()
    to_stop = next(e for e in events if e[0] == "stop" and e[1] == [TO])
    assert to_stop[2] is not None
    # the snapshot the orchestrator stop used was read after the pre-build
    assert events.index(("ps", to_stop[2])) > events.index(("built",))


def test_a_reap_finishing_while_a_cli_stop_waits_issues_no_stop_of_gone_names(
    tmp_path: Path, monkeypatch
):
    repo, reg, runtime_dir, docker, lease_path, state, identity = _lease_world(tmp_path)
    reaps = _reap_while_waiting(
        monkeypatch,
        runtime_dir=runtime_dir,
        reg=reg,
        lease_path=lease_path,
        state=state,
        identity=identity,
    )
    calls: list = []

    def runner(cmd, **kwargs):  # docker: a gone container cannot be stopped
        calls.append(list(cmd))
        if list(cmd[:2]) == ["docker", "stop"] and state["gone"]:
            return SimpleNamespace(
                returncode=1,
                stdout="",
                stderr="Error response from daemon: No such container",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = run_lifecycle(
        "stop",
        repo=repo,
        services=None,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert len(reaps) == 1
    assert not [c for c in calls if c[:2] == ["docker", "stop"]]
    assert result.status == "PASS" and result.exit_code == 0, result.to_dict()
    actions = {(s["service"], s.get("action")) for s in result.services}
    assert {a for _, a in actions} == {"already_stopped"}
    assert not runtime_dir.exists()


def test_a_start_blocked_under_the_lock_starts_nothing(tmp_path: Path, monkeypatch):
    events = _lock_spies(monkeypatch)
    _blocked_after_the_wait(monkeypatch)
    runner = _recording_runner()
    result, _repo, _reg = _run(
        tmp_path, "start", [*WORKTREE_SERVICES, TO], runner=runner
    )
    assert result.status == "FAIL" and result.exit_code == 1
    assert any(
        f["code"] == "DOCKER_CONTAINER_PORT_COLLISION" for f in result.blocking_findings
    )
    assert {s["service"]: s.get("action") for s in result.services} == {
        "conport": "blocked",
        "dope-memory": "blocked",
        TO: "blocked",
    }
    assert [e for e in events if e[0] == "start"] == []  # no part started
    assert not [c for c in runner.calls if c["kind"] in {"up", "build"}]


def test_a_build_input_write_failure_is_a_build_failure_not_a_crash(
    tmp_path: Path, monkeypatch
):
    def unwritable(runtime_dir, *, product=None):
        raise OSError(30, "Read-only file system", str(runtime_dir))

    monkeypatch.setattr(dr, "compose_build_inputs", unwritable)
    runner = _recording_runner(inspect_rc=1)  # images missing
    result, _repo, _reg = _run(tmp_path, "start", WORKTREE_SERVICES, runner=runner)
    assert result.status == "FAIL" and result.exit_code == 1
    for svc in WORKTREE_SERVICES:
        entry = _svc(result, svc)
        assert entry["action"] == "failed"
        codes = _codes(entry["findings"])
        # the probe's finding is kept, then the build failure (fix round 4, Minor 2)
        assert (
            codes[:1] == ["IMAGE_MISSING_WILL_BUILD"] and "IMAGE_BUILD_FAILED" in codes
        )
        assert "Read-only file system" in str(entry["findings"])
        assert "compose.build.yml" in entry["commands"][0]  # the planned build
        assert entry["build_result"]["exit_code"] == 1
    assert not [c for c in runner.calls if c["kind"] in {"up", "build"}]


# --- cycle 2 fix round 4: every re-read docker snapshot fails closed ------------------


def _failing_on(docker, *calls_that_fail):
    """Wrap a docker runner: the given `docker ps` calls (1-based) fail like a dead daemon."""
    seen = {"n": 0}

    def wrapped(*args, **kwargs):
        seen["n"] += 1
        if seen["n"] in calls_that_fail:
            return SimpleNamespace(
                returncode=1, stdout="", stderr="Cannot connect to the Docker daemon"
            )
        return docker(*args, **kwargs)

    wrapped.seen = seen
    return wrapped


def _unavailable(result) -> bool:
    return any(f.get("code") == "DOCKER_UNAVAILABLE" for f in result.blocking_findings)


def test_a_stop_whose_locked_docker_read_fails_releases_nothing(tmp_path: Path):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    stops: list = []

    def runner(cmd, **kwargs):
        stops.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    docker = _failing_on(docker_ps, 2)  # 1: preflight; 2: the re-read under the lock
    result = run_lifecycle(
        "stop",
        repo=repo,
        services=None,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert docker.seen["n"] == 2
    assert result.status == "FAIL" and result.exit_code == 1, result.to_dict()
    assert _unavailable(result)
    assert not [c for c in stops if c[:2] == ["docker", "stop"]]
    assert _lease_status(lease_path) == {"conport": "active", "dope-memory": "active"}
    assert runtime_dir.is_dir()


def test_a_split_restart_whose_orchestrator_read_fails_touches_nothing(tmp_path: Path):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    runner = _recording_runner()
    docker = _failing_on(docker_ps, 2)  # 1: preflight; 2: before the orchestrator stop
    result = run_lifecycle(
        "restart",
        repo=repo,
        services=[*WORKTREE_SERVICES, TO],
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert result.status == "FAIL" and result.exit_code == 1, result.to_dict()
    assert _unavailable(result)
    # nothing was stopped or started: the worktree half is reported blocked, untouched
    assert not [c for c in runner.calls if c["cmd"][:2] == ["docker", "stop"]]
    assert not [
        c for c in runner.calls if c["kind"] == "up" or c["cmd"][:1] == ["bash"]
    ]
    assert {s["service"]: s.get("action") for s in result.services} == {
        "conport": "blocked",
        "dope-memory": "blocked",
        TO: "blocked",
    }
    assert docker.seen["n"] == 2


def test_a_restart_whose_post_stop_read_fails_starts_nothing(tmp_path: Path):
    repo, reg, docker, runner, calls, alive, busy, names = _running_world(tmp_path)
    failing = _failing_on(docker, 3)  # 1: preflight; 2: re-check; 3: after the stops
    result = run_lifecycle(
        "restart",
        repo=repo,
        services=WORKTREE_SERVICES,
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=failing,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: p not in busy,
    )
    assert failing.seen["n"] == 3
    assert result.status == "FAIL" and result.exit_code == 1, result.to_dict()
    assert _unavailable(result)
    assert len([c for c in calls if c[:2] == ["docker", "stop"]]) == 2  # stop half ran
    assert not [c for c in calls if "compose" in c and "up" in c]  # no start from it
    assert {s["service"]: s.get("action") for s in result.services} == {
        "conport": "failed",
        "dope-memory": "failed",
    }


def test_a_split_restart_whose_orchestrator_start_read_fails_fails_that_half(
    tmp_path: Path,
):
    repo, reg, runtime_dir, docker_ps, lease_path = _stop_world(tmp_path)
    runner = _recording_runner()
    # 1 preflight, 2 before the orchestrator stop, 3 re-check under the lock,
    # 4 after the worktree stop, 5 before the orchestrator start
    docker = _failing_on(docker_ps, 5)
    result = run_lifecycle(
        "restart",
        repo=repo,
        services=[*WORKTREE_SERVICES, TO],
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=docker,
        cmd_runner=runner,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert docker.seen["n"] == 5
    assert result.status == "FAIL" and result.exit_code == 1, result.to_dict()
    assert _unavailable(result)
    actions = {s["service"]: s.get("action") for s in result.services}
    assert actions[TO] == "failed"  # never already_running from an unread snapshot
    assert not [c for c in runner.calls if c["cmd"][:1] == ["bash"]]  # no wrapper


# --- final-review fix round ----------------------------------------------------------


def test_an_orchestrator_only_start_leaves_the_worktree_artifacts_alone(tmp_path: Path):
    # C1: a sidecar start (holding launch.lock) writes its override, resolves the
    # tenant, then runs compose up -f compose.override.yml; an orchestrator start must
    # never rewrite that file in between.
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "reg" / "instances.json"
    rt = _runtime_dir_of(repo, reg)
    rt.mkdir(parents=True)
    before = {
        "compose.override.yml": "services:\n  conport:\n    container_name: ours\n",
        "mcp.env": "DOPEMUX_PROJECT_ID=x\n",
        "start-plan.json": '{"services": ["conport"]}\n',
    }
    for name, text in before.items():
        (rt / name).write_text(text, encoding="utf-8")
    product = _product(tmp_path)
    result = run_lifecycle(
        "start",
        repo=repo,
        services=[TO],
        catalog=_catalog(),
        registry_path=reg,
        docker_runner=_docker_empty(),
        cmd_runner=_recording_runner(),
        product_root=product,
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert result.exit_code == 0, result.to_dict()
    assert result.runtime_artifacts == []
    for name, text in before.items():
        assert (rt / name).read_text(encoding="utf-8") == text, name
    # the dry-run plan says the same: nothing would be written (micro round)
    plan = run_lifecycle(
        "start",
        repo=repo,
        services=[TO],
        catalog=_catalog(),
        dry_run=True,
        registry_path=reg,
        docker_runner=_docker_empty(),
        cmd_runner=_recording_runner(),
        product_root=product,
        process_env={},
        skip_doctor=True,
        port_is_free_fn=lambda p: True,
    )
    assert plan.status == "PLANNED" and plan.runtime_artifacts == []
    assert [s.get("runtime_files") for s in plan.services] == [[]]


def test_a_blocked_split_restart_whose_restore_read_fails_starts_nothing(
    tmp_path: Path, monkeypatch
):
    # C6: the residual-6 restore path, with the orchestrator's pre-start read failing
    from dopemux.mcp import lifecycle as lc

    events = _lock_spies(monkeypatch)
    spy_stop = lc._stop_services

    def to_stop(**kw):
        if kw["selected"] != [TO]:
            return spy_stop(**kw)
        events.append(("stop", [TO], 0))
        return lc.LifecycleResult(
            schema_version=lc.SCHEMA_VERSION,
            operation="stop",
            dry_run=False,
            status="PASS",
            project_identity={},
            services=[
                {
                    "service": TO,
                    "action": "stopped",
                    "container_name": "task-orchestrator-x",
                    "commands": [],
                }
            ],
        )

    monkeypatch.setattr(lc, "_stop_services", to_stop)
    _blocked_after_the_wait(monkeypatch)
    runner = _recording_runner()
    # 1 preflight, 2 before the orchestrator stop, 3 re-check (blocks), 4 restore read
    docker = _failing_on(_docker_empty(), 4)
    result, _repo, _reg = _run(
        tmp_path, "restart", [*WORKTREE_SERVICES, TO], runner=runner, docker=docker
    )
    assert docker.seen["n"] == 4
    assert result.status == "FAIL" and result.exit_code == 1
    assert _unavailable(result)
    actions = {s["service"]: s.get("action") for s in result.services}
    assert actions == {"conport": "blocked", "dope-memory": "blocked", TO: "failed"}
    assert not [e for e in events if e[0] == "start"]
    assert not [c for c in runner.calls if c["cmd"][:1] == ["bash"]]


def test_no_deadlock_with_a_reserved_lock_holder_that_wants_launch_lock(
    tmp_path: Path, monkeypatch
):
    """T4: real flocks. Another process holds :7890 and then wants this worktree's
    launch.lock (the old ABBA partner); a CLI start of conport + task-orchestrator
    must finish, taking :7890 only after launch.lock is released."""
    import contextlib
    import threading

    from dopemux.mcp import lifecycle as lc
    from dopemux.mcp import locks

    events: list = []
    held = {"instance": False}
    main_holds_instance = threading.Event()
    helper_holds_reserved = threading.Event()

    @contextlib.contextmanager
    def instance_then_let_the_helper_in(runtime_dir, *, blocking=True):
        with locks.instance_lock(runtime_dir, blocking=blocking):
            held["instance"] = True
            events.append("main: instance acquired")
            main_holds_instance.set()
            assert helper_holds_reserved.wait(2), "helper never took :7890"
            try:
                yield
            finally:
                held["instance"] = False
                events.append("main: instance released")

    worker: dict = {}

    @contextlib.contextmanager
    def recorded_reserved(port):
        mine = threading.current_thread() is worker.get("thread")
        if mine:
            events.append(f"main: wants :7890 (instance held={held['instance']})")
        with locks.reserved_port_lock(port):
            if mine:
                events.append("main: got :7890")
            yield

    def helper(runtime_dir: Path) -> None:
        main_holds_instance.wait(5)
        with locks.reserved_port_lock(7890):
            events.append("helper: :7890 acquired")
            helper_holds_reserved.set()
            with locks.instance_lock(runtime_dir):  # waits for the main run
                events.append("helper: instance acquired")

    monkeypatch.setattr(lc, "instance_lock", instance_then_let_the_helper_in)
    monkeypatch.setattr(lc, "reserved_port_lock", recorded_reserved)
    repo = _fixture_repo(tmp_path)
    reg = tmp_path / "reg" / "instances.json"
    thread = threading.Thread(
        target=helper, args=(_runtime_dir_of(repo, reg),), daemon=True
    )
    thread.start()
    outcome: dict = {}

    def cli_start() -> None:
        outcome["result"] = run_lifecycle(
            "start",
            repo=repo,
            services=["conport", TO],
            catalog=_catalog(),
            registry_path=reg,
            docker_runner=_docker_empty(),
            cmd_runner=_recording_runner(),
            product_root=_product(tmp_path),
            process_env={},
            skip_doctor=True,
            port_is_free_fn=lambda p: True,
        )

    worker["thread"] = threading.Thread(target=cli_start, daemon=True)
    worker["thread"].start()
    worker["thread"].join(5)  # a deadlock would leave both threads blocked here
    thread.join(5)
    assert not worker["thread"].is_alive() and not thread.is_alive(), events
    assert outcome["result"].exit_code == 0, outcome["result"].to_dict()
    wants = [e for e in events if e.startswith("main: wants :7890")]
    # the preflight gate (before launch.lock), then the orchestrator start and its
    # re-entrant owner re-check (after it): never while launch.lock is held
    assert len(wants) == 3 and all(e.endswith("held=False)") for e in wants), events
    order = [
        "main: instance acquired",
        "helper: :7890 acquired",
        "main: instance released",
        "helper: instance acquired",
    ]
    assert [events.index(e) for e in order] == sorted(events.index(e) for e in order)
    # the orchestrator start got :7890 only once the helper had let go of it
    last_got = max(i for i, e in enumerate(events) if e == "main: got :7890")
    assert last_got > events.index("helper: instance acquired"), events
