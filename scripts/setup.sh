#!/bin/bash
#
# Dopemux Setup — COMPATIBILITY SHIM (restored 2026-07-28, PR #1150 supervisor MUST_FIX P1).
#
# The original one-command setup script was retired under design packet P-22
# (claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md): it duplicated the
# canonical installer and started fleet services with raw docker compose.
# Installation tutorials (docs/01-tutorials/installation.md) still direct fresh
# users here, so this shim preserves the documented entrypoint and flags while
# delegating ONLY to the canonical installer and the dopemux MCP lifecycle.
#
# Usage (unchanged):
#   ./scripts/setup.sh                 # one-command install (delegates to ./install.sh --quick --yes)
#   ./scripts/setup.sh --skip-docker   # skip Docker services (delegates to the installer's
#                                      # documented INSTALLER_TEST_MODE=1 dry-run guard)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SKIP_DOCKER=false
for arg in "$@"; do
    case "$arg" in
        --skip-docker)
            SKIP_DOCKER=true
            ;;
        *)
            echo "warning: unknown option '$arg' (supported: --skip-docker)" >&2
            ;;
    esac
done

echo "scripts/setup.sh is a compatibility shim — delegating to the canonical installer (./install.sh)."

if [ "$SKIP_DOCKER" = true ]; then
    echo "--skip-docker: running the installer with its documented INSTALLER_TEST_MODE guard"
    echo "(skips docker checks, network creation, and compose pull/up)."
    echo "Start Docker MCP services later with: dopemux mcp start"
    INSTALLER_TEST_MODE=1 ./install.sh --quick --yes
else
    ./install.sh --quick --yes
fi
