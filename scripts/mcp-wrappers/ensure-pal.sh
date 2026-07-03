#!/usr/bin/env bash
set -euo pipefail

# ensure-pal.sh — Idempotent ensure/recover for the off-compose PAL MCP container.
#
# PAL (multi-model reasoning MCP, `mcp__pal__*` / `pal/*`) runs as a
# persistent, off-compose container named `pal-mcp-server`, shared by
# Claude Code (~/.claude.json → mcpServers.pal) and Codex
# (~/.codex/config.toml → [mcp_servers.pal], required=true — Codex HARD-FAILS
# at session start if this container is missing). Both clients talk to it via
# `docker exec -i pal-mcp-server /opt/venv/bin/python server.py`; this script
# only ensures the container exists and is running — it does not speak MCP.
#
# There is no restart/ensure script for this container upstream: it vanishes
# on `docker system prune` or a Docker Desktop restart. See:
#   docs/ops/pal-mcp-codex-claude-stdio.md (canonical runbook)
#
# Usage:
#   scripts/mcp-wrappers/ensure-pal.sh              # ensure running (idempotent, quiet fast path)
#   scripts/mcp-wrappers/ensure-pal.sh --recreate    # kill + recreate even if already running
#
# Exit codes:
#   0  container is running (already was, or was started/created)
#   1  docker daemon unreachable, image missing, or other precondition failure

CONTAINER_NAME="pal-mcp-server"
IMAGE_REF="pal-mcp-server:latest"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
ENV_FILE="${REPO_ROOT}/.env"

# shellcheck source=./_lib.sh
source "${SCRIPT_DIR}/_lib.sh"

RECREATE=false
case "${1:-}" in
  --recreate)
    RECREATE=true
    shift
    ;;
  "") ;;
  *)
    printf 'ensure-pal: unsupported argument: %s\n' "${1:-}" >&2
    exit 1
    ;;
esac

if [[ "$#" -gt 0 ]]; then
  printf 'ensure-pal: unsupported argument: %s\n' "$1" >&2
  exit 1
fi

require_docker "ensure-pal"

if ! docker info >/dev/null 2>&1; then
  echo "❌ ensure-pal: Docker daemon is not reachable (is Docker Desktop running?)" >&2
  exit 1
fi

running_id="$(docker ps -q --filter "name=^${CONTAINER_NAME}$" 2>/dev/null || true)"
existing_id="$(docker ps -aq --filter "name=^${CONTAINER_NAME}$" 2>/dev/null || true)"

if [[ "${RECREATE}" == "true" && -n "${existing_id}" ]]; then
  echo "🔄 ensure-pal: --recreate requested, removing existing container '${CONTAINER_NAME}'" >&2
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  running_id=""
  existing_id=""
fi

if [[ -n "${running_id}" ]]; then
  # Fast path: already up, nothing to do.
  exit 0
fi

if [[ -n "${existing_id}" ]]; then
  echo "▶️  ensure-pal: starting stopped container '${CONTAINER_NAME}'" >&2
  docker start "${CONTAINER_NAME}" >/dev/null
  exit 0
fi

# No container by this name at all — need to create it. Requires the image.
if ! docker image inspect "${IMAGE_REF}" >/dev/null 2>&1; then
  echo "❌ ensure-pal: image '${IMAGE_REF}' not found locally" >&2
  echo "💡 Build it via the PAL checkout's compose file (produces ${IMAGE_REF} with /opt/venv/bin/python, matching what clients exec):" >&2
  echo "   cd ~/code/pal-mcp-server && docker compose up -d --build" >&2
  echo "   Note: docker/mcp-servers-source/pal/Dockerfile in this repo builds a different, non-exec-compatible layout (/app/.venv) — not a substitute." >&2
  exit 1
fi

env_file_args=()
if [[ -f "${ENV_FILE}" ]]; then
  env_file_args=(--env-file "${ENV_FILE}")
else
  echo "⚠️  ensure-pal: no .env at ${ENV_FILE} — starting '${CONTAINER_NAME}' without --env-file (PAL tool calls needing API keys will fail until keys are supplied)" >&2
fi

echo "🚀 ensure-pal: creating container '${CONTAINER_NAME}' from ${IMAGE_REF}" >&2
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  "${env_file_args[@]+"${env_file_args[@]}"}" \
  --entrypoint sleep \
  "${IMAGE_REF}" \
  infinity >/dev/null

echo "✅ ensure-pal: '${CONTAINER_NAME}' is running" >&2
