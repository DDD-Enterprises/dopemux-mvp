"""``dopemux mcp launch <service>``: find or start the worktree's sidecar, then proxy stdio.

Design D2/D4/D7 of claudedocs/mcp-just-works-design-2026-11-05.md:

1. Root: git top-level of ``--root`` or the process cwd; refuse outside git or
   when ``.mcp.json`` is not the dopemux-rendered launcher entry.
2. Identity from git only (``resolve_identity_view``), never ambient env.
3. Warm path: registry record + SDK probe, no lifecycle call. Cold path: under
   ``instance_lock(runtime_dir)``, start through ``run_lifecycle("start")``.
   A missing image is built detached and the launch refuses (never block a
   session on a multi-minute build).
4. Task Orchestrator: under ``reserved_port_lock(7890)``, ownership is proven
   from the labels of the container publishing 7890; foreign or unknown
   owners refuse, a free port starts this project's jar.
5. Attach record, then the SDK stdio proxy with an owner guard that re-proves
   the backend's owner from Docker labels before every backend connect (the
   first included; this launch-time check's reserved lock is released by then)
   and again right after each ``initialize``.

Every refusal is one line ``CODE: remedy`` on stderr and exit code 3 (an
``OSError`` before the proxy runs is ``LAUNCH_IO_ERROR``). SIGTERM and SIGHUP
exit 143 and 129 through ``finally``, so the attach record is always detached.

``launch(service, *, root=None, env=None, registry_path=None, reaper=...)``:
``env=None`` means ``os.environ`` read at call time (a default of the mapping
itself would render every variable, secrets included, in ``help()``).
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional
from urllib.parse import urlparse

from . import docker_runtime as dr
from . import stdio_proxy
from .docker_inspect import DockerContainerInfo, inspect_running_containers
from .lifecycle import _port_is_free, run_lifecycle, runtime_dir_for
from .locks import instance_lock, reserved_port_lock
from .reap import _pid_alive, attach, detach, maybe_reap
from .runtime_registry import RuntimeRegistry, default_registry_path
from .runtime_state import (
    PROJECT_MCP_FILENAME,
    ProjectIdentityView,
    resolve_identity_view,
    sidecar_url,
)
from .stdio_proxy import (
    BackendSpec,
    ProxyRefused,
    probe_backend,
    quiet_sdk_loggers,
    run_proxy,
)
from .task_orchestrator_identity import identity_from_docker_labels, match_target

__all__ = [
    "LaunchError",
    "LaunchTarget",
    "attach",
    "build_target",
    "detach",
    "ensure_backend",
    "ensure_orchestrator",
    "find_backend",
    "launch",
    "reconnect_guard",
    "resolve_launch_root",
]

DEFAULT_WAIT_S = 25.0
WAIT_ENV = "DOPEMUX_LAUNCH_WAIT"
POLL_INTERVAL_S = 0.5
EXIT_REFUSED = 3

TO_SERVICE = "task-orchestrator"
TO_PORT = 7890
TO_BACKEND = BackendSpec(f"http://127.0.0.1:{TO_PORT}/mcp", "http", TO_SERVICE)
TO_WRONG_PROJECT = "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT"
TO_UNKNOWN_OWNER = "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER"
OWNER_CHANGED = "LAUNCH_BACKEND_OWNER_CHANGED"
#: ``docker ps`` budget of one reconnect-guard call (the proxy bounds the call itself too).
GUARD_DOCKER_TIMEOUT_S = 10.0

Probe = Callable[[BackendSpec], bool]


class LaunchError(Exception):
    """A refusal with a finding code and a one-line remedy."""

    def __init__(self, code: str, remedy: str) -> None:
        super().__init__(f"{code}: {remedy}")
        self.code = code
        self.remedy = remedy


@dataclass(frozen=True)
class LaunchTarget:
    root: Path
    identity: ProjectIdentityView
    service: str
    spec: Mapping[str, Any]
    runtime_dir: Path
    compose_project: str
    # Carried for the lifecycle call and registry reads; not part of identity.
    catalog: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    registry_path: Optional[Path] = None


# --- root -------------------------------------------------------------------


def _git_toplevel(base: Path) -> Optional[Path]:
    if not base.is_dir():
        return None
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    top = proc.stdout.strip()
    if proc.returncode != 0 or not top:
        return None
    return Path(top).resolve()


def _is_launcher_entry(name: str, entry: Any) -> bool:
    return (
        isinstance(entry, dict)
        and entry.get("type") == "stdio"
        and entry.get("args") == ["mcp", "launch", name]
    )


def _require_managed_mcp_json(root: Path, service: Optional[str]) -> None:
    path = root / PROJECT_MCP_FILENAME
    remedy = f"{path} is not dopemux-rendered; run dopemux mcp repair-config --apply"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise LaunchError("LAUNCH_MCP_JSON_NOT_MANAGED", remedy) from None
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        raise LaunchError("LAUNCH_MCP_JSON_NOT_MANAGED", remedy)
    if service is not None:
        managed = _is_launcher_entry(service, servers.get(service))
    else:
        managed = any(
            _is_launcher_entry(name, entry) for name, entry in servers.items()
        )
    if not managed:
        raise LaunchError("LAUNCH_MCP_JSON_NOT_MANAGED", remedy)


def resolve_launch_root(
    explicit: Optional[Path], *, cwd: Path, service: Optional[str] = None
) -> Path:
    """Git top-level of ``explicit or cwd`` whose ``.mcp.json`` is dopemux-rendered.

    With ``service``, that service's entry must be the stdio launcher entry
    Task 3a renders; without it, at least one entry must be.
    """
    base = Path(explicit if explicit is not None else cwd).expanduser()
    root = _git_toplevel(base)
    if root is None:
        raise LaunchError(
            "LAUNCH_ROOT_NOT_GIT",
            f"{base} is not inside a git work tree; start the session in a checkout",
        )
    _require_managed_mcp_json(root, service)
    return root


# --- target -------------------------------------------------------------------


def build_target(
    root: Path,
    service: str,
    *,
    catalog: Mapping[str, Any],
    registry_path: Optional[Path] = None,
) -> LaunchTarget:
    from .fleet_catalog import catalog_client_shape  # lazy: imports the CLI module

    spec = (catalog.get("servers") or {}).get(service)
    if not isinstance(spec, Mapping) or catalog_client_shape(dict(spec)) != "launcher":
        raise LaunchError(
            "LAUNCH_SERVICE_UNKNOWN",
            f"{service} is not a launcher service in the MCP catalog; run dopemux mcp doctor",
        )
    identity = resolve_identity_view(Path(root))
    if (
        not identity.project_id
        or not identity.project_root
        or identity.identity_confidence == "UNKNOWN"
    ):
        raise LaunchError("PROJECT_IDENTITY_UNKNOWN", "run dopemux mcp doctor")
    slug = dr.project_slug(Path(identity.project_root).name)
    return LaunchTarget(
        root=Path(root),
        identity=identity,
        service=service,
        spec=spec,
        runtime_dir=runtime_dir_for(identity, registry_path=registry_path),
        compose_project=dr.compose_project_name(slug, identity.worktree_hash or ""),
        catalog=catalog,
        registry_path=registry_path,
    )


# --- backend discovery --------------------------------------------------------


def _registry_file(target: LaunchTarget, registry_path: Optional[Path] = None) -> Path:
    return Path(registry_path or target.registry_path or default_registry_path())


def _backend(target: LaunchTarget, ports: Mapping[str, Any]) -> Optional[BackendSpec]:
    """The sidecar at ``ports``; None when they lack the service's port (never a default)."""
    clean = {
        str(k): int(v)
        for k, v in ports.items()
        if isinstance(v, int) or str(v).isdigit()
    }
    url = sidecar_url(target.spec, clean)
    if url is None:
        return None
    return BackendSpec(url, target.spec["transport"], target.service)


