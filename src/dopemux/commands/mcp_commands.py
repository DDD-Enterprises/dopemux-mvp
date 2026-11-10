"""
MCP Server Management Commands

Commands for starting, stopping, and monitoring MCP Docker servers
(``start``/``stop``/``up``/``down``/``status``/``logs``/``start-all``), plus MCP
config scaffolding driven by repo-local or bundled ``mcp_catalog.yaml`` data
(``init``/``repair-config``/``fleet``/``add``/``remove``/``list``/``doctor``/
``sync-globals``), plus a docker-down tool-surface snapshot builder
(``snapshot-tools`` — see ``dopemux.mcp.tool_snapshot``).

The ``servers`` group is an alias for ``mcp`` for backward compatibility.
"""

import asyncio
import hashlib
import importlib.resources
import json
import os
import re
import shutil
import socket
import sys
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Callable, Dict, List, Mapping, NoReturn, Optional, Tuple, TypeVar
from urllib.parse import urlparse

import click
import yaml

from ..auth import AuthError, get_token
from ..coldstart.network import ensure_docker_networks
from ..console import console
from ..mcp.project_identity import ProjectIdentityError, resolve_project_identity
from ..worktree_commands import get_repo_root


# desktop-commander and exa are quarantined (lifecycle: decision-required)
# and excluded from the default set; start them explicitly via --services.
DEFAULT_MCP_SERVICES = {
    "adhd-engine",
    "conport",
    "dope-context",
    "dope-memory",
    "dopecon-bridge",
    "gptr-mcp",
    "leantime-bridge",
    "litellm",
    "pal",
    "serena",
    "task-orchestrator",
}


def _compose_path() -> Path:
    return Path.cwd() / "compose.yml"


def _compose_services(compose_path: Path | None = None) -> set[str]:
    """Return service names declared by the active compose file."""
    path = compose_path or _compose_path()
    if not path.exists():
        return set(DEFAULT_MCP_SERVICES)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise click.ClickException(f"Invalid compose file {path}: {exc}") from exc

    services = data.get("services", {}) if isinstance(data, dict) else {}
    if not isinstance(services, dict):
        raise click.ClickException(f"Invalid compose file {path}: services must be a mapping")
    return {str(name) for name in services}


def _parse_services(services: str | None, *, allowed: set[str] | None = None) -> list[str]:
    parsed = [svc.strip() for svc in (services or "").split(",") if svc.strip()]
    if not parsed:
        return []

    allowed_services = allowed or _compose_services()
    invalid = sorted(set(parsed) - allowed_services)
    if invalid:
        valid_hint = ", ".join(sorted(allowed_services))
        raise click.ClickException(
            f"Unknown compose service(s): {', '.join(invalid)}. Valid services: {valid_hint}"
        )
    return parsed


@click.group()
def mcp():
    """
    🔬 Neural Architecture: Command the MCP infrastructure

    Manages the Docker-based Model Context Protocol servers. These daemons 
    (ConPort, PAL, Serena, etc.) provide the underlying neural architecture 
    for the cockpit's tool capabilities and semantic context management.
    """


def _lifecycle_repo_option():
    return click.option(
        "--repo",
        "repo_arg",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
        default=None,
        help="Target repo/worktree (default: git top-level of cwd). Works without compose.yml in the target.",
    )


_F = TypeVar("_F", bound=Callable[..., Any])


def _trust_env_option() -> Callable[[_F], _F]:
    return click.option(
        "--trust-env",
        "trust_env",
        is_flag=True,
        default=False,
        help=(
            "Let ambient DOPEMUX_*/TASK_ORCHESTRATOR_* environment variables override "
            "the checkout's git identity (default: identity comes from git only)."
        ),
    )


def _lifecycle_process_env(trust_env: bool) -> Dict[str, str]:
    """``os.environ`` for the lifecycle, minus ``AMBIENT_SCRUB_VARS`` unless ``--trust-env``.

    A shell that sourced another checkout's env file carries its identity, port
    and tenant exports; ports an env names win over the lease registry, so they
    must not reach the lifecycle by default (D3, final review M6).
    """
    from dopemux.mcp.docker_runtime import AMBIENT_SCRUB_VARS

    env = dict(os.environ)
    if not trust_env:
        for name in AMBIENT_SCRUB_VARS:
            env.pop(name, None)
    return env


def _lifecycle_services_option():
    return click.option(
        "--services",
        "services",
        default=None,
        help="Comma-separated project-scoped services (conport,dope-memory,task-orchestrator).",
    )


def _git_toplevel(path: Path) -> Path:
    """Git top-level of ``path`` (any directory inside a checkout); ``path`` itself outside git.

    An explicit ``--repo ./src`` must act on the enclosing checkout, as the
    launcher does (it normalizes its root with ``git rev-parse --show-toplevel``).
    """
    resolved = Path(path).expanduser().resolve()
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=resolved,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return resolved
    top = proc.stdout.strip()
    if proc.returncode == 0 and top:
        return Path(top).resolve()
    return resolved


def _run_lifecycle_cli(
    operation: str,
    *,
    repo_arg: Optional[Path],
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
    trust_env: bool = False,
) -> None:
    """Shared entry for start/stop/restart/status reconciler."""
    from dopemux.mcp.lifecycle import format_lifecycle_human, run_lifecycle

    # An explicit --repo may be a subdirectory: the checkout root owns .mcp.json,
    # the envrc and the repo-local catalog (as for the launcher), so both the
    # catalog and the lifecycle run use it.
    target_root = _git_toplevel(repo_arg) if repo_arg is not None else None
    catalog = _load_catalog(target_root) if target_root is not None else _load_catalog()
    svc_list = [s.strip() for s in (services or "").split(",") if s.strip()] or None
    result = run_lifecycle(
        operation,
        repo=target_root,
        services=svc_list,
        catalog=catalog,
        dry_run=dry_run,
        process_env=_lifecycle_process_env(trust_env),
        trust_env=trust_env,
    )
    if json_output:
        sys.stdout.write(result.to_json())
    else:
        text = format_lifecycle_human(result)
        if result.status in {"PASS", "PLANNED"}:
            console.logger.info(f"[success]{text.rstrip()}[/success]")
        elif result.status in {"PASS_WITH_WARNINGS"}:
            console.logger.info(f"[warning]{text.rstrip()}[/warning]")
        elif result.status in {"FAIL", "BLOCKED"}:
            console.logger.info(f"[error]{text.rstrip()}[/error]")
        else:
            console.logger.info(f"[info]{text.rstrip()}[/info]")
    if result.exit_code:
        sys.exit(result.exit_code)


@mcp.command("start")
@_lifecycle_repo_option()
@_trust_env_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="Plan only; no Docker mutations, no registry writes.")
@click.option("--json", "json_output", is_flag=True, help="Emit lifecycle JSON report.")
def mcp_start_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """
    🚀 Start project-scoped MCP sidecars (repo-aware reconciler)

    Starts conport / dope-memory / task-orchestrator for the target repo with
    unique names, labels, absolute memory volumes, and runtime registry updates.
    Does not use the unsafe env-injection compose pattern.
    """
    _run_lifecycle_cli(
        "start",
        repo_arg=repo_arg,
        services=services,
        dry_run=dry_run,
        json_output=json_output,
        trust_env=trust_env,
    )


@mcp.command("stop")
@_lifecycle_repo_option()
@_trust_env_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="Plan only; do not stop containers.")
@click.option("--json", "json_output", is_flag=True, help="Emit lifecycle JSON report.")
def mcp_stop_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """
    🛑 Stop Dopemux-managed MCP sidecars for a target repo

    Stops only containers with dopemux.managed=true and matching project labels
    (or registry-known task-orchestrator wrappers). Never stops unlabeled strangers.
    """
    _run_lifecycle_cli(
        "stop",
        repo_arg=repo_arg,
        services=services,
        dry_run=dry_run,
        json_output=json_output,
        trust_env=trust_env,
    )


@mcp.command("restart")
@_lifecycle_repo_option()
@_trust_env_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="Plan stop+start without mutations.")
@click.option("--json", "json_output", is_flag=True, help="Emit lifecycle JSON report.")
def mcp_restart_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """♻️ Restart project-scoped MCP sidecars (safe stop then start)."""
    _run_lifecycle_cli(
        "restart",
        repo_arg=repo_arg,
        services=services,
        dry_run=dry_run,
        json_output=json_output,
        trust_env=trust_env,
    )


@mcp.command("launch")
@click.argument("service")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=None,
    help="Checkout to serve (default: git top-level of the working directory).",
)
@click.option(
    "--wait",
    type=float,
    default=None,
    help="Seconds to wait for a starting sidecar (default: $DOPEMUX_LAUNCH_WAIT, else 25).",
)
def mcp_launch_cmd(service: str, root: Optional[Path], wait: Optional[float]):
    """Stdio MCP entry for SERVICE: find or start this checkout's sidecar, then proxy.

    This is the command `.mcp.json` launcher entries run; MCP clients start it,
    people rarely do. Refusals print one `CODE: remedy` line on stderr and exit 3.
    """
    from dopemux.mcp.launcher import WAIT_ENV, launch

    env = dict(os.environ)
    if wait is not None:
        env[WAIT_ENV] = str(wait)
    sys.exit(launch(service, root=root, env=env))


