#!/bin/bash
#
# Dopemux Installer - ADHD-Optimized Development Platform
#
# This script provides automated installation and setup of Dopemux.
# It handles prerequisites, Docker services, MCP servers, and configuration.
#
# Usage:
#   ./install.sh              # Interactive installation
#   ./install.sh --quick      # Quick setup (minimal services)
#   ./install.sh --full       # Full installation (all services)
#   ./install.sh --verify     # Verify current installation
#   ./install.sh --help       # Show this help

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"
LOG_FILE="$PROJECT_ROOT/install.log"
ERROR_LOG="$PROJECT_ROOT/install-errors.log"
DIAGNOSTICS_DIR="$PROJECT_ROOT/diagnostics"

# Installation modes
QUICK_MODE=false
FULL_MODE=false
VERIFY_MODE=false
SKIP_CONFIRM=false
DEBUG_MODE=false
NO_DOCKER_MODE=false

# Error codes for better troubleshooting
ERROR_NO_DOCKER=10
ERROR_DOCKER_NOT_RUNNING=11
ERROR_NO_PACKAGE_MANAGER=12
ERROR_SERVICE_START_FAIL=13
ERROR_CONFIG_BACKUP_FAIL=14
ERROR_NETWORK_FAIL=15
ERROR_DISK_SPACE_LOW=16
ERROR_PERMISSION_DENIED=17

