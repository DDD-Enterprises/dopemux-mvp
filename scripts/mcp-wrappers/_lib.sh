#!/usr/bin/env bash
# Shared helpers for MCP wrapper scripts.
# Source this file from each wrapper:
#   source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
#
# Provides:
#   detect_workspace       — Resolve the active workspace path (env > git > cwd)
#   detect_instance_id     — Stable short ID for the workspace (env > basename)
#   find_container <name>  — Locate a running Docker container by EXACT name (no fallback)
#   require_docker         — Fail with a clear error if `docker` is not on PATH

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

detect_instance_id() {
  local workspace_id="${1:-${DOPEMUX_WORKSPACE_ID:-$(detect_workspace)}}"
  printf '%s\n' "${DOPEMUX_INSTANCE_ID:-$(basename "${workspace_id}")}"
}

# find_container <exact-name>
# Prints <exact-name> and returns 0 only when a running container has exactly
# that name. Never falls back to a substring/prefix match: a different
# worktree's or project's container (e.g. "<name>_other", "<name>-2") must never
# be selected. On a miss, prints the expected name to stderr and returns 1.
find_container() {
  local expected="$1"
  local found line
  found=""
  while IFS= read -r line; do
    if [[ "${line}" == "${expected}" ]]; then
      found="${line}"
      break
    fi
  done < <(docker ps --filter "name=^${expected}\$" --format '{{.Names}}' 2>/dev/null || true)

  if [[ -n "${found}" ]]; then
    printf '%s\n' "${found}"
    return 0
  fi
  echo "find_container: no running container named exactly '${expected}'" >&2
  return 1
}

require_docker() {
  local script_label="${1:-mcp-wrapper}"
  if ! command -v docker >/dev/null 2>&1; then
    echo "❌ ${script_label}: docker is required but not found in PATH" >&2
    exit 1
  fi
}

# ─── Task-orchestrator identity (shared by stdio, HTTP singleton, rollback) ───
_to_require_dir() {
  # Print the physical (symlink-resolved) path of an existing directory.
  local candidate="$1"
  if [[ -n "${candidate}" && -d "${candidate}" ]]; then
    (cd "${candidate}" >/dev/null 2>&1 && pwd -P)
    return
  fi
  return 1
}