@mcp.command("reap")
@click.option(
    "--dry-run/--apply",
    default=True,
    help="List what would be reaped (default) or stop it, release its leases and remove its runtime dir.",
)
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def mcp_reap_cmd(dry_run: bool, json_output: bool):
    """Reap sidecars of removed or idle worktrees (design D8).

    An instance is reaped when no launcher is attached AND its worktree no longer
    exists, or it has been idle (last launcher detached) for 20 minutes; never while
    a detached image build is running in its runtime dir. A launcher killed outright
    leaves a dead attach record; its attach time counts as the detach. Containers are
    matched by dopemux labels plus a registry entry; project and singleton scope
    (the task-orchestrator) are never touched. A runtime dir
    that a launcher marked (instance.json) but that never got a sidecar (a
    build-only launch) is removed once its worktree is gone and no launcher or
    detached image build still uses it; never for idleness. Nothing is planned
    while the runtime registry file is missing (a start creates it). --apply ignores the
    automatic-reaping kill switch (file reap.disabled or DOPEMUX_MCP_REAP=0).
    """
    import time

    from dopemux.mcp import reap
    from dopemux.mcp.port_leases import PortLeaseRegistry, default_lease_registry_path
    from dopemux.mcp.runtime_registry import RuntimeRegistry

    disabled = reap.reaping_disabled_reason()
    if disabled and not dry_run:
        click.echo(
            f"Note: automatic reaping is disabled ({disabled}); --apply runs anyway.", err=True
        )

    def fail(message: str) -> NoReturn:
        if json_output:
            click.echo(json.dumps({"dry_run": dry_run, "error": message, "candidates": []}))
        else:
            click.echo(f"{message}; nothing reaped.", err=True)
        sys.exit(1)

    registry = RuntimeRegistry.load(reap.runtime_registry_path())
    if registry.parse_status == "ERROR":
        fail(f"Runtime registry unreadable ({registry.error})")
    docker = reap.inspect_all_managed_containers()
    if not docker.available:
        fail(f"Docker unavailable ({docker.error})")

    candidates = reap.plan_reap(
        registry=registry,
        containers=docker.containers,
        now=time.time(),
        lease_registry=PortLeaseRegistry.load(default_lease_registry_path()),
    )
    report = None if dry_run else reap.apply_reap(candidates, runner=reap.run_cmd)

    if json_output:
        payload = {
            "dry_run": dry_run,
            "automatic_reaping_disabled": disabled,
            "candidates": [c.to_dict() for c in candidates],
            "reaped": [c.to_dict() for c in report.reaped] if report else [],
            "skipped": report.to_dict()["skipped"] if report else [],  # keeps skip_reason
            "errors": list(report.errors) if report else [],
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        if not candidates:
            click.echo("Nothing to reap.")
        for c in candidates:
            click.echo(
                f"{'would reap' if dry_run else 'reap'} {c.project_id}/{c.worktree_hash} "
                f"({c.reason}) {c.worktree_root} containers={','.join(c.container_ids)}"
            )
        if report:
            click.echo(f"Reaped {len(report.reaped)} of {len(candidates)}.")
            for line in report.errors:
                click.echo(f"error: {line}", err=True)
    if report and report.errors:
        sys.exit(1)


@mcp.command("switch-project")
@_lifecycle_repo_option()
@click.option("--yes", is_flag=True, help="Stop the current owner without asking.")
def mcp_switch_project_cmd(repo_arg: Optional[Path], yes: bool):
    """Move the reserved task-orchestrator (:7890) to this project.

    Stops and removes the managed task-orchestrator container serving another
    project, then starts this project's through the lifecycle. Refuses when
    :7890 is held by anything that is not a managed task-orchestrator container.
    The confirmation is asked without holding the host-wide :7890 lock; the
    owner is then re-inspected under the lock and must be the same container.
    The stopped owner's registry entry is marked stopped (registry lock inside
    the reserved lock).
    """
    from dopemux.mcp import docker_inspect as di
    from dopemux.mcp import docker_runtime as dr
    from dopemux.mcp import lifecycle as lc
    from dopemux.mcp.locks import reserved_port_lock, save_state_locked
    from dopemux.mcp.runtime_registry import RuntimeRegistry, default_registry_path
    from dopemux.mcp.runtime_state import resolve_identity_view
    from dopemux.mcp.task_orchestrator_identity import identity_from_docker_labels, match_target

    port = 7890

    def refuse(message: str) -> NoReturn:
        click.echo(message, err=True)
        sys.exit(1)

    # An explicit --repo may be a subdirectory of the checkout: act on its root.
    target = _git_toplevel(lc.resolve_target_repo(repo_arg))
    identity = resolve_identity_view(target)
    if not identity.project_id or not identity.project_root:
        refuse(f"Cannot resolve the project identity of {target}; run dopemux mcp doctor")
    catalog = _load_catalog(target)

    def inspect_owner() -> Tuple[Any, Optional[str]]:
        """(owner container or None when :7890 is free, its project root when foreign)."""
        state = di.inspect_running_containers()
        if not state.available:
            refuse(f"Docker unavailable ({state.error}); cannot identify the :{port} owner")
        owners = [c for c in state.containers if port in (c.published_ports or [])]
        if not owners:
            if not lc._port_is_free(port):
                refuse(
                    f":{port} is held by a process that is not a managed task-orchestrator "
                    "container; refusing"
                )
            return None, None
        owner = owners[0]
        labels = owner.labels or {}
        if (
            len(owners) != 1
            or labels.get("dopemux.managed") != "true"
            or labels.get("dopemux.service") != "task-orchestrator"
        ):
            refuse(
                f":{port} is held by {owner.name}, which is not a managed "
                "task-orchestrator container; refusing"
            )
        observed = identity_from_docker_labels(labels, port=port, container_name=owner.name)
        verdict = match_target(
            observed, project_id=identity.project_id, project_root=identity.project_root
        )
        if verdict == "OK":
            return owner, None
        return owner, observed.project_root or observed.project_id or "an unknown project"

    def already_serves(owner: Any) -> None:
        click.echo(
            f"task-orchestrator on :{port} already serves {identity.project_root} ({owner.name})"
        )

    # Phase 1, no lock: look, and ask. A prompt must never hold the host-wide lock.
    owner, foreign_root = inspect_owner()
    if owner is not None and foreign_root is None:
        already_serves(owner)
        return
    if owner is not None:
        click.echo(f"task-orchestrator on :{port} serves {foreign_root} ({owner.name})")
        if not yes:
            click.confirm(
                f"Stop it and start {identity.project_root}'s task-orchestrator?",
                default=False,
                abort=True,
            )
    else:
        click.echo(f":{port} is free")

    # Phase 2, under the lock: act only on what was confirmed.
    with reserved_port_lock(port):
        current, current_foreign = inspect_owner()
        if current is not None and current_foreign is None:
            already_serves(current)
            return
        if current is not None and (owner is None or current.id != owner.id):
            refuse(
                f":{port} owner changed since it was inspected "
                f"({owner.name if owner is not None else 'free'} -> {current.name}); "
                "rerun dopemux mcp switch-project"
            )
        if current is not None:
            for verb in ("stop", "rm"):
                res = dr.run_cmd(["docker", verb, current.id], timeout=60)
                if res.exit_code != 0:
                    detail = (res.stderr or res.stdout or "").strip()
                    refuse(f"docker {verb} {current.id} failed: {detail}")
            owner_id = (current.labels or {}).get("dopemux.project_id") or ""
            stopped_name = current.name

            def mark_owner_stopped(reg: Any) -> None:
                now = datetime.now(timezone.utc).isoformat()
                for inst in reg.instances():
                    if inst.get("service") != "task-orchestrator" or inst.get("status") == "stopped":
                        continue
                    if (owner_id and inst.get("project_id") == owner_id) or stopped_name in (
                        inst.get("container_names") or []
                    ):
                        inst["status"] = "stopped"
                        inst["updated_at"] = now

            error = save_state_locked(RuntimeRegistry, default_registry_path(), mark_owner_stopped)
            if error:
                click.echo(f"warning: previous owner's registry entry not updated: {error}", err=True)
        click.echo(f"Starting task-orchestrator for {identity.project_root}")
        result = lc.run_lifecycle(
            "start",
            repo=target,
            services=["task-orchestrator"],
            catalog=catalog,
            process_env=_lifecycle_process_env(False),
        )
    if result.exit_code:
        for finding in result.blocking_findings or []:
            click.echo(f"{finding.get('code')}: {finding.get('message')}", err=True)
        click.echo(f"task-orchestrator start failed (status {result.status})", err=True)
        sys.exit(result.exit_code)
    click.echo(f"task-orchestrator on :{port} now serves {identity.project_root}")


@mcp.command("up")
@click.option("--all", "all_services", is_flag=True, help="🚀 Boot Fleet: Start every configured MCP service simultaneously.")
@click.option("--services", "services", help="🎯 Targeted Ignition: Comma-separated list of specific MCP services to ignite.")
@_lifecycle_repo_option()
@_trust_env_option()
@click.option("--dry-run", is_flag=True, help="When --repo is set: plan-only reconciler start.")
@click.option("--json", "json_output", is_flag=True, help="When --repo is set: JSON lifecycle report.")
def mcp_up_cmd(
    all_services: bool,
    services: str,
    repo_arg: Optional[Path],
    trust_env: bool,
    dry_run: bool,
    json_output: bool,
):
    """
    ⚡ Ignite Engine: Deploy MCP servers

    With ``--repo``: compatibility alias for ``dopemux mcp start --repo``.
    Without ``--repo``: legacy cwd compose behavior against the default
    service set (or ``--services`` if given).
    ``--dry-run`` / ``--json`` only apply with ``--repo`` (ignored otherwise).
    """
    if repo_arg is not None:
        _run_lifecycle_cli(
            "start",
            repo_arg=repo_arg,
            services=services,
            dry_run=dry_run,
            json_output=json_output,
            trust_env=trust_env,
        )
        return
    try:
        if all_services or not services:
            # Derive from the default set so `up` stays symmetric with `down`
            # (previously shelled out to the now-removed
            # scripts/start-all-mcp-servers.sh — see design P-22 safe subset).
            svc_list = sorted(DEFAULT_MCP_SERVICES & _compose_services())
            if not svc_list:
                svc_list = sorted(DEFAULT_MCP_SERVICES)
        else:
            svc_list = _parse_services(services)
        explicit_services = bool(services) and not all_services
        token_set = bool(str(os.environ.get("DOPECON_BRIDGE_TOKEN") or "").strip())
        if "task-orchestrator" in svc_list and not token_set:
            if explicit_services:
                console.logger.error(
                    "[error]DOPECON_BRIDGE_TOKEN is required to start compose "
                    "task-orchestrator. For the wrapper-singleton on :7890 use "
                    "`dopemux mcp start --repo .` instead.[/error]"
                )
                sys.exit(1)
            svc_list = [s for s in svc_list if s != "task-orchestrator"]
            console.logger.info(
                "[warning]Skipping compose task-orchestrator: DOPECON_BRIDGE_TOKEN "
                "is unset. Use `dopemux mcp start --repo .` for the "
                "wrapper-singleton on :7890.[/warning]"
            )
        if not svc_list:
            console.logger.info(
                "[warning]No compose services left to start after skipping "
                "task-orchestrator. Not invoking `docker compose up`.[/warning]"
            )
            return
        from ..mcp.docker_runtime import env_with_compose_interpolation

        ensure_docker_networks(["dopemux-network"], runner=subprocess.run)
        cmd = ["docker", "compose", "-f", "compose.yml", "up", "-d", "--build"] + svc_list
        console.logger.info(f"[info]{' '.join(cmd)}[/info]")
        subprocess.run(
            cmd,
            check=True,
            env=env_with_compose_interpolation(
                host_path_defaults="dope-context" not in svc_list
            ),
        )
        console.logger.info("[success]MCP servers started[/success]")
    except (CalledProcessError, FileNotFoundError, RuntimeError) as exc:
        console.logger.error(f"[error]Failed to start MCP servers: {exc}[/error]")
        sys.exit(1)


@mcp.command("down")
@_lifecycle_repo_option()
@_trust_env_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="When --repo is set: plan-only stop.")
@click.option("--json", "json_output", is_flag=True, help="When --repo is set: JSON lifecycle report.")
def mcp_down_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """
    💧 Cool Down Cores: Terminate MCP containers

    With ``--repo``: compatibility alias for ``dopemux mcp stop --repo``.
    Without ``--repo``: legacy cwd compose rm behavior.
    ``--dry-run`` / ``--json`` only apply with ``--repo`` (ignored otherwise).
    """
    if repo_arg is not None:
        _run_lifecycle_cli(
            "stop",
            repo_arg=repo_arg,
            services=services,
            dry_run=dry_run,
            json_output=json_output,
            trust_env=trust_env,
        )
        return
    try:
        # Derive from the default set so `down` stays symmetric with `up`
        # (previously a hardcoded list that omitted several running services).
        from ..mcp.docker_runtime import env_with_compose_interpolation

        mcp_services = sorted(DEFAULT_MCP_SERVICES & _compose_services())
        if not mcp_services:
            mcp_services = sorted(DEFAULT_MCP_SERVICES)
        subprocess.run(
            ["docker", "compose", "-f", "compose.yml", "rm", "-f", "-s", "-v"] + mcp_services,
            check=True,
            env=env_with_compose_interpolation(),
        )
        console.logger.info("[success]MCP servers stopped[/success]")
    except (CalledProcessError, FileNotFoundError) as exc:
        console.logger.error(f"[error]Failed to stop MCP servers: {exc}[/error]")
        sys.exit(1)


@mcp.command("status")
@_lifecycle_repo_option()
@_trust_env_option()
@click.option("--json", "json_output", is_flag=True, help="Emit repo-aware status JSON (registry+docker+probes).")
@click.option(
    "--legacy-compose",
    is_flag=True,
    help="Force legacy `docker compose ps` from cwd (ignores --repo).",
)
def mcp_status_cmd(
    repo_arg: Optional[Path], trust_env: bool, json_output: bool, legacy_compose: bool
):
    """
    📊 Diagnostic HUD: Interrogate MCP service health

    Default / with ``--repo`` / ``--json``: repo-aware status (registry + Docker + probes).
    ``--legacy-compose``: previous cwd `docker compose ps` behavior.
    """
    if legacy_compose:
        from ..mcp.docker_runtime import env_with_compose_interpolation

        try:
            subprocess.run(
                ["docker", "compose", "-f", "compose.yml", "ps"],
                check=True,
                env=env_with_compose_interpolation(),
            )
        except (CalledProcessError, FileNotFoundError):
            sys.exit(1)
        return

    # Prefer reconciler status when --repo/--json or target has .mcp.json
    use_reconciler = (
        repo_arg is not None
        or json_output
        or (Path.cwd() / PROJECT_MCP_FILENAME).exists()
        or (Path.cwd() / ENVRC_FILENAME).exists()
    )
    if use_reconciler:
        _run_lifecycle_cli(
            "status",
            repo_arg=repo_arg,
            services=None,
            dry_run=False,
            json_output=json_output,
            trust_env=trust_env,
        )
        return
    from ..mcp.docker_runtime import env_with_compose_interpolation

    try:
        subprocess.run(
            ["docker", "compose", "-f", "compose.yml", "ps"],
            check=True,
            env=env_with_compose_interpolation(),
        )
    except (CalledProcessError, FileNotFoundError):
        sys.exit(1)


@mcp.command("logs")
@click.option("--service", "service", help="📊 Telemetry Filter: Focus the log stream on a specific MCP daemon.")
def mcp_logs_cmd(service: str):
    """
    🧠 Tap Telemetry: Stream real-time log data from MCP services

    Enables direct observation of the signal exchange between the cockpit 
    and its distributed toolset for granular ritual debugging.
    """
    from ..mcp.docker_runtime import env_with_compose_interpolation

    try:
        if service:
            svc_list = _parse_services(service)
            cmd = ["docker", "compose", "-f", "compose.yml", "logs", "-f"] + svc_list
        else:
            cmd = ["docker", "compose", "-f", "compose.yml", "logs", "-f"]
        console.logger.info(f"[info]{' '.join(cmd)}[/info]")
        subprocess.run(cmd, check=True, env=env_with_compose_interpolation())
    except (CalledProcessError, FileNotFoundError):
        sys.exit(1)