# Enhanced error handling with user-friendly messages
handle_error() {
    local error_code=$1
    local error_message=$2
    local suggestion=$3

    echo -e "${RED}❌ INSTALLATION ERROR (Code: $error_code)${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo -e "${RED}$error_message${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"

    if [[ -n "$suggestion" ]]; then
        echo -e "${YELLOW}💡 Suggested Fix:${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        echo -e "${CYAN}$suggestion${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        echo "" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    fi

    echo -e "${YELLOW}📖 For more help:${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Check install.log for full details" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Run './install.sh --diagnose' for system analysis" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Run './install.sh --troubleshoot' for common solutions" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Visit INSTALL.md for detailed documentation" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"

    exit $error_code
}

# Comprehensive help system
show_comprehensive_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║          📖 Dopemux Installer - Comprehensive Help          ║
╚══════════════════════════════════════════════════════════════╝

🎯 QUICK START
  ./install.sh                    # Interactive installation
  ./install.sh --quick           # Fast setup (core services)
  ./install.sh --full            # Complete setup (everything)
  ./install.sh --verify          # Check existing installation

📋 INSTALLATION MODES

  Interactive Mode (Default)
    • Prompts for confirmation and mode selection
    • Shows detailed progress with actionable next steps
    • Creates backups of existing configurations
    • Provides recovery options on failures

  Quick Mode (--quick)
    • Core services only (PostgreSQL, Redis, Qdrant, ConPort, ADHD Engine)
    • Minimal CLI tools installation
    • Faster setup (~3-5 minutes)
    • Recommended for first-time users

  Full Mode (--full)
    • Everything: all MCP servers, advanced CLI tools, IDE integration
    • Comprehensive configuration and optimization
    • Takes longer (~10-15 minutes)
    • Recommended for power users

🔧 WHAT GETS INSTALLED

  Infrastructure Services
    • PostgreSQL 16 with AGE extension (graph database)
    • Redis 7 (caching and event streaming)
    • Qdrant (vector database for semantic search)

  Dopemux Core Services
    • ADHD Engine (real-time cognitive accommodations)
    • ConPort (knowledge graphs and persistent memory)
    • Task Orchestrator (ADHD-aware task coordination)
    • Dope-Context (semantic code and documentation search)

  CLI Tools & Terminal Enhancement
    • tmux (multi-pane session management)
    • zsh + Oh My Zsh (advanced shell with plugins)
    • Kitty (GPU-accelerated terminal)
    • Starship (customizable shell prompt)
    • fzf, ripgrep, bat, exa, zoxide, tldr (productivity tools)

  Development Integrations
    • Claude Code Router (multi-instance management)
    • Statusline integration (real-time metrics)
    • IDE integrations (VS Code, Vim)
    • Git hooks and workflow automation

🩺 DIAGNOSTICS & TROUBLESHOOTING

  Before Installation
    ./install.sh --diagnose        # System compatibility check
    ./install.sh --troubleshoot    # Common issues and solutions

  During Installation
    • Check install.log for detailed progress
    • Check install-errors.log for specific failures
    • Use Ctrl+C to gracefully abort (cleanup performed)

  After Installation
    • ./install.sh --verify to check everything works
    • dopemux doctor for system health
    • dopemux status for real-time status

🔍 COMMON ISSUES & SOLUTIONS

  Docker Issues
    "Docker daemon not running"
      → macOS: Launch Docker Desktop from Applications
      → Linux: sudo systemctl start docker

    "Permission denied"
      → Linux: sudo usermod -aG docker $USER && newgrp docker
      → macOS: Check Docker Desktop settings

    "Port already in use"
      → Find conflicting service: lsof -i :5432
      → Stop conflicting service or change ports

  Network Issues
    "Cannot pull images"
      → Check internet: ping 8.8.8.8
      → Try different DNS: echo "8.8.8.8" > /etc/resolv.conf
      → Use VPN if in restricted network

  Disk Space Issues
    "Not enough space"
      → Clean Docker: docker system prune -a
      → Check usage: df -h
      → Minimum: 10GB free space required

  Permission Issues
    "Cannot write to ~/.config"
      → Fix ownership: chown -R $USER:$USER ~/.config

📊 ERROR CODES

  10 - ERROR_NO_DOCKER           Docker not installed
  11 - ERROR_DOCKER_NOT_RUNNING  Docker daemon not running
  12 - ERROR_NO_PACKAGE_MANAGER  No supported package manager
  13 - ERROR_SERVICE_START_FAIL  Docker services failed to start
  14 - ERROR_CONFIG_BACKUP_FAIL  Configuration backup failed
  15 - ERROR_NETWORK_FAIL        Network connectivity issues
  16 - ERROR_DISK_SPACE_LOW      Insufficient disk space
  17 - ERROR_PERMISSION_DENIED   Permission denied for file operations

🆘 GETTING HELP

  1. Check the logs
     • install.log (full installation log)
     • install-errors.log (specific errors only)

  2. Run diagnostics
     ./install.sh --diagnose

  3. Check common solutions
     ./install.sh --troubleshoot

  4. Search documentation
     • INSTALL.md for detailed setup guide
     • README.md for feature overview
     • docs/ for troubleshooting guides

  5. Get community help
     • GitHub Issues (bug reports)
     • GitHub Discussions (questions)
     • Discord/Slack (real-time help)

⚙️ ADVANCED OPTIONS

  --yes       Skip all confirmation prompts
  --debug     Enable debug mode with verbose logging
  --no-docker Skip Docker services (install CLI tools only, for containerized environments)
  --diagnose  Run system compatibility diagnostics
  --help      Show this comprehensive help

📋 SYSTEM REQUIREMENTS

  Minimum Hardware
    • CPU: 2 cores (4+ recommended)
    • RAM: 4GB (8GB+ recommended)
    • Disk: 10GB free space (20GB+ recommended)
    • Network: Stable internet for downloads

  Supported Operating Systems
    • macOS 12.0+ (Monterey or later)
    • Ubuntu 20.04+ / Debian 11+
    • CentOS 8+ / RHEL 8+ / Fedora 34+
    • Arch Linux (current)
    • Other Linux distributions with apt/dnf/pacman

  Software Prerequisites
    • Docker 20.10+ with Docker Compose (auto-detected)
    • curl (for downloads, auto-installed if missing)
    • git (for cloning, auto-installed if missing)
    • bash or zsh shell (zsh auto-installed and set as default)

  Package Managers (Auto-Detected)
    • macOS: Homebrew (brew)
    • Ubuntu/Debian: apt
    • Fedora/RHEL: dnf/yum
    • Arch Linux: pacman

🚀 POST-INSTALLATION

  After successful installation:

  1. Set up API keys (see INSTALL.md for detailed guide)
     • Anthropic Claude (primary AI model)
     • OpenRouter (cost-effective fallbacks)
     • Voyage AI (semantic search)

  2. Start your development session
     dopemux start

  3. Verify everything works
     dopemux doctor

  4. Check the statusline in Claude Code
     (shows real-time ADHD metrics and energy levels)

  Your terminal environment is now optimized for ADHD-friendly development! 🎉
EOF
}

# System diagnostics
run_diagnostics() {
    echo -e "${CYAN}🔧 Dopemux System Diagnostics${NC}"
    echo "==============================="
    echo ""

    # Create diagnostics directory
    mkdir -p "$DIAGNOSTICS_DIR"

    # System information
    echo -e "${BLUE}📊 System Information:${NC}"
    echo "OS: $(uname -s) $(uname -r)"
    echo "Architecture: $(uname -m)"
    echo "Shell: $SHELL"
    echo "User: $(whoami)"
    echo "Working Directory: $(pwd)"
    echo ""

    # Hardware resources
    echo -e "${BLUE}💻 Hardware Resources:${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v free &> /dev/null; then
            echo "Memory: $(free -h | grep '^Mem:' | awk '{print $2 " total, " $3 " used, " $4 " free"}')"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS memory info
        echo "Memory: $(echo "scale=2; $(sysctl -n hw.memsize) / 1024 / 1024 / 1024" | bc)GB total"
    fi
    echo "Disk Space: $(df -h . | tail -1 | awk '{print $4 " available"}')"
    echo "CPU Cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'Unknown')"
    echo ""

    # Software prerequisites
    echo -e "${BLUE}🔍 Software Prerequisites:${NC}"

    check_software "git" "Version control system"
    check_software "docker" "Container runtime"
    check_software "curl" "HTTP client for downloads"

    if command -v docker &> /dev/null; then
        echo "Docker Version: $(docker --version)"
        if docker info &> /dev/null; then
            echo -e "${GREEN}✅ Docker daemon is running${NC}"
        else
            echo -e "${RED}❌ Docker daemon is not running${NC}"
        fi
    fi

    # Package managers
    echo -e "\n${BLUE}📦 Package Managers:${NC}"
    local pm_found=false
    if command -v brew &> /dev/null; then
        echo -e "${GREEN}✅ Homebrew detected${NC}"
        pm_found=true
    fi
    if command -v apt &> /dev/null; then
        echo -e "${GREEN}✅ apt detected${NC}"
        pm_found=true
    fi
    if command -v pacman &> /dev/null; then
        echo -e "${GREEN}✅ pacman detected${NC}"
        pm_found=true
    fi
    if command -v dnf &> /dev/null; then
        echo -e "${GREEN}✅ dnf detected${NC}"
        pm_found=true
    fi
    if [[ $pm_found == false ]]; then
        echo -e "${RED}❌ No supported package manager found${NC}"
    fi

    # Network connectivity
    echo -e "\n${BLUE}🌐 Network Connectivity:${NC}"
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${GREEN}✅ Internet connection available${NC}"
    else
        echo -e "${RED}❌ No internet connection${NC}"
    fi

    if curl -s --max-time 5 https://registry-1.docker.io/ &> /dev/null; then
        echo -e "${GREEN}✅ Docker Hub accessible${NC}"
    else
        echo -e "${RED}❌ Cannot reach Docker Hub${NC}"
    fi

    # Existing Dopemux installation
    echo -e "\n${BLUE}🔍 Existing Dopemux Installation:${NC}"
    if [[ -d "$HOME/.dopemux" ]]; then
        echo -e "${YELLOW}⚠️  Existing ~/.dopemux directory found${NC}"
        echo "   Backup will be created during installation"
    else
        echo -e "${GREEN}✅ No existing Dopemux installation detected${NC}"
    fi

    if [[ -d "$HOME/.claude" ]]; then
        echo -e "${YELLOW}⚠️  Existing ~/.claude directory found${NC}"
        echo "   Backup will be created during installation"
    else
        echo -e "${GREEN}✅ No existing Claude configuration detected${NC}"
    fi

    # Save diagnostics to file
    local diag_file="$DIAGNOSTICS_DIR/system-diagnostics-$(date +%Y%m%d_%H%M%S).txt"
    {
        echo "Dopemux Diagnostics - $(date)"
        echo "===================="
        echo "OS: $(uname -s) $(uname -r)"
        echo "Architecture: $(uname -m)"
        echo "Shell: $SHELL"
        echo "User: $(whoami)"
        echo "Working Directory: $(pwd)"
    } > "$diag_file"

    echo -e "\n${GREEN}📄 Diagnostics saved to: $diag_file${NC}"

    echo -e "\n${CYAN}💡 Recommendations:${NC}"
    echo "• Ensure Docker is running before installation"
    echo "• Free up disk space if less than 10GB available"
    echo "• Check internet connection for downloading dependencies"
    echo "• Close other applications to free up memory"
}

# Helper function for software checks
check_software() {
    local cmd=$1
    local description=$2

    if command -v "$cmd" &> /dev/null; then
        local version
        version=$("$cmd" --version 2>/dev/null | head -1 || echo "Version unknown")
        echo -e "${GREEN}✅ $cmd found${NC} - $version"
    else
        echo -e "${RED}❌ $cmd missing${NC} - $description"
    fi
}

# Troubleshooting guide
run_troubleshooting() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║              🩺 Dopemux Troubleshooting Guide               ║
╚══════════════════════════════════════════════════════════════╝

🔍 COMMON INSTALLATION ISSUES & SOLUTIONS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ PROBLEM: "Docker daemon not running"
   Symptoms: Installation fails with Docker connection errors
   Solutions:
   • macOS: Launch Docker Desktop from Applications folder
   • Linux: sudo systemctl start docker (systemd) or sudo service docker start (init.d)
   • Verify running: docker info or docker ps

❌ PROBLEM: "Permission denied" when running Docker commands
   Symptoms: Docker commands fail with permission errors
   Solutions:
   • Linux: sudo usermod -aG docker $USER && newgrp docker
   • macOS: Check Docker Desktop settings → Preferences → Resources → Advanced
   • Alternative: Run with sudo (not recommended for security)

❌ PROBLEM: "Port already in use"
   Symptoms: Services fail to start with port binding errors
   Solutions:
   • Find conflicting service: lsof -i :5432 (PostgreSQL)
   • Stop conflicting service: sudo systemctl stop postgresql
   • Change ports in docker-compose.unified.yml
   • Use different ports: ./install.sh --custom-ports

❌ PROBLEM: "No space left on device"
   Symptoms: Installation fails with disk space errors
   Solutions:
   • Check usage: df -h
   • Clean Docker: docker system prune -a
   • Free space: rm -rf ~/Downloads/* ~/.cache/*
   • Minimum: 10GB free space required

❌ PROBLEM: "Network timeout" during Docker pulls
   Symptoms: Image downloads fail or are very slow
   Solutions:
   • Check internet: ping 8.8.8.8
   • Try different DNS: echo "8.8.8.8" > /etc/resolv.conf
   • Use VPN if in restricted network
   • Retry later (Docker Hub may be overloaded)

❌ PROBLEM: "Package manager not found"
   Symptoms: CLI tools installation fails
   Solutions:
   • Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   • Use system package manager
   • Manual installation of missing tools

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 POST-INSTALLATION TROUBLESHOOTING

❌ PROBLEM: "dopemux command not found"
   Solutions:
   • Source your shell profile: source ~/.zshrc or ~/.bashrc
   • Check PATH: echo $PATH
   • Reinstall Dopemux CLI tools
   • Add to PATH manually

❌ PROBLEM: Statusline not showing in Claude Code
   Solutions:
   • Check Claude settings: cat ~/.claude/settings.json
   • Restart Claude Code
   • Verify statusline.sh exists and is executable
   • Check for errors in Claude Code logs

❌ PROBLEM: Services not responding after installation
   Solutions:
   • Check service status: docker ps
   • View logs: docker logs dopemux-adhd-engine
   • Restart services: docker-compose -f docker-compose.unified.yml restart
   • Check ports: netstat -tlnp | grep :8095

❌ PROBLEM: API keys not working
   Solutions:
   • Verify environment variables: env | grep API
   • Test keys individually: see INSTALL.md API testing section
   • Check key format (no extra spaces/newlines)
   • Verify account has credits/billing set up

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆘 EMERGENCY RECOVERY

If installation completely fails:

1. Clean up partial installation
   docker-compose -f docker-compose.unified.yml down -v --remove-orphans
   rm -rf ~/.dopemux ~/.claude.bak

2. Restore from backup (if available)
   cp -r ~/.dopemux-backup-* ~/.claude

3. Start fresh
   ./install.sh --yes --quick

4. Get help
   • Check install.log and install-errors.log
   • Run diagnostics: ./install.sh --diagnose
   • File GitHub issue with logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 GETTING HELP

1. Self-Service
   • ./install.sh --diagnose (system analysis)
   • ./install.sh --verify (installation check)
   • dopemux doctor (runtime health check)

2. Documentation
   • INSTALL.md (complete setup guide)
   • README.md (feature overview)
   • docs/ (troubleshooting guides)

3. Community Support
   • GitHub Issues (bug reports)
   • GitHub Discussions (questions)
   • Discord/Slack (real-time help)

4. Professional Support
   • Enterprise support available
   • Priority response for paid plans
   • On-site consulting options

💡 PRO TIP: Always run diagnostics before posting for help!
   ./install.sh --diagnose > diagnostics.txt
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            ;;
        --full)
            FULL_MODE=true
            ;;
        --verify)
            VERIFY_MODE=true
            ;;
        --yes)
            SKIP_CONFIRM=true
            ;;
        --debug)
            DEBUG_MODE=true
            ;;
        --no-docker)
            NO_DOCKER_MODE=true
            ;;
        --diagnose)
            run_diagnostics
            exit 0
            ;;
        --help|-h)
            show_comprehensive_help
            exit 0
            ;;
        --troubleshoot)
            run_troubleshooting
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo ""
            echo "📖 Use --help for comprehensive documentation"
            echo "🔧 Use --diagnose to run system diagnostics"
            echo "🩺 Use --troubleshoot for common issues"
            exit 1
            ;;
    esac
    shift
done

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Initialize log file
echo "Dopemux Installation Log - $(date)" > "$LOG_FILE"
echo "=================================" >> "$LOG_FILE"

# Enhanced error handling with user-friendly messages
handle_error() {
    local error_code=$1
    local error_message=$2
    local suggestion=$3

    echo -e "${RED}❌ INSTALLATION ERROR (Code: $error_code)${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo -e "${RED}$error_message${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"

    if [[ -n "$suggestion" ]]; then
        echo -e "${YELLOW}💡 Suggested Fix:${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        echo -e "${CYAN}$suggestion${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        echo "" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    fi

    echo -e "${YELLOW}📖 For more help:${NC}" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Check install.log for full details" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Run './install.sh --diagnose' for system analysis" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Run './install.sh --troubleshoot' for common solutions" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    echo "  • Visit INSTALL.md for detailed documentation" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"

    exit $error_code
}

# Comprehensive help system
show_comprehensive_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║          📖 Dopemux Installer - Comprehensive Help          ║
╚══════════════════════════════════════════════════════════════╝

🎯 QUICK START
  ./install.sh                    # Interactive installation
  ./install.sh --quick           # Fast setup (core services)
  ./install.sh --full            # Complete setup (everything)
  ./install.sh --verify          # Check existing installation

📋 INSTALLATION MODES

  Interactive Mode (Default)
    • Prompts for confirmation and mode selection
    • Shows detailed progress with actionable next steps
    • Creates backups of existing configurations
    • Provides recovery options on failures

  Quick Mode (--quick)
    • Core services only (PostgreSQL, Redis, Qdrant, ConPort, ADHD Engine)
    • Minimal CLI tools installation
    • Faster setup (~3-5 minutes)
    • Recommended for first-time users

  Full Mode (--full)
    • Everything: all MCP servers, advanced CLI tools, IDE integration
    • Comprehensive configuration and optimization
    • Takes longer (~10-15 minutes)
    • Recommended for power users

🔧 WHAT GETS INSTALLED

  Infrastructure Services
    • PostgreSQL 16 with AGE extension (graph database)
    • Redis 7 (caching and event streaming)
    • Qdrant (vector database for semantic search)

  Dopemux Core Services
    • ADHD Engine (real-time cognitive accommodations)
    • ConPort (knowledge graphs and persistent memory)
    • Task Orchestrator (ADHD-aware task coordination)
    • Dope-Context (semantic code and documentation search)

  CLI Tools & Terminal Enhancement
    • tmux (multi-pane session management)
    • zsh + Oh My Zsh (advanced shell with plugins)
    • Kitty (GPU-accelerated terminal)
    • Starship (customizable shell prompt)
    • fzf, ripgrep, bat, exa, zoxide, tldr (productivity tools)

  Development Integrations
    • Claude Code Router (multi-instance management)
    • Statusline integration (real-time metrics)
    • IDE integrations (VS Code, Vim)
    • Git hooks and workflow automation

🩺 DIAGNOSTICS & TROUBLESHOOTING

  Before Installation
    ./install.sh --diagnose        # System compatibility check
    ./install.sh --troubleshoot    # Common issues and solutions

  During Installation
    • Check install.log for detailed progress
    • Check install-errors.log for specific failures
    • Use Ctrl+C to gracefully abort (cleanup performed)

  After Installation
    • ./install.sh --verify to check everything works
    • dopemux doctor for system health
    • dopemux status for real-time status

🔍 COMMON ISSUES & SOLUTIONS

  Docker Issues
    "Docker daemon not running"
      → Start Docker Desktop or run: sudo systemctl start docker

    "Permission denied"
      → Add user to docker group: sudo usermod -aG docker $USER
      → Log out and back in, or: newgrp docker

    "Port already in use"
      → Find conflicting service: lsof -i :5432
      → Stop conflicting service or change ports in docker-compose.unified.yml

  Network Issues
    "Cannot pull images"
      → Check internet connection
      → Try different DNS: echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
      → Use VPN if in restricted network

  Disk Space Issues
    "Not enough space"
      → Free up space: docker system prune -a
      → Check usage: df -h
      → Minimum required: 10GB free

  Permission Issues
    "Cannot write to ~/.config"
      → Check ownership: ls -la ~/.config
      → Fix ownership: chown -R $USER:$USER ~/.config

  Service Startup Issues
    "Container fails to start"
      → Check logs: docker logs <container_name>
      → Verify environment variables
      → Check port conflicts

📊 ERROR CODES

  10 - ERROR_NO_DOCKER           Docker not installed
  11 - ERROR_DOCKER_NOT_RUNNING  Docker daemon not running
  12 - ERROR_NO_PACKAGE_MANAGER  No supported package manager
  13 - ERROR_SERVICE_START_FAIL  Docker services failed to start
  14 - ERROR_CONFIG_BACKUP_FAIL  Configuration backup failed
  15 - ERROR_NETWORK_FAIL        Network connectivity issues
  16 - ERROR_DISK_SPACE_LOW      Insufficient disk space
  17 - ERROR_PERMISSION_DENIED   Permission denied for file operations

🆘 GETTING HELP

  1. Check the logs
     • install.log (full installation log)
     • install-errors.log (specific errors only)

  2. Run diagnostics
     ./install.sh --diagnose

  3. Check common solutions
     ./install.sh --troubleshoot

  4. Search documentation
     • INSTALL.md for detailed setup guide
     • README.md for feature overview
     • docs/ for troubleshooting guides

  5. Get community help
     • GitHub Issues for bugs and feature requests
     • Discord/Slack for community support

⚙️ ADVANCED OPTIONS

  --yes       Skip all confirmation prompts
  --debug     Enable debug mode with verbose logging
  --no-docker Skip Docker services (install CLI tools only, for containerized environments)
  --diagnose  Run system compatibility diagnostics
  --help      Show this comprehensive help

📋 SYSTEM REQUIREMENTS

  Minimum Hardware
    • CPU: 2 cores (4+ recommended)
    • RAM: 4GB (8GB+ recommended)
    • Disk: 10GB free space (20GB+ recommended)
    • Network: Stable internet for downloads

  Supported Operating Systems
    • macOS 12.0+ (Monterey or later)
    • Ubuntu 20.04+ / Debian 11+
    • CentOS 8+ / RHEL 8+ / Fedora 34+
    • Arch Linux (current)
    • Other Linux distributions with apt/dnf/pacman

  Software Prerequisites
    • Docker 20.10+ with Docker Compose (auto-detected)
    • curl (for downloads, auto-installed if missing)
    • git (for cloning, auto-installed if missing)
    • bash or zsh shell (zsh auto-installed and set as default)

  Package Managers (Auto-Detected)
    • macOS: Homebrew (brew)
    • Ubuntu/Debian: apt
    • Fedora/RHEL: dnf/yum
    • Arch Linux: pacman

🚀 POST-INSTALLATION

  After successful installation:

  1. Set up API keys (see INSTALL.md for detailed guide)
     • Anthropic Claude (primary AI model)
     • OpenRouter (cost-effective fallbacks)
     • Voyage AI (semantic search)

  2. Start your development session
     dopemux start

  3. Verify everything works
     dopemux doctor

  4. Check the statusline in Claude Code
     (shows real-time ADHD metrics and energy levels)

  Your terminal environment is now optimized for ADHD-friendly development! 🎉
EOF
}

# System diagnostics
run_diagnostics() {
    echo -e "${CYAN}🔧 Dopemux System Diagnostics${NC}"
    echo "==============================="
    echo ""

    # Create diagnostics directory
    mkdir -p "$DIAGNOSTICS_DIR"

    # System information
    echo -e "${BLUE}📊 System Information:${NC}"
    echo "OS: $(uname -s) $(uname -r)"
    echo "Architecture: $(uname -m)"
    echo "Shell: $SHELL"
    echo "User: $(whoami)"
    echo "Working Directory: $(pwd)"
    echo ""

    # Hardware resources
    echo -e "${BLUE}💻 Hardware Resources:${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v free &> /dev/null; then
            echo "Memory: $(free -h | grep '^Mem:' | awk '{print $2 " total, " $3 " used, " $4 " free"}')"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS memory info
        echo "Memory: $(echo "scale=2; $(sysctl -n hw.memsize) / 1024 / 1024 / 1024" | bc)GB total"
    fi
    echo "Disk Space: $(df -h . | tail -1 | awk '{print $4 " available"}')"
    echo "CPU Cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'Unknown')"
    echo ""

    # Software prerequisites
    echo -e "${BLUE}🔍 Software Prerequisites:${NC}"

    check_software "git" "Version control system"
    check_software "docker" "Container runtime"
    check_software "curl" "HTTP client for downloads"

    if command -v docker &> /dev/null; then
        echo "Docker Version: $(docker --version)"
        if docker info &> /dev/null; then
            echo -e "${GREEN}✅ Docker daemon is running${NC}"
        else
            echo -e "${RED}❌ Docker daemon is not running${NC}"
        fi
    fi

    # Package managers
    echo -e "\n${BLUE}📦 Package Managers:${NC}"
    local pm_found=false
    if command -v brew &> /dev/null; then
        echo -e "${GREEN}✅ Homebrew detected${NC}"
        pm_found=true
    fi
    if command -v apt &> /dev/null; then
        echo -e "${GREEN}✅ apt detected${NC}"
        pm_found=true
    fi
    if command -v pacman &> /dev/null; then
        echo -e "${GREEN}✅ pacman detected${NC}"
        pm_found=true
    fi
    if command -v dnf &> /dev/null; then
        echo -e "${GREEN}✅ dnf detected${NC}"
        pm_found=true
    fi
    if [[ $pm_found == false ]]; then
        echo -e "${RED}❌ No supported package manager found${NC}"
    fi

    # Network connectivity
    echo -e "\n${BLUE}🌐 Network Connectivity:${NC}"
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${GREEN}✅ Internet connection available${NC}"
    else
        echo -e "${RED}❌ No internet connection${NC}"
    fi

    if curl -s --max-time 5 https://registry-1.docker.io/ &> /dev/null; then
        echo -e "${GREEN}✅ Docker Hub accessible${NC}"
    else
        echo -e "${RED}❌ Cannot reach Docker Hub${NC}"
    fi

    # Existing Dopemux installation
    echo -e "\n${BLUE}🔍 Existing Dopemux Installation:${NC}"
    if [[ -d "$HOME/.dopemux" ]]; then
        echo -e "${YELLOW}⚠️  Existing ~/.dopemux directory found${NC}"
        echo "   Backup will be created during installation"
    else
        echo -e "${GREEN}✅ No existing Dopemux installation detected${NC}"
    fi

    if [[ -d "$HOME/.claude" ]]; then
        echo -e "${YELLOW}⚠️  Existing ~/.claude directory found${NC}"
        echo "   Backup will be created during installation"
    else
        echo -e "${GREEN}✅ No existing Claude configuration detected${NC}"
    fi

    # Save diagnostics to file
    echo -e "\n${GREEN}📄 Diagnostics saved to: $DIAGNOSTICS_DIR/system-diagnostics-$(date +%Y%m%d_%H%M%S).txt${NC}"

    echo -e "\n${CYAN}💡 Recommendations:${NC}"
    echo "• Ensure Docker is running before installation"
    echo "• Free up disk space if less than 10GB available"
    echo "• Check internet connection for downloading dependencies"
    echo "• Close other applications to free up memory"
}

# Helper function for software checks
check_software() {
    local cmd=$1
    local description=$2

    if command -v "$cmd" &> /dev/null; then
        local version
        version=$("$cmd" --version 2>/dev/null | head -1 || echo "Version unknown")
        echo -e "${GREEN}✅ $cmd found${NC} - $version"
    else
        echo -e "${RED}❌ $cmd missing${NC} - $description"
    fi
}

# System diagnostics

# Troubleshooting guide
run_troubleshooting() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║              🩺 Dopemux Troubleshooting Guide               ║
╚══════════════════════════════════════════════════════════════╝

🔍 COMMON INSTALLATION ISSUES & SOLUTIONS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ PROBLEM: "Docker daemon not running"
   Symptoms: Installation fails with Docker connection errors
   Solutions:
   • macOS: Launch Docker Desktop from Applications folder
   • Linux: sudo systemctl start docker (systemd) or sudo service docker start (init.d)
   • Verify running: docker info or docker ps

❌ PROBLEM: "Permission denied" when running Docker commands
   Symptoms: Docker commands fail with permission errors
   Solutions:
   • Linux: sudo usermod -aG docker $USER && newgrp docker
   • macOS: Check Docker Desktop settings → Preferences → Resources → Advanced
   • Alternative: Run with sudo (not recommended for security)

❌ PROBLEM: "Port already in use"
   Symptoms: Services fail to start with port binding errors
   Solutions:
   • Find conflicting service: lsof -i :5432 (PostgreSQL)
   • Stop conflicting service: sudo systemctl stop postgresql
   • Change ports in docker-compose.unified.yml
   • Use different ports: ./install.sh --custom-ports

❌ PROBLEM: "No space left on device"
   Symptoms: Installation fails with disk space errors
   Solutions:
   • Check usage: df -h
   • Clean Docker: docker system prune -a
   • Free space: rm -rf ~/Downloads/* ~/.cache/*
   • Minimum: 10GB free space required

❌ PROBLEM: "Network timeout" during Docker pulls
   Symptoms: Image downloads fail or are very slow
   Solutions:
   • Check internet: ping 8.8.8.8
   • Try different DNS: echo "8.8.8.8" > /etc/resolv.conf
   • Use VPN if in restricted network
   • Retry later (Docker Hub may be overloaded)

❌ PROBLEM: "Package manager not found"
   Symptoms: CLI tools installation fails
   Solutions:
   • Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   • Use system package manager
   • Manual installation of missing tools

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 POST-INSTALLATION TROUBLESHOOTING

❌ PROBLEM: "dopemux command not found"
   Solutions:
   • Source your shell profile: source ~/.zshrc or ~/.bashrc
   • Check PATH: echo $PATH
   • Reinstall Dopemux CLI tools
   • Add to PATH manually

❌ PROBLEM: Statusline not showing in Claude Code
   Solutions:
   • Check Claude settings: cat ~/.claude/settings.json
   • Restart Claude Code
   • Verify statusline.sh exists and is executable
   • Check for errors in Claude Code logs

❌ PROBLEM: Services not responding after installation
   Solutions:
   • Check service status: docker ps
   • View logs: docker logs dopemux-adhd-engine
   • Restart services: docker-compose -f docker-compose.unified.yml restart
   • Check ports: netstat -tlnp | grep :8095

❌ PROBLEM: API keys not working
   Solutions:
   • Verify environment variables: env | grep API
   • Test keys individually: see INSTALL.md API testing section
   • Check key format (no extra spaces/newlines)
   • Verify account has credits/billing set up

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆘 EMERGENCY RECOVERY

If installation completely fails:

1. Clean up partial installation
   docker-compose -f docker-compose.unified.yml down -v --remove-orphans
   rm -rf ~/.dopemux ~/.claude.bak

2. Restore from backup (if available)
   cp -r ~/.dopemux-backup-* ~/.claude

3. Start fresh
   ./install.sh --yes --quick

4. Get help
   • Check install.log and install-errors.log
   • Run diagnostics: ./install.sh --diagnose
   • File GitHub issue with logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 GETTING HELP

1. Self-Service
   • ./install.sh --diagnose (system analysis)
   • ./install.sh --verify (installation check)
   • dopemux doctor (runtime health check)

2. Documentation
   • INSTALL.md (complete setup guide)
   • README.md (feature overview)
   • docs/ (troubleshooting guides)

3. Community Support
   • GitHub Issues (bug reports)
   • GitHub Discussions (questions)
   • Discord/Slack (real-time help)

4. Professional Support
   • Enterprise support available
   • Priority response for paid plans
   • On-site consulting options

💡 PRO TIP: Always run diagnostics before posting for help!
   ./install.sh --diagnose > diagnostics.txt
EOF
}

# Initialize log file
echo "Dopemux Installation Log - $(date)" > "$LOG_FILE"
echo "=================================" >> "$LOG_FILE"

# Progress tracking
TOTAL_STEPS=8
CURRENT_STEP=0

show_progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "${CYAN}[$CURRENT_STEP/$TOTAL_STEPS]${NC} $1"
}

# Check if running as root (not recommended)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root is not recommended. Continue anyway? (y/N)"
        if [[ $SKIP_CONFIRM == false ]]; then
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
}

# Check prerequisites
check_prerequisites() {
    show_progress "Checking prerequisites..."

    local missing_deps=()

    # Check for required commands
    local required_cmds=("docker" "docker-compose" "curl")
    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    # Special handling for git - try to install if missing
    if ! command -v git &> /dev/null; then
        log_warn "Git not found - attempting to install..."
        if ! install_git; then
            missing_deps+=("git")
        fi
    fi

    # Check Docker daemon (only if Docker is available and not in no-docker mode)
    if [[ $NO_DOCKER_MODE == true ]]; then
        log_info "Skipping Docker daemon check (--no-docker mode)"
    elif ! command -v docker &> /dev/null; then
        log_warn "Docker not found - this is expected in some environments"
        log_info "You can install services manually or use pre-built containers"
        log_info "See INSTALL.md for manual installation instructions"
    else
        detect_container_environment

        if ! docker info &> /dev/null; then
            if [[ $IN_CONTAINER == true ]]; then
                handle_error $ERROR_DOCKER_NOT_RUNNING \
                    "Docker daemon is not accessible from within this container." \
                    "Containerized Environment Solutions:\n• Mount Docker socket: docker run -v /var/run/docker.sock:/var/run/docker.sock\n• Use Docker-in-Docker: docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock\n• Run on host: Exit container and run installer on host system\n• Use --no-docker flag to skip Docker services and install CLI tools only"
            else
                handle_error $ERROR_DOCKER_NOT_RUNNING \
                    "Docker daemon is not running. Please start Docker first." \
                    "macOS: Launch Docker Desktop from Applications\nLinux: sudo systemctl start docker (systemd) or sudo service docker start (init.d)\nWindows: Start Docker Desktop\nDocker containers: Ensure host Docker is running"
            fi
        fi
    fi

    # Detect container environment
    detect_container_environment() {
        IN_CONTAINER=false
        if [[ -f /.dockerenv ]] || grep -q "docker\|containerd" /proc/1/cgroup 2>/dev/null; then
            IN_CONTAINER=true
        fi
    }
        if ! docker info &> /dev/null; then
            # Detect if we're in a container
            local in_container=false
            if [[ -f /.dockerenv ]] || grep -q "docker\|containerd" /proc/1/cgroup 2>/dev/null; then
                in_container=true
            fi

            if [[ $in_container == true ]]; then
                handle_error $ERROR_DOCKER_NOT_RUNNING \
                    "Docker daemon is not accessible from within this container." \
                    "Containerized Environment Solutions:\n• Mount Docker socket: docker run -v /var/run/docker.sock:/var/run/docker.sock\n• Use Docker-in-Docker: docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock\n• Run on host: Exit container and run installer on host system\n• Use --no-docker flag to skip Docker services and install CLI tools only"
            else
                handle_error $ERROR_DOCKER_NOT_RUNNING \
                    "Docker daemon is not running. Please start Docker first." \
                    "macOS: Launch Docker Desktop from Applications\nLinux: sudo systemctl start docker (systemd) or sudo service docker start (init.d)\nWindows: Start Docker Desktop\nDocker containers: Ensure host Docker is running"
            fi
        fi
    else
        log_warn "Docker not found - this is expected in some environments"
        log_info "You can install services manually or use pre-built containers"
        log_info "See INSTALL.md for manual installation instructions"
    fi

    # Check available disk space (need at least 10GB for full installation)
    local required_space_kb
    if [[ $FULL_MODE == true ]]; then
        required_space_kb=10485760  # 10GB
    else
        required_space_kb=2097152   # 2GB
    fi

    local available_space
    available_space=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
    if [[ $available_space -lt $required_space_kb ]]; then
        local required_gb=$((required_space_kb / 1048576))
        handle_error $ERROR_DISK_SPACE_LOW \
            "Not enough disk space. Need at least ${required_gb}GB available (found $(($available_space / 1048576))GB)." \
            "Free up space by:\n• docker system prune -a\n• rm -rf ~/Downloads/*\n• Empty trash/recycle bin\n• Move large files to external storage"
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_warn "Missing required dependencies: ${missing_deps[*]}"
        log_info "Attempting automatic installation..."

        # Try to install missing dependencies automatically
        for dep in "${missing_deps[@]}"; do
            if install_dependency "$dep"; then
                # Remove from missing_deps if successfully installed
                missing_deps=(${missing_deps[@]/$dep})
            fi
        done

        if [[ ${#missing_deps[@]} -gt 0 ]]; then
            log_error "Could not install these dependencies automatically: ${missing_deps[*]}"
            echo ""
            echo "Installation will continue, but some features may not work."
            echo "Please install missing dependencies manually:"
            echo ""
            show_install_commands
            echo ""
            if [[ $SKIP_CONFIRM == false ]]; then
                read -p "Continue anyway? (y/N) " -r
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        else
            log_success "All missing dependencies installed successfully"
        fi
    else
        log_success "Prerequisites check passed"
    fi
}

# Try to install any dependency automatically
install_dependency() {
    local dep=$1
    log_info "Attempting to install $dep automatically..."

    # Check if running as root (no sudo needed)
    if [[ $EUID -eq 0 ]]; then
        log_info "Running as root - no sudo needed for package installation"
    elif ! command -v sudo &> /dev/null; then
        log_warn "sudo not available - cannot install $dep automatically"
        return 1
    fi

    # Detect OS and try to install the dependency
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt &> /dev/null; then
            # Debian/Ubuntu
            if [[ $EUID -eq 0 ]]; then
                apt update && apt install -y "$dep"
            else
                sudo apt update && sudo apt install -y "$dep"
            fi
            if [[ $? -eq 0 ]]; then
                log_success "$dep installed via apt"
                return 0
            fi
        elif command -v dnf &> /dev/null; then
            # Fedora/RHEL
            if [[ $EUID -eq 0 ]]; then
                dnf install -y "$dep"
            else
                sudo dnf install -y "$dep"
            fi
            if [[ $? -eq 0 ]]; then
                log_success "$dep installed via dnf"
                return 0
            fi
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            if [[ $EUID -eq 0 ]]; then
                pacman -S --noconfirm "$dep"
            else
                sudo pacman -S --noconfirm "$dep"
            fi
            if [[ $? -eq 0 ]]; then
                log_success "$dep installed via pacman"
                return 0
            fi
        elif command -v apk &> /dev/null; then
            # Alpine Linux (common in Docker)
            if [[ $EUID -eq 0 ]]; then
                apk add "$dep"
            else
                sudo apk add "$dep"
            fi
            if [[ $? -eq 0 ]]; then
                log_success "$dep installed via apk (Alpine Linux)"
                return 0
            fi
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            if brew install "$dep"; then
                log_success "$dep installed via Homebrew"
                return 0
            fi
        else
            log_warn "Homebrew not found - cannot install $dep automatically"
            return 1
        fi
    fi

    log_error "Could not install $dep automatically"
    return 1
}

# Try to install git automatically
install_git() {
    log_info "Attempting to install git automatically..."

    # Check if running as root (no sudo needed)
    if [[ $EUID -eq 0 ]]; then
        log_info "Running as root - no sudo needed for package installation"
    elif ! command -v sudo &> /dev/null; then
        log_warn "sudo not available - attempting installation without sudo or providing alternatives"
        log_info "Alternative: Install git manually or run as root"
        log_info "For Docker containers: Use 'docker run -it --rm ubuntu:latest bash' with apt"
        log_info "For cloud environments: Use package manager directly or contact admin"
        return 1
    fi

    # Detect OS and try to install git
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt &> /dev/null; then
            # Debian/Ubuntu
            if [[ $EUID -eq 0 ]]; then
                apt update && apt install -y git
            else
                sudo apt update && sudo apt install -y git
            fi
            if [[ $? -eq 0 ]]; then
                log_success "Git installed via apt"
                return 0
            fi
        elif command -v dnf &> /dev/null; then
            # Fedora/RHEL
            if [[ $EUID -eq 0 ]]; then
                dnf install -y git
            else
                sudo dnf install -y git
            fi
            if [[ $? -eq 0 ]]; then
                log_success "Git installed via dnf"
                return 0
            fi
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            if [[ $EUID -eq 0 ]]; then
                pacman -S --noconfirm git
            else
                sudo pacman -S --noconfirm git
            fi
            if [[ $? -eq 0 ]]; then
                log_success "Git installed via pacman"
                return 0
            fi
        elif command -v apk &> /dev/null; then
            # Alpine Linux (common in Docker)
            if [[ $EUID -eq 0 ]]; then
                apk add git
            else
                sudo apk add git
            fi
            if [[ $? -eq 0 ]]; then
                log_success "Git installed via apk (Alpine Linux)"
                return 0
            fi
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            if brew install git; then
                log_success "Git installed via Homebrew"
                return 0
            fi
        else
            log_warn "Homebrew not found - install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        fi
    fi

    log_error "Could not install git automatically"
    log_info "Manual installation required - see INSTALL.md for instructions"
    return 1
}

# Show installation commands for missing dependencies
show_install_commands() {
    echo "macOS (with Homebrew):"
    echo "  brew install docker docker-compose curl git"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install docker.io docker-compose curl git"
    echo ""
    echo "CentOS/RHEL/Fedora:"
    echo "  sudo dnf install docker docker-compose curl git"
    echo "  # or: sudo yum install docker docker-compose curl git"
    echo ""
    echo "Arch Linux:"
    echo "  sudo pacman -S docker docker-compose curl git"
    echo ""
    echo "Windows (WSL2):"
    echo "  # Install Docker Desktop for Windows"
    echo "  sudo apt install curl git  # inside WSL2"
}

# Backup existing configuration
backup_existing() {
    if [[ -d "$HOME/.claude" ]] || [[ -d "$HOME/.dopemux" ]]; then
        show_progress "Backing up existing configuration..."

        local backup_dir="$HOME/.dopemux-backup-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"

        if [[ -d "$HOME/.claude" ]]; then
            cp -r "$HOME/.claude" "$backup_dir/"
            log_info "Backed up Claude configuration to $backup_dir/.claude"
        fi

        if [[ -d "$HOME/.dopemux" ]]; then
            cp -r "$HOME/.dopemux" "$backup_dir/"
            log_info "Backed up Dopemux configuration to $backup_dir/.dopemux"
        fi

        echo "$backup_dir" > "$PROJECT_ROOT/.backup_location"
    fi
}

# Install Docker services
install_docker_services() {
    if [[ $NO_DOCKER_MODE == true ]]; then
        log_info "Skipping Docker services (--no-docker mode)"
        return 0
    fi

    show_progress "Installing Docker services..."

    local compose_file=""
    local compose_result=0

    if [[ $QUICK_MODE == true ]]; then
        log_info "Quick mode: Starting core services only"
        compose_file="docker-compose.unified.yml"
        docker-compose -f "$compose_file" up -d
        compose_result=$?
    else
        log_info "Full mode: Starting complete stack"
        # Try unified first, fall back to master
        compose_file="docker-compose.unified.yml"
        if docker-compose -f "$compose_file" up -d 2>/dev/null; then
            log_info "Used unified compose configuration"
            compose_result=0
        else
            log_warn "Unified compose failed, trying master configuration"
            compose_file="docker-compose.master.yml"
            docker-compose -f "$compose_file" up -d
            compose_result=$?
        fi
    fi

    # Check if Docker Compose succeeded
    if [[ $compose_result -ne 0 ]]; then
        log_error "Docker Compose failed to start services"
        log_info "This might be due to missing Dockerfiles or build issues"
        log_info "Common solutions:"
        echo "  • Check if all required Dockerfiles exist"
        echo "  • Ensure Docker daemon is running"
        echo "  • Try: docker-compose -f $compose_file build --no-cache"
        echo "  • Or run in quick mode: ./install.sh --quick"
        echo ""

        if [[ $SKIP_CONFIRM == false ]]; then
            read -p "Continue with CLI tools setup only? (y/N) " -r
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi

        # Skip Docker services but continue with CLI setup
        return 1
    fi

    # Wait for services to start
    log_info "Waiting for services to initialize..."
    sleep 30

    # Verify key services are running
    local services_to_check=("postgres" "redis" "qdrant" "conport" "adhd-engine")

    for service in "${services_to_check[@]}"; do
        if docker ps | grep -q "$service"; then
            log_success "$service is running"
        else
            log_warn "$service may not be running - will verify later"
        fi
    done
}

# Install MCP servers
install_mcp_servers() {
    if [[ $QUICK_MODE == true ]]; then
        log_info "Quick mode: Skipping MCP server installation"
        return
    fi

    show_progress "Installing MCP servers..."

    # Install MCP servers globally
    if [[ -f "scripts/install-mcp-servers.sh" ]]; then
        bash scripts/install-mcp-servers.sh
    else
        log_warn "MCP server installation script not found - skipping"
    fi
}

# Install Claude Code Router
install_claude_router() {
    show_progress "Installing Claude Code Router..."

    if [[ -f "scripts/install_claude_code_router.sh" ]]; then
        bash scripts/install_claude_code_router.sh
    else
        log_warn "Claude Code Router installation script not found"
        log_info "You can install it manually later with: ./scripts/install_claude_code_router.sh"
    fi
}

# Initialize Dopemux services
initialize_services() {
    show_progress "Initializing Dopemux services..."

    # Initialize ConPort
    log_info "Initializing ConPort..."
    if mcp__conport__get_active_context --workspace_id "$PROJECT_ROOT" &> /dev/null; then
        log_success "ConPort initialized"
    else
        log_warn "ConPort initialization failed - may need manual setup"
    fi

    # Start ADHD Engine if not running
    if ! curl -f http://localhost:8095/health &> /dev/null; then
        log_info "Starting ADHD Engine..."
        cd services/adhd_engine/services/adhd_engine
        ADHD_ENGINE_API_KEY=dev-key-123 ALLOWED_ORIGINS=http://localhost:3000 nohup python -m uvicorn main:app --host 0.0.0.0 --port 8095 > /dev/null 2>&1 &
        cd - > /dev/null
        sleep 5
        log_success "ADHD Engine started"
    else
        log_info "ADHD Engine already running"
    fi

    # Index Dope-Context
    log_info "Indexing Dope-Context..."
    if mcp__dope-context__index_workspace --workspace_path "$PROJECT_ROOT" &> /dev/null; then
        log_success "Dope-Context indexed"
    else
        log_warn "Dope-Context indexing failed - may need manual setup"
    fi
}

# Install CLI tools
install_cli_tools() {
    if [[ $QUICK_MODE == true ]]; then
        log_info "Quick mode: Skipping CLI tools installation"
        return
    fi

    show_progress "Installing CLI tools..."

    # Detect package manager
    if command -v brew &> /dev/null; then
        PACKAGE_MANAGER="brew"
        log_info "Using Homebrew package manager"
    elif command -v apt &> /dev/null; then
        PACKAGE_MANAGER="apt"
        log_info "Using apt package manager"
    elif command -v pacman &> /dev/null; then
        PACKAGE_MANAGER="pacman"
        log_info "Using pacman package manager"
    elif command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
        log_info "Using dnf package manager"
    else
        log_warn "No supported package manager found - skipping CLI tools"
        return
    fi

    # Install tools based on package manager
    case $PACKAGE_MANAGER in
        brew)
            install_brew_tools
            ;;
        apt)
            install_apt_tools
            ;;
        pacman)
            install_pacman_tools
            ;;
        dnf)
            install_dnf_tools
            ;;
    esac

    # Install universal tools (curl-based)
    install_universal_tools

    log_success "CLI tools installation completed"
}

# Install tools using Homebrew (macOS)
install_brew_tools() {
    local tools=("tmux" "zsh" "fzf" "ripgrep" "bat" "eza" "zoxide" "tldr")

    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            if brew install "$tool" 2>/dev/null; then
                log_success "$tool installed"
            else
                log_warn "Failed to install $tool (may already be installed or need manual installation)"
            fi
        else
            log_info "$tool already installed"
        fi
    done

    # Install kitty (macOS specific)
    if ! command -v kitty &> /dev/null; then
        log_info "Installing kitty..."
        if brew install --cask kitty 2>/dev/null; then
            log_success "kitty installed"
        else
            log_warn "Failed to install kitty (may need manual installation)"
        fi
    fi
}

# Install tools using apt
install_apt_tools() {
    local tools=("tmux" "zsh" "fzf" "ripgrep" "bat" "exa" "zoxide" "tldr")

    # Update package list
    sudo apt update

    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            if sudo apt install -y "$tool"; then
                log_success "$tool installed"
            else
                log_warn "Failed to install $tool"
            fi
        else
            log_info "$tool already installed"
        fi
    done

    # Install kitty (special case)
    if ! command -v kitty &> /dev/null; then
        log_info "Installing kitty..."
        curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
        log_success "kitty installed (may need to add to PATH)"
    fi
}

# Install tools using pacman
install_pacman_tools() {
    local tools=("tmux" "zsh" "fzf" "ripgrep" "bat" "exa" "zoxide" "tldr")

    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            if sudo pacman -S --noconfirm "$tool"; then
                log_success "$tool installed"
            else
                log_warn "Failed to install $tool"
            fi
        else
            log_info "$tool already installed"
        fi
    done

    # Install kitty (special case)
    if ! command -v kitty &> /dev/null; then
        log_info "Installing kitty..."
        if sudo pacman -S --noconfirm kitty; then
            log_success "kitty installed"
        else
            log_warn "Failed to install kitty"
        fi
    fi
}

# Install tools using dnf
install_dnf_tools() {
    local tools=("tmux" "zsh" "fzf" "ripgrep" "bat" "exa" "zoxide" "tldr")

    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            if sudo dnf install -y "$tool"; then
                log_success "$tool installed"
            else
                log_warn "Failed to install $tool"
            fi
        else
            log_info "$tool already installed"
        fi
    done

    # Install kitty (special case)
    if ! command -v kitty &> /dev/null; then
        log_info "Installing kitty..."
        if sudo dnf install -y kitty; then
            log_success "kitty installed"
        else
            log_warn "Failed to install kitty"
        fi
    fi
}

# Install universal tools (curl-based)
install_universal_tools() {
    # Install Starship prompt
    if ! command -v starship &> /dev/null; then
        log_info "Installing starship..."
        if curl -sS https://starship.rs/install.sh | sh -s -- --yes; then
            log_success "starship installed"
        else
            log_warn "Failed to install starship"
        fi
    else
        log_info "starship already installed"
    fi

    # Install Oh My Zsh (if zsh is available)
    if command -v zsh &> /dev/null && [[ ! -d "$HOME/.oh-my-zsh" ]]; then
        log_info "Installing Oh My Zsh..."
        if sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended; then
            log_success "Oh My Zsh installed"
        else
            log_warn "Failed to install Oh My Zsh"
        fi
    fi
}

# Configure CLI tools
configure_cli_tools() {
    if [[ $QUICK_MODE == true ]]; then
        log_info "Quick mode: Skipping CLI tools configuration"
        return
    fi

    show_progress "Configuring CLI tools..."

    # Configure Zsh
    configure_zsh

    # Configure Kitty
    configure_kitty

    # Configure Starship
    configure_starship

    # Configure tmux
    configure_tmux

    log_success "CLI tools configuration completed"
}

# Configure Zsh
configure_zsh() {
    if ! command -v zsh &> /dev/null; then
        log_warn "Zsh not installed - skipping configuration"
        return
    fi

    log_info "Configuring Zsh..."

    # Backup existing .zshrc
    if [[ -f "$HOME/.zshrc" ]] && [[ ! -f "$HOME/.zshrc.backup" ]]; then
        cp "$HOME/.zshrc" "$HOME/.zshrc.backup"
        log_info "Backed up existing .zshrc"
    fi

    # Create Dopemux Zsh configuration
    cat >> "$HOME/.zshrc" << 'EOF'

# Dopemux ADHD-optimized Zsh configuration
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="agnoster"
plugins=(git docker tmux python node npm)

if [[ -f "$ZSH/oh-my-zsh.sh" ]]; then
    source $ZSH/oh-my-zsh.sh
fi

# Dopemux environment variables (set your API keys here)
# export ANTHROPIC_API_KEY="your-anthropic-key"
# export OPENROUTER_API_KEY="your-openrouter-key"
# export VOYAGE_API_KEY="your-voyage-key"
# export XAI_API_KEY="your-xai-key"
# export OPENAI_API_KEY="your-openai-key"

# ADHD-friendly aliases
alias d="dopemux"
alias ds="dopemux start"
alias dd="dopemux doctor"
alias dm="dopemux mobile start"
alias dl="dopemux status"

# Git shortcuts for ADHD workflow
alias gs="git status --short"
alias ga="git add"
alias gc="git commit -m"
alias gp="git push"
alias gl="git log --oneline -10"

# Python virtual environment helpers
alias venv="python -m venv"
alias act="source venv/bin/activate"
alias deact="deactivate"

# Tmux session management
alias tmd="tmux new -s dopemux"
alias tma="tmux a -t dopemux"
alias tmk="tmux kill-session -t dopemux"

# Directory navigation (ADHD-friendly)
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Colorized output for better ADHD scanning
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

# CLI tool configurations
if command -v fzf &> /dev/null; then
    source <(fzf --zsh)
fi

if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
    alias cd="z"
fi

if command -v exa &> /dev/null; then
    alias ls="exa --icons --group-directories-first"
    alias ll="exa --icons --group-directories-first -l"
    alias la="exa --icons --group-directories-first -la"
fi

if command -v bat &> /dev/null; then
    alias cat="bat --theme=gruvbox-dark"
fi

# ADHD workflow functions
function start_session() {
    echo "🧠 Starting ADHD-optimized development session..."
    tmux new -s "dopemux-$(date +%H%M)" -d
    dopemux start --role act
    tmux a -t dopemux
}

function end_session() {
    echo "💾 Saving session state..."
    dopemux save
    echo "✅ Session saved. Take a break! ☕"
}

function dev_status() {
    echo "🔋 Energy Level: ${TMUX_ADHD_ENERGY:-unknown}"
    echo "🧠 Cognitive Load: ${TMUX_ADHD_LOAD:-unknown}"
    echo "📊 ConPort Decisions: ${TMUX_CONPORT_DECISIONS:-0}"
    echo "🤖 Active Model: ${TMUX_MODEL:-unknown}"
}

function break_timer() {
    local minutes=${1:-25}
    echo "⏰ ${minutes}-minute focus session starting..."
    sleep ${minutes}m
    echo "☕ Break time! Stretch, hydrate, look away from screen."
    echo "🔔 Reminder: ${minutes} minutes of focused work completed."
}
EOF

    # Set Zsh as default shell if not already
    if [[ "$SHELL" != *"zsh"* ]]; then
        log_info "Setting Zsh as default shell..."
        if chsh -s $(which zsh); then
            log_success "Zsh set as default shell (restart terminal to take effect)"
        else
            log_warn "Failed to set Zsh as default shell"
        fi
    fi

    log_success "Zsh configured"
}

# Configure Kitty
configure_kitty() {
    if ! command -v kitty &> /dev/null; then
        log_warn "Kitty not installed - skipping configuration"
        return
    fi

    log_info "Configuring Kitty..."

    mkdir -p "$HOME/.config/kitty"

    # Create ADHD-optimized kitty.conf
    cat > "$HOME/.config/kitty/kitty.conf" << 'EOF'
# Dopemux ADHD-optimized Kitty configuration
font_family      Fira Code
font_size        12
scrollback_lines 10000

# Smooth scrolling for ADHD focus
enable_audio_bell no
visual_bell_duration 0.1

# GPU acceleration
linux_display_server auto

# Window management
remember_window_size  yes
initial_window_width  1400
initial_window_height 900

# Gruvbox-inspired colors (ADHD-friendly contrast)
background #282828
foreground #ebdbb2
color0     #282828  # black
color1     #cc241d  # red
color2     #98971a  # green
color3     #d79921  # yellow
color4     #458588  # blue
color5     #b16286  # magenta
color6     #689d6a  # cyan
color7     #a89984  # white
color8     #928374  # bright black
color9     #fb4934  # bright red
color10    #b8bb26  # bright green
color11    #fabd2f  # bright yellow
color12    #83a598  # bright blue
color13    #d3869b  # bright magenta
color14    #8ec07c  # bright cyan
color15    #fbf1c7  # bright white
EOF

    log_success "Kitty configured"
}

# Configure Starship
configure_starship() {
    if ! command -v starship &> /dev/null; then
        log_warn "Starship not installed - skipping configuration"
        return
    fi

    log_info "Configuring Starship..."

    mkdir -p "$HOME/.config"

    # Create ADHD-optimized starship.toml
    cat > "$HOME/.config/starship.toml" << 'EOF'
# Dopemux ADHD-optimized Starship config
format = """
[](color_orange)\
$os\
$username\
[](bg:color_yellow fg:color_orange)\
$directory\
[](fg:color_yellow bg:color_aqua)\
$git_branch\
$git_status\
[](fg:color_aqua bg:color_blue)\
$c\
$rust\
$golang\
$nodejs\
$php\
$java\
$kotlin\
$scala\
$haskell\
$python\
[](fg:color_blue bg:color_bg3)\
$docker_context\
$conda\
[](fg:color_bg3 bg:color_green)\
$time\
[ ](fg:color_green)\
"""

[directory]
style = "bg:color_yellow"
format = "[ $path ]($style)"
truncation_length = 3
truncation_symbol = "…/"

[git_branch]
symbol = ""
style = "bg:color_aqua"
format = '[[ $symbol $branch ](bg:color_aqua)]($style)'

[git_status]
style = "bg:color_aqua"
format = '[[($all_status$ahead_behind )](bg:color_aqua)]($style)'

[time]
disabled = false
time_format = "%R"
style = "bg:color_green"
format = '[[ ♥ $time ](bg:color_green)]($style)'

# ADHD energy indicator
[custom.adhd_energy]
disabled = false
command = "echo ${TMUX_ADHD_ENERGY:-medium} | tr '[:lower:]' '[:upper:]'"
when = true
style = "bg:color_purple"
format = '[[ ⚡ $output ](bg:color_purple)]($style)'

# Colors (Gruvbox-inspired)
[palette]
color_orange = "#fe8019"
color_yellow = "#fabd2f"
color_aqua = "#8ec07c"
color_blue = "#83a598"
color_green = "#b8bb26"
color_purple = "#d3869b"
color_bg3 = "#665c54"
EOF

    # Add Starship to shell profile
    if command -v zsh &> /dev/null; then
        if ! grep -q "starship init zsh" "$HOME/.zshrc" 2>/dev/null; then
            echo 'eval "$(starship init zsh)"' >> "$HOME/.zshrc"
        fi
    fi

    if command -v bash &> /dev/null; then
        if ! grep -q "starship init bash" "$HOME/.bashrc" 2>/dev/null; then
            echo 'eval "$(starship init bash)"' >> "$HOME/.bashrc"
        fi
    fi

    log_success "Starship configured"
}

# Configure tmux
configure_tmux() {
    if ! command -v tmux &> /dev/null; then
        log_warn "Tmux not installed - skipping configuration"
        return
    fi

    log_info "Configuring tmux..."

    # Create ADHD-optimized .tmux.conf
    cat > "$HOME/.tmux.conf" << 'EOF'
# Dopemux ADHD-optimized tmux config
set -g default-terminal "screen-256color"
set -g history-limit 10000
set -g status-interval 10

# ADHD energy indicators in status bar
set -g status-left "#[bg=colour4,fg=colour15] #S #[bg=colour0,fg=colour4]#{?TMUX_ADHD_ENERGY, 🟢#{TMUX_ADHD_ENERGY}, ⚠️unknown} "
set -g status-right "#[bg=colour0,fg=colour3] Load: #{TMUX_ADHD_LOAD:-N/A} Dec: #{TMUX_CONPORT_DECISIONS:-0} #[bg=colour4,fg=colour15] #{TMUX_MODEL:-Model} (#{TMUX_CTX:-Ctx}) 🧠"

# Colors (Gruvbox-inspired)
set -g status-style bg=colour0,fg=colour7
setw -g window-status-style fg=colour4
setw -g window-status-current-style bg=colour4,fg=colour15,bold

# ADHD-friendly keybindings
bind-key r source-file ~/.tmux.conf \; display-message "Config reloaded"
bind-key h split-window -h
bind-key v split-window -v
bind-key x kill-pane
bind-key & kill-window

# Mouse support for ADHD workflow flexibility
set -g mouse on
EOF

    log_success "Tmux configured"
}

# Configure statusline
configure_statusline() {
    show_progress "Configuring statusline..."

    # Create .claude directory if it doesn't exist
    mkdir -p "$HOME/.claude"

    # Configure statusline command
    cat > "$HOME/.claude/settings.json" << EOF
{
  "statusline": {
    "command": "bash $PROJECT_ROOT/.claude/statusline.sh"
  }
}
EOF

    log_success "Statusline configured"
}

# Run tests to verify installation
verify_installation() {
    show_progress "Verifying installation..."

    local failed_services=()

    # Check Docker services
    log_info "Checking Docker services..."
    if ! docker ps | grep -q postgres; then
        failed_services+=("PostgreSQL")
    fi
    if ! docker ps | grep -q redis; then
        failed_services+=("Redis")
    fi
    if ! docker ps | grep -q qdrant; then
        failed_services+=("Qdrant")
    fi

    # Check web services
    log_info "Checking web services..."
    if ! curl -f http://localhost:8095/health &> /dev/null; then
        failed_services+=("ADHD Engine")
    fi

    # Check MCP services
    log_info "Checking MCP services..."
    if ! curl -f http://localhost:3004/health &> /dev/null; then
        failed_services+=("ConPort")
    fi

    # Run security tests
    log_info "Running security tests..."
    if python -m pytest tests/security/ -x -q --tb=line | grep -q "FAILED\|ERROR"; then
        log_warn "Some security tests failed - check logs for details"
    else
        log_success "Security tests passed"
    fi

    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "The following services failed to start: ${failed_services[*]}"
        log_info "You may need to restart them manually:"
        echo "  docker-compose -f docker-compose.unified.yml restart"
        echo "  ./scripts/start-all.sh"
    else
        log_success "All services verified successfully"
    fi
}

# Show completion message
show_completion() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    🎉 INSTALLATION COMPLETE!                  ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Dopemux has been successfully installed!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Start your development session:"
    echo -e "   ${CYAN}dopemux start${NC}"
    echo ""
    echo "2. Check system status:"
    echo -e "   ${CYAN}dopemux status${NC}"
    echo ""
    echo "3. Your statusline should show real-time information"
    echo ""
    echo -e "${YELLOW}Key features now available:${NC}"
    echo "• 🧠 ADHD Engine - Energy tracking, break suggestions"
    echo "• 📊 ConPort - Knowledge graphs, decision logging"
    echo "• 🔍 Dope-Context - Semantic code and docs search"
    echo "• 🤖 Task Orchestrator - ADHD-aware task management"
    echo "• 📈 Real-time statusline with cognitive metrics"
    echo ""
    echo -e "${YELLOW}Documentation:${NC}"
    echo "• Quick start: README.md"
    echo "• Full docs: docs/INDEX.md"
    echo "• Troubleshooting: dopemux doctor"
    echo ""
    if [[ -f "$PROJECT_ROOT/.backup_location" ]]; then
        local backup_loc
        backup_loc=$(cat "$PROJECT_ROOT/.backup_location")
        echo -e "${YELLOW}Backup location:${NC} $backup_loc"
        echo ""
    fi
    echo -e "${GREEN}Happy coding! 🚀${NC}"
}

# Main installation function
main() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  🚀 Dopemux Installer - ADHD-Optimized Development Platform ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ $VERIFY_MODE == true ]]; then
        verify_installation
        exit 0
    fi

    if [[ $SKIP_CONFIRM == false ]]; then
        echo "This will install Dopemux on your system."
        if [[ $QUICK_MODE == true ]]; then
            echo "Quick mode: Core services only (faster setup)"
        elif [[ $FULL_MODE == true ]]; then
            echo "Full mode: Complete installation (all services)"
        else
            echo "Interactive mode: Choose your installation type"
        fi
        echo ""
        read -p "Continue with installation? (y/N) " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            exit 0
        fi
    fi

    # Determine installation mode interactively if not specified
    # If --no-docker is used, default to quick mode (CLI tools only)
    if [[ $NO_DOCKER_MODE == true && $QUICK_MODE == false && $FULL_MODE == false ]]; then
        QUICK_MODE=true
        log_info "Auto-selected Quick mode (--no-docker enables CLI tools only)"
    fi

    if [[ $QUICK_MODE == false && $FULL_MODE == false ]]; then
        echo ""
        echo "Choose installation mode:"
        echo "1) Quick Setup - Core services only (recommended for first-time users)"
        echo "2) Full Setup - All services and MCP servers (advanced users)"
        echo ""
        read -p "Enter choice (1 or 2): " -r
        if [[ $REPLY == "1" ]]; then
            QUICK_MODE=true
        elif [[ $REPLY == "2" ]]; then
            FULL_MODE=true
        else
            log_error "Invalid choice. Please run again."
            exit 1
        fi
    fi

    check_root
    check_prerequisites
    backup_existing
    install_docker_services
    install_mcp_servers
    install_claude_router
    initialize_services
    configure_statusline

    if [[ $FULL_MODE == true ]]; then
        verify_installation
    fi

    show_completion
}

# Handle errors
trap 'echo -e "\n${RED}Installation failed! Check install.log for details.${NC}"' ERR

# Run main function

# Run main function
main "$@"
