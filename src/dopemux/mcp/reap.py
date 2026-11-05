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
* Registry entries and leases are changed only for the services whose containers
  this reap stopped and removed (the ``dopemux.service`` label). The task-orchestrator
  is a ``project``-scope container, never a candidate, so it is never marked stopped.
  A pair whose worktree is gone and whose containers are already gone (a reap killed
  after ``docker rm``) is cleaned by a state-only candidate (no container ids).
* Automatic runs are bounded (candidate cap, ``docker stop --time``, command timeout).
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
from .lifecycle import runtime_dir_for_paths
from .locks import _mkdir_private, _runtime_dir, instance_lock, save_state_locked
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
    _mkdir_private(record.parent)
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
    services: List[str] = field(default_factory=list)  # dopemux.service of those containers

    @property
    def state_only(self) -> bool:
        """No container left: only leases, registry entries and the runtime dir."""
        return not self.container_ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "worktree_hash": self.worktree_hash,
            "worktree_root": self.worktree_root,
            "runtime_dir": str(self.runtime_dir),
            "container_ids": list(self.container_ids),
            "reason": self.reason,
            "services": list(self.services),
        }


@dataclass
class ReapReport:
    reaped: List[ReapCandidate] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    skipped: List[ReapCandidate] = field(default_factory=list)
    skip_reasons: List[str] = field(default_factory=list)  # parallel to ``skipped``

    def skip(self, cand: ReapCandidate, reason: str) -> None:
        """``reason``: ``attached`` (a launcher attached first), ``cap`` or ``deadline``."""
        self.skipped.append(cand)
        self.skip_reasons.append(reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reaped": [c.to_dict() for c in self.reaped],
            "skipped": [
                {**c.to_dict(), "skip_reason": r} for c, r in zip(self.skipped, self.skip_reasons)
            ],
            "errors": list(self.errors),
        }


def _worktree_gone(root: str, exists: Callable[[Path], bool]) -> bool:
    try:
        return not exists(Path(root))
    except Exception:  # noqa: BLE001 - unreadable means unknown, never "missing"
        return False


_ORCHESTRATOR = "task-orchestrator"


def _entry_for(
    registry: RuntimeRegistry, project_id: str, worktree_hash: str
) -> Optional[Tuple[str, str, List[Dict[str, Any]]]]:
    """``(worktree_root, project_root, entries)`` of the pair's worktree-scope entries."""
    roots = set()
    project_root = ""
    entries: List[Dict[str, Any]] = []
    for inst in registry.instances():
        if (
            inst.get("project_id") == project_id
            and inst.get("worktree_hash") == worktree_hash
            and inst.get("scope") == _REAPABLE_SCOPE
            and inst.get("worktree_root")
        ):
            roots.add(str(inst["worktree_root"]))
            project_root = str(inst.get("project_root") or inst["worktree_root"])
            entries.append(inst)
    if len(roots) != 1:
        return None
    return next(iter(roots)), project_root, entries


def _last_detach_age(runtime_dir: Path, now: float) -> Optional[float]:
    try:
        return now - (runtime_dir / LAST_DETACH).stat().st_mtime
    except OSError:
        return None


def _has_active_leases(
    leases: Optional[PortLeaseRegistry], worktree_root: str, project_id: str
) -> bool:
    if leases is None or leases.parse_status != "OK":
        return False
    root = worktree_root.rstrip("/")
    return any(
        str(lease.get("worktree_root") or "").rstrip("/") == root
        and (lease.get("scope") or _REAPABLE_SCOPE) == _REAPABLE_SCOPE
        and lease.get("service") != _ORCHESTRATOR
        and (not lease.get("project_id") or lease["project_id"] == project_id)
        for lease in leases.active_leases()
    )