_to_git_project_root() {
  local candidate="$1" common_dir
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

# resolve_task_orchestrator_identity
# Single source of truth for the task-orchestrator project root and container
# names. Sets (globals): TO_WORKSPACE_ROOT TO_PROJECT_ROOT TO_STATE_ID
# TO_PROJECT_ID TO_DATA_DIR TO_CONFIG_ROOT TO_STDIO_CONTAINER_NAME
# TO_HTTP_ID TO_HTTP_CONTAINER_NAME.
#
# Env precedence (first existing directory wins; every root is realpath'd):
#   workspace root: TASK_ORCHESTRATOR_WORKSPACE_ROOT, DOPEMUX_WORKTREE_ROOT,
#                   DOPEMUX_WORKSPACE_ROOT, CODEX_WORKSPACE_ROOT,
#                   CODEX_PROJECT_ROOT, git toplevel of $PWD, then project env.
#   project root:   TASK_ORCHESTRATOR_PROJECT_ROOT, DOPEMUX_PROJECT_ROOT,
#                   git common dir of the workspace root.
# The stdio launcher's order is used for project root because the data_dir hash
# (and therefore the DB the singleton mounts) already derives from it; the old
# singleton order (DOPEMUX_* first) could label a root different from the one
# whose hash named the data dir. A project-root env var that is set but is not
# an existing directory is an error (fail closed), not a silent fallthrough.
#
# Container names: stdio  = task-orchestrator-<TO_STATE_ID> (hash of root);
#                  HTTP   = task-orchestrator-<DOPEMUX_PROJECT_ID or TO_STATE_ID>.
# Returns 0 ok, 2 no workspace detected (silent; caller decides), 1 error (message on stderr).
resolve_task_orchestrator_identity() {
  local var_name var_value resolved git_root
  TO_WORKSPACE_ROOT=""
  TO_PROJECT_ROOT=""

  for var_name in TASK_ORCHESTRATOR_WORKSPACE_ROOT DOPEMUX_WORKTREE_ROOT DOPEMUX_WORKSPACE_ROOT CODEX_WORKSPACE_ROOT CODEX_PROJECT_ROOT; do
    var_value="${!var_name:-}"
    if resolved="$(_to_require_dir "${var_value}")"; then
      TO_WORKSPACE_ROOT="${resolved}"
      break
    fi
  done

  if [[ -z "${TO_WORKSPACE_ROOT}" ]]; then
    if git_root="$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null)" && [[ -n "${git_root}" ]]; then
      TO_WORKSPACE_ROOT="$(cd "${git_root}" && pwd -P)"
    fi
  fi

  if [[ -z "${TO_WORKSPACE_ROOT}" ]]; then
    for var_name in TASK_ORCHESTRATOR_PROJECT_ROOT DOPEMUX_PROJECT_ROOT; do
      var_value="${!var_name:-}"
      if resolved="$(_to_require_dir "${var_value}")"; then
        TO_WORKSPACE_ROOT="${resolved}"
        break
      fi
    done
  fi

  if [[ -z "${TO_WORKSPACE_ROOT}" ]]; then
    return 2
  fi

  for var_name in TASK_ORCHESTRATOR_PROJECT_ROOT DOPEMUX_PROJECT_ROOT; do
    var_value="${!var_name:-}"
    [[ -n "${var_value}" ]] || continue
    if resolved="$(_to_require_dir "${var_value}")"; then
      TO_PROJECT_ROOT="${resolved}"
      break
    fi
    printf '%s=%s is not an existing directory\n' "${var_name}" "${var_value}" >&2
    return 1
  done
  if [[ -z "${TO_PROJECT_ROOT}" ]]; then
    TO_PROJECT_ROOT="$(_to_git_project_root "${TO_WORKSPACE_ROOT}")" || TO_PROJECT_ROOT=""
  fi
  if [[ -z "${TO_PROJECT_ROOT}" || ! -d "${TO_PROJECT_ROOT}" ]]; then
    printf 'could not derive project root from TASK_ORCHESTRATOR_PROJECT_ROOT, DOPEMUX_PROJECT_ROOT, or git common dir\n' >&2
    return 1
  fi

  local hash name
  if command -v shasum >/dev/null 2>&1; then
    hash="$(printf '%s' "${TO_PROJECT_ROOT}" | shasum -a 256 | awk '{print substr($1, 1, 16)}')"
  elif command -v sha256sum >/dev/null 2>&1; then
    hash="$(printf '%s' "${TO_PROJECT_ROOT}" | sha256sum | awk '{print substr($1, 1, 16)}')"
  else
    hash="$(python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest()[:16])' <<<"${TO_PROJECT_ROOT}")"
  fi
  name="$(basename "${TO_PROJECT_ROOT}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')"
  [[ -n "${name}" ]] || name="workspace"
  TO_STATE_ID="${name}-${hash}"
  TO_PROJECT_ID="${DOPEMUX_PROJECT_ID:-$(basename "${TO_PROJECT_ROOT}")}"
  TO_DATA_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/dopemux-mission-control/task-orchestrator/${TO_STATE_ID}"

  TO_CONFIG_ROOT="${TO_WORKSPACE_ROOT}"
  if [[ ! -f "${TO_CONFIG_ROOT}/.taskorchestrator/config.yaml" && -f "${TO_PROJECT_ROOT}/.taskorchestrator/config.yaml" ]]; then
    TO_CONFIG_ROOT="${TO_PROJECT_ROOT}"
  fi

  TO_STDIO_CONTAINER_NAME="task-orchestrator-${TO_STATE_ID}"
  TO_HTTP_ID="${DOPEMUX_PROJECT_ID:-${TO_STATE_ID}}"
  TO_HTTP_CONTAINER_NAME="task-orchestrator-${TO_HTTP_ID}"
  return 0
}
