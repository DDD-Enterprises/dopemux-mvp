"""Reuse/idempotence tests for the task-orchestrator HTTP singleton launcher.

Regression guard for PR #935 review (codex P2 "Recreate pre-fix singleton
containers"): a running same-image container that publishes the host port but
was started with the OLD ``MCP_PORT`` env (which the jar ignores) must NOT be
accepted as "already running" — it serves nothing on the published port. The
launcher must treat such env-missing containers as stale and recreate them.
"""

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HTTP_LAUNCHER = REPO_ROOT / "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh"
STDIO_LAUNCHER = REPO_ROOT / "scripts/mcp-wrappers/task-orchestrator-current-stdio.sh"


def _image_ref() -> str:
    for line in STDIO_LAUNCHER.read_text().splitlines():
        m = re.match(r'^IMAGE="([^"]+)"', line)
        if m:
            return m.group(1)
    raise AssertionError("could not parse IMAGE= from stdio launcher")


# Stub `docker` covering the calls the reuse path makes:
#   ps -q                           -> running container id (refuse_foreign_port_owner)
#   ps -q --filter name=^X$         -> running container id
#   inspect --format '{{.Config.Image}}' -> the expected image (match)
#   inspect --format '{{.Name}}'    -> container name matching expected singleton
#   inspect Labels dopemux.project_root -> project_root label for ownership check
#   port <cid> 7890/tcp             -> 127.0.0.1:7890 (port published)
#   inspect --format '{{range .Config.Env}}...' -> env, with/without MCP_HTTP_PORT
#   run ...                         -> record a marker (proves recreate happened)
# Everything else (stale removal, etc.) is a harmless no-op.
_DOCKER_STUB = r"""#!/usr/bin/env bash
cmd="$1"; shift || true
case "$cmd" in
  ps) echo runningcid ;;
  port) printf '127.0.0.1:%s\n' "7890" ;;
  inspect)
    fmt="$(printf '%s ' "$@")"
    if printf '%s' "$fmt" | grep -q 'Config.Image'; then
      printf '%s\n' "${EXPECTED_IMAGE}"
    elif printf '%s' "$fmt" | grep -q 'Config.Env'; then
      printf 'MCP_TRANSPORT=http\n'
      if [[ "${STUB_ENV_OK:-0}" == "1" ]]; then
        printf 'MCP_HTTP_PORT=7890\nMCP_HTTP_HOST=0.0.0.0\n'
      else
        printf 'MCP_PORT=7890\n'
      fi
    elif printf '%s' "$fmt" | grep -q 'dopemux.project_root'; then
      # Labeled same-project owner so refuse_foreign_port_owner does not block reuse
      printf '%s\n' "${DOPEMUX_PROJECT_ROOT:-}"
    elif printf '%s' "$fmt" | grep -q '\.Name'; then
      # Match container_name derived by launcher (task-orchestrator-<state_id>)
      # state_id comes from stdio --print-resolution; tests set PROJECT_ROOT so
      # any name that is NOT treated as foreign unlabeled is fine. Use empty
      # when project_root label is set; launcher only dies on unlabeled foreign.
      printf '/task-orchestrator-stub\n'
    fi ;;
  run) : > "${DOCKER_RUN_MARKER:?}" ;;
  *) : ;;
esac
exit 0
"""


def _run(tmp_path: Path, *, env_ok: bool):
    bin_dir = tmp_path / "stubbin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(_DOCKER_STUB)
    docker.chmod(0o755)
    run_marker = tmp_path / "docker_run_called"
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "DOPEMUX_PROJECT_ROOT": str(REPO_ROOT),
            "DOPEMUX_WORKSPACE_ROOT": str(REPO_ROOT),
            "TASK_ORCHESTRATOR_PROJECT_ROOT": str(REPO_ROOT),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
            "EXPECTED_IMAGE": _image_ref(),
            "STUB_ENV_OK": "1" if env_ok else "0",
            "DOCKER_RUN_MARKER": str(run_marker),
        }
    )
    result = subprocess.run(
        [str(HTTP_LAUNCHER)],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    return result, run_marker


def test_reuses_running_singleton_with_http_env(tmp_path):
    """Healthy singleton (MCP_HTTP_PORT/HOST set) is reused, not recreated."""
    result, run_marker = _run(tmp_path, env_ok=True)
    assert result.returncode == 0, result.stderr
    assert "already running" in result.stderr
    assert (
        not run_marker.exists()
    ), "recreated a healthy singleton instead of reusing it"


def test_recreates_running_singleton_missing_http_env(tmp_path):
    """Pre-fix container (MCP_PORT only, no MCP_HTTP_PORT) is treated as stale
    and recreated rather than accepted as already running."""
    result, run_marker = _run(tmp_path, env_ok=False)
    assert result.returncode == 0, result.stderr
    assert "already running" not in result.stderr
    assert run_marker.exists(), "did not recreate a stale pre-fix singleton"