def plan_reap(
    *,
    registry: RuntimeRegistry,
    containers: Sequence[DockerContainerInfo],
    now: float,
    idle_s: float = 1200,
    exists: Callable[[Path], bool] = Path.exists,
    lease_registry: Optional[PortLeaseRegistry] = None,
) -> List[ReapCandidate]:
    """Instances to reap. Read-only; an unreadable registry yields ``[]``.

    Besides container candidates, a registry pair whose worktree is gone and which
    has no container at all but still has unfinished state (a running entry, active
    leases or a runtime dir) yields a state-only candidate, so a reap that died
    after ``docker rm`` is finished by the next run.
    """
    if registry.parse_status != "OK":
        return []

    groups: Dict[Tuple[str, str], List[DockerContainerInfo]] = {}
    seen_pairs = set()
    for c in containers:
        labels = c.labels or {}
        project_id = labels.get("dopemux.project_id") or ""
        worktree_hash = labels.get("dopemux.worktree_hash") or ""
        if labels.get(dr.LABEL_MANAGED) == "true" and project_id and worktree_hash:
            seen_pairs.add((project_id, worktree_hash))
        if (
            labels.get(dr.LABEL_MANAGED) != "true"
            or labels.get("dopemux.scope") != _REAPABLE_SCOPE
            or not project_id
            or not _SAFE_HASH.fullmatch(worktree_hash)
            or not c.id
        ):
            continue
        groups.setdefault((project_id, worktree_hash), []).append(c)

    candidates: List[ReapCandidate] = []
    for (project_id, worktree_hash), members in groups.items():
        entry = _entry_for(registry, project_id, worktree_hash)
        if entry is None:
            continue
        worktree_root, project_root, _ = entry
        runtime_dir = runtime_dir_for_paths(
            project_root=project_root, worktree_hash=worktree_hash, registry_path=registry.path
        )
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
                container_ids=sorted(c.id for c in members),
                reason=reason,
                services=sorted(
                    {(c.labels or {}).get("dopemux.service") or "" for c in members} - {""}
                ),
            )
        )

    pairs = {
        (str(i.get("project_id") or ""), str(i.get("worktree_hash") or ""))
        for i in registry.instances()
        if i.get("scope") == _REAPABLE_SCOPE
    }
    for project_id, worktree_hash in sorted(pairs):
        if (
            not project_id
            or not _SAFE_HASH.fullmatch(worktree_hash)
            or (project_id, worktree_hash) in seen_pairs
        ):
            continue
        entry = _entry_for(registry, project_id, worktree_hash)
        if entry is None:
            continue
        worktree_root, project_root, entries = entry
        if not _worktree_gone(worktree_root, exists):
            continue
        runtime_dir = runtime_dir_for_paths(
            project_root=project_root, worktree_hash=worktree_hash, registry_path=registry.path
        )
        if live_attachments(runtime_dir, prune=False) > 0:
            continue
        unfinished = (
            any(
                e.get("status") != "stopped" and e.get("service") != _ORCHESTRATOR
                for e in entries
            )
            or _has_active_leases(lease_registry, worktree_root, project_id)
            or runtime_dir.exists()
        )
        if unfinished:
            candidates.append(
                ReapCandidate(
                    project_id=project_id,
                    worktree_hash=worktree_hash,
                    worktree_root=worktree_root,
                    runtime_dir=runtime_dir,
                    container_ids=[],
                    reason="worktree_missing",
                    services=[],
                )
            )
    return candidates


# --- apply ------------------------------------------------------------------------


def _owned_by(service: Optional[str], cand: ReapCandidate) -> bool:
    """Whether this reap is responsible for ``service`` of the candidate's pair."""
    if not service:
        return False
    if cand.state_only:
        return service != _ORCHESTRATOR  # never the reserved orchestrator
    return service in cand.services


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
        if not _owned_by(lease.get("service"), cand):
            continue
        if lease.get("lease_id"):
            reg.mark_released(lease_id=lease["lease_id"])
        else:
            reg.mark_released(service=lease["service"], worktree_root=cand.worktree_root)


def _mark_instances_stopped(reg: RuntimeRegistry, cand: ReapCandidate) -> None:
    services = sorted(
        {
            str(inst["service"])
            for inst in reg.instances()
            if inst.get("project_id") == cand.project_id
            and inst.get("worktree_hash") == cand.worktree_hash
            and inst.get("scope") == _REAPABLE_SCOPE
            and _owned_by(inst.get("service"), cand)
        }
    )
    for service in services:
        reg.mark_stopped(
            project_id=cand.project_id, service=service, worktree_root=cand.worktree_root
        )


def _runtime_dir_is_ours(cand: ReapCandidate, registry_path: Path) -> bool:
    rt = Path(cand.runtime_dir)
    return (
        bool(_SAFE_HASH.fullmatch(cand.worktree_hash))
        and rt.name.endswith(f"-{cand.worktree_hash}")
        and rt.parent.resolve() == registry_path.parent.resolve()
    )


def _already_gone(result: Any) -> bool:
    return "no such container" in (result.stderr or "").lower()


