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
* Eligibility is decided twice: by ``plan_reap`` and again under the instance lock,
  after pruning dead attach records (which can stamp a newer ``last_detach``). A
  candidate that no longer has zero live attachments AND (a missing worktree OR
  ``idle_s`` since ``last_detach``) is skipped as ``stale``: no docker call, no
  state change.
* "Idle" is measured from the newer of ``last_detach`` and the newest dead attach
  record (``_effective_last_detach``). A launcher ended by SIGTERM/SIGHUP detaches
  through ``finally``; one killed outright leaves a dead attach record, which
  planning reads without changing anything, and which pruning under the lock
  replaces by a ``last_detach`` stamped with the record's mtime unless a newer one
  exists. A runtime dir with neither has an unknown idle time and only the
  ``worktree_missing`` reason can select it.
* Containers are stopped and removed by id, never through ``docker compose`` and
  never with ``rm -f``. A container that fails to stop keeps its leases, registry
  entries and runtime dir. Images are never removed: one image per service and
  Dockerfile version is shared by every worktree and project.
* Registry entries and leases are changed only for the services whose containers
  this reap stopped and removed (the ``dopemux.service`` label), service by service:
  when one service's container fails, the services whose containers are all gone
  are still released and the runtime dir stays. The task-orchestrator
  is a ``project``-scope container, never a candidate, so it is never marked stopped.
  A pair whose worktree is gone and whose containers are already gone (a reap killed
  after ``docker rm``) is cleaned by a state-only candidate (no container ids); that
  candidate also clears entries and leases with an empty service (owned by nobody).
* A runtime dir that never got a registry entry (a launch refused with
  ``LAUNCH_IMAGE_BUILDING`` before any start) is found through the launcher's
  ``instance.json`` marker: a dir-only candidate (``dir_only``, no container ids)
  once its worktree is gone, with no live attachment and no live detached build.
  Never on idle. A marker that is malformed, or that does not name exactly the dir
  holding it, is ignored; a dir without a marker is never a candidate.
* Automatic runs are bounded (candidate cap, ``docker stop --time``, command timeout,
  deadline). Under a deadline each docker call gets ``min(cmd_timeout_s, time left)``;
  a candidate is skipped (``deadline``) only once no time is left. They never wait:
  each instance lock is taken non-blocking (a busy instance is skipped, ``locked``)
  and the initial ``docker ps -a`` is bounded by ``min(cmd_timeout_s, time left)``;
  a timed-out inspection skips the whole run. The final registry/lease update
  waits for the registry lock at most ``min(time left, 2 s)``; when it stays busy
  the candidate is skipped as ``registry_busy`` with its containers already gone,
  registry, leases and runtime dir untouched, and a later run finishes it (a
  state-only candidate once the worktree is gone). A registry or lease save that
  fails (a corrupt file left as is, an ``OSError``) is skipped as ``state_error``
  the same way, on every run: the runtime dir is removed, and the candidate
  counted as reaped, only after both saves succeeded. A run that attempted no
  candidate (``deadline``/``cap``/``locked``/``stale``), or whose inspection timed
  out, leaves the ``reap.last`` throttle as it was. The explicit CLI ``--apply``
  waits for every lock.
* Automatic reaping (:func:`maybe_reap`: hooks and launcher) honours a kill switch:
  the file ``<runtime root>/reap.disabled`` or ``DOPEMUX_MCP_REAP`` set to
  ``0``/``off``/``false``. The explicit CLI ``dopemux mcp reap --apply`` ignores it.

Lock order: ``instance_lock(runtime_dir)`` outside, ``registry_lock`` inside
(through ``locked_reload_and_save``). Never a daemon.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from . import docker_runtime as dr
from .docker_inspect import DockerContainerInfo, inspect_all_managed_containers
from .docker_runtime import run_cmd
from .lifecycle import runtime_dir_for_paths
from .locks import (
    LockBusy,
    _mkdir_private,
    _runtime_dir,
    instance_lock,
    save_state_locked,
    save_states_locked,
)
from .port_leases import PortLeaseRegistry, default_lease_registry_path
from .runtime_registry import REGISTRY_ENV, RuntimeRegistry, default_registry_path

