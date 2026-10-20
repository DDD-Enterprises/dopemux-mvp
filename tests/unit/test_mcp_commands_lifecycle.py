"""CLI tests for repo-aware mcp start/stop/status."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from dopemux.commands import mcp_commands


def _catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT}/sse",
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
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
            },
        },
    }


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "conport": {"type": "sse", "url": "http://localhost:${CONPORT_MCP_PORT}/sse"},
                }
            }
        )
    )
    (repo / ".envrc.dopemux-mcp").write_text(
        f"export DOPEMUX_WORKSPACE_ID={repo}\n"
        f"export DOPEMUX_WORKSPACE_ROOT={repo}\n"
        f"export DOPEMUX_PROJECT_ROOT={repo}\n"
        f"export CONPORT_MCP_PORT=3041\n"
        f"export CONPORT_HTTP_PORT=3040\n"
        f"export CONPORT_INFO_PORT=4040\n"
        f"export DOPEMUX_INSTANCE_ID=abcd\n"
    )
    return repo


def test_cli_start_dry_run_json(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))

    # Avoid real docker
    import dopemux.mcp.docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["start", "--repo", str(repo), "--services", "conport", "--dry-run", "--json"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["operation"] == "start"
    assert payload["dry_run"] is True
    assert payload["schema_version"] == "1.0"
    assert not reg.exists()  # dry-run no registry


def test_cli_status_json(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))

    import dopemux.mcp.docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["status", "--repo", str(repo), "--json"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["operation"] == "status"
    assert "registry" in payload
    assert "services" in payload


def test_cli_up_repo_aliases_start(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))

    import dopemux.mcp.docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["up", "--repo", str(repo), "--services", "conport", "--dry-run", "--json"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["operation"] == "start"


def test_cli_up_dry_run_without_repo_stays_legacy(monkeypatch):
    """--dry-run/--json alone must not divert bare `mcp up` to the reconciler."""
    called = {"legacy": False, "lifecycle": False}

    def fake_run(cmd, **kwargs):  # noqa: ARG001
        called["legacy"] = True
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_lifecycle(*args, **kwargs):  # noqa: ARG001
        called["lifecycle"] = True
        raise AssertionError("lifecycle should not run without --repo")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)
    monkeypatch.setattr(mcp_commands, "_run_lifecycle_cli", fake_lifecycle)

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["up", "--services", "conport", "--dry-run", "--json"],
    )
    assert called["lifecycle"] is False, result.output
    assert called["legacy"] is True, result.output
    assert result.exit_code == 0, result.output


def test_cli_up_creates_missing_external_network_before_compose(monkeypatch):
    """Removing network initialization must fail before compose reaches a clean host."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):  # noqa: ARG001
        calls.append(list(cmd))
        if cmd == ["docker", "network", "ls", "--format", "{{.Name}}"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)

    result = CliRunner().invoke(
        mcp_commands.mcp,
        ["up", "--services", "conport"],
    )

    assert result.exit_code == 0, result.output
    assert calls[0] == ["docker", "network", "ls", "--format", "{{.Name}}"]
    assert calls[1] == ["docker", "network", "create", "dopemux-network"]
    assert calls[2] == [
        "docker",
        "compose",
        "-f",
        "compose.yml",
        "up",
        "-d",
        "--build",
        "conport",
    ]


