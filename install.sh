#!/bin/bash
#
# Dopemux Universal Installer
# 
# One-command installation for dopemux across all supported platforms
# Designed for ADHD developers - clear progress, helpful errors, easy rollback
#
# Usage:
#   curl -fsSL https://get.dopemux.dev/install.sh | bash
#   ./install.sh                    # Interactive mode
#   ./install.sh --quick            # Quick setup (core only)
#   ./install.sh --full             # Full setup (all features)
#   ./install.sh --verify           # Verify existing installation
#   ./install.sh --uninstall        # Remove dopemux
#
# Version: 1.0.0
# Last Updated: 2025-11-13
#

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# --- Fail-Safe Rollback Trap ---
on_error() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ "$INSTALL_MODE" != "uninstall" ]; then
        echo
        error "Installation failed at step: $BASH_COMMAND"
        warning "Would you like to cleanup partially installed files in $DOPEMUX_HOME?"
        if ask_yes_no "Cleanup & Exit?" "n"; then
            rm -rf "$DOPEMUX_HOME"
            success "Cleanup complete. You can try again later."
        else
            log "Leaving files for debugging. Check $DOPEMUX_HOME for logs."
        fi
    fi
    exit $exit_code
}
trap on_error ERR

# ============================================================================
# Configuration & Constants
# ============================================================================

VERSION="1.0.0"
DOPEMUX_HOME="${DOPEMUX_HOME:-$HOME/.dopemux}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
BACKUP_DIR="$HOME/.dopemux.backup.$(date +%Y%m%d_%H%M%S)"
DOCKER_COMPOSE_CORE="-f compose.yml"
DOCKER_COMPOSE_RESEARCH="-f compose.yml"
DOCKER_COMPOSE_FULL="-f compose.yml"
SELECTED_STACK="core"  # core | research | full
SELECTED_COMPOSE_FILE="$DOCKER_COMPOSE_CORE"
ENV_FILE="${ENV_FILE:-.env}"
STACK_SELECTED_FROM_FLAG=false
INSTALLER_TEST_MODE="${INSTALLER_TEST_MODE:-0}"
STARTED_CAPABILITIES=()
DEFERRED_CAPABILITIES=()
RESOLVED_SECRET_VALUE=""
SECRET_SOURCE_CHOICE=""

CORE_STACK_PORTS=(5432 6379 6333 6334 3004 8000 8095)
RESEARCH_STACK_EXTRA_PORTS=(3009 3011)
FULL_STACK_EXTRA_PORTS=(3003 3009 3011 3012 3015 3016 4000 8081 8090 8790)

CORE_STACK_ENV_VARS=(
    AGE_PASSWORD
    TASK_ORCHESTRATOR_API_KEY
    ADHD_ENGINE_API_KEY
)
RESEARCH_STACK_ENV_VARS=(
    OPENAI_API_KEY
    TAVILY_API_KEY
    EXA_API_KEY
)
FULL_STACK_ENV_VARS=(
    AGE_PASSWORD
    ANTHROPIC_API_KEY
    OPENAI_API_KEY
    OPENROUTER_API_KEY
    GEMINI_API_KEY
    XAI_API_KEY
    VOYAGE_API_KEY
    LEANTIME_URL
    LEANTIME_TOKEN
    TASK_ORCHESTRATOR_API_KEY
    ADHD_ENGINE_API_KEY
    LITELLM_MASTER_KEY
    LITELLM_DATABASE_URL
    TAVILY_API_KEY
    EXA_API_KEY
    OPENAI_WEBHOOK_SECRET
)

CORE_STACK_SUMMARY=(
    "PostgreSQL 16 + AGE extension"
    "Redis 7 (cache/event bus)"
    "Qdrant vector DB"
    "ConPort MCP server"
    "ADHD Engine API"
    "Task Orchestrator"
)
RESEARCH_STACK_SUMMARY=(
    "Everything from core stack"
    "GPT-Researcher (Deep academic research)"
    "Exa (Neural search engine)"
)
FULL_STACK_SUMMARY=(
    "Everything from core stack"
    "Project Management (Leantime + MySQL)"
    "Model Routing (LiteLLM + PAL)"
    "Research Tools (GPT-Researcher + Exa)"
    "Agents & Automation (Desktop Commander + Webhooks)"
)

CORE_STACK_ESTIMATE="~3-5 minutes"
RESEARCH_STACK_ESTIMATE="~5-8 minutes"
FULL_STACK_ESTIMATE="~10-15 minutes"


# Required versions
REQUIRED_PYTHON_VERSION="3.11"
REQUIRED_DOCKER_VERSION="20.10"
REQUIRED_GIT_VERSION="2.30"

# Colors for output (ADHD-friendly visual hierarchy)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

# Installation mode
INSTALL_MODE="interactive"  # interactive, quick, full, verify, uninstall
AUTO_CONFIRM=false
VERBOSE=false

# ============================================================================
# Utility Functions
# ============================================================================

log() {
    echo -e "${CYAN}ℹ${NC}  $*"
}

success() {
    echo -e "${GREEN}✅${NC} $*"
}

warning() {
    echo -e "${YELLOW}⚠️${NC}  $*"
}

error() {
    echo -e "${RED}❌${NC} $*" >&2
}

fatal() {
    error "$*"
    echo
    error "Installation failed. See above for details."
    error "For help, visit: https://github.com/dopemux/dopemux-mvp/issues"
    exit 1
}

debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${MAGENTA}🔍${NC} $*"
    fi
}

# ============================================================================
# Stack & Environment Helpers
# ============================================================================

compose_file_for_stack() {
    local stack="${1:-core}"
    case "$stack" in
        full) echo "$DOCKER_COMPOSE_FULL" ;;
        research) echo "$DOCKER_COMPOSE_RESEARCH" ;;
        *) echo "$DOCKER_COMPOSE_CORE" ;;
    esac
}

stack_estimate() {
    case "$1" in
        full) echo "$FULL_STACK_ESTIMATE" ;;
        research) echo "$RESEARCH_STACK_ESTIMATE" ;;
        *) echo "$CORE_STACK_ESTIMATE" ;;
    esac
}

stack_summary_items() {
    case "$1" in
        full)
            printf "%s\n" "${FULL_STACK_SUMMARY[@]}"
            ;;
        research)
            printf "%s\n" "${RESEARCH_STACK_SUMMARY[@]}"
            ;;
        *)
            printf "%s\n" "${CORE_STACK_SUMMARY[@]}"
            ;;
    esac
}

show_stack_summary() {
    local stack="${1:-core}"
    local estimate
    estimate=$(stack_estimate "$stack")
    local stack_upper
    stack_upper=$(printf '%s' "$stack" | tr '[:lower:]' '[:upper:]')
    echo
    echo -e "${BOLD}Selected stack:${NC} ${stack_upper}  |  Estimated runtime: $estimate"
    echo "Includes:"
    local item
    while IFS= read -r item; do
        [ -z "$item" ] && continue
        echo "  - $item"
    done <<EOF
$(stack_summary_items "$stack")
EOF
    echo
}

