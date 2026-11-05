"""Tests for MCP lock primitives and reload-under-lock persistence."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Dict, List

import pytest

from dopemux.mcp import locks
from dopemux.mcp.port_leases import PortLeaseRegistry
from dopemux.mcp.runtime_registry import RuntimeRegistry

HOLD_SECS = 0.3


def _child_env(reg: Path, leases: Path) -> Dict[str, str]:
    env = dict(os.environ)
    env["DOPEMUX_MCP_RUNTIME_REGISTRY"] = str(reg)
    env["DOPEMUX_MCP_PORT_LEASE_REGISTRY"] = str(leases)
    return env


def _spawn(code: str, reg: Path, leases: Path, *args: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", textwrap.dedent(code), *args],
        env=_child_env(reg, leases),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _finish(procs: List[subprocess.Popen]) -> List[str]:
    outs = []
    for p in procs:
        out, err = p.communicate(timeout=60)
        assert p.returncode == 0, err
        outs.append(out)
    return outs


HOLD_CODE = """
import sys, time
from dopemux.mcp.locks import registry_lock
with registry_lock():
    t0 = time.time()
    time.sleep(%s)
    t1 = time.time()
print(t0, t1)
""" % HOLD_SECS


def test_registry_lock_is_exclusive_across_processes(tmp_path: Path):
    reg = tmp_path / "rt" / "instances.json"
    leases = tmp_path / "rt" / "port-leases.json"
    started = time.time()
    procs = [_spawn(HOLD_CODE, reg, leases) for _ in range(2)]
    outs = _finish(procs)
    wall = time.time() - started

    spans = sorted(tuple(float(x) for x in out.split()) for out in outs)
    # Critical sections never overlap, and the second only starts after the first ends.
    assert spans[1][0] >= spans[0][1]
    assert wall > HOLD_SECS


UPSERT_CODE = """
import sys
from pathlib import Path
from dopemux.mcp.locks import locked_reload_and_save
from dopemux.mcp.runtime_registry import RuntimeRegistry

path = Path(sys.argv[1]); iid = sys.argv[2]
import time
def mutate(reg):
    time.sleep(%s)
    reg.upsert_instance({"instance_id": iid, "service": iid})
