#!/bin/bash
#
# Dopemux Setup Script - One-Command Installation
#
# Installs dopemux for multi-user, multi-project deployment.
# Safe to run multiple times (idempotent).
#
# Usage:
#   ./scripts/setup.sh
#   ./scripts/setup.sh --skip-docker  # Skip Docker services (for testing)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_DOCKER=false
for arg in "$@"; do
    case $arg in
        --skip-docker)
            SKIP_DOCKER=true
            ;;
    esac
done

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🚀 Dopemux Setup - ADHD-Optimized Development Platform    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================

echo -e "${CYAN}📋 Step 1/8: Checking prerequisites...${NC}"

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ Required: $1${NC}"
        echo -e "${YELLOW}   Install $1 and retry${NC}"
        exit 1
    fi
    echo -e "${GREEN}   ✅ $1 found${NC}"
}

check_command git
check_command python3

# Check Python version (need 3.11+)
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.11" ]; then
    echo -e "${RED}❌ Python 3.11+ required (found: $PYTHON_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}   ✅ Python $PYTHON_VERSION${NC}"

if [ "$SKIP_DOCKER" = false ]; then
    check_command docker
fi

# ============================================================================
# Step 2: Setup ~/.dopemux/ Directory
# ============================================================================

echo
echo -e "${CYAN}📁 Step 2/8: Creating ~/.dopemux/ directory...${NC}"

DOPEMUX_HOME="$HOME/.dopemux"
mkdir -p "$DOPEMUX_HOME"/{profiles,databases,cache}
echo -e "${GREEN}   ✅ Created $DOPEMUX_HOME${NC}"

# ============================================================================
# Step 3: Install Default Profiles
# ============================================================================

echo
echo -e "${CYAN}📋 Step 3/8: Installing default profiles...${NC}"