env_prompt() {
    case "$1" in
        AGE_PASSWORD) echo "PostgreSQL AGE password (ConPort, LiteLLM, bridge)" ;;
        ANTHROPIC_API_KEY) echo "Anthropic Claude API key (sk-ant-...)" ;;
        OPENAI_API_KEY) echo "OpenAI API key (Zen/LiteLLM fallback)" ;;
        OPENROUTER_API_KEY) echo "OpenRouter API key (Grok/GPT routing)" ;;
        GEMINI_API_KEY) echo "Google Gemini API key (optional)" ;;
        XAI_API_KEY) echo "xAI Grok API key (optional)" ;;
        VOYAGE_API_KEY) echo "Voyage API key (Dope-Context + GPT-Researcher embeddings)" ;;
        TAVILY_API_KEY) echo "Tavily API key (GPT-Researcher web search)" ;;
        EXA_API_KEY) echo "Exa API key (research fallback search)" ;;
        LEANTIME_URL) echo "Leantime base URL" ;;
        LEANTIME_TOKEN) echo "Leantime API token" ;;
        TASK_ORCHESTRATOR_API_KEY) echo "Task Orchestrator API key" ;;
        ADHD_ENGINE_API_KEY) echo "ADHD Engine API key" ;;
        LITELLM_MASTER_KEY) echo "LiteLLM master key (generate with: printf 'sk-%s\\n' \"$(openssl rand -hex 32)\")" ;;
        LITELLM_DATABASE_URL) echo "LiteLLM database URL (PostgreSQL DSN)" ;;
        OPENAI_WEBHOOK_SECRET) echo "OpenAI webhook secret (optional receiver verification)" ;;
        *) echo "$1" ;;
    esac
}

env_default() {
    case "$1" in
        AGE_PASSWORD) env_generated_secret ;;
        LEANTIME_URL) echo "http://localhost:8097" ;;
        TASK_ORCHESTRATOR_API_KEY) env_generated_secret ;;
        ADHD_ENGINE_API_KEY) env_generated_secret ;;
        LITELLM_MASTER_KEY) python3 -c 'import secrets; print("sk-" + secrets.token_hex(32))' ;;
        LITELLM_DATABASE_URL)
            local age_password="${AGE_PASSWORD:-$(env_generated_secret)}"
            echo "postgresql://dopemux_age:${age_password}@dopemux-postgres-age:5432/litellm"
            ;;
        *) echo "" ;;
    esac
}

env_generated_secret() {
    python3 -c 'import secrets; print(secrets.token_hex(32))'
}

env_is_placeholder_value() {
    local value="${1:-}"
    local lowered
    lowered=$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')

    case "$lowered" in
        your_secure_*|your_*_here|dev-key-*|changeme*|change_me*|*_placeholder|dopemux_age_dev_password)
            return 0
            ;;
        postgresql://dopemux_age:dopemux_age_dev_password@*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

env_is_sensitive() {
    case "$1" in
        AGE_PASSWORD|ANTHROPIC_API_KEY|OPENAI_API_KEY|OPENROUTER_API_KEY|GEMINI_API_KEY|XAI_API_KEY|VOYAGE_API_KEY|TAVILY_API_KEY|EXA_API_KEY|LEANTIME_TOKEN|TASK_ORCHESTRATOR_API_KEY|ADHD_ENGINE_API_KEY|LITELLM_MASTER_KEY|LITELLM_DATABASE_URL|OPENAI_WEBHOOK_SECRET)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Installer policy:
# - local-defaultable: a deterministic repo-local default is safe to use.
# - provider-optional: no safe default exists; the user can keep an existing
#   value, enter one directly, source it from an external secret store/command,
#   or defer the capability.
# - boot-critical: reserved for future values that cannot be deferred.
#   This installer currently keeps that set empty and fails closed in --yes
#   mode when a provider-optional value is missing.
env_policy() {
    case "$1" in
        AGE_PASSWORD|LEANTIME_URL|TASK_ORCHESTRATOR_API_KEY|ADHD_ENGINE_API_KEY|LITELLM_MASTER_KEY|LITELLM_DATABASE_URL)
            echo "local-defaultable"
            ;;
        ANTHROPIC_API_KEY|OPENAI_API_KEY|OPENROUTER_API_KEY|GEMINI_API_KEY|XAI_API_KEY|VOYAGE_API_KEY|TAVILY_API_KEY|EXA_API_KEY|LEANTIME_TOKEN|OPENAI_WEBHOOK_SECRET)
            echo "provider-optional"
            ;;
        *)
            echo "boot-critical"
            ;;
    esac
}

capability_label() {
    case "$1" in
        AGE_PASSWORD) echo "PostgreSQL AGE password" ;;
        ANTHROPIC_API_KEY) echo "Anthropic provider" ;;
        OPENAI_API_KEY) echo "OpenAI provider" ;;
        OPENROUTER_API_KEY) echo "OpenRouter provider" ;;
        GEMINI_API_KEY) echo "Gemini provider" ;;
        XAI_API_KEY) echo "xAI provider" ;;
        VOYAGE_API_KEY) echo "Voyage embeddings" ;;
        TAVILY_API_KEY) echo "Tavily research" ;;
        EXA_API_KEY) echo "Exa search" ;;
        LEANTIME_URL) echo "Leantime URL" ;;
        LEANTIME_TOKEN) echo "Leantime sync" ;;
        TASK_ORCHESTRATOR_API_KEY) echo "Task Orchestrator auth" ;;
        ADHD_ENGINE_API_KEY) echo "ADHD Engine auth" ;;
        LITELLM_MASTER_KEY) echo "LiteLLM master key" ;;
        LITELLM_DATABASE_URL) echo "LiteLLM database URL" ;;
        OPENAI_WEBHOOK_SECRET) echo "OpenAI webhook verification" ;;
        *) echo "$1" ;;
    esac
}

record_capability_status() {
    local status="$1"
    local label="$2"

    case "$status" in
        started)
            STARTED_CAPABILITIES+=("$label")
            ;;
        deferred)
            DEFERRED_CAPABILITIES+=("$label")
            ;;
    esac
}

resolve_existing_env_value() {
    local var="$1"
    local env_file="$2"
    local shell_override="${!var:-}"
    local value=""
    local source=""
    if [ -n "$shell_override" ]; then
        value="$shell_override"
        source="shell environment"
    else
        value=$(read_env_file_value "$var" "$env_file")
        source="$env_file"
    fi

    if [ -n "$value" ] && env_is_placeholder_value "$value"; then
        warning "$var is set to a placeholder or development value in $source; ignoring it." >&2
        echo ""
        return 0
    fi

    echo "$value"
}

read_secret_from_keychain() {
    local service="$1"
    if ! check_command security; then
        return 1
    fi
    security find-generic-password -w -s "$service" 2>/dev/null
}

