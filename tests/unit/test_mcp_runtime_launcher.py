"""Tests for docker_runtime helpers (compose commands / artifacts)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dopemux.mcp import docker_runtime as dr


def test_compose_up_command_includes_override_and_no_deps(tmp_path: Path):
    product = tmp_path
    (product / "compose.yml").write_text("services: {}\n")
    override = tmp_path / "compose.override.yml"
    envf = tmp_path / "mcp.env"
    override.write_text("services: {}\n")
    envf.write_text("X=1\n")
    cmd = dr.compose_up_command(
        product=product,
        override_path=override,
        env_file=envf,
        project_name="dopemux_proj_abcd",
        services=["conport", "dope-memory"],
        no_deps=True,
    )
    assert cmd[:2] == ["docker", "compose"]
    assert "--no-deps" in cmd
    assert "conport" in cmd
    assert str(override) in cmd
    assert "dopemux_proj_abcd" in cmd


def test_write_runtime_artifacts_dry_run_no_files(tmp_path: Path):
    runtime = tmp_path / "rt"
    paths = dr.write_runtime_artifacts(
        runtime,
        env_text="A=1\n",
        override_text="services: {}\n",
        plan={"x": 1},
        dry_run=True,
    )
    assert "mcp.env" in paths
    assert not runtime.exists()


def test_write_runtime_artifacts_writes(tmp_path: Path):
    runtime = tmp_path / "rt"
    paths = dr.write_runtime_artifacts(
        runtime,
        env_text="CONPORT_MCP_PORT=3041\n",
        override_text="services:\n  conport: {}\n",
        plan={"services": ["conport"]},
        dry_run=False,
    )
    assert Path(paths["mcp.env"]).is_file()
    assert "3041" in Path(paths["mcp.env"]).read_text()
    assert Path(paths["compose.override.yml"]).is_file()


def test_env_with_compose_interpolation_sets_placeholder(monkeypatch):
    monkeypatch.delenv("DOPECON_BRIDGE_TOKEN", raising=False)
    env = dr.env_with_compose_interpolation({"PATH": "/bin"})
    assert env["DOPECON_BRIDGE_TOKEN"] == dr.COMPOSE_INTERPOLATION_PLACEHOLDER
    kept = dr.env_with_compose_interpolation(
        {"PATH": "/bin", "DOPECON_BRIDGE_TOKEN": "real-jwt"}
    )
    assert kept["DOPECON_BRIDGE_TOKEN"] == "real-jwt"


def _fake_product_root(monkeypatch, tmp_path: Path) -> Path:
    root = tmp_path / "dopemux-mvp"
    monkeypatch.setattr(dr, "product_root", lambda: root)
    return root


def test_env_with_compose_interpolation_derives_host_paths(
    monkeypatch, tmp_path
):
    root = _fake_product_root(monkeypatch, tmp_path)
    env = dr.env_with_compose_interpolation({"PATH": "/bin"})
    assert env["HOST_CODE_PARENT_DIR"] == str(root.parent)
    assert env["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"


def test_env_with_compose_interpolation_preserves_preset_host_paths(
    monkeypatch, tmp_path
):
    _fake_product_root(monkeypatch, tmp_path)
    env = dr.env_with_compose_interpolation(
        {
            "HOST_CODE_PARENT_DIR": "/operator/code",
            "HOST_PROJECT_RELATIVE_PATH": "other",
        }
    )
    assert env["HOST_CODE_PARENT_DIR"] == "/operator/code"
    assert env["HOST_PROJECT_RELATIVE_PATH"] == "other"


def test_env_with_compose_interpolation_replaces_blank_host_paths(
    monkeypatch, tmp_path
):
    root = _fake_product_root(monkeypatch, tmp_path)
    env = dr.env_with_compose_interpolation(
        {"HOST_CODE_PARENT_DIR": "", "HOST_PROJECT_RELATIVE_PATH": "  "}
    )
    assert env["HOST_CODE_PARENT_DIR"] == str(root.parent)
    assert env["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"


def test_env_with_compose_interpolation_tolerates_missing_product_root(
    monkeypatch,
):
    def boom() -> Path:
        raise FileNotFoundError("no product root")

    monkeypatch.setattr(dr, "product_root", boom)
    env = dr.env_with_compose_interpolation({"PATH": "/bin"})
    assert "HOST_CODE_PARENT_DIR" not in env
    assert "HOST_PROJECT_RELATIVE_PATH" not in env
    assert env["DOPECON_BRIDGE_TOKEN"] == dr.COMPOSE_INTERPOLATION_PLACEHOLDER


def test_env_with_compose_interpolation_host_path_defaults_disabled(
    monkeypatch, tmp_path
):
    _fake_product_root(monkeypatch, tmp_path)
    env = dr.env_with_compose_interpolation(
        {"PATH": "/bin"}, host_path_defaults=False
    )
    assert "HOST_CODE_PARENT_DIR" not in env
    assert "HOST_PROJECT_RELATIVE_PATH" not in env
    assert env["DOPECON_BRIDGE_TOKEN"] == dr.COMPOSE_INTERPOLATION_PLACEHOLDER


def test_mcp_env_skips_secrets():
    text = dr.generate_mcp_env(
        {
            "CONPORT_MCP_PORT": 3041,
            "OPENAI_API_KEY": "sk-secret",
            "DOPEMUX_WORKSPACE_ID": "/tmp/x",
        }
    )
    assert "3041" in text
    assert "OPENAI_API_KEY" not in text
    assert "DOPEMUX_WORKSPACE_ID" in text


def test_labels_required_keys():
    labels = dr.build_labels(
        project_id="p",
        workspace_id="/w",
        project_root="/p",
        worktree_root="/w",
        project_hash="h",
        worktree_hash="abcd",
        instance_id="p-abcd-conport",
        service="conport",
        scope="worktree",
        transport="sse",
    )
    assert labels["dopemux.managed"] == "true"
    assert labels["dopemux.created_by"] == "dopemux-mcp"
    assert labels["dopemux.service"] == "conport"


def test_should_name_image_project_dash_service_when_compose_has_build_only():
    # Arrange / Act
    name = dr.compose_image_name("dopemux_adops_a22d", "conport")
    # Assert
    assert name == "dopemux_adops_a22d-conport"


def test_should_build_inspect_command_with_id_format_when_probing_image():
    # Arrange / Act
    cmd = dr.docker_image_inspect_command("proj-conport")
    # Assert
    assert cmd == ["docker", "image", "inspect", "proj-conport", "--format", "{{.Id}}"]


def _fake_runner(returncode: int, stdout: str = "", stderr: str = "", raises=None):
    calls = []

    def runner(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        if raises is not None:
            raise raises
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    runner.calls = calls
    return runner


def test_should_report_image_present_when_inspect_exits_zero():
    # Arrange
    runner = _fake_runner(0, stdout="sha256:abc\n")
    # Act
    present = dr.docker_image_exists("proj-conport", runner=runner)
    # Assert
    assert present is True
    assert runner.calls[0][0] == dr.docker_image_inspect_command("proj-conport")
    assert runner.calls[0][1]["timeout"] == 30.0


def test_should_report_image_absent_when_inspect_exits_one():
    # Arrange
    runner = _fake_runner(1, stderr="Error: No such image: proj-conport")
    # Act / Assert
    assert dr.docker_image_exists("proj-conport", runner=runner) is False


def test_should_report_image_unknown_when_docker_is_not_installed():
    # Arrange
    runner = _fake_runner(0, raises=FileNotFoundError("docker"))
    # Act / Assert
    assert dr.docker_image_exists("proj-conport", runner=runner) is None


def test_should_report_image_unknown_when_inspect_exits_unexpected_code():
    # Arrange
    runner = _fake_runner(125)
    # Act / Assert
    assert dr.docker_image_exists("proj-conport", runner=runner) is None


def test_should_build_compose_build_command_with_same_prefix_as_up(tmp_path: Path):
    # Arrange
    override = tmp_path / "compose.override.yml"
    envf = tmp_path / "mcp.env"
    # Act
    cmd = dr.compose_build_command(
        product=tmp_path,
        override_path=override,
        env_file=envf,
        project_name="dopemux_proj_abcd",
        services=["conport", "dope-memory"],
    )
    up = dr.compose_up_command(
        product=tmp_path,
        override_path=override,
        env_file=envf,
        project_name="dopemux_proj_abcd",
        services=["conport"],
    )
    # Assert
    assert cmd[:2] == ["docker", "compose"]
    assert cmd[: up.index("up")] == cmd[: cmd.index("build")]
    assert cmd[2:4] == ["-f", str(tmp_path / "compose.yml")]
    assert cmd[4:6] == ["-f", str(override)]
    assert cmd[6:8] == ["--env-file", str(envf)]
    assert cmd[8:10] == ["-p", "dopemux_proj_abcd"]
    assert cmd[10:] == ["build", "conport", "dope-memory"]


def test_should_default_build_timeout_when_env_unset_or_invalid():
    # Arrange / Act / Assert
    assert dr.build_timeout_secs({}) == 1800.0
    assert dr.build_timeout_secs({"DOPEMUX_MCP_BUILD_TIMEOUT_SECS": "42"}) == 42.0
    assert dr.build_timeout_secs({"DOPEMUX_MCP_BUILD_TIMEOUT_SECS": "nope"}) == 1800.0
    assert dr.build_timeout_secs({"DOPEMUX_MCP_BUILD_TIMEOUT_SECS": "-5"}) == 1800.0
    assert dr.build_timeout_secs({"DOPEMUX_MCP_BUILD_TIMEOUT_SECS": "0"}) == 1800.0


def test_should_default_up_timeout_when_env_unset_or_invalid():
    # Arrange / Act / Assert
    assert dr.up_timeout_secs({}) == 180.0
    assert dr.up_timeout_secs({"DOPEMUX_MCP_UP_TIMEOUT_SECS": "300"}) == 300.0
    assert dr.up_timeout_secs({"DOPEMUX_MCP_UP_TIMEOUT_SECS": "x"}) == 180.0
    assert dr.up_timeout_secs({"DOPEMUX_MCP_UP_TIMEOUT_SECS": "-1"}) == 180.0


def test_should_read_timeouts_from_process_env_when_no_mapping_given(monkeypatch):
    # Arrange
    monkeypatch.setenv("DOPEMUX_MCP_BUILD_TIMEOUT_SECS", "77")
    # Act / Assert
    assert dr.build_timeout_secs() == 77.0


def test_should_set_host_dirs_from_product_when_unset():
    # Arrange / Act
    env = dr.env_with_compose_interpolation({}, product=Path("/x/y/dopemux-mvp"))
    # Assert
    assert env["HOST_CODE_PARENT_DIR"] == "/x/y"
    assert env["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"
    assert env["DOPECON_BRIDGE_TOKEN"] == dr.COMPOSE_INTERPOLATION_PLACEHOLDER


def test_should_preserve_explicit_host_dirs_when_set_in_base():
    # Arrange
    base = {"HOST_CODE_PARENT_DIR": "/keep", "HOST_PROJECT_RELATIVE_PATH": "me"}
    # Act
    env = dr.env_with_compose_interpolation(base, product=Path("/x/y/dopemux-mvp"))
    # Assert
    assert env["HOST_CODE_PARENT_DIR"] == "/keep"
    assert env["HOST_PROJECT_RELATIVE_PATH"] == "me"


def test_should_replace_blank_host_dirs_when_base_has_empty_values():
    # Arrange
    base = {"HOST_CODE_PARENT_DIR": "  ", "HOST_PROJECT_RELATIVE_PATH": ""}
    # Act
    env = dr.env_with_compose_interpolation(base, product=Path("/x/y/dopemux-mvp"))
    # Assert
    assert env["HOST_CODE_PARENT_DIR"] == "/x/y"
    assert env["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"


def test_should_leave_host_dirs_unset_when_product_root_not_found(monkeypatch):
    # Arrange
    def boom():
        raise FileNotFoundError("nope")

    monkeypatch.setattr(dr, "product_root", boom)
    # Act
    env = dr.env_with_compose_interpolation({})
    # Assert
    assert "HOST_CODE_PARENT_DIR" not in env
    assert "HOST_PROJECT_RELATIVE_PATH" not in env


def test_should_report_budget_in_timeout_message_when_command_times_out():
    # Arrange
    import subprocess

    runner = _fake_runner(0, raises=subprocess.TimeoutExpired(cmd="x", timeout=5))
    # Act
    result = dr.run_cmd(["docker", "x"], runner=runner, timeout=5.0)
    # Assert
    assert result.exit_code == 124
    assert "timed out after 5s" in result.stderr


def test_should_report_image_unknown_when_daemon_unreachable_exits_one():
    # Arrange: docker CLI exits 1 for daemon errors too, without "No such image"
    runner = _fake_runner(
        1, stderr="Cannot connect to the Docker daemon at unix:///var/run/docker.sock"
    )
    # Act
    present = dr.docker_image_exists("proj-conport", runner=runner)
    # Assert
    assert present is None
