#!/bin/bash
set -e

echo "=== Git Worktree and Branch Consolidation ==="
echo "Starting from: $(pwd)"

# Store original branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Original branch: $ORIGINAL_BRANCH"

# Ensure we're on main
if [ "$ORIGINAL_BRANCH" != "main" ]; then
    echo "Switching to main branch..."
    git checkout main
fi

# Pull latest main to minimize conflicts
echo "Pulling latest main..."
git pull upstream main || echo "Pull failed, continuing anyway"

# Function to merge a branch safely
merge_branch() {
    local branch_name="$1"
    echo ""
    echo "=== Processing branch: $branch_name ==="
    
    # Check if branch exists
    if ! git show-ref --verify --quiet "refs/heads/$branch_name"; then
        echo "Branch $branch_name does not exist locally, skipping..."
        return 0
    fi
    
    # Checkout the branch
    git checkout "$branch_name"
    
    # Check for uncommitted changes
    if ! git diff --quiet; then
        echo "WARNING: Branch $branch_name has uncommitted changes!"
        git stash push -m "uncommitted-changes-$branch_name"
    fi
    
    # Checkout main and merge
    git checkout main
    
    # Try merge
    if git merge --no-ff --no-commit "$branch_name"; then
        echo "Merge successful, committing..."
        git commit -m "Merge branch '$branch_name' into main"
    else
        echo "Merge conflict detected!"
        git merge --abort
        echo "Aborting merge of $branch_name due to conflicts"
        return 1
    fi
    
    return 0
}

# Function to process stashes
process_stashes() {
    echo ""
    echo "=== Processing stashes ==="
    
    local stash_count=$(git stash list | wc -l)
    if [ "$stash_count" -eq 0 ]; then
        echo "No stashes found"
        return 0
    fi
    
    echo "Found $stash_count stashes to process"
    
    # Process stashes in reverse order (oldest first)
    for i in $(seq 0 $((stash_count-1)) | tac); do
        echo ""
        echo "Processing stash@{$i}..."
        
        # Show what's in the stash
        git stash show -p "stash@{$i}" | head -20
        
        # Apply the stash
        if git stash apply "stash@{$i}"; then
            echo "Stash applied successfully"
            
            # Check if there are changes to commit
            if ! git diff --quiet; then
                echo "Committing stash changes..."
                git add .
                git commit -m "Recover stashed work: $(git stash list --format=%gd --reverse | sed -n "$((i+1))p")"
            else
                echo "No changes after applying stash"
            fi
            
            # Drop the stash
            git stash drop "stash@{$i}"
        else
            echo "ERROR: Failed to apply stash@{$i}"
            # Try to drop it anyway
            git stash drop "stash@{$i}" || true
        fi
    done
}

# Main consolidation loop
BRANCHES_TO_MERGE=(
    "codex/tp-pro-prompts-v1"
    "codex/dopemux-kernel-mvp" 
    "feature/new-worktree"
    "tp-vibe-mcp-truth-lockdown"
)

for branch in "${BRANCHES_TO_MERGE[@]}"; do
    merge_branch "$branch" || echo "Failed to merge $branch, continuing..."
done

# Process stashes
process_stashes

# Clean up: delete merged branches
echo ""
echo "=== Cleaning up merged branches ==="
for branch in "${BRANCHES_TO_MERGE[@]}"; do
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        echo "Deleting branch $branch..."
        git branch -D "$branch" || echo "Failed to delete $branch"
    fi
done

# Remove worktrees
echo ""
echo "=== Removing worktrees ==="
git worktree list | grep -v "^\[main\]" | awk '{print $1}' | while read -r worktree_path; do
    if [ -d "$worktree_path" ]; then
        echo "Removing worktree: $worktree_path"
        git worktree remove "$worktree_path" || echo "Failed to remove worktree"
    fi
done

# Return to original branch
echo ""
echo "Returning to original branch: $ORIGINAL_BRANCH"
git checkout "$ORIGINAL_BRANCH"

echo ""
echo "=== Consolidation Complete ==="
echo "Summary:"
echo "- Processed ${#BRANCHES_TO_MERGE[@]} branches"
echo "- Processed $stash_count stashes (if any)"
echo "- Cleaned up worktrees"
echo ""
echo "Current status:"
git status -sb
git log --oneline -5