def find_backend(
    target: LaunchTarget, *, registry_path: Optional[Path] = None
) -> Optional[BackendSpec]:
    """The newest ``running`` registry record for this worktree and service.

    A record without the service's port is not a backend (the cold path starts
    through the lifecycle, which records the ports again).
    """
    registry = RuntimeRegistry.load(_registry_file(target, registry_path))
    if registry.parse_status != "OK":
        return None
    running = [
        rec
        for rec in registry.find(
            project_id=target.identity.project_id,
            worktree_root=target.identity.worktree_root,
            service=target.service,
        )
        if rec.get("status") == "running"
    ]
    if not running:
        return None
    newest = max(running, key=lambda rec: str(rec.get("updated_at") or ""))
    return _backend(target, newest.get("ports") or {})


def _lifecycle_env(
    env: Optional[Mapping[str, str]], catalog: Mapping[str, Any]
) -> Dict[str, str]:
    """Process env for the lifecycle minus ambient identity and catalog port vars.

    Ports come from the lease registry (and the checkout's own envrc, which
    the lifecycle reads itself), never from another checkout's exports. The
    identity/port/tenant set is ``docker_runtime.AMBIENT_SCRUB_VARS`` (D3, D5),
    defined once and shared with the lifecycle's compose environment.
    """
    drop = set(dr.AMBIENT_SCRUB_VARS)
    for spec in (catalog.get("servers") or {}).values():
        if not isinstance(spec, Mapping):
            continue
        if spec.get("port_var"):
            drop.add(str(spec["port_var"]))
        for extra in spec.get("extra_port_vars") or []:
            if isinstance(extra, Mapping) and extra.get("var"):
                drop.add(str(extra["var"]))
    source = os.environ if env is None else env
    return {k: v for k, v in source.items() if k not in drop}


