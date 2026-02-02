#!/bin/bash
#
# Dopemux Shell Integration for Worktree Switching (PURE BASH - NO PYTHON!)
#
# Optimized for ADHD workflows with zero Python overhead:
# - 10-20ms switching (vs 500ms+ with Python)
# - No memory overhead (pure git commands)
# - Instant fuzzy matching
# - Works immediately after sourcing
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
#   dwt <pattern>         # Switch to worktree (fuzzy match)
#   dwt ui               # Matches "ui-build"
#   dwt feature          # Matches "feature/test-worktree-isolation"
#   dwtls                # List all worktrees (pure git)
#   dwtcur               # Show current worktree (pure git)
#

# Detect shell type
DOPEMUX_SHELL_TYPE="${BASH_VERSION:+bash}${ZSH_VERSION:+zsh}"

_dopemux_source_env_for_path() {
    local repo_path="$1"
    if [ -z "$repo_path" ]; then
        return
    fi
    local env_file="$repo_path/.dopemux/env/current.sh"
    if [ -f "$env_file" ]; then
        # shellcheck disable=SC1090
        source "$env_file"
    fi
}

#
# OPTIMIZED: Pure git-based worktree switching (NO PYTHON!)
#
dwt() {
    local pattern="$1"

    if [ -z "$pattern" ]; then
        echo "Usage: dwt <branch-pattern>"
        echo "Example: dwt ui (matches ui-build)"
        return 1
    fi

    # Pure git worktree list - FAST! (~10-20ms)
    local worktree_list
    worktree_list=$(git worktree list 2>/dev/null)

    if [ -z "$worktree_list" ]; then
        echo "❌ Not in a git repository"
        return 1
    fi

    # Fuzzy match: check branch name or path component
    # Priority: exact match > branch contains > path contains
    local target_path=""
    local match_type=""

    # Try exact branch match first
    while IFS= read -r line; do
        local branch=$(echo "$line" | awk '{print $NF}' | tr -d '[]')
        if [ "$branch" = "$pattern" ]; then
            target_path=$(echo "$line" | awk '{print $1}')
            match_type="exact"
            break
        fi
    done <<< "$worktree_list"

    # Try branch contains pattern
    if [ -z "$target_path" ]; then
        while IFS= read -r line; do
            local branch=$(echo "$line" | awk '{print $NF}' | tr -d '[]')
            if echo "$branch" | grep -iq "$pattern"; then
                target_path=$(echo "$line" | awk '{print $1}')
                match_type="branch"
                break
            fi
        done <<< "$worktree_list"
    fi

    # Try path contains pattern
    if [ -z "$target_path" ]; then
        while IFS= read -r line; do
            local path=$(echo "$line" | awk '{print $1}')
            if echo "$path" | grep -iq "$pattern"; then
                target_path="$path"
                match_type="path"
                break
            fi
        done <<< "$worktree_list"
    fi

    # Switch to found worktree
    if [ -n "$target_path" ] && [ -d "$target_path" ]; then
        cd "$target_path" || return 1
        _dopemux_source_env_for_path "$target_path"

        # Visual confirmation with ADHD-friendly output
        local current_branch
        current_branch=$(git branch --show-current 2>/dev/null || echo "detached")

        echo "✅ Switched to: $(basename "$target_path")"
        echo "   Path: $target_path"
        echo "   Branch: $current_branch"
        [ -n "$match_type" ] && echo "   Match: $match_type"

        return 0
    else
        # No match found
        echo "❌ No worktree matching: $pattern"
        echo
        echo "Available worktrees:"
        git worktree list
        return 1
    fi
}

#
# OPTIMIZED: Pure git worktree list (NO PYTHON!)
#
dwtls() {
    echo "📁 Git Worktrees:"
    git worktree list 2>/dev/null || echo "❌ Not in a git repository"
}

#
# OPTIMIZED: Pure git current worktree (NO PYTHON!)
#
dwtcur() {
    local current_path
    current_path=$(git rev-parse --show-toplevel 2>/dev/null)

    if [ -n "$current_path" ]; then
        local current_branch
        current_branch=$(git branch --show-current 2>/dev/null || echo "detached")

        echo "📍 Current worktree:"
        echo "   Path: $current_path"
        echo "   Name: $(basename "$current_path")"
        echo "   Branch: $current_branch"
    else
        echo "❌ Not in a git repository"
        return 1
    fi
}

#
# OPTIMIZED: Quick worktree creation (minimal Python)
#
dwtcreate() {
    local branch_name="$1"

    if [ -z "$branch_name" ]; then
        echo "Usage: dwtcreate <branch-name>"
        return 1
    fi

    # Get repo root (pure git)
    local repo_root
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null)

    if [ -z "$repo_root" ]; then
        echo "❌ Not in a git repository"
        return 1
    fi

    # Create worktree in ../worktree-name pattern
    local parent_dir=$(dirname "$repo_root")
    local worktree_path="$parent_dir/$(basename "$repo_root")-$branch_name"

    echo "Creating worktree: $worktree_path"

    if git worktree add "$worktree_path" -b "$branch_name"; then
        echo "✅ Created worktree: $worktree_path"
        echo "   Switching to it..."
        cd "$worktree_path" || return 1
        _dopemux_source_env_for_path "$worktree_path"
        echo "   Branch: $(git branch --show-current)"
    else
        echo "❌ Failed to create worktree"
        return 1
    fi
}

#
# ADHD Helper: Quick status overview
#
dwtstatus() {
    dwtcur
    echo
    dwtls
}

#
# Auto-completion for worktree names (performance optimized)
#
if [ "$DOPEMUX_SHELL_TYPE" = "bash" ]; then
    _dwt_completions() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local branches
        # Extract just branch names from git worktree list
        branches=$(git worktree list 2>/dev/null | awk '{print $NF}' | tr -d '[]' | grep -v HEAD)
        COMPREPLY=($(compgen -W "$branches" -- "$cur"))
    }
    complete -F _dwt_completions dwt
    complete -F _dwt_completions dopemux_switch

elif [ "$DOPEMUX_SHELL_TYPE" = "zsh" ]; then
    _dwt_completions() {
        local branches
        branches=(${(f)"$(git worktree list 2>/dev/null | awk '{print $NF}' | tr -d '[]' | grep -v HEAD)"})
        _describe 'worktree branches' branches
    }
    compdef _dwt_completions dwt
    compdef _dwt_completions dopemux_switch
fi

# Only show welcome message in interactive shells
if [ -t 1 ]; then
    echo "✅ Dopemux shell integration loaded! (Pure bash - zero Python overhead)"
    echo "   dwt <branch>   → Switch worktrees (10-20ms!)"
    echo "   dwtls          → List worktrees"
    echo "   dwtcur         → Current worktree"
    echo "   dwtcreate      → Create new worktree"
    echo "   dwtstatus      → Full status overview"
fi
