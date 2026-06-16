"""Docker Compose orchestration extracted from install.sh."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Callable, Mapping


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _compose_ps_records(output: str) -> list[tuple[str, str, str]]:
    records = _compose_json_records(output)
    if records:
        return records
    return _compose_table_records(output)


def _compose_json_records(output: str) -> list[tuple[str, str, str]]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return []

    items = data if isinstance(data, list) else [data]
    records: list[tuple[str, str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        service = str(item.get("Service") or item.get("Name") or "").strip().lower()
        state = str(item.get("State") or item.get("Status") or "").strip().lower()
        health = str(item.get("Health") or "").strip().lower()
        if service:
            records.append((service, state, health))
    return records


def _compose_table_records(output: str) -> list[tuple[str, str, str]]:
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return []

    header = next((line for line in lines if "SERVICE" in line and "STATUS" in line), "")
    headers = [column.lower() for column in re.split(r"\s{2,}", header.strip())]
    if "service" not in headers or "status" not in headers:
        return []
    service_index = headers.index("service")
    status_index = headers.index("status")

    records: list[tuple[str, str, str]] = []
    for line in lines:
        if line == header:
            continue
        columns = re.split(r"\s{2,}", line.strip())
        if len(columns) <= max(service_index, status_index):
            continue
        service = columns[service_index].strip().lower()
        status = columns[status_index].strip().lower()
        if service:
            records.append((service, status, ""))
    return records


def _compose_service_ready(state: str, health: str) -> bool:
    if health:
        return health == "healthy"
    if "unhealthy" in state or "health:" in state or "starting" in state:
        return False
    if "healthy" in state:
        return True
    return "running" in state or "up" in state


class ComposeOrchestrator:
    def __init__(
        self,
        *,
        runner: Runner = subprocess.run,
        env_file: Path | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        monotonic_values: Iterator[float] | None = None,
    ) -> None:
        self.runner = runner
        self.env_file = env_file
        self.sleeper = sleeper
        self._clock = clock
        self._monotonic_values = monotonic_values

    def _now(self) -> float:
        if self._monotonic_values is not None:
            return next(self._monotonic_values)
        return self._clock()

    def _compose_base(self, compose_file: Path, profile: str | None = None) -> list[str]:
        args = ["docker", "compose"]
        if self.env_file and self.env_file.exists():
            args.extend(["--env-file", str(self.env_file)])
        if profile:
            args.extend(["--profile", profile])
        args.extend(["-f", str(compose_file)])
        return args

    def _run(self, args: list[str], *, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        result = self.runner(args, capture_output=True, text=True, check=False, env=merged_env)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"command failed: {' '.join(args)}")
        return result

    def pull_images(self, compose_file: Path, profile: str | None = None) -> None:
        self._run([*self._compose_base(compose_file, profile), "pull"])

    def bring_up(
        self,
        compose_file: Path,
        profile: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._run([*self._compose_base(compose_file, profile), "up", "-d"], env=env)

    def bring_down(self, compose_file: Path) -> None:
        self._run([*self._compose_base(compose_file), "down"])

    def wait_healthy(
        self,
        services: list[str],
        timeout_s: int = 120,
        interval_s: int = 5,
        compose_file: Path | None = None,
        profile: str | None = None,
    ) -> bool:
        if not services:
            return True

        start = self._now()
        while self._now() - start < timeout_s:
            args = self._compose_base(compose_file or Path("compose.yml"), profile)
            result = self.runner([*args, "ps", "--format", "json"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return False

            services_lower = {service.lower() for service in services}
            service_records = [
                record
                for record in _compose_ps_records(result.stdout)
                if record[0] in services_lower
            ]
            all_services_present = all(
                any(record[0] == service for record in service_records)
                for service in services_lower
            )
            all_ready = bool(service_records) and all(
                _compose_service_ready(state, health)
                for _, state, health in service_records
            )
            if all_services_present and all_ready:
                return True
            self.sleeper(interval_s)
        return False
