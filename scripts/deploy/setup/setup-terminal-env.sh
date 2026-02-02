#!/bin/bash
#
# Dopemux Terminal Environment Installer
# Sets up an ADHD-optimized terminal environment with:
# - Modern terminal emulator (Kitty or Alacritty)
# - Fast shell (zsh with oh-my-zsh)
# - Beautiful prompt (Starship)
# - Productivity tools (fzf, ripgrep, bat, eza)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji for ADHD-friendly visual feedback
INFO="ℹ️ "
SUCCESS="✅"
WARNING="⚠️ "
ERROR="❌"
ROCKET="🚀"

# Configuration
DOPEMUX_HOME="${HOME}/.dopemux"
CONFIG_DIR="${DOPEMUX_HOME}/terminal-configs"

# Logging
log() {
    echo -e "${CYAN}${INFO}${NC} $1"
}

success() {
    echo -e "${GREEN}${SUCCESS}${NC} $1"
}

warning() {
    echo -e "${YELLOW}${WARNING}${NC} $1"
}

error() {
    echo -e "${RED}${ERROR}${NC} $1"
}

heading() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "========================================"
}

# Detect OS and package manager
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MGR="brew"
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS="${ID}"
        if command -v apt-get &> /dev/null; then
            PKG_MGR="apt"
        elif command -v pacman &> /dev/null; then
            PKG_MGR="pacman"
        elif command -v dnf &> /dev/null; then
            PKG_MGR="dnf"
        fi
    else
        error "Unsupported operating system"
        exit 1
    fi
    
    log "Detected: ${OS} with ${PKG_MGR}"
}

# Install package based on OS
install_package() {
    local package=$1
    local package_name=$2
    
    log "Installing ${package_name}..."
    
    case $PKG_MGR in
        brew)
            if ! brew list $package &>/dev/null; then
                brew install $package
            else
                log "${package_name} already installed"
            fi
            ;;
        apt)
            if ! dpkg -l | grep -q "^ii  $package "; then
                sudo apt update -qq
                sudo apt install -y $package
            else
                log "${package_name} already installed"
            fi
            ;;
        pacman)
            if ! pacman -Qi $package &>/dev/null; then
                sudo pacman -S --noconfirm $package
            else
                log "${package_name} already installed"
            fi
            ;;
        dnf)
            if ! rpm -q $package &>/dev/null; then
                sudo dnf install -y $package
            else
                log "${package_name} already installed"
            fi
            ;;
    esac
}

# Install Kitty terminal
install_kitty() {
    heading "Installing Kitty Terminal"
    
    if command -v kitty &> /dev/null; then
        success "Kitty already installed"
        return 0
    fi
    
    case $OS in
        macos)
            install_package "kitty" "Kitty"
            ;;
        ubuntu|debian)
            log "Installing Kitty from official installer..."
            curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
            
            # Create desktop shortcut
            ln -sf ~/.local/kitty.app/bin/kitty ~/.local/bin/
            cp ~/.local/kitty.app/share/applications/kitty.desktop ~/.local/share/applications/
            
            # Update icon path
            sed -i "s|Icon=kitty|Icon=/home/$USER/.local/kitty.app/share/icons/hicolor/256x256/apps/kitty.png|g" \
                ~/.local/share/applications/kitty*.desktop
            ;;
        arch)
            install_package "kitty" "Kitty"
            ;;
        fedora)
            install_package "kitty" "Kitty"
            ;;
    esac
    
    success "Kitty installed"
}

# Install zsh
install_zsh() {
    heading "Installing zsh"
    
    if command -v zsh &> /dev/null; then
        success "zsh already installed"
    else
        install_package "zsh" "zsh"
    fi
    
    # Set zsh as default shell
    if [[ "$SHELL" != *"zsh"* ]]; then
        log "Setting zsh as default shell..."
        chsh -s $(which zsh)
        success "zsh set as default shell (will take effect on next login)"
    fi
}

