#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

workspace_id="$(detect_workspace)"
instance_id="$(detect_instance_id "$workspace_id")"

export DOPEMUX_WORKSPACE_ID="${workspace_id}"
export DOPEMUX_INSTANCE_ID="${instance_id}"

require_docker "conport-codex-wrapper"

if ! command -v timeout >/dev/null 2>&1; then
  echo "conport-codex-wrapper: timeout command is required but not found in PATH" >&2
  exit 1
fi

# Fail closed: only allow the Dopemux Dockerized Conport runtime.
if ! timeout 2 docker exec -i mcp-conport true >/dev/null 2>&1; then
  echo "conport-codex-wrapper: mcp-conport is unavailable; start your Dopemux Conport container" >&2
  exit 1
fi

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  -e DOPEMUX_INSTANCE_ID="${DOPEMUX_INSTANCE_ID}" \
  mcp-conport \
  uvx --from context-portal-mcp conport-mcp --mode stdio "$@"