# Copy profile templates
PROFILE_SOURCE="config/profiles"
if [ -d "$PROFILE_SOURCE" ]; then
    for profile in "$PROFILE_SOURCE"/*.yaml; do
        if [ -f "$profile" ]; then
            profile_name=$(basename "$profile")
            dest="$DOPEMUX_HOME/profiles/$profile_name"

            if [ ! -f "$dest" ]; then
                cp "$profile" "$dest"
                echo -e "${GREEN}   ✅ Installed: $(basename "$profile" .yaml)${NC}"
            else
                echo -e "${YELLOW}   ⏭️  Already exists: $(basename "$profile" .yaml)${NC}"
            fi
        fi
    done
else
    echo -e "${YELLOW}   ⚠️  Profile source not found: $PROFILE_SOURCE${NC}"
fi

# ============================================================================
# Step 4: Setup .env File
# ============================================================================

echo
echo -e "${CYAN}🔐 Step 4/8: Setting up environment variables...${NC}"

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}   ✅ Created .env from template${NC}"
        echo -e "${YELLOW}   ⚠️  IMPORTANT: Edit .env and add your API keys!${NC}"
        echo -e "${YELLOW}      Required: OPENAI_API_KEY, VOYAGEAI_API_KEY${NC}"
    else
        echo -e "${YELLOW}   ⚠️  .env.example not found${NC}"
    fi
else
    echo -e "${GREEN}   ✅ .env already exists${NC}"
fi

# ============================================================================
# Step 5: Install Python Package
# ============================================================================

echo
echo -e "${CYAN}📦 Step 5/8: Installing dopemux package...${NC}"

if python3 -m pip install -e . > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Installed dopemux (editable mode)${NC}"
else
    echo -e "${RED}   ❌ pip install failed${NC}"
    exit 1
fi

# Verify installation
if command -v dopemux &> /dev/null; then
    VERSION=$(dopemux --version 2>&1 | head -1 || echo "unknown")
    echo -e "${GREEN}   ✅ dopemux command available: $VERSION${NC}"
else
    echo -e "${YELLOW}   ⚠️  dopemux command not in PATH${NC}"
    echo -e "${YELLOW}      Add to PATH or use: python -m dopemux${NC}"
fi

# ============================================================================
# Step 6: Initialize Git Submodules (Future: Zen MCP)
# ============================================================================

echo
echo -e "${CYAN}🔧 Step 6/8: Initializing git submodules...${NC}"

if git submodule update --init --recursive 2>&1 | grep -q "Submodule"; then
    echo -e "${GREEN}   ✅ Submodules initialized${NC}"
else
    echo -e "${YELLOW}   ⏭️  No submodules configured yet${NC}"
fi

# ============================================================================
# Step 7: Docker Setup (Optional)
# ============================================================================

if [ "$SKIP_DOCKER" = false ]; then
    echo
    echo -e "${CYAN}🐳 Step 7/8: Setting up Docker services...${NC}"

    # Create Docker network
    if docker network create dopemux-unified-network 2>&1 | grep -q "already exists"; then
        echo -e "${YELLOW}   ⏭️  Network already exists: dopemux-unified-network${NC}"
    else
        echo -e "${GREEN}   ✅ Created network: dopemux-unified-network${NC}"
    fi

    # Start MCP services
    echo -e "${CYAN}   🐳 Starting MCP services...${NC}"
    if docker compose -f compose.yml up -d 2>&1 | tail -5; then
        echo -e "${GREEN}   ✅ MCP services started${NC}"
    else
        echo -e "${RED}   ❌ Docker startup failed${NC}"
        exit 1
    fi

    # Wait for services
    echo -e "${CYAN}   ⏳ Waiting for services to be healthy (15s)...${NC}"
    sleep 15
else
    echo
    echo -e "${YELLOW}🐳 Step 7/8: Skipping Docker setup (--skip-docker flag)${NC}"
fi

# ============================================================================
# Step 8: Health Check
# ============================================================================

echo
echo -e "${CYAN}🏥 Step 8/8: Verifying installation...${NC}"

# Check if dopemux health command exists
if command -v dopemux &> /dev/null; then
    if [ "$SKIP_DOCKER" = false ]; then
        echo -e "${CYAN}   Running health check...${NC}"
        if dopemux health 2>&1 | head -10; then
            echo -e "${GREEN}   ✅ Health check passed${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Some services may not be ready yet${NC}"
        fi
    else
        echo -e "${YELLOW}   ⏭️  Skipping health check (Docker not started)${NC}"
    fi
fi

# ============================================================================
# Step 9: ADHD Integration (Optional)
# ============================================================================

echo
echo -e "${CYAN}🧠 Step 9/9: ADHD Engine Integration...${NC}"

if [ -f "./scripts/setup/install-adhd-integration.sh" ]; then
    read -p "   Install ADHD-optimized shell tools/aliases? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}   Installing ADHD tools...${NC}"
        ./scripts/setup/install-adhd-integration.sh
    else
        echo -e "${YELLOW}   ⏭️  Skipping ADHD integration${NC}"
    fi
else
    echo -e "${YELLOW}   ⏭️  ADHD installer not found${NC}"
fi

# ============================================================================
# Installation Complete!
# ============================================================================

echo
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ Dopemux Setup Complete! ✅                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${CYAN}📚 Next Steps:${NC}"
echo
echo -e "  ${CYAN}1.${NC} Edit .env with your API keys:"
echo -e "     ${YELLOW}nano .env${NC}"
echo -e "     Required: OPENAI_API_KEY, VOYAGEAI_API_KEY"
echo
echo -e "  ${CYAN}2.${NC} Initialize dopemux in your project:"
echo -e "     ${YELLOW}cd ~/my-project${NC}"
echo -e "     ${YELLOW}dopemux init${NC}"
echo -e "     (Auto-detects project type and suggests profile)"
echo
echo -e "  ${CYAN}3.${NC} Start working:"
echo -e "     ${YELLOW}dopemux start${NC}"
echo
echo -e "${CYAN}📖 Documentation:${NC}"
echo -e "  • Profiles: ${YELLOW}dopemux profile list${NC}"
echo -e "  • Decisions: ${YELLOW}dopemux decisions --help${NC}"
echo -e "  • Health: ${YELLOW}dopemux health${NC}"
echo
echo -e "${GREEN}🎉 Happy coding with ADHD-optimized development!${NC}"
echo