# Install oh-my-zsh
install_oh_my_zsh() {
    heading "Installing Oh My Zsh"
    
    if [[ -d "${HOME}/.oh-my-zsh" ]]; then
        success "Oh My Zsh already installed"
        return 0
    fi
    
    log "Installing Oh My Zsh..."
    RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    
    # Install popular plugins
    log "Installing zsh plugins..."
    
    # zsh-autosuggestions
    if [[ ! -d "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions" ]]; then
        git clone https://github.com/zsh-users/zsh-autosuggestions \
            ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
    fi
    
    # zsh-syntax-highlighting
    if [[ ! -d "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting" ]]; then
        git clone https://github.com/zsh-users/zsh-syntax-highlighting \
            ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
    fi
    
    success "Oh My Zsh and plugins installed"
}

# Install Starship prompt
install_starship() {
    heading "Installing Starship Prompt"
    
    if command -v starship &> /dev/null; then
        success "Starship already installed"
        return 0
    fi
    
    case $OS in
        macos)
            install_package "starship" "Starship"
            ;;
        *)
            log "Installing Starship from official installer..."
            curl -sS https://starship.rs/install.sh | sh -s -- -y
            ;;
    esac
    
    success "Starship installed"
}

# Install productivity CLI tools
install_cli_tools() {
    heading "Installing Productivity CLI Tools"
    
    # fzf - fuzzy finder
    if ! command -v fzf &> /dev/null; then
        log "Installing fzf..."
        install_package "fzf" "fzf"
    else
        success "fzf already installed"
    fi
    
    # ripgrep - fast grep
    if ! command -v rg &> /dev/null; then
        log "Installing ripgrep..."
        install_package "ripgrep" "ripgrep"
    else
        success "ripgrep already installed"
    fi
    
    # bat - better cat
    if ! command -v bat &> /dev/null && ! command -v batcat &> /dev/null; then
        log "Installing bat..."
        install_package "bat" "bat"
    else
        success "bat already installed"
    fi
    
    # eza - better ls (formerly exa)
    if ! command -v eza &> /dev/null; then
        log "Installing eza..."
        case $OS in
            macos)
                install_package "eza" "eza"
                ;;
            ubuntu|debian)
                # eza requires manual installation on Ubuntu
                if ! command -v cargo &> /dev/null; then
                    log "Installing Rust (required for eza)..."
                    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
                    source "$HOME/.cargo/env"
                fi
                cargo install eza
                ;;
            arch)
                install_package "eza" "eza"
                ;;
            fedora)
                install_package "eza" "eza"
                ;;
        esac
    else
        success "eza already installed"
    fi
    
    # fd - better find
    if ! command -v fd &> /dev/null; then
        log "Installing fd..."
        install_package "fd" "fd"
    else
        success "fd already installed"
    fi
    
    success "Productivity tools installed"
}

# Create Kitty configuration
configure_kitty() {
    heading "Configuring Kitty"
    
    mkdir -p "${HOME}/.config/kitty"
    
    cat > "${HOME}/.config/kitty/kitty.conf" << 'EOF'
# Dopemux ADHD-Optimized Kitty Configuration

# Font Configuration
font_family      JetBrains Mono
bold_font        JetBrains Mono Bold
italic_font      JetBrains Mono Italic
bold_italic_font JetBrains Mono Bold Italic
font_size 13.0

# Reduce visual noise
cursor_blink_interval 0
window_padding_width 10

# ADHD-friendly color scheme (reduced eye strain)
foreground #d8d8d8
background #1e1e1e
cursor #d8d8d8

# Black
color0 #1e1e1e
color8 #545454

# Red
color1 #f92672
color9 #f92672

# Green
color2  #a6e22e
color10 #a6e22e

# Yellow
color3  #e6db74
color11 #e6db74

# Blue
color4  #66d9ef
color12 #66d9ef

# Magenta
color5  #ae81ff
color13 #ae81ff

# Cyan
color6  #a1efe4
color14 #a1efe4

# White
color7  #f8f8f2
color15 #f9f8f5

# Tab bar
tab_bar_edge top
tab_bar_style powerline
tab_powerline_style slanted

# Layouts
enabled_layouts splits,stack

# Keyboard shortcuts for ADHD workflow
map ctrl+shift+enter launch --cwd=current
map ctrl+shift+t new_tab_with_cwd
map ctrl+shift+w close_tab

# Split windows
map ctrl+shift+- launch --location=hsplit --cwd=current
map ctrl+shift+\ launch --location=vsplit --cwd=current

# Navigate splits
map ctrl+shift+left neighboring_window left
map ctrl+shift+right neighboring_window right
map ctrl+shift+up neighboring_window up
map ctrl+shift+down neighboring_window down

# Copy/paste
map ctrl+shift+c copy_to_clipboard
map ctrl+shift+v paste_from_clipboard

# Performance
repaint_delay 10
input_delay 3
sync_to_monitor yes
EOF
    
    success "Kitty configured"
}