__all__ = [
    "DISABLE_ENV",
    "DISABLE_FILENAME",
    "INSTANCE_MARKER",
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
#: Written by each launcher under the instance lock: which instance owns the dir.
INSTANCE_MARKER = "instance.json"
INSTANCE_MARKER_FIELDS = (
    "project_id",
    "worktree_hash",
    "worktree_root",
    "project_root",
)
DISABLE_FILENAME = "reap.disabled"
DISABLE_ENV = "DOPEMUX_MCP_REAP"
STATE_FILENAME = "reap.last"
_OFF_VALUES = {"0", "off", "false"}
_REAPABLE_SCOPE = "worktree"
_HOOK_DOCKER_TIMEOUT_S = 10.0  # hooks must not stall a turn on a hung docker
_REGISTRY_WAIT_S = 2.0  # automatic runs wait at most this long for the registry lock
_SAFE_HASH = re.compile(r"[A-Za-z0-9_-]{1,64}")

Reason = Literal["worktree_missing", "idle"]


def _utc_stamp(at: Optional[float] = None) -> str:
    moment = (
        datetime.now(timezone.utc)
        if at is None
        else datetime.fromtimestamp(at, timezone.utc)
    )
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _is_pid_text(text: str) -> bool:
    """Whether ``text`` is a positive pid in ASCII digits (``"²".isdigit()`` is true)."""
    return text.isascii() and text.isdigit() and int(text) > 0


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


def _stamp_last_detach(runtime_dir: Path, at: float) -> None:
    """Set ``last_detach`` to ``at`` unless it already records a later detach."""
    marker = runtime_dir / LAST_DETACH
    try:
        if marker.stat().st_mtime >= at:
            return
    except FileNotFoundError:
        pass
    except OSError:
        return
    tmp = runtime_dir / f".{LAST_DETACH}.{os.getpid()}.tmp"
    try:
        tmp.write_text(f"{_utc_stamp(at)}\n", encoding="utf-8")
        os.utime(tmp, (at, at))
        os.replace(tmp, marker)
    except OSError:
        with contextlib.suppress(OSError):
            tmp.unlink()


def live_attachments(runtime_dir: Path, *, prune: bool = True) -> int:
    """Number of attach records whose pid is alive.

    The pid is the file name (older records hold the pid as content, newer ones a
    timestamp; both work). Records of dead pids are removed when ``prune`` is true,
    and the newest pruned record's mtime becomes ``last_detach`` when that file is
    absent or older (a launcher killed with SIGKILL never detached). Planning
    passes ``prune=False`` so a dry run never changes anything. An unreadable
    ``attached`` dir counts as attached.
    """
    attached = Path(runtime_dir) / ATTACHED_DIR
    try:
        entries = list(attached.iterdir())
    except FileNotFoundError:
        return 0
    except OSError:
        return 1
    live = 0
    newest_dead: Optional[float] = None
    for entry in entries:
        name = entry.name
        if not _is_pid_text(name):
            continue
        if _pid_alive(int(name)):
            live += 1
        elif prune:
            try:
                mtime = entry.stat().st_mtime
                entry.unlink()
            except OSError:
                continue
            newest_dead = mtime if newest_dead is None else max(newest_dead, mtime)
    if newest_dead is not None:
        _stamp_last_detach(Path(runtime_dir), newest_dead)
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
    services: List[str] = field(
        default_factory=list
    )  # dopemux.service of those containers
    #: ``container id -> dopemux.service`` (for releasing state service by service).
    container_services: Dict[str, str] = field(default_factory=dict)
    #: Found through the launcher's ``instance.json`` marker alone: no registry entry
    #: and no container (a build-only launch). Reaped on ``worktree_missing`` only.
    dir_only: bool = False

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
            "state_only": self.state_only,
            "dir_only": self.dir_only,
        }


