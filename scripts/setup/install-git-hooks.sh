#!/bin/bash
#
# Install Git Hooks for ADHD Activity Tracking
#
# Copies post-commit hook to .git/hooks/ for automatic commit tracking.
# Run this once per repository to enable git commit activity tracking.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Installing ADHD activity tracking git hooks..."
echo ""

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "ERROR: Not a git repository ($PROJECT_ROOT)"
    exit 1
fi

# Copy post-commit hook
echo "Installing post-commit hook..."
cp "$SCRIPT_DIR/git-hooks/post-commit" "$PROJECT_ROOT/.git/hooks/post-commit"
chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"
echo "✅ post-commit hook installed"

# Verify
if [ -x "$PROJECT_ROOT/.git/hooks/post-commit" ]; then
    echo "✅ Hook is executable"
else
    echo "⚠️  Hook not executable, fixing..."
    chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"
fi

echo ""
echo "=========================================="
echo "Git hooks installed successfully!"
echo "=========================================="
echo ""
echo "Now every commit will:"
echo "  1. Track commit metadata (hash, files, lines)"
echo "  2. Emit code.committed event to Activity Capture"
echo "  3. Log as high-productivity activity to ADHD Engine"
echo ""
echo "Make a commit to test it!"
echo ""
