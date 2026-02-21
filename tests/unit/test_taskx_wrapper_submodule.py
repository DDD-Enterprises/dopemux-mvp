from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER_SOURCE = REPO_ROOT / "scripts" / "taskx"


def _write_wrapper(repo_root: Path) -> Path:
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = scripts_dir / "taskx"
    wrapper_path.write_text(WRAPPER_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    wrapper_path.chmod(0o755)
    return wrapper_path


def _write_identity_rails(repo_root: Path, *, project_id: str = "dopemux-mvp") -> None:
    (repo_root / ".taskxroot").write_text("", encoding="utf-8")
    (repo_root / ".repo_id").write_text(f"project={project_id}\n", encoding="utf-8")
    taskx_dir = repo_root / ".taskx"
    taskx_dir.mkdir(parents=True, exist_ok=True)
    (taskx_dir / "project.json").write_text(json.dumps({"project_id": project_id}), encoding="utf-8")


def _run_wrapper(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    wrapper = repo_root / "scripts" / "taskx"
    return subprocess.run(
        [str(wrapper), *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_wrapper_refuses_when_submodule_missing(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 2
    assert "TaskX submodule missing" in result.stderr


def test_wrapper_refuses_when_identity_is_invalid(tmp_path: Path) -> None:
    _write_wrapper(tmp_path)
    (tmp_path / ".taskxroot").write_text("", encoding="utf-8")

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 2
    assert ".repo_id missing" in result.stderr


def test_wrapper_executes_when_submodule_and_venv_are_ready(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)

    vendor_taskx = tmp_path / "vendor" / "taskx"
    vendor_taskx.mkdir(parents=True, exist_ok=True)
    (vendor_taskx / "pyproject.toml").write_text("[project]\nname='taskx-kernel'\nversion='0.0.0'\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=vendor_taskx, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=vendor_taskx, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=vendor_taskx, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=vendor_taskx, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=vendor_taskx, check=True, capture_output=True, text=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=vendor_taskx,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    venv_bin = tmp_path / ".taskx_venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".taskx_venv" / ".taskx_submodule_commit").write_text(f"{commit}\n", encoding="utf-8")
    (venv_bin / "activate").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    stub_taskx = venv_bin / "taskx"
    stub_taskx.write_text("#!/usr/bin/env bash\necho STUB_TASKX_OK\n", encoding="utf-8")
    stub_taskx.chmod(0o755)

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 0
    assert "STUB_TASKX_OK" in result.stdout
