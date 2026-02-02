#!/bin/bash
# ADHD Integration Installer
# One-command setup for all ADHD Engine integrations
#
# Usage:
#   ./install-adhd-integration.sh
#
# What it does:
#   1. Symlinks shell aliases to ~/.adhd-aliases
#   2. Adds source line to ~/.zshrc
#   3. Symlinks tmux config to ~/.adhd-tmux.conf
#   4. Adds source-file to ~/.tmux.conf
#   5. Installs git hooks to current repo
#   6. Copies tmux status script to ~/.dopemux/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOPEMUX_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ADHD_ENGINE="$DOPEMUX_ROOT/services/adhd_engine"
DOTFILES="$DOPEMUX_ROOT/dotfiles/adhd"

# Colors
GREEN='\033[32m'
YELLOW='\033[33m'
CYAN='\033[36m'
RESET='\033[0m'

echo -e "${CYAN}🧠 ADHD Engine Integration Installer${RESET}"
echo "========================================"
echo ""

# ───────────────────────────────────────────────────────────────
# 1. Shell Aliases
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[1/6]${RESET} Setting up shell aliases..."

if [ -f "$DOTFILES/.adhd-aliases" ]; then
    ln -sf "$DOTFILES/.adhd-aliases" ~/.adhd-aliases
    echo "  ✅ Symlinked ~/.adhd-aliases"
    
    # Add to .zshrc if not already present
    if [ -f ~/.zshrc ]; then
        if ! grep -q "source ~/.adhd-aliases" ~/.zshrc; then
            echo "" >> ~/.zshrc
            echo "# ADHD Engine aliases" >> ~/.zshrc
            echo "[ -f ~/.adhd-aliases ] && source ~/.adhd-aliases" >> ~/.zshrc
            echo "  ✅ Added source line to ~/.zshrc"
        else
            echo "  ℹ️  Already in ~/.zshrc"
        fi
    fi
else
    echo "  ⚠️  No aliases file found at $DOTFILES/.adhd-aliases"
fi

# ───────────────────────────────────────────────────────────────
# 2. Tmux Configuration
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[2/6]${RESET} Setting up tmux configuration..."

if [ -f "$DOTFILES/.adhd-tmux.conf" ]; then
    ln -sf "$DOTFILES/.adhd-tmux.conf" ~/.adhd-tmux.conf
    echo "  ✅ Symlinked ~/.adhd-tmux.conf"
    
    # Add to .tmux.conf if not already present
    if [ -f ~/.tmux.conf ]; then
        if ! grep -q "source-file ~/.adhd-tmux.conf" ~/.tmux.conf; then
            echo "" >> ~/.tmux.conf
            echo "# ADHD Engine integration" >> ~/.tmux.conf
            echo "source-file ~/.adhd-tmux.conf" >> ~/.tmux.conf
            echo "  ✅ Added source-file to ~/.tmux.conf"
        else
            echo "  ℹ️  Already in ~/.tmux.conf"
        fi
    else
        echo "  ⚠️  No ~/.tmux.conf found, creating one"
        echo "source-file ~/.adhd-tmux.conf" > ~/.tmux.conf
    fi
else
    echo "  ⚠️  No tmux config found at $DOTFILES/.adhd-tmux.conf"
fi

# ───────────────────────────────────────────────────────────────
# 3. Tmux Status Script
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[3/6]${RESET} Installing tmux status script..."

mkdir -p ~/.dopemux
if [ -f "$ADHD_ENGINE/scripts/adhd-tmux-status.sh" ]; then
    cp "$ADHD_ENGINE/scripts/adhd-tmux-status.sh" ~/.dopemux/adhd-tmux-status.sh
    chmod +x ~/.dopemux/adhd-tmux-status.sh
    echo "  ✅ Installed ~/.dopemux/adhd-tmux-status.sh"
else
    echo "  ⚠️  Status script not found"
fi

# ───────────────────────────────────────────────────────────────
# 4. Git Hooks
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[4/6]${RESET} Installing git hooks..."

if [ -d .git ]; then
    if [ -f "$ADHD_ENGINE/hooks/git-post-commit" ]; then
        cp "$ADHD_ENGINE/hooks/git-post-commit" .git/hooks/post-commit
        chmod +x .git/hooks/post-commit
        echo "  ✅ Installed .git/hooks/post-commit"
    fi
    
    if [ -f "$ADHD_ENGINE/hooks/git-pre-push" ]; then
        cp "$ADHD_ENGINE/hooks/git-pre-push" .git/hooks/pre-push
        chmod +x .git/hooks/pre-push
        echo "  ✅ Installed .git/hooks/pre-push"
    fi
else
    echo "  ⚠️  Not in a git repository, skipping hooks"
fi

# ───────────────────────────────────────────────────────────────
# 5. CLI in PATH
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[5/6]${RESET} Setting up CLI..."

ADHD_CLI="$ADHD_ENGINE/cli/adhd.py"
if [ -f "$ADHD_CLI" ]; then
    chmod +x "$ADHD_CLI"
    echo "  ✅ CLI ready at: $ADHD_CLI"
    echo "  💡 Alias 'adhd' is available after sourcing ~/.adhd-aliases"
else
    echo "  ⚠️  CLI not found at $ADHD_CLI"
fi

# ───────────────────────────────────────────────────────────────
# 6. Reload tmux if running
# ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[6/6]${RESET} Reloading tmux configuration..."

if command -v tmux &> /dev/null && tmux list-sessions &> /dev/null; then
    tmux source-file ~/.tmux.conf 2>/dev/null || true
    echo "  ✅ Tmux configuration reloaded"
else
    echo "  ℹ️  Tmux not running, will apply on next session"
fi

# ───────────────────────────────────────────────────────────────
# Done
# ───────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}✅ Installation complete!${RESET}"
echo ""
echo "Next steps:"
echo "  1. Reload your shell:  source ~/.zshrc"
echo "  2. Check status:       adhd status"
echo "  3. Tmux bindings:      Prefix + a (status), Prefix + b (break)"
echo ""
echo -e "${YELLOW}🧠 Remember: You've got this!${RESET}"