@dataclass
class ReapReport:
    reaped: List[ReapCandidate] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    skipped: List[ReapCandidate] = field(default_factory=list)
    skip_reasons: List[str] = field(default_factory=list)  # parallel to ``skipped``

    def skip(self, cand: ReapCandidate, reason: str) -> None:
        """``reason``: ``attached`` (a launcher attached first), ``cap``, ``deadline``,
        ``locked`` (an automatic run found the instance lock busy), ``stale`` (no
        longer eligible under the lock), ``registry_busy`` (containers removed, the
        registry lock stayed busy: a later run finishes the state) or
        ``state_error`` (containers removed, a registry or lease save failed: the
        runtime dir stays and a later run finishes the state)."""
        self.skipped.append(cand)
        self.skip_reasons.append(reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reaped": [c.to_dict() for c in self.reaped],
            "skipped": [
                {**c.to_dict(), "skip_reason": r}
                for c, r in zip(self.skipped, self.skip_reasons)
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


def _still_eligible(
    cand: "ReapCandidate", *, now: float, idle_s: float, exists: Callable[[Path], bool]
) -> bool:
    """The plan's predicate on current state (live attachments checked by the caller).

    Idle time comes from ``_effective_last_detach``, the helper planning uses; under
    the lock the prune has already turned dead records into ``last_detach``, so
    both agree. A dir-only candidate qualifies only while its worktree is gone and
    no detached build is live (never on idle).
    """
    if cand.dir_only:
        return _worktree_gone(cand.worktree_root, exists) and not _live_build(
            cand.runtime_dir, now
        )
    if _worktree_gone(cand.worktree_root, exists):
        return True
    age = _last_detach_age(cand.runtime_dir, now)
    return age is not None and age >= idle_s


def _last_detach_age(runtime_dir: Path, now: float) -> Optional[float]:
    detached = _effective_last_detach(runtime_dir)
    return None if detached is None else now - detached


def _effective_last_detach(runtime_dir: Path) -> Optional[float]:
    """When the last launcher left, read-only: ``None`` when unknown.

    The newer of ``last_detach``'s mtime and the newest dead attach record's mtime
    (a launcher killed outright never detached; ``live_attachments(prune=True)``
    would stamp that time). Records whose name is not a positive pid are ignored,
    as in ``live_attachments``. Nothing is unlinked or stamped, so planning stays a
    dry run. An unreadable ``attached`` dir is ``None`` (it also counts as attached).
    """
    latest: Optional[float] = None
    try:
        latest = (Path(runtime_dir) / LAST_DETACH).stat().st_mtime
    except OSError:
        pass
    try:
        entries = list((Path(runtime_dir) / ATTACHED_DIR).iterdir())
    except FileNotFoundError:
        return latest
    except OSError:
        return None
    for entry in entries:
        name = entry.name
        if not _is_pid_text(name) or _pid_alive(int(name)):
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue  # vanished meanwhile (a concurrent prune stamps last_detach)
        latest = mtime if latest is None else max(latest, mtime)
    return latest


def _read_instance_marker(runtime_dir: Path) -> Optional[Dict[str, str]]:
    """The identity fields of ``<runtime_dir>/instance.json``; ``None`` when absent,
    unreadable or malformed (any field missing, empty or not a string)."""
    try:
        data = json.loads(
            (Path(runtime_dir) / INSTANCE_MARKER).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    fields: Dict[str, str] = {}
    for key in INSTANCE_MARKER_FIELDS:
        value = data.get(key)
        if not isinstance(value, str) or not value:
            return None
        fields[key] = value
    return fields


def _live_build(runtime_dir: Path, now: float) -> bool:
    """Whether a detached image build may still write into ``runtime_dir``.

    The launcher's rule (``launcher._live_build_pid``, not imported: the launcher
    imports this module): a ``build-<service>.pid`` whose pid is alive and whose
    file is at most ``build_timeout_secs()`` old. A dir or pid file that cannot be
    read counts as live (never delete under a build); a non-numeric pid does not.
    """
    try:
        entries = list(Path(runtime_dir).iterdir())
    except FileNotFoundError:
        return False
    except OSError:
        return True
    budget = dr.build_timeout_secs()
    for entry in entries:
        if not (entry.name.startswith("build-") and entry.name.endswith(".pid")):
            continue
        try:
            text = entry.read_text(encoding="utf-8").strip()
            age = now - entry.stat().st_mtime
        except FileNotFoundError:
            continue
        except OSError:
            return True
        except ValueError:  # not text: not a pid the launcher wrote
            continue
        if not _is_pid_text(text):
            continue
        if age <= budget and _pid_alive(int(text)):
            return True
    return False


def _dir_only_candidates(
    registry: RuntimeRegistry,
    seen_pairs: Set[Tuple[str, str]],
    *,
    now: float,
    exists: Callable[[Path], bool],
) -> List[ReapCandidate]:
    """Launcher-marked runtime dirs that no registry entry or container accounts for.

    A launch refused with ``LAUNCH_IMAGE_BUILDING`` writes its runtime dir before
    any lifecycle start creates a registry entry. Such a dir is a candidate only
    when its ``instance.json`` is well-formed (an absolute ``worktree_root``) and
    names exactly this dir (``runtime_dir_for_paths``), the pair has no registry
    entry and no managed container, its worktree is gone, no launcher is attached
    and no detached build is live. Never on idle (a container-less dir costs
    nothing). Read-only.
    """
    base = Path(registry.path).parent
    try:
        dirs = sorted(p for p in base.iterdir() if p.is_dir() and not p.is_symlink())
    except OSError:
        return []
    found: List[ReapCandidate] = []
    for runtime_dir in dirs:
        marker = _read_instance_marker(runtime_dir)
        if marker is None:
            continue
        project_id, worktree_hash = marker["project_id"], marker["worktree_hash"]
        if (
            not _SAFE_HASH.fullmatch(worktree_hash)
            or not os.path.isabs(marker["worktree_root"])  # relative: judged vs the cwd
            or (project_id, worktree_hash) in seen_pairs
            or _entry_for(registry, project_id, worktree_hash) is not None
        ):
            continue
        expected = runtime_dir_for_paths(
            project_root=marker["project_root"],
            worktree_hash=worktree_hash,
            registry_path=registry.path,
        )
        if expected != runtime_dir:
            continue  # not a dir this marker's instance would use: not ours
        if (
            not _worktree_gone(marker["worktree_root"], exists)
            or live_attachments(runtime_dir, prune=False) > 0
            or _live_build(runtime_dir, now)
        ):
            continue
        found.append(
            ReapCandidate(
                project_id=project_id,
                worktree_hash=worktree_hash,
                worktree_root=marker["worktree_root"],
                runtime_dir=runtime_dir,
                container_ids=[],
                reason="worktree_missing",
                services=[],
                dir_only=True,
            )
        )
    return found


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
    after ``docker rm`` is finished by the next run. A launcher-marked runtime dir
    with no registry entry and no container yields a dir-only candidate
    (``_dir_only_candidates``). Idle time includes dead attach records
    (``_effective_last_detach``); nothing is pruned or stamped here.
    """
    if registry.parse_status != "OK":
        return []

    groups: Dict[Tuple[str, str], List[DockerContainerInfo]] = {}
    seen_pairs: Set[Tuple[str, str]] = set()
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
            project_root=project_root,
            worktree_hash=worktree_hash,
            registry_path=registry.path,
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
                    {(c.labels or {}).get("dopemux.service") or "" for c in members}
                    - {""}
                ),
                container_services={
                    c.id: (c.labels or {}).get("dopemux.service") or "" for c in members
                },
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
            project_root=project_root,
            worktree_hash=worktree_hash,
            registry_path=registry.path,
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
    candidates.extend(
        _dir_only_candidates(registry, seen_pairs, now=now, exists=exists)
    )
    return candidates


# --- apply ------------------------------------------------------------------------


def _owned_by(service: Optional[str], cand: ReapCandidate) -> bool:
    """Whether this reap is responsible for ``service`` of the candidate's pair.

    An empty service belongs to nobody: only a state-only candidate (worktree
    gone, no container left) clears it, so it cannot keep the pair alive forever.
    """
    if not service:
        return cand.state_only
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
        elif lease.get("service"):
            reg.mark_released(
                service=lease["service"], worktree_root=cand.worktree_root
            )
        else:  # no id and no service: nothing else can address it
            lease["status"] = "released"
            lease["updated_at"] = _utc_stamp()


def _mark_instances_stopped(reg: RuntimeRegistry, cand: ReapCandidate) -> None:
    owned = [
        inst
        for inst in reg.instances()
        if inst.get("project_id") == cand.project_id
        and inst.get("worktree_hash") == cand.worktree_hash
        and inst.get("scope") == _REAPABLE_SCOPE
        and _owned_by(inst.get("service"), cand)
    ]
    for service in sorted(
        {str(inst["service"]) for inst in owned if inst.get("service")}
    ):
        reg.mark_stopped(
            project_id=cand.project_id,
            service=service,
            worktree_root=cand.worktree_root,
        )
    for inst in owned:
        if not inst.get(
            "service"
        ):  # mark_stopped(service="") would match every service
            inst["status"] = "stopped"
            inst["updated_at"] = _utc_stamp()


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
    call_timeout: Callable[[], Optional[float]] = lambda: None,
    out_of_time: Callable[[], bool] = lambda: False,
) -> Tuple[List[str], List[str]]:
    """``(errors, ids of containers now gone)``; ``call_timeout()`` bounds each docker call."""

    def kwargs() -> Dict[str, Any]:
        timeout = call_timeout()
        return {} if timeout is None else {"timeout": timeout}

    stop_cmd = ["docker", "stop"] + (
        [] if stop_time_s is None else ["--time", str(stop_time_s)]
    )
    errors: List[str] = []
    gone: List[str] = []
    for cid in cand.container_ids:
        if out_of_time():
            errors.append(
                f"{cid}: deadline reached before docker call; resumes next run"
            )
            break
        stop = runner([*stop_cmd, cid], **kwargs())
        if stop.exit_code != 0 and not _already_gone(stop):
            errors.append(
                f"{cid}: docker stop failed ({stop.exit_code}): {stop.stderr.strip()[:200]}"
            )
            continue  # never remove (let alone force-remove) what did not stop
        if out_of_time():
            errors.append(f"{cid}: deadline reached before docker rm; resumes next run")
            break
        rm = runner(["docker", "rm", cid], **kwargs())
        if rm.exit_code != 0 and not _already_gone(rm):
            errors.append(
                f"{cid}: docker rm failed ({rm.exit_code}): {rm.stderr.strip()[:200]}"
            )
            continue
        gone.append(cid)
    return errors, gone


def _services_gone(cand: ReapCandidate, gone: Sequence[str]) -> List[str]:
    """Services of ``cand`` all of whose containers are in ``gone``."""
    removed = set(gone)
    return [
        svc
        for svc in cand.services
        if all(
            cid in removed
            for cid, owner in cand.container_services.items()
            if owner == svc
        )
        and any(owner == svc for owner in cand.container_services.values())
    ]


def _release_state(
    cand: ReapCandidate,
    lease_path: Path,
    registry_path: Path,
    report: ReapReport,
    label: str,
    *,
    wait_s: Optional[float] = None,
) -> List[str]:
    """Release ``cand``'s leases and mark its registry entries stopped (registry lock inside).

    Both registries in one directory share one ``registry.lock`` and are updated
    under one acquisition, so a lock that stays busy past ``wait_s`` raises
    ``LockBusy`` with neither changed. ``wait_s=None`` blocks (the CLI).

    Returns the error strings it appended to ``report.errors`` (a corrupt registry
    left as is, an ``OSError`` on save): empty means both registries were saved.
    """
    updates: List[Tuple[Any, Path, Callable[[Any], Any]]] = [
        (PortLeaseRegistry, lease_path, lambda reg: _release_leases(reg, cand)),
        (
            RuntimeRegistry,
            registry_path,
            lambda reg: _mark_instances_stopped(reg, cand),
        ),
    ]
    if Path(lease_path).parent.resolve() == Path(registry_path).parent.resolve():
        errors = save_states_locked(updates, wait_s=wait_s)
    else:  # separate directories (overridden paths): one lock each
        errors = [
            e
            for e in (save_state_locked(c, p, m, wait_s=wait_s) for c, p, m in updates)
            if e
        ]
    recorded = [f"{label}: {error}" for error in errors]
    report.errors.extend(recorded)
    return recorded


def _reap_one(
    cand: ReapCandidate,
    runner: Callable[..., Any],
    lease_path: Path,
    registry_path: Path,
    report: ReapReport,
    *,
    stop_time_s: Optional[int],
    call_timeout: Callable[[], Optional[float]] = lambda: None,
    out_of_time: Callable[[], bool] = lambda: False,
    blocking_lock: bool = True,
    now: Callable[[], float] = time.time,
    idle_s: float = 1200,
    exists: Callable[[Path], bool] = Path.exists,
    registry_wait: Optional[Callable[[], float]] = None,
) -> None:
    label = f"{cand.project_id}/{cand.worktree_hash}"
    if not _runtime_dir_is_ours(cand, registry_path):
        report.errors.append(
            f"{label}: runtime dir {cand.runtime_dir} is outside {registry_path.parent}"
        )
        return
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(instance_lock(cand.runtime_dir, blocking=blocking_lock))
        except LockBusy:
            report.skip(cand, "locked")  # a launcher or stop holds it: next run
            return
        if live_attachments(cand.runtime_dir) > 0:
            report.skip(cand, "attached")
            return
        if not _still_eligible(cand, now=now(), idle_s=idle_s, exists=exists):
            report.skip(
                cand, "stale"
            )  # a launcher came and went, or the worktree is back
            return
        docker_errors, gone = _stop_and_remove(
            cand,
            runner,
            stop_time_s=stop_time_s,
            call_timeout=call_timeout,
            out_of_time=out_of_time,
        )
        if docker_errors:
            report.errors.extend(f"{label}: {e}" for e in docker_errors)
            # Some containers may still run: keep their leases, entries and the dir,
            # but release every service whose containers are all gone now. This
            # branch never removes the dir and never counts as reaped (a failed
            # save below is already in ``report.errors``).
            done = _services_gone(cand, gone)
            if done:
                try:
                    _release_state(
                        replace(cand, services=done),
                        lease_path,
                        registry_path,
                        report,
                        label,
                        wait_s=None if registry_wait is None else registry_wait(),
                    )
                except LockBusy:
                    report.errors.append(
                        f"{label}: registry busy; the state of {', '.join(done)} "
                        "is released by a later run"
                    )
            return
        try:
            state_errors = _release_state(
                cand,
                lease_path,
                registry_path,
                report,
                label,
                wait_s=None if registry_wait is None else registry_wait(),
            )
        except LockBusy:
            # Containers are gone; registry, leases and the runtime dir stay for a
            # later run (a state-only candidate once the worktree is gone).
            report.skip(cand, "registry_busy")
            return
        if state_errors:
            # Same as registry_busy: the containers are gone, but a registry or lease
            # save failed (already in report.errors), so the runtime dir stays as the
            # recovery artifact and a later run finishes the state.
            report.skip(cand, "state_error")
            return
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
    blocking_locks: bool = True,
    now: Callable[[], float] = time.time,
    idle_s: float = 1200,
    exists: Callable[[Path], bool] = Path.exists,
) -> ReapReport:
    """Reap each candidate under its instance lock; failures are recorded, never raised.

    Under the lock the plan's predicate is evaluated again on current state
    (``now``, ``idle_s``, ``exists`` as for ``plan_reap``); a candidate that no
    longer qualifies is skipped as ``stale``. ``blocking_locks=False`` (automatic
    runs) skips a candidate whose instance lock is busy (``locked``) and waits for
    the registry lock at most ``min(time left, 2 s)`` (``registry_busy``). A failed
    registry or lease save keeps the runtime dir (``state_error``).

    ``max_candidates`` caps the work of one call, ``stop_time_s`` becomes
    ``docker stop --time N``, ``cmd_timeout_s`` is the per-command timeout and
    ``deadline`` an absolute ``clock()`` (monotonic) value. Under a deadline each
    docker call is bounded by ``min(cmd_timeout_s, time left)``, so a timeout longer
    than the time left never skips a candidate by itself; once no time is left the
    remaining candidates are reported under ``skipped`` (reasons ``cap`` /
    ``deadline``) and wait for the next run. All default to unbounded (the explicit
    CLI).
    """
    leases = (
        Path(lease_path) if lease_path is not None else default_lease_registry_path()
    )
    registry = (
        Path(registry_path) if registry_path is not None else runtime_registry_path()
    )
    report = ReapReport()
    limit = len(candidates) if max_candidates is None else max(0, max_candidates)

    def time_left() -> Optional[float]:
        return None if deadline is None else deadline - clock()

    def out_of_time() -> bool:
        left = time_left()
        return left is not None and left <= 0

    def call_timeout() -> Optional[float]:
        left = time_left()
        if left is None:
            return cmd_timeout_s
        return left if cmd_timeout_s is None else min(cmd_timeout_s, left)

    def registry_wait() -> float:
        left = time_left()
        return (
            _REGISTRY_WAIT_S if left is None else max(0.0, min(_REGISTRY_WAIT_S, left))
        )

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
                call_timeout=call_timeout,
                out_of_time=out_of_time,
                blocking_lock=blocking_locks,
                now=now,
                idle_s=idle_s,
                exists=exists,
                registry_wait=None if blocking_locks else registry_wait,
            )
        except Exception as exc:  # noqa: BLE001 - one bad candidate stops no other
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
    candidates, ``docker stop --time 5``, 20 s per command; the Stop hook adds a 60 s
    deadline. A launcher passes 1 candidate, ``--time 2``, 3 s per command and an 8 s
    deadline because it runs inside Claude's connect budget; SessionEnd passes 1 / 3 /
    10 and a 45 s deadline.

    ``state_file`` is touched before any work (so concurrent hooks do not all run);
    when candidates existed but none was attempted (deadline, cap, or a busy
    instance lock), or the docker inspection timed out, the touch is undone, so a
    run that did nothing never consumes the throttle. Instance locks are taken
    non-blocking and the inspection is bounded by ``min(cmd_timeout_s, time left)``.
    """
    if reaping_disabled_reason() is not None:
        return None
    deadline = None if deadline_s is None else monotonic() + deadline_s
    state = (
        Path(state_file) if state_file is not None else _runtime_dir() / STATE_FILENAME
    )
    current = now()
    if throttle_s > 0:
        try:
            if current - state.stat().st_mtime < throttle_s:
                return None
        except OSError:
            pass
    try:
        previous: Optional[float] = state.stat().st_mtime
    except OSError:
        previous = None
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
    inspect_timeout = min(
        _HOOK_DOCKER_TIMEOUT_S, cmd_timeout_s or _HOOK_DOCKER_TIMEOUT_S
    )
    if deadline is not None:
        left = deadline - monotonic()
        if left <= 0:
            _restore_throttle(state, previous)
            report.errors.append("deadline reached before docker inspection; skipped")
            return report
        inspect_timeout = min(inspect_timeout, left)
    run_inspect = inspector or inspect_all_managed_containers
    docker = run_inspect(timeout=inspect_timeout)
    if not docker.available:
        timed_out = "timed out" in str(docker.error or "").lower() or (
            deadline is not None and monotonic() >= deadline
        )
        if timed_out:  # a slow docker skips the whole run and touches nothing
            _restore_throttle(state, previous)
            report.errors.append(
                f"docker inspection timed out; skipped ({docker.error})"
            )
            return report
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
    report = apply_reap(
        candidates,
        runner=runner or run_cmd,
        max_candidates=max_candidates,
        stop_time_s=stop_time_s,
        cmd_timeout_s=cmd_timeout_s,
        deadline=deadline,
        clock=monotonic,
        blocking_locks=False,
        now=now,
        idle_s=idle_s,
    )
    not_attempted = sum(
        1 for r in report.skip_reasons if r in {"cap", "deadline", "locked", "stale"}
    )
    if not_attempted == len(candidates):
        _restore_throttle(state, previous)
    return report


def _restore_throttle(state: Path, previous: Optional[float]) -> None:
    """Undo ``maybe_reap``'s touch of ``state`` (to ``previous``, or remove it)."""
    with contextlib.suppress(OSError):
        if previous is None:
            state.unlink()
        else:
            os.utime(state, (previous, previous))
