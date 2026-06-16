import sys
from pathlib import Path

from dopemux.coldstart.platform import PlatformInfo, detect_platform


def test_detect_platform_uses_explicit_ostype_and_tool_probe(tmp_path: Path) -> None:
    os_release = tmp_path / "os-release"
    os_release.write_text('ID=ubuntu\nPRETTY_NAME="Ubuntu"\n', encoding="utf-8")

    def fake_which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "apt" else None

    info = detect_platform(
        ostype="linux-gnu",
        os_release_path=os_release,
        which=fake_which,
        machine=lambda: "x86_64",
        python_path=sys.executable,
    )

    assert info == PlatformInfo(
        os_family="linux",
        arch="x86_64",
        python_path=sys.executable,
        has_brew=False,
        has_apt=True,
        has_dnf=False,
        has_pacman=False,
        distro="ubuntu",
        package_manager="apt",
        is_wsl2=False,
    )


def test_detect_platform_reports_macos_without_linux_release() -> None:
    info = detect_platform(
        ostype="darwin23",
        which=lambda name: "/opt/homebrew/bin/brew" if name == "brew" else None,
        machine=lambda: "arm64",
        python_path="/usr/bin/python3",
    )

    assert info.os_family == "macos"
    assert info.distro == "macos"
    assert info.package_manager == "brew"
    assert info.has_brew is True
    assert info.arch == "arm64"
