"""Docker Compose orchestration extracted from install.sh."""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Callable, Mapping


Runner = Callable[..., subprocess.CompletedProcess[str]]


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
            result = self.runner([*args, "ps"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return False

            output = result.stdout
            services_lower = [service.lower() for service in services]
            lines = [line.lower() for line in output.splitlines() if line.strip()]
            service_lines = [
                line
                for line in lines
                if any(service in line for service in services_lower)
            ]
            all_services_present = all(
                any(service in line for line in service_lines)
                for service in services_lower
            )
            all_healthy = bool(service_lines) and all(
                "healthy" in line and "unhealthy" not in line
                for line in service_lines
            )
            running_without_healthchecks = (
                bool(service_lines)
                and all("healthy" not in line for line in service_lines)
                and all(("running" in line or "up" in line) for line in service_lines)
            )
            if all_services_present and (all_healthy or running_without_healthchecks):
                return True
            self.sleeper(interval_s)
        return False