def _lifecycle_error(result: Any, service: str) -> LaunchError:
    for finding in getattr(result, "blocking_findings", None) or []:
        if finding.get("code"):
            message = finding.get("message") or "start blocked"
            return LaunchError(
                str(finding["code"]), f"{message}; run dopemux mcp doctor"
            )
    for svc in getattr(result, "services", None) or []:
        for finding in svc.get("findings") or []:
            if finding.get("severity") in {"ERROR", "FAIL"} and finding.get("code"):
                return LaunchError(
                    str(finding["code"]), str(finding.get("message") or "")
                )
    tail = ""
    for svc in getattr(result, "services", None) or []:
        stderr = ((svc.get("result") or {}).get("stderr") or "").strip()
        if stderr:
            tail = f" ({stderr[-200:]})"
    return LaunchError(
        "LAUNCH_START_FAILED",
        f"dopemux mcp start --services {service} exited {getattr(result, 'exit_code', '?')}"
        f"{tail}; run dopemux mcp doctor",
    )


def _backend_from_result(target: LaunchTarget, result: Any) -> Optional[BackendSpec]:
    for svc in getattr(result, "services", None) or []:
        if svc.get("service") == target.service and isinstance(
            svc.get("ports"), Mapping
        ):
            backend = _backend(target, svc["ports"])
            if backend is None:
                raise LaunchError(
                    "LAUNCH_BACKEND_PORT_UNKNOWN",
                    f"start reported no {target.spec.get('port_var') or 'port'} for "
                    f"{target.service}; run dopemux mcp doctor",
                )
            return backend
    return None


def _wait_for(
    backend: BackendSpec,
    *,
    probe: Probe,
    deadline: float,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
) -> BackendSpec:
    while clock() < deadline:
        sleep(POLL_INTERVAL_S)
        if probe(backend):
            return backend
    raise LaunchError("LAUNCH_WAIT_EXCEEDED", "run /mcp reconnect all")