def test_cli_start_all_fallback_creates_missing_external_network_before_compose(monkeypatch):
    """start-all's manual fallback must not reach compose on a clean host without
    the network preflight (same class of bug `mcp up` already had fixed)."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):  # noqa: ARG001
        calls.append(list(cmd))
        if cmd == ["docker", "network", "ls", "--format", "{{.Name}}"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)
    monkeypatch.setattr(mcp_commands.Path, "exists", lambda self: False)

    result = CliRunner().invoke(mcp_commands.mcp, ["start-all"])

    assert result.exit_code == 0, result.output
    assert calls[0] == ["docker", "network", "ls", "--format", "{{.Name}}"]
    assert calls[1] == ["docker", "network", "create", "dopemux-network"]
    assert calls[2] == ["docker", "compose", "-f", "compose.yml", "up", "-d"]
    assert calls[3] == [
        "docker",
        "compose",
        "-f",
        "compose.yml",
        "--profile",
        "manual",
        "up",
        "-d",
        "task-orchestrator",
    ]


def test_cli_down_dry_run_without_repo_stays_legacy(monkeypatch):
    """--dry-run/--json alone must not divert bare `mcp down` to the reconciler."""
    called = {"legacy": False, "lifecycle": False}

    def fake_run(cmd, check=True, **kwargs):  # noqa: ARG001
        called["legacy"] = True
        return SimpleNamespace(returncode=0)

    def fake_lifecycle(*args, **kwargs):  # noqa: ARG001
        called["lifecycle"] = True
        raise AssertionError("lifecycle should not run without --repo")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)
    monkeypatch.setattr(mcp_commands, "_run_lifecycle_cli", fake_lifecycle)
    monkeypatch.setattr(mcp_commands, "_compose_services", lambda: {"conport"})
    monkeypatch.setattr(mcp_commands, "DEFAULT_MCP_SERVICES", {"conport"})

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["down", "--dry-run", "--json"],
    )
    assert called["lifecycle"] is False, result.output
    assert called["legacy"] is True, result.output
    assert result.exit_code == 0, result.output


def _clear_host_path_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("HOST_CODE_PARENT_DIR", raising=False)
    monkeypatch.delenv("HOST_PROJECT_RELATIVE_PATH", raising=False)
    product = tmp_path / "dopemux-mvp"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))


_Call = tuple[list[str], "dict | None"]


def _capture_subprocess_envs(monkeypatch) -> list[_Call]:
    calls: list[_Call] = []

    def fake_run(cmd, **kwargs):
        calls.append((list(cmd), kwargs.get("env")))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)
    return calls


def _compose_envs(calls, verb: str):
    prefix = ["docker", "compose", "-f", "compose.yml"]
    return [env for cmd, env in calls if cmd[:4] == prefix and verb in cmd]


def test_cli_down_and_logs_pass_compose_host_path_env(
    monkeypatch, tmp_path
):
    _clear_host_path_env(monkeypatch, tmp_path)
    calls = _capture_subprocess_envs(monkeypatch)
    monkeypatch.setattr(mcp_commands, "_compose_services", lambda: {"conport"})
    monkeypatch.setattr(mcp_commands, "DEFAULT_MCP_SERVICES", {"conport"})

    runner = CliRunner()
    down = runner.invoke(mcp_commands.mcp, ["down"])
    logs = runner.invoke(mcp_commands.mcp, ["logs"])

    assert down.exit_code == 0, down.output
    assert logs.exit_code == 0, logs.output
    rm_envs = _compose_envs(calls, "rm")
    log_envs = _compose_envs(calls, "logs")
    assert len(rm_envs) == 1 and len(log_envs) == 1
    for env in rm_envs + log_envs:
        assert env is not None
        assert env["HOST_CODE_PARENT_DIR"] == str(tmp_path)
        assert env["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"


def test_cli_up_injects_host_paths_unless_dope_context_started(
    monkeypatch, tmp_path
):
    _clear_host_path_env(monkeypatch, tmp_path)
    calls = _capture_subprocess_envs(monkeypatch)
    monkeypatch.setattr(
        mcp_commands, "_compose_services", lambda: {"postgres", "dope-context"}
    )

    runner = CliRunner()
    ok = runner.invoke(mcp_commands.mcp, ["up", "--services", "postgres"])
    guarded = runner.invoke(
        mcp_commands.mcp, ["up", "--services", "dope-context"]
    )

    assert ok.exit_code == 0, ok.output
    assert guarded.exit_code == 0, guarded.output
    up_envs = _compose_envs(calls, "up")
    assert len(up_envs) == 2
    postgres_env, dope_context_env = up_envs
    assert postgres_env["HOST_CODE_PARENT_DIR"] == str(tmp_path)
    assert postgres_env["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"
    # dope-context keeps the fail-closed `:?` guard: no derived defaults.
    assert "HOST_CODE_PARENT_DIR" not in dope_context_env
    assert "HOST_PROJECT_RELATIVE_PATH" not in dope_context_env


def test_cli_start_all_fallback_never_defaults_host_paths(
    monkeypatch, tmp_path
):
    _clear_host_path_env(monkeypatch, tmp_path)
    calls = _capture_subprocess_envs(monkeypatch)
    monkeypatch.setattr(mcp_commands.Path, "exists", lambda self: False)

    result = CliRunner().invoke(mcp_commands.mcp, ["start-all"])

    assert result.exit_code == 0, result.output
    up_envs = _compose_envs(calls, "up")
    assert len(up_envs) == 2
    for env in up_envs:
        assert env is not None
        assert env["DOPECON_BRIDGE_TOKEN"]
        assert "HOST_CODE_PARENT_DIR" not in env


def test_cli_legacy_status_passes_compose_host_path_env(
    monkeypatch, tmp_path
):
    _clear_host_path_env(monkeypatch, tmp_path)
    calls = _capture_subprocess_envs(monkeypatch)

    result = CliRunner().invoke(
        mcp_commands.mcp, ["status", "--legacy-compose"]
    )

    assert result.exit_code == 0, result.output
    ps_envs = _compose_envs(calls, "ps")
    assert len(ps_envs) == 1
    assert ps_envs[0]["HOST_CODE_PARENT_DIR"] == str(tmp_path)
