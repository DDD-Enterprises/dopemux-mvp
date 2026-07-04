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
  docker start "${CONTAINER_NAME}" >/dev/null
  printf 'ensure-pal: started existing (stopped) %s (Codex consumer)\n' "${CONTAINER_NAME}" >&2
  exit 0
fi

if ! docker image inspect "${IMAGE_REF}" >/dev/null 2>&1; then
  die "image ${IMAGE_REF} not found locally. Build it first, e.g.: \
docker build -t ${IMAGE_REF} -f docker/mcp-servers/pal/Dockerfile ${ROOT_DIR}"
fi

env_file_args=()
if [[ -f "${ENV_FILE}" ]]; then
  env_file_args=(--env-file "${ENV_FILE}")
else
  printf 'ensure-pal: warning: no .env file at %s — starting %s without --env-file\n' \
    "${ENV_FILE}" "${CONTAINER_NAME}" >&2
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  "${env_file_args[@]}" \
  --entrypoint sleep \
  "${IMAGE_REF}" \
  infinity >/dev/null

printf 'ensure-pal: created %s from %s (Codex consumer)\n' "${CONTAINER_NAME}" "${IMAGE_REF}" >&2
