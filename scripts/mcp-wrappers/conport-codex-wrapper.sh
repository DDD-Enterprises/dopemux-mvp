#!/usr/bin/env bash
set -euo pipefail

detect_workspace() {
  if [[ -n "${DOPEMUX_WORKSPACE_ID:-}" ]]; then
    printf '%s\n' "${DOPEMUX_WORKSPACE_ID}"
    return
  fi

  if command -v git >/dev/null 2>&1; then
    local git_root
    git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "${git_root}" ]]; then
      printf '%s\n' "${git_root}"
      return
    fi
  fi

  pwd
}

workspace_id="$(detect_workspace)"
instance_id="${DOPEMUX_INSTANCE_ID:-$(basename "${workspace_id}")}"

export DOPEMUX_WORKSPACE_ID="${workspace_id}"
export DOPEMUX_INSTANCE_ID="${instance_id}"

# Fail closed: only allow the Dopemux Dockerized Conport runtime.
if ! command -v docker >/dev/null 2>&1; then
  echo "conport-codex-wrapper: docker is required but not found in PATH" >&2
  exit 1
fi

if ! command -v timeout >/dev/null 2>&1; then
  echo "conport-codex-wrapper: timeout command is required but not found in PATH" >&2
  exit 1
fi

if ! timeout 2 docker exec -i mcp-conport true >/dev/null 2>&1; then
  echo "conport-codex-wrapper: mcp-conport is unavailable; start your Dopemux Conport container" >&2
  exit 1
fi

exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID="${DOPEMUX_WORKSPACE_ID}" \
  -e DOPEMUX_INSTANCE_ID="${DOPEMUX_INSTANCE_ID}" \
  mcp-conport \
  uvx --from context-portal-mcp conport-mcp --mode stdio "$@"