# --- image policy (D4) ----------------------------------------------------------


def build_pid_path(runtime_dir: Path, service: str) -> Path:
    """``<runtime_dir>/build-<service>.pid``: one per service, so both sidecars may build at once."""
    return Path(runtime_dir) / f"build-{service}.pid"


def _live_build_pid(pid_file: Path) -> Optional[int]:
    """The pid of a build still running, or None (absent, dead, or older than the build budget).

    The age limit is ``build_timeout_secs()`` (``DOPEMUX_MCP_BUILD_TIMEOUT_SECS``,
    default 1800 s), the budget a build gets, never the shorter ``up`` budget.
    """
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        age = time.time() - pid_file.stat().st_mtime
    except (OSError, ValueError):
        return None
    if pid <= 0 or age > dr.build_timeout_secs() or not _pid_alive(pid):
        return None  # stale: replaced by the next build
    return pid


def _write_build_pid(pid_file: Path, pid: int) -> None:
    tmp = pid_file.with_name(f".{pid_file.name}.{os.getpid()}.tmp")
    tmp.write_text(f"{pid}\n", encoding="utf-8")
    os.replace(tmp, pid_file)


def _build_image_if_missing(target: LaunchTarget) -> None:
    """Refuse with ``LAUNCH_IMAGE_BUILDING`` while the shared image is missing (D4).

    The first launch spawns one detached ``compose build`` of this service and
    records its pid in ``<runtime_dir>/build-<service>.pid``; a launch of the same
    service while that pid is alive spawns nothing. The other service's build is
    independent: conport and dope-memory may build at once.
    """
    if target.spec.get("management_model") != "compose-service":
        return
    product = dr.product_root()
    env = dr.env_with_compose_interpolation(product=product, scrub_ambient=True)
    image = dr.compose_image_name(target.service, product=product)
    if dr.docker_image_exists(image, env=env) is not False:
        return
    remedy = "building image; retry with /mcp reconnect all in a few minutes"
    log_path = target.runtime_dir / "build.log"
    pid_file = build_pid_path(target.runtime_dir, target.service)
    running = _live_build_pid(pid_file)
    if running is not None:
        print(
            f"dopemux mcp launch: {image} is still building (pid {running}); log {log_path}",
            file=sys.stderr,
        )
        raise LaunchError("LAUNCH_IMAGE_BUILDING", remedy)
    override, env_file = dr.compose_build_inputs(target.runtime_dir, product=product)
    command = dr.compose_build_command(
        product=product,
        override_path=override,
        env_file=env_file,
        project_name=target.compose_project,
        services=[target.service],
    )
    # Append: conport and dope-memory may build at once (separate pid files).
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=str(product),
            env=env,
            start_new_session=True,
        )
    _write_build_pid(pid_file, proc.pid)
    print(f"dopemux mcp launch: building {image}; log {log_path}", file=sys.stderr)
    raise LaunchError("LAUNCH_IMAGE_BUILDING", remedy)


# --- ensure ---------------------------------------------------------------------


def ensure_backend(
    target: LaunchTarget,
    *,
    wait_s: float,
    lifecycle: Callable[..., Any] = run_lifecycle,
    probe: Probe = probe_backend,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    env: Optional[Mapping[str, str]] = None,
) -> BackendSpec:
    """A reachable sidecar for ``target`` (conport / dope-memory)."""
    deadline = clock() + wait_s
    warm = find_backend(target)
    if warm is not None and probe(warm):
        return warm
    with instance_lock(target.runtime_dir):
        warm = find_backend(target)
        if warm is not None and probe(warm):
            return warm
        _build_image_if_missing(target)
        result = lifecycle(
            "start",
            repo=target.root,
            services=[target.service],
            catalog=target.catalog,
            registry_path=target.registry_path,
            process_env=_lifecycle_env(env, target.catalog),
            trust_env=False,
        )
        if result.exit_code != 0:
            raise _lifecycle_error(result, target.service)
        backend = _backend_from_result(target, result) or find_backend(target)
        if backend is None:
            raise LaunchError(
                "LAUNCH_START_FAILED",
                f"start reported no ports for {target.service}; run dopemux mcp doctor",
            )
        if probe(backend):
            return backend
    return _wait_for(backend, probe=probe, deadline=deadline, clock=clock, sleep=sleep)