def _stop_and_remove(
    cand: ReapCandidate,
    runner: Callable[..., Any],
    *,
    stop_time_s: Optional[int],
    cmd_timeout_s: Optional[float],
    out_of_time: Callable[[], bool] = lambda: False,
) -> List[str]:
    kwargs: Dict[str, Any] = {} if cmd_timeout_s is None else {"timeout": cmd_timeout_s}
    stop_cmd = ["docker", "stop"] + ([] if stop_time_s is None else ["--time", str(stop_time_s)])
    errors: List[str] = []
    for cid in cand.container_ids:
        if out_of_time():
            errors.append(f"{cid}: deadline reached before docker call; resumes next run")
            break
        stop = runner([*stop_cmd, cid], **kwargs)
        if stop.exit_code != 0 and not _already_gone(stop):
            errors.append(f"{cid}: docker stop failed ({stop.exit_code}): {stop.stderr.strip()[:200]}")
            continue  # never remove (let alone force-remove) what did not stop
        if out_of_time():
            errors.append(f"{cid}: deadline reached before docker rm; resumes next run")
            break
        rm = runner(["docker", "rm", cid], **kwargs)
        if rm.exit_code != 0 and not _already_gone(rm):
            errors.append(f"{cid}: docker rm failed ({rm.exit_code}): {rm.stderr.strip()[:200]}")
    return errors


def _reap_one(
    cand: ReapCandidate,
    runner: Callable[..., Any],
    lease_path: Path,
    registry_path: Path,
    report: ReapReport,
    *,
    stop_time_s: Optional[int],
    cmd_timeout_s: Optional[float],
    out_of_time: Callable[[], bool] = lambda: False,
) -> None:
    label = f"{cand.project_id}/{cand.worktree_hash}"
    if not _runtime_dir_is_ours(cand, registry_path):
        report.errors.append(f"{label}: runtime dir {cand.runtime_dir} is outside {registry_path.parent}")
        return
    with instance_lock(cand.runtime_dir):
        if live_attachments(cand.runtime_dir) > 0:
            report.skip(cand, "attached")
            return
        docker_errors = _stop_and_remove(
            cand,
            runner,
            stop_time_s=stop_time_s,
            cmd_timeout_s=cmd_timeout_s,
            out_of_time=out_of_time,
        )
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
    max_candidates: Optional[int] = None,
    stop_time_s: Optional[int] = None,
    cmd_timeout_s: Optional[float] = None,
    deadline: Optional[float] = None,
    clock: Callable[[], float] = time.monotonic,
) -> ReapReport:
    """Reap each candidate under its instance lock; failures are recorded, never raised.

    ``max_candidates`` caps the work of one call, ``stop_time_s`` becomes
    ``docker stop --time N``, ``cmd_timeout_s`` is the per-command timeout and
    ``deadline`` an absolute ``clock()`` (monotonic) value: once the next docker call
    could not finish before it, the remaining candidates are reported under
    ``skipped`` (reasons ``cap`` / ``deadline``) and wait for the next run. All
    default to unbounded (the explicit CLI).
    """
    leases = Path(lease_path) if lease_path is not None else default_lease_registry_path()
    registry = Path(registry_path) if registry_path is not None else runtime_registry_path()
    report = ReapReport()
    limit = len(candidates) if max_candidates is None else max(0, max_candidates)
    reserve = cmd_timeout_s or 0.0

    def out_of_time() -> bool:
        return deadline is not None and clock() + reserve > deadline

    for index, cand in enumerate(candidates):
        if index >= limit:
            report.skip(cand, "cap")
            continue
        if out_of_time():
            report.skip(cand, "deadline")
            continue
        try:
            _reap_one(
                cand,
                runner,
                leases,
                registry,
                report,
                stop_time_s=stop_time_s,
                cmd_timeout_s=cmd_timeout_s,
                out_of_time=out_of_time,
            )
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
    max_candidates: Optional[int] = 3,
    stop_time_s: Optional[int] = 5,
    cmd_timeout_s: Optional[float] = 20.0,
    deadline_s: Optional[float] = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> Optional[ReapReport]:
    """Throttled, bounded plan-and-apply for hooks and launchers; ``None`` if it did not run.

    Does nothing when automatic reaping is disabled (see module docstring) or when
    ``state_file`` (default ``<runtime root>/reap.last``) was touched within
    ``throttle_s`` seconds. Docker is only asked when the runtime registry holds
    instances; an unreachable docker reaps nothing. Defaults suit hooks: at most 3
    candidates, ``docker stop --time 5``, 20 s per command (a launcher passes 1 / 3 /
    10 because it runs inside Claude's connect budget; SessionEnd adds a 45 s deadline).
    """
    if reaping_disabled_reason() is not None:
        return None
    deadline = None if deadline_s is None else monotonic() + deadline_s
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
        registry=registry,
        containers=docker.containers,
        now=current,
        idle_s=idle_s,
        lease_registry=PortLeaseRegistry.load(default_lease_registry_path()),
    )
    if not candidates:
        return report
    return apply_reap(
        candidates,
        runner=runner or run_cmd,
        max_candidates=max_candidates,
        stop_time_s=stop_time_s,
        cmd_timeout_s=cmd_timeout_s,
        deadline=deadline,
        clock=monotonic,
    )
