"""Reap-only cleanup of idle or removed worktree sidecars (design D8, P-09).

A launcher writes ``<runtime_dir>/attached/<pid>`` while it is connected and
``<runtime_dir>/last_detach`` when it leaves. An instance, the
``(dopemux.project_id, dopemux.worktree_hash)`` pair, is reaped when it has zero
live attachments AND (its worktree path no longer exists OR it has been idle at
least ``idle_s`` since the last detach). Reaping stops and removes the instance's
containers by container id, releases its port leases, marks its registry entries
stopped and removes its runtime dir.

Safety rules (all fail closed):

* Containers are joined to an instance by labels ``dopemux.managed=true``,
  ``dopemux.project_id``, ``dopemux.worktree_hash`` and ``dopemux.scope=worktree``
  plus a runtime-registry entry for that pair. Anything else is never touched;
  ``project`` and ``singleton`` scope (the task-orchestrator, host singletons)
  are never reaped.
* "Idle" needs a ``last_detach`` file. A runtime dir without one has an unknown
  idle time and only the ``worktree_missing`` reason can select it.
* Containers are stopped and removed by id, never through ``docker compose`` and
  never with ``rm -f``. A container that fails to stop keeps its leases, registry
  entries and runtime dir.
* Automatic reaping (:func:`maybe_reap`: hooks and launcher) honours a kill switch:
  the file ``<runtime root>/reap.disabled`` or ``DOPEMUX_MCP_REAP`` set to
  ``0``/``off``/``false``. The explicit CLI ``dopemux mcp reap --apply`` ignores it.

Lock order: ``instance_lock(runtime_dir)`` outside, ``registry_lock`` inside
(through ``locked_reload_and_save``). Never a daemon.
"""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Tuple

from . import docker_runtime as dr
from .docker_inspect import DockerContainerInfo, inspect_all_managed_containers
from .docker_runtime import run_cmd
from .locks import _runtime_dir, instance_lock, locked_reload_and_save
from .port_leases import PortLeaseRegistry, default_lease_registry_path
from .runtime_registry import REGISTRY_ENV, RuntimeRegistry, default_registry_path

__all__ = [
    "DISABLE_ENV",
    "DISABLE_FILENAME",
    "ReapCandidate",
    "ReapReport",
    "apply_reap",
    "attach",
    "detach",
    "live_attachments",
    "maybe_reap",
    "plan_reap",
    "reaping_disabled_reason",
    "save_state_locked",
    "runtime_registry_path",
]

ATTACHED_DIR = "attached"
LAST_DETACH = "last_detach"
DISABLE_FILENAME = "reap.disabled"
DISABLE_ENV = "DOPEMUX_MCP_REAP"
STATE_FILENAME = "reap.last"
_OFF_VALUES = {"0", "off", "false"}
_REAPABLE_SCOPE = "worktree"
_HOOK_DOCKER_TIMEOUT_S = 10.0  # hooks must not stall a turn on a hung docker
_SAFE_HASH = re.compile(r"[A-Za-z0-9_-]{1,64}")

Reason = Literal["worktree_missing", "idle"]


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- attachments ------------------------------------------------------------------


def attach(runtime_dir: Path) -> Path:
    """Write ``<runtime_dir>/attached/<pid>`` (ISO-8601 UTC timestamp) for this launcher."""
    record = Path(runtime_dir) / ATTACHED_DIR / str(os.getpid())
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(f"{_utc_stamp()}\n", encoding="utf-8")
    return record


def detach(path: Path) -> None:
    """Remove an attach record and stamp ``last_detach`` in the runtime dir.

    An already-removed record is fine. A runtime dir that was reaped meanwhile is
    not recreated.
    """
    record = Path(path)
    with contextlib.suppress(FileNotFoundError):
        record.unlink()
    runtime_dir = record.parent.parent
    if not runtime_dir.is_dir():
        return
    tmp = runtime_dir / f".{LAST_DETACH}.{os.getpid()}.tmp"
    try:
        tmp.write_text(f"{_utc_stamp()}\n", encoding="utf-8")
        os.replace(tmp, runtime_dir / LAST_DETACH)
    except OSError:
        with contextlib.suppress(OSError):
            tmp.unlink()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return True  # unknown: fail closed
    return True


