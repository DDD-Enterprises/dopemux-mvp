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
5. Attach record, then the SDK stdio proxy.

Every refusal is one line ``CODE: remedy`` on stderr and exit code 3.

``launch(service, *, root=None, env=None, registry_path=None, reaper=...)``:
``env=None`` means ``os.environ`` read at call time (a default of the mapping
itself would render every variable, secrets included, in ``help()``).
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

from . import docker_runtime as dr
from .docker_inspect import DockerContainerInfo, inspect_running_containers
from .lifecycle import _port_is_free, run_lifecycle, runtime_dir_for
from .locks import instance_lock, reserved_port_lock
from .runtime_registry import RuntimeRegistry, default_registry_path
from .runtime_state import (
    PROJECT_MCP_FILENAME,
    ProjectIdentityView,
    resolve_identity_view,
    sidecar_url,
)
from .stdio_proxy import BackendSpec, probe_backend, run_proxy
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
        managed = any(_is_launcher_entry(name, entry) for name, entry in servers.items())
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


def _backend(target: LaunchTarget, ports: Mapping[str, Any]) -> BackendSpec:
    clean = {str(k): int(v) for k, v in ports.items() if isinstance(v, int) or str(v).isdigit()}
    return BackendSpec(sidecar_url(target.spec, clean), target.spec["transport"], target.service)


def find_backend(
    target: LaunchTarget, *, registry_path: Optional[Path] = None
) -> Optional[BackendSpec]:
    """The newest ``running`` registry record for this worktree and service."""
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


def _lifecycle_env(env: Optional[Mapping[str, str]], catalog: Mapping[str, Any]) -> Dict[str, str]:
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
            return LaunchError(str(finding["code"]), f"{message}; run dopemux mcp doctor")
    for svc in getattr(result, "services", None) or []:
        for finding in svc.get("findings") or []:
            if finding.get("severity") in {"ERROR", "FAIL"} and finding.get("code"):
                return LaunchError(str(finding["code"]), str(finding.get("message") or ""))
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
        if svc.get("service") == target.service and isinstance(svc.get("ports"), Mapping):
            return _backend(target, svc["ports"])
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


def _build_image_if_missing(target: LaunchTarget) -> None:
    if target.spec.get("management_model") != "compose-service":
        return
    product = dr.product_root()
    env = dr.env_with_compose_interpolation(product=product, scrub_ambient=True)
    image = dr.compose_image_name(target.compose_project, target.service)
    if dr.docker_image_exists(image, env=env) is not False:
        return
    override, env_file = dr.compose_build_inputs(target.runtime_dir)
    command = dr.compose_build_command(
        product=product,
        override_path=override,
        env_file=env_file,
        project_name=target.compose_project,
        services=[target.service],
    )
    log_path = target.runtime_dir / "build.log"
    with open(log_path, "ab") as log:  # append: conport and dope-memory may build at once
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=str(product),
            env=env,
            start_new_session=True,
        )
    print(f"dopemux mcp launch: building {image}; log {log_path}", file=sys.stderr)
    raise LaunchError(
        "LAUNCH_IMAGE_BUILDING", "building image; retry with /mcp reconnect all in a few minutes"
    )


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


def _orchestrator_owner_verdict(owners: List[DockerContainerInfo], target: LaunchTarget) -> None:
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
            TO_WRONG_PROJECT, f"{owner_root}; run dopemux mcp switch-project here to take it over"
        )
    raise LaunchError(TO_UNKNOWN_OWNER, "run dopemux mcp doctor")


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
        state = docker()
        owners = (
            [c for c in state.containers if TO_PORT in (c.published_ports or [])]
            if state.available
            else []
        )
        if owners:
            _orchestrator_owner_verdict(owners, target)
            return TO_BACKEND
        if not port_is_free(TO_PORT):
            raise LaunchError(TO_UNKNOWN_OWNER, "run dopemux mcp doctor")
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
    return _wait_for(TO_BACKEND, probe=probe, deadline=deadline, clock=clock, sleep=sleep)


# --- attach (D8; Task 5 moves these to reap.py and re-exports them) --------------


def attach(runtime_dir: Path) -> Path:
    """Write ``<runtime_dir>/attached/<pid>`` for this launcher."""
    record = Path(runtime_dir) / "attached" / str(os.getpid())
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(f"{os.getpid()}\n", encoding="utf-8")
    return record


def detach(path: Path) -> None:
    """Remove an attach record; already gone is fine."""
    with contextlib.suppress(FileNotFoundError):
        Path(path).unlink()


# --- launch -----------------------------------------------------------------------


def _load_catalog() -> Dict[str, Any]:
    import click

    from dopemux.commands.mcp_commands import _load_catalog as load

    try:
        return load()
    except click.ClickException as exc:
        raise LaunchError("LAUNCH_CATALOG_INVALID", exc.format_message()) from None


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
    reaper: Callable[[], None] = lambda: None,
) -> int:
    """Run the launcher for ``service``; returns the process exit code.

    ``env`` defaults to ``os.environ`` as it is when called.
    """
    if env is None:
        env = os.environ
    record: Optional[Path] = None
    try:
        # stdout is the MCP channel: nothing before the proxy may print there.
        with contextlib.redirect_stdout(sys.stderr):
            launch_root = resolve_launch_root(root, cwd=_process_cwd(), service=service)
            target = build_target(
                launch_root, service, catalog=_load_catalog(), registry_path=registry_path
            )
            record = attach(target.runtime_dir)
            reaper()
            wait_s = _wait_seconds(env)
            if service == TO_SERVICE:
                backend = ensure_orchestrator(target, wait_s=wait_s, env=env)
            else:
                backend = ensure_backend(target, wait_s=wait_s, env=env)
        return run_proxy(backend)
    except LaunchError as exc:
        print(f"{exc.code}: {exc.remedy}", file=sys.stderr, flush=True)
        return EXIT_REFUSED
    finally:
        if record is not None:
            detach(record)