read_secret_from_1password() {
    local ref="$1"
    if ! check_command op; then
        return 1
    fi
    if [ -z "$ref" ]; then
        return 1
    fi
    op read "$ref" 2>/dev/null
}

read_secret_from_command() {
    local command_spec="$1"
    if [ -z "$command_spec" ]; then
        return 1
    fi
    bash -lc "$command_spec" 2>/dev/null
}

prompt_secret_source() {
    local var="$1"
    SECRET_SOURCE_CHOICE=""

    echo
    echo "How should $(capability_label "$var") be provided?"
    echo "  1) Enter it manually now"
    echo "  2) Load from macOS Keychain"
    echo "  3) Load from 1Password CLI"
    echo "  4) Run a command"
    echo "  5) Defer this capability for now"
    if ! read -p "$(echo -e "${CYAN}?${NC} Choose [1-5]: ")" source_choice; then
        echo >&2 "EOF encountered"
        exit 1
    fi

    case "${source_choice:-1}" in
        1) SECRET_SOURCE_CHOICE="manual" ;;
        2) SECRET_SOURCE_CHOICE="keychain" ;;
        3) SECRET_SOURCE_CHOICE="1password" ;;
        4) SECRET_SOURCE_CHOICE="command" ;;
        5) SECRET_SOURCE_CHOICE="defer" ;;
        *)
            warning "Please choose a source between 1 and 5."
            SECRET_SOURCE_CHOICE="invalid"
            ;;
    esac
    echo "$SECRET_SOURCE_CHOICE"
}

resolve_secret_value() {
    local var="$1"
    local current="$2"
    local env_file="$3"
    RESOLVED_SECRET_VALUE=""
    local policy
    policy=$(env_policy "$var")
    local label
    label=$(capability_label "$var")
    local default
    default=$(env_default "$var")
    local prompt
    prompt=$(env_prompt "$var")
    local sensitive="false"
    if env_is_sensitive "$var"; then
        sensitive="true"
    fi

    if [ -n "$current" ]; then
        if [ "$AUTO_CONFIRM" = true ]; then
            export "$var=$current"
            record_capability_status "started" "$label"
            RESOLVED_SECRET_VALUE="$current"
            echo "$current"
            return 0
        fi

        local display_value="$current"
        if [ "$sensitive" = "true" ] && [ ${#current} -gt 8 ]; then
            display_value="${current:0:4}...${current: -4}"
        fi
        log "$var currently set to: $display_value"
        if ask_yes_no "Keep existing value?" "y"; then
            export "$var=$current"
            record_capability_status "started" "$label"
            RESOLVED_SECRET_VALUE="$current"
            echo "$current"
            return 0
        fi
    fi

    case "$policy" in
        local-defaultable)
            if [ "$AUTO_CONFIRM" = true ]; then
                export "$var=$default"
                record_capability_status "started" "$label"
                RESOLVED_SECRET_VALUE="$default"
                echo "$default"
                return 0
            fi

            local input=""
            while true; do
                local prompt_hint=""
                if [ -n "$default" ]; then
                    prompt_hint=" (press Enter for default)"
                fi

                if [ "$sensitive" = "true" ]; then
                    if [ -n "$default" ]; then
                        if ! read -s -p "$(echo -e "${CYAN}?${NC} $prompt${prompt_hint} [****]: ")" input; then echo >&2 "EOF"; exit 1; fi
                        echo >&2
                    else
                        if ! read -s -p "$(echo -e "${CYAN}?${NC} $prompt${prompt_hint}: ")" input; then echo >&2 "EOF"; exit 1; fi
                        echo >&2
                    fi
                else
                    if [ -n "$default" ]; then
                        if ! read -p "$(echo -e "${CYAN}?${NC} $prompt${prompt_hint} [$default]: ")" input; then echo >&2 "EOF"; exit 1; fi
                    else
                        if ! read -p "$(echo -e "${CYAN}?${NC} $prompt${prompt_hint}: ")" input; then echo >&2 "EOF"; exit 1; fi
                    fi
                fi

                input=${input:-$default}
                if [ -n "$input" ]; then
                    export "$var=$input"
                    record_capability_status "started" "$label"
                    RESOLVED_SECRET_VALUE="$input"
                    echo "$input"
                    return 0
                fi

                warning "$var cannot be empty"
            done
            ;;
        provider-optional)
            if [ "$AUTO_CONFIRM" = true ]; then
                unset "$var"
                record_capability_status "deferred" "$label"
                RESOLVED_SECRET_VALUE=""
                echo ""
                return 0
            fi

            while true; do
                prompt_secret_source "$var" >/dev/null
                case "$SECRET_SOURCE_CHOICE" in
                    manual)
                        local input=""
                        if ! read -s -p "$(echo -e "${CYAN}?${NC} Enter $prompt: ")" input; then echo >&2 "EOF"; exit 1; fi
                        echo >&2
                        if [ -n "$input" ]; then
                            export "$var=$input"
                            record_capability_status "started" "$label"
                            RESOLVED_SECRET_VALUE="$input"
                            echo "$input"
                            return 0
                        fi
                        warning "$var cannot be empty"
                        ;;
                    keychain)
                        local service_name="${var}"
                        local keychain_value=""
                        if ! read -p "$(echo -e "${CYAN}?${NC} Keychain service name [$service_name]: ")" keychain_value; then echo >&2 "EOF"; exit 1; fi
                        keychain_value=${keychain_value:-$service_name}
                        if keychain_value=$(read_secret_from_keychain "$keychain_value"); then
                            export "$var=$keychain_value"
                            record_capability_status "started" "$label"
                            RESOLVED_SECRET_VALUE="$keychain_value"
                            echo "$keychain_value"
                            return 0
                        fi
                        warning "Could not read $var from the macOS Keychain."
                        ;;
                    1password)
                        local op_ref=""
                        if ! read -p "$(echo -e "${CYAN}?${NC} 1Password item reference for $var: ")" op_ref; then echo >&2 "EOF"; exit 1; fi
                        if op_value=$(read_secret_from_1password "$op_ref"); then
                            export "$var=$op_value"
                            record_capability_status "started" "$label"
                            RESOLVED_SECRET_VALUE="$op_value"
                            echo "$op_value"
                            return 0
                        fi
                        warning "Could not read $var from 1Password CLI."
                        ;;
                    command)
                        local command_spec=""
                        if ! read -p "$(echo -e "${CYAN}?${NC} Command that prints $var: ")" command_spec; then echo >&2 "EOF"; exit 1; fi
                        if command_value=$(read_secret_from_command "$command_spec"); then
                            export "$var=$command_value"
                            record_capability_status "started" "$label"
                            RESOLVED_SECRET_VALUE="$command_value"
                            echo "$command_value"
                            return 0
                        fi
                        warning "Command lookup for $var failed."
                        ;;
                    defer)
                        unset "$var"
                        record_capability_status "deferred" "$label"
                        RESOLVED_SECRET_VALUE=""
                        echo ""
                        return 0
                        ;;
                    invalid)
                        continue
                        ;;
                esac
            done
            ;;
        *)
            if [ "$AUTO_CONFIRM" = true ]; then
                fatal "$var is not configured. Pre-populate $ENV_FILE or export it before using --yes, or run without --yes to choose a source or defer the capability."
            fi
            warning "$var does not have a safe default."
            ;;
    esac
}