def live_attachments(runtime_dir: Path, *, prune: bool = True) -> int:
    """Number of attach records whose pid is alive.

    The pid is the file name (older records hold the pid as content, newer ones a
    timestamp; both work). Records of dead pids are removed when ``prune`` is true;
    planning passes ``prune=False`` so a dry run never changes anything. An
    unreadable ``attached`` dir counts as attached.
    """
    attached = Path(runtime_dir) / ATTACHED_DIR
    try:
        entries = list(attached.iterdir())
    except FileNotFoundError:
        return 0
    except OSError:
        return 1
    live = 0
    for entry in entries:
        name = entry.name
        if not name.isdigit() or int(name) <= 0:
            continue
        if _pid_alive(int(name)):
            live += 1
        elif prune:
            with contextlib.suppress(OSError):
                entry.unlink()
    return live


# --- kill switch and paths --------------------------------------------------------


def runtime_registry_path() -> Path:
    """The runtime registry, redirected like the lock files under pytest."""
    if os.environ.get(REGISTRY_ENV):
        return default_registry_path()
    return _runtime_dir() / "instances.json"


def reaping_disabled_reason() -> Optional[str]:
    """Why automatic reaping is switched off, or ``None`` when it is allowed."""
    raw = os.environ.get(DISABLE_ENV)
    if raw is not None and raw.strip().lower() in _OFF_VALUES:
        return f"{DISABLE_ENV}={raw.strip()}"
    marker = _runtime_dir() / DISABLE_FILENAME
    try:
        if marker.exists():
            return f"{marker} exists"
    except OSError as exc:
        return f"{marker} unreadable ({exc})"
    return None


# --- plan -------------------------------------------------------------------------


@dataclass
class ReapCandidate:
    project_id: str
    worktree_hash: str
    worktree_root: str
    runtime_dir: Path
    container_ids: List[str] = field(default_factory=list)
    reason: Reason = "worktree_missing"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "worktree_hash": self.worktree_hash,
            "worktree_root": self.worktree_root,
            "runtime_dir": str(self.runtime_dir),
            "container_ids": list(self.container_ids),
            "reason": self.reason,
        }


@dataclass
class ReapReport:
    reaped: List[ReapCandidate] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    skipped: List[ReapCandidate] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reaped": [c.to_dict() for c in self.reaped],
            "skipped": [c.to_dict() for c in self.skipped],
            "errors": list(self.errors),
        }


def _worktree_gone(root: str, exists: Callable[[Path], bool]) -> bool:
    try:
        return not exists(Path(root))
    except Exception:  # noqa: BLE001 - unreadable means unknown, never "missing"
        return False


def _entry_for(
    registry: RuntimeRegistry, project_id: str, worktree_hash: str
) -> Optional[Tuple[str, str]]:
    """``(worktree_root, project_root)`` of the pair's registry entry, or None."""
    roots = set()
    project_root = ""
    for inst in registry.instances():
        if (
            inst.get("project_id") == project_id
            and inst.get("worktree_hash") == worktree_hash
            and inst.get("scope") == _REAPABLE_SCOPE
            and inst.get("worktree_root")
        ):
            roots.add(str(inst["worktree_root"]))
            project_root = str(inst.get("project_root") or inst["worktree_root"])
    if len(roots) != 1:
        return None
    return next(iter(roots)), project_root


def _last_detach_age(runtime_dir: Path, now: float) -> Optional[float]:
    try:
        return now - (runtime_dir / LAST_DETACH).stat().st_mtime
    except OSError:
        return None