def _orchestrator_owner_verdict(
    owners: List[DockerContainerInfo], target: LaunchTarget
) -> None:
    """Return when the 7890 container is this project's; raise otherwise."""
    if len(owners) != 1:
        raise LaunchError(TO_UNKNOWN_OWNER, "run dopemux mcp doctor")
    owner = owners[0]
    observed = identity_from_docker_labels(
        owner.labels or {}, port=TO_PORT, container_name=owner.name
    )
    verdict = match_target(
        observed,
        project_id=target.identity.project_id,
        project_root=target.identity.project_root,
    )
    if verdict == "OK":
        return
    if verdict == "WRONG_PROJECT":
        owner_root = observed.project_root or observed.project_id or owner.name
        raise LaunchError(
            TO_WRONG_PROJECT,
            f"{owner_root}; run dopemux mcp switch-project here to take it over",
        )
    raise LaunchError(TO_UNKNOWN_OWNER, "run dopemux mcp doctor")


def _orchestrator_port_is_ours(
    target: LaunchTarget, state: Any, port_is_free: Callable[[int], bool]
) -> bool:
    """True when this project's orchestrator publishes :7890, False when the port is free.

    Raises ``LaunchError`` for a foreign or unknown owner.
    """
    owners = (
        [c for c in state.containers if TO_PORT in (c.published_ports or [])]
        if state.available
        else []
    )
    if owners:
        _orchestrator_owner_verdict(owners, target)
        return True
    if not port_is_free(TO_PORT):
        raise LaunchError(TO_UNKNOWN_OWNER, "run dopemux mcp doctor")
    return False


def ensure_orchestrator(
    target: LaunchTarget,
    *,
    docker: Callable[[], Any] = inspect_running_containers,
    lifecycle: Callable[..., Any] = run_lifecycle,
    probe: Probe = probe_backend,
    port_is_free: Callable[[int], bool] = _port_is_free,
    wait_s: float = DEFAULT_WAIT_S,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    env: Optional[Mapping[str, str]] = None,
) -> BackendSpec:
    """The reserved-port orchestrator, proven to be this project's (D2, D7)."""
    deadline = clock() + wait_s
    with reserved_port_lock(TO_PORT):
        if _orchestrator_port_is_ours(target, docker(), port_is_free):
            return TO_BACKEND
        result = lifecycle(
            "start",
            repo=target.root,
            services=[TO_SERVICE],
            catalog=target.catalog,
            registry_path=target.registry_path,
            process_env=_lifecycle_env(env, target.catalog),
            trust_env=False,
        )
        if result.exit_code != 0:
            raise _lifecycle_error(result, TO_SERVICE)
        if probe(TO_BACKEND):
            return TO_BACKEND
    return _wait_for(
        TO_BACKEND, probe=probe, deadline=deadline, clock=clock, sleep=sleep
    )


# --- reconnect guard (C1) ---------------------------------------------------------


