#!/bin/bash

# Claude Code Platform Evolution Universal Installer
# Installs the distributed multi-agent system globally or locally

set -e

VERSION="1.0.0"
PLATFORM_DIR="$HOME/.claude-platform"
GLOBAL_INSTALL=true
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Claude Code Platform Evolution Installer v${VERSION}

USAGE:
    ./install.sh [OPTIONS]

OPTIONS:
    --local                 Install locally (project-specific)
    --global               Install globally (default)
    --platform-dir DIR     Custom installation directory (default: ~/.claude-platform)
    --verbose              Verbose output
    --help                 Show this help message

EXAMPLES:
    ./install.sh                          # Global installation
    ./install.sh --local                  # Local installation
    ./install.sh --platform-dir ~/my-platform  # Custom directory

The Platform Evolution system provides:
- Context7-first development with mandatory documentation integration
- Multi-agent clusters for specialized development workflows
- Token budget optimization (60-80% reduction)
- Universal compatibility across any project
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --local)
                GLOBAL_INSTALL=false
                PLATFORM_DIR="$(pwd)/.claude-platform"
                shift
                ;;
            --global)
                GLOBAL_INSTALL=true
                shift
                ;;
            --platform-dir)
                PLATFORM_DIR="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for required commands
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again"
        exit 1
    fi
    
    log_success "All dependencies found"
}

create_directory_structure() {
    log_info "Creating directory structure at ${PLATFORM_DIR}..."
    
    # Create main directories
    mkdir -p "${PLATFORM_DIR}"/{src,config,deployment,logs,data}
    mkdir -p "${PLATFORM_DIR}/src"/{core,agents,context7,monitoring}
    mkdir -p "${PLATFORM_DIR}/config"/{templates,defaults,profiles}
    mkdir -p "${PLATFORM_DIR}/deployment"/{docker,scripts}
    
    log_success "Directory structure created"
}

