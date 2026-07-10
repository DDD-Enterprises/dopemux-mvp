"""Docker/compose execution helpers for repo-aware MCP lifecycle.

Preferred strategy: generated compose override + env file + unique project name,
with --no-deps for project sidecars (shared infra assumed already running).

task-orchestrator uses a wrapper-compatible docker run path (fixed host port)
with Dopemux labels applied at create time.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

Runner = Callable[..., subprocess.CompletedProcess]

LABEL_MANAGED = "dopemux.managed"
LABEL_CREATED_BY = "dopemux.created_by"


def product_root() -> Path:
    """Locate dopemux-mvp product root (compose.yml + scripts)."""
    env = os.environ.get("DOPEMUX_MVP_ROOT") or os.environ.get("DOPEMUX_PRODUCT_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "compose.yml").is_file():
            return p
    # src/dopemux/mcp/docker_runtime.py → repo root
    here = Path(__file__).resolve()
    candidate = here.parents[3]
    if (candidate / "compose.yml").is_file():
        return candidate
    # Fall back: walk parents
    for parent in here.parents:
        if (parent / "compose.yml").is_file() and (parent / "mcp_catalog.yaml").is_file():
            return parent
    raise FileNotFoundError(
        "Cannot locate dopemux product root with compose.yml. "
        "Set DOPEMUX_MVP_ROOT to the dopemux-mvp checkout."
    )


def project_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug or "workspace")[:40]


def container_name_for(slug: str, worktree_hash: str, service: str) -> str:
    svc = service.replace("_", "-").lower()
    # Docker name max 63; keep deterministic short form
    base = f"dopemux-{slug}-{worktree_hash}-{svc}"
    return base[:63].rstrip("-")


def compose_project_name(slug: str, worktree_hash: str) -> str:
    name = f"dopemux_{slug}_{worktree_hash}".lower()
    return re.sub(r"[^a-z0-9_-]", "_", name)[:63]


def build_labels(
    *,
    project_id: str,
    workspace_id: str,
    project_root: str,
    worktree_root: str,
    project_hash: str,
    worktree_hash: str,
    instance_id: str,
    service: str,
    scope: str,
    transport: str = "unknown",
    catalog_service: Optional[str] = None,
) -> Dict[str, str]:
    return {
        LABEL_MANAGED: "true",
        "dopemux.project_id": project_id,
        "dopemux.workspace_id": workspace_id,
        "dopemux.project_root": project_root,
        "dopemux.worktree_root": worktree_root,
        "dopemux.project_hash": project_hash,
        "dopemux.worktree_hash": worktree_hash,
        "dopemux.instance_id": instance_id,
        "dopemux.service": service,
        "dopemux.scope": scope,
        LABEL_CREATED_BY: "dopemux-mcp",
        "dopemux.repo_basename": Path(project_root).name,
        "dopemux.catalog_service": catalog_service or service,
        "dopemux.transport": transport,
    }


def labels_as_compose_map(labels: Mapping[str, str]) -> str:
    lines = ["    labels:"]
    for key in sorted(labels.keys()):
        val = str(labels[key]).replace('"', '\\"')
        lines.append(f'      {key}: "{val}"')
    return "\n".join(lines)


def generate_compose_override(
    *,
    services: Sequence[str],
    identity: Mapping[str, str],
    ports: Mapping[str, int],
    container_names: Mapping[str, str],
    labels_by_service: Mapping[str, Mapping[str, str]],
    memory_data_path: Path,
) -> str:
    """Generate compose.override.yml that neutralizes fixed names + relative volumes."""
    blocks: List[str] = ["services:"]

    if "conport" in services:
        cname = container_names["conport"]
        labels = labels_as_compose_map(labels_by_service["conport"])
        blocks.append(
            f"""  conport:
    container_name: {cname}
    ports:
      - "{ports.get('CONPORT_HTTP_PORT', 3004)}:3004"
      - "{ports.get('CONPORT_MCP_PORT', 3005)}:3005"
      - "{ports.get('CONPORT_INFO_PORT', 4004)}:4004"
    environment:
      DOPEMUX_INSTANCE_ID: "{identity.get('DOPEMUX_INSTANCE_ID', '')}"
      DOPEMUX_WORKSPACE_ID: "{identity.get('DOPEMUX_WORKSPACE_ID', '')}"
      DOPEMUX_PROJECT_ROOT: "{identity.get('DOPEMUX_PROJECT_ROOT', '')}"
      DOPEMUX_WORKTREE_ROOT: "{identity.get('DOPEMUX_WORKTREE_ROOT', '')}"
      DOPEMUX_WORKSPACE_ROOT: "{identity.get('DOPEMUX_WORKSPACE_ROOT', '')}"
{labels}
"""
        )

    if "dope-memory" in services:
        cname = container_names["dope-memory"]
        labels = labels_as_compose_map(labels_by_service["dope-memory"])
        data = str(memory_data_path.resolve())
        blocks.append(
            f"""  dope-memory:
    container_name: {cname}
    ports:
      - "{ports.get('DOPE_MEMORY_PORT', 3020)}:3020"
    environment:
      DOPE_MEMORY_WORKSPACE_ID: "{identity.get('DOPE_MEMORY_WORKSPACE_ID', '')}"
      DOPE_MEMORY_INSTANCE_ID: "{identity.get('DOPE_MEMORY_INSTANCE_ID', '')}"
      DOPEMUX_WORKSPACE_ID: "{identity.get('DOPEMUX_WORKSPACE_ID', '')}"
      DOPEMUX_PROJECT_ROOT: "{identity.get('DOPEMUX_PROJECT_ROOT', '')}"
      DOPEMUX_WORKTREE_ROOT: "{identity.get('DOPEMUX_WORKTREE_ROOT', '')}"
      DOPEMUX_INSTANCE_ID: "{identity.get('DOPEMUX_INSTANCE_ID', '')}"
    volumes:
      - "{data}:/data"
{labels}
"""
        )

    # External shared network so --no-deps still joins existing mesh
    blocks.append(
        """networks:
  dopemux-network:
    external: true
    name: dopemux-network