def plan_reap(
    *,
    registry: RuntimeRegistry,
    containers: Sequence[DockerContainerInfo],
    now: float,
    idle_s: float = 1200,
    exists: Callable[[Path], bool] = Path.exists,
) -> List[ReapCandidate]:
    """Instances to reap. Read-only; an unreadable registry yields ``[]``."""
    if registry.parse_status != "OK":
        return []

    groups: Dict[Tuple[str, str], List[str]] = {}
    for c in containers:
        labels = c.labels or {}
        project_id = labels.get("dopemux.project_id") or ""
        worktree_hash = labels.get("dopemux.worktree_hash") or ""
        if (
            labels.get(dr.LABEL_MANAGED) != "true"
            or labels.get("dopemux.scope") != _REAPABLE_SCOPE
            or not project_id
            or not _SAFE_HASH.fullmatch(worktree_hash)
            or not c.id
        ):
            continue
        groups.setdefault((project_id, worktree_hash), []).append(c.id)

    candidates: List[ReapCandidate] = []
    for (project_id, worktree_hash), ids in groups.items():
        entry = _entry_for(registry, project_id, worktree_hash)
        if entry is None:
            continue
        worktree_root, project_root = entry
        slug = dr.project_slug(Path(project_root).name)
        runtime_dir = registry.path.parent / f"{slug}-{worktree_hash}"
        if live_attachments(runtime_dir, prune=False) > 0:
            continue
        reason: Optional[Reason] = None
        if _worktree_gone(worktree_root, exists):
            reason = "worktree_missing"
        else:
            age = _last_detach_age(runtime_dir, now)
            if age is not None and age >= idle_s:
                reason = "idle"
        if reason is None:
            continue
        candidates.append(
            ReapCandidate(
                project_id=project_id,
                worktree_hash=worktree_hash,
                worktree_root=worktree_root,
                runtime_dir=runtime_dir,
                container_ids=sorted(ids),
                reason=reason,
            )
        )
    return candidates


# --- apply ------------------------------------------------------------------------


def _release_leases(reg: PortLeaseRegistry, cand: ReapCandidate) -> None:
    root = cand.worktree_root.rstrip("/")
    for lease in reg.leases():
        if lease.get("status") != "active":
            continue
        if str(lease.get("worktree_root") or "").rstrip("/") != root:
            continue
        if (lease.get("scope") or _REAPABLE_SCOPE) != _REAPABLE_SCOPE:
            continue
        if lease.get("project_id") and lease["project_id"] != cand.project_id:
            continue
        if lease.get("lease_id"):
            reg.mark_released(lease_id=lease["lease_id"])
        elif lease.get("service"):
            reg.mark_released(service=lease["service"], worktree_root=cand.worktree_root)


def _mark_instances_stopped(reg: RuntimeRegistry, cand: ReapCandidate) -> None:
    services = sorted(
        {
            str(inst["service"])
            for inst in reg.instances()
            if inst.get("project_id") == cand.project_id
            and inst.get("worktree_hash") == cand.worktree_hash
            and inst.get("scope") == _REAPABLE_SCOPE
            and inst.get("service")
        }
    )
    for service in services:
        reg.mark_stopped(
            project_id=cand.project_id, service=service, worktree_root=cand.worktree_root
        )


def save_state_locked(
    registry_cls: Any, path: Path, mutate: Callable[[Any], Any]
) -> Optional[str]:
    """Locked reload-mutate-save; never replaces a corrupt file. Returns an error or None."""
    if not path.exists():
        return None
    if registry_cls.load(path).parse_status == "ERROR":
        return f"{path} is unreadable; left as is"
    try:
        fresh = locked_reload_and_save(registry_cls, path, mutate)
    except Exception as exc:  # noqa: BLE001
        return f"{path}: {exc}"
    if getattr(fresh, "recovered_from_corrupt", False):
        return f"{path} became unreadable during the update"
    return None


def _runtime_dir_is_ours(cand: ReapCandidate, registry_path: Path) -> bool:
    rt = Path(cand.runtime_dir)
    return (
        bool(_SAFE_HASH.fullmatch(cand.worktree_hash))
        and rt.name.endswith(f"-{cand.worktree_hash}")
        and rt.parent.resolve() == registry_path.parent.resolve()
    )


def _stop_and_remove(cand: ReapCandidate, runner: Callable[..., Any]) -> List[str]:
    errors: List[str] = []
    for cid in cand.container_ids:
        stop = runner(["docker", "stop", cid])
        if stop.exit_code != 0:
            errors.append(f"{cid}: docker stop failed ({stop.exit_code}): {stop.stderr.strip()[:200]}")
            continue  # never remove (let alone force-remove) what did not stop
        rm = runner(["docker", "rm", cid])
        if rm.exit_code != 0:
            errors.append(f"{cid}: docker rm failed ({rm.exit_code}): {rm.stderr.strip()[:200]}")
    return errors


