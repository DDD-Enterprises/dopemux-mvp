"""Advisory file locks for MCP lifecycle state.

Every lock is an exclusive ``fcntl.flock`` on a small file, released when the
context manager exits (including on exceptions). Lock files live beside the
state they guard, so a test that points ``DOPEMUX_MCP_RUNTIME_REGISTRY`` at a
tmp dir never touches ``~/.dopemux``.

Lock order when nested (never the reverse):

* ``instance_lock``      outside ``registry_lock``
* ``reserved_port_lock`` outside ``registry_lock``
* ``instance_lock``      outside ``provision_lock`` (a launcher start provisions
  the ConPort tenant inside its instance lock; ``provision_lock`` never wraps
  another lock)

``flock`` is per open file description, so taking ``registry_lock`` again in
the same process while already holding it deadlocks. Never nest it with
``locked_reload_and_save``, which takes it itself.

``reserved_port_lock`` is the one exception: it is re-entrant within a thread,
because the launcher and ``switch-project`` hold it around a lifecycle start
whose own orchestrator preflight takes it again. Other threads and processes
still wait for it.
"""

from __future__ import annotations

import fcntl
import getpass
import hashlib
import importlib
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, ContextManager, Iterator, Optional, Type, TypeVar

from .runtime_registry import REGISTRY_ENV, default_registry_path

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


_LOCK_ATTEMPTS = 50
_LOCK_RETRY_SLEEP_S = 0.005


@contextmanager
def _flock(path: Path) -> Iterator[None]:
    """Exclusive ``flock`` on ``path`` that never holds an orphaned inode.

    A holder may delete the lock file (reap removes a whole runtime dir while
    holding its ``launch.lock``). A waiter that acquired the old inode would then
    run alongside a newer holder of a freshly created file, so after acquiring the
    lock the path is re-checked against the open descriptor and the attempt is
    retried when the file is gone or replaced.
    """
    for _ in range(_LOCK_ATTEMPTS):
        try:
            _mkdir_private(path.parent)
            fd = os.open(str(path), os.O_RDWR | os.O_CREAT, _FILE_MODE)
        except FileNotFoundError:  # parent removed between mkdir and open
            time.sleep(_LOCK_RETRY_SLEEP_S)
            continue
        acquired = False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                held = os.fstat(fd)
                current = os.stat(path)
                acquired = (held.st_dev, held.st_ino) == (
                    current.st_dev,
                    current.st_ino,
                )
            except FileNotFoundError:
                acquired = False
            if acquired:
                try:
                    yield
                finally:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                return
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
        time.sleep(_LOCK_RETRY_SLEEP_S)
    raise OSError(f"could not acquire a stable lock on {path}")


def _runtime_dir() -> Path:
    """Directory holding the shared lock files.

    ``DOPEMUX_MCP_RUNTIME_REGISTRY`` always wins. Under pytest (without the
    allow-home escape hatch shared with the lease registry) this never resolves
    ``~/.dopemux``: it falls back to a per-uid/worker/pid/test scratch dir, so a
    test that forgets the override cannot create lock files in the real home.
    """
    if os.environ.get(REGISTRY_ENV):
        return default_registry_path().parent
    if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get(
        "DOPEMUX_ALLOW_HOME_LEASE_REGISTRY"
    ):
        uid = getpass.getuser() or str(
            os.getuid() if hasattr(os, "getuid") else "nouser"
        )
        worker = os.environ.get("PYTEST_XDIST_WORKER") or "gw0"
        node = os.environ.get("PYTEST_CURRENT_TEST") or "unknown"
        session = os.environ.get("PYTEST_XDIST_TESTRUNUID") or os.environ.get(
            "DOPEMUX_PYTEST_SESSION", "session"
        )
        digest = hashlib.sha1(f"{node}:{session}".encode("utf-8")).hexdigest()[:10]
        return (
            Path(tempfile.gettempdir())
            / "dopemux-mcp-tests"
            / uid
            / worker
            / str(os.getpid())
            / digest
            / "runtime"
        )
    return default_registry_path().parent


def registry_lock(registry_path: Optional[Path] = None) -> ContextManager[None]:
    """Guard read-modify-write of a runtime or lease registry.

    The lock file sits next to ``registry_path`` (the file actually being
    written); without it, next to the default runtime registry.
    """
    base = Path(registry_path).parent if registry_path is not None else _runtime_dir()
    return _flock(base / "registry.lock")


_held = threading.local()


@contextmanager
def _reentrant_flock(path: Path) -> Iterator[None]:
    """``_flock`` that a thread already holding ``path`` re-enters without blocking."""
    depth = getattr(_held, "depth", None)
    if depth is None:
        depth = _held.depth = {}
    key = str(path)
    if depth.get(key):
        depth[key] += 1
        try:
            yield
        finally:
            depth[key] -= 1
        return
    with _flock(path):
        depth[key] = 1
        try:
            yield
        finally:
            del depth[key]


def reserved_port_lock(port: int) -> ContextManager[None]:
    """Serialize starts that contend for one reserved singleton port (re-entrant per thread)."""
    return _reentrant_flock(_runtime_dir() / f"reserved-{int(port)}.lock")


def instance_lock(runtime_dir: Path) -> ContextManager[None]:
    """Serialize launches of one worktree instance (``<runtime_dir>/launch.lock``)."""
    return _flock(Path(runtime_dir) / "launch.lock")


def project_dir(project_id: str) -> Path:
    """Per-project state dir ``<runtime parent>/projects/<project_id>``.

    Shared by ``provision_lock`` and the ConPort tenant secrets file, with the
    same pytest guard as every other lock path (never ``~/.dopemux`` in tests).
    """
    pid = str(project_id or "")
    if pid in {"", ".", ".."} or "/" in pid or "\\" in pid or "\x00" in pid:
        raise ValueError(f"unsafe project_id for lock path: {project_id!r}")
    return _runtime_dir().parent / "projects" / pid


def provision_lock(project_id: str) -> ContextManager[None]:
    """Serialize per-project provisioning (tenants, credentials)."""
    return _flock(project_dir(project_id) / "provision.lock")


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
    with registry_lock(reg_path):
        recovered = False
        fresh: R
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


class _CorruptState(Exception):
    pass


def save_state_locked(
    registry_cls: Type[R], path: Path, mutate: Callable[[R], Any]
) -> Optional[str]:
    """``locked_reload_and_save`` that never replaces a corrupt file.

    Returns ``None`` on success (or when ``path`` does not exist: nothing to
    update) and an error string otherwise. When the fresh load is corrupt,
    ``mutate`` is not run and nothing is saved, so the unreadable file stays for a
    person to inspect.
    """
    reg_path = Path(path)
    if not reg_path.exists():
        return None

    def guarded(reg: R) -> None:
        if getattr(reg, "recovered_from_corrupt", False):
            raise _CorruptState()
        mutate(reg)

    try:
        locked_reload_and_save(registry_cls, reg_path, guarded)
    except _CorruptState:
        return f"{reg_path} is unreadable; left as is"
    except Exception as exc:  # noqa: BLE001
        return f"{reg_path}: {exc}"
    return None
