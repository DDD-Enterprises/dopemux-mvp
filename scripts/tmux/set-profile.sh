#!/bin/bash
# Dopemux Profile Management Script
# Switch between different security and operational profiles

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"
PROFILES_DIR="$CONFIG_DIR/profiles"
ENV_FILE="$PROJECT_ROOT/.env"

# Available profiles
AVAILABLE_PROFILES=("dangerous" "safe" "development" "production")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "Dopemux Profile Management"
    echo ""
    echo "Usage: $0 [COMMAND] [PROFILE]"
    echo ""
    echo "Commands:"
    echo "  set <profile>    Set active profile"
    echo "  current          Show current profile"
    echo "  list             List available profiles"
    echo "  help             Show this help"
    echo ""
    echo "Available Profiles:"
    echo "  dangerous        No approval gates, all tools available (⚠️  DEV ONLY)"
    echo "  safe            Full security restrictions (PRODUCTION)"
    echo "  development     Balanced settings for development"
    echo "  production      Alias for 'safe'"
    echo ""
    echo "Examples:"
    echo "  $0 set dangerous     # Enable dangerous mode"
    echo "  $0 set safe         # Enable safe mode"
    echo "  $0 current          # Show current profile"
}

get_current_profile() {
    if [[ -f "$ENV_FILE" ]]; then
        if grep -q "DOPEMUX_DANGEROUS_MODE=true" "$ENV_FILE" 2>/dev/null; then
            echo "dangerous"
        elif grep -q "DOPEMUX_PROFILE=" "$ENV_FILE" 2>/dev/null; then
            grep "DOPEMUX_PROFILE=" "$ENV_FILE" | cut -d'=' -f2
        else
            echo "default"
        fi
    else
        echo "unknown"
    fi
}

set_profile() {
    local profile="$1"

    # Validate profile
    if [[ ! " ${AVAILABLE_PROFILES[@]} " =~ " ${profile} " ]] && [[ "$profile" != "development" ]] && [[ "$profile" != "production" ]]; then
        echo -e "${RED}Error: Unknown profile '$profile'${NC}"
        echo "Available profiles: ${AVAILABLE_PROFILES[*]}"
        exit 1
    fi

    # Handle aliases
    case "$profile" in
        "production") profile="safe" ;;
        "development") profile="dangerous" ;;
    esac

    echo -e "${BLUE}Setting Dopemux profile to: ${GREEN}$profile${NC}"

    # Backup current .env
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}Backed up current .env file${NC}"
    fi

    case "$profile" in
        "dangerous")
            set_dangerous_profile
            ;;
        "safe")
            set_safe_profile
            ;;
        *)
            echo -e "${RED}Error: Profile implementation for '$profile' not found${NC}"
            exit 1
            ;;
    esac

    echo -e "${GREEN}✅ Profile '$profile' activated successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Restart any running Dopemux instances:"
    echo "   dopemux stop && dopemux start"
    echo ""
    echo "2. Verify the profile is active:"
    echo "   $0 current"
}

set_dangerous_profile() {
    # Ensure the dangerous mode environment variables are set
    if ! grep -q "DOPEMUX_DANGEROUS_MODE=true" "$ENV_FILE" 2>/dev/null; then
        echo -e "${YELLOW}Adding dangerous mode environment variables...${NC}"
        cat >> "$ENV_FILE" << 'EOF'

# ===========================================
# DANGEROUS MODE PROFILE SETTINGS
# ===========================================
DOPEMUX_PROFILE=dangerous
DOPEMUX_DANGEROUS_MODE=true
HOOKS_ENABLE_ADAPTIVE_SECURITY=0
CLAUDE_CODE_SKIP_PERMISSIONS=true
METAMCP_ROLE_ENFORCEMENT=false
METAMCP_APPROVAL_REQUIRED=false
METAMCP_BUDGET_ENFORCEMENT=false
EOF
    fi

    # Copy dangerous profile configuration
    if [[ -f "$PROFILES_DIR/dangerous.yaml" ]]; then
        cp "$PROFILES_DIR/dangerous.yaml" "$CONFIG_DIR/active-profile.yaml"
        echo -e "${YELLOW}Applied dangerous profile configuration${NC}"
    fi

    echo -e "${RED}⚠️  WARNING: DANGEROUS MODE ENABLED${NC}"
    echo -e "${RED}   All safety restrictions are DISABLED${NC}"
    echo -e "${RED}   Use only in isolated development environments!${NC}"
}

set_safe_profile() {
    # Remove dangerous mode settings from .env
    if [[ -f "$ENV_FILE" ]]; then
        # Remove dangerous mode section and variables
        sed -i.bak '/DANGEROUS MODE PROFILE SETTINGS/,/^$/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/DOPEMUX_DANGEROUS_MODE/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/HOOKS_ENABLE_ADAPTIVE_SECURITY/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/CLAUDE_CODE_SKIP_PERMISSIONS/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/METAMCP_ROLE_ENFORCEMENT/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/METAMCP_APPROVAL_REQUIRED/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/METAMCP_BUDGET_ENFORCEMENT/d' "$ENV_FILE" 2>/dev/null || true
        rm -f "$ENV_FILE.bak" 2>/dev/null || true
    fi

    # Add safe mode settings
    if ! grep -q "DOPEMUX_PROFILE=safe" "$ENV_FILE" 2>/dev/null; then
        echo "" >> "$ENV_FILE"
        echo "# Safe mode profile settings" >> "$ENV_FILE"
        echo "DOPEMUX_PROFILE=safe" >> "$ENV_FILE"
    fi

    # Copy safe profile configuration
    if [[ -f "$PROFILES_DIR/safe.yaml" ]]; then
        cp "$PROFILES_DIR/safe.yaml" "$CONFIG_DIR/active-profile.yaml"
        echo -e "${YELLOW}Applied safe profile configuration${NC}"
    fi

    echo -e "${GREEN}✅ SAFE MODE ENABLED${NC}"
    echo -e "${GREEN}   All security restrictions are active${NC}"
}

list_profiles() {
    echo "Available Dopemux Profiles:"
    echo ""

    current=$(get_current_profile)

    for profile in "${AVAILABLE_PROFILES[@]}"; do
        if [[ "$profile" == "$current" ]]; then
            echo -e "  ${GREEN}✓ $profile (current)${NC}"
        else
            echo "    $profile"
        fi
    done

    echo ""
    echo "Aliases:"
    echo "  development -> dangerous"
    echo "  production  -> safe"
}

show_current() {
    local current_profile
    current_profile=$(get_current_profile)

    echo "Current Dopemux Profile: $current_profile"

    case "$current_profile" in
        "dangerous")
            echo -e "${RED}⚠️  Dangerous Mode Active - No Safety Restrictions${NC}"
            ;;
        "safe")
            echo -e "${GREEN}✅ Safe Mode Active - Full Security Enabled${NC}"
            ;;
        "default")
            echo -e "${YELLOW}Default configuration (no explicit profile set)${NC}"
            ;;
        "unknown")
            echo -e "${YELLOW}Unable to determine profile (.env file not found)${NC}"
            ;;
    esac
}

# Main script logic
case "${1:-help}" in
    "set")
        if [[ -z "${2:-}" ]]; then
            echo -e "${RED}Error: Profile name required${NC}"
            echo "Usage: $0 set <profile>"
            exit 1
        fi
        set_profile "$2"
        ;;
    "current")
        show_current
        ;;
    "list")
        list_profiles
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        show_help
        exit 1
        ;;
esac