install_core_files() {
    log_info "Installing core Platform Evolution files..."
    
    # Copy source files
    cp -r src/* "${PLATFORM_DIR}/src/" 2>/dev/null || true
    cp -r config/* "${PLATFORM_DIR}/config/" 2>/dev/null || true
    cp -r deployment/* "${PLATFORM_DIR}/deployment/" 2>/dev/null || true
    
    # Create core configuration
    cat > "${PLATFORM_DIR}/config/platform.yaml" << EOF
# Claude Code Platform Evolution Configuration
platform:
  version: "${VERSION}"
  mode: distributed
  context7_enforced: true
  installation_type: $([ "$GLOBAL_INSTALL" = true ] && echo "global" || echo "local")
  installation_path: "${PLATFORM_DIR}"

clusters:
  research:
    token_budget: 20000
    agents: [context7, exa]
    enabled: true
  implementation:
    token_budget: 25000
    agents: [serena, claude-context, taskmaster, sequential-thinking]
    enabled: true
  quality:
    token_budget: 15000
    agents: [zen]
    enabled: true
  coordination:
    token_budget: 10000
    agents: [conport, openmemory, cli]
    enabled: true

monitoring:
  enabled: true
  port: 8080
  metrics_retention: 7d
  log_level: INFO

context7:
  enforced: true
  timeout: 30
  fallback_enabled: false

docker:
  network_name: claude-platform-network
  compose_file: "${PLATFORM_DIR}/deployment/docker/docker-compose.yml"
EOF
    
    log_success "Core files installed"
}

create_cli_tool() {
    log_info "Creating CLI management tool..."
    
    local cli_path
    if [ "$GLOBAL_INSTALL" = true ]; then
        # Use home bin directory instead of /usr/local/bin to avoid sudo
        mkdir -p "$HOME/bin"
        cli_path="$HOME/bin/claude-platform"
    else
        cli_path="${PLATFORM_DIR}/bin/claude-platform"
        mkdir -p "${PLATFORM_DIR}/bin"
    fi
    
    cat > "$cli_path" << 'EOF'
#!/bin/bash

# Claude Code Platform Evolution CLI
# Universal management tool for distributed multi-agent development

PLATFORM_DIR="${HOME}/.claude-platform"
if [ -f ".claude-platform.yaml" ]; then
    # Local installation detected
    PLATFORM_DIR="$(pwd)/.claude-platform"
fi

CONFIG_FILE="${PLATFORM_DIR}/config/platform.yaml"

show_help() {
    cat << HELP
Claude Code Platform Evolution CLI

COMMANDS:
    activate [--profile PROFILE]    Activate platform in current project
    deactivate                      Deactivate platform
    start                          Start distributed agent clusters
    stop                           Stop all agents
    restart                        Restart the platform
    status                         Show platform status
    dashboard                      Open monitoring dashboard
    profile list                   List available profiles
    profile create NAME            Create new profile
    logs [CLUSTER]                 Show agent logs
    config [edit|show]             Manage configuration
    update                         Update platform
    uninstall                      Remove platform

EXAMPLES:
    claude-platform activate               # Activate in current project
    claude-platform start                  # Start distributed agents
    claude-platform status                 # Check platform status
    claude-platform dashboard              # Open monitoring at localhost:8080
    claude-platform profile create react  # Create React-specific profile
    claude-platform logs implementation    # Show implementation cluster logs

For more information, visit: https://github.com/your-org/claude-platform-evolution
HELP
}

activate_platform() {
    local profile="default"
    
    if [[ "$1" == "--profile" && -n "$2" ]]; then
        profile="$2"
    fi
    
    echo "🚀 Activating Claude Code Platform Evolution..."
    echo "Profile: $profile"
    echo "Platform Directory: $PLATFORM_DIR"
    
    # Create project-specific activation marker
    cat > .claude-platform-active << ACTIVE
# Claude Code Platform Evolution Active
platform_dir: ${PLATFORM_DIR}
profile: ${profile}
activated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
project: $(basename "$(pwd)")
ACTIVE
    
    echo "✅ Platform Evolution activated for this project"
    echo "💡 Use 'claude-platform start' to launch distributed agents"
}

start_platform() {
    if [ ! -f ".claude-platform-active" ]; then
        echo "❌ Platform not activated in this project"
        echo "💡 Run 'claude-platform activate' first"
        exit 1
    fi
    
    echo "🚀 Starting Claude Code Platform Evolution..."
    
    # Start Docker containers
    cd "$PLATFORM_DIR/deployment/docker"
    docker-compose up -d
    
    echo "✅ Distributed agent clusters started"
    echo "📊 Monitor at: http://localhost:8080"
}

stop_platform() {
    echo "🛑 Stopping Claude Code Platform Evolution..."
    
    cd "$PLATFORM_DIR/deployment/docker"
    docker-compose down
    
    echo "✅ All agent clusters stopped"
}

show_status() {
    echo "📊 Claude Code Platform Evolution Status"
    echo "========================================"
    
    if [ -f ".claude-platform-active" ]; then
        echo "Project Status: ✅ Active"
        echo "Project: $(basename "$(pwd)")"
        
        # Check if containers are running
        cd "$PLATFORM_DIR/deployment/docker"
        if docker-compose ps | grep -q "Up"; then
            echo "Clusters: ✅ Running"
        else
            echo "Clusters: ❌ Stopped"
        fi
    else
        echo "Project Status: ❌ Not activated"
    fi
    
    echo ""
    echo "Platform Directory: $PLATFORM_DIR"
    echo "Configuration: $CONFIG_FILE"
}

case "$1" in
    activate)
        shift
        activate_platform "$@"
        ;;
    start)
        start_platform
        ;;
    stop)
        stop_platform
        ;;
    status)
        show_status
        ;;
    dashboard)
        echo "📊 Opening monitoring dashboard..."
        if command -v open &> /dev/null; then
            open http://localhost:8080
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:8080
        else
            echo "🌐 Dashboard available at: http://localhost:8080"
        fi
        ;;
    --help|help)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac
EOF
    
    chmod +x "$cli_path"
    
    if [ "$GLOBAL_INSTALL" = true ]; then
        log_success "CLI tool installed globally at $cli_path"
    else
        log_success "CLI tool installed locally at $cli_path"
        log_info "Add ${PLATFORM_DIR}/bin to your PATH to use globally"
    fi
}

create_docker_configs() {
    log_info "Creating Docker configurations..."
    
    mkdir -p "${PLATFORM_DIR}/deployment/docker"
    
    # Create Docker Compose for distributed agents
    cat > "${PLATFORM_DIR}/deployment/docker/docker-compose.yml" << EOF
version: '3.8'

networks:
  claude-platform:
    driver: bridge

services:
  research-agent:
    build:
      context: .
      dockerfile: Dockerfile.research
    container_name: claude-research-cluster
    networks:
      - claude-platform
    environment:
      - CLUSTER_TYPE=research
      - TOKEN_BUDGET=20000
      - CONTEXT7_ENABLED=true
    volumes:
      - ${PLATFORM_DIR}/config:/app/config:ro
      - ${PLATFORM_DIR}/logs:/app/logs
    restart: unless-stopped

  implementation-agent:
    build:
      context: .
      dockerfile: Dockerfile.implementation
    container_name: claude-implementation-cluster
    networks:
      - claude-platform
    environment:
      - CLUSTER_TYPE=implementation
      - TOKEN_BUDGET=25000
      - CONTEXT7_ENABLED=true
    volumes:
      - ${PLATFORM_DIR}/config:/app/config:ro
      - ${PLATFORM_DIR}/logs:/app/logs
    restart: unless-stopped

  quality-agent:
    build:
      context: .
      dockerfile: Dockerfile.quality
    container_name: claude-quality-cluster
    networks:
      - claude-platform
    environment:
      - CLUSTER_TYPE=quality
      - TOKEN_BUDGET=15000
    volumes:
      - ${PLATFORM_DIR}/config:/app/config:ro
      - ${PLATFORM_DIR}/logs:/app/logs
    restart: unless-stopped

  coordination-agent:
    build:
      context: .
      dockerfile: Dockerfile.coordination
    container_name: claude-coordination-cluster
    networks:
      - claude-platform
    environment:
      - CLUSTER_TYPE=coordination
      - TOKEN_BUDGET=10000
    volumes:
      - ${PLATFORM_DIR}/config:/app/config:ro
      - ${PLATFORM_DIR}/logs:/app/logs
    restart: unless-stopped

  monitoring-dashboard:
    build:
      context: .
      dockerfile: Dockerfile.monitoring
    container_name: claude-platform-monitoring
    networks:
      - claude-platform
    ports:
      - "8080:8080"
    environment:
      - MONITORING_ENABLED=true
    volumes:
      - ${PLATFORM_DIR}/config:/app/config:ro
      - ${PLATFORM_DIR}/logs:/app/logs
      - ${PLATFORM_DIR}/data:/app/data
    restart: unless-stopped
EOF
    
    log_success "Docker configurations created"
}

setup_shell_integration() {
    if [ "$GLOBAL_INSTALL" = true ]; then
        log_info "Setting up shell integration..."
        
        # Add to bash profile if exists
        if [ -f "$HOME/.bashrc" ]; then
            if ! grep -q "claude-platform" "$HOME/.bashrc"; then
                echo "" >> "$HOME/.bashrc"
                echo "# Claude Code Platform Evolution" >> "$HOME/.bashrc"
                echo "export CLAUDE_PLATFORM_HOME=\"${PLATFORM_DIR}\"" >> "$HOME/.bashrc"
            fi
        fi
        
        # Add to zsh profile if exists
        if [ -f "$HOME/.zshrc" ]; then
            if ! grep -q "claude-platform" "$HOME/.zshrc"; then
                echo "" >> "$HOME/.zshrc"
                echo "# Claude Code Platform Evolution" >> "$HOME/.zshrc"
                echo "export CLAUDE_PLATFORM_HOME=\"${PLATFORM_DIR}\"" >> "$HOME/.zshrc"
            fi
        fi
        
        log_success "Shell integration configured"
    fi
}

main() {
    echo ""
    echo "🚀 Claude Code Platform Evolution Installer v${VERSION}"
    echo "================================================"
    echo ""
    
    parse_args "$@"
    
    if [ "$GLOBAL_INSTALL" = true ]; then
        log_info "Installing globally at ${PLATFORM_DIR}"
    else
        log_info "Installing locally at ${PLATFORM_DIR}"
    fi
    
    check_dependencies
    create_directory_structure
    install_core_files
    create_cli_tool
    create_docker_configs
    setup_shell_integration
    
    echo ""
    log_success "🎉 Platform Evolution installation complete!"
    echo ""
    echo "Next steps:"
    echo "1. Navigate to any project: cd /path/to/your/project"
    echo "2. Activate platform: claude-platform activate"
    echo "3. Start agents: claude-platform start"
    echo "4. Use Claude Code as normal - now with distributed agents!"
    echo ""
    echo "Monitor your platform at: http://localhost:8080"
    echo "Documentation: https://github.com/your-org/claude-platform-evolution"
    echo ""
}

main "$@"