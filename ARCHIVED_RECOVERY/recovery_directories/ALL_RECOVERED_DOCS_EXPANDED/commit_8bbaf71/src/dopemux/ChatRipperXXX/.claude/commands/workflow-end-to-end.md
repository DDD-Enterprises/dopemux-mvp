# Feature Development End-to-End Workflow

## Overview
Complete feature development cycle with TaskMaster integration, design via sequential thinking, comprehensive testing, documentation, and automated completion workflow.

## Phase 1: Preparation & Planning

### 1.1 Task Selection & Setup
```bash
# Start with TaskMaster
task-master next                           # Get next available task
task-master show <id>                     # Review requirements
task-master set-status --id=<id> --status=in-progress

# Alternative: Create new task
task-master add-task --prompt="Feature description" --research
```

### 1.2 Branch Isolation (Multi-Session)
```bash
# Create feature branch for isolation
FEATURE_NAME="$(basename $(pwd))-feature-$(date +%s)"
git checkout -b "feature/$FEATURE_NAME"

# Verify isolation
git branch  # Confirm on feature branch
```

### 1.3 Research & Requirements Gathering
```bash
/research
# → context7 API docs + Exa search
# → Log sources, unknowns to ConPort
# → Gather API docs, examples, constraints
```

### 1.4 Story & Acceptance Criteria
```bash
/story
# → User story + AC + NFR from research
# → Test scenarios and edge cases
# → Store in ConPort with research links
```

### 1.5 Design via Sequential Thinking
```bash
# Use sequential_thinking for complex design
mcp__sequential-thinking__sequentialthinking:
- thought: "Design [Feature Name] architecture"
- nextThoughtNeeded: true
- thoughtNumber: 1
- totalThoughts: 5

# Alternative: Use plan command
/plan
# → sequential_thinking for multi-step reasoning
# → ≤5 steps with explicit files & tests
# → Store design decisions in ConPort
```

## Phase 2: Implementation (TDD Loop)

### 2.1 Test-First Development
```bash
# Start TDD cycle
/implement

# 1. Write failing tests first
#    - Unit tests for core functionality
#    - Integration tests for component interaction
#    - Edge case and error scenario tests
#    - Schema validation tests

# 2. Minimal implementation to pass tests
#    - Use Serena for precise code edits
#    - Minimal diffs, focused changes
#    - Cite design docs in comments

# 3. Refactor while maintaining test coverage
#    - Run tests after each change
#    - Maintain ≥90% coverage target
```

### 2.2 Quality Gates (Continuous)
```bash
# Run quality checks after each TDD cycle
python -m pip install -e .[dev]
pytest --cov=src/chatx --cov-fail-under=90 --cov-report=term-missing
ruff check .
mypy src

# Loop until all gates pass
```

### 2.3 Documentation Updates
```bash
# Update README and docs
# Create ADR stub for design decisions
# Update API documentation
# Log progress to ConPort
```

## Phase 3: Completion & Integration

### 3.1 Quality Verification
```bash
# Final comprehensive checks
/complete
# OR for TaskMaster integration:
/tm/complete-task TASK_ID=<id>

# Automated verification:
# ✅ Tests: All passing, ≥90% coverage
# ✅ Lint: ruff clean
# ✅ Types: mypy clean
# ✅ Documentation: Updated
# ✅ ADR: Created if needed
```

### 3.2 Git Workflow (Automated)
```bash
# Feature branch commit (handled by /complete)
/commit-pr  # Quick automated workflow
# OR:
/complete   # Full manual workflow

# Automated process:
# 1. Feature branch creation (if needed)
# 2. Conventional commit with quality status
# 3. Push to origin
# 4. Detailed PR creation
# 5. Include all quality gate results
```

### 3.3 Memory & Context Updates
```bash
# ConPort: Log implementation decisions
mcp__conport__log_decision:
- workspace_id: "/Users/hue/code/Dopemux-ChatRipperXXX"
- summary: "Completed [Feature Name] implementation"
- rationale: "Based on research and design analysis"
- implementation_details: "Key technical decisions made"

/decision
# Alternative: Use /decision command
# → Logs decision to ConPort
# → Mirrors to OpenMemory if cross-project
```

