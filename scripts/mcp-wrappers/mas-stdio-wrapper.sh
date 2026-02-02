#!/bin/bash
# Wrapper script for mas-sequential-thinking MCP server via docker exec
exec docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking "$@"