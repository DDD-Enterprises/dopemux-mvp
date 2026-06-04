import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TO_LAUNCHER = REPO_ROOT / "scripts/mcp-wrappers/task-orchestrator-current-stdio.sh"


def test_task_orchestrator_launcher_is_tracked_executable():
    assert TO_LAUNCHER.exists()
    assert os.access(TO_LAUNCHER, os.X_OK)


def test_task_orchestrator_launcher_print_resolution_from_non_repo_cwd(tmp_path):
    env = os.environ.copy()
    env.update(
        {
            "DOPEMUX_PROJECT_ROOT": str(REPO_ROOT),
            "DOPEMUX_WORKSPACE_ROOT": str(REPO_ROOT),
            "TASK_ORCHESTRATOR_PROJECT_ROOT": str(REPO_ROOT),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
        }
    )

    result = subprocess.run(
        [str(TO_LAUNCHER), "--print-resolution"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert f"workspace_root={REPO_ROOT}" in result.stdout
    assert f"project_root={REPO_ROOT}" in result.stdout
    assert f"config_root={REPO_ROOT}" in result.stdout
    assert "database_path=" in result.stdout
