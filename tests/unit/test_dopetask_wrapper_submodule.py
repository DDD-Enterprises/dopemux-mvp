from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER_SOURCE = REPO_ROOT / "scripts" / "dopetask"


def _write_wrapper(repo_root: Path) -> Path:
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = scripts_dir / "dopetask"
    wrapper_path.write_text(WRAPPER_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    wrapper_path.chmod(0o755)
    return wrapper_path


def _write_identity_rails(repo_root: Path) -> None:
    (repo_root / ".dopetaskroot").write_text("", encoding="utf-8")


def _run_wrapper(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    wrapper = repo_root / "scripts" / "dopetask"
    return subprocess.run(
        [str(wrapper), *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_wrapper_refuses_when_pin_missing(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 2
    assert ".dopetask-pin missing" in result.stderr


def test_wrapper_refuses_when_root_marker_missing(tmp_path: Path) -> None:
    _write_wrapper(tmp_path)
    (tmp_path / ".dopetask-pin").write_text("install=pip\ndep=dopetask\nversion=0.5.1\n", encoding="utf-8")

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 2
    assert ".dopetaskroot missing" in result.stderr


def test_wrapper_refuses_invalid_install_method(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)
    (tmp_path / ".dopetask-pin").write_text("install=magic\ndep=dopetask\nversion=0.5.1\n", encoding="utf-8")

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 2
    assert "Invalid install method" in result.stderr


def test_wrapper_executes_when_pin_and_venv_are_ready(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)
    
    # Create .dopetask-pin
    (tmp_path / ".dopetask-pin").write_text("install=pip\ndep=dopetask\nversion=0.5.1\n", encoding="utf-8")

    venv_bin = tmp_path / ".dopetask_venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".dopetask_venv" / ".dopetask_version").write_text("0.5.1\n", encoding="utf-8")
    (venv_bin / "activate").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    stub_dopetask = venv_bin / "dopetask"
    stub_dopetask.write_text("#!/usr/bin/env bash\necho STUB_DOPETASK_OK\n", encoding="utf-8")
    stub_dopetask.chmod(0o755)

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 0
    assert "STUB_DOPETASK_OK" in result.stdout


def test_wrapper_triggers_install_on_version_drift(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)
    (tmp_path / ".dopetask-pin").write_text("install=pip\ndep=dopetask\nversion=0.5.1\n", encoding="utf-8")

    venv_bin = tmp_path / ".dopetask_venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".dopetask_venv" / ".dopetask_version").write_text("0.2.0\n", encoding="utf-8")
    (venv_bin / "activate").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    
    # The wrapper will try to run pip install. We'll stub 'pip' to just update the version file.
    stub_pip = venv_bin / "pip"
    stub_pip.write_text(f"#!/usr/bin/env bash\necho '0.5.1' > {tmp_path}/.dopetask_venv/.dopetask_version\n", encoding="utf-8")
    stub_pip.chmod(0o755)
    
    stub_dopetask = venv_bin / "dopetask"
    stub_dopetask.write_text("#!/usr/bin/env bash\necho STUB_DOPETASK_OK\n", encoding="utf-8")
    stub_dopetask.chmod(0o755)

    result = _run_wrapper(tmp_path, "--version")
    assert "Installing dopetask==0.5.1" in result.stdout
    assert result.returncode == 0
    assert (tmp_path / ".dopetask_venv" / ".dopetask_version").read_text(encoding="utf-8").strip() == "0.5.1"