@mcp.command("start-all")
@click.option("--verify", "-v", is_flag=True, help="✅ Verify Pulse: Execute high-fidelity health checks after ignition.")
def mcp_start_all_cmd(verify: bool):
    """
    🧙 Summon Ecosystem: Ignite the complete DØPEMÜX stack

    Initiates the full ritual environment: MCP servers, Integration Bridge, 
    Task Orchestrator, and application services. Primes the cockpit for 
    intensive work log sessions.
    """
    try:
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "start-all.sh"

        if not script_path.exists():
            console.logger.info(f"[error]start-all.sh not found at {script_path}[/error]")
            console.logger.info("[warning]Falling back to manual startup...[/warning]")

            # Same "network not found on a clean host" class of bug that
            # `mcp up` already had fixed — ensure the external network exists
            # before either compose invocation below (idempotent).
            ensure_docker_networks(["dopemux-network"], runner=subprocess.run)

            from ..mcp.docker_runtime import env_with_compose_interpolation

            console.logger.info("[info]Starting MCP servers...[/info]")
            # Whole-file `up` includes dope-context: never default the host
            # path variables, so the `:?` guard keeps failing closed.
            compose_env = env_with_compose_interpolation(
                host_path_defaults=False
            )
            subprocess.run(
                ["docker", "compose", "-f", "compose.yml", "up", "-d"],
                check=True,
                env=compose_env,
            )

            # NOTE: the legacy docker/conport-kg integration-bridge is dead
            # code (kill-list per the MCP fleet audit) and must not be
            # resurrected here.

            console.logger.info("[info]Starting Task Orchestrator...[/info]")
            subprocess.run(
                ["docker", "compose", "-f", "compose.yml", "--profile", "manual", "up", "-d", "task-orchestrator"],
                check=True,
                env=compose_env,
            )

            console.logger.info("[success]All services started[/success]")
        else:
            cmd = ["bash", str(script_path)]
            if verify:
                cmd.append("--verify")
            subprocess.run(cmd, check=True)

    except (CalledProcessError, FileNotFoundError, RuntimeError):
        console.logger.error("[error]Failed to start all services[/error]")
        console.logger.info("[warning]Try: docker ps to see running containers[/warning]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# `servers` group — alias for `mcp`
# ---------------------------------------------------------------------------

@click.group()
def servers():
    """
    🔬 Cockpit Alias: Alternative entry point for MCP operations

    Inherits all Model Context Protocol management capabilities. Provides 
    a secondary routing path for managing the neural server fleet.
    """


@servers.command("up")
@click.option("--all", "all_services", is_flag=True, help="🚀 Boot Fleet: Start every configured MCP service simultaneously.")
@click.option("--services", "services", help="🎯 Targeted Ignition: Comma-separated list of specific MCP services to ignite.")
@click.option("--repo", "repo_arg", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=None)
@_trust_env_option()
@click.option("--dry-run", is_flag=True)
@click.option("--json", "json_output", is_flag=True)
def servers_up_cmd(
    all_services: bool,
    services: str,
    repo_arg: Optional[Path],
    trust_env: bool,
    dry_run: bool,
    json_output: bool,
):
    """
    ⚡ Ignite Engine (Alias): Deploy MCP servers via Docker Compose
    """
    mcp_up_cmd.callback(all_services, services, repo_arg, trust_env, dry_run, json_output)


@servers.command("down")
@click.option("--repo", "repo_arg", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=None)
@click.option("--services", "services", default=None)
@_trust_env_option()
@click.option("--dry-run", is_flag=True)
@click.option("--json", "json_output", is_flag=True)
def servers_down_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """
    💧 Cool Down Cores (Alias): Terminate MCP containers and volumes
    """
    mcp_down_cmd.callback(repo_arg, trust_env, services, dry_run, json_output)


@servers.command("status")
@click.option("--repo", "repo_arg", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=None)
@click.option("--json", "json_output", is_flag=True)
@click.option("--legacy-compose", is_flag=True)
@_trust_env_option()
def servers_status_cmd(
    repo_arg: Optional[Path], json_output: bool, legacy_compose: bool, trust_env: bool
):
    """
    📊 Diagnostic HUD (Alias): Interrogate MCP service health
    """
    mcp_status_cmd.callback(repo_arg, trust_env, json_output, legacy_compose)


@servers.command("logs")
@click.option("--service", "service", help="📊 Telemetry Filter: Focus the log stream on a specific MCP daemon.")
def servers_logs_cmd(service: str):
    """
    🧠 Tap Telemetry (Alias): Stream real-time log data
    """
    mcp_logs_cmd.callback(service)


# ---------------------------------------------------------------------------
# Catalog-driven config management
# ---------------------------------------------------------------------------
#
# These subcommands read ``mcp_catalog.yaml`` at the repo root and use it to
# manage two distinct surfaces:
#
#   ~/.claude.json mcpServers   — singletons shared across all worktrees
#   <worktree>/.mcp.json        — per-worktree servers with env-var ports
#
# Per-worktree port allocation is deterministic:
#     port = base + (sha1(worktree_abspath)[:4]_hex % 100)
# giving each worktree a stable port offset in a 100-port window per service.

CATALOG_FILENAME = "mcp_catalog.yaml"
CATALOG_ENV_VAR = "DOPEMUX_MCP_CATALOG"
DEFAULT_CATALOG_RESOURCE = "default_catalog.yaml"
PROJECT_MCP_FILENAME = ".mcp.json"
ENVRC_FILENAME = ".envrc.dopemux-mcp"   # sourced from .envrc; keeps generated content separate


def _catalog_path(repo: Optional[Path] = None) -> Optional[Path]:
    """Locate an explicit or repo-local MCP catalog path, if present.

    ``repo`` (the launcher's ``--root`` checkout) replaces the git top-level of
    the current directory as the place to look for a repo-local catalog.
    """
    explicit = os.environ.get(CATALOG_ENV_VAR)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise click.ClickException(
                f"{CATALOG_ENV_VAR} points to a missing catalog: {path}"
            )
        return path

    root = str(repo) if repo is not None else get_repo_root(fallback_cwd=False)
    if root:
        candidate = Path(root) / CATALOG_FILENAME
        if candidate.exists():
            return candidate
    return None


def _load_catalog(repo: Optional[Path] = None) -> Dict[str, Any]:
    catalog_path = _catalog_path(repo) if repo is not None else _catalog_path()
    if catalog_path:
        with catalog_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    else:
        try:
            resource = importlib.resources.files("dopemux.mcp").joinpath(
                DEFAULT_CATALOG_RESOURCE
            )
            with resource.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except FileNotFoundError as exc:
            raise click.ClickException(
                f"Bundled MCP catalog `{DEFAULT_CATALOG_RESOURCE}` is missing."
            ) from exc

    if data.get("version") != 1:
        raise click.ClickException(
            f"Unsupported catalog version: {data.get('version')!r}. Expected 1."
        )
    if "servers" not in data:
        raise click.ClickException("Catalog missing required `servers` block.")
    return data


def _instance_id(worktree_path: str) -> str:
    """Short stable hash of the worktree absolute path (4 hex chars)."""
    return hashlib.sha1(str(Path(worktree_path).resolve()).encode("utf-8")).hexdigest()[:4]


def _port_for(worktree_path: str, base_port: int) -> int:
    """Deterministic port within `[base, base+99]` keyed by worktree path.

    The 100-slot ceiling means inter-worktree port collisions become probable
    by birthday-paradox math past ~12 active worktrees and likely past ~50.
    `_allocate_ports` only catches *intra*-worktree collisions; cross-worktree
    collisions surface at runtime (port already in use). Widen the modulus
    here and bump `default_port_base` spacing in mcp_catalog.yaml if you need
    more headroom.
    """
    offset = int(_instance_id(worktree_path), 16) % 100
    return base_port + offset


def _port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    """True if nothing is currently bound on (host, port).

    Note: `doctor` inverts this (`not _port_is_free(port)`) because a *listening*
    port means the worktree's MCP server is actually running — the opposite of
    what `init`/`list` want, which is to confirm a port is *available* before
    claiming it.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) != 0
    finally:
        sock.close()


# Wave 2A: the memory servers reach runners through the authenticating stdio
# route (`dopemux.mcp.http_stdio_bridge --server NAME --principal P`), which
# finds the checkout's ports in `.envrc.dopemux-mcp` and reads P's token from
# the keychain. The bridge is the same in every worktree, so these entries are
# rendered from this table, not from the catalog's per-worktree `url_template`
# (which still feeds health probes, port allocation and compose alignment).
# In Wave 2A only the Codex config uses it by default; Claude Code's bridge
# entry (`_render_claude_memory_bridge_entry`) exists but is not wired in.
#
# The interpreter is the bare name `python`, the same choice the legacy
# `--base-url` entries make (config/manager.py): a fixed string keeps the
# generated files, the Codex parity gate and `ensure` drift detection
# independent of which interpreter ran the generator.
MEMORY_BRIDGE_SERVERS: Tuple[str, ...] = ("conport", "dope-memory")
MEMORY_BRIDGE_PYTHON = "python"
MEMORY_BRIDGE_MODULE = "dopemux.mcp.http_stdio_bridge"
CLAUDE_MEMORY_PRINCIPAL = "runner:claude"
CODEX_MEMORY_PRINCIPAL = "runner:codex"


def _memory_bridge_command(server: str, principal: str) -> Tuple[str, List[str]]:
    """`(command, args)` that start the stdio route for one memory server."""
    return MEMORY_BRIDGE_PYTHON, ["-m", MEMORY_BRIDGE_MODULE, "--server", server, "--principal", principal]


def _render_claude_memory_bridge_entry(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Claude Code stdio entry that runs the authenticating bridge as `runner:claude`.

    Not used by default: in Wave 2A Claude Code keeps its direct HTTP/SSE
    entries from `_render_local_entry` (AMENDMENT_02); Wave 2B wires this up.
    The entry carries no `env` because the bridge reads the checkout's envrc
    itself.
    """
    if name not in MEMORY_BRIDGE_SERVERS:
        raise click.ClickException(
            f"`{name}` has no stdio bridge profile (expected one of {', '.join(MEMORY_BRIDGE_SERVERS)})."
        )
    command, args = _memory_bridge_command(name, CLAUDE_MEMORY_PRINCIPAL)
    entry: Dict[str, Any] = {"type": "stdio", "command": command, "args": args}
    if spec.get("description"):
        entry["description"] = spec["description"]
    return entry


# `client: launcher` catalog entries reach clients as a stdio `dopemux mcp launch`
# command (identity and ports resolved at connect time), never as a URL.
LAUNCHER_COMMAND = "${DOPEMUX_BIN:-dopemux}"


def _launcher_entry(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """The stdio launcher entry shape: no URL and no `env` block."""
    entry: Dict[str, Any] = {
        "type": "stdio",
        "command": LAUNCHER_COMMAND,
        "args": ["mcp", "launch", name],
    }
    if description:
        entry["description"] = description
    return entry


def _render_local_entry(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render a per-worktree catalog entry as a Claude Code .mcp.json mcpServers value.
    Uses ${VAR} placeholders so Claude Code expands them at session start.
    """
    from dopemux.mcp.fleet_catalog import catalog_client_shape

    if catalog_client_shape(spec) == "launcher":
        return _launcher_entry(name, spec.get("description"))

    transport = spec.get("transport", "http")
    entry: Dict[str, Any] = {"type": transport}

    if transport in {"http", "sse"}:
        url = spec.get("url_template") or spec.get("url")
        if not url:
            raise click.ClickException(f"Server `{name}` missing `url`/`url_template`.")
        entry["url"] = url
    elif transport == "stdio":
        entry["command"] = spec.get("command_template") or spec.get("command")
        if not entry["command"]:
            raise click.ClickException(f"Server `{name}` missing `command`/`command_template`.")
        args = spec.get("args_template") or spec.get("args") or []
        entry["args"] = list(args)
    else:
        raise click.ClickException(f"Unsupported transport `{transport}` for `{name}`.")

    env_template = spec.get("env_template") or {}
    env_keys = list(spec.get("requires_env", []) or []) + list(spec.get("optional_env", []) or [])
    env: Dict[str, str] = {k: f"${{{k}:-}}" for k in env_keys}
    env.update(env_template)   # explicit templates win over default `${VAR:-}` shape
    if env:
        entry["env"] = env

    if spec.get("description"):
        entry["description"] = spec["description"]

    return entry


def _render_global_entry(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Render a singleton catalog entry as a ~/.claude.json mcpServers value."""
    transport = spec.get("transport", "http")
    entry: Dict[str, Any] = {"type": transport}

    if transport in {"http", "sse"}:
        if not spec.get("url"):
            raise click.ClickException(f"Singleton `{name}` requires `url`.")
        entry["url"] = spec["url"]
    elif transport == "stdio":
        if not spec.get("command"):
            raise click.ClickException(f"Singleton `{name}` requires `command`.")
        entry["command"] = spec["command"]
        if spec.get("args"):
            entry["args"] = list(spec["args"])
    else:
        raise click.ClickException(f"Unsupported transport `{transport}` for `{name}`.")

    env_keys = list(spec.get("requires_env", []) or []) + list(spec.get("optional_env", []) or [])
    if env_keys:
        entry["env"] = {k: f"${{{k}:-}}" for k in env_keys}

    if spec.get("description"):
        entry["description"] = spec["description"]
    return entry


def _is_startable_global_entry(spec: Dict[str, Any]) -> bool:
    """True when a catalog entry may appear in generated startable configs.

    Excluded (ADR-MCPINT-001): `decision-required` (quarantined pending a
    follow-on decision), `planned-active` (built but not yet deployed — no
    truthful endpoint exists), `managed: false` / `transport: external`
    (host-level surfaces the repo does not manage), and `agents: none`
    (infra/PM-sync entries with no agent matrix row).
    """
    if spec.get("lifecycle") in {"decision-required", "planned-active"}:
        return False
    if spec.get("managed") is False:
        return False
    if spec.get("transport") == "external":
        return False
    if spec.get("agents") == "none":
        return False
    return True


def _build_global_mcp_servers(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Construct startable singleton MCP entries for global client config."""

    return {
        name: _render_global_entry(name, spec)
        for name, spec in catalog["servers"].items()
        if spec.get("scope") == "singleton" and _is_startable_global_entry(spec)
    }


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r") as fh:
        return json.load(fh)


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    tmp.replace(path)


def _claude_global_path() -> Path:
    return Path.home() / ".claude.json"


def _backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return path.with_suffix(path.suffix + f".backup-{stamp}")


def _singleton_reserved_ports(catalog: Dict[str, Any]) -> Dict[int, str]:
    """
    Return a map of {port: server_name} for all singleton servers that have a
    statically-declared port in the catalog.  These ports must never be assigned
    to per-worktree services regardless of what hash offset `_port_for` produces.

    Two sources of port reservation are recognised:

    1. ``url`` field — parsed via urllib (e.g. ``http://localhost:3009/mcp``).
    2. ``reserved_port`` field — an explicit integer for singletons whose MCP
       transport is ``stdio`` (e.g. ``gpt-researcher``) but whose Docker service
       still binds a host port that per-worktree services must not shadow.
    """
    from urllib.parse import urlparse as _urlparse

    reserved: Dict[int, str] = {}
    for name, spec in catalog.get("servers", {}).items():
        if spec.get("scope") != "singleton":
            continue

        # Source 1: explicit reserved_port (stdio singletons that still bind a host port)
        explicit = spec.get("reserved_port")
        if explicit is not None:
            try:
                reserved[int(explicit)] = name
            except (TypeError, ValueError):
                console.logger.warning(
                    f"[warning]mcp_catalog: singleton '{name}' has a non-integer "
                    f"reserved_port value ({explicit!r}); skipping port reservation.[/warning]"
                )

        # Source 2: url field (HTTP/SSE singletons)
        raw_url = spec.get("url")
        if raw_url:
            try:
                port = _urlparse(str(raw_url)).port
                if port:
                    reserved[port] = name
            except Exception as exc:  # noqa: BLE001
                console.logger.warning(
                    f"[warning]mcp_catalog: singleton '{name}' has an unparseable "
                    f"url ({raw_url!r}); skipping port reservation. ({exc})[/warning]"
                )
    return reserved


def _allocate_ports(
    worktree: str,
    names: List[str],
    catalog: Dict[str, Any],
    *,
    project_root: str | None = None,
    persist: bool = True,
    dry_run: bool = False,
    existing_envrc: Optional[Dict[str, str]] = None,
    is_free_fn: Any = None,
    source: str = "dopemux mcp init",
) -> Dict[str, int]:
    """
    Allocate ports for each per-worktree server via the lease registry allocator.

    Preferred ports still come from the legacy hash formula
    (``base + sha1(path)[:4] % 100``) or existing envrc values, but assignment
    only succeeds after reserved/lease/socket safety checks. Unsafe preferred
    ports are rebound within the service base search window.

    Safety rules:
    - Singleton reserved catalog ports are never assigned to project sidecars.
    - Active leases owned by other projects/worktrees are never stolen.
    - Live TCP sockets block assignment (except reuse of our own lease).
    - ``wrapper-singleton`` services use fixed ``default_port_base`` (no rebind).
    - ``dry_run=True`` / ``persist=False`` skips lease registry writes.
    """
    from dopemux.mcp.port_allocator import allocate_ports_map

    try:
        return allocate_ports_map(
            worktree,
            names,
            catalog,
            project_root=project_root,
            existing_envrc=existing_envrc,
            persist=persist and not dry_run,
            dry_run=dry_run,
            source=source,
            is_free_fn=is_free_fn,
        )
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc


def _project_env_exports(worktree: str, project_root: str) -> Dict[str, str]:
    return {
        "DOPEMUX_WORKSPACE_ID": worktree,
        "DOPEMUX_WORKSPACE_ROOT": worktree,
        "DOPEMUX_PROJECT_ROOT": project_root,
        "TASK_ORCHESTRATOR_PROJECT_ROOT": project_root,
        "DOPEMUX_INSTANCE_ID": _instance_id(worktree),
        "DOPE_MEMORY_WORKSPACE_ID": Path(worktree).name,
        "DOPE_MEMORY_INSTANCE_ID": _instance_id(worktree),
        "WORKSPACE_ID": worktree,
    }


def _write_envrc(
    envrc_path: Path,
    port_vars: Dict[str, int],
    worktree: str,
    project_root: str,
    *,
    preserve: Mapping[str, str],
) -> None:
    """Write the per-worktree env file (sourced by direnv `.envrc` or `.env.mcp` consumers).

    ``preserve`` holds tenant keys (``CONPORT_DB_*``) read from the previous file;
    they are re-emitted so ``init --force`` cannot orphan an existing database.
    """
    env_exports = _project_env_exports(worktree, project_root)
    lines = [
        "# Generated by `dopemux mcp init` for humans; nothing needs it sourced. dopemux reads it itself:",
        "# init, doctor and each sidecar start take its ports, and the first ConPort tenant resolution",
        "# adopts legacy CONPORT_DB_* from it once (legacy_envrc). Identity comes from git; re-run init to regenerate.",
        f"# Worktree: {worktree}",
        f"# Project:  {project_root}",
        f"# Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for var, value in env_exports.items():
        lines.append(f"export {var}={shlex_quote(str(value))}")
    lines.append("")
    for var, port in sorted(port_vars.items()):
        lines.append(f"export {var}={port}")
    if preserve:
        lines.append("")
        lines.append("# Preserved from the previous file (tenant keys)")
        for var, value in sorted(preserve.items()):
            lines.append(f"export {var}={shlex_quote(str(value))}")
    envrc_path.write_text("\n".join(lines) + "\n")


def _append_missing_env_exports(envrc_path: Path, exports: Dict[str, Any]) -> List[str]:
    """Append missing port exports to an existing env file without rewriting user content."""
    existing = envrc_path.read_text() if envrc_path.exists() else ""
    missing = [
        (var, value)
        for var, value in sorted(exports.items())
        if f"export {var}=" not in existing
    ]
    if not missing:
        return []

    prefix = "" if not existing or existing.endswith("\n") else "\n"
    with envrc_path.open("a") as fh:
        fh.write(prefix)
        for var, value in missing:
            fh.write(f"export {var}={shlex_quote(str(value))}\n")
    return [var for var, _ in missing]


def shlex_quote(value: str) -> str:
    """Local shlex.quote shim (avoid importing shlex into top-of-module namespace)."""
    import shlex
    return shlex.quote(value)


def _build_local_mcp_json(server_names: List[str], catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the .mcp.json contents for the given per-worktree server names."""
    servers: Dict[str, Any] = {}
    for name in server_names:
        spec = catalog["servers"].get(name)
        if not spec:
            raise click.ClickException(f"Unknown server `{name}` (not in {CATALOG_FILENAME}).")
        if spec.get("scope") != "per-worktree":
            raise click.ClickException(
                f"`{name}` is a singleton — declare it once in `~/.claude.json` via "
                f"`dopemux mcp sync-globals`, not per-worktree."
            )
        servers[name] = _render_local_entry(name, spec)
    return {"mcpServers": servers}


# ---------------------------------------------------------------------------
# Codex memory gate (Wave 2A design 5.7): replaces `--allow-sequenced`.
#
# Before `generate --apply` writes a write-capable Codex config for the memory
# servers it checks (1) that dope-memory and ConPort report log or enforce mode
# with identity-required writes (AMENDMENT_03), and (2) that a keychain token
# exists for the target runner. Any failure leaves only the preview and names
# the check.
# ---------------------------------------------------------------------------

ALLOW_SEQUENCED_REMOVED_MESSAGE = (
    "--allow-sequenced was removed in Wave 2A. The in-repo .codex/config.toml write is now "
    "gated by two checks that `dopemux mcp generate --agent-matrix --apply` runs itself: "
    "(1) the dope-memory and ConPort /health endpoints report auth_mode 'log' or 'enforce' and "
    "identity_required_writes true (ConPort also auth_principal_column 'ok'); "
    f"(2) a keychain token exists for {CODEX_MEMORY_PRINCIPAL} "
    f"(`dopemux auth issue {CODEX_MEMORY_PRINCIPAL} --apply`). "
    "When a check fails only the preview is written and the check is named. "
    "Re-run without --allow-sequenced."
)

# `off` and anything else fail. In `log` mode the servers still store the
# verified principal for every request that carries a token.
_GATE_ACCEPTED_AUTH_MODES = ("log", "enforce")

_HEALTH_TIMEOUT_SECONDS = 3.0
# Loopback health probes carry no credentials; an empty ProxyHandler keeps them
# off any environment proxy.
_HEALTH_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# (server, envrc key holding the port that serves its REST /health, extra
# fields that must equal a value). ConPort's REST port is CONPORT_HTTP_PORT,
# not the MCP port the bridge uses.
_MEMORY_HEALTH_TARGETS: Tuple[Tuple[str, str, Tuple[Tuple[str, str], ...]], ...] = (
    ("dope-memory", "DOPE_MEMORY_PORT", ()),
    ("conport", "CONPORT_HTTP_PORT", (("auth_principal_column", "ok"),)),
)


class _HealthProbeError(Exception):
    """A server's /health could not be located or read (message is safe to print)."""


@dataclass(frozen=True)
class GateCheck:
    name: str
    ok: bool
    detail: str
    # Server name and its reported auth_mode for a passing health check; lets
    # the apply output say when servers are still in log mode.
    server: Optional[str] = None
    auth_mode: Optional[str] = None


@dataclass(frozen=True)
class CodexMemoryGate:
    """Outcome of every gate check; carries messages only, never a token."""

    checks: Tuple[GateCheck, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    @property
    def failures(self) -> Tuple[str, ...]:
        return tuple(check.detail for check in self.checks if not check.ok)

    @property
    def log_mode_servers(self) -> Tuple[str, ...]:
        """Servers whose passing health check reported `log` (not yet `enforce`)."""
        return tuple(
            check.server
            for check in self.checks
            if check.ok and check.auth_mode == "log" and check.server
        )


def _fetch_health(port: int) -> Dict[str, Any]:
    """GET http://127.0.0.1:<port>/health and return the JSON object (200 only)."""
    import http.client

    url = f"http://127.0.0.1:{port}/health"
    try:
        with _HEALTH_OPENER.open(url, timeout=_HEALTH_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise _HealthProbeError(f"{url} answered HTTP {response.status}")
            raw = response.read(1 << 16)
    except _HealthProbeError:
        raise
    except urllib.error.HTTPError as exc:
        raise _HealthProbeError(f"{url} answered HTTP {exc.code}") from None
    except (OSError, ValueError, http.client.HTTPException) as exc:
        raise _HealthProbeError(f"{url} is unreachable ({type(exc).__name__})") from None
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise _HealthProbeError(f"{url} did not return JSON") from None
    if not isinstance(body, dict):
        raise _HealthProbeError(f"{url} did not return a JSON object")
    return body


def _health_port(repo_path: Path, key: str) -> int:
    """The `key` port from the checkout's envrc, reading no other value from it."""
    from ..mcp import http_stdio_bridge as bridge
    from ..mcp.envrc import safe_port_int

    envrc = bridge._find_envrc(repo_path)
    if envrc is None:
        raise _HealthProbeError(
            f"no {bridge.ENVRC_FILENAME} from {repo_path} up to the checkout root; "
            "run `dopemux mcp init` in this checkout"
        )
    try:
        values = bridge._read_selected_keys(envrc, frozenset({key}))
    except bridge.BridgeStartupError as exc:
        raise _HealthProbeError(str(exc)) from None
    port = safe_port_int(values, key)
    if port is None:
        raise _HealthProbeError(
            f"{envrc} has no valid {key}; run `dopemux mcp init` / `dopemux mcp start` in this checkout"
        )
    return port


def _short(value: Any) -> str:
    # Brackets would read as console markup when the message is logged.
    text = repr(value).replace("[", "(").replace("]", ")")
    return text if len(text) <= 40 else text[:37] + "..."


def _check_memory_server_health(
    repo_path: Path,
    server: str,
    port_key: str,
    extra: Tuple[Tuple[str, str], ...],
) -> GateCheck:
    prefix = f"gate check 1 (server health) {server}"
    name = f"memory-health:{server}"
    try:
        body = _fetch_health(_health_port(repo_path, port_key))
    except _HealthProbeError as exc:
        return GateCheck(name, False, f"{prefix}: {exc}")
    problems: List[str] = []
    mode = body.get("auth_mode")
    if mode not in _GATE_ACCEPTED_AUTH_MODES:
        problems.append(f"auth_mode is {_short(mode)}, expected 'log' or 'enforce'")
    if body.get("identity_required_writes") is not True:
        problems.append(
            f"identity_required_writes is {_short(body.get('identity_required_writes'))}, expected true"
        )
    for key, expected in extra:
        if body.get(key) != expected:
            problems.append(f"{key} is {_short(body.get(key))}, expected {expected!r}")
    if problems:
        return GateCheck(name, False, f"{prefix}: " + "; ".join(problems))
    return GateCheck(name, True, f"{prefix}: {mode}, identity-required writes", server=server, auth_mode=mode)


def _check_runner_token(principal: str) -> GateCheck:
    name = f"runner-token:{principal}"
    try:
        get_token(principal)  # existence check only: the value is discarded unread
    except AuthError as exc:
        return GateCheck(
            name,
            False,
            f"gate check 2 (runner token) {principal}: no usable keychain token "
            f"({type(exc).__name__}: {exc}); issue one with `dopemux auth issue {principal} --apply`",
        )
    return GateCheck(name, True, f"gate check 2 (runner token) {principal}: present")


def evaluate_codex_memory_gate(
    repo_path: Path,
    principal: str = CODEX_MEMORY_PRINCIPAL,
) -> CodexMemoryGate:
    """Run every gate check for the checkout at `repo_path`; never raises for a failed check."""
    checks = [
        _check_memory_server_health(repo_path, server, port_key, extra)
        for server, port_key, extra in _MEMORY_HEALTH_TARGETS
    ]
    checks.append(_check_runner_token(principal))
    return CodexMemoryGate(tuple(checks))


# ---------------------------------------------------------------------------
# `mcp generate` / `ensure` / `init` / `add` / `remove` / `list` / `doctor` / `sync-globals`
# ---------------------------------------------------------------------------


@mcp.command("generate")
@click.option("--apply", is_flag=True, help="Write generated outputs. Default is dry-run.")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Directory for generated output files when --apply is set.",
)
@click.option(
    "--allow-sequenced",
    "allow_sequenced",
    is_flag=True,
    help=(
        "Removed (Wave 2A). Passing it is an error: the .codex/config.toml write is "
        "controlled by the memory-server gate, not by a flag."
    ),
)
@click.option(
    "--profile",
    "profile_name",
    default=None,
    help=(
        "Named MCP profile (ADR-DMX-MCPPROF-001). When set, emit profile-selected "
        "projections only (never all servers). Forbidden: all/*."
    ),
)
@click.option(
    "--agent-matrix",
    "agent_matrix",
    is_flag=True,
    help=(
        "Emit ADR-MCPINT-001 agent-matrix fleet fragments (opencode/codex/copilot "
        "parity). Mutually exclusive with --profile. Without either flag, defaults "
        "to compatibility profile core-code profile plane."
    ),
)
def mcp_generate_cmd(
    apply: bool,
    output_dir: Optional[Path],
    allow_sequenced: bool,
    profile_name: Optional[str],
    agent_matrix: bool,
):
    """
    🧾 Project Fleet: Render catalog-backed MCP config fragments

    Profile plane (ADR-DMX-MCPPROF-001): default resolves to explicit compatibility
    profile ``core-code`` unless ``--profile`` or ``--agent-matrix`` is passed.
    There is no implicit ``all`` profile.

    Agent-matrix mode (``--agent-matrix``): ADR-MCPINT-001 projections for local
    .mcp.json, Claude globals, Codex/OpenCode/Copilot fragments, health probes.
    Dry-run is the default; writes require both --apply and --output-dir.

    With --agent-matrix, --apply also writes the in-repo .codex/config.toml, but
    only when the memory gate holds (dope-memory and ConPort report auth_mode log
    or enforce with identity-required writes, and a keychain token exists for
    runner:codex).
    Otherwise only the preview under --output-dir is written and the failed
    checks are named.
    """
    from dopemux.mcp import fleet_catalog
    from dopemux.mcp import profile_policy

    if allow_sequenced:
        raise click.ClickException(ALLOW_SEQUENCED_REMOVED_MESSAGE)

    catalog = _load_catalog()

    if agent_matrix and profile_name:
        raise click.ClickException("Pass only one of --profile or --agent-matrix.")

    use_profile_plane = False
    if profile_name is not None:
        use_profile_plane = True
    elif agent_matrix:
        use_profile_plane = False
    elif catalog.get("profiles"):
        # Catalog declares profiles: default to explicit compatibility profile,
        # never an implicit all-servers surface (ADR-DMX-MCPPROF-001).
        use_profile_plane = True
    else:
        # Legacy catalog without profiles: agent-matrix projection.
        use_profile_plane = False

    if not use_profile_plane:
        outputs = fleet_catalog.generate_fleet_output_files(catalog)
        console.logger.info(
            "[info]Agent-matrix fleet projection (ADR-MCPINT-001). "
            "Not a profile=all surface. Use --profile <name> for task profiles.[/info]"
        )
    else:
        try:
            profile_policy.assert_no_implicit_all(profile_name)
            resolved = profile_policy.resolve_default_profile(catalog, profile_name)
        except profile_policy.ProfilePolicyError as exc:
            raise click.ClickException(str(exc)) from exc
        if profile_name is None:
            console.logger.info(
                f"[info]No --profile given; resolving compatibility profile "
                f"`{resolved}` (never all servers). "
                f"Pass --profile <name> or --agent-matrix explicitly.[/info]"
            )
        repo = get_repo_root(fallback_cwd=False)
        repo_path = Path(repo) if repo else None
        try:
            outputs = fleet_catalog.generate_profile_output_files(
                catalog, resolved, repo_root=repo_path
            )
        except profile_policy.ProfilePolicyError as exc:
            raise click.ClickException(str(exc)) from exc

    if not apply:
        console.logger.info("[info]Dry-run only. No files were written.[/info]")
        for relative_path, content in outputs.items():
            line_count = len(content.splitlines())
            console.logger.info(f"[info]Would write {relative_path} ({line_count} lines)[/info]")
        if not use_profile_plane:
            console.logger.info(
                "[info]--apply also updates in-repo agent configs: opencode.jsonc (managed "
                "mcp section), mcp-proxy-config.copilot.yaml, and — only when the "
                "memory gate holds — .codex/config.toml.[/info]"
            )
        return

    if output_dir is None:
        raise click.ClickException("--apply requires --output-dir to bound generated writes.")

    for relative_path, content in outputs.items():
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        console.logger.info(f"[success]Wrote {target}[/success]")

    if not use_profile_plane:
        _apply_in_repo_agent_configs(catalog, output_dir)


def _apply_in_repo_agent_configs(
    catalog: Dict[str, Any],
    output_dir: Path,
) -> None:
    """Write the in-repo agent config targets owned by the generate pipeline.

    ADR-MCPINT-001 §2: the generate pipeline is the sole producer of agent
    configs. opencode.jsonc is a managed-merge — only the marker-delimited `mcp`
    section is replaced; user keys (`permission`, `instructions`, …) are
    preserved. mcp-proxy-config.copilot.yaml is fully generated.
    .codex/config.toml carries write-capable memory servers, so the in-repo write
    happens only when `fleet_catalog.evaluate_codex_memory_gate` holds, and then
    only the released servers are written; a preview of every Codex-renderable
    server always lands under the output dir.
    """
    from dopemux.mcp import fleet_catalog

    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException(
            "--apply writes in-repo agent configs and must run inside a git repository."
        )
    repo_path = Path(repo)

    opencode_path = repo_path / "opencode.jsonc"
    existing_opencode = (
        opencode_path.read_text(encoding="utf-8") if opencode_path.exists() else None
    )
    try:
        merged_opencode = fleet_catalog.render_opencode_jsonc(existing_opencode, catalog)
    except fleet_catalog.MCPFleetCatalogError as exc:
        raise click.ClickException(str(exc)) from exc
    opencode_path.write_text(merged_opencode, encoding="utf-8")
    console.logger.info(
        f"[success]Wrote {opencode_path} (managed mcp section; non-managed keys preserved)[/success]"
    )

    copilot_path = repo_path / "mcp-proxy-config.copilot.yaml"
    copilot_path.write_text(
        fleet_catalog.render_copilot_proxy_config(catalog), encoding="utf-8"
    )
    console.logger.info(f"[success]Wrote {copilot_path}[/success]")

    codex_path = repo_path / ".codex" / "config.toml"
    gate = evaluate_codex_memory_gate(repo_path)
    if gate.ok:
        existing_codex = codex_path.read_text(encoding="utf-8") if codex_path.exists() else None
        try:
            merged_codex = fleet_catalog.merge_codex_config_toml(
                existing_codex, catalog, released_only=True
            )
        except fleet_catalog.MCPFleetCatalogError as exc:
            raise click.ClickException(str(exc)) from exc
        codex_path.parent.mkdir(parents=True, exist_ok=True)
        codex_path.write_text(merged_codex, encoding="utf-8")
        console.logger.info(
            f"[success]Wrote {codex_path} (managed mcp_servers section, released servers only; "
            "existing keys preserved)[/success]"
        )
        if gate.log_mode_servers:
            console.logger.info(
                f"[warning]Memory servers in log mode ({', '.join(gate.log_mode_servers)}): "
                "Codex's writes are verified as runner:codex; writers without a token are "
                "still accepted and recorded as unverified until enforce.[/warning]"
            )
    else:
        console.logger.info(
            "[warning]Refused to write .codex/config.toml: the memory gate does not hold. "
            "Failed checks:[/warning]"
        )
        for failure in gate.failures:
            console.logger.info(f"  - {failure}")
        console.logger.info(
            f"[info]Preview written to {output_dir / 'codex' / 'config.toml'}; "
            "fix the failed checks and re-run `dopemux mcp generate --agent-matrix --apply`.[/info]"
        )


def _ensure_context(*, trust_env: bool = False) -> tuple[Path, Any]:
    repo = get_repo_root(fallback_cwd=False, trust_env=trust_env)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    repo_path = Path(repo)
    identity_env = dict(os.environ) if trust_env else {}
    identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
    try:
        identity = resolve_project_identity(cwd=repo_path, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc
    return repo_path, identity


def _ensure_fast_context(*, trust_env: bool = False) -> tuple[Path, Path]:
    # Fast mode never spawns a subprocess, so the checkout is found by walking up
    # from cwd; ambient DOPEMUX_*/TASK_ORCHESTRATOR_* only count with --trust-env.
    env_map = os.environ if trust_env else {}
    env_repo = env_map.get("DOPEMUX_WORKSPACE_ROOT") or env_map.get("DOPEMUX_PROJECT_ROOT")
    if env_repo:
        repo_path = Path(env_repo).expanduser().resolve()
        if not repo_path.is_dir():
            raise click.ClickException(f"MCP workspace root does not point to a directory: {repo_path}")
    else:
        start = Path.cwd().resolve()
        repo_path = next(
            (
                candidate
                for candidate in (start, *start.parents)
                if (candidate / PROJECT_MCP_FILENAME).exists() or (candidate / ".git").exists()
            ),
            None,
        )
        if repo_path is None:
            raise click.ClickException(
                "Could not determine MCP workspace root without subprocess; "
                "set DOPEMUX_WORKSPACE_ROOT or run from the repository root."
            )

    project_override = env_map.get("TASK_ORCHESTRATOR_PROJECT_ROOT") or env_map.get("DOPEMUX_PROJECT_ROOT")
    if project_override:
        project_root = Path(project_override).expanduser().resolve()
        if not project_root.is_dir():
            raise click.ClickException(f"MCP project root does not point to a directory: {project_root}")
    else:
        project_root = repo_path
    return repo_path, project_root


def _ensure_fast_problems(catalog: Dict[str, Any], repo_path: Path, project_root: Path) -> List[str]:
    problems: List[str] = []
    mcp_json_path = repo_path / PROJECT_MCP_FILENAME
    envrc_path = repo_path / ENVRC_FILENAME

    if not mcp_json_path.exists():
        problems.append(
            f"Missing {PROJECT_MCP_FILENAME} at {mcp_json_path} — run `dopemux mcp init`."
        )
    else:
        defaults = catalog.get("defaults", {}).get("per_worktree", []) or []
        try:
            expected = _build_local_mcp_json(list(defaults), catalog)
            actual = _read_json(mcp_json_path)
        except (json.JSONDecodeError, click.ClickException) as exc:
            problems.append(f"{mcp_json_path} is not a valid catalog-backed MCP config: {exc}")
        else:
            if actual != expected:
                problems.append(f"{mcp_json_path} does not match catalog defaults.")

    if not envrc_path.exists():
        problems.append(f"Missing {ENVRC_FILENAME} at {envrc_path} — run `dopemux mcp init`.")

    local_env = {
        **os.environ,
        **_project_env_exports(str(repo_path), str(project_root)),
    }
    for name in catalog.get("defaults", {}).get("per_worktree", []) or []:
        spec = catalog.get("servers", {}).get(name) or {}
        for env_key in spec.get("requires_env", []) or []:
            if not local_env.get(env_key):
                problems.append(f"`{name}`: required env `{env_key}` is unavailable.")
    return problems


DEFAULT_ENSURE_TIMEOUT_SECONDS = 120
DEFAULT_COMPOSE_WAIT_TIMEOUT_SECONDS = 90
# `docker compose up` also BUILDS any missing local images before the health
# wait begins, and a cold multi-image build easily exceeds the health-wait
# budget. Give the compose step its own generous (but still bounded) subprocess
# budget so a first-run build isn't killed, while --wait-timeout still bounds
# the post-build health wait.
DEFAULT_COMPOSE_UP_TIMEOUT_SECONDS = 900


def _catalog_compose_services(catalog: Dict[str, Any]) -> List[str]:
    """Compose services that `ensure --full` may auto-start.

    Includes ``lifecycle: active`` and ``lifecycle: operator-managed`` servers —
    both are consumed by clients (e.g. ``pal-stdio`` is the ``mcp-pal-stdio``
    container that Claude/Codex configs exec into), so ensure must bring them up
    or it would report green while a configured server is down. Only
    ``decision-required`` servers (e.g. desktop-commander) — quarantined
    out of generated startable config pending an operator decision — are
    excluded, along with any server missing a lifecycle field.
    """
    services = {
        str(spec["docker_compose_service"])
        for spec in catalog.get("servers", {}).values()
        if spec.get("docker_compose_service")
        and spec.get("lifecycle") in ("active", "operator-managed")
    }
    return sorted(services)


def _run_checked(
    cmd: List[str],
    *,
    cwd: Path,
    label: str,
    timeout: int = DEFAULT_ENSURE_TIMEOUT_SECONDS,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    console.logger.info(f"[info]{label}: {' '.join(cmd)}[/info]")
    try:
        subprocess.run(cmd, cwd=cwd, check=True, timeout=timeout, env=env)
    except FileNotFoundError as exc:
        raise click.ClickException(f"{label}: command not found: {cmd[0]}") from exc
    except CalledProcessError as exc:
        raise click.ClickException(f"{label} failed with exit code {exc.returncode}.") from exc
    except subprocess.TimeoutExpired as exc:
        raise click.ClickException(
            f"{label} timed out after {exc.timeout}s (command: {' '.join(cmd)})."
        ) from exc


_ENV_TEMPLATE_RE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}")


def _resolve_env_template(value: str, env: Dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2) or ""
        return env.get(name) or default

    return _ENV_TEMPLATE_RE.sub(repl, value)


def _probeable_http_servers(catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    env = dict(os.environ)
    servers: Dict[str, Dict[str, Any]] = {}
    for name, spec in sorted(catalog.get("servers", {}).items()):
        if spec.get("transport") != "http":
            continue
        raw_url = spec.get("url") or spec.get("url_template")
        if not raw_url:
            continue
        url = _resolve_env_template(str(raw_url), env)
        parsed = urlparse(url)
        if parsed.hostname not in {"localhost", "127.0.0.1"}:
            continue
        servers[name] = {"url": url}
    return servers


def _run_mcp_tools_list_probes(catalog: Dict[str, Any]) -> List[str]:
    servers = _probeable_http_servers(catalog)
    if not servers:
        return []
    try:
        from dopemux.mcp.discovery import ToolDiscoveryClient
    except ModuleNotFoundError as exc:
        return [f"MCP probe client unavailable: missing dependency `{exc.name}`."]

    report = asyncio.run(ToolDiscoveryClient(timeout=2.0).discover(servers))
    return [
        f"`{server['name']}`: MCP tools-list probe failed ({server.get('status', 'unknown')})."
        for server in report.get("servers", [])
        if not server.get("reachable")
    ]


def _report_ensure_problems(problems: List[str]) -> None:
    console.logger.info(f"[warning]{len(problems)} ensure issue(s) found:[/warning]")
    for problem in problems:
        console.logger.info(f"  • {problem}")
    sys.exit(1)


@mcp.command("ensure")
@_trust_env_option()
@click.option(
    "--fast",
    is_flag=True,
    help="Static prerequisite checks only (config/env presence) — no daemon probes, no health checks.",
)
@click.option("--full", "full_mode", is_flag=True, help="Run local checks plus bounded service remediation/probes.")
def mcp_ensure_cmd(trust_env: bool, fast: bool, full_mode: bool):
    """
    🛠️ Stabilize Fleet: Check or remediate catalog-backed MCP prerequisites

    `--fast` performs static prerequisite checks only: it verifies `.mcp.json`
    matches catalog defaults, `.envrc.dopemux-mcp` exists, and required env
    vars are present. It does not probe any daemon, container, or HTTP
    endpoint, live or cached. `--full` additionally starts catalog compose
    services (lifecycle: active only), ensures PAL and the Task Orchestrator
    singleton, then runs bounded local HTTP MCP tools-list probes.
    """
    if fast and full_mode:
        raise click.ClickException("Choose exactly one of --fast or --full.")
    if not fast and not full_mode:
        fast = True

    catalog = _load_catalog()
    if fast:
        repo_path, project_root = _ensure_fast_context(trust_env=trust_env)
    else:
        repo_path, identity = _ensure_context(trust_env=trust_env)
        project_root = identity.project_root
    problems = _ensure_fast_problems(catalog, repo_path, project_root)
    if problems:
        _report_ensure_problems(problems)

    if fast:
        console.logger.info("[success]Fast MCP ensure checks green.[/success]")
        return

    if shutil.which("docker") is None:
        raise click.ClickException("docker is required for `dopemux mcp ensure --full`.")
    if not (repo_path / "compose.yml").exists():
        raise click.ClickException(f"Missing {repo_path / 'compose.yml'} for compose remediation.")

    compose_services = _catalog_compose_services(catalog)
    if compose_services:
        from ..mcp.docker_runtime import env_with_compose_interpolation

        # --wait blocks until dependent services report healthy (bounded by
        # --wait-timeout). The Python-side timeout= is a backstop against a
        # hung CLI and must cover BOTH a cold first-run image build AND the
        # health wait, so it uses the generous compose-up budget rather than
        # the short health-wait one.
        _run_checked(
            [
                "docker", "compose", "-f", "compose.yml", "up", "-d",
                "--wait", "--wait-timeout", str(DEFAULT_COMPOSE_WAIT_TIMEOUT_SECONDS),
                *compose_services,
            ],
            cwd=repo_path,
            label="compose",
            timeout=DEFAULT_COMPOSE_UP_TIMEOUT_SECONDS,
            env=env_with_compose_interpolation(
                host_path_defaults="dope-context" not in compose_services
            ),
        )

    # ensure-pal.sh owns the off-compose Codex pal-mcp-server container only;
    # the compose step above already (re)started the compose `pal` service
    # that Claude Code talks to, so there is no overlap between the two.
    _run_checked(["bash", "scripts/mcp-wrappers/ensure-pal.sh"], cwd=repo_path, label="pal")
    _run_checked(
        ["bash", "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh"],
        cwd=repo_path,
        label="task-orchestrator",
    )

    probe_problems = _run_mcp_tools_list_probes(catalog)
    if probe_problems:
        _report_ensure_problems(probe_problems)
    console.logger.info("[success]Full MCP ensure checks green.[/success]")


# `mcp init` sidecar steps (D4/D5) run their docker/psql through this
# subprocess.run-compatible callable; tests inject a fake. None means the real
# subprocess.run, which is refused under pytest so no test reaches docker.
_INIT_RUNNER: Optional[Any] = None


def _init_sidecars(
    repo_path: Path,
    services: List[str],
    envrc_values: Mapping[str, str],
    *,
    trust_env: bool = False,
) -> bool:
    """Resolve (provisioning if needed) the ConPort tenant and pre-build sidecar images.

    Never starts a container. Prints the tenant source word, never the password
    or the user. Returns False after one FAIL line; config already written stays.
    """
    from rich.markup import escape

    from dopemux.mcp import conport_tenant as ct
    from dopemux.mcp import docker_runtime as dr
    from dopemux.mcp.lifecycle import runtime_dir_for
    from dopemux.mcp.runtime_state import resolve_identity_view

    def say(markup: str) -> None:
        console.logger.info(markup, soft_wrap=True)

    wanted = [s for s in ("conport", "dope-memory") if s in services]
    if not wanted:
        return True
    runner = _INIT_RUNNER
    if runner is None and os.environ.get("PYTEST_CURRENT_TEST"):
        say("[info]Sidecar pre-build and ConPort tenant skipped (pytest, no injected runner).[/info]")
        return True
    identity = resolve_identity_view(
        repo_path, envrc_values=(dict(os.environ) if trust_env else None), trust_env=trust_env
    )
    if "conport" in wanted:
        try:
            creds = ct.resolve_tenant(
                identity,
                envrc_values=envrc_values,
                psql=ct.default_psql_runner(runner=runner),
            )
        except ct.TenantError as exc:
            say(f"[error]FAIL {exc.code}: {escape(exc.detail or exc.code)}[/error]")
            return False
        except (OSError, ValueError) as exc:
            detail = escape(ct.os_error_detail(exc))
            say(f"[error]FAIL CONPORT_TENANT_PROVISION_FAILED: {detail}[/error]")
            return False
        detail = f" ({escape(creds.evidence)})" if creds.evidence else ""
        say(f"[info]ConPort tenant: {creds.source}{detail}[/info]")
    try:
        product = dr.product_root()
        runtime_dir = runtime_dir_for(identity)
    except (FileNotFoundError, ValueError) as exc:
        say(f"[error]FAIL IMAGE_BUILD_FAILED: {escape(str(exc))}[/error]")
        return False
    slug = dr.project_slug(Path(str(identity.project_root)).name)
    compose_project = dr.compose_project_name(slug, identity.worktree_hash or "")
    env = dr.env_with_compose_interpolation(product=product, scrub_ambient=True)
    log_path = runtime_dir / "build.log"
    budget = dr.build_timeout_secs()
    for svc in wanted:
        image = dr.compose_image_name(svc, product=product)  # shared by every worktree
        if dr.docker_image_exists(image, runner=runner, env=env) is True:
            say(f"[info]Image {image} present; no pre-build for {svc}.[/info]")
            continue
        override, env_file = dr.compose_build_inputs(runtime_dir, product=product)
        say(
            f"[info]Building the {svc} image {image} (up to {budget:.0f}s, "
            f"{dr.BUILD_TIMEOUT_ENV}); log {escape(str(log_path))}[/info]"
        )
        result = dr.run_cmd(
            dr.compose_build_command(
                product=product,
                override_path=override,
                env_file=env_file,
                project_name=compose_project,
                services=[svc],
            ),
            runner=runner,
            cwd=product,
            env=env,
            timeout=budget,
        )
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(result.stdout or "")
            log.write(result.stderr or "")
        if result.exit_code != 0:
            say(
                f"[error]FAIL IMAGE_BUILD_FAILED: compose build {svc} exited "
                f"{result.exit_code}; log {escape(str(log_path))}[/error]"
            )
            return False
        say(f"[success]Built {image}[/success]")
    return True


@mcp.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing .mcp.json and env file without prompting.")
@click.option("--with", "extra", multiple=True, help="Additional server name beyond catalog defaults (repeatable).")
@click.option(
    "--profile",
    "profile_name",
    default=None,
    help=(
        "Named MCP profile (ADR-DMX-MCPPROF-001). Defaults to compatibility "
        "profile core-code when omitted. Never all servers."
    ),
)
@_lifecycle_repo_option()
@_trust_env_option()
def mcp_init_cmd(
    force: bool,
    extra: Tuple[str, ...],
    profile_name: Optional[str],
    repo_arg: Optional[Path],
    trust_env: bool,
):
    """
    🌱 Bootstrap Worktree: Scaffold .mcp.json + per-worktree env file

    Generates the per-worktree MCP config from the selected profile's
    per-worktree servers (default: compatibility profile ``core-code``) plus any
    `--with NAME` extras. Allocates ports deterministically from the worktree
    path so two worktrees never collide on the same host port.

    The target is ``--repo`` when given, else the current git checkout; ambient
    ``DOPEMUX_*`` variables are ignored unless ``--trust-env`` is passed.
    """
    from dopemux.mcp import profile_policy

    if repo_arg is not None:
        repo = str(Path(repo_arg).expanduser().resolve())
    else:
        repo = get_repo_root(fallback_cwd=False, trust_env=trust_env)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    repo_path = Path(repo)
    try:
        identity = resolve_project_identity(
            cwd=repo_path, env=(dict(os.environ) if trust_env else {})
        )
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc

    # `--repo` may be any directory inside the checkout; catalog lookup, profile
    # inventory, port allocation and every file write use the worktree root, as
    # the launcher does. (Test doubles for the identity may not carry one.)
    worktree_root = getattr(identity, "worktree_root", None)
    if worktree_root and Path(worktree_root) != repo_path:
        # Only an enclosing checkout root replaces the target; an ambient
        # override (--trust-env) pointing elsewhere never redirects the writes.
        if Path(worktree_root).resolve() in repo_path.resolve().parents:
            repo_path = Path(worktree_root)
            repo = str(repo_path)

    # The resolved target's catalog, not the caller's: `init --repo <target>` from
    # another checkout must see the target's own servers and defaults.
    catalog = _load_catalog(repo_path)

    if catalog.get("profiles") or profile_name is not None:
        try:
            profile_policy.assert_no_implicit_all(profile_name)
            resolved_profile = profile_policy.resolve_default_profile(
                catalog, profile_name
            )
            inv = profile_policy.resolve_profile(
                catalog,
                resolved_profile,
                repo_root=repo_path,
                check_inventory_baseline=True,
            )
        except profile_policy.ProfilePolicyError as exc:
            raise click.ClickException(str(exc)) from exc
        servers_map = catalog.get("servers") or {}
        profile_per_worktree = [
            name
            for name in inv.selected_servers
            if isinstance(servers_map.get(name), dict)
            and servers_map[name].get("scope") == "per-worktree"
        ]
        # Fallback: if profile has no per-worktree members, use catalog defaults
        # (still an explicit named profile selection, not all servers).
        base_names = profile_per_worktree or list(
            catalog.get("defaults", {}).get("per_worktree", [])
        )
        console.logger.info(
            f"[info]Profile `{resolved_profile}` "
            f"(digest={inv.profile_digest[:12]}…) → per-worktree base: {base_names}[/info]"
        )
    else:
        base_names = list(catalog.get("defaults", {}).get("per_worktree", []))

    server_names = list(base_names) + list(extra)
    # de-dup while preserving order
    seen, ordered = set(), []
    for n in server_names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)

    mcp_json_path = repo_path / PROJECT_MCP_FILENAME
    envrc_path = repo_path / ENVRC_FILENAME
    config = _build_local_mcp_json(ordered, catalog)

    if envrc_path.exists() and not force:
        raise click.ClickException(
            f"{envrc_path.name} already exists. Use --force to overwrite."
        )

    wrote_mcp_json = True
    if mcp_json_path.exists() and not force:
        existing_config = _read_json(mcp_json_path)
        if existing_config != config:
            raise click.ClickException(
                f"{mcp_json_path.name} already exists and does not match the catalog template. "
                "Use --force to overwrite."
            )
        wrote_mcp_json = False

    # Allocate only after init preconditions pass so dry collisions do not write leases.
    existing_env: Dict[str, str] = {}
    if envrc_path.exists():
        try:
            from dopemux.mcp.envrc import load_envrc

            parsed = load_envrc(envrc_path)
            if parsed.values:
                existing_env = dict(parsed.values)
        except Exception:  # noqa: BLE001 — fall back to pure preferred formula
            existing_env = {}
    port_vars = _allocate_ports(
        repo,
        ordered,
        catalog,
        project_root=str(identity.project_root),
        existing_envrc=existing_env or None,
        source="dopemux mcp init",
    )

    if wrote_mcp_json:
        _atomic_write_json(mcp_json_path, config)
    elif mcp_json_path.exists() and force:
        _atomic_write_json(mcp_json_path, config)
        wrote_mcp_json = True

    preserved = {k: v for k, v in existing_env.items() if k.startswith("CONPORT_DB_")}
    _write_envrc(envrc_path, port_vars, repo, str(identity.project_root), preserve=preserved)

    if wrote_mcp_json:
        console.logger.info(f"[success]Wrote {mcp_json_path}[/success]")
    else:
        console.logger.info(f"[info]Kept existing catalog-matching {mcp_json_path}[/info]")
    console.logger.info(f"[success]Wrote {envrc_path}[/success]")
    console.logger.info(f"[info]Worktree:   {repo}[/info]")
    console.logger.info(f"[info]Project:    {identity.project_root}[/info]")
    console.logger.info(f"[info]Instance:   {_instance_id(repo)}[/info]")
    if port_vars:
        for var, port in sorted(port_vars.items()):
            free = "[success]free[/success]" if _port_is_free(port) else "[warning]in use[/warning]"
            console.logger.info(f"[info]  {var}={port} ({free})[/info]")
    # D4/D5: tenant (provisioned if needed) and synchronous image pre-build (#1459).
    if not _init_sidecars(repo_path, ordered, existing_env, trust_env=trust_env):
        sys.exit(1)
    console.logger.info("")
    console.logger.info("[info]Next:[/info]")
    from rich.markup import escape

    console.logger.info("[info]  1. Commit `.mcp.json` (leave `.envrc.dopemux-mcp` uncommitted).[/info]")
    console.logger.info(
        "[info]  2. Open a Claude session in this checkout; approve the project's MCP servers "
        "once when prompted.[/info]"
    )
    console.logger.info(f"[info]  3. Verify: `dopemux mcp doctor --repo {escape(str(repo_path))}`.[/info]")
    console.logger.info(
        "[info]  4. Optional: `dopemux mcp switch-project` moves the task-orchestrator to this project.[/info]"
    )


@mcp.command("add")
@click.argument("name")
@_trust_env_option()
def mcp_add_cmd(name: str, trust_env: bool):
    """
    ➕ Append Server: Add a per-worktree MCP from the catalog to .mcp.json

    The server must be present in `mcp_catalog.yaml` with `scope: per-worktree`.
    Singletons are added via `dopemux mcp sync-globals` instead.
    """
    repo = get_repo_root(fallback_cwd=False, trust_env=trust_env)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    identity_env = dict(os.environ) if trust_env else {}
    identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
    try:
        identity = resolve_project_identity(cwd=repo, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc

    catalog = _load_catalog()
    if name not in catalog["servers"]:
        raise click.ClickException(f"Unknown server `{name}`. See `dopemux mcp list`.")
    if catalog["servers"][name].get("scope") != "per-worktree":
        raise click.ClickException(
            f"`{name}` is a singleton. Add via `dopemux mcp sync-globals`, not `mcp add`."
        )

    mcp_json_path = Path(repo) / PROJECT_MCP_FILENAME
    if not mcp_json_path.exists():
        raise click.ClickException(
            f"{PROJECT_MCP_FILENAME} not found. Run `dopemux mcp init` first."
        )

    data = _read_json(mcp_json_path)
    servers = data.setdefault("mcpServers", {})
    if name in servers:
        console.logger.info(f"[warning]`{name}` already in {PROJECT_MCP_FILENAME}; nothing to do.[/warning]")
        return

    servers[name] = _render_local_entry(name, catalog["servers"][name])
    _atomic_write_json(mcp_json_path, data)

    envrc_path = Path(repo) / ENVRC_FILENAME
    env_exports: Dict[str, Any] = {
        **_project_env_exports(repo, str(identity.project_root)),
        **_allocate_ports(repo, [name], catalog, project_root=str(identity.project_root)),
    }
    appended = _append_missing_env_exports(envrc_path, env_exports)
    for var in appended:
        console.logger.info(f"[info]Appended {var}={env_exports[var]} to {envrc_path.name}.[/info]")

    console.logger.info(f"[success]Added `{name}` to {mcp_json_path}.[/success]")


@mcp.command("remove")
@click.argument("name")
def mcp_remove_cmd(name: str):
    """
    ➖ Drop Server: Remove a per-worktree MCP from .mcp.json
    """
    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    mcp_json_path = Path(repo) / PROJECT_MCP_FILENAME
    if not mcp_json_path.exists():
        raise click.ClickException(f"{PROJECT_MCP_FILENAME} not found.")

    data = _read_json(mcp_json_path)
    servers = data.get("mcpServers", {})
    if name not in servers:
        console.logger.info(f"[warning]`{name}` not in {PROJECT_MCP_FILENAME}; nothing to remove.[/warning]")
        return

    del servers[name]
    _atomic_write_json(mcp_json_path, data)
    console.logger.info(f"[success]Removed `{name}` from {mcp_json_path}.[/success]")
    console.logger.info(
        "[info]The corresponding env-var entry in .envrc.dopemux-mcp is left intact "
        "(re-run `dopemux mcp init --force` to regenerate cleanly).[/info]"
    )


@mcp.command("list")
def mcp_list_cmd():
    """
    📋 Survey Fleet: Show globals, locals, catalog availability

    Lists what the catalog knows, what `~/.claude.json` declares globally,
    and what the current worktree's `.mcp.json` declares locally. Flags
    duplicates or drift between catalog and declared configs.
    """
    catalog = _load_catalog()
    repo = get_repo_root(fallback_cwd=False)
    global_path = _claude_global_path()
    global_data = _read_json(global_path)
    global_servers = (global_data.get("mcpServers") or {})

    local_data: Dict[str, Any] = {}
    if repo:
        local_path = Path(repo) / PROJECT_MCP_FILENAME
        local_data = _read_json(local_path)
    local_servers = (local_data.get("mcpServers") or {})

    console.logger.info("[info]== Catalog ==[/info]")
    for name, spec in catalog["servers"].items():
        scope = spec.get("scope", "?")
        transport = spec.get("transport", "?")
        console.logger.info(f"  {name}  ({scope}, {transport})  — {spec.get('description', '')}")

    console.logger.info("")
    console.logger.info("[info]== Global (~/.claude.json mcpServers) ==[/info]")
    for name in sorted(global_servers):
        marker = "" if name in catalog["servers"] else "  [warning](not in catalog)[/warning]"
        console.logger.info(f"  {name}{marker}")

    console.logger.info("")
    if repo:
        console.logger.info(f"[info]== Local ({repo}/{PROJECT_MCP_FILENAME}) ==[/info]")
        if not local_servers:
            console.logger.info("  (none — run `dopemux mcp init`)")
        for name in sorted(local_servers):
            marker = ""
            if name in global_servers:
                marker = "  [warning](DUPLICATE — also in global)[/warning]"
            elif name not in catalog["servers"]:
                marker = "  [warning](not in catalog)[/warning]"
            console.logger.info(f"  {name}{marker}")


def _run_stdio_doctor(name: str, spec: Dict[str, Any], env: Dict[str, str], cwd: Path) -> List[str]:
    """Run a stdio server's configured non-mutating doctor command."""
    doctor_args = list(spec.get("doctor_args") or [])
    if not doctor_args:
        return []

    command = spec.get("command_template") or spec.get("command")
    if not command:
        return [f"`{name}`: stdio server missing command for doctor check."]

    try:
        result = subprocess.run(
            [command, *doctor_args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=env,
            cwd=cwd,
        )
    except FileNotFoundError:
        return [f"`{name}`: doctor command not found: {command}"]
    except subprocess.TimeoutExpired:
        return [f"`{name}`: doctor command timed out."]

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        suffix = f" {detail}" if detail else ""
        return [f"`{name}`: doctor command failed.{suffix}"]

    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            console.logger.info(f"[info]`{name}`: {line}[/info]")
    return []


@mcp.command("doctor")
@click.option(
    "--repo",
    "repo_arg",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Target repo/worktree to diagnose (defaults to current git root). Works from any cwd.",
)
@_trust_env_option()
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Emit the full doctor JSON report (schema_version 1.0) to stdout.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Include more findings in the human summary.",
)
@click.option(
    "--skip-docker",
    is_flag=True,
    help="Skip Docker inspection (still reports DOCKER_UNAVAILABLE).",
)
@click.option(
    "--legacy",
    is_flag=True,
    help="Use the pre-Packet-001 problem-list doctor (cwd git root only).",
)
@click.option(
    "--profile",
    "profile_name",
    default=None,
    help=(
        "When set, emit profile inventory/doctor overlay (ADR-DMX-MCPPROF-001) "
        "instead of the full fleet doctor. Forbidden: all/*."
    ),
)
def mcp_doctor_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    json_output: bool,
    verbose: bool,
    skip_docker: bool,
    legacy: bool,
    profile_name: Optional[str],
):
    """
    🩺 Health Sweep: Repo-aware MCP truth gate (read-only)

    Loads the target repo's `.envrc.dopemux-mcp`, validates catalog transports,
    detects port collision risks, compose lifecycle drift, and Docker ownership
    where labels exist. Does not start or stop containers.

    With ``--profile``, runs the profile inventory overlay only (no Docker).

    Examples:
      dopemux mcp doctor
      dopemux mcp doctor --repo ~/code/other-project
      dopemux mcp doctor --repo ~/code/other-project --json
      dopemux mcp doctor --profile core-code
    """
    if profile_name is not None:
        if legacy:
            raise click.ClickException("--profile cannot be combined with --legacy.")
        _mcp_doctor_profile(profile_name, repo_arg=repo_arg, json_output=json_output)
        return

    if legacy:
        if repo_arg is not None:
            raise click.ClickException(
                "--legacy does not support --repo; omit --legacy for repo-aware doctor."
            )
        _mcp_doctor_legacy(trust_env=trust_env)
        return

    catalog = _load_catalog()
    catalog_path = _catalog_path()
    catalog_paths = [str(catalog_path)] if catalog_path else ["bundled:default_catalog.yaml"]

    repo: Optional[str]
    if repo_arg is not None:
        repo = str(repo_arg.resolve())
    else:
        repo = get_repo_root(fallback_cwd=False, trust_env=trust_env)
        if not repo:
            raise click.ClickException(
                "Not inside a git repository. Pass --repo <path> to diagnose another project."
            )

    from dopemux.mcp.doctor import format_human_summary, run_mcp_doctor

    # Only the target repo's compose.yml. Never pass a foreign cwd compose.yml
    # as compose_path — that bypasses run_mcp_doctor's repo-owned compose guard.
    compose_candidate = Path(repo) / "compose.yml"
    if not compose_candidate.is_file():
        compose_candidate = None

    report = run_mcp_doctor(
        repo,
        catalog=catalog,
        catalog_paths_checked=catalog_paths,
        compose_path=compose_candidate,
        skip_docker=skip_docker,
        process_env=dict(os.environ),
        trust_env=trust_env,
        check_dopemux_bin=True,
        check_conport_tenant=True,
    )

    if json_output:
        # Deterministic JSON to stdout (not through rich logger)
        sys.stdout.write(report.to_json())
    else:
        summary = format_human_summary(report, verbose=verbose)
        # Color the status line lightly via console, keep body plain for copy/paste
        status = report.status
        if status == "PASS":
            console.logger.info(f"[success]{summary.rstrip()}[/success]")
        elif status == "PASS_WITH_WARNINGS":
            console.logger.info(f"[warning]{summary.rstrip()}[/warning]")
        elif status == "FAIL":
            console.logger.info(f"[error]{summary.rstrip()}[/error]")
        else:
            console.logger.info(f"[info]{summary.rstrip()}[/info]")

    if report.exit_code:
        sys.exit(report.exit_code)


def _mcp_doctor_legacy(trust_env: bool = False) -> None:
    """Pre-Packet-001 doctor: problem list for cwd git root (compat)."""
    catalog = _load_catalog()
    repo = get_repo_root(fallback_cwd=False, trust_env=trust_env)
    if not repo:
        raise click.ClickException("Not inside a git repository.")

    envrc_path = Path(repo) / ENVRC_FILENAME
    mcp_json_path = Path(repo) / PROJECT_MCP_FILENAME
    problems: List[str] = []
    try:
        identity_env = dict(os.environ) if trust_env else {}
        identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
        identity = resolve_project_identity(cwd=repo, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc

    # Load envrc when present so legacy path no longer false-fails on unset ports.
    doctor_env = dict(os.environ)
    doctor_env.update(_project_env_exports(repo, str(identity.project_root)))
    if envrc_path.is_file():
        from dopemux.mcp.envrc import load_envrc, merge_envrc_into_environ

        parsed = load_envrc(envrc_path)
        doctor_env = merge_envrc_into_environ(doctor_env, parsed, override=True)

    if not mcp_json_path.exists():
        problems.append(f"Missing {mcp_json_path} — run `dopemux mcp init`.")
    if not envrc_path.exists():
        problems.append(f"Missing {envrc_path} — run `dopemux mcp init`.")

    local_data = _read_json(mcp_json_path) if mcp_json_path.exists() else {}
    declared = list((local_data.get("mcpServers") or {}).keys())

    for name in declared:
        spec = catalog["servers"].get(name)
        if not spec:
            problems.append(f"Server `{name}` declared locally but not in catalog.")
            continue
        is_stdio = spec.get("transport") == "stdio"
        env_source = doctor_env if is_stdio else doctor_env
        for env_key in spec.get("requires_env", []) or []:
            if not env_source.get(env_key):
                problems.append(f"`{name}`: required env `{env_key}` is unset.")
        if is_stdio:
            problems.extend(_run_stdio_doctor(name, spec, doctor_env, Path(repo)))
            continue
        if spec.get("port_var"):
            port_str = doctor_env.get(spec["port_var"])
            if not port_str:
                problems.append(f"`{name}`: env `{spec['port_var']}` is unset (source the .envrc?).")
                continue
            port = int(port_str)
            reachable = not _port_is_free(port)   # something listening => good
            if not reachable:
                problems.append(f"`{name}`: nothing listening on :{port} (start the container?).")

    if not problems:
        console.logger.info("[success]All checks green.[/success]")
        return
    console.logger.info(f"[warning]{len(problems)} issue(s) found:[/warning]")
    for p in problems:
        console.logger.info(f"  • {p}")
    sys.exit(1)


def _mcp_doctor_profile(
    profile_name: str,
    *,
    repo_arg: Optional[Path],
    json_output: bool,
) -> None:
    """Profile inventory/doctor overlay (no Docker). Fail closed on unknown profile."""
    from dopemux.mcp import profile_policy

    catalog = _load_catalog()
    if repo_arg is not None:
        repo_path = Path(repo_arg).expanduser().resolve()
    else:
        repo = get_repo_root(fallback_cwd=False)
        if not repo:
            raise click.ClickException(
                "Not inside a git repository. Pass --repo <path> with --profile."
            )
        repo_path = Path(repo).resolve()

    try:
        profile_policy.assert_no_implicit_all(profile_name)
        resolved = profile_policy.resolve_default_profile(catalog, profile_name)
        inventory = profile_policy.resolve_profile(
            catalog,
            resolved,
            repo_root=repo_path,
            check_inventory_baseline=True,
        )
    except profile_policy.ProfilePolicyError as exc:
        raise click.ClickException(str(exc)) from exc

    report = profile_policy.render_profile_doctor_report(inventory)
    if json_output:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return
    sys.stdout.write(profile_policy.format_profile_doctor_human(inventory))
    inv = report.get("invariants") or {}
    if inv.get("pal_http_selected") or inv.get("playwright_in_core") or inv.get(
        "github_writes_visible"
    ):
        sys.exit(1)


@mcp.group("profile")
def mcp_profile_group():
    """🎛️ MCP profiles: list/show task-selected tool planes (ADR-DMX-MCPPROF-001)."""


@mcp_profile_group.command("list")
@click.option("--json", "json_output", is_flag=True, help="Emit profile names as JSON.")
def mcp_profile_list_cmd(json_output: bool):
    """List declared profiles (no implicit all)."""
    from dopemux.mcp import profile_policy

    catalog = _load_catalog()
    try:
        names = profile_policy.list_profiles(catalog)
    except profile_policy.ProfilePolicyError as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        sys.stdout.write(json.dumps({"profiles": names}, indent=2) + "\n")
        return
    if not names:
        console.logger.info("[warning]No profiles declared in catalog.[/warning]")
        return
    console.logger.info(f"[info]Profiles ({len(names)}):[/info]")
    profiles = catalog.get("profiles") or {}
    for name in names:
        desc = ""
        spec = profiles.get(name) or {}
        if isinstance(spec, dict):
            desc = str(spec.get("description") or "")
        console.logger.info(f"  • {name}" + (f" — {desc}" if desc else ""))
    console.logger.info(
        f"[info]Compatibility default: {profile_policy.COMPATIBILITY_PROFILE}[/info]"
    )


@mcp_profile_group.command("show")
@click.argument("name")
@click.option("--json", "json_output", is_flag=True, help="Emit full inventory JSON.")
@click.option(
    "--repo",
    "repo_arg",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Repo root for domain-read validation (defaults to current git root).",
)
def mcp_profile_show_cmd(name: str, json_output: bool, repo_arg: Optional[Path]):
    """Show selected servers, visible tools, and digests for a profile."""
    from dopemux.mcp import profile_policy

    catalog = _load_catalog()
    if repo_arg is not None:
        repo_path = Path(repo_arg).expanduser().resolve()
    else:
        repo = get_repo_root(fallback_cwd=False)
        repo_path = Path(repo).resolve() if repo else None

    try:
        profile_policy.assert_no_implicit_all(name)
        inventory = profile_policy.resolve_profile(
            catalog,
            name,
            repo_root=repo_path,
            check_inventory_baseline=True,
        )
    except profile_policy.ProfilePolicyError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        sys.stdout.write(json.dumps(inventory.to_dict(), indent=2, sort_keys=True) + "\n")
        return
    sys.stdout.write(profile_policy.format_profile_doctor_human(inventory))


def _functional_subset(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Strip advisory fields (description) for diff purposes — they're documentation, not config."""
    return {k: v for k, v in entry.items() if k != "description"}


def _resolve_repo_arg(repo_arg: Optional[Path], *, trust_env: bool = False) -> Path:
    """Resolve --repo or current git root to an absolute path."""
    if repo_arg is not None:
        return _git_toplevel(repo_arg)
    repo = get_repo_root(fallback_cwd=False, trust_env=trust_env)
    if not repo:
        raise click.ClickException(
            "Not inside a git repository. Pass --repo <path> to target another project."
        )
    return Path(repo).resolve()


def _require_exactly_one_dry_run_or_apply(dry_run: bool, apply: bool) -> None:
    if dry_run and apply:
        raise click.ClickException("Pass exactly one of --dry-run or --apply (not both).")
    if not dry_run and not apply:
        raise click.ClickException(
            "Pass exactly one of --dry-run or --apply. "
            "Preview with --dry-run; write local config with --apply."
        )


@mcp.group("leases")
def mcp_leases_group():
    """🔐 Port leases: inspect/reconcile operational lease registry (006R)."""


@mcp_leases_group.command("reconcile")
@click.option("--dry-run", is_flag=True, help="Plan only; write nothing.")
@click.option("--apply", is_flag=True, help="Release invalid singleton leases after backup.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON plan/result.")
def mcp_leases_reconcile_cmd(dry_run: bool, apply: bool, json_output: bool):
    """
    Release invalid project/worktree leases on reserved singleton ports (e.g. 7890).

    Does not stop containers. Backs up the registry before apply.
    """
    _require_exactly_one_dry_run_or_apply(dry_run, apply)
    from dopemux.mcp.port_allocator import singleton_reserved_ports
    from dopemux.mcp.port_leases import PortLeaseRegistry

    catalog = _load_catalog()
    reserved = singleton_reserved_ports(catalog)
    # Always treat 7890 as reserved for TO even if catalog lagging
    reserved.setdefault(7890, "task-orchestrator")
    reg = PortLeaseRegistry.load()
    if reg.parse_status == "ERROR":
        raise click.ClickException(f"Lease registry unreadable: {reg.error}")
    plan = reg.reconcile_reserved_singleton_leases(reserved, dry_run=not apply)
    if apply and plan.get("invalid_count"):
        # re-run applied path already in reconcile when dry_run=False
        pass
    if json_output:
        sys.stdout.write(json.dumps(plan, indent=2) + "\n")
    else:
        console.logger.info(
            f"[info]leases reconcile dry_run={plan.get('dry_run')} "
            f"invalid={plan.get('invalid_count')} applied={plan.get('applied')}[/info]"
        )
        for item in plan.get("invalid_leases") or []:
            console.logger.info(
                f"  • port={item.get('port')} lease={item.get('lease_id')} "
                f"root={item.get('project_root')} — {item.get('reason')}"
            )
        if plan.get("backup_path"):
            console.logger.info(f"[info]backup: {plan['backup_path']}[/info]")


@mcp.group("registry")
def mcp_registry_group():
    """📇 Runtime registry: inspect/reconcile ~/.dopemux/mcp/runtime/instances.json"""


@mcp_registry_group.command("reconcile")
@click.option("--dry-run", is_flag=True, help="Plan only; write nothing.")
@click.option("--apply", is_flag=True, help="Mark stale running instances stopped after backup.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON plan/result.")
def mcp_registry_reconcile_cmd(dry_run: bool, apply: bool, json_output: bool):
    """
    Mark registry instances stopped when their containers are not running.

    Lists `running` entries whose containers are absent from `docker ps` and, with
    --apply, backs the registry up and marks them `stopped` with a NOT_RUNNING
    probe record. Never deletes entries and never touches containers.

    WARNING: --apply rewrites instances.json without a cross-process lock. Never
    run it concurrently with `dopemux mcp start/stop/restart/up/down` or another
    reconcile.
    """
    _require_exactly_one_dry_run_or_apply(dry_run, apply)
    import dopemux.mcp.docker_inspect as docker_inspect
    from dopemux.mcp.runtime_registry import RegistryError, RuntimeRegistry

    reg = RuntimeRegistry.load()
    if reg.parse_status == "ERROR":
        raise click.ClickException(f"Runtime registry unreadable: {reg.error}")
    inspected = docker_inspect.inspect_running_containers()
    if not inspected.available:
        raise click.ClickException(
            f"Docker unavailable; registry left unchanged: {inspected.error}"
        )
    running = {c.name for c in inspected.containers}
    try:
        plan = reg.reconcile_stale_running(running, dry_run=not apply)
    except RegistryError as exc:
        raise click.ClickException(str(exc)) from exc
    if json_output:
        sys.stdout.write(json.dumps(plan, indent=2) + "\n")
        return
    click.echo(
        f"registry reconcile dry_run={plan['dry_run']} "
        f"stale={plan['stale_count']} applied={plan['applied']}"
    )
    for item in plan["stale"]:
        click.echo(
            f"  - {item['instance_id']} service={item['service']} "
            f"root={item['project_root']} containers={','.join(item['container_names'])}"
        )
    if plan.get("backup_path"):
        click.echo(f"backup: {plan['backup_path']}")


@mcp.command("repair-config")
@click.option(
    "--repo",
    "repo_arg",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Target repo/worktree (defaults to current git root).",
)
@_trust_env_option()
@click.option("--dry-run", is_flag=True, help="Plan only; write nothing.")
@click.option("--apply", is_flag=True, help="Write local .mcp.json / envrc / agent bootstrap doc.")
@click.option("--json", "json_output", is_flag=True, help="Emit repair plan JSON to stdout.")
def mcp_repair_config_cmd(
    repo_arg: Optional[Path],
    trust_env: bool,
    dry_run: bool,
    apply: bool,
    json_output: bool,
):
    """
    🔧 Repair local MCP config: .mcp.json transports, envrc, agent bootstrap

    Previewable and idempotent. Never mutates ~/.claude.json and never starts
    or stops containers. Unknown/custom mcpServers entries are preserved.

    Examples:
      dopemux mcp repair-config --dry-run --json
      dopemux mcp repair-config --repo ~/code/other --apply
    """
    _require_exactly_one_dry_run_or_apply(dry_run, apply)

    from dopemux.mcp.config_repair import apply_repair, format_repair_human, plan_repair

    repo_path = _resolve_repo_arg(repo_arg, trust_env=trust_env)
    catalog = _load_catalog(repo_path)
    catalog_path = _catalog_path(repo_path)
    catalog_paths = [str(catalog_path)] if catalog_path else ["bundled:default_catalog.yaml"]

    plan = plan_repair(
        repo_path,
        catalog,
        dry_run=dry_run,
        catalog_paths=catalog_paths,
        process_env=dict(os.environ),
        trust_env=trust_env,
    )

    if apply and plan.status != "BLOCKED":
        plan.dry_run = False
        plan = apply_repair(plan)

    if json_output:
        sys.stdout.write(plan.to_json())
    else:
        summary = format_repair_human(plan)
        if plan.status in {"APPLIED", "NOOP"}:
            console.logger.info(f"[success]{summary.rstrip()}[/success]")
        elif plan.status == "BLOCKED":
            console.logger.info(f"[error]{summary.rstrip()}[/error]")
        else:
            console.logger.info(f"[info]{summary.rstrip()}[/info]")

    if plan.status == "BLOCKED":
        sys.exit(2)


@mcp.group("fleet")
def mcp_fleet_group():
    """
    🚢 Fleet: multi-worktree MCP config init and doctor aggregation

    Config-only operations. Does not start containers or mutate globals.
    """


@mcp_fleet_group.command("init")
@click.option(
    "--repo",
    "repo_arg",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Project root that owns the worktrees.",
)
@click.option(
    "--worktrees",
    "worktrees",
    required=True,
    multiple=True,
    type=click.Path(path_type=Path),
    help="Worktree paths (repeatable).",
)
@click.option("--dry-run", is_flag=True, help="Plan only; write nothing.")
@click.option("--apply", is_flag=True, help="Apply repair-config per valid worktree.")
@click.option("--json", "json_output", is_flag=True, help="Emit fleet-init JSON to stdout.")
def mcp_fleet_init_cmd(
    repo_arg: Path,
    worktrees: Tuple[Path, ...],
    dry_run: bool,
    apply: bool,
    json_output: bool,
):
    """
    Scaffold/repair MCP config across worktrees (no container start).
    """
    _require_exactly_one_dry_run_or_apply(dry_run, apply)
    if not worktrees:
        raise click.ClickException("Pass at least one --worktrees path.")

    from dopemux.mcp.fleet import fleet_init, format_fleet_init_human

    catalog = _load_catalog()
    catalog_path = _catalog_path()
    catalog_paths = [str(catalog_path)] if catalog_path else ["bundled:default_catalog.yaml"]

    report = fleet_init(
        repo_arg,
        list(worktrees),
        catalog,
        dry_run=dry_run,
        apply=apply,
        catalog_paths=catalog_paths,
    )

    if json_output:
        sys.stdout.write(report.to_json())
    else:
        console.logger.info(f"[info]{format_fleet_init_human(report).rstrip()}[/info]")

    if report.status in {"FAIL", "UNKNOWN"}:
        sys.exit(1)


@mcp_fleet_group.command("doctor")
@click.option(
    "--repo",
    "repo_arg",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Project root that owns the worktrees.",
)
@click.option(
    "--worktrees",
    "worktrees",
    required=True,
    multiple=True,
    type=click.Path(path_type=Path),
    help="Worktree paths (repeatable).",
)
@click.option("--json", "json_output", is_flag=True, help="Emit fleet-doctor JSON to stdout.")
@click.option(
    "--skip-docker/--probe-docker",
    default=True,
    help="Skip Docker inspection per worktree (default: skip for speed).",
)
def mcp_fleet_doctor_cmd(
    repo_arg: Path,
    worktrees: Tuple[Path, ...],
    json_output: bool,
    skip_docker: bool,
):
    """
    Aggregate Packet 001 doctor results across worktrees (read-only).
    """
    if not worktrees:
        raise click.ClickException("Pass at least one --worktrees path.")

    from dopemux.mcp.fleet import fleet_doctor, format_fleet_doctor_human

    catalog = _load_catalog()
    catalog_path = _catalog_path()
    catalog_paths = [str(catalog_path)] if catalog_path else ["bundled:default_catalog.yaml"]

    report = fleet_doctor(
        repo_arg,
        list(worktrees),
        catalog,
        catalog_paths=catalog_paths,
        skip_docker=skip_docker,
        process_env=dict(os.environ),
    )

    if json_output:
        sys.stdout.write(report.to_json())
    else:
        console.logger.info(f"[info]{format_fleet_doctor_human(report).rstrip()}[/info]")

    if report.status in {"FAIL", "UNKNOWN"}:
        sys.exit(1)


@mcp.command("sync-globals")
@click.option("--apply", is_flag=True, help="Actually write ~/.claude.json (default: dry-run with diff).")
@click.option("--prune", is_flag=True, help="Remove singletons that exist in ~/.claude.json but not the catalog (default: keep them).")
def mcp_sync_globals_cmd(apply: bool, prune: bool):
    """
    🌐 Promote Singletons: Reconcile ~/.claude.json mcpServers with the catalog

    Defaults to dry-run: prints the functional diff between `~/.claude.json`
    `mcpServers` and the catalog's singletons. User-set descriptions are
    preserved on apply; only functional fields (type, url, command, args, env)
    are changed. Pass --apply to write (after a timestamped backup).
    Pass --prune to remove existing globals that aren't in the catalog.
    """
    catalog = _load_catalog()
    desired = _build_global_mcp_servers(catalog)

    global_path = _claude_global_path()
    global_data = _read_json(global_path) if global_path.exists() else {}
    current = global_data.get("mcpServers", {}) or {}

    additions = sorted(set(desired) - set(current))
    removals = sorted(set(current) - set(desired))
    changed = sorted(
        n for n in (set(desired) & set(current))
        if _functional_subset(current[n]) != _functional_subset(desired[n])
    )

    if not (additions or (prune and removals) or changed):
        console.logger.info("[success]~/.claude.json mcpServers already matches the catalog (functionally).[/success]")
        if removals and not prune:
            console.logger.info(
                f"[info]Note: {len(removals)} extra entries in global config (not in catalog): "
                f"{', '.join(removals)}. Pass --prune to remove them.[/info]"
            )
        return

    console.logger.info("[info]Planned changes to ~/.claude.json mcpServers:[/info]")
    for n in additions:
        console.logger.info(f"  [success]+ {n}[/success]")
    if prune:
        for n in removals:
            console.logger.info(f"  [warning]- {n} (in ~/.claude.json but not catalog)[/warning]")
    else:
        for n in removals:
            console.logger.info(f"  [info]· {n} (kept; pass --prune to remove)[/info]")
    for n in changed:
        console.logger.info(f"  [info]~ {n} (functional drift)[/info]")

    if not apply:
        console.logger.info("")
        console.logger.info("[info]Dry-run only. Re-run with --apply to write.[/info]")
        return

    # Build the merged result: catalog defines functional fields,
    # but preserve any user-set descriptions on existing entries.
    merged: Dict[str, Any] = {}
    for name, new_entry in desired.items():
        existing = current.get(name) or {}
        merged_entry = dict(new_entry)
        if "description" in existing and "description" not in merged_entry:
            merged_entry["description"] = existing["description"]
        merged[name] = merged_entry
    if not prune:
        # Keep entries that are in current but not in catalog.
        for name, entry in current.items():
            if name not in merged:
                merged[name] = entry

    backup = _backup_path(global_path)
    if global_path.exists():
        backup.write_bytes(global_path.read_bytes())
        console.logger.info(f"[info]Backup: {backup}[/info]")

    new_data = dict(global_data)
    new_data["mcpServers"] = merged
    _atomic_write_json(global_path, new_data)
    console.logger.info(f"[success]Wrote {global_path}.[/success]")


@mcp.command("snapshot-tools")
@click.option(
    "--seed-from",
    "seed_from",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Ingest prior tools/list probe captures (verdict OK only) from this directory.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Snapshot file to read/write (default: <repo-root>/mcp_tool_surfaces.json).",
)
@click.option(
    "--offline",
    is_flag=True,
    help="Skip live probing; only ingest --seed-from (or reuse the existing file untouched).",
)
@click.option(
    "--timeout",
    type=float,
    default=6.0,
    show_default=True,
    help="Per-server network timeout (seconds) for live tools/list probes.",
)
def mcp_snapshot_tools_cmd(
    seed_from: Optional[Path],
    output_path: Optional[Path],
    offline: bool,
    timeout: float,
):
    """
    📸 Freeze Tool Surfaces: Capture every catalog server's MCP tools/list into a committed snapshot

    Builds/updates `mcp_tool_surfaces.json` — the docker-down cache the
    (future) tool-granular drift gate and doc generators consume. Loads any
    existing snapshot file as a base, optionally ingests seed capture files
    (`--seed-from`), then optionally probes the live fleet's `tools/list`
    surface for every catalog server (skip with `--offline`). Fresh data
    always wins over stale data except when the fresh probe is itself
    `unreachable` and the base already has better data for that server.
    """
    from dopemux.mcp import tool_snapshot

    catalog = _load_catalog()

    if output_path is None:
        repo = get_repo_root(fallback_cwd=False)
        if not repo:
            raise click.ClickException(
                "Not inside a git repository; pass --output explicitly."
            )
        output_path = Path(repo) / "mcp_tool_surfaces.json"

    snapshot = tool_snapshot.load_snapshot(output_path)

    if seed_from is not None:
        seed_snapshot = tool_snapshot.snapshot_from_seed(seed_from)
        snapshot = tool_snapshot.merge_snapshots(snapshot, seed_snapshot)

    if not offline:
        live_snapshot = tool_snapshot.snapshot_from_live(catalog, timeout=timeout)
        snapshot = tool_snapshot.merge_snapshots(snapshot, live_snapshot)

    servers = snapshot.get("servers") or {}
    if not servers:
        raise click.ClickException(
            "Refusing to write an empty snapshot (0 servers). "
            "Pass --seed-from with capture files, or run with the fleet up (drop --offline)."
        )

    try:
        output_path.write_text(tool_snapshot.dump_snapshot(snapshot), encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Failed to write {output_path}: {exc}") from exc

    console.logger.info(
        f"[success]Wrote {output_path} ({len(servers)} server(s))[/success]"
    )
    console.logger.info("[info]== Tool Surfaces ==[/info]")
    for name in sorted(servers):
        entry = servers[name]
        source = entry.get("source", "?")
        tool_count = entry.get("tool_count", 0)
        console.logger.info(f"  {name:<20} source={source:<11} tools={tool_count}")


# ---------------------------------------------------------------------------
# P1 fleet control plane: read-only identity/catalog/reconcile preview
# (TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001).
#
# Both commands below only ever read state and print it. Neither creates the
# identity registry or the service-lease store if either is absent
# (create_missing=False), neither writes mcp_catalog.yaml, and neither
# selects/starts/stops/adopts a service. They exist so an operator can
# inspect P1's dormant infrastructure without touching the live v1 catalog
# pipeline (_load_catalog/load_root_catalog, unchanged above).
# ---------------------------------------------------------------------------


@mcp.group("control-plane")
def mcp_control_plane_group():
    """
    🧭 P1 fleet control plane: read-only identity/catalog/reconcile preview.

    Dormant infrastructure only -- no service starts, no catalog writes, no
    registry auto-creation. See docs/03-reference/mcp/multiproject-control-plane.md.
    """


@mcp_control_plane_group.command("identity")
@click.option(
    "--repo",
    "repo_arg",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Repo/worktree path to resolve identity for (default: cwd).",
)
@click.option("--json", "json_output", is_flag=True, help="Emit the resolved-execution-identity JSON.")
def mcp_control_plane_identity_cmd(repo_arg: Optional[Path], json_output: bool):
    """
    Preview registry-backed execution identity for a path (read-only).

    Never creates the identity registry: if none exists, resolution is
    UNKNOWN by design (dormant/default-off), not an error.
    """
    import getpass

    from dopemux.mcp.identity import resolve_execution_identity
    from dopemux.mcp.identity_registry import IdentityRegistry

    cwd = (repo_arg or Path.cwd()).resolve()
    registry = IdentityRegistry.load(create_missing=False)
    resolved = resolve_execution_identity(
        cwd=cwd,
        registry=registry,
        actor_id=getpass.getuser() or "unknown-actor",
        client_id="dopemux-cli",
    )

    if json_output:
        sys.stdout.write(json.dumps(resolved.to_schema_dict(), indent=2, sort_keys=True) + "\n")
        return
    console.logger.info(f"[info]resolution_status={resolved.resolution_status}[/info]")
    console.logger.info(f"[info]project_id={resolved.project_id}[/info]")
    console.logger.info(f"[info]workspace_id={resolved.workspace_id}[/info]")
    console.logger.info(f"[info]instance_id={resolved.instance_id}[/info]")
    console.logger.info(f"[info]mutable_routing_allowed={resolved.mutable_routing_allowed}[/info]")


@mcp_control_plane_group.command("reconcile")
@click.option(
    "--repo",
    "repo_arg",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Repo/worktree path to build the plan for (default: cwd).",
)
@click.option("--json", "json_output", is_flag=True, help="Emit the reconcile report JSON.")
def mcp_control_plane_reconcile_cmd(repo_arg: Optional[Path], json_output: bool):
    """
    Preview a read-only reconcile/control-plane plan (no executor).

    Compiles the live v1 catalog to an in-memory v2 projection, resolves
    identity, and reads the service-lease store (never creating it) to
    classify each service MATCHED/MISSING/FOREIGN/AMBIGUOUS/STALE/
    LEGACY_UNBOUND. A blocked plan (e.g. identity not VERIFIED) is a normal,
    exit-0 result, not a CLI error.
    """
    import getpass

    from dopemux.mcp import fleet_catalog
    from dopemux.mcp.control_plane import build_control_plane_plan
    from dopemux.mcp.identity import resolve_execution_identity
    from dopemux.mcp.identity_registry import IdentityRegistry
    from dopemux.mcp.service_leases import ServiceLeaseRegistry

    repo = (repo_arg or get_repo_root(fallback_cwd=True) or Path.cwd())
    repo = Path(repo).resolve()

    v1_catalog = fleet_catalog.load_root_catalog(repo)
    topology_path = repo / "docs/03-reference/mcp/multiproject-service-topology.json"
    topology = json.loads(topology_path.read_text(encoding="utf-8"))
    catalog_v2 = fleet_catalog.compile_catalog_v2(v1_catalog, topology)

    identity_registry = IdentityRegistry.load(create_missing=False)
    resolved = resolve_execution_identity(
        cwd=repo,
        registry=identity_registry,
        actor_id=getpass.getuser() or "unknown-actor",
        client_id="dopemux-cli",
    )
    lease_registry = ServiceLeaseRegistry.load(create_missing=False)

    plan = build_control_plane_plan(
        resolved_identity=resolved, catalog_v2=catalog_v2, lease_registry=lease_registry
    )

    if json_output:
        payload = {
            "resolved_identity": plan.resolved_identity.to_schema_dict(),
            "blockers": list(plan.blockers),
            "selected_service_count": len(plan.selected_services),
            "reconcile": [
                {
                    "service_id": e.service_id,
                    "status": str(e.status),
                    "lease_verdict": e.lease_verdict,
                    "recommendation": e.recommendation,
                }
                for e in plan.reconcile.entries
            ],
        }
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return

    if plan.is_blocked:
        console.logger.info("[error]blocked:[/error]")
        for reason in plan.blockers:
            console.logger.info(f"[error]  - {reason}[/error]")
        return

    console.logger.info(
        f"[info]identity: project_id={plan.resolved_identity.project_id} "
        f"workspace_id={plan.resolved_identity.workspace_id} "
        f"instance_id={plan.resolved_identity.instance_id}[/info]"
    )
    for entry in plan.reconcile.entries:
        console.logger.info(f"[info]  {entry.service_id:<24} {entry.status:<14} {entry.recommendation}[/info]")
