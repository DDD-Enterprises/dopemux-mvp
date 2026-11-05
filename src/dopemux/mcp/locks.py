"""Advisory file locks for MCP lifecycle state.

Every lock is an exclusive ``fcntl.flock`` on a small file, released when the
context manager exits (including on exceptions). Lock files live beside the
state they guard, so a test that points ``DOPEMUX_MCP_RUNTIME_REGISTRY`` at a
tmp dir never touches ``~/.dopemux``.

Lock order when nested (never the reverse):

* ``instance_lock``      outside ``registry_lock``
* ``reserved_port_lock`` outside ``registry_lock``

``flock`` is per open file description, so taking ``registry_lock`` again in
the same process while already holding it deadlocks. Never nest it with
``locked_reload_and_save``, which takes it itself.
"""

from __future__ import annotations

import fcntl
import importlib
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, ContextManager, Iterator, Type, TypeVar

from .runtime_registry import default_registry_path

R = TypeVar("R")

_DIR_MODE = 0o700
_FILE_MODE = 0o600


def _mkdir_private(directory: Path) -> None:
    """Create ``directory`` and any missing parents with mode 0700."""
    missing = []
    cur = directory
    while not cur.exists():
        missing.append(cur)
        if cur.parent == cur:
            break
        cur = cur.parent
    for d in reversed(missing):
        try:
            os.mkdir(d, _DIR_MODE)
        except FileExistsError:
            continue
        os.chmod(d, _DIR_MODE)  # defeat a restrictive/odd umask


@contextmanager
def _flock(path: Path) -> Iterator[None]:
    _mkdir_private(path.parent)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, _FILE_MODE)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _runtime_dir() -> Path:
    return default_registry_path().parent


def registry_lock() -> ContextManager[None]:
    """Guard read-modify-write of the runtime and lease registries."""
    return _flock(_runtime_dir() / "registry.lock")


def reserved_port_lock(port: int) -> ContextManager[None]:
    """Serialize starts that contend for one reserved singleton port."""
    return _flock(_runtime_dir() / f"reserved-{int(port)}.lock")


def instance_lock(runtime_dir: Path) -> ContextManager[None]:
    """Serialize launches of one worktree instance (``<runtime_dir>/launch.lock``)."""
    return _flock(Path(runtime_dir) / "launch.lock")


def provision_lock(project_id: str) -> ContextManager[None]:
    """Serialize per-project provisioning (tenants, credentials)."""
    pid = str(project_id or "")
    if pid in {"", ".", ".."} or "/" in pid or "\\" in pid or "\x00" in pid:
        raise ValueError(f"unsafe project_id for lock path: {project_id!r}")
    return _flock(_runtime_dir().parent / "projects" / pid / "provision.lock")


def _empty_registry_for(registry_cls: Type[R], path: Path) -> R:
    module = importlib.import_module(registry_cls.__module__)
    return registry_cls(  # type: ignore[call-arg]
        path=path,
        data=module.empty_registry(),
        present=True,
        parse_status="OK",
    )


def locked_reload_and_save(
    registry_cls: Type[R],
    path: Path,
    mutate: Callable[[R], Any],
) -> R:
    """Under ``registry_lock``: fresh load, ``mutate``, save; return the registry.

    A corrupt or unreadable file is replaced by an empty document and the
    returned registry carries ``recovered_from_corrupt = True``. Works for
    ``RuntimeRegistry`` and ``PortLeaseRegistry``.
    """
    reg_path = Path(path)
    with registry_lock():
        recovered = False
        try:
            fresh = registry_cls.load(reg_path, create_missing=True)  # type: ignore[attr-defined]
            if getattr(fresh, "parse_status", "OK") == "ERROR":
                recovered = True
        except Exception:  # noqa: BLE001 - any load failure means start from empty
            recovered = True
        if recovered:
            fresh = _empty_registry_for(registry_cls, reg_path)
        fresh.recovered_from_corrupt = recovered  # type: ignore[attr-defined]
        mutate(fresh)
        fresh.save()  # type: ignore[attr-defined]
        return fresh