def _check_sidecar_owner(
    target: LaunchTarget,
    port: Optional[int],
    state: Any,
    port_is_free: Callable[[int], bool],
) -> None:
    """Pass when ``port`` is free or published by this worktree's own sidecar; else raise."""
    service = target.service
    if port is None:
        raise LaunchError(OWNER_CHANGED, f"the {service} backend URL names no port")
    owners = (
        [c for c in state.containers if port in (c.published_ports or [])]
        if state.available
        else []
    )
    if not owners:
        if port_is_free(port):
            return  # backend down: the reconnect attempt fails and retries
        raise LaunchError(
            OWNER_CHANGED,
            f":{port} is held by a process that is not this worktree's {service}; "
            "run dopemux mcp doctor",
        )
    labels = (owners[0].labels or {}) if len(owners) == 1 else {}
    ident = target.identity
    if (
        len(owners) != 1
        or labels.get(dr.LABEL_MANAGED) != "true"
        or labels.get("dopemux.project_id") != ident.project_id
        or labels.get("dopemux.worktree_hash") != ident.worktree_hash
        or labels.get("dopemux.service", service) != service
    ):
        names = ", ".join(c.name for c in owners)
        raise LaunchError(
            OWNER_CHANGED,
            f"{names} now publishes :{port} and is not this worktree's {service}; "
            f"run /mcp reconnect {service}",
        )


def reconnect_guard(
    target: LaunchTarget,
    backend: BackendSpec,
    *,
    docker: Optional[Callable[[], Any]] = None,
    port_is_free: Callable[[int], bool] = _port_is_free,
) -> Callable[[], None]:
    """The proxy's ``reconnect_guard`` for ``target``: re-prove who owns the backend port.

    task-orchestrator: the docker inspection and owner verdict of
    ``ensure_orchestrator`` (``TASK_ORCHESTRATOR_START_BLOCKED_*``). conport and
    dope-memory: the container publishing the backend port must carry
    ``dopemux.managed=true`` and this instance's ``dopemux.project_id`` and
    ``dopemux.worktree_hash`` (``LAUNCH_BACKEND_OWNER_CHANGED``). A free port passes:
    nothing can answer there, so the connect attempt fails and is retried. The
    proxy calls it before every connect and again after every ``initialize``.
    """

    def inspect() -> Any:
        if docker is not None:
            return docker()
        return inspect_running_containers(timeout=GUARD_DOCKER_TIMEOUT_S)

    port = urlparse(backend.url).port

    def guard() -> None:
        try:
            if target.service == TO_SERVICE:
                _orchestrator_port_is_ours(target, inspect(), port_is_free)
            else:
                _check_sidecar_owner(target, port, inspect(), port_is_free)
        except LaunchError as exc:
            raise ProxyRefused(exc.code, exc.remedy) from None

    return guard


# --- launch -----------------------------------------------------------------------


def _load_catalog(root: Optional[Path] = None) -> Dict[str, Any]:
    """The MCP catalog for ``root``: ``$DOPEMUX_MCP_CATALOG``, else its repo-local one, else bundled."""
    import click

    from dopemux.commands.mcp_commands import _load_catalog as load

    try:
        catalog: Dict[str, Any] = load(repo=root)
    except click.ClickException as exc:
        raise LaunchError("LAUNCH_CATALOG_INVALID", exc.format_message()) from None
    return catalog


# A launcher runs inside Claude's connect budget: one candidate, short docker calls
# (each also capped at the time left), all within 8 s.
LAUNCH_REAP_LIMITS: Dict[str, Any] = {
    "max_candidates": 1,
    "stop_time_s": 2,
    "cmd_timeout_s": 3.0,
    "deadline_s": 8.0,
}

#: Exit codes of a launcher ended by a signal (128 + signal number).
_SIGNAL_EXITS = {"SIGTERM": 143, "SIGHUP": 129}


