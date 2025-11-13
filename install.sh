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

# ============================================================================
# Configuration & Constants
# ============================================================================

VERSION="1.0.0"
DOPEMUX_HOME="${DOPEMUX_HOME:-$HOME/.dopemux}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
BACKUP_DIR="$HOME/.dopemux.backup.$(date +%Y%m%d_%H%M%S)"

# Required versions
REQUIRED_PYTHON_VERSION="3.10"
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
            read -p "$(echo -e "${CYAN}?${NC} $prompt [Y/n]: ")" yn
        else
            read -p "$(echo -e "${CYAN}?${NC} $prompt [y/N]: ")" yn
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
            echo "  - Python 3.10+"
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
    log "Running pre-flight checks..."
    
    # Check disk space (need at least 10GB free)
    local available_space
    available_space=$(df -h "$HOME" | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [ "${available_space%.*}" -lt 10 ]; then
        warning "Low disk space: ${available_space}GB available"
        warning "Dopemux requires at least 10GB free space"
        
        if ! ask_yes_no "Continue anyway?" "n"; then
            fatal "Insufficient disk space"
        fi
    else
        success "Disk space: ${available_space}GB available"
    fi
    
    # Check port availability
    local ports=(5432 6379 6333 8095 3004)
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
    
    # Install Python package
    if [ -f "pyproject.toml" ]; then
        python3 -m pip install --user -e . || fatal "Failed to install Python package"
        success "Python package installed"
    else
        warning "pyproject.toml not found, skipping Python package install"
    fi
    
    # Copy configuration files
    if [ -d "config" ]; then
        cp -r config/* "$DOPEMUX_HOME/config/" 2>/dev/null || true
        success "Configuration files copied"
    fi
}

install_docker_services() {
    log "Setting up Docker services..."
    
    if [ ! -f "docker-compose.unified.yml" ]; then
        warning "docker-compose.unified.yml not found"
        return 1
    fi
    
    # Pull images (with progress)
    log "Pulling Docker images (this may take a few minutes)..."
    docker-compose -f docker-compose.unified.yml pull &
    spinner $!
    
    success "Docker images pulled"
    
    # Start services
    log "Starting Docker services..."
    docker-compose -f docker-compose.unified.yml up -d || fatal "Failed to start Docker services"
    
    # Wait for services to be healthy
    log "Waiting for services to be ready..."
    sleep 10
    
    success "Docker services started"
}

configure_shell_integration() {
    log "Configuring shell integration..."
    
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
    
    # Add dopemux to PATH if not already there
    if ! grep -q "dopemux" "$shell_rc" 2>/dev/null; then
        cat >> "$shell_rc" << 'EOF'

# Dopemux
export PATH="$HOME/.local/bin:$PATH"
export DOPEMUX_HOME="$HOME/.dopemux"
alias dopemux="python3 -m dopemux.cli"
EOF
        success "Shell integration added to $shell_rc"
        warning "Run 'source $shell_rc' or restart your terminal to activate"
    else
        success "Shell integration already configured"
    fi
}

verify_installation() {
    log "Verifying installation..."
    
    local checks_passed=0
    local checks_total=5
    
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
    if docker-compose -f docker-compose.unified.yml ps | grep -q "Up"; then
        success "Docker services OK"
        ((checks_passed++))
    else
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
    
    # Pre-flight checks
    preflight_checks
    echo
    
    # Main installation
    create_directory_structure
    install_dopemux_core
    install_docker_services
    configure_shell_integration
    echo
    
    # Verify
    verify_installation
    echo
    
    # Success message
    echo -e "${BOLD}${GREEN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ✅ Dopemux Installed Successfully!                              ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo "🎉 Next steps:"
    echo
    echo "  1. Restart your terminal (or run: source ~/.zshrc)"
    echo "  2. Run: dopemux init"
    echo "  3. Start coding with ADHD superpowers! 🧠⚡"
    echo
    echo "📚 Documentation: https://docs.dopemux.dev"
    echo "💬 Community: https://discord.gg/dopemux"
    echo "🐛 Issues: https://github.com/dopemux/dopemux-mvp/issues"
    echo
}

quick_install() {
    log "Quick installation mode (core services only)..."
    
    detect_platform
    check_python || fatal "Python 3.10+ required"
    check_git || fatal "Git required"
    check_docker || fatal "Docker required"
    
    create_directory_structure
    install_dopemux_core
    
    success "Quick installation complete!"
    warning "Docker services not started. Run 'dopemux start' when ready."
}

full_install() {
    log "Full installation mode (all features)..."
    
    AUTO_CONFIRM=true
    interactive_install
}

# ============================================================================
# Terminal Environment Setup
# ============================================================================

setup_terminal_environment() {
    log "Setting up ADHD-optimized terminal environment..."
    
    # Check if terminal setup script exists
    local script_path="${SCRIPT_DIR}/scripts/setup-terminal-env.sh"
    
    if [[ ! -f "$script_path" ]]; then
        error "Terminal setup script not found: $script_path"
        log "Please run this from the dopemux-mvp directory"
        exit 1
    fi
    
    # Run the terminal setup script
    chmod +x "$script_path"
    exec "$script_path"
}

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
    if [ -f "docker-compose.unified.yml" ]; then
        log "Stopping Docker services..."
        docker-compose -f docker-compose.unified.yml down -v 2>/dev/null || true
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
            --terminal)
                INSTALL_MODE="terminal"
                shift
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
    --terminal      Setup ADHD-optimized terminal environment
    --verify        Verify existing installation
    --uninstall     Remove Dopemux from system
    -y, --yes       Auto-confirm all prompts
    -v, --verbose   Verbose output
    -h, --help      Show this help message

EXAMPLES:
    $0                      # Interactive installation
    $0 --quick              # Quick install
    $0 --full --yes         # Full install, no prompts
    $0 --terminal           # Setup terminal (zsh, kitty, starship)
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
        terminal)
            setup_terminal_environment
            ;;
        uninstall)
            uninstall_dopemux
            ;;
    esac
}

# Run main function
main "$@"
