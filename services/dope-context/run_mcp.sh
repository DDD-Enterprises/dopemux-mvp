#!/bin/bash
cd "$(dirname "$0")"
exec python -m src.mcp.server
