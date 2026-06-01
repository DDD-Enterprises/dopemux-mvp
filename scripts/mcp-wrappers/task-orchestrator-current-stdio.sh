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

require_dir() {
  local candidate="$1"
  if [[ -n "${candidate}" && -d "${candidate}" ]]; then
    cd "${candidate}" >/dev/null 2>&1 && pwd -P
    return 0
  fi
  return 1
}

git_worktree_root() {
  local candidate="$1"
  git -C "${candidate}" rev-parse --show-toplevel 2>/dev/null
}

git_project_root() {
  local candidate="$1"
  local common_dir
  common_dir="$(git -C "${candidate}" rev-parse --git-common-dir 2>/dev/null)" || return 1
  if [[ "${common_dir}" != /* ]]; then
    common_dir="$(cd "${candidate}/${common_dir}" >/dev/null 2>&1 && pwd -P)" || return 1
  else
    common_dir="$(cd "${common_dir}" >/dev/null 2>&1 && pwd -P)" || return 1
  fi

  if [[ "$(basename "${common_dir}")" == ".git" ]]; then
    dirname "${common_dir}"
  else
    printf '%s\n' "${common_dir}"
  fi
}

workspace_root=""
for var_name in TASK_ORCHESTRATOR_WORKSPACE_ROOT DOPEMUX_WORKSPACE_ROOT CODEX_WORKSPACE_ROOT CODEX_PROJECT_ROOT; do
  var_value="${!var_name:-}"
  if resolved="$(require_dir "${var_value}")"; then
    workspace_root="${resolved}"
    break
  fi
done

if [[ -z "${workspace_root}" ]]; then
  if git_root="$(git_worktree_root "${PWD}")"; then
    workspace_root="$(cd "${git_root}" && pwd -P)"
  fi
fi

if [[ -z "${workspace_root}" ]]; then
  for var_name in TASK_ORCHESTRATOR_PROJECT_ROOT DOPEMUX_PROJECT_ROOT; do
    var_value="${!var_name:-}"
    if resolved="$(require_dir "${var_value}")"; then
      workspace_root="${resolved}"
      break
    fi
  done
fi

[[ -n "${workspace_root}" ]] || die "could not derive workspace root from env or current git root"
[[ -f "${LOGBACK_CONFIG}" ]] || die "missing logback config at ${LOGBACK_CONFIG}"

project_root=""
if resolved="$(require_dir "${TASK_ORCHESTRATOR_PROJECT_ROOT:-}")"; then
  project_root="${resolved}"
elif resolved="$(require_dir "${DOPEMUX_PROJECT_ROOT:-}")"; then
  project_root="${resolved}"
elif git_project="$(git_project_root "${workspace_root}")"; then
  project_root="${git_project}"
fi

[[ -n "${project_root}" ]] || die "could not derive project root from TASK_ORCHESTRATOR_PROJECT_ROOT, DOPEMUX_PROJECT_ROOT, or git common dir"

hash_input="${project_root}"
if command -v shasum >/dev/null 2>&1; then
  workspace_hash="$(printf '%s' "${hash_input}" | shasum -a 256 | awk '{print substr($1, 1, 16)}')"
elif command -v sha256sum >/dev/null 2>&1; then
  workspace_hash="$(printf '%s' "${hash_input}" | sha256sum | awk '{print substr($1, 1, 16)}')"
else
  workspace_hash="$(python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest()[:16])' <<<"${hash_input}")"
fi

workspace_name="$(basename "${project_root}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')"
[[ -n "${workspace_name}" ]] || workspace_name="workspace"
workspace_id="${workspace_name}-${workspace_hash}"

data_root="${XDG_DATA_HOME:-${HOME}/.local/share}/dopemux-mission-control/task-orchestrator"
data_dir="${data_root}/${workspace_id}"

config_root="${workspace_root}"
if [[ ! -f "${config_root}/.taskorchestrator/config.yaml" && -f "${project_root}/.taskorchestrator/config.yaml" ]]; then
  config_root="${project_root}"
fi

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
container_name="task-orchestrator-${workspace_id}"

stale_by_name="$(docker ps -aq --filter "name=^${container_name}$" 2>/dev/null || true)"

stale_by_mount="$(docker ps -q 2>/dev/null | while read -r cid; do
  [[ -z "${cid}" ]] && continue
  mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/app/data"}}{{.Source}}{{end}}{{end}}' "${cid}" 2>/dev/null)"
  if [[ "${mount}" == "${data_dir}" ]]; then
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
