"""macOS environment detection for system-data cleanup."""

from __future__ import annotations

import os
import platform
import shutil
import socket
from pathlib import Path

from .models import DiskVolume, EnvironmentSnapshot
from .tools import ToolRunner, run_duf


def disk_pressure(free_bytes: int, total_bytes: int) -> str:
    if total_bytes <= 0:
        return "unknown"
    free_ratio = free_bytes / total_bytes
    if free_bytes < 10 * 1024**3 or free_ratio < 0.05:
        return "critical"
    if free_bytes < 25 * 1024**3 or free_ratio < 0.10:
        return "low"
    return "healthy"


def source_volume(path: Path, volumes: tuple[DiskVolume, ...]) -> DiskVolume | None:
    resolved = str(path.expanduser())
    candidates = sorted(volumes, key=lambda volume: len(volume.mount_point), reverse=True)
    for volume in candidates:
        mount = volume.mount_point.rstrip("/") or "/"
        if resolved == mount or resolved.startswith(mount.rstrip("/") + "/"):
            return volume
    return None


def same_device(source: Path, target: Path) -> bool:
    try:
        return source.exists() and target.exists() and os.stat(source).st_dev == os.stat(target).st_dev
    except OSError:
        return False


def full_disk_access_confidence(home: Path) -> str:
    probes = [
        home / "Library" / "Messages",
        home / "Library" / "Containers",
        home / "Library" / "Developer",
    ]
    blocked = [str(path) for path in probes if path.exists() and not os.access(path, os.R_OK)]
    if blocked:
        return "limited"
    return "not_proven" if any(not path.exists() for path in probes) else "likely"


def build_environment(home: Path, runner: ToolRunner) -> EnvironmentSnapshot:
    volumes = run_duf(runner)
    root_volume = source_volume(home, volumes) or next(
        (volume for volume in volumes if volume.mount_point == "/"),
        None,
    )
    if root_volume:
        free = root_volume.free_bytes
        total = root_volume.total_bytes
    else:
        usage = shutil.disk_usage(home if home.exists() else Path("/"))
        free = usage.free
        total = usage.total

    external = tuple(
        sorted(
            volume.mount_point
            for volume in volumes
            if volume.device_type in {"network", "fuse"} or volume.mount_point.startswith("/Volumes/")
        )
    )
    docker_installed = shutil.which("docker") is not None
    docker_reachable = False
    if docker_installed:
        result = runner.run(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=5)
        docker_reachable = result.returncode == 0

    warnings: list[str] = []
    if platform.system() != "Darwin":
        warnings.append("unsupported platform: this feature is macOS-only")

    return EnvironmentSnapshot(
        hostname=socket.gethostname(),
        platform=platform.system(),
        macos_version=platform.mac_ver()[0] or "unknown",
        home=str(home),
        disk_pressure=disk_pressure(free, total),
        free_bytes=free,
        total_bytes=total,
        full_disk_access=full_disk_access_confidence(home),
        docker_cli_installed=docker_installed,
        docker_daemon_reachable=docker_reachable,
        external_volumes=external,
        volumes=volumes,
        warnings=tuple(warnings),
    )
