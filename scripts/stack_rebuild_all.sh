#!/usr/bin/env bash
set -euo pipefail

# Rebuild all Docker Compose stacks with latest base images
# Usage:
#   scripts/stack_rebuild_all.sh [--no-cache] [--pull-only|--build-only|--no-up] [--dry-run]
#
# Defaults: pull latest images, rebuild with --pull, and up -d --build for each stack.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

NO_CACHE=0
PULL_ONLY=0
BUILD_ONLY=0
NO_UP=0
DRY_RUN=0

usage() {
  cat <<EOF
Rebuild all Docker Compose stacks (project-wide) with latest base images.

Options:
  --no-cache      Build without cache
  --pull-only     Only pull remote images (no build, no up)
  --build-only    Pull + build, but do not run up
  --no-up         Skip 'up -d --build' (pull + build only)
  --dry-run       Print commands without executing
  -h, --help      Show this help

Examples:
  ${0}                 # pull, build --pull, up -d (all stacks)
  ${0} --no-cache      # force rebuild all with latest bases
  ${0} --build-only    # update images + rebuild, do not restart containers
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-cache) NO_CACHE=1; shift ;;
    --pull-only) PULL_ONLY=1; NO_UP=1; shift ;;
    --build-only) BUILD_ONLY=1; NO_UP=1; shift ;;
    --no-up) NO_UP=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

# Load project-wide env file if present to provide API keys, tokens, etc.
if [[ -f "$ROOT_DIR/.env" ]]; then
  echo "🔑 Loading environment from $ROOT_DIR/.env"
  set -a
  # shellcheck disable=SC1090
  source "$ROOT_DIR/.env"
  set +a
fi

# Compose wrapper (prefer plugin, fallback to docker-compose)
compose() {
  if docker compose version >/dev/null 2>&1; then
    if [[ $DRY_RUN -eq 1 ]]; then echo docker compose "$@"; else docker compose "$@"; fi
  else
    if [[ $DRY_RUN -eq 1 ]]; then echo docker-compose "$@"; else docker-compose "$@"; fi
  fi
}

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "$@"; else eval "$@"; fi
}

ensure_network() {
  local net="$1"
  if ! docker network inspect "$net" >/dev/null 2>&1; then
    echo "🌐 Creating network: $net"
    run "docker network create '$net' >/dev/null"
  else
    echo "✅ Network exists: $net"
  fi
}

# Ensure external networks used by stacks exist
# Note: do NOT pre-create leantime-net here; the Leantime compose defines
# and creates it itself. MCP Servers attach to it as an external network
# after Leantime brings it up.
ensure_network mcp-network
ensure_network dopemux-unified-network

# Build flags
BUILD_FLAGS=(--pull)
if [[ $NO_CACHE -eq 1 ]]; then BUILD_FLAGS+=(--no-cache); fi

process_compose_file() {
  local file="$1"; shift
  local name="$1"; shift

  if [[ ! -f "$file" ]]; then
    echo "• Skipping $name (not found): $file"
    return 0
  fi

  local dir base
  dir="$(cd "$(dirname "$file")" && pwd)"
  base="$(basename "$file")"

  echo "\n==> Refreshing: $name ($file)"
  pushd "$dir" >/dev/null

  # Compose file set: base + any docker-compose.override*.yml siblings
  local compose_args=(-f "$base")
  shopt -s nullglob
  local overrides=(docker-compose.override*.yml docker-compose.override*.yaml)
  # Avoid known conflicts in MCP Servers override volumes file
  if [[ "$file" != *"/docker/mcp-servers/docker-compose.yml"* ]]; then
    if (( ${#overrides[@]} )); then
      for ov in "${overrides[@]}"; do compose_args+=( -f "$ov" ); done
      echo "   Using overrides: ${overrides[*]}"
    fi
  else
    echo "   Skipping overrides for MCP Servers (volume conflicts)"
  fi
  shopt -u nullglob

  # Pull
  echo "   Pulling remote images..."
  compose "${compose_args[@]}" pull || true
  if [[ $PULL_ONLY -eq 1 ]]; then
    popd >/dev/null
    return 0
  fi

  # Build (update base images)
  echo "   Building images with flags: ${BUILD_FLAGS[*]}"
  compose "${compose_args[@]}" build "${BUILD_FLAGS[@]}"

  # Up (recreate as needed)
  if [[ $NO_UP -eq 0 ]]; then
    echo "   Recreating containers (up -d --build)"
    compose "${compose_args[@]}" up -d --build
  else
    echo "   Skipping 'up -d' (per flags)"
  fi

  popd >/dev/null
}

echo "== Dopemux: Pulling and rebuilding all stacks =="

# Priority-ordered stacks
process_compose_file "$ROOT_DIR/docker/docker-compose.event-bus.yml" "Event Bus (Redis + UI)"
process_compose_file "$ROOT_DIR/docker/memory-stack/docker-compose.yml" "Memory Stack"
process_compose_file "$ROOT_DIR/docker/leantime/docker-compose.yml" "Leantime"
process_compose_file "$ROOT_DIR/docker/conport-kg/docker-compose.yml" "ConPort KG"

# MCP Servers (orchestrated stack)
process_compose_file "$ROOT_DIR/docker/mcp-servers/docker-compose.yml" "MCP Servers"

# Additional stacks (discovered), excluding zen-mcp-server dev compose to avoid conflicts
mapfile -t discovered < <(cd "$ROOT_DIR" && rg --files --glob '*docker-compose*.yml' --glob '*docker-compose*.yaml' --glob '*compose*.yml' --glob '*compose*.yaml')

declare -A seen
for f in \
  "docker/docker-compose.event-bus.yml" \
  "docker/memory-stack/docker-compose.yml" \
  "docker/leantime/docker-compose.yml" \
  "docker/conport-kg/docker-compose.yml" \
  "docker/mcp-servers/docker-compose.yml"; do
  seen["$f"]=1
done

for f in "${discovered[@]}"; do
  # Normalize path relative to ROOT_DIR
  rel="${f#${ROOT_DIR}/}"
  # Skip already processed and Zen dev compose (covered by MCP Servers)
  if [[ -n "${seen[$rel]:-}" ]]; then continue; fi
  if [[ "$rel" == docker/mcp-servers/zen/zen-mcp-server/docker-compose.yml ]]; then continue; fi
  process_compose_file "$ROOT_DIR/$rel" "$rel"
done

echo "\n== Summary: docker ps =="
if [[ $DRY_RUN -eq 1 ]]; then
  echo "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
else
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | sed -n '1,200p'
fi

echo "\n✅ Rebuild complete."
