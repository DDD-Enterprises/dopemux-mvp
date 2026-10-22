#!/usr/bin/env bash
set -euo pipefail

IMAGE="ghcr.io/jpicklyk/task-orchestrator@sha256:e47ed00aae313a85de0e6340010bfec8bdcd5f8c253d002759a4bb1ef8c122c1"  # v3.8.0 — upgraded 2026-05-27 to activate .taskorchestrator/config.yaml schema support
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
LOGBACK_CONFIG="${SCRIPT_DIR}/task-orchestrator-logback.xml"
PRINT_RESOLUTION=false

if [[ "${1:-}" == "--print-resolution" ]]; then
  PRINT_RESOLUTION=true
  shift
fi

if [[ "$#" -gt 0 ]]; then
  printf 'task-orchestrator-current-stdio: unsupported argument: %s\n' "$1" >&2
  exit 1
fi

die() {
  printf 'task-orchestrator-current-stdio: %s\n' "$*" >&2
  exit 1
}

source "${SCRIPT_DIR}/_lib.sh"

# Shared derivation (see _lib.sh resolve_task_orchestrator_identity).
if resolve_task_orchestrator_identity; then
  :
else
  rc=$?
  if [[ "${rc}" -eq 2 ]]; then
    printf 'task-orchestrator-current-stdio: no workspace detected (CWD not in a git repo and no *_WORKSPACE_ROOT/*_PROJECT_ROOT env set); skipping orchestrator for this session\n' >&2
    exit 0
  fi
  die "could not resolve task-orchestrator identity"
fi
workspace_root="${TO_WORKSPACE_ROOT}"
project_root="${TO_PROJECT_ROOT}"
workspace_id="${TO_STATE_ID}"
data_dir="${TO_DATA_DIR}"
config_root="${TO_CONFIG_ROOT}"
[[ -f "${LOGBACK_CONFIG}" ]] || die "missing logback config at ${LOGBACK_CONFIG}"

if [[ "${PRINT_RESOLUTION}" == "true" ]]; then
  printf 'workspace_root=%s\n' "${workspace_root}"
  printf 'project_root=%s\n' "${project_root}"
  printf 'state_id=%s\n' "${workspace_id}"
  printf 'data_dir=%s\n' "${data_dir}"
  printf 'database_path=%s\n' "${data_dir}/current-tasks.db"
  printf 'config_root=%s\n' "${config_root}"
  exit 0
fi

command -v docker >/dev/null 2>&1 || die "docker is not available on PATH"
mkdir -p "${data_dir}"

# ─── Singleton enforcement (kill-and-replace) ──────────────────────────
# Prevents multi-spawn — without this, every wrapper invocation spawned
# a new docker container against the same SQLite DB, leading to concurrent
# JVM writers contending on WAL locks. Containers also leaked when Claude
# Code crashed without cleanly closing the MCP stdio pipe.
#
# Strategy: assign a deterministic container name per workspace and remove
# any existing container with that name OR mounting the same data_dir
# before starting a fresh one. One container per project at any time.
#
# Tradeoff: opening a second Claude session in the same project disconnects
# the first session's MCP. For typical single-operator-per-project use
# this matches expectations.
container_name="${TO_STDIO_CONTAINER_NAME}"
http_container_name="${TO_HTTP_CONTAINER_NAME}"

# ─── Defer to a running HTTP singleton ─────────────────────────────────
# Claude (and any HTTP client) runs this workspace's orchestrator as a
# long-lived HTTP singleton container that PUBLISHES a host TCP port
# (task-orchestrator-http-singleton.sh, default :7890). It shares this
# launcher's data_dir, and is named from DOPEMUX_PROJECT_ID when that is set
# (TO_HTTP_CONTAINER_NAME), otherwise it shares this launcher's name. Our
# kill-and-replace below would tear it down and disconnect the other client.
#
# A stdio container never publishes a host port, so a *running* container with
# the singleton's exact name AND a host-published port binding is
# unambiguously the HTTP singleton. In that case defer: emit a note and exit 0
# without touching it. Leaked stdio containers publish no host port, so they
# are NOT matched here and are still reaped below.
for candidate_name in "${http_container_name}" "${container_name}"; do
  singleton_cid="$(docker ps -q --filter "name=^${candidate_name}$" 2>/dev/null | awk 'NF{print;exit}' || true)"
  [[ -n "${singleton_cid}" ]] || continue
  singleton_port="$(docker inspect \
    --format '{{range $p,$conf := .NetworkSettings.Ports}}{{if $conf}}{{(index $conf 0).HostPort}} {{end}}{{end}}' \
    "${singleton_cid}" 2>/dev/null | awk '{print $1; exit}' || true)"
  if [[ -n "${singleton_port}" ]]; then
    health="unverified"
    if command -v curl >/dev/null 2>&1; then
      if curl -fsS -m 3 \
        -X POST "http://127.0.0.1:${singleton_port}/mcp" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"stdio-defer-probe","version":"1.0"}}}' 2>/dev/null \
        | grep -q 'serverInfo'; then
        health="healthy"
      fi
    fi
    printf 'task-orchestrator-current-stdio: HTTP singleton already running for %s at http://127.0.0.1:%s/mcp (%s); deferring — skipping stdio launch\n' \
      "${candidate_name}" "${singleton_port}" "${health}" >&2
    exit 0
  fi
