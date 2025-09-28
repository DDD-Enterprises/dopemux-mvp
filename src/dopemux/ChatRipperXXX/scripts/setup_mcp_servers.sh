#!/usr/bin/env bash
set -euo pipefail

# --- Config: set required tokens/paths in your shell or a local .env you source BEFORE running this script ---
: "${EXA_API_KEY:?set EXA_API_KEY}"
: "${DDG_REGION:=ca-en}"
: "${GITHUB_TOKEN:?set GITHUB_TOKEN}"
: "${NOTION_API_KEY:?set NOTION_API_KEY}"
: "${NOTION_BASE_ID:?set NOTION_BASE_ID}"
: "${CHROMA_URL:=http://localhost:8000}"
# Choose which vector memory backend to use for semantic recall. Valid values are "lance" (local LanceDB), "chroma" or "pgvector".
# When set to "lance" (the default) this script will not install any additional vector memory server because Claude Context uses
# LanceDB for local vector storage by default.
: "${VECTOR_STORE:=lance}"

# Path to store the LanceDB vector database when using the local backend. If unset, the default path is "$HOME/.claude-context/lancedb".
# Only relevant when VECTOR_STORE="lance".
: "${LANCEDB_PATH:=$HOME/.claude-context/lancedb}"
: "${CONTEXT7_API_KEY:?set CONTEXT7_API_KEY}"

add_server() {
  local name="$1"
  local json="$2"
  echo ">>> adding MCP server: ${name}"
  claude mcp add-json "${name}" "${json}" >/dev/null
  claude mcp get "${name}" | sed -n '1,120p' || true
  echo
}

add_server filesystem '{
  "type":"stdio",
  "command":"mcp-filesystem",
  "args":["--root","."],
  "env":{}
}'

add_server github "{
  \"type\":\"stdio\",
  \"command\":\"mcp-github\",
  \"env\":{\"GITHUB_TOKEN\":\"${GITHUB_TOKEN}\"}
}"

add_server notion "{
  \"type\":\"stdio\",
  \"command\":\"mcp-notion\",
  \"env\":{\"NOTION_API_KEY\":\"${NOTION_API_KEY}\",\"NOTION_BASE_ID\":\"${NOTION_BASE_ID}\"}
}"

add_server exa "{
  \"type\":\"stdio\",
  \"command\":\"mcp-exa\",
  \"env\":{\"EXA_API_KEY\":\"${EXA_API_KEY}\"}
}"

add_server duckduckgo "{
  \"type\":\"stdio\",
  \"command\":\"mcp-duckduckgo\",
  \"env\":{\"DDG_REGION\":\"${DDG_REGION}\"}
}"

add_server context7 "{
  \"type\":\"stdio\",
  \"command\":\"mcp-context7\",
  \"env\":{\"CONTEXT7_API_KEY\":\"${CONTEXT7_API_KEY}\"}
}"

add_server sequential-thinking '{
  "type":"stdio",
  "command":"mcp-sequential-thinking",
  "env":{}
}'

add_server memory-bank '{
  "type":"stdio",
  "command":"mcp-memory-bank",
  "env":{}
}'

add_server kg-memory "{
  \"type\":\"stdio\",
  \"command\":\"mcp-knowledge-graph\",
  \"env\":{}
}"

if [[ "$VECTOR_STORE" == "chroma" || "$VECTOR_STORE" == "pgvector" ]]; then
  add_server vector-memory "{\"type\":\"stdio\",\"command\":\"mcp-vector-store\",\"env\":{\"VECTOR_STORE\":\"${VECTOR_STORE}\",\"CHROMA_URL\":\"${CHROMA_URL}\",\"LANCEDB_PATH\":\"${LANCEDB_PATH}\"}}"
elif [[ "$VECTOR_STORE" == "lance" ]]; then
  echo ">>> Using LanceDB for vector memory; no additional MCP server needed."
else
  echo ">>> Unknown VECTOR_STORE value '${VECTOR_STORE}'; skipping vector memory MCP server." >&2
fi

add_server pandoc '{
  "type":"stdio",
  "command":"mcp-pandoc",
  "env":{}
}'

add_server compass '{
  "type":"stdio",
  "command":"mcp-compass",
  "env":{}
}'

echo "All MCP servers registered."
