import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TO_LAUNCHER = REPO_ROOT / "scripts/mcp-wrappers/task-orchestrator-current-stdio.sh"

# Stub `docker` that lets us exercise the singleton-defer branch without a real
# daemon. STUB_SINGLETON=1 makes a name-filtered `docker ps -q` report a running
# container; `docker inspect` always reports a host-published port (7890); a
# `docker run` invocation records a marker so tests can assert kill-and-replace
# did NOT happen on the defer path.
_DOCKER_STUB = r"""#!/usr/bin/env bash
cmd="$1"; shift || true
has_arg() { local want="$1"; shift; for a in "$@"; do [[ "$a" == "$want" ]] && return 0; done; return 1; }
case "$cmd" in
  ps)
    if [[ "${STUB_SINGLETON:-0}" == "1" ]] && has_arg "-q" "$@" && printf '%s\n' "$@" | grep -q 'name='; then
      echo deadbeefcid
    fi
    ;;
  inspect) printf '7890 \n' ;;
  run) : > "${DOCKER_RUN_MARKER:?}" ;;
  *) : ;;
esac
exit 0
"""

# Stub `curl` so the best-effort health probe never reaches the real :7890.
_CURL_STUB = "#!/usr/bin/env bash\nexit 1\n"


def _make_stub_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "stubbin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(_DOCKER_STUB)
    docker.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text(_CURL_STUB)
    curl.chmod(0o755)
    return bin_dir


def _launcher_env(tmp_path: Path, *, singleton: bool, run_marker: Path) -> dict:
    bin_dir = _make_stub_bin(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "DOPEMUX_PROJECT_ROOT": str(REPO_ROOT),
            "DOPEMUX_WORKSPACE_ROOT": str(REPO_ROOT),
            "TASK_ORCHESTRATOR_PROJECT_ROOT": str(REPO_ROOT),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
            "STUB_SINGLETON": "1" if singleton else "0",
            "DOCKER_RUN_MARKER": str(run_marker),
        }
    )
    return env


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


def test_task_orchestrator_launcher_defers_to_running_http_singleton(tmp_path):
    """When a same-named container publishes a host port (the HTTP singleton),
    the stdio launcher must defer (exit 0) and never reach kill-and-replace."""
    run_marker = tmp_path / "docker_run_called"
    env = _launcher_env(tmp_path, singleton=True, run_marker=run_marker)

    result = subprocess.run(
        [str(TO_LAUNCHER)],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "deferring" in result.stderr
    assert "skipping stdio launch" in result.stderr
    # Defer path must NOT kill-and-replace or launch a stdio container.
    assert not run_marker.exists(), "launcher ran `docker run` instead of deferring"


def test_task_orchestrator_launcher_runs_when_no_singleton(tmp_path):
    """With no published-port singleton, the launcher falls through to a normal
    stdio launch (so Codex still gets tools when it is the only client)."""
    run_marker = tmp_path / "docker_run_called"
    env = _launcher_env(tmp_path, singleton=False, run_marker=run_marker)

    result = subprocess.run(
        [str(TO_LAUNCHER)],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "deferring" not in result.stderr
    # Fell through to launch (stub `docker run` records the marker).
    assert run_marker.exists(), "launcher did not fall through to `docker run`"