def _reap_one(
    cand: ReapCandidate,
    runner: Callable[..., Any],
    lease_path: Path,
    registry_path: Path,
    report: ReapReport,
) -> None:
    label = f"{cand.project_id}/{cand.worktree_hash}"
    if not _runtime_dir_is_ours(cand, registry_path):
        report.errors.append(f"{label}: runtime dir {cand.runtime_dir} is outside {registry_path.parent}")
        return
    with instance_lock(cand.runtime_dir):
        if live_attachments(cand.runtime_dir) > 0:
            report.skipped.append(cand)
            return
        docker_errors = _stop_and_remove(cand, runner)
        if docker_errors:
            report.errors.extend(f"{label}: {e}" for e in docker_errors)
            return  # containers may still run: keep leases, registry entries and dir
        for cls, path, mutate in (
            (PortLeaseRegistry, lease_path, lambda reg: _release_leases(reg, cand)),
            (RuntimeRegistry, registry_path, lambda reg: _mark_instances_stopped(reg, cand)),
        ):
            error = save_state_locked(cls, path, mutate)
            if error:
                report.errors.append(f"{label}: {error}")
        try:
            shutil.rmtree(cand.runtime_dir)
        except FileNotFoundError:
            pass
        except OSError as exc:
            report.errors.append(f"{label}: could not remove {cand.runtime_dir}: {exc}")
            return
        report.reaped.append(cand)


def apply_reap(
    candidates: Sequence[ReapCandidate],
    *,
    runner: Callable[..., Any] = run_cmd,
    lease_path: Optional[Path] = None,
    registry_path: Optional[Path] = None,
) -> ReapReport:
    """Reap each candidate under its instance lock; failures are recorded, never raised."""
    leases = Path(lease_path) if lease_path is not None else default_lease_registry_path()
    registry = Path(registry_path) if registry_path is not None else runtime_registry_path()
    report = ReapReport()
    for cand in candidates:
        try:
            _reap_one(cand, runner, leases, registry, report)
        except Exception as exc:  # noqa: BLE001 - one bad candidate must not stop the rest
            report.errors.append(f"{cand.project_id}/{cand.worktree_hash}: {exc}")
    return report


# --- automatic entry point --------------------------------------------------------


def maybe_reap(
    *,
    throttle_s: float = 600,
    state_file: Optional[Path] = None,
    now: Callable[[], float] = time.time,
    idle_s: float = 1200,
    inspector: Optional[Callable[..., Any]] = None,
    runner: Optional[Callable[..., Any]] = None,
) -> Optional[ReapReport]:
    """Throttled plan-and-apply for hooks and launchers; ``None`` when it did not run.

    Does nothing when automatic reaping is disabled (see module docstring) or when
    ``state_file`` (default ``<runtime root>/reap.last``) was touched within
    ``throttle_s`` seconds. Docker is only asked when the runtime registry holds
    instances; an unreachable docker reaps nothing.
    """
    if reaping_disabled_reason() is not None:
        return None
    state = Path(state_file) if state_file is not None else _runtime_dir() / STATE_FILENAME
    current = now()
    if throttle_s > 0:
        try:
            if current - state.stat().st_mtime < throttle_s:
                return None
        except OSError:
            pass
    with contextlib.suppress(OSError):
        state.parent.mkdir(parents=True, exist_ok=True)
        state.touch()
        os.utime(state, (current, current))

    report = ReapReport()
    registry = RuntimeRegistry.load(runtime_registry_path())
    if registry.parse_status == "ERROR":
        report.errors.append(f"{registry.path}: unreadable ({registry.error})")
        return report
    if not registry.instances():
        return report
    docker = inspector() if inspector else inspect_all_managed_containers(timeout=_HOOK_DOCKER_TIMEOUT_S)
    if not docker.available:
        report.errors.append(f"docker unavailable: {docker.error}")
        return report
    candidates = plan_reap(
        registry=registry, containers=docker.containers, now=current, idle_s=idle_s
    )
    if not candidates:
        return report
    return apply_reap(candidates, runner=runner or run_cmd)
