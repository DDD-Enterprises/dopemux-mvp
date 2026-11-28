"""Per-root idle retention with actual detach receipts and synthetic reap effects."""

from __future__ import annotations

import contextlib
import os
import subprocess
from pathlib import Path

import pytest

from dopemux.mcp import reap
from dopemux.mcp.docker_inspect import DockerContainerInfo
from dopemux.mcp.lifecycle import runtime_dir_for
from dopemux.mcp.runtime_registry import RuntimeRegistry, build_instance_record
from dopemux.mcp.runtime_state import resolve_identity_view


@pytest.fixture
def instances(tmp_path, monkeypatch):
    registry_path = tmp_path / "runtime" / "instances.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(registry_path))
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "leases.json"))
    registry = RuntimeRegistry.load(registry_path, create_missing=True)
    result = []
    for name in ("retained", "unrelated"):
        root = tmp_path / name
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        identity = resolve_identity_view(root)
        runtime = runtime_dir_for(identity)
        record = reap.attach(runtime)
        assert record.name == str(os.getpid())
        reap.detach(record)
        container = DockerContainerInfo(
            id=name,
            name=name,
            labels={
                "dopemux.managed": "true",
                "dopemux.project_id": identity.project_id,
                "dopemux.worktree_hash": identity.worktree_hash,
                "dopemux.service": "conport",
                "dopemux.scope": "worktree",
            },
        )
        registry.upsert_instance(
            build_instance_record(
                instance_id=name,
                project_id=identity.project_id,
                workspace_id=str(root),
                project_root=str(root),
                worktree_root=str(root),
                worktree_hash=identity.worktree_hash,
                project_hash=identity.project_hash,
                service="conport",
                scope="worktree",
                status="running",
                ports={},
                urls={},
                container_names=[name],
                compose_project_name=name,
                labels=container.labels,
            )
        )
        result.append((root, runtime, container))
    registry.save()
    now = (
        max(runtime.joinpath("last_detach").stat().st_mtime for _, runtime, _ in result)
        + 1300
    )
    return registry, result, now


def _plan(instances):
    registry, rows, now = instances
    return reap.plan_reap(
        registry=registry, containers=[row[2] for row in rows], now=now
    )


def test_actual_detach_then_idle_retention_is_target_local(instances):
    root, _, _ = instances[1][0]
    (root / ".envrc.dopemux-mcp").write_text("export DOPEMUX_MCP_RETAIN_IDLE=true\n")
    candidates = _plan(instances)
    assert [c.worktree_root for c in candidates] == [str(instances[1][1][0])]


@pytest.mark.parametrize("replacement", [None, "false"])
def test_retention_removal_or_false_restores_default_idle_reap(instances, replacement):
    root = instances[1][0][0]
    path = root / ".envrc.dopemux-mcp"
    path.write_text("DOPEMUX_MCP_RETAIN_IDLE=true\n")
    assert len(_plan(instances)) == 1
    if replacement is None:
        path.unlink()
    else:
        path.write_text(f"DOPEMUX_MCP_RETAIN_IDLE={replacement}\n")
    assert len(_plan(instances)) == 2


@pytest.mark.parametrize(
    "body",
    [
        "DOPEMUX_MCP_RETAIN_IDLE=yes\n",
        "DOPEMUX_MCP_RETAIN_IDLE=true\nDOPEMUX_MCP_RETAIN_IDLE=false\n",
        "DOPEMUX_MCP_RETAIN_IDLE=$(touch sentinel)\n",
        "eval 'export DOPEMUX_MCP_RETAIN_IDLE=true'\n",
        'export "$DOPEMUX_MCP_RETAIN_IDLE"=true\n',
        'OTHER="DOPEMUX_MCP_RETAIN_IDLE=true"; eval "$OTHER"\n',
        'export X="a # b"; export DOPEMUX_MCP_RETAIN_IDLE=false\n',
    ],
)
def test_invalid_or_ambiguous_retention_holds_idle_work(instances, body):
    root = instances[1][0][0]
    (root / ".envrc.dopemux-mcp").write_text(body)
    assert [c.worktree_root for c in _plan(instances)] == [str(instances[1][1][0])]
    assert not (root / "sentinel").exists()


def test_missing_worktree_cleanup_is_not_suppressed(instances):
    root = instances[1][0][0]
    (root / ".envrc.dopemux-mcp").write_text("DOPEMUX_MCP_RETAIN_IDLE=true\n")
    root.rename(root.with_name("moved"))
    candidate = next(c for c in _plan(instances) if c.worktree_root == str(root))
    assert candidate.reason == "worktree_missing"


@pytest.mark.parametrize(
    "policy,reason",
    [("true", "retained_idle"), ("private-value", "idle_retention_invalid")],
)
def test_apply_rechecks_retention_under_existing_instance_lock(
    instances, monkeypatch, policy, reason
):
    registry, rows, now = instances
    candidate = next(c for c in _plan(instances) if c.worktree_root == str(rows[0][0]))
    original = reap.instance_lock

    @contextlib.contextmanager
    def lock(path, **kwargs):
        with original(path, **kwargs):
            (rows[0][0] / ".envrc.dopemux-mcp").write_text(
                f"DOPEMUX_MCP_RETAIN_IDLE={policy}\n"
            )
            yield

    monkeypatch.setattr(reap, "instance_lock", lock)
    calls = []

    def runner(cmd, **kwargs):
        calls.append(cmd)
        raise AssertionError(
            "retained candidate must stop before Docker or state effects"
        )

    before = registry.path.read_bytes()
    report = reap.apply_reap(
        [candidate],
        runner=runner,
        registry_path=registry.path,
        lease_path=Path(os.environ["DOPEMUX_MCP_PORT_LEASE_REGISTRY"]),
        now=lambda: now,
    )
    assert report.skip_reasons == [reason]
    assert not calls and registry.path.read_bytes() == before


def test_unreadable_policy_holds_idle_but_not_missing_cleanup(instances, monkeypatch):
    root = instances[1][0][0]
    path = root / ".envrc.dopemux-mcp"
    path.write_text("DOPEMUX_MCP_RETAIN_IDLE=true\n")
    original = Path.open

    def denied(self, *args, **kwargs):
        if self == path:
            raise PermissionError("private-policy-content")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied)
    assert len(_plan(instances)) == 1
    root.rename(root.with_name("moved"))
    assert (
        next(c for c in _plan(instances) if c.worktree_root == str(root)).reason
        == "worktree_missing"
    )


def test_selected_policy_ignores_unrelated_values_and_ambient_identity(
    instances, monkeypatch
):
    root = instances[1][0][0]
    (root / ".envrc.dopemux-mcp").write_text(
        'UNRELATED="DOPEMUX_MCP_RETAIN_IDLE=true"\n'
        "# DOPEMUX_MCP_RETAIN_IDLE=false\n"
        "export DOPEMUX_MCP_RETAIN_IDLE='true' # valid policy\n"
    )
    monkeypatch.setenv("DOPEMUX_PROJECT_ROOT", str(instances[1][1][0]))
    monkeypatch.setenv("GIT_DIR", str(instances[1][1][0] / ".git"))
    assert len(_plan(instances)) == 1


def test_retention_does_not_inherit_a_nested_git_root(instances):
    from dopemux.mcp.idle_retention import idle_retention

    root = instances[1][0][0]
    nested = root / "nested"
    nested.mkdir()
    (nested / ".envrc.dopemux-mcp").write_text("DOPEMUX_MCP_RETAIN_IDLE=true\n")
    decision = idle_retention(nested)
    assert decision.hold_idle and decision.reason == "idle_retention_unbound"
