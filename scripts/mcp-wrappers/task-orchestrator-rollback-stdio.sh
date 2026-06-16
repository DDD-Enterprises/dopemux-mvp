#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
STDIO_SCRIPT="${SCRIPT_DIR}/task-orchestrator-current-stdio.sh"
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

get_resolution_field() {
  local key="$1"
  printf '%s\n' "${resolution}" | awk -F= -v k="${key}" '$1 == k { sub(/^[^=]*=/, ""); print; exit }'
}

[[ -x "${STDIO_SCRIPT}" ]] || die "missing executable stdio wrapper at ${STDIO_SCRIPT}"
resolution="$("${STDIO_SCRIPT}" --print-resolution)"
workspace_id="$(get_resolution_field state_id)"
data_dir="$(get_resolution_field data_dir)"
[[ -n "${workspace_id}" ]] || die "could not derive state_id"
[[ -n "${data_dir}" ]] || die "could not derive data_dir"

container_name="task-orchestrator-${workspace_id}"

if [[ "${DRY_RUN}" == "true" ]]; then
  printf 'container_name=%s\n' "${container_name}"
  printf 'data_dir=%s\n' "${data_dir}"
  printf 'docker rm -f %q\n' "${container_name}"
  printf 'restore .mcp.json task-orchestrator entry to type=stdio command=scripts/mcp-wrappers/task-orchestrator-current-stdio.sh args=[]\n'
  exit 0
fi

command -v docker >/dev/null 2>&1 || die "docker is not available on PATH"
docker rm -f "${container_name}" >/dev/null 2>&1 || true
cat >&2 <<'MSG'
task-orchestrator-rollback-stdio: HTTP singleton stopped.
Restore .mcp.json task-orchestrator to:
  type: stdio
  command: scripts/mcp-wrappers/task-orchestrator-current-stdio.sh
  args: []
Then reconnect the MCP client session.
MSG