# Create Starship configuration
configure_starship() {
    heading "Configuring Starship"
    
    mkdir -p "${HOME}/.config"
    
    cat > "${HOME}/.config/starship.toml" << 'EOF'
# Dopemux ADHD-Optimized Starship Configuration
# Fast, minimal, informative

# Reduce prompt latency for ADHD focus
command_timeout = 500

# Format: simplified for reduced cognitive load
format = """
[╭─](bold blue)$directory$git_branch$git_status
[╰─](bold blue)$character"""

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"
vicmd_symbol = "[❮](bold yellow)"

[directory]
truncation_length = 3
truncate_to_repo = true
style = "bold cyan"
format = "[$path]($style) "

[git_branch]
symbol = " "
style = "bold purple"
format = "[$symbol$branch]($style) "

[git_status]
style = "bold yellow"
format = "[$all_status$ahead_behind]($style) "
conflicted = "⚠️ "
ahead = "⇡${count} "
behind = "⇣${count} "
diverged = "⇕⇡${ahead_count}⇣${behind_count} "
untracked = "?${count} "
stashed = "📦 "
modified = "!${count} "
staged = "+${count} "
renamed = "»${count} "
deleted = "✘${count} "

# Hide unless in specific context (reduce noise)
[python]
format = "[$symbol$pyenv_prefix($version )]($style)"
symbol = "🐍 "
disabled = false

[nodejs]
format = "[$symbol($version )]($style)"
symbol = " "
disabled = false

[rust]
format = "[$symbol($version )]($style)"
symbol = "🦀 "
disabled = false

# Fast execution time display
[cmd_duration]
min_time = 500
format = "[$duration](bold yellow) "
disabled = false

# Battery for laptops (ADHD reminder to charge)
[battery]
full_symbol = "🔋"
charging_symbol = "⚡"
discharging_symbol = "💀"
disabled = false

[[battery.display]]
threshold = 20
style = "bold red"

[[battery.display]]
threshold = 50
style = "bold yellow"
EOF
    
    success "Starship configured"
}

