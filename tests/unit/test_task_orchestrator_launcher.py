from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = (
    REPO_ROOT
    / "plugins"
    / "dopemux-mission-control"
    / "scripts"
    / "task-orchestrator-current-stdio.sh"
)


def _write_codex_session(codex_home: Path, cwd: Path) -> None:
    session_id = "019e7b8e-4411-7d40-bddc-a4f21ae1a2bf"
    session_index = codex_home / "session_index.jsonl"
    session_index.parent.mkdir(parents=True)
    session_index.write_text(
        json.dumps(
            {
                "id": session_id,
                "thread_name": "Launcher fallback regression",
                "updated_at": "2026-05-31T01:03:27.345398Z",
            }
        )
        + "\n"
    )

    session_file = (
        codex_home
        / "sessions"
        / "2026"
        / "05"
        / "30"
        / "rollout-2026-05-30T18-03-01-019e7b8e-4411-7d40-bddc-a4f21ae1a2bf.jsonl"
    )
    session_file.parent.mkdir(parents=True)
    session_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-05-31T01:03:20.034Z",
                "type": "session_meta",
                "payload": {
                    "id": session_id,
                    "cwd": str(cwd),
                    "originator": "Codex Desktop",
                },
            }
        )
        + "\n"
    )


def test_launcher_print_resolution_uses_codex_session_cwd_without_env_or_git_cwd(
    tmp_path: Path,
) -> None:
    assert LAUNCHER.is_file()

    codex_home = tmp_path / ".codex"
    workspace = tmp_path / "workspace"
    nongit_cwd = tmp_path / "nongit"
    workspace.mkdir()
    nongit_cwd.mkdir()
    _write_codex_session(codex_home, workspace)

    env = {
        "HOME": str(tmp_path),
        "PATH": os.environ["PATH"],
    }
    result = subprocess.run(
        [str(LAUNCHER), "--print-resolution"],
        cwd=nongit_cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert f"workspace_root={workspace}" in result.stdout
    assert f"project_root={workspace}" in result.stdout
    assert "database_path=" in result.stdout


def test_launcher_print_resolution_does_not_require_home(
    tmp_path: Path,
) -> None:
    assert LAUNCHER.is_file()

    codex_home = tmp_path / ".codex"
    workspace = tmp_path / "workspace"
    nongit_cwd = tmp_path / "nongit"
    data_home = tmp_path / "data"
    workspace.mkdir()
    nongit_cwd.mkdir()
    _write_codex_session(codex_home, workspace)

    env = {
        "CODEX_HOME": str(codex_home),
        "XDG_DATA_HOME": str(data_home),
        "PATH": os.environ["PATH"],
    }
    result = subprocess.run(
        [str(LAUNCHER), "--print-resolution"],
        cwd=nongit_cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert f"workspace_root={workspace}" in result.stdout
    assert f"project_root={workspace}" in result.stdout
    assert f"data_dir={data_home}/dopemux-mission-control/task-orchestrator/" in result.stdout