"""
    )
    return "\n".join(blocks)


def generate_mcp_env(env_map: Mapping[str, str | int]) -> str:
    lines = ["# Generated by dopemux mcp start — operational ports/paths only"]
    for key in sorted(env_map.keys()):
        val = env_map[key]
        # Skip secret-like keys
        upper = key.upper()
        if any(m in upper for m in ("SECRET", "TOKEN", "PASSWORD", "API_KEY", "CREDENTIAL")):
            continue
        lines.append(f"{key}={val}")
    return "\n".join(lines) + "\n"


@dataclass
class RuntimeCommandResult:
    command: List[str]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": list(self.command),
            "exit_code": self.exit_code,
            "stdout": self.stdout[:2000],
            "stderr": self.stderr[:2000],
            "dry_run": self.dry_run,
        }


def run_cmd(
    cmd: Sequence[str],
    *,
    runner: Optional[Runner] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
    dry_run: bool = False,
    timeout: float = 180.0,
) -> RuntimeCommandResult:
    if dry_run:
        return RuntimeCommandResult(command=list(cmd), exit_code=0, dry_run=True)
    run = runner or subprocess.run
    try:
        result = run(
            list(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=dict(env) if env else None,
            cwd=str(cwd) if cwd else None,
        )
        return RuntimeCommandResult(
            command=list(cmd),
            exit_code=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
        )
    except FileNotFoundError as exc:
        return RuntimeCommandResult(
            command=list(cmd),
            exit_code=127,
            stderr=str(exc),
        )
    except subprocess.TimeoutExpired:
        return RuntimeCommandResult(
            command=list(cmd),
            exit_code=124,
            stderr="command timed out",
        )


def compose_up_command(
    *,
    product: Path,
    override_path: Path,
    env_file: Path,
    project_name: str,
    services: Sequence[str],
    no_deps: bool = True,
) -> List[str]:
    cmd = [
        "docker",
        "compose",
        "-f",
        str(product / "compose.yml"),
        "-f",
        str(override_path),
        "--env-file",
        str(env_file),
        "-p",
        project_name,
        "up",
        "-d",
    ]
    if no_deps:
        cmd.append("--no-deps")
    cmd.extend(list(services))
    return cmd


def compose_stop_command(
    *,
    product: Path,
    override_path: Path,
    env_file: Path,
    project_name: str,
    services: Sequence[str],
) -> List[str]:
    return [
        "docker",
        "compose",
        "-f",
        str(product / "compose.yml"),
        "-f",
        str(override_path),
        "--env-file",
        str(env_file),
        "-p",
        project_name,
        "stop",
        *list(services),
    ]


def docker_rm_force_command(container_name: str) -> List[str]:
    return ["docker", "rm", "-f", container_name]


def docker_stop_command(container_name: str) -> List[str]:
    return ["docker", "stop", container_name]


def task_orchestrator_wrapper_path(product: Path) -> Path:
    return product / "scripts" / "mcp-wrappers" / "task-orchestrator-http-singleton.sh"


def task_orchestrator_start_command(product: Path, *, dry_run: bool = False) -> List[str]:
    script = task_orchestrator_wrapper_path(product)
    cmd = ["bash", str(script)]
    if dry_run:
        cmd.append("--dry-run")
    return cmd


def apply_labels_via_docker_run_note() -> str:
    """Wrapper creates containers without dopemux labels; we re-label by recreate in lifecycle when needed."""
    return (
        "task-orchestrator uses wrapper-singleton script; lifecycle records "
        "container name and attempts label verification post-start"
    )


def write_runtime_artifacts(
    runtime_dir: Path,
    *,
    env_text: str,
    override_text: str,
    plan: Mapping[str, Any],
    dry_run: bool = False,
) -> Dict[str, str]:
    """Write mcp.env, compose.override.yml, start-plan.json under runtime_dir."""
    paths = {
        "mcp.env": runtime_dir / "mcp.env",
        "compose.override.yml": runtime_dir / "compose.override.yml",
        "start-plan.json": runtime_dir / "start-plan.json",
    }
    if dry_run:
        return {k: str(v) for k, v in paths.items()}
    runtime_dir.mkdir(parents=True, exist_ok=True)
    paths["mcp.env"].write_text(env_text, encoding="utf-8")
    paths["compose.override.yml"].write_text(override_text, encoding="utf-8")
    import json

    paths["start-plan.json"].write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {k: str(v) for k, v in paths.items()}


def redact_command(cmd: Sequence[str]) -> str:
    """Shell-ish preview without expanding secrets (commands should not contain secrets)."""
    return " ".join(shlex.quote(c) for c in cmd)
