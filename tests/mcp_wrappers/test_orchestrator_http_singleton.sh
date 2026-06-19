#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
HTTP_SCRIPT="${ROOT}/scripts/mcp-wrappers/task-orchestrator-http-singleton.sh"
ROLLBACK_SCRIPT="${ROOT}/scripts/mcp-wrappers/task-orchestrator-rollback-stdio.sh"
MCP_JSON="${ROOT}/.mcp.json"

die() {
  printf 'test_orchestrator_http_singleton: %s\n' "$*" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  [[ "${haystack}" == *"${needle}"* ]] || die "expected output to contain: ${needle}"
}

if [[ "${1:-}" == "--dry-run" ]]; then
  http_output="$("${HTTP_SCRIPT}" --dry-run)"
  rollback_output="$("${ROLLBACK_SCRIPT}" --dry-run)"

  assert_contains "${http_output}" "container_name=task-orchestrator-"
  assert_contains "${http_output}" "data_dir="
  assert_contains "${http_output}" "url=http://127.0.0.1:7890/mcp"
  assert_contains "${http_output}" "MCP_TRANSPORT=http"
  assert_contains "${http_output}" "MCP_HTTP_PORT=7890"
  assert_contains "${http_output}" "MCP_HTTP_HOST=0.0.0.0"
  assert_contains "${http_output}" "127.0.0.1:7890:7890"
  assert_contains "${rollback_output}" "restore .mcp.json task-orchestrator entry to type=stdio"

  python - <<'PY' "${MCP_JSON}"
import json
import sys
from pathlib import Path

entry = json.loads(Path(sys.argv[1]).read_text())["mcpServers"]["task-orchestrator"]
assert entry["type"] == "http", entry
assert entry["url"] == "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp", entry
assert "command" not in entry, entry
assert "args" not in entry, entry
assert entry["env"]["TASK_ORCHESTRATOR_HTTP_PORT"] == "${TASK_ORCHESTRATOR_HTTP_PORT:-7890}", entry
PY
  exit 0
fi

command -v docker >/dev/null 2>&1 || {
  printf 'test_orchestrator_http_singleton: docker unavailable, skipping live test\n' >&2
  exit 0
}
command -v curl >/dev/null 2>&1 || {
  printf 'test_orchestrator_http_singleton: curl unavailable, skipping live endpoint probe\n' >&2
  exit 0
}

cleanup() {
  "${ROLLBACK_SCRIPT}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

"${HTTP_SCRIPT}"
"${HTTP_SCRIPT}"

container_name="$("${HTTP_SCRIPT}" --dry-run | awk -F= '$1 == "container_name" { print $2; exit }')"
count="$(docker ps --format '{{.Names}}' | awk -v n="${container_name}" '$0 == n { c++ } END { print c + 0 }')"
[[ "${count}" == "1" ]] || die "expected exactly one ${container_name}, got ${count}"

port="${TASK_ORCHESTRATOR_HTTP_PORT:-7890}"
for _ in $(seq 1 45); do
  if curl -fsS \
    -X POST "http://127.0.0.1:${port}/mcp" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-orchestrator-http-singleton","version":"1.0"}}}' |
    grep -q 'serverInfo'; then
    exit 0
  fi
  sleep 1
done

die "HTTP singleton did not become ready at http://127.0.0.1:${port}/mcp"