show_capability_summary() {
    echo
    echo -e "${BOLD}Capability status:${NC}"
    if [ ${#STARTED_CAPABILITIES[@]} -gt 0 ]; then
        echo -e "${GREEN}Started:${NC}"
        local item
        for item in "${STARTED_CAPABILITIES[@]}"; do
            echo "  - $item"
        done
    else
        echo -e "${GREEN}Started:${NC} none"
    fi

    if [ ${#DEFERRED_CAPABILITIES[@]} -gt 0 ]; then
        echo -e "${YELLOW}Deferred:${NC}"
        local deferred_item
        for deferred_item in "${DEFERRED_CAPABILITIES[@]}"; do
            echo "  - $deferred_item"
        done
    else
        echo -e "${YELLOW}Deferred:${NC} none"
    fi
    echo
}

read_env_file_value() {
    local var="$1"
    local env_file="$2"
    if [ ! -f "$env_file" ]; then
        echo ""
        return 0
    fi
    set +e
    local line
    line=$(grep -E "^${var}=" "$env_file" | tail -1)
    local status=$?
    set -e
    if [ $status -ne 0 ] || [ -z "$line" ]; then
        echo ""
        return 0
    fi
    echo "${line#*=}"
}

choose_install_stack() {
    if [ "$STACK_SELECTED_FROM_FLAG" = true ]; then
        show_stack_summary "$SELECTED_STACK"
        return 0
    fi

    if [ "$AUTO_CONFIRM" = true ]; then
        log "Auto mode using ${SELECTED_STACK} stack"
        show_stack_summary "$SELECTED_STACK"
        return 0
    fi

    while true; do
        echo "Select installation scope:"
        echo "  1) Core services (Postgres, Redis, Qdrant, ConPort, ADHD Engine, Task Orchestrator)"
        echo "  2) Research stack (adds GPT-Researcher, Exa)"
        echo "  3) Full stack (adds everything including PM, LiteLLM, Agents)"
        if ! read -p "$(echo -e "${CYAN}?${NC} Choose [1/2/3]: ")" stack_choice; then
            echo >&2 "EOF encountered"
            exit 1
        fi
        case "${stack_choice:-1}" in
            3) SELECTED_STACK="full" ;;
            2) SELECTED_STACK="research" ;;
            1|*) SELECTED_STACK="core" ;;
        esac
        show_stack_summary "$SELECTED_STACK"
        if ask_yes_no "Proceed with the ${SELECTED_STACK} stack?" "y"; then
            break
        fi
        echo
    done
}

ensure_docker_networks() {
    local stack="${1:-core}"
    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping docker network creation"
        return 0
    fi
    # BETA-INSTALL-02: compose.yml declares "dopemux-network" as external: true
    # for ALL services — every stack type (core/research/full) needs it.
    # Create it unconditionally so core and --quick installs don't fail with
    # "network not found" when docker compose up runs.
    local core_networks=("dopemux-network")
    # mcp-network and leantime-net are only referenced by full-stack services.
    local full_only_networks=("mcp-network" "leantime-net")

    local networks=("${core_networks[@]}")
    if [ "$stack" = "full" ]; then
        networks+=("${full_only_networks[@]}")
    fi

    for network in "${networks[@]}"; do
        if docker network ls --format '{{.Name}}' | grep -q "^${network}$"; then
            debug "Docker network already exists: $network"
        else
            log "Creating docker network: $network"
            docker network create "$network" >/dev/null
        fi
    done
}

resolve_env_value() {
    local var="$1"
    local current="$2"
    resolve_secret_value "$var" "$current" "$ENV_FILE" >/dev/null
    echo "$RESOLVED_SECRET_VALUE"
}

ensure_env_file() {
    local stack="${1:-core}"
    local env_file="$ENV_FILE"
    STARTED_CAPABILITIES=()
    DEFERRED_CAPABILITIES=()
    local -a required_vars=()
    if [ "$stack" = "full" ]; then
        required_vars=("${FULL_STACK_ENV_VARS[@]}")
    elif [ "$stack" = "research" ]; then
        required_vars=("${RESEARCH_STACK_ENV_VARS[@]}")
    elif [ "$stack" = "core" ]; then
        required_vars=("${CORE_STACK_ENV_VARS[@]}")
    fi

    if [ ${#required_vars[@]} -eq 0 ]; then
        return 0
    fi

    echo
    warning "SECURITY NOTICE: The ${stack} stack requires API keys."
    warning "These keys will be stored in plain-text in '$env_file'."
    warning "Ensure this file is ignored by git and stored securely."
    echo

    log "Checking environment variables for ${stack} stack..."

    local -a collected_vars=()
    local -a collected_values=()
    local var value current env_override

    for var in "${required_vars[@]}"; do
        current=$(resolve_existing_env_value "$var" "$env_file")
        resolve_secret_value "$var" "$current" "$env_file" >/dev/null
        value="$RESOLVED_SECRET_VALUE"
        collected_vars+=("$var")
        collected_values+=("$value")
    done

    local tmp_file
    tmp_file=$(mktemp -t dopemux-env.XXXXXX)

    {
        echo "# Dopemux installer managed values ($(date -Iseconds))"
        local idx
        for idx in "${!collected_vars[@]}"; do
            if [ -n "${collected_values[$idx]}" ]; then
                echo "${collected_vars[$idx]}=${collected_values[$idx]}"
            fi
        done
        if [ -f "$env_file" ]; then
            while IFS= read -r line || [ -n "$line" ]; do
                [[ -z "$line" ]] && continue
                [[ "$line" == \#* ]] && continue
                local key="${line%%=*}"
                local skip="false"
                for var in "${collected_vars[@]}"; do
                    if [ "$key" = "$var" ]; then
                        skip="true"
                        break
                    fi
                done
                if [ "$skip" = "false" ]; then
                    echo "$line"
                fi
            done < "$env_file"
        fi
    } > "$tmp_file"
    mv "$tmp_file" "$env_file"
    chmod 600 "$env_file"

    success "Environment variables saved to $env_file"
    show_capability_summary
}

# --- Pre-flight Hardware Validation ---
check_system_resources() {
    local stack="${1:-$SELECTED_STACK}"
    log "Validating system resources..."

    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        return 0
    fi

    local ram_gb=0
    local cpu_cores=0

    if [[ "$OSTYPE" == "darwin"* ]]; then
        ram_gb=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
        cpu_cores=$(sysctl -n hw.ncpu)
    else
        ram_gb=$(free -g | awk '/^Mem:/{print $2}')
        cpu_cores=$(nproc)
    fi

    local min_ram=8
    [ "$stack" = "full" ] && min_ram=16

    log "Detected: $ram_gb GB RAM, $cpu_cores CPU cores"

    if [ "$ram_gb" -lt "$min_ram" ]; then
        warning "Low memory detected: ${ram_gb}GB (Recommended: ${min_ram}GB for ${stack} stack)"
        if ! ask_yes_no "Continue anyway? (May lead to system instability)" "n"; then
            fatal "Installation aborted due to low memory"
        fi
    fi

    if [ "$cpu_cores" -lt 4 ]; then
        warning "Low CPU core count: ${cpu_cores} (Recommended: 4+)"
    fi

    success "Resource validation complete"
}

# --- Deterministic Service Readiness ---
wait_for_containers() {
    local stack="${1:-$SELECTED_STACK}"
    local compose_file
    compose_file=$(compose_file_for_stack "$stack")
    local -a compose_env_args=()
    if [ -f "$ENV_FILE" ]; then
        compose_env_args=(--env-file "$ENV_FILE")
    fi

    log "Waiting for services to be healthy..."

    local timeout=120
    local start_time=$(date +%s)
    local ready=false

    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        local total_containers=$(docker compose "${compose_env_args[@]}" $compose_file ps -q | wc -l)
        local healthy_containers=$(docker compose "${compose_env_args[@]}" $compose_file ps | grep -c "healthy")
        local running_containers=$(docker compose "${compose_env_args[@]}" $compose_file ps | grep -c "Up")

        if [ "$healthy_containers" -eq "$total_containers" ] && [ "$total_containers" -gt 0 ]; then
            ready=true
            break
        fi

        # Fallback for services without healthchecks
        if [ "$running_containers" -eq "$total_containers" ] && [ "$total_containers" -gt 0 ] && [ "$healthy_containers" -eq 0 ]; then
             # Give them a bit more time if no healthchecks are defined
             sleep 10
             ready=true
             break
        fi

        printf "."
        sleep 5
    done

    echo
    if [ "$ready" = true ]; then
        success "All services are ready!"
    else
        warning "Some services are still starting up. Check 'docker compose ps' for status."
    fi
}

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percent=$((current * 100 / total))
    local filled=$((width * current / total))
    
    printf "\r["
    printf "%${filled}s" | tr ' ' '█'
    printf "%$((width - filled))s" | tr ' ' '░'
    printf "] %3d%%" "$percent"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [ "$AUTO_CONFIRM" = true ]; then
        echo "y"
        return 0
    fi
    
    local yn
    while true; do
        if [ "$default" = "y" ]; then
            if ! read -p "$(echo -e "${CYAN}?${NC} $prompt [Y/n]: ")" yn; then
                echo >&2 "EOF encountered"
                return 1
            fi
        else
            if ! read -p "$(echo -e "${CYAN}?${NC} $prompt [y/N]: ")" yn; then
                echo >&2 "EOF encountered"
                return 1
            fi
        fi
        
        yn=${yn:-$default}
        case $yn in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

# ============================================================================
# Platform Detection
# ============================================================================

detect_platform() {
    debug "Detecting platform..."
    
    OS="unknown"
    DISTRO="unknown"
    ARCH="$(uname -m)"
    PACKAGE_MANAGER="unknown"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
        PACKAGE_MANAGER="brew"
        
        # Detect Apple Silicon vs Intel
        if [ "$ARCH" = "arm64" ]; then
            success "Detected: macOS (Apple Silicon)"
        else
            success "Detected: macOS (Intel)"
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        
        # Detect WSL2
        if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
            DISTRO="wsl2"
            success "Detected: WSL2 (Windows Subsystem for Linux)"
        else
            # Detect Linux distribution
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO="${ID}"
                
                case "$DISTRO" in
                    ubuntu|debian)
                        PACKAGE_MANAGER="apt"
                        success "Detected: $PRETTY_NAME"
                        ;;
                    fedora|rhel|centos)
                        PACKAGE_MANAGER="dnf"
                        success "Detected: $PRETTY_NAME"
                        ;;
                    arch|manjaro)
                        PACKAGE_MANAGER="pacman"
                        success "Detected: $PRETTY_NAME"
                        ;;
                    *)
                        warning "Unknown distribution: $DISTRO"
                        PACKAGE_MANAGER="unknown"
                        ;;
                esac
            else
                warning "Cannot detect Linux distribution"
            fi
        fi
    else
        fatal "Unsupported operating system: $OSTYPE"
    fi
    
    export OS DISTRO ARCH PACKAGE_MANAGER
}

# ============================================================================
# Dependency Checking
# ============================================================================

check_command() {
    local cmd="$1"
    command -v "$cmd" &> /dev/null
}

version_gte() {
    # Compare versions: return 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

check_python() {
    log "Checking Python..."
    
    if ! check_command python3; then
        error "Python 3 not found"
        return 1
    fi
    
    local py_version
    py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    
    if ! version_gte "$py_version" "$REQUIRED_PYTHON_VERSION"; then
        error "Python $REQUIRED_PYTHON_VERSION+ required (found: $py_version)"
        return 1
    fi
    
    success "Python $py_version"
    return 0
}

check_git() {
    log "Checking Git..."
    
    if ! check_command git; then
        error "Git not found"
        return 1
    fi
    
    local git_version
    git_version=$(git --version | awk '{print $3}')
    
    if ! version_gte "$git_version" "$REQUIRED_GIT_VERSION"; then
        warning "Git $REQUIRED_GIT_VERSION+ recommended (found: $git_version)"
    fi
    
    success "Git $git_version"
    return 0
}

check_docker() {
    log "Checking Docker..."

    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping Docker checks"
        return 0
    fi
    
    if ! check_command docker; then
        error "Docker not found"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        error "Please start Docker Desktop (macOS) or dockerd (Linux)"
        return 1
    fi
    
    local docker_version
    docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    
    if ! version_gte "$docker_version" "$REQUIRED_DOCKER_VERSION"; then
        warning "Docker $REQUIRED_DOCKER_VERSION+ recommended (found: $docker_version)"
    fi
    
    success "Docker $docker_version"
    return 0
}

check_optional_tools() {
    log "Checking optional tools..."
    
    local tools=("tmux" "jq" "curl" "sqlite3")
    local missing=()
    
    for tool in "${tools[@]}"; do
        if check_command "$tool"; then
            success "$tool installed"
        else
            warning "$tool not installed (optional but recommended)"
            missing+=("$tool")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo
        warning "Missing optional tools: ${missing[*]}"
        warning "Some features may be limited"
    fi
}

# ============================================================================
# Auto-Installation of Dependencies
# ============================================================================

install_dependencies() {
    log "Installing missing dependencies..."
    
    case "$PACKAGE_MANAGER" in
        brew)
            install_with_brew
            ;;
        apt)
            install_with_apt
            ;;
        dnf)
            install_with_dnf
            ;;
        pacman)
            install_with_pacman
            ;;
        *)
            warning "Unknown package manager. Please install dependencies manually:"
            echo "  - Python 3.11+"
            echo "  - Git 2.30+"
            echo "  - Docker 20.10+"
            echo "  - tmux, jq, curl, sqlite3 (optional)"
            return 1
            ;;
    esac
}

