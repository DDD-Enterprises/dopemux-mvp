from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = REPO_ROOT / "install.sh"
SETUP_SH = REPO_ROOT / "scripts" / "setup.sh"


def _run_bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", script],
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
    )


def test_setup_skip_docker_delegates_without_enabling_installer_test_mode(
    tmp_path: Path,
) -> None:
    """Removing the real no-Docker flag must not turn setup into a CI dry-run."""
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy2(SETUP_SH, scripts_dir / "setup.sh")

    fake_installer = repo / "install.sh"
    fake_installer.write_text(
        "#!/bin/bash\n"
        "printf 'DOPEMUX_SKIP_DOCKER=%s\\n' \"${DOPEMUX_SKIP_DOCKER-unset}\"\n"
        "printf 'INSTALLER_TEST_MODE=%s\\n' \"${INSTALLER_TEST_MODE-unset}\"\n",
        encoding="utf-8",
    )
    fake_installer.chmod(0o755)

    result = subprocess.run(
        ["bash", str(scripts_dir / "setup.sh"), "--skip-docker"],
        text=True,
        capture_output=True,
        cwd=repo,
        env={**os.environ, "INSTALLER_TEST_MODE": "unset-by-test"},
    )

    assert result.returncode == 0, result.stderr
    assert "DOPEMUX_SKIP_DOCKER=1" in result.stdout
    assert "INSTALLER_TEST_MODE=unset-by-test" in result.stdout


def test_install_skip_docker_returns_before_docker_only_setup() -> None:
    """Moving the skip below env/network setup must make this test fail."""
    script = f"""
set -euo pipefail
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
DOPEMUX_SKIP_DOCKER=1
INSTALLER_TEST_MODE=0
check_system_resources() {{ printf 'UNEXPECTED_RESOURCE_CHECK\\n'; return 91; }}
ensure_env_file() {{ printf 'UNEXPECTED_ENV_SETUP\\n'; return 92; }}
ensure_docker_networks() {{ printf 'UNEXPECTED_NETWORK_SETUP\\n'; return 93; }}
install_docker_services core
"""

    result = _run_bash(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "UNEXPECTED_" not in result.stdout


def test_install_skip_docker_verifies_non_docker_installation(tmp_path: Path) -> None:
    """No-Docker verification must not execute Docker or count it as a check."""
    dopemux_home = tmp_path / ".dopemux"
    python_bin = dopemux_home / "venv" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    python_bin.chmod(0o755)
    (dopemux_home / "config" / "profiles").mkdir(parents=True)
    (dopemux_home / "config" / "profiles" / "adhd-default.yaml").write_text(
        "name: test\n",
        encoding="utf-8",
    )
    (tmp_path / ".zshrc").write_text(
        'export PATH="$HOME/.dopemux/venv/bin:$PATH"\n', encoding="utf-8"
    )

    script = f"""
set -euo pipefail
export HOME={shlex.quote(str(tmp_path))}
export DOPEMUX_HOME={shlex.quote(str(dopemux_home))}
export SHELL=/bin/zsh
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
DOPEMUX_SKIP_DOCKER=1
INSTALLER_TEST_MODE=0
docker() {{ printf 'UNEXPECTED_DOCKER\\n'; return 77; }}
verify_installation core
"""

    result = _run_bash(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "UNEXPECTED_DOCKER" not in result.stdout
    assert "All checks passed! (4/4)" in result.stdout
