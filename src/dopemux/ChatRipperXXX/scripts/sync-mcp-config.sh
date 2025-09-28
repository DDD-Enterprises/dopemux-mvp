#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root (works no matter where you run from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOADER="${ROOT_DIR}/tools/mcp/load-env.cjs"
TEMPLATE="${ROOT_DIR}/mcp.config.template.json"

if [[ ! -f "${LOADER}" ]]; then
  echo "Loader not found at: ${LOADER}" >&2
  exit 2
fi
if [[ ! -f "${TEMPLATE}" ]]; then
  echo "Template not found at: ${TEMPLATE}" >&2
  exit 2
fi

# Detect OS + default Claude Desktop config path
DEST=""
case "$(uname -s)" in
  Darwin) DEST="${HOME}/Library/Application Support/Claude/mcp.config.json" ;; # macOS
  Linux)  DEST="${HOME}/.config/Claude/mcp.config.json" ;;
  MINGW*|MSYS*|CYGWIN*) DEST="${APPDATA}/Claude/mcp.config.json" ;;
  *) echo "Unsupported OS: $(uname -s)"; exit 1 ;;
esac

# Ensure parent dir exists (handle spaces)
mkdir -p "$(dirname "${DEST}")"

# Expand template into Claude Desktop path
node "${LOADER}" "${TEMPLATE}" "${DEST}"
echo "Synced Claude Desktop config → ${DEST}"

# Optional: mirror to Claude Code project path if present
if [[ -d "${ROOT_DIR}/.claude" ]]; then
  node "${LOADER}" "${TEMPLATE}" "${ROOT_DIR}/.claude/mcp.config.json"
  echo "Synced Claude Code config → ${ROOT_DIR}/.claude/mcp.config.json"
fi

echo "Done."
