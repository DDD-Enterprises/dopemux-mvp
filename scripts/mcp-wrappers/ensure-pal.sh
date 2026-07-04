#!/usr/bin/env bash
# Ensures the off-compose `pal-mcp-server` container that Codex's
# ~/.codex/config.toml hard-depends on (required = true) is up.
#
# This container is SEPARATE from the compose-managed `pal` service that
# Claude Code talks to (http://localhost:3003/mcp) — that one is owned by
# `dopemux mcp ensure --full`'s compose-up step, not this script. Codex
# instead does `docker exec -i pal-mcp-server /opt/venv/bin/python server.py`
# against a standalone container (image pal-mcp-server:latest) that
# `compose.yml` has no service for, so `docker compose up` can never
# start/repair it — this script is the only thing that does.
#
# Idempotent: running while pal-mcp-server is already up is a no-op (exit 0).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
ENV_FILE="${ROOT_DIR}/.env"

CONTAINER_NAME="pal-mcp-server"
IMAGE_REF="pal-mcp-server:latest"
RECREATE=false

for arg in "$@"; do
  case "${arg}" in
    --recreate)
      RECREATE=true
      ;;
    *)
      printf 'ensure-pal: unsupported argument: %s\n' "${arg}" >&2
      exit 1
      ;;
  esac
done

die() {
  printf 'ensure-pal: %s\n' "$*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || die "docker is required but not found in PATH"
docker info >/dev/null 2>&1 || die "docker daemon is not reachable"

if [[ "${RECREATE}" == "true" ]]; then
  if docker ps -aq --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
    printf 'ensure-pal: --recreate requested, removing existing %s\n' "${CONTAINER_NAME}" >&2
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  fi
fi

running_id="$(docker ps -q --filter "name=^${CONTAINER_NAME}$" || true)"
if [[ -n "${running_id}" ]]; then
  printf 'ensure-pal: %s already running (Codex consumer)\n' "${CONTAINER_NAME}" >&2
  exit 0
fi

stopped_id="$(docker ps -aq --filter "name=^${CONTAINER_NAME}$" || true)"
if [[ -n "${stopped_id}" ]]; then
  # Try to start the existing container, then VERIFY it stayed up. A stale
  # container created before this script with the image's default stdio
  # command (`python server.py`) exits immediately on closed stdin when
  # started detached, so `docker start` returning 0 does NOT mean the Codex
  # consumer is actually running. Only report success if it is still running;
  # otherwise remove it and fall through to recreate with the sleep entrypoint.
  docker start "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  sleep 1
  if [[ -n "$(docker ps -q --filter "name=^${CONTAINER_NAME}$" || true)" ]]; then
    printf 'ensure-pal: started existing (stopped) %s (Codex consumer)\n' "${CONTAINER_NAME}" >&2
    exit 0
  fi
  printf 'ensure-pal: existing %s exited after start (stale command); recreating\n' "${CONTAINER_NAME}" >&2
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

if ! docker image inspect "${IMAGE_REF}" >/dev/null 2>&1; then
  die "image ${IMAGE_REF} not found locally. Build it from your standalone \
pal-mcp-server checkout, which produces the /opt/venv stdio image Codex execs \
into — from that checkout directory run: docker compose up -d --build. \
(The in-repo docker/mcp-servers/pal/Dockerfile builds a different /app/.venv \
HTTP-wrapper image for the compose 'pal' service and is NOT a substitute for \
this container.)"
fi

# Build the run args as an always-non-empty array and append --env-file only
# when .env exists. This avoids the empty-array expansion trap (which can emit
# a stray empty argument that docker misreads as the image name) entirely.
run_args=(-d --name "${CONTAINER_NAME}" --restart unless-stopped)
if [[ -f "${ENV_FILE}" ]]; then
  run_args+=(--env-file "${ENV_FILE}")
else
  printf 'ensure-pal: warning: no .env file at %s — starting %s without --env-file\n' \
    "${ENV_FILE}" "${CONTAINER_NAME}" >&2
fi
run_args+=(--entrypoint sleep "${IMAGE_REF}" infinity)

docker run "${run_args[@]}" >/dev/null

printf 'ensure-pal: created %s from %s (Codex consumer)\n' "${CONTAINER_NAME}" "${IMAGE_REF}" >&2
