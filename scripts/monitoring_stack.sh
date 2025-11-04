#!/usr/bin/env bash
#
# Convenience wrapper for the Component 6 monitoring stack (Prometheus + Grafana).
# Usage:
#   ./scripts/monitoring_stack.sh start|stop|status|logs
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_DIR="$(cd "${SCRIPT_DIR}/../services/task-orchestrator/observability" && pwd)"
COMPOSE_FILE="${STACK_DIR}/docker-compose-monitoring.yml"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "🚫 Compose file not found at ${COMPOSE_FILE}" >&2
  exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker-compose)
elif docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker compose)
else
  echo "🚫 Neither 'docker-compose' nor 'docker compose' is available on PATH." >&2
  exit 1
fi

run_compose() {
  "${DOCKER_COMPOSE[@]}" -f "${COMPOSE_FILE}" "$@"
}

ensure_docker_running() {
  if ! docker info >/dev/null 2>&1; then
    echo "🚫 Docker daemon is not running. Start Docker Desktop or dockerd and retry." >&2
    exit 1
  fi
}

ACTION="${1:-}"

case "${ACTION}" in
  start)
    ensure_docker_running
    echo "🚀 Starting monitoring stack (Prometheus + Grafana + Pushgateway)"
    run_compose up -d
    echo "✅ Stack launch command dispatched. First run may take a minute while images download."
    ;;
  stop)
    ensure_docker_running
    echo "🛑 Stopping monitoring stack"
    run_compose down
    ;;
  status)
    ensure_docker_running
    run_compose ps
    ;;
  logs)
    ensure_docker_running
    run_compose logs -f
    ;;
  *)
    echo "Usage: $0 {start|stop|status|logs}" >&2
    exit 1
    ;;
esac
