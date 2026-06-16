"""Docker network helpers extracted from install.sh."""

from __future__ import annotations

import subprocess
from typing import Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]


def ensure_docker_networks(
    networks: list[str],
    *,
    runner: Runner = subprocess.run,
) -> None:
    """Create missing Docker networks using deterministic argument lists."""

    result = runner(
        ["docker", "network", "ls", "--format", "{{.Name}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "docker network ls failed")

    existing = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    for network in networks:
        if network in existing:
            continue
        created = runner(
            ["docker", "network", "create", network],
            capture_output=True,
            text=True,
            check=False,
        )
        if created.returncode != 0:
            raise RuntimeError(created.stderr.strip() or f"docker network create failed: {network}")
