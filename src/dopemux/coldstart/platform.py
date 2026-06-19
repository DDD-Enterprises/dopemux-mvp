"""Platform detection extracted from install.sh."""

from __future__ import annotations

import os
import platform as platform_module
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal


OsFamily = Literal["macos", "linux", "unknown"]


@dataclass(frozen=True)
class PlatformInfo:
    os_family: OsFamily
    arch: str
    python_path: str
    has_brew: bool
    has_apt: bool
    has_dnf: bool
    has_pacman: bool
    distro: str = "unknown"
    package_manager: str = "unknown"
    is_wsl2: bool = False


def _parse_os_release(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _is_wsl2(proc_version_path: Path) -> bool:
    if not proc_version_path.exists():
        return False
    text = proc_version_path.read_text(encoding="utf-8", errors="ignore")
    return "microsoft" in text.lower() or "wsl" in text.lower()


def detect_platform(
    *,
    ostype: str | None = None,
    os_release_path: Path = Path("/etc/os-release"),
    proc_version_path: Path = Path("/proc/version"),
    which: Callable[[str], str | None] = shutil.which,
    machine: Callable[[], str] = platform_module.machine,
    python_path: str = sys.executable,
) -> PlatformInfo:
    """Detect platform facts without mutating environment globals."""

    observed_ostype = ostype or os.environ.get("OSTYPE") or sys.platform
    arch = machine()

    has_brew = which("brew") is not None
    has_apt = which("apt") is not None
    has_dnf = which("dnf") is not None
    has_pacman = which("pacman") is not None

    if observed_ostype.startswith("darwin"):
        return PlatformInfo(
            os_family="macos",
            distro="macos",
            arch=arch,
            python_path=python_path,
            has_brew=has_brew,
            has_apt=has_apt,
            has_dnf=has_dnf,
            has_pacman=has_pacman,
            package_manager="brew",
        )

    if observed_ostype.startswith("linux"):
        is_wsl2 = _is_wsl2(proc_version_path)
        if is_wsl2:
            return PlatformInfo(
                os_family="linux",
                distro="wsl2",
                arch=arch,
                python_path=python_path,
                has_brew=has_brew,
                has_apt=has_apt,
                has_dnf=has_dnf,
                has_pacman=has_pacman,
                package_manager="unknown",
                is_wsl2=True,
            )

        distro = _parse_os_release(os_release_path).get("ID", "unknown")
        package_manager = "unknown"
        if distro in {"ubuntu", "debian"}:
            package_manager = "apt"
        elif distro in {"fedora", "rhel", "centos"}:
            package_manager = "dnf"
        elif distro in {"arch", "manjaro"}:
            package_manager = "pacman"

        return PlatformInfo(
            os_family="linux",
            distro=distro,
            arch=arch,
            python_path=python_path,
            has_brew=has_brew,
            has_apt=has_apt,
            has_dnf=has_dnf,
            has_pacman=has_pacman,
            package_manager=package_manager,
        )

    return PlatformInfo(
        os_family="unknown",
        arch=arch,
        python_path=python_path,
        has_brew=has_brew,
        has_apt=has_apt,
        has_dnf=has_dnf,
        has_pacman=has_pacman,
    )