# Configure zsh
configure_zsh() {
    heading "Configuring zsh"
    
    # Backup existing .zshrc
    if [[ -f "${HOME}/.zshrc" ]]; then
        cp "${HOME}/.zshrc" "${HOME}/.zshrc.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    cat > "${HOME}/.zshrc.ultimate" << 'EOF'
# Dopemux ADHD-Optimized zsh Configuration
# Path to oh-my-zsh installation
export ZSH="$HOME/.oh-my-zsh"

# Reduce startup time
ZSH_DISABLE_COMPFIX=true

# Plugins (ADHD-friendly: useful without overwhelming)
plugins=(
    git
    docker
    zsh-autosuggestions
    zsh-syntax-highlighting
    fzf
)

source $ZSH/oh-my-zsh.sh

# Initialize Starship prompt
eval "$(starship init zsh)"

# ADHD-friendly aliases
alias ls='eza --icons --group-directories-first'
alias ll='eza -l --icons --group-directories-first'
alias la='eza -la --icons --group-directories-first'
alias lt='eza --tree --level=2 --icons'

# Better cat
if command -v bat &> /dev/null; then
    alias cat='bat --style=plain --paging=never'
elif command -v batcat &> /dev/null; then
    alias cat='batcat --style=plain --paging=never'
fi

# Git aliases for quick context switching (ADHD-friendly)
alias gs='git status'
alias ga='git add'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --decorate -10'
alias gd='git diff'

# Quick navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# Dopemux shortcuts
alias dm='dopemux'
alias dms='dopemux start'
alias dmi='dopemux init'
alias dmd='dopemux doctor'

# FZF configuration (ADHD-optimized colors)
export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border --preview 'bat --style=numbers --color=always {}' --preview-window=right:60%"
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'

# History configuration (ADHD-friendly: easy to search back)
HISTSIZE=10000
SAVEHIST=10000
setopt EXTENDED_HISTORY
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS

# Auto-suggestions configuration
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=8'
ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# Key bindings for ADHD workflow
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward
bindkey '^R' fzf-history-widget

# Dopemux environment
export DOPEMUX_HOME="$HOME/.dopemux"
export PATH="$DOPEMUX_HOME/bin:$PATH"

# Fast directory jumping with 'z'
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
    alias cd='z'
fi

# Welcome message (can be disabled if too distracting)
echo "🧠 Dopemux terminal ready! Type 'dm' for dopemux commands."
EOF

    # Ensure ~/.zshrc sources .zshrc.ultimate (non-destructive)
    if ! grep -q 'source "$HOME/.zshrc.ultimate"' "${HOME}/.zshrc" 2>/dev/null; then
        echo -e '\n# Dopemux Terminal Setup\nif [ -f "$HOME/.zshrc.ultimate" ]; then\n  source "$HOME/.zshrc.ultimate"\nfi' >> "${HOME}/.zshrc"
    fi

    success "zsh configured"
}

# Install additional ADHD-friendly tools
install_adhd_tools() {
    heading "Installing ADHD-Friendly Tools"
    
    # zoxide - smarter cd
    if ! command -v zoxide &> /dev/null; then
        log "Installing zoxide (smart directory jumping)..."
        case $OS in
            macos)
                install_package "zoxide" "zoxide"
                ;;
            *)
                curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash
                ;;
        esac
    else
        success "zoxide already installed"
    fi
    
    # tldr - simplified man pages
    if ! command -v tldr &> /dev/null; then
        log "Installing tldr (simplified man pages)..."
        install_package "tldr" "tldr"
    else
        success "tldr already installed"
    fi
    
    success "ADHD tools installed"
}

# Main installation flow
main() {
    clear
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════╗
║                                                   ║
║   🧠 Dopemux Terminal Environment Setup 🚀        ║
║                                                   ║
║   ADHD-optimized terminal for focused coding     ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    log "This will install and configure:"
    echo "  • Kitty terminal (GPU-accelerated)"
    echo "  • zsh with Oh My Zsh"
    echo "  • Starship prompt (fast & beautiful)"
    echo "  • CLI productivity tools (fzf, ripgrep, bat, eza)"
    echo "  • ADHD-optimized configurations"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Installation cancelled"
        exit 0
    fi
    
    detect_platform
    
    install_kitty
    install_zsh
    install_oh_my_zsh
    install_starship
    install_cli_tools
    install_adhd_tools
    
    configure_kitty
    configure_starship
    configure_zsh
    
    echo ""
    heading "Installation Complete!"
    echo ""
    success "Terminal environment setup complete!"
    echo ""
    log "Next steps:"
    echo "  1. Restart your terminal (or run: exec zsh)"
    echo "  2. Open Kitty terminal (if you want to use it)"
    echo "  3. Enjoy your ADHD-optimized development environment!"
    echo ""
    warning "Note: Shell changes take effect on next login"
    echo ""
    log "Quick tips:"
    echo "  • Use 'dm' as shortcut for 'dopemux'"
    echo "  • Press Ctrl+R to search command history with fzf"
    echo "  • Use 'z <directory>' to jump to frequent directories"
    echo "  • Type 'tldr <command>' for quick command help"
    echo ""
    success "${ROCKET} Happy coding!"
}

# Run main installation
main "$@"
