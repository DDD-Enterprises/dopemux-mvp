#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
COMPOSE_FILE="${ROOT_DIR}/compose.yml"

die() {
  printf 'ensure-pal: %s\n' "$*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || die "docker is required but not found in PATH"
[[ -f "${COMPOSE_FILE}" ]] || die "missing compose file at ${COMPOSE_FILE}"

docker compose -f "${COMPOSE_FILE}" up -d pal pal-stdio
printf 'ensure-pal: PAL compose services requested\n' >&2
