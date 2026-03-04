#!/bin/bash
# MCP Server Profile Starter
# Quick way to start different server profiles

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Profile definitions
declare -A PROFILES
PROFILES[minimal]="pal litellm serena qdrant"
PROFILES[development]="pal litellm serena qdrant dope-context task-orchestrator context7 desktop-commander exa"
PROFILES[full]=""  # Empty means all services

show_help() {
    echo -e "${BLUE}MCP Server Profile Starter${NC}"
    echo ""
    echo "Usage: ./start-profile.sh [profile] [options]"
    echo ""
    echo "Profiles:"
    echo -e "  ${GREEN}minimal${NC}      - 5 servers (pal, litellm, serena, qdrant)"
    echo "                   Memory: ~300MB, Startup: ~30s"
    echo ""
    echo -e "  ${GREEN}development${NC}  - 10 servers (minimal + dope-context, task-orchestrator, etc.)"
    echo "                   Memory: ~700MB, Startup: ~45s"
    echo ""
    echo -e "  ${GREEN}full${NC}         - All servers (13+)"
    echo "                   Memory: ~1GB, Startup: ~60s"
    echo ""
    echo "Options:"
    echo "  --stop          Stop current profile before starting new one"
    echo "  --logs          Show logs after starting"
    echo "  --health        Wait and check health after starting"
    echo "  -h, --help      Show this help"
    echo ""
    echo "Examples:"
    echo "  ./start-profile.sh minimal"
    echo "  ./start-profile.sh development --stop --health"
    echo "  ./start-profile.sh full --logs"
}

start_profile() {
    local profile=$1
    local stop_first=${2:-false}
    local show_logs=${3:-false}
    local check_health=${4:-false}

    echo -e "${BLUE}Starting ${profile} profile...${NC}"
    echo ""

    # Stop if requested
    if [ "$stop_first" = true ]; then
        echo -e "${YELLOW}Stopping current services...${NC}"
        docker-compose down
        echo ""
    fi

    # Start services
    if [ "$profile" = "full" ]; then
        echo -e "${GREEN}Starting all services...${NC}"
        docker-compose up -d
    else
        local services="${PROFILES[$profile]}"
        echo -e "${GREEN}Starting: $services${NC}"
        docker-compose up -d $services
    fi

    echo ""
    echo -e "${GREEN}✓ Profile started!${NC}"
    echo ""

    # Show what's running
    echo -e "${BLUE}Running containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep dopemux || echo "No dopemux containers running"
    echo ""

    # Show logs if requested
    if [ "$show_logs" = true ]; then
        echo -e "${BLUE}Showing logs (Ctrl+C to exit):${NC}"
        docker-compose logs -f
    fi

    # Check health if requested
    if [ "$check_health" = true ]; then
        echo -e "${BLUE}Waiting for services to be healthy...${NC}"
        sleep 30
        echo ""
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep dopemux
    fi
}

stop_all() {
    echo -e "${YELLOW}Stopping all MCP servers...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ All servers stopped${NC}"
}

check_status() {
    echo -e "${BLUE}MCP Server Status:${NC}"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep dopemux || echo "No dopemux containers running"
    echo ""
    echo -e "${BLUE}Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep dopemux | head -10
}

# Main script
PROFILE="${1:-}"
STOP_FIRST=false
SHOW_LOGS=false
CHECK_HEALTH=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        minimal|development|full)
            PROFILE="$1"
            shift
            ;;
        --stop)
            STOP_FIRST=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --health)
            CHECK_HEALTH=true
            shift
            ;;
        --status)
            check_status
            exit 0
            ;;
        --stop-all)
            stop_all
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate profile
if [ -z "$PROFILE" ]; then
    show_help
    exit 1
fi

if [[ ! " minimal development full " =~ " $PROFILE " ]]; then
    echo -e "${RED}Invalid profile: $PROFILE${NC}"
    echo "Valid profiles: minimal, development, full"
    exit 1
fi

# Start the profile
start_profile "$PROFILE" "$STOP_FIRST" "$SHOW_LOGS" "$CHECK_HEALTH"