install_with_brew() {
    log "Using Homebrew to install dependencies..."
    
    # Check if Homebrew is installed
    if ! check_command brew; then
        if ask_yes_no "Homebrew not found. Install it now?" "y"; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        else
            fatal "Homebrew required for automatic installation on macOS"
        fi
    fi
    
    local packages=()
    
    check_python || packages+=("python@3.11")
    check_git || packages+=("git")
    check_command tmux || packages+=("tmux")
    check_command jq || packages+=("jq")
    check_command sqlite3 || packages+=("sqlite")
    
    if [ ${#packages[@]} -gt 0 ]; then
        log "Installing: ${packages[*]}"
        brew install "${packages[@]}"
    fi
    
    # Docker Desktop requires manual installation on macOS
    if ! check_docker; then
        warning "Docker Desktop not found"
        warning "Please install from: https://www.docker.com/products/docker-desktop"
        
        if ask_yes_no "Open Docker Desktop download page?" "y"; then
            open "https://www.docker.com/products/docker-desktop"
        fi
        
        fatal "Please install Docker Desktop and retry"
    fi
}

install_with_apt() {
    log "Using apt to install dependencies..."
    
    sudo apt update
    
    local packages=()
    
    check_python || packages+=("python3.11" "python3.11-venv" "python3-pip")
    check_git || packages+=("git")
    check_command tmux || packages+=("tmux")
    check_command jq || packages+=("jq")
    check_command curl || packages+=("curl")
    check_command sqlite3 || packages+=("sqlite3")
    
    if [ ${#packages[@]} -gt 0 ]; then
        log "Installing: ${packages[*]}"
        sudo apt install -y "${packages[@]}"
    fi
    
    # Install Docker if missing
    if ! check_docker; then
        if ask_yes_no "Install Docker?" "y"; then
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker "$USER"
            warning "Docker installed. Please log out and back in, then re-run installer"
            exit 0
        fi
    fi
}

install_with_dnf() {
    log "Using dnf to install dependencies..."
    
    sudo dnf check-update || true
    
    local packages=()
    
    check_python || packages+=("python3.11" "python3-pip")
    check_git || packages+=("git")
    check_command tmux || packages+=("tmux")
    check_command jq || packages+=("jq")
    check_command curl || packages+=("curl")
    check_command sqlite3 || packages+=("sqlite")
    
    if [ ${#packages[@]} -gt 0 ]; then
        log "Installing: ${packages[*]}"
        sudo dnf install -y "${packages[@]}"
    fi
    
    if ! check_docker; then
        if ask_yes_no "Install Docker?" "y"; then
            sudo dnf install -y docker
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker "$USER"
            warning "Docker installed. Please log out and back in, then re-run installer"
            exit 0
        fi
    fi
}

install_with_pacman() {
    log "Using pacman to install dependencies..."
    
    sudo pacman -Sy
    
    local packages=()
    
    check_python || packages+=("python")
    check_git || packages+=("git")
    check_command tmux || packages+=("tmux")
    check_command jq || packages+=("jq")
    check_command curl || packages+=("curl")
    check_command sqlite3 || packages+=("sqlite")
    
    if [ ${#packages[@]} -gt 0 ]; then
        log "Installing: ${packages[*]}"
        sudo pacman -S --noconfirm "${packages[@]}"
    fi
    
    if ! check_docker; then
        if ask_yes_no "Install Docker?" "y"; then
            sudo pacman -S --noconfirm docker
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker "$USER"
            warning "Docker installed. Please log out and back in, then re-run installer"
            exit 0
        fi
    fi
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

preflight_checks() {
    local stack="${1:-core}"
    
    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping pre-flight checks"
        return 0
    fi

    log "Running pre-flight checks..."
    
    # Check disk space (need at least 10GB free)
    local available_space
    available_space=$(df -k "$HOME" | awk 'NR==2 {print $4}') # Get KB
    local available_gb=$((available_space / 1024 / 1024))
    
    if [ "$available_gb" -lt 10 ]; then
        warning "Low disk space: ${available_gb}GB available"
        warning "Dopemux requires at least 10GB free space"
        
        if ! ask_yes_no "Continue anyway?" "n"; then
            fatal "Insufficient disk space"
        fi
    else
        success "Disk space: ${available_gb}GB available"
    fi
    
    # Check port availability
    local -a ports=("${CORE_STACK_PORTS[@]}")
    if [ "$stack" = "full" ]; then
        ports+=("${FULL_STACK_EXTRA_PORTS[@]}")
    elif [ "$stack" = "research" ]; then
        ports+=("${RESEARCH_STACK_EXTRA_PORTS[@]}")
    fi
    local busy_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -i ":$port" &> /dev/null || netstat -an 2>/dev/null | grep -q ":$port "; then
            busy_ports+=("$port")
        fi
    done
    
    if [ ${#busy_ports[@]} -gt 0 ]; then
        warning "Ports in use: ${busy_ports[*]}"
        warning "These ports are needed for Dopemux services"
        
        if ! ask_yes_no "Continue? (services may fail to start)" "n"; then
            fatal "Port conflicts detected"
        fi
    else
        success "Required ports available"
    fi
    
    # Check write permissions
    if [ ! -w "$HOME" ]; then
        fatal "Cannot write to $HOME directory"
    fi
    success "Write permissions OK"
}

# ============================================================================
# Main Installation Functions
# ============================================================================

create_directory_structure() {
    log "Creating directory structure..."
    
    mkdir -p "$DOPEMUX_HOME"/{config,data,cache,logs,backups,workspaces}
    mkdir -p "$DOPEMUX_HOME"/config/{profiles,mcp-servers}
    
    success "Created $DOPEMUX_HOME"
}

install_dopemux_core() {
    log "Installing Dopemux core..."

    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping Python package install"
    else
        # Install Python package
        if [ -f "pyproject.toml" ]; then
            log "Creating virtual environment at $DOPEMUX_HOME/venv..."
            python3 -m venv "$DOPEMUX_HOME/venv" || fatal "Failed to create virtual environment"

            log "Installing package into virtual environment..."
            "$DOPEMUX_HOME/venv/bin/pip" install -e . || fatal "Failed to install Python package"
            success "Python package installed"
        else
            warning "pyproject.toml not found, skipping Python package install"
        fi
    fi

    # Copy configuration files
    if [ -d "config" ]; then
        cp -r config/* "$DOPEMUX_HOME/config/" 2>/dev/null || true
        success "Configuration files copied"
    fi
}

install_docker_services() {
    local stack="${1:-$SELECTED_STACK}"
    local compose_file
    compose_file=$(compose_file_for_stack "$stack")
    local -a compose_env_args=()
    if [ -f "$ENV_FILE" ]; then
        compose_env_args=(--env-file "$ENV_FILE")
    fi

    # Validate resources before starting containers
    check_system_resources "$stack"

    log "Setting up Docker services for ${stack} stack..."
    
    if [ ! -f "compose.yml" ]; then
        fatal "Canonical compose file not found"
    fi

    ensure_env_file "$stack"
    ensure_docker_networks "$stack"

    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping docker compose pull/up"
        SELECTED_COMPOSE_FILE="$compose_file"
        return 0
    fi
    
    local profile_arg=""
    if [ "$stack" = "full" ]; then
        profile_arg="--profile full"
    fi

    log "Pulling Docker images from $compose_file (this may take a few minutes)..."
    docker compose "${compose_env_args[@]}" $profile_arg $compose_file pull &
    spinner $!
    success "Docker images pulled"
    
    log "Starting Docker services..."
    docker compose "${compose_env_args[@]}" $profile_arg $compose_file up -d || fatal "Failed to start Docker services"
    
    # Wait for services to be ready
    wait_for_containers "$stack"

    if [ "$stack" = "full" ]; then
        log "Running project management setup (Leantime)..."
        "$DOPEMUX_HOME/venv/bin/python" installers/leantime/install.py -u || warning "PM setup script encountered an issue"
    fi

    SELECTED_COMPOSE_FILE="$compose_file"
    success "Docker services started (${stack} stack)"
}

configure_shell_integration() {
    log "Configuring shell integration..."
    
    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping shell configuration"
        return 0
    fi
    
    local shell_rc
    case "$SHELL" in
        */zsh)
            shell_rc="$HOME/.zshrc"
            ;;
        */bash)
            shell_rc="$HOME/.bashrc"
            ;;
        *)
            warning "Unknown shell: $SHELL"
            return 0
            ;;
    esac
    
    # Use the virtual environment bin directory
    local python_user_bin="$DOPEMUX_HOME/venv/bin"
    
    # Add dopemux to PATH if not already there
    if ! grep -q "dopemux" "$shell_rc" 2>/dev/null; then
        cat >> "$shell_rc" << EOF

# Dopemux
export PATH="$python_user_bin:\$HOME/.local/bin:\$PATH"
export DOPEMUX_HOME="\$HOME/.dopemux"
alias dopemux="\"\$DOPEMUX_HOME/venv/bin/python\" -m dopemux.cli"

# Multi-Workspace Support
export DEFAULT_WORKSPACE_PATH="\$PWD"  # Set to your main project
# export WORKSPACE_PATHS="~/code/project1,~/code/project2"  # Optional: additional workspaces
export ENABLE_WORKSPACE_ISOLATION=true
export ENABLE_CROSS_WORKSPACE_QUERIES=true
EOF
        success "Shell integration added to $shell_rc"
        success "Python bin directory added to PATH: $python_user_bin"
        warning "Run 'source $shell_rc' or restart your terminal to activate"
    else
        success "Shell integration already configured"
    fi
    
    # Prompt user to set default workspace
    log ""
    log "${BOLD}Multi-Workspace Configuration${NC}"
    log "Dopemux can now track multiple projects separately."
    log "Current directory will be set as DEFAULT_WORKSPACE_PATH: $PWD"
    
    if ask_yes_no "Is this your main workspace?" "y"; then
        # Already set to $PWD above
        success "Default workspace: $PWD"
    else
        read -p "Enter your main workspace path: " custom_workspace
        if [ -d "$custom_workspace" ]; then
            sed -i.bak "s|export DEFAULT_WORKSPACE_PATH=.*|export DEFAULT_WORKSPACE_PATH=\"$custom_workspace\"|" "$shell_rc"
            success "Default workspace: $custom_workspace"
        else
            warning "Directory not found, keeping: $PWD"
        fi
    fi
}

verify_installation() {
    log "Verifying installation..."

    if [ "$INSTALLER_TEST_MODE" = "1" ]; then
        warning "[test-mode] Skipping verification (assumed success)"
        return 0
    fi
    
    local checks_passed=0
    local checks_total=5
    local stack="${1:-$SELECTED_STACK}"
    
    # Check 1: Directory structure
    if [ -d "$DOPEMUX_HOME" ]; then
        success "Directory structure OK"
        ((checks_passed++))
    else
        error "Directory structure missing"
    fi
    
    # Check 2: Python package
    if python3 -c "import dopemux" 2>/dev/null; then
        success "Python package OK"
        ((checks_passed++))
    else
        warning "Python package not importable"
    fi

    # Check 3: Docker services
    local docker_ok=false
    local compose_args
    compose_args=$(compose_file_for_stack "$stack")
    local -a compose_env_args=()
    if [ -f "$ENV_FILE" ]; then
        compose_env_args=(--env-file "$ENV_FILE")
    fi

    local profile_arg=""
    [ "$stack" = "full" ] && profile_arg="--profile full"

    if docker compose "${compose_env_args[@]}" $profile_arg $compose_args ps >/dev/null 2>&1 && docker compose "${compose_env_args[@]}" $profile_arg $compose_args ps | grep -q "Up"; then
        success "Docker services OK"
        docker_ok=true
        ((checks_passed++))
    else
        warning "Docker services not running or unhealthy"
    fi

    if [ "$docker_ok" = false ]; then
        warning "Docker services not running"
    fi
    
    # Check 4: Configuration files
    if [ -f "$DOPEMUX_HOME/config/profiles/default.yaml" ]; then
        success "Configuration files OK"
        ((checks_passed++))
    else
        warning "Configuration files missing"
    fi
    
    # Check 5: Shell integration
    if grep -q "dopemux" "$HOME/.zshrc" 2>/dev/null || grep -q "dopemux" "$HOME/.bashrc" 2>/dev/null; then
        success "Shell integration OK"
        ((checks_passed++))
    else
        warning "Shell integration not configured"
    fi
    
    echo
    progress_bar "$checks_passed" "$checks_total"
    echo
    
    if [ "$checks_passed" -eq "$checks_total" ]; then
        success "All checks passed! ($checks_passed/$checks_total)"
        return 0
    elif [ "$checks_passed" -ge 3 ]; then
        warning "Installation incomplete ($checks_passed/$checks_total checks passed)"
        warning "Some features may not work correctly"
        return 0
    else
        error "Installation verification failed ($checks_passed/$checks_total checks passed)"
        return 1
    fi
}

# ============================================================================
# Installation Modes
# ============================================================================

interactive_install() {
    echo -e "${BOLD}${CYAN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║       🚀 Dopemux Interactive Installation                         ║
║                                                                   ║
║   ADHD-Optimized Development Platform                            ║
║   Making development workflows easier, one session at a time     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo "This installer will:"
    echo "  1. Detect your platform and check dependencies"
    echo "  2. Install missing dependencies (with your approval)"
    echo "  3. Set up Dopemux directory structure"
    echo "  4. Install Docker services (ConPort, ADHD Engine, etc.)"
    echo "  5. Configure shell integration"
    echo "  6. Verify the installation"
    echo
    
    if ! ask_yes_no "Ready to begin?" "y"; then
        log "Installation cancelled"
        exit 0
    fi
    
    echo
    detect_platform
    echo
    
    # Check dependencies
    local deps_missing=false
    check_python || deps_missing=true
    check_git || deps_missing=true
    check_docker || deps_missing=true
    check_optional_tools
    echo
    
    # Install missing dependencies if needed
    if [ "$deps_missing" = true ]; then
        if ask_yes_no "Install missing dependencies automatically?" "y"; then
            install_dependencies
            echo
        else
            fatal "Required dependencies missing. Please install manually and retry."
        fi
    fi

    choose_install_stack
    
    # Pre-flight checks
    preflight_checks "$SELECTED_STACK"
    echo
    
    # Main installation
    create_directory_structure
    install_dopemux_core
    install_docker_services "$SELECTED_STACK"
    configure_shell_integration
    echo

    # Verify
    verify_installation
    echo
    
    # Soft Landing UX
    echo
    echo -e "${BOLD}${CYAN}┌───────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}${CYAN}│                                                                   │${NC}"
    echo -e "${BOLD}${CYAN}│   ${GREEN}✅ Dopemux Setup Complete!${CYAN}                                      │${NC}"
    echo -e "${BOLD}${CYAN}│                                                                   │${NC}"
    echo -e "${BOLD}${CYAN}└───────────────────────────────────────────────────────────────────┘${NC}"
    echo
    echo -e "${BOLD}NEXT STEP:${NC}"
    echo -e "${MAGENTA}  source ~/.zshrc && dopemux dashboard${NC}"
    echo
    echo -e "${CYAN}Where to go from here:${NC}"
    echo "  • Run 'dopemux --help' to see all commands"
    echo "  • Visit https://docs.dopemux.dev for guides"
    echo "  • Stay focused. You've got this. 🧠⚡"
    echo
}

quick_install() {
    log "Quick installation mode (core services only)..."
    AUTO_CONFIRM=true
    SELECTED_STACK="core"

    detect_platform
    check_python || fatal "Python 3.11+ required"
    check_git || fatal "Git required"
    check_docker || fatal "Docker required"
    check_optional_tools

    preflight_checks "$SELECTED_STACK"
    create_directory_structure
    install_dopemux_core
    install_docker_services "$SELECTED_STACK"
    configure_shell_integration
    verify_installation
    
    # Soft Landing UX
    echo
    echo -e "${BOLD}${CYAN}┌───────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}${CYAN}│                                                                   │${NC}"
    echo -e "${BOLD}${CYAN}│   ${GREEN}✅ Dopemux (Core) Setup Complete!${CYAN}                               │${NC}"
    echo -e "${BOLD}${CYAN}│                                                                   │${NC}"
    echo -e "${BOLD}${CYAN}└───────────────────────────────────────────────────────────────────┘${NC}"
    echo
    echo -e "${BOLD}NEXT STEP:${NC}"
    echo -e "${MAGENTA}  source ~/.zshrc && dopemux start${NC}"
    echo
}

full_install() {
    log "Full installation mode (all features)..."
    
    AUTO_CONFIRM=true
    SELECTED_STACK="full"
    interactive_install
}

# ============================================================================
# Terminal Environment Setup
# ============================================================================


# ============================================================================
# Uninstall
# ============================================================================

uninstall_dopemux() {
    warning "This will remove Dopemux from your system"
    
    if ! ask_yes_no "Are you sure?" "n"; then
        log "Uninstall cancelled"
        exit 0
    fi
    
    # Backup data before uninstalling
    if [ -d "$DOPEMUX_HOME" ]; then
        log "Creating backup at $BACKUP_DIR..."
        cp -r "$DOPEMUX_HOME" "$BACKUP_DIR"
        success "Backup created"
    fi
    
    # Stop Docker services
    if [ -f "compose.yml" ]; then
        log "Stopping current stack..."
        docker compose --profile full -f compose.yml down -v 2>/dev/null || true
    fi
    
    # Remove directories
    log "Removing Dopemux files..."
    rm -rf "$DOPEMUX_HOME"
    
    # Remove from PATH (best effort)
    for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
        if [ -f "$rc" ]; then
            # Remove dopemux lines
            sed -i.bak '/# Dopemux/,+3d' "$rc" 2>/dev/null || true
        fi
    done
    
    success "Dopemux uninstalled"
    log "Backup saved at: $BACKUP_DIR"
}

# ============================================================================
# Main Entry Point
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                INSTALL_MODE="quick"
                shift
                ;;
            --full)
                INSTALL_MODE="full"
                shift
                ;;
            --verify)
                INSTALL_MODE="verify"
                shift
                ;;
            --uninstall)
                INSTALL_MODE="uninstall"
                shift
                ;;
            --stack)
                if [ $# -lt 2 ]; then
                    fatal "--stack requires an argument (core|research|full)"
                fi
                case "$2" in
                    core|research|full)
                        SELECTED_STACK="$2"
                        STACK_SELECTED_FROM_FLAG=true
                        ;;
                    *)
                        fatal "Invalid stack '$2'. Expected 'core', 'research', or 'full'"
                        ;;
                esac
                shift 2
                ;;
            --env-file)
                if [ $# -lt 2 ]; then
                    fatal "--env-file requires a path argument"
                fi
                ENV_FILE="$2"
                shift 2
                ;;
            --yes|-y)
                AUTO_CONFIRM=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                cat << EOF
Dopemux Universal Installer v$VERSION

Usage: $0 [OPTIONS]

OPTIONS:
    --quick         Quick installation (core services only)
    --full          Full installation (all features, no prompts)
    --stack <mode>  Force stack selection (core|research|full)
    --verify        Verify existing installation
    --uninstall     Remove Dopemux from system
    --env-file PATH Write/read env vars from PATH instead of .env
    -y, --yes       Auto-confirm all prompts
    -v, --verbose   Verbose output
    -h, --help      Show this help message

EXAMPLES:
    $0                      # Interactive installation
    $0 --quick              # Quick install
    $0 --full --yes         # Full install, no prompts
    $0 --verify             # Check installation health
    $0 --uninstall          # Remove Dopemux

For more information: https://docs.dopemux.dev/installation
EOF
                exit 0
                ;;
            *)
                warning "Unknown option: $1"
                shift
                ;;
        esac
    done
}

main() {
    parse_args "$@"
    
    case "$INSTALL_MODE" in
        interactive)
            interactive_install
            ;;
        quick)
            quick_install
            ;;
        full)
            full_install
            ;;
        verify)
            detect_platform
            verify_installation
            ;;
        uninstall)
            uninstall_dopemux
            ;;
    esac
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
