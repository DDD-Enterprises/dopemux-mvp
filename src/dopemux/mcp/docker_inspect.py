"""Read-only Docker inspection helpers for MCP doctor.

Never starts/stops containers. Docker unavailable produces structured findings,
not crashes.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence


# Labels we understand for project ownership (Packet 002 may expand these).
PROJECT_LABEL_KEYS = (
    "dopemux.project_id",
    "dopemux.project_root",
    "dopemux.workspace_id",
    "dopemux.worktree_root",
    "com.dopemux.project_id",
    "com.dopemux.project_root",
    "com.dopemux.workspace_id",
)


@dataclass
class DockerContainerInfo:
    """Normalized container snapshot."""

    id: str
    name: str
    image: str = ""
    status: str = ""
    ports: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    published_ports: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "status": self.status,
            "ports": list(self.ports),
            "labels": _redact_labels(self.labels),
            "published_ports": list(self.published_ports),
        }


@dataclass
class DockerInspectResult:
    """Result of a read-only docker inspection pass."""

    available: bool
    error: Optional[str] = None
    containers: List[DockerContainerInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "error": self.error,
            "containers": [c.to_dict() for c in self.containers],
        }


def _redact_labels(labels: Dict[str, str]) -> Dict[str, str]:
    redacted: Dict[str, str] = {}
    for key, value in labels.items():
        upper = key.upper()
        if any(m in upper for m in ("SECRET", "TOKEN", "PASSWORD", "KEY", "CREDENTIAL")):
            # Allow identity-like keys even if they contain "KEY" substring carefully
            if "project" in key.lower() or "workspace" in key.lower() or "instance" in key.lower():
                redacted[key] = value
            else:
                redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted


def _parse_published_ports(ports_field: str) -> List[int]:
    """Extract host ports from docker ps Ports column or JSON Port bindings string."""
    found: List[int] = []
    if not ports_field:
        return found
    # Formats: "0.0.0.0:3041->3005/tcp, :::3041->3005/tcp" or "3041/tcp"
    for part in ports_field.replace(",", " ").split():
        if "->" in part:
            left = part.split("->", 1)[0]
            host_port = left.rsplit(":", 1)[-1]
            try:
                found.append(int(host_port))
            except ValueError:
                continue
        elif part.endswith("/tcp") or part.endswith("/udp"):
            # container-only publish without host mapping — skip
            continue
    return sorted(set(found))


def parse_docker_ps_json_lines(text: str) -> List[DockerContainerInfo]:
    """Parse `docker ps --format '{{json .}}'` newline-delimited JSON."""
    containers: List[DockerContainerInfo] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        labels_raw = row.get("Labels") or row.get("labels") or ""
        labels: Dict[str, str] = {}
        if isinstance(labels_raw, dict):
            labels = {str(k): str(v) for k, v in labels_raw.items()}
        elif isinstance(labels_raw, str) and labels_raw:
            for piece in labels_raw.split(","):
                if "=" in piece:
                    k, v = piece.split("=", 1)
                    labels[k.strip()] = v.strip()
        ports_field = str(row.get("Ports") or row.get("ports") or "")
        name = str(row.get("Names") or row.get("names") or row.get("Name") or "")
        # docker --format json uses Names as comma-separated; take first
        name = name.split(",")[0].lstrip("/")
        containers.append(
            DockerContainerInfo(
                id=str(row.get("ID") or row.get("Id") or row.get("id") or "")[:12],
                name=name,
                image=str(row.get("Image") or row.get("image") or ""),
                status=str(row.get("Status") or row.get("status") or ""),
                ports=[ports_field] if ports_field else [],
                labels=labels,
                published_ports=_parse_published_ports(ports_field),
            )
        )
    return containers


Runner = Callable[..., subprocess.CompletedProcess]


def inspect_running_containers(
    *,
    runner: Optional[Runner] = None,
    timeout: float = 25.0,
) -> DockerInspectResult:
    """List running containers via `docker ps` (read-only)."""
    run = runner or subprocess.run
    if runner is None and shutil.which("docker") is None:
        return DockerInspectResult(available=False, error="docker binary not found on PATH")

    try:
        result = run(
            [
                "docker",
                "ps",
                "--format",
                "{{json .}}",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return DockerInspectResult(available=False, error="docker binary not found")
    except subprocess.TimeoutExpired:
        return DockerInspectResult(available=False, error="docker ps timed out")
    except OSError as exc:
        return DockerInspectResult(available=False, error=f"docker ps failed: {exc}")

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "docker ps failed").strip()
        return DockerInspectResult(available=False, error=err[:500])

    containers = parse_docker_ps_json_lines(result.stdout or "")
    return DockerInspectResult(available=True, containers=containers)


def classify_container_ownership(
    container: DockerContainerInfo,
    *,
    project_root: Optional[str],
    workspace_id: Optional[str],
    project_id: Optional[str],
    expected_ports: Sequence[int] = (),
    expected_name_substrings: Sequence[str] = (),
    project_slug_hints: Sequence[str] = (),
) -> str:
    """
    Return label_status:
      MATCH | WRONG_PROJECT | UNLABELED | UNKNOWN | SKIPPED | COMPOSE_MATCH

    Trust order:
      1. explicit dopemux.* labels
      2. compose project/service + name/port heuristics (secondary)
      3. name/port alone → UNLABELED (never ownership proof)
    """
    labels = container.labels or {}
    has_project_labels = any(k in labels for k in PROJECT_LABEL_KEYS)

    # Name / port match heuristics
    name_l = (container.name or "").lower()
    name_match = any(s.lower() in name_l for s in expected_name_substrings if s)
    port_match = bool(set(container.published_ports) & set(expected_ports))

    # Compose secondary evidence (006R)
    compose_project = (
        labels.get("com.docker.compose.project")
        or labels.get("com.docker.compose.project.name")
        or ""
    ).lower()
    compose_workdir = labels.get("com.docker.compose.project.working_dir") or ""
    compose_service = (labels.get("com.docker.compose.service") or "").lower()

    slug_hints = [s.lower().replace("_", "").replace("-", "") for s in project_slug_hints if s]
    if project_root:
        slug_hints.append(Path(project_root).name.lower().replace("_", "").replace("-", ""))
    if project_id:
        slug_hints.append(str(project_id).lower().replace("_", "").replace("-", "")[:16])

    def _slug_in(text: str) -> bool:
        t = text.lower().replace("_", "").replace("-", "")
        return any(h and h in t for h in slug_hints)

    compose_project_match = bool(compose_project and _slug_in(compose_project))
    compose_workdir_match = bool(
        compose_workdir and project_root and _norm_path(compose_workdir) == _norm_path(project_root)
    )
    name_slug_match = bool(name_l and _slug_in(name_l))

    if not has_project_labels:
        # Secondary: compose + name/port strongly associate with target
        if (compose_project_match or compose_workdir_match or name_slug_match) and (
            name_match or port_match or compose_service
        ):
            # Not ideal ownership (no explicit labels) but not "not found"
            return "COMPOSE_MATCH"
        if name_match or port_match:
            return "UNLABELED"
        return "UNKNOWN"

    # Compare known labels
    label_project_root = (
        labels.get("dopemux.project_root")
        or labels.get("com.dopemux.project_root")
    )
    label_workspace = (
        labels.get("dopemux.workspace_id")
        or labels.get("com.dopemux.workspace_id")
        or labels.get("dopemux.worktree_root")
    )
    label_project_id = labels.get("dopemux.project_id") or labels.get("com.dopemux.project_id")

    mismatches: List[str] = []
    if project_root and label_project_root:
        if _norm_path(label_project_root) != _norm_path(project_root):
            mismatches.append("project_root")
    if workspace_id and label_workspace:
        if _norm_path(label_workspace) != _norm_path(workspace_id):
            mismatches.append("workspace_id")
    if project_id and label_project_id:
        if label_project_id != project_id:
            mismatches.append("project_id")

    if mismatches:
        return "WRONG_PROJECT"
    if label_project_root or label_workspace or label_project_id:
        return "MATCH"
    return "UNKNOWN"


def _norm_path(value: str) -> str:
    return str(value).rstrip("/")


def inspect_container_mounts(
    container_id: str,
    *,
    runner: Optional[Runner] = None,
    timeout: float = 15.0,
) -> List[str]:
    """Read-only ``docker inspect --format '{{json .Mounts}}'`` for one
    container, normalized to a sorted list of ``"<source>:<destination>"``
    strings.

    P1 ownership evidence (``ownership.py``) uses this as storage/mount
    corroboration only -- one of the four evidence classes required for
    ``mutation_eligible``, never sufficient by itself. Never starts, stops,
    or otherwise mutates anything; an unavailable/erroring docker binary
    yields an empty list rather than raising.
    """

    run = runner or subprocess.run
    if runner is None and shutil.which("docker") is None:
        return []
    try:
        result = run(
            ["docker", "inspect", "--format", "{{json .Mounts}}", container_id],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode != 0:
        return []
    try:
        mounts = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(mounts, list):
        return []
    out: List[str] = []
    for mount in mounts:
        if not isinstance(mount, dict):
            continue
        source = str(mount.get("Source") or "")
        dest = str(mount.get("Destination") or "")
        if source and dest:
            out.append(f"{source}:{dest}")
    return sorted(set(out))


def find_containers_for_service(
    docker: DockerInspectResult,
    *,
    service_name: str,
    expected_ports: Sequence[int] = (),
    name_hints: Sequence[str] = (),
) -> List[DockerContainerInfo]:
    """Find containers that might belong to a service by name/port heuristics."""
    if not docker.available:
        return []
    hints = [h.lower() for h in name_hints if h]
    if service_name:
        hints.append(service_name.lower().replace("_", "-"))
        hints.append(service_name.lower().replace("-", "_"))
    matches: List[DockerContainerInfo] = []
    for c in docker.containers:
        name_l = c.name.lower()
        if any(h in name_l for h in hints):
            matches.append(c)
            continue
        if expected_ports and set(c.published_ports) & set(expected_ports):
            matches.append(c)
    return matches
