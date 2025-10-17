#!/bin/bash
#
# Dopemux Shell Integration for Worktree Switching
#
# This script provides shell functions that enable proper worktree switching.
# Python subprocesses cannot change the parent shell's directory due to POSIX
# limitations, so we use shell functions that execute cd in the shell's context.
#
# Installation:
#   For Bash:
#     dopemux shell-setup bash >> ~/.bashrc
#     source ~/.bashrc
#
#   For Zsh:
#     dopemux shell-setup zsh >> ~/.zshrc
#     source ~/.zshrc
#
# Usage:
#   dwt <branch>          # Switch to worktree (fuzzy match supported)
#   dwt ui               # Matches "ui-build"
#   dwt feature          # Matches "feature/test-worktree-isolation"
#

# Detect shell type
DOPEMUX_SHELL_TYPE="${BASH_VERSION:+bash}${ZSH_VERSION:+zsh}"

#
# Main worktree switching function
#
dopemux_switch() {
    local branch_name="$1"

    if [ -z "$branch_name" ]; then
        echo "Usage: dopemux_switch <branch>"
        echo "       dwt <branch>  (alias)"
        return 1
    fi

    # Get target path from dopemux (with fuzzy matching)
    local target_path
    target_path=$(python -m dopemux worktrees switch-path "$branch_name" 2>/dev/null)
    local exit_code=$?

    if [ $exit_code -eq 0 ] && [ -n "$target_path" ] && [ -d "$target_path" ]; then
        # Successfully found worktree - switch to it
        cd "$target_path" || return 1

        # Visual confirmation
        echo "✅ Switched to worktree: $target_path"
        echo "   Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"

        # Update dopemux cache for MCP efficiency
        python -m dopemux worktrees current --no-cache > /dev/null 2>&1

        return 0
    else
        # Worktree not found
        echo "❌ Worktree not found: $branch_name"
        echo
        python -m dopemux worktrees list
        return 1
    fi
}

#
# Convenient alias for quick switching
#
alias dwt='dopemux_switch'

#
# Optional: Auto-completion for worktree names
#
if [ "$DOPEMUX_SHELL_TYPE" = "bash" ]; then
    _dopemux_switch_completions() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local branches
        branches=$(git worktree list 2>/dev/null | tail -n +1 | awk '{print $NF}' | tr -d '[]')
        COMPREPLY=($(compgen -W "$branches" -- "$cur"))
    }
    complete -F _dopemux_switch_completions dopemux_switch
    complete -F _dopemux_switch_completions dwt

elif [ "$DOPEMUX_SHELL_TYPE" = "zsh" ]; then
    _dopemux_switch_completions() {
        local branches
        branches=(${(f)"$(git worktree list 2>/dev/null | tail -n +1 | awk '{print $NF}' | tr -d '[]')"})
        _describe 'worktree branches' branches
    }
    compdef _dopemux_switch_completions dopemux_switch
    compdef _dopemux_switch_completions dwt
fi

#
# Additional helper: List worktrees quickly
#
alias dwtls='python -m dopemux worktrees list'

#
# Additional helper: Show current worktree
#
alias dwtcur='python -m dopemux worktrees current'

# Only show messages if running interactively (not in subshell)
if [ -t 1 ]; then
    echo "✅ Dopemux shell integration loaded!"
    echo "   Use: dwt <branch>  to switch worktrees"
    echo "   Use: dwtls         to list all worktrees"
    echo "   Use: dwtcur        to show current worktree"
fi