locked_reload_and_save(RuntimeRegistry, path, mutate)
""" % HOLD_SECS


def test_locked_reload_and_save_merges_concurrent_upserts(tmp_path: Path):
    reg = tmp_path / "rt" / "instances.json"
    leases = tmp_path / "rt" / "port-leases.json"
    procs = [_spawn(UPSERT_CODE, reg, leases, str(reg), iid) for iid in ("inst-a", "inst-b")]
    _finish(procs)

    data = json.loads(reg.read_text())
    ids = {i["instance_id"] for i in data["instances"]}
    assert ids == {"inst-a", "inst-b"}


def test_locked_reload_tolerates_corrupt_registry(tmp_path: Path, monkeypatch):
    reg = tmp_path / "rt" / "instances.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    reg.parent.mkdir(parents=True)
    reg.write_text("{")

    fresh = locks.locked_reload_and_save(
        RuntimeRegistry,
        reg,
        lambda r: r.upsert_instance({"instance_id": "inst-1", "service": "conport"}),
    )

    assert fresh.recovered_from_corrupt is True
    data = json.loads(reg.read_text())
    assert [i["instance_id"] for i in data["instances"]] == ["inst-1"]
    assert RuntimeRegistry.load(reg).parse_status == "OK"


def test_locked_reload_works_for_lease_registry(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json"))
    leases = tmp_path / "rt" / "port-leases.json"
    leases.parent.mkdir(parents=True)
    leases.write_text("not json")

    fresh = locks.locked_reload_and_save(
        PortLeaseRegistry,
        leases,
        lambda r: r.data.setdefault("leases", []).append({"lease_id": "l1", "status": "active"}),
    )

    assert fresh.recovered_from_corrupt is True
    assert [x["lease_id"] for x in json.loads(leases.read_text())["leases"]] == ["l1"]


def test_locked_reload_clean_registry_is_not_flagged(tmp_path: Path, monkeypatch):
    reg = tmp_path / "rt" / "instances.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    fresh = locks.locked_reload_and_save(RuntimeRegistry, reg, lambda r: None)
    assert fresh.recovered_from_corrupt is False
    assert reg.exists()


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_lock_files_created_0700_parents(tmp_path: Path, monkeypatch):
    reg = tmp_path / "a" / "b" / "instances.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))

    with locks.registry_lock():
        pass
    assert (tmp_path / "a" / "b" / "registry.lock").exists()
    assert _mode(tmp_path / "a") == 0o700
    assert _mode(tmp_path / "a" / "b") == 0o700

    with locks.reserved_port_lock(7890):
        pass
    assert (tmp_path / "a" / "b" / "reserved-7890.lock").exists()

    runtime_dir = tmp_path / "x" / "y" / "proj-abcd"
    with locks.instance_lock(runtime_dir):
        pass
    assert (runtime_dir / "launch.lock").exists()
    assert _mode(tmp_path / "x") == 0o700
    assert _mode(tmp_path / "x" / "y") == 0o700
    assert _mode(runtime_dir) == 0o700

    with locks.provision_lock("proj-1234"):
        pass
    prov = tmp_path / "a" / "projects" / "proj-1234" / "provision.lock"
    assert prov.exists()
    assert _mode(prov.parent) == 0o700
    assert _mode(prov.parent.parent) == 0o700


def test_lock_released_on_exception(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json"))
    with pytest.raises(RuntimeError):
        with locks.registry_lock():
            raise RuntimeError("boom")
    # Re-acquire from a second fd in the same process would deadlock if still held;
    # a non-blocking probe proves release.
    import fcntl

    fd = os.open(str(tmp_path / "rt" / "registry.lock"), os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(fd)


@pytest.mark.parametrize("bad", ["", ".", "..", "a/b", "a\\b"])
def test_provision_lock_rejects_unsafe_project_id(bad: str, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json"))
    with pytest.raises(ValueError):
        with locks.provision_lock(bad):
            pass


def test_registry_lock_follows_explicit_registry_path(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_RUNTIME_REGISTRY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    reg = tmp_path / "elsewhere" / "instances.json"

    with locks.registry_lock(reg):
        pass

    assert (reg.parent / "registry.lock").exists()
    assert not (tmp_path / "home" / ".dopemux").exists()


def test_locked_reload_lock_follows_path_argument(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_RUNTIME_REGISTRY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    reg = tmp_path / "elsewhere" / "instances.json"

    locks.locked_reload_and_save(RuntimeRegistry, reg, lambda r: None)

    assert (reg.parent / "registry.lock").exists()
    assert not (tmp_path / "home" / ".dopemux").exists()


def test_pytest_guard_never_resolves_home_lock_dir(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_RUNTIME_REGISTRY", raising=False)
    monkeypatch.delenv("DOPEMUX_ALLOW_HOME_LEASE_REGISTRY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    with locks.registry_lock():
        pass
    with locks.reserved_port_lock(7890):
        pass
    with locks.provision_lock("proj-guard"):
        pass

    assert not (tmp_path / "home" / ".dopemux").exists()
    assert not str(locks._runtime_dir()).startswith(str(tmp_path / "home"))


def test_reserved_port_lock_reentrant_in_thread_exclusive_across_threads(
    tmp_path: Path, monkeypatch
):
    import fcntl
    import threading

    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json"))
    lock_file = tmp_path / "rt" / "reserved-7890.lock"
    other_thread_got_it = threading.Event()

    def contend() -> None:
        with locks.reserved_port_lock(7890):
            other_thread_got_it.set()

    with locks.reserved_port_lock(7890):
        with locks.reserved_port_lock(7890):  # the lifecycle preflight under the launcher
            pass
        contender = threading.Thread(target=contend)
        contender.start()
        assert not other_thread_got_it.wait(HOLD_SECS)  # still held after the inner exit
    contender.join(timeout=10)
    assert other_thread_got_it.is_set()

    fd = os.open(str(lock_file), os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # fully released
    finally:
        os.close(fd)
