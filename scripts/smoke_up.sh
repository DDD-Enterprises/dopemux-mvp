#!/usr/bin/env bash
#
# Smoke Stack Startup Script
#
# Brings up smoke stack and runs runtime gate for verification.
#
# Usage:
#   scripts/smoke_up.sh [--no-build] [--wait-time SECONDS]
#
# Options:
#   --no-build     Skip docker build step (use existing images)
#   --wait-time N  Wait N seconds before health checks (default: 10)
#
# Exit codes:
#   0 = Stack up and healthy
#   1 = Stack failed to start or runtime gate failed

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
BUILD=true
WAIT_TIME=10
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-build)
            BUILD=false
            shift
            ;;
        --wait-time)
            WAIT_TIME="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

cd "$REPO_ROOT"

echo -e "${BLUE}🚀 Smoke Stack Startup${NC}"
echo "=================================================="
echo ""

# Step 1: Generate .env.smoke if missing
if [[ ! -f .env.smoke ]]; then
    echo -e "${YELLOW}⚙️  Generating .env.smoke...${NC}"
    if [[ -f tools/generate_smoke_env.py ]]; then
        python tools/generate_smoke_env.py
        echo -e "${GREEN}✅ Generated .env.smoke${NC}"
    else
        echo -e "${RED}❌ tools/generate_smoke_env.py not found${NC}"
        exit 1
    fi
    echo ""
fi

# Step 2: Build + Start
if [[ "$BUILD" == "true" ]]; then
    echo -e "${YELLOW}🔨 Building and starting stack...${NC}"
    docker compose -f docker-compose.smoke.yml up -d --build
else
    echo -e "${YELLOW}🔨 Starting stack (no build)...${NC}"
    docker compose -f docker-compose.smoke.yml up -d
fi

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Failed to start stack${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Stack started${NC}"
echo ""

# Step 3: Wait for startup
echo -e "${YELLOW}⏳ Waiting ${WAIT_TIME}s for services to initialize...${NC}"
sleep "$WAIT_TIME"
echo ""

# Step 4: Run runtime gate
echo -e "${YELLOW}🏥 Running runtime health gate...${NC}"
echo ""

python tools/smoke_runtime_gate.py

GATE_EXIT=$?

echo ""
echo "=================================================="

if [[ $GATE_EXIT -eq 0 ]]; then
    echo -e "${GREEN}✅ Smoke stack is UP and HEALTHY${NC}"
    echo ""
    echo "Next steps:"
    echo "  • View logs:     docker compose -f docker-compose.smoke.yml logs -f"
    echo "  • Stop stack:    scripts/smoke_down.sh"
    echo "  • Manual checks: python tools/ports_health_audit.py --mode runtime"
    exit 0
else
    echo -e "${RED}❌ Smoke stack FAILED runtime gate${NC}"
    echo ""
    echo "Evidence collected in: reports/g35/"
    echo ""
    echo "Troubleshooting:"
    echo "  • Check logs:    docker compose -f docker-compose.smoke.yml logs"
    echo "  • Check status:  docker compose -f docker-compose.smoke.yml ps"
    echo "  • View evidence: cat reports/g35/runtime_gate.md"
    echo "  • Stop stack:    scripts/smoke_down.sh"
    exit 1
fi
