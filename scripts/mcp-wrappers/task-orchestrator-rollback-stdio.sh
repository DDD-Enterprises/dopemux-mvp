#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  shift
fi

if [[ "$#" -gt 0 ]]; then
  printf 'task-orchestrator-rollback-stdio: unsupported argument: %s\n' "$1" >&2
  exit 1
fi

die() {
  printf 'task-orchestrator-rollback-stdio: %s\n' "$*" >&2
  exit 1
}

source "${SCRIPT_DIR}/_lib.sh"
# Same shared derivation as the stdio launcher and HTTP singleton.
resolve_task_orchestrator_identity || die "could not resolve task-orchestrator identity (no workspace/project root)"
data_dir="${TO_DATA_DIR}"
container_name="${TO_HTTP_CONTAINER_NAME}"

if [[ "${DRY_RUN}" == "true" ]]; then
  printf 'container_name=%s\n' "${container_name}"
  printf 'data_dir=%s\n' "${data_dir}"
  printf 'docker rm -f %q\n' "${container_name}"
  printf 'restore .mcp.json task-orchestrator entry to type=stdio command=scripts/mcp-wrappers/task-orchestrator-current-stdio.sh args=[]\n'
  exit 0
fi

command -v docker >/dev/null 2>&1 || die "docker is not available on PATH"
if [[ -z "$(docker ps -aq --filter "name=^${container_name}$" 2>/dev/null || true)" ]]; then
  die "no container named exactly '${container_name}' found; nothing stopped (set DOPEMUX_PROJECT_ID if the singleton was started with one)"
fi
docker rm -f "${container_name}" >/dev/null || die "docker rm -f ${container_name} failed"
cat >&2 <<'MSG'
task-orchestrator-rollback-stdio: HTTP singleton stopped.
Restore .mcp.json task-orchestrator to:
  type: stdio
  command: scripts/mcp-wrappers/task-orchestrator-current-stdio.sh
  args: []
Then reconnect the MCP client session.
MSG
