#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
STDIO_SCRIPT="${SCRIPT_DIR}/task-orchestrator-current-stdio.sh"
LOGBACK_CONFIG="${SCRIPT_DIR}/task-orchestrator-logback.xml"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  shift
elif [[ "${1:-}" == "--print-resolution" ]]; then
  exec "${STDIO_SCRIPT}" --print-resolution
fi

if [[ "$#" -gt 0 ]]; then
  printf 'task-orchestrator-http-singleton: unsupported argument: %s\n' "$1" >&2
  exit 1
fi

die() {
  printf 'task-orchestrator-http-singleton: %s\n' "$*" >&2
  exit 1
}

get_resolution_field() {
  local key="$1"
  printf '%s\n' "${resolution}" | awk -F= -v k="${key}" '$1 == k { sub(/^[^=]*=/, ""); print; exit }'
}

parse_image_ref() {
  awk -F'"' '/^IMAGE="/ { print $2; exit }' "${STDIO_SCRIPT}"
}

require_numeric_port() {
  local value="$1"
  if [[ ! "${value}" =~ ^[0-9]+$ ]] || [[ "${value}" -lt 1 ]] || [[ "${value}" -gt 65535 ]]; then
    die "TASK_ORCHESTRATOR_HTTP_PORT must be a TCP port number (1-65535), got '${value}'"
  fi
}

find_running_container_by_name() {
  local name="$1"
  docker ps -q --filter "name=^${name}$" 2>/dev/null || true
}

find_containers_by_data_dir() {
  local dir="$1"
  docker ps -aq 2>/dev/null | while read -r cid; do
    [[ -z "${cid}" ]] && continue
    mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/app/data"}}{{.Source}}{{end}}{{end}}' "${cid}" 2>/dev/null || true)"
    if [[ "${mount}" == "${dir}" ]]; then
      printf '%s\n' "${cid}"
    fi
  done
}

container_has_expected_port() {
  local cid="$1"
  local expected_port="$2"
  local binding
  binding="$(docker port "${cid}" "${expected_port}/tcp" 2>/dev/null || true)"
  printf '%s\n' "${binding}" | grep -qx "127.0.0.1:${expected_port}"
}

# A correctly-started singleton carries MCP_HTTP_PORT/MCP_HTTP_HOST (the env the
# jar actually reads). Pre-fix containers were started with MCP_PORT, which the
# jar ignores — so they publish the host port mapping but serve nothing on it.
# The port mapping alone (container_has_expected_port) cannot tell them apart, so
# a stale MCP_PORT container would otherwise be accepted as "already running" and
# never recreated, leaving the endpoint dead. Require the HTTP env to match.
container_has_http_env() {
  local cid="$1"
  local expected_port="$2"
  local env_lines
  env_lines="$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${cid}" 2>/dev/null || true)"
  grep -qx "MCP_HTTP_PORT=${expected_port}" <<<"${env_lines}" &&
    grep -q '^MCP_HTTP_HOST=' <<<"${env_lines}"
}

[[ -x "${STDIO_SCRIPT}" ]] || die "missing executable stdio wrapper at ${STDIO_SCRIPT}"
[[ -f "${LOGBACK_CONFIG}" ]] || die "missing logback config at ${LOGBACK_CONFIG}"

resolution="$("${STDIO_SCRIPT}" --print-resolution)"
workspace_root="$(get_resolution_field workspace_root)"
project_root="$(get_resolution_field project_root)"
workspace_id="$(get_resolution_field state_id)"
data_dir="$(get_resolution_field data_dir)"
database_path="$(get_resolution_field database_path)"
config_root="$(get_resolution_field config_root)"
image="$(parse_image_ref)"
port="${TASK_ORCHESTRATOR_HTTP_PORT:-7890}"

