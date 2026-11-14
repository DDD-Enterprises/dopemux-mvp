"""`--repo <target>` commands load the target checkout's mcp_catalog.yaml, not the caller's."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
import yaml
from click.testing import CliRunner

from dopemux.commands import mcp_commands


def _git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(
            ["git", "config", key, value], cwd=path, check=True, capture_output=True
        )
    (path / "README").write_text("x\n")
    subprocess.run(["git", "add", "README"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)
    return path.resolve()


def _server(port_var: str, base: int) -> Dict[str, Any]:
    return {
        "scope": "per-worktree",
        "transport": "http",
        "url_template": f"http://localhost:${{{port_var}:-{base}}}/mcp",
        "port_var": port_var,
        "default_port_base": base,
        "management_model": "compose-service",
    }


def _write_catalog(repo: Path, servers: Dict[str, Dict[str, Any]], defaults: List[str]) -> None:
    (repo / mcp_commands.CATALOG_FILENAME).write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "defaults": {"per_worktree": defaults},
                "servers": servers,
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture
def repos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    for name in (
        "DOPEMUX_MCP_CATALOG",
        "DOPEMUX_WORKSPACE_ROOT",
        "DOPEMUX_PROJECT_ROOT",
        "DOPEMUX_INSTANCE_ID",
        "DOPEMUX_WORKSPACE_ID",
        "TASK_ORCHESTRATOR_PROJECT_ROOT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "leases.json"))
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "runtime.json"))
    caller = _git_init(tmp_path / "caller")
    target = _git_init(tmp_path / "target")
    _write_catalog(caller, {"base-svc": _server("BASE_SVC_PORT", 4100)}, ["base-svc"])
    _write_catalog(
        target,
        {
            "base-svc": _server("BASE_SVC_PORT", 4100),
            "target-only-svc": _server("TARGET_ONLY_PORT", 4200),
        },
        ["base-svc"],
    )
    monkeypatch.chdir(caller)
    return SimpleNamespace(caller=caller, target=target)


def test_init_repo_uses_the_targets_catalog_from_another_cwd(repos: SimpleNamespace) -> None:
    result = CliRunner().invoke(
        mcp_commands.mcp,
        ["init", "--repo", str(repos.target), "--with", "target-only-svc"],
    )

    assert result.exit_code == 0, result.output
    rendered = json.loads((repos.target / ".mcp.json").read_text())
    assert set(rendered["mcpServers"]) == {"base-svc", "target-only-svc"}
    envrc = (repos.target / mcp_commands.ENVRC_FILENAME).read_text()
    assert "export TARGET_ONLY_PORT=" in envrc
    assert not (repos.caller / ".mcp.json").exists()


def test_init_without_repo_still_uses_the_cwd_checkouts_catalog(
    repos: SimpleNamespace,
) -> None:
    result = CliRunner().invoke(mcp_commands.mcp, ["init", "--with", "target-only-svc"])

    # The caller's own catalog does not define the target-only server.
    assert result.exit_code != 0
    assert "target-only-svc" in result.output
    assert not (repos.caller / ".mcp.json").exists()


@pytest.mark.parametrize("operation", ["start", "stop", "restart", "status"])
def test_run_lifecycle_cli_loads_the_resolved_repo_catalog(
    operation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dopemux.mcp import lifecycle

    loaded: List[Optional[Path]] = []
    sentinel = {"version": 1, "servers": {}, "marker": "target"}

    def fake_load(repo: Optional[Path] = None) -> Dict[str, Any]:
        loaded.append(repo)
        return sentinel

    seen: Dict[str, Any] = {}

    def fake_run(op: str, **kwargs: Any) -> Any:
        seen.update(kwargs)
        return SimpleNamespace(
            status="PASS", exit_code=0, to_json=lambda: "{}\n"
        )

    monkeypatch.setattr(mcp_commands, "_load_catalog", fake_load)
    monkeypatch.setattr(lifecycle, "run_lifecycle", fake_run)
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sub" / ".." / "target"
    target.mkdir(parents=True)

    mcp_commands._run_lifecycle_cli(
        operation,
        repo_arg=target,
        services=None,
        dry_run=True,
        json_output=True,
    )

    assert loaded == [target.resolve()]
    assert seen["catalog"] is sentinel
    assert seen["repo"] == target.resolve()


def test_run_lifecycle_cli_without_repo_keeps_the_default_catalog_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dopemux.mcp import lifecycle

    loaded: List[Any] = []

    def fake_load(*args: Any) -> Dict[str, Any]:
        loaded.append(args)
        return {"version": 1, "servers": {}}

    monkeypatch.setattr(mcp_commands, "_load_catalog", fake_load)
    monkeypatch.setattr(
        lifecycle,
        "run_lifecycle",
        lambda op, **kw: SimpleNamespace(status="PASS", exit_code=0, to_json=lambda: "{}\n"),
    )

    mcp_commands._run_lifecycle_cli(
        "status", repo_arg=None, services=None, dry_run=True, json_output=True
    )

    assert loaded == [()]


def test_repair_config_repo_reports_and_uses_the_targets_catalog(
    repos: SimpleNamespace,
) -> None:
    (repos.target / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    result = CliRunner().invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(repos.target), "--dry-run", "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    target_catalog = str(repos.target / mcp_commands.CATALOG_FILENAME)
    assert data["inputs"]["catalog_paths"] == [target_catalog]


# --- Task A2: an explicit --repo inside a checkout is normalized to its root ----


@pytest.fixture
def target_subdir(repos: SimpleNamespace) -> Path:
    sub = repos.target / "src" / "pkg"
    sub.mkdir(parents=True)
    return sub


def test_init_repo_subdirectory_writes_at_the_checkout_root(
    repos: SimpleNamespace, target_subdir: Path
) -> None:
    result = CliRunner().invoke(
        mcp_commands.mcp,
        ["init", "--repo", str(target_subdir), "--with", "target-only-svc"],
    )

    assert result.exit_code == 0, result.output
    # Files land at the checkout root, never in the subdirectory.
    assert (repos.target / ".mcp.json").is_file()
    assert (repos.target / mcp_commands.ENVRC_FILENAME).is_file()
    assert not (target_subdir / ".mcp.json").exists()
    assert not (target_subdir / mcp_commands.ENVRC_FILENAME).exists()
    # The checkout's repo-local catalog was used (target-only server accepted).
    rendered = json.loads((repos.target / ".mcp.json").read_text())
    assert set(rendered["mcpServers"]) == {"base-svc", "target-only-svc"}
    envrc = (repos.target / mcp_commands.ENVRC_FILENAME).read_text()
    assert f"export DOPEMUX_PROJECT_ROOT={repos.target}" in envrc
    assert str(target_subdir) not in envrc
    # Output and next steps name the root, not the subdirectory.
    flat = "".join(result.output.split())
    assert "".join(str(repos.target).split()) in flat
    assert "".join(f"--repo {target_subdir}".split()) not in flat


def test_init_repo_outside_git_keeps_the_identity_error(
    repos: SimpleNamespace, tmp_path: Path
) -> None:
    plain = tmp_path / "not-a-checkout"
    plain.mkdir()

    result = CliRunner().invoke(mcp_commands.mcp, ["init", "--repo", str(plain)])

    assert result.exit_code != 0
    assert "Could not resolve project identity" in result.output
    assert not (plain / ".mcp.json").exists()


def test_resolve_repo_arg_normalizes_a_subdirectory_to_the_toplevel(
    repos: SimpleNamespace, target_subdir: Path
) -> None:
    assert mcp_commands._resolve_repo_arg(target_subdir) == repos.target
    assert mcp_commands._resolve_repo_arg(repos.target) == repos.target


def test_git_toplevel_helper_degrades_to_the_given_path_outside_git(
    tmp_path: Path,
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()

    assert mcp_commands._git_toplevel(plain) == plain.resolve()


def test_run_lifecycle_cli_loads_the_toplevel_catalog_for_a_subdirectory(
    repos: SimpleNamespace, target_subdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dopemux.mcp import lifecycle

    loaded: List[Optional[Path]] = []

    def fake_load(repo: Optional[Path] = None) -> Dict[str, Any]:
        loaded.append(repo)
        return {"version": 1, "servers": {}}

    monkeypatch.setattr(mcp_commands, "_load_catalog", fake_load)
    monkeypatch.setattr(
        lifecycle,
        "run_lifecycle",
        lambda op, **kw: SimpleNamespace(status="PASS", exit_code=0, to_json=lambda: "{}\n"),
    )

    mcp_commands._run_lifecycle_cli(
        "status", repo_arg=target_subdir, services=None, dry_run=True, json_output=True
    )

    assert loaded == [repos.target]


def test_status_repo_subdirectory_reads_mcp_json_from_the_checkout_root(
    repos: SimpleNamespace,
    target_subdir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Real run_lifecycle (not faked): .mcp.json / envrc must come from the root,
    # not from the --repo subdirectory where they do not exist.
    import dopemux.mcp.docker_inspect as di

    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "instances.json"))
    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )
    (repos.target / ".mcp.json").write_text(
        json.dumps(
            {"mcpServers": {"target-only-svc": {"type": "http", "url": "http://localhost:4200/mcp"}}}
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        mcp_commands.mcp, ["status", "--repo", str(target_subdir), "--json"]
    )

    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["project_identity"]["worktree_root"] == str(repos.target)
    assert "target-only-svc" in json.dumps(payload["services"])


def test_git_toplevel_returns_the_resolved_path_for_a_nonexistent_dir(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does" / "not" / "exist"

    assert mcp_commands._git_toplevel(missing) == missing.resolve()


@pytest.mark.parametrize(
    "error",
    [OSError("no git"), subprocess.TimeoutExpired(cmd="git", timeout=5)],
    ids=["oserror", "timeout"],
)
def test_git_toplevel_returns_the_resolved_path_when_git_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def boom(*_a: Any, **_k: Any) -> Any:
        raise error

    monkeypatch.setattr(mcp_commands.subprocess, "run", boom)

    assert mcp_commands._git_toplevel(tmp_path) == tmp_path.resolve()


def test_repair_config_repo_subdirectory_repairs_the_checkout_root(
    repos: SimpleNamespace, target_subdir: Path
) -> None:
    (repos.target / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    result = CliRunner().invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(target_subdir), "--dry-run", "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["repo"] == str(repos.target)
    assert data["inputs"]["mcp_json_path"] == str(repos.target / ".mcp.json")
    assert data["inputs"]["catalog_paths"] == [
        str(repos.target / mcp_commands.CATALOG_FILENAME)
    ]


def test_identity_view_already_normalizes_a_subdirectory(
    repos: SimpleNamespace, target_subdir: Path
) -> None:
    # Survey fact for lifecycle/switch-project: `run_lifecycle` and `switch-project`
    # take their worktree root from the identity view, which resolves the git
    # toplevel of any directory inside the checkout.
    from dopemux.mcp.runtime_state import resolve_identity_view

    assert resolve_identity_view(target_subdir).worktree_root == str(repos.target)
