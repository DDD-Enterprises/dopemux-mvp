Complete TaskMaster task with full quality gates and commit/PR workflow.

## Task Completion Flow

### 1. TaskMaster Task Status Update
```bash
# Mark task as completed in TaskMaster
mcp__task-master-ai__set_task_status:
- id: "$TASK_ID"  # e.g., "1.2" or "3.1"
- status: "done"
- projectRoot: "/Users/hue/code/Dopemux-ChatRipperXXX"
```

### 2. Quality Gates Verification
```bash
# Run comprehensive checks
python -m pip install -e .[dev]
pytest --cov=src/chatx --cov-fail-under=90 --cov-report=term-missing
ruff check .
mypy src
```

### 3. Documentation Updates
```bash
# Update project documentation if needed
# - README updates for new features
# - docs/ updates
# - TODO updates in project files
```

### 4. Feature Branch Management
```bash
# Create feature branch for the task
TASK_BRANCH="task-$TASK_ID-$(date +%s)"
git checkout -b "$TASK_BRANCH"

# Or use existing pattern:
# git checkout -b "feature/task-$TASK_ID"
```

### 5. Conventional Commit
```bash
git add -A
git commit -m "feat(task-$TASK_ID): complete implementation

Task: $TASK_ID - [Task Title from TaskMaster]
Status: ✅ Completed with quality gates

Quality Gates:
- ✅ Tests: All passing, coverage ≥90%
- ✅ Lint: Clean (ruff)
- ✅ Types: Clean (mypy)
- ✅ Documentation: Updated

TaskMaster: Marked as done
Files: $(git diff --cached --name-only | wc -l) modified

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 6. Push and PR Creation
```bash
# Push feature branch
git push -u origin "$TASK_BRANCH"

# Create PR with TaskMaster context
gh pr create \
  --title "feat(task-$TASK_ID): complete implementation" \
  --body "## Task Completion: $TASK_ID

### TaskMaster Status ✅
- **Task ID**: $TASK_ID
- **Status**: Completed
- **Quality Gates**: All passed

### Implementation Details
$(task-master show $TASK_ID | grep -A 10 "Description:")

### Quality Verification
- **Tests**: $(pytest --cov=src/chatx --cov-fail-under=90 2>/dev/null && echo "✅ All passing ≥90% coverage" || echo "❌ Tests failed")
- **Lint**: $(ruff check . 2>/dev/null && echo "✅ Clean" || echo "❌ Issues found")
- **Types**: $(mypy src 2>/dev/null && echo "✅ Clean" || echo "❌ Type errors")

### Files Changed
$(git diff --cached --name-only | sed 's/^/- /')

### Ready for Review
Branch: $TASK_BRANCH
Task: Marked complete in TaskMaster

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>" \
  --label "enhancement,task-complete"
```

## Usage Examples

### Complete Current Task
```bash
# For current/next TaskMaster task
TASK_ID=$(mcp__task-master-ai__next_task projectRoot="/Users/hue/code/Dopemux-ChatRipperXXX" | jq -r '.id')
/tm/complete-task TASK_ID=$TASK_ID
```

### Complete Specific Task
```bash
# Complete specific task ID
/tm/complete-task TASK_ID=1.2
/tm/complete-task TASK_ID=3.1
```

### Multi-Session Task Completion
```bash
# Each session completes its assigned tasks
# Session 1 working on auth tasks:
/tm/complete-task TASK_ID=1.2  # Login feature
/tm/complete-task TASK_ID=1.3  # Registration

# Session 2 working on payment tasks:
/tm/complete-task TASK_ID=2.1  # Payment processing
/tm/complete-task TASK_ID=2.2  # Refund handling
```

## Integration Points

### With TaskMaster Workflow
```bash
# Standard workflow
task-master next                                    # Get next task
task-master show <id>                              # Review task details
# Implement task...
/tm/complete-task TASK_ID=<id>                     # Complete with quality gates
```

### With Existing Commands
```bash
# Use with other workflow commands
/story                                           # Define requirements
/plan                                            # Plan implementation
/implement                                        # Write code and tests
/tm/complete-task TASK_ID=<id>                   # Quality gates + git flow
```

## Quality Gates (Automated)

### Code Quality
- ✅ **Tests**: All pass with ≥90% coverage
- ✅ **Lint**: `ruff check .` clean
- ✅ **Types**: `mypy src` clean
- ✅ **Coverage**: `pytest --cov-fail-under=90`

### Process Quality
- ✅ **TaskMaster**: Task marked as done
- ✅ **Documentation**: Updated as needed
- ✅ **Git Flow**: Feature branch + conventional commit
- ✅ **PR**: Detailed PR with quality status

### Multi-Session Safety
- ✅ **Branch Isolation**: Each task gets its own feature branch
- ✅ **Concurrent Work**: Multiple sessions can complete tasks independently
- ✅ **Conflict Prevention**: Feature branches prevent main branch conflicts

## Definition of Done

✅ **Task Status**: Marked complete in TaskMaster
✅ **Code Quality**: All lint, types, tests, coverage gates passed
✅ **Documentation**: Updated for implemented features
✅ **Git Hygiene**: Feature branch, conventional commit, detailed PR
✅ **Multi-Session**: Isolated branches for concurrent development
✅ **Quality Tracking**: All metrics captured in PR description

This command ensures every TaskMaster task completion follows the same rigorous quality and git workflow standards, with full multi-session support.