done

# True when container $1 is (or may be) the HTTP singleton: exact singleton
# name, dopemux.transport=http label, or any host-published port. Such a
# container is never ours to remove.
is_http_singleton() {
  local cid="$1" cname transport ports
  cname="$(docker inspect --format '{{.Name}}' "${cid}" 2>/dev/null | sed 's#^/##' || true)"
  [[ "${cname}" == "${http_container_name}" ]] && return 0
  transport="$(docker inspect --format '{{index .Config.Labels "dopemux.transport"}}' "${cid}" 2>/dev/null || true)"
  [[ "${transport}" == "http" ]] && return 0
  ports="$(docker inspect \
    --format '{{range $p,$conf := .NetworkSettings.Ports}}{{if $conf}}{{(index $conf 0).HostPort}} {{end}}{{end}}' \
    "${cid}" 2>/dev/null | awk '{print $1; exit}' || true)"
  [[ -n "${ports}" ]] && return 0
  return 1
}

# Our own containers: exact stdio name, plus leaked containers holding the same
# data_dir mount. Mount-matched containers are skipped if they are the singleton.
stale_by_name="$(docker ps -aq --filter "name=^${container_name}$" 2>/dev/null || true)"
stale_by_name="$(printf '%s\n' "${stale_by_name}" | while read -r cid; do
  [[ -z "${cid}" ]] && continue
  is_http_singleton "${cid}" && continue
  printf '%s\n' "${cid}"
done)"

stale_by_mount="$(docker ps -q 2>/dev/null | while read -r cid; do
  [[ -z "${cid}" ]] && continue
  mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/app/data"}}{{.Source}}{{end}}{{end}}' "${cid}" 2>/dev/null)"
  if [[ "${mount}" == "${data_dir}" ]]; then
    is_http_singleton "${cid}" && continue
    printf '%s\n' "${cid}"
  fi
done)"

stale_combined="$(printf '%s\n%s\n' "${stale_by_name}" "${stale_by_mount}" | awk 'NF' | sort -u)"

if [[ -n "${stale_combined}" ]]; then
  printf 'task-orchestrator-current-stdio: removing %d stale container(s) for %s\n' \
    "$(echo "${stale_combined}" | wc -l | tr -d ' ')" "${data_dir}" >&2
  # shellcheck disable=SC2086
  echo "${stale_combined}" | xargs docker rm -f >/dev/null 2>&1 || true
fi

docker_args=(
  run
  --rm
  -i
  --name "${container_name}"
  --user "$(id -u):$(id -g)"
  -v "${data_dir}:/app/data"
  -v "${LOGBACK_CONFIG}:/tmp/logback.xml:ro"
  -e "DATABASE_PATH=/app/data/current-tasks.db"
  -e "MCP_TRANSPORT=stdio"
  -e "USE_FLYWAY=true"
  -e "AGENT_CONFIG_DIR=/project"
)

if [[ -f "${config_root}/.taskorchestrator/config.yaml" ]]; then
  docker_args+=(
    -v "${config_root}/.taskorchestrator:/project/.taskorchestrator:ro"
  )
fi

exec docker "${docker_args[@]}" "${IMAGE}" \
  java \
  -Dfile.encoding=UTF-8 \
  -Djava.awt.headless=true \
  --enable-native-access=ALL-UNNAMED \
  -Dlogback.configurationFile=/tmp/logback.xml \
  -jar orchestrator.jar
