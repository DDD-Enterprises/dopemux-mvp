Quick commit and PR creation for completed implementations (with quality verification).

## Quick Quality Check
```bash
# Essential checks (run automatically)
python -m pytest --cov=src/chatx --cov-fail-under=90 --tb=short
ruff check .
mypy src
```

## Automated Commit + PR Flow

### 1. Feature Branch Creation
```bash
# Auto-create feature branch if not already on one
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ]; then
  TIMESTAMP=$(date +%s)
  git checkout -b "feature/impl-$TIMESTAMP"
  echo "Created feature branch: feature/impl-$TIMESTAMP"
fi
```

### 2. Quality Verification
```bash
# Run essential checks
echo "🔍 Running quality checks..."

# Tests with coverage
if ! pytest --cov=src/chatx --cov-fail-under=90 --tb=short; then
  echo "❌ Tests failed - fix issues before committing"
  exit 1
fi

# Lint check
if ! ruff check .; then
  echo "❌ Linting failed - fix style issues"
  exit 1
fi

# Type check
if ! mypy src; then
  echo "❌ Type checking failed - fix type errors"
  exit 1
fi

echo "✅ All quality gates passed!"
```

### 3. Conventional Commit
```bash
# Auto-generate commit message
FILES_CHANGED=$(git diff --cached --name-only | wc -l)
TEST_FILES=$(git diff --cached --name-only | grep -c "test")

# Determine commit type
if [ $TEST_FILES -gt $((FILES_CHANGED / 2)) ]; then
  TYPE="test"
elif git diff --cached --name-only | grep -q "README\|docs"; then
  TYPE="docs"
else
  TYPE="feat"
fi

# Generate scope from changed files
SCOPE=$(git diff --cached --name-only | head -1 | sed 's/.*\///' | sed 's/\..*//')

# Create commit
git commit -m "$TYPE($SCOPE): implement feature

- Quality gates: ✅ tests, ✅ lint, ✅ types, ✅ coverage ≥90%
- Files changed: $FILES_CHANGED
- Test files: $TEST_FILES

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4. Push and PR Creation
```bash
# Push branch
BRANCH=$(git branch --show-current)
git push -u origin "$BRANCH"

# Create PR with quality status
gh pr create \
  --title "$TYPE($SCOPE): implement feature" \
  --body "## Implementation Complete

### Quality Gates ✅
- **Tests**: All passing with ≥90% coverage
- **Lint**: Clean (ruff)
- **Types**: Clean (mypy)
- **Files**: $FILES_CHANGED modified

### Changes
$(git log --oneline -1 | cut -d' ' -f2-)

### Ready for Review
- Feature branch: $BRANCH
- Conventional commit format
- Quality gates verified

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>" \
  --label "enhancement"

# Output PR URL for monitoring
echo "📋 PR created and ready for review"
```

## Usage Patterns

### Quick Complete (Automated)
```bash
# From any implementation, just run:
/commit-pr
# → Auto quality check → feature branch → commit → push → PR
```

### With TaskMaster Integration
```bash
# Mark task complete and create PR
task-master set-status --id=1.2 --status=done
/commit-pr
```

### Multi-Session Support
```bash
# Each session gets its own branch
# Session 1: git checkout -b feature/auth-impl-001
# Session 2: git checkout -b feature/payment-impl-002
/commit-pr  # Each creates its own PR independently
```

## What This Handles

✅ **Quality Verification**: Auto-runs tests, lint, types, coverage
✅ **Feature Branches**: Auto-creates if on main
✅ **Conventional Commits**: Auto-generates proper format
✅ **PR Creation**: Detailed PR with quality status
✅ **Multi-Session**: Branch isolation maintained
✅ **Integration**: Works with TaskMaster task completion

## Error Handling

- **Tests Fail**: Stops process, shows error details
- **Lint/Type Errors**: Stops process, shows violations
- **No Changes**: Warns about empty commit
- **Branch Conflicts**: Handles existing branches gracefully

Perfect for routine implementations where you want automated quality gates and git flow without manual steps.