[[ -n "${workspace_root}" ]] || die "could not derive workspace_root"
[[ -n "${project_root}" ]] || die "could not derive project_root"
[[ -n "${workspace_id}" ]] || die "could not derive state_id"
[[ -n "${data_dir}" ]] || die "could not derive data_dir"
[[ -n "${database_path}" ]] || die "could not derive database_path"
[[ -n "${config_root}" ]] || die "could not derive config_root"
[[ -n "${image}" ]] || die "could not parse IMAGE from ${STDIO_SCRIPT}"
require_numeric_port "${port}"

container_name="task-orchestrator-${workspace_id}"

docker_args=(
  run
  -d
  --restart unless-stopped
  --name "${container_name}"
  --user "$(id -u):$(id -g)"
  -p "127.0.0.1:${port}:${port}"
  -v "${data_dir}:/app/data"
  -v "${LOGBACK_CONFIG}:/tmp/logback.xml:ro"
  -e "DATABASE_PATH=/app/data/current-tasks.db"
  -e "MCP_TRANSPORT=http"
  -e "MCP_HTTP_PORT=${port}"
  -e "MCP_HTTP_HOST=0.0.0.0"
  -e "USE_FLYWAY=true"
  -e "AGENT_CONFIG_DIR=/project"
)

if [[ -f "${config_root}/.taskorchestrator/config.yaml" ]]; then
  docker_args+=(
    -v "${config_root}/.taskorchestrator:/project/.taskorchestrator:ro"
  )
fi

java_args=(
  java
  -Dfile.encoding=UTF-8
  -Djava.awt.headless=true
  --enable-native-access=ALL-UNNAMED
  -Dlogback.configurationFile=/tmp/logback.xml
  -jar orchestrator.jar
)

if [[ "${DRY_RUN}" == "true" ]]; then
  printf 'workspace_root=%s\n' "${workspace_root}"
  printf 'project_root=%s\n' "${project_root}"
  printf 'state_id=%s\n' "${workspace_id}"
  printf 'data_dir=%s\n' "${data_dir}"
  printf 'database_path=%s\n' "${database_path}"
  printf 'config_root=%s\n' "${config_root}"
  printf 'container_name=%s\n' "${container_name}"
  printf 'image=%s\n' "${image}"
  printf 'url=http://127.0.0.1:%s/mcp\n' "${port}"
  printf 'docker '
  printf '%q ' "${docker_args[@]}" "${image}" "${java_args[@]}"
  printf '\n'
  exit 0
fi

command -v docker >/dev/null 2>&1 || die "docker is not available on PATH"
mkdir -p "${data_dir}"

running_by_name="$(find_running_container_by_name "${container_name}")"
if [[ -n "${running_by_name}" ]]; then
  running_image="$(docker inspect --format '{{.Config.Image}}' "${running_by_name}" 2>/dev/null || true)"
  if [[ "${running_image}" == "${image}" ]] &&
    container_has_expected_port "${running_by_name}" "${port}" &&
    container_has_http_env "${running_by_name}" "${port}"; then
    printf 'task-orchestrator-http-singleton: already running %s at http://127.0.0.1:%s/mcp\n' "${container_name}" "${port}" >&2
    exit 0
  fi
fi

stale_by_name="$(docker ps -aq --filter "name=^${container_name}$" 2>/dev/null || true)"
stale_by_mount="$(find_containers_by_data_dir "${data_dir}")"
stale_combined="$(printf '%s\n%s\n' "${stale_by_name}" "${stale_by_mount}" | awk 'NF' | sort -u)"

if [[ -n "${stale_combined}" ]]; then
  printf 'task-orchestrator-http-singleton: removing %d stale container(s) for %s\n' \
    "$(printf '%s\n' "${stale_combined}" | wc -l | tr -d ' ')" "${data_dir}" >&2
  printf '%s\n' "${stale_combined}" | xargs docker rm -f >/dev/null 2>&1 || true
fi

docker "${docker_args[@]}" "${image}" "${java_args[@]}" >/dev/null
printf 'task-orchestrator-http-singleton: started %s at http://127.0.0.1:%s/mcp\n' "${container_name}" "${port}" >&2
