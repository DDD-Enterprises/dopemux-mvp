#!/usr/bin/env bash
#
# Smoke Stack Shutdown Script
#
# Gracefully shuts down smoke stack with optional volume cleanup.
#
# Usage:
#   scripts/smoke_down.sh [--volumes]
#
# Options:
#   --volumes    Also remove volumes (WARNING: destroys data)
#
# Exit codes:
#   0 = Successfully shut down
#   1 = Shutdown failed

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
REMOVE_VOLUMES=false
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

cd "$REPO_ROOT"

echo -e "${BLUE}🛑 Smoke Stack Shutdown${NC}"
echo "=================================================="
echo ""

if [[ "$REMOVE_VOLUMES" == "true" ]]; then
    echo -e "${YELLOW}⚠️  Stopping stack AND removing volumes (data will be lost)${NC}"
    read -p "Are you sure? (yes/no): " -r
    echo ""

    if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Cancelled${NC}"
        exit 0
    fi

    docker compose -f docker-compose.smoke.yml down --volumes
else
    echo -e "${YELLOW}🛑 Stopping stack (preserving volumes)${NC}"
    docker compose -f docker-compose.smoke.yml down
fi

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Failed to stop stack${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Stack stopped${NC}"
echo ""

if [[ "$REMOVE_VOLUMES" == "true" ]]; then
    echo "Volumes removed: postgres data, redis data, qdrant data"
else
    echo "Volumes preserved (use --volumes to remove)"
fi

echo ""
echo "Next steps:"
echo "  • Start again:   scripts/smoke_up.sh"
echo "  • View remnants: docker ps -a"
echo "  • Clean images:  docker image prune"