@contextlib.contextmanager
def _signals_exit_through_finally() -> Iterator[None]:
    """SIGTERM/SIGHUP end the launch with 143/129 through ``finally``; restored on exit.

    Outside an event loop the handler raises ``SystemExit(128 + signum)``. Inside
    one (a backend probe or the proxy) raising there is unsafe (an exception group,
    or a loop shutdown that never finishes), so the handler defers: the loop is
    cancelled at a safe point and ``run_proxy`` returns the code, or
    ``probe_backend`` raises it once its loop has ended. Only the main thread can
    install handlers; elsewhere this does nothing.
    """
    installed: Dict[int, Any] = {}
    stdio_proxy.reset_deferred_exit()

    def _exit(signum: int, _frame: Any) -> None:
        if stdio_proxy.defer_exit_in_event_loop(128 + signum):
            return
        raise SystemExit(128 + signum)

    if threading.current_thread() is threading.main_thread():
        for name in _SIGNAL_EXITS:
            signum = getattr(signal, name, None)
            if signum is not None:
                installed[signum] = signal.signal(signum, _exit)
    try:
        yield
    finally:
        for signum, previous in installed.items():
            signal.signal(signum, previous)


def _run_reaper(reaper: Optional[Callable[[], Any]]) -> None:
    try:
        if reaper is not None:
            reaper()
        else:
            maybe_reap(**LAUNCH_REAP_LIMITS)
    except Exception as exc:  # noqa: BLE001 - cleanup must never block a launch
        print(f"reap skipped: {exc}", file=sys.stderr, flush=True)


def _wait_seconds(env: Mapping[str, str]) -> float:
    try:
        value = float(env.get(WAIT_ENV) or DEFAULT_WAIT_S)
    except ValueError:
        return DEFAULT_WAIT_S
    return value if value > 0 else DEFAULT_WAIT_S


def _process_cwd() -> Path:
    try:
        return Path.cwd()
    except FileNotFoundError:
        raise LaunchError(
            "LAUNCH_ROOT_NOT_GIT", "the working directory no longer exists"
        ) from None


def launch(
    service: str,
    *,
    root: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    registry_path: Optional[Path] = None,
    reaper: Optional[Callable[[], Any]] = None,
) -> int:
    """Run the launcher for ``service``; returns the process exit code.

    ``env`` defaults to ``os.environ`` as it is when called. ``reaper`` defaults to
    ``reap.maybe_reap`` (throttled, kill-switchable, capped at one candidate, 8 s
    deadline); it runs after this launcher's attach record exists, so its own
    instance is never reaped, and outside the instance lock. A reap failure never
    refuses a launch. ``root`` (``--root``) picks the checkout and its catalog.
    """
    if env is None:
        env = os.environ
    record: Optional[Path] = None
    with _signals_exit_through_finally(), quiet_sdk_loggers():
        try:
            # stdout is the MCP channel: nothing before the proxy may print there.
            with contextlib.redirect_stdout(sys.stderr):
                launch_root = resolve_launch_root(
                    root, cwd=_process_cwd(), service=service
                )
                target = build_target(
                    launch_root,
                    service,
                    catalog=_load_catalog(launch_root),
                    registry_path=registry_path,
                )
                # D8: the attach record is written under the instance lock, so a reap
                # that holds the lock sees either the record or none of this launch.
                # Released before the reaper (the reap takes the lock itself) and
                # before ensure_backend (which takes it again; it is not re-entrant).
                with instance_lock(target.runtime_dir):
                    record = attach(target.runtime_dir)
                _run_reaper(reaper)
                wait_s = _wait_seconds(env)
                if service == TO_SERVICE:
                    backend = ensure_orchestrator(target, wait_s=wait_s, env=env)
                else:
                    backend = ensure_backend(target, wait_s=wait_s, env=env)
                guard = reconnect_guard(target, backend)
            return run_proxy(backend, reconnect_guard=guard)
        except LaunchError as exc:
            print(f"{exc.code}: {exc.remedy}", file=sys.stderr, flush=True)
            return EXIT_REFUSED
        except OSError as exc:
            # attach, build.log, a lock that never stabilised: a refusal, not a traceback
            print(
                f"LAUNCH_IO_ERROR: {exc}; retry, and run dopemux mcp doctor if it persists",
                file=sys.stderr,
                flush=True,
            )
            return EXIT_REFUSED
        finally:
            if record is not None:
                detach(record)
