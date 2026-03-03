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


def _write_identity_rails(repo_root: Path, *, project_id: str = "dopemux-mvp") -> None:
    (repo_root / ".dopetaskroot").write_text("", encoding="utf-8")
    (repo_root / ".repo_id").write_text(f"project={project_id}\n", encoding="utf-8")
    dopetask_dir = repo_root / ".dopetask"
    dopetask_dir.mkdir(parents=True, exist_ok=True)
    (dopetask_dir / "project.json").write_text(json.dumps({"project_id": project_id}), encoding="utf-8")


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


def test_wrapper_refuses_when_identity_is_invalid(tmp_path: Path) -> None:
    _write_wrapper(tmp_path)
    (tmp_path / ".dopetaskroot").write_text("", encoding="utf-8")

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 2
    assert ".repo_id missing" in result.stderr


def test_wrapper_executes_when_pin_and_venv_are_ready(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)
    
    # Create .dopetask-pin
    (tmp_path / ".dopetask-pin").write_text("install=pip\ndep=dopetask\nversion=0.2.0\n", encoding="utf-8")

    venv_bin = tmp_path / ".dopetask_venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".dopetask_venv" / ".dopetask_version").write_text("0.2.0\n", encoding="utf-8")
    (venv_bin / "activate").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    stub_dopetask = venv_bin / "dopetask"
    stub_dopetask.write_text("#!/usr/bin/env bash\necho STUB_DOPETASK_OK\n", encoding="utf-8")
    stub_dopetask.chmod(0o755)

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 0
    assert "STUB_DOPETASK_OK" in result.stdout


def test_wrapper_uses_installed_version_when_marker_is_stale(tmp_path: Path) -> None:
    _write_identity_rails(tmp_path)
    _write_wrapper(tmp_path)
    (tmp_path / ".dopetask-pin").write_text("install=pip\ndep=dopetask\nversion=0.2.0\n", encoding="utf-8")

    venv_bin = tmp_path / ".dopetask_venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".dopetask_venv" / ".dopetask_version").write_text("0.1.4\n", encoding="utf-8")
    (venv_bin / "activate").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    stub_python = venv_bin / "python"
    stub_python.write_text(
        "#!/usr/bin/env bash\n"
        "cat <<'EOF'\n"
        "0.2.0\n"
        "EOF\n",
        encoding="utf-8",
    )
    stub_python.chmod(0o755)
    stub_dopetask = venv_bin / "dopetask"
    stub_dopetask.write_text("#!/usr/bin/env bash\necho STUB_DOPETASK_OK\n", encoding="utf-8")
    stub_dopetask.chmod(0o755)

    result = _run_wrapper(tmp_path, "--version")
    assert result.returncode == 0
    assert "STUB_DOPETASK_OK" in result.stdout
    assert (tmp_path / ".dopetask_venv" / ".dopetask_version").read_text(encoding="utf-8").strip() == "0.2.0"
