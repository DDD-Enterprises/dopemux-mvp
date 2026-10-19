"""Exact-container-match and HTTP-singleton safety tests for MCP wrappers.

Covers W4-F01 (find_container unanchored fallback), W3-F03 (stdio cleanup
removing the HTTP singleton named from DOPEMUX_PROJECT_ID) and W3-F05
(rollback `|| true` hiding a miss).  A fake ``docker`` on PATH logs argv and
answers from a canned container table; the real docker is never used.
"""

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPERS = REPO_ROOT / "scripts/mcp-wrappers"
CONPORT = WRAPPERS / "conport-wrapper.sh"
DOPE_CONTEXT = WRAPPERS / "dope-context-wrapper.sh"
STDIO = WRAPPERS / "task-orchestrator-current-stdio.sh"
ROLLBACK = WRAPPERS / "task-orchestrator-rollback-stdio.sh"

# Container table lines: name|host_ports|transport_label|data_mount_source
# (id == name).  Handles the docker calls the wrappers make.
_DOCKER = r"""#!/usr/bin/env bash
printf '%s\n' "docker $*" >> "${DOCKER_LOG:?}"
cmd="$1"; shift || true
table() { cat "${DOCKER_TABLE:?}" 2>/dev/null; }
case "$cmd" in
  ps)
    filt=""; quiet=0; fmt=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        -q|-aq|-qa) quiet=1 ;;
        --filter) shift; filt="${1#name=}"; filt="${filt#^}"; filt="${filt%\$}" ;;
        --format) shift; fmt="$1" ;;
      esac
      shift
    done
    [[ "$fmt" == table* ]] && echo NAMES
    table | while IFS='|' read -r name ports transport mount; do
      [[ -z "$name" ]] && continue
      if [[ -n "$filt" && "$name" != "$filt" ]]; then continue; fi
      echo "$name"
    done ;;
  inspect)
    fmt=""; cid=""
    while [[ $# -gt 0 ]]; do
      case "$1" in --format) shift; fmt="$1" ;; *) cid="$1" ;; esac
      shift
    done
    row="$(table | awk -F'|' -v n="$cid" '$1==n')"
    ports="$(printf '%s' "$row" | cut -d'|' -f2)"
    transport="$(printf '%s' "$row" | cut -d'|' -f3)"
    mount="$(printf '%s' "$row" | cut -d'|' -f4)"
    case "$fmt" in
      *Mounts*) printf '%s\n' "$mount" ;;
      *NetworkSettings.Ports*) [[ -n "$ports" ]] && printf '%s \n' "$ports" ;;
      *dopemux.transport*) printf '%s\n' "$transport" ;;
      *.Name*) printf '/%s\n' "$cid" ;;
    esac ;;
  *) : ;;
esac
exit 0
"""


def _setup(tmp_path: Path, rows):
    bin_dir = tmp_path / "stubbin"
    bin_dir.mkdir()
    for name, body in (("docker", _DOCKER), ("curl", "#!/usr/bin/env bash\nexit 1\n")):
        f = bin_dir / name
        f.write_text(body)
        f.chmod(0o755)
    table = tmp_path / "table.txt"
    table.write_text("".join(r + "\n" for r in rows))
    log = tmp_path / "docker.log"
    log.write_text("")
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DOPEMUX_", "TASK_ORCHESTRATOR_", "CODEX_", "CONPORT_"))
    }
    env.update(
        PATH=f"{bin_dir}:{env['PATH']}",
        DOCKER_TABLE=str(table),
        DOCKER_LOG=str(log),
        XDG_DATA_HOME=str(tmp_path / "xdg"),
        TASK_ORCHESTRATOR_PROJECT_ROOT=str(project),
        TASK_ORCHESTRATOR_WORKSPACE_ROOT=str(project),
    )
    return env, log, project


def _run(script, env, cwd, *args):
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _data_dir(env, tmp_path) -> str:
    out = _run(STDIO, env, tmp_path, "--print-resolution").stdout
    return next(
        ln.split("=", 1)[1] for ln in out.splitlines() if ln.startswith("data_dir=")
    )


def test_conport_wrapper_picks_exact_container_not_prefix_sibling(tmp_path):
    env, log, _ = _setup(tmp_path, ["X-conport-ab|||", "X-conport-a|||"])
    env["CONPORT_CONTAINER_NAME"] = "X-conport-a"
    result = _run(CONPORT, env, tmp_path)
    calls = log.read_text().splitlines()
    execs = [c for c in calls if c.startswith("docker exec")]
    assert result.returncode == 0, result.stderr
    assert len(execs) == 1
    assert " X-conport-a " in execs[0] + " "
    assert "X-conport-ab" not in execs[0]


def test_conport_wrapper_refuses_other_worktree_container(tmp_path):
    env, log, _ = _setup(tmp_path, ["mcp-conport_other-worktree|||"])
    result = _run(CONPORT, env, tmp_path)
    assert result.returncode != 0
    assert "mcp-conport" in result.stderr
    assert not any(c.startswith("docker exec") for c in log.read_text().splitlines())


def test_dope_context_wrapper_refuses_other_project_container(tmp_path):
    env, log, _ = _setup(tmp_path, ["other-dope-context-1|||", "mcp-dope-context2|||"])
    result = _run(DOPE_CONTEXT, env, tmp_path)
    assert result.returncode != 0
    assert "mcp-dope-context" in result.stderr
    assert not any(c.startswith("docker exec") for c in log.read_text().splitlines())


def test_stdio_does_not_remove_http_singleton_named_from_project_id(tmp_path):
    env, log, _ = _setup(tmp_path, [])
    env["DOPEMUX_PROJECT_ID"] = "proj-abc"
    data_dir = _data_dir(env, tmp_path)
    Path(env["DOCKER_TABLE"]).write_text(
        f"task-orchestrator-proj-abc|7890|http|{data_dir}\n"
    )
    result = _run(STDIO, env, tmp_path)
    calls = log.read_text().splitlines()
    assert result.returncode == 0, result.stderr
    assert not any(" rm " in f" {c} " for c in calls), calls
    assert not any(c.startswith("docker run") for c in calls), calls


def test_stdio_still_reaps_leaked_stdio_container_on_same_data_dir(tmp_path):
    env, log, _ = _setup(tmp_path, [])
    data_dir = _data_dir(env, tmp_path)
    Path(env["DOCKER_TABLE"]).write_text(f"leaked-stdio|||{data_dir}\n")
    _run(STDIO, env, tmp_path)
    calls = log.read_text().splitlines()
    assert any(c.startswith("docker rm -f") and "leaked-stdio" in c for c in calls)


def test_rollback_without_match_exits_nonzero(tmp_path):
    env, log, _ = _setup(tmp_path, ["unrelated|||"])
    env["DOPEMUX_PROJECT_ID"] = "proj-abc"
    result = _run(ROLLBACK, env, tmp_path)
    assert result.returncode != 0
    assert "task-orchestrator-proj-abc" in result.stderr
    assert not any(c.startswith("docker rm") for c in log.read_text().splitlines())


def test_rollback_removes_project_id_named_singleton(tmp_path):
    env, log, _ = _setup(tmp_path, ["task-orchestrator-proj-abc|7890|http|"])
    env["DOPEMUX_PROJECT_ID"] = "proj-abc"
    result = _run(ROLLBACK, env, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "docker rm -f task-orchestrator-proj-abc" in log.read_text().splitlines()