### 3.4 OpenMemory Integration
```bash
# Personal/context updates
mcp__openmemory__add-memory:
- content: "Feature implementation patterns for [domain]"

# Query relevant context
/mem-query
# → Search OpenMemory by topic/keyword
# → Retrieve relevant past implementations
```

### 3.5 TaskMaster Completion
```bash
# Mark task as completed
task-master set-status --id=<id> --status=done
task-master update-subtask --id=<id> --prompt="Implementation completed with full quality gates"

/tm/complete-task TASK_ID=<id>
# → Automated TaskMaster + quality gates + git flow
```

## Phase 4: Post-Implementation

### 4.1 PR Review & Merge
```bash
# Monitor CI checks
gh pr checks

# Merge when ready
gh pr merge --squash

# Clean up branch
git branch -d "feature/$FEATURE_NAME"
```

### 4.2 Retrospective & Follow-ups
```bash
/retrospect
# → Analyze what worked/failed
# → Log lessons learned to ConPort
# → Add follow-ups to backlog

/followup
# → Add progress/todo to ConPort
# → Schedule maintenance items
```

### 4.3 Context Preservation
```bash
# Compact slice state
/switch
# → ConPort: Implementation summary
# → OpenMemory: Durable insights
# → Clear transient context for next feature
```

## Integration Points

### TaskMaster Integration
- ✅ Task selection and status tracking
- ✅ Progress logging during development
- ✅ Automated completion workflow
- ✅ Documentation of implementation decisions

### Sequential Thinking Integration
- ✅ Design phase reasoning
- ✅ Step-by-step problem breakdown
- ✅ Risk analysis and decision documentation
- ✅ Design validation through structured thinking

### Memory Systems
- ✅ **ConPort**: Project decisions, progress, context
- ✅ **OpenMemory**: Personal preferences, cross-project patterns
- ✅ **Search**: Query past implementations for consistency
- ✅ **Logging**: Decision rationale and implementation details

### Quality Gates (Automated)
- ✅ **Tests**: ≥90% coverage, all passing
- ✅ **Lint**: Clean code style
- ✅ **Types**: Full type checking
- ✅ **Docs**: Updated documentation
- ✅ **ADR**: Architecture decisions recorded

## Multi-Session Considerations

### Branch Isolation Strategy
```bash
# Each session works independently
# Session 1: feature/auth-system-001
# Session 2: feature/payment-integration-002
# Session 3: feature/ui-redesign-003

# Independent completion:
/complete  # Each session runs own quality gates
# Result: Separate PRs for each feature
```

### Conflict Prevention
- Different sessions modify different file sets
- Independent commits and quality verification
- Separate PRs prevent integration conflicts
- Main branch merges controlled and reviewed

### Coordination Points
- TaskMaster for overall project tracking
- ConPort for shared design decisions
- Main branch for final integration
- Retrospective for cross-session learning

## Error Handling & Rollback

### Quality Gate Failures
```bash
# If quality gates fail in /complete:
/complete  # → Stops at failed gate
# → Fix issues manually
# → Re-run /complete

# Alternative rollback:
git reset --hard HEAD~1  # Undo last commit
# → Fix implementation
# → Re-run completion workflow
```

### PR Rejections
```bash
# Address review feedback
git checkout feature/branch-name
# → Make requested changes
# → Amend commit or add fix commit
git push --force-with-lease
# → Re-request review
```

### Branch Cleanup
```bash
# After successful merge
git branch -d feature/completed-feature
# Or force delete if needed:
git branch -D feature/abandoned-feature
```

## Definition of Done

✅ **Planning**: Story + AC + design via sequential_thinking
✅ **Implementation**: TDD with comprehensive tests
✅ **Quality**: ≥90% coverage, lint clean, types clean
✅ **Documentation**: README/docs updated, ADR created
✅ **Git Flow**: Feature branch, conventional commit, detailed PR
✅ **Integration**: TaskMaster completed, ConPort/OpenMemory updated
✅ **Multi-Session**: Isolated branches, independent completion

This workflow ensures every feature follows rigorous quality standards while maintaining full traceability through TaskMaster, ConPort, and OpenMemory integration.