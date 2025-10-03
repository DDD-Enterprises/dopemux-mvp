---
description: "Zen precommit validation, test coverage check, commit, and PR creation"
arguments: "[commit_message]"
allowed-tools: [
  "Bash", "Read", "Write", "Edit", "Grep", "Glob",
  "mcp__zen__precommit",
  "mcp__conport__log_decision",
  "mcp__conport__update_active_context"
]
model: "claude-sonnet-4-5-20250929"
---

# /dx:commit - Validated Commit & PR

Comprehensive pre-commit validation with Zen analysis, documentation updates, test coverage check, automatic commit, and PR creation.

**Purpose**: ADHD-friendly git workflow that ensures quality while reducing manual validation steps.

---

## Phase 1: Pre-Commit Validation with Zen

### Step 1.1: Run Zen Precommit Analysis

Use mcp__zen__precommit to validate changes:

```
mcp__zen__precommit with:
  model: "o3-mini"
  step: "Analyze staged changes for:
    - Code quality and potential bugs
    - Test coverage gaps
    - Documentation updates needed
    - ADHD metadata in new features
    - Breaking changes or API modifications
    - Security concerns
    - Performance implications

    Current git status:
    [Run: git status]

    Git diff:
    [Run: git diff --cached]

    Recent commits:
    [Run: git log --oneline -5]

    Provide detailed analysis and recommendations."
  step_number: 1
  total_steps: 3
  next_step_required: true
  findings: "Initial validation of staged changes"
```

Continue Zen precommit analysis through all steps until complete.

### Step 1.2: Review Zen Findings

Display Zen precommit results with ADHD-friendly formatting:

```
Zen Pre-Commit Analysis
═══════════════════════════════════════════

Issues Found:
[Loop through issues_found]
🔴 [severity]: [description]

Recommendations:
[Display key recommendations]

Files Analyzed: [files_checked count]
Confidence: [confidence level]

═══════════════════════════════════════════
```

### Step 1.3: Address Critical Issues

If CRITICAL or HIGH severity issues found:
- Show: "⚠️ Critical issues detected. These should be addressed before committing."
- List issues with file:line references
- Ask: "Fix issues now? (y/n/skip)"
  - If yes: Guide user through fixes, then re-run Zen precommit
  - If skip: Ask for confirmation to proceed anyway

---

## Phase 2: Documentation Validation & Updates

### Step 2.1: Check for Documentation Updates Needed

Use Grep to find modified code files:
```bash
git diff --cached --name-only | grep -E '\.(py|ts|js|go|rs)$'
```

For each modified code file, check if documentation exists and needs updates:

**Check for**:
- README.md in same directory
- docs/ entries referencing the file
- ADR entries if architectural changes
- Frontmatter in docs (required: id, title, date, owner)

### Step 2.2: Validate Existing Documentation

Use Grep to check documentation frontmatter:
```bash
grep -r "^---" docs/ --include="*.md" -A 10
```

Verify all docs have required frontmatter:
- id: Unique identifier
- title: Clear title
- date: YYYY-MM-DD format
- owner: Responsibility assignment

**If missing frontmatter**:
- Show: "📝 Documentation frontmatter missing or incomplete"
- List files needing updates
- Offer to add frontmatter automatically

### Step 2.3: Check ADHD Metadata

For new features, verify ADHD metadata exists:
- Task complexity scores
- Estimated durations
- Energy requirements
- Break points for long tasks

**If missing**:
- Show: "🧠 ADHD metadata missing for new features"
- Suggest: "Add ADHD metadata to task descriptions in ConPort"

---

## Phase 3: Test Coverage Validation

### Step 3.1: Run Test Suite

```bash
# Run tests with coverage
pytest services/adhd_engine/tests/ --cov=services/adhd_engine --cov-report=term-missing --tb=short -q
```

### Step 3.2: Check Coverage Threshold

Parse coverage output:
- Extract overall coverage percentage
- Identify files with <80% coverage
- Check if new files have tests

**Coverage Requirements**:
- Overall: >60% acceptable, >80% ideal
- New files: Must have tests
- Critical files (engine.py, api/routes.py): >70%

**If coverage below threshold**:
- Show: "⚠️ Test coverage below threshold"
- List files needing more tests
- Ask: "Add tests now? (y/n/skip)"
  - If yes: Guide test creation
  - If skip: Note in commit message

---

## Phase 4: Create Commit

### Step 4.1: Generate Commit Message

**If $ARGUMENTS provided** (commit message):
- Use provided message as summary

**Else**, generate from Zen analysis:
- Summary: Brief description of changes (50 chars)
- Body: Detailed explanation including:
  - What changed and why
  - Zen precommit findings summary
  - Test coverage results
  - Documentation updates made
  - Any ADHD accommodations added

**Commit Message Format**:
```
feat|fix|docs|refactor: Brief summary (50 chars)

Detailed description of changes.

Zen Precommit: [Pass/Conditional Pass/Issues Found]
Test Coverage: XX% (was YY%)
Docs Updated: [Yes/No]
ADHD Metadata: [Added/Updated/N/A]

Related Decisions: #XXX, #YYY

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Step 4.2: Execute Commit

```bash
git commit -m "$(cat <<'EOF'
[Generated commit message here]
EOF
)"
```

Verify commit succeeded:
```bash
git log -1 --oneline
```

---

## Phase 5: Create Pull Request

### Step 5.1: Check if PR Needed

Ask user: "Create pull request? (y/n)"

If no:
- Show: "✅ Commit complete. Changes on current branch."
- Exit command

### Step 5.2: Gather PR Information

Ask user:
```
Pull Request Creation
═══════════════════════════════════════════

PR Title: (default: commit summary)
>

PR Description: (auto-generated from commit + Zen analysis)
- Use default? (y/n)
>
```

### Step 5.3: Generate PR Description

**Auto-generated PR template**:
```markdown
## Summary

[Commit summary and key changes]

## Changes

[Bulleted list of main changes from git diff]

## Zen Precommit Analysis

**Issues Found**: [count]
- [High/Medium/Low severity summary]

**Validation**:
- ✅ Code quality checked
- ✅ Test coverage validated (XX%)
- ✅ Documentation reviewed
- ✅ ADHD metadata verified

## Test Coverage

- Overall: XX%
- New files: [coverage stats]
- Critical paths: [status]

## Testing Checklist

- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing complete
- [ ] No regressions introduced

## ADHD Accommodations

[Any ADHD-related improvements in this PR]

## Related Decisions

ConPort Decisions: #XXX, #YYY

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Step 5.4: Create PR with GitHub CLI

```bash
gh pr create \
  --title "PR_TITLE" \
  --body "$(cat <<'EOF'
[Generated PR description]
EOF
)" \
  --base main \
  --head current-branch
```

### Step 5.5: Log to ConPort

Log PR creation as decision:
```
mcp__conport__log_decision with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  summary: "PR Created: [PR_TITLE]"
  rationale: "Changes: [summary]. Zen validation: [status]. Coverage: XX%."
  implementation_details: "[Detailed changes from PR description]"
  tags: ["pull-request", "zen-validated", "coverage-XX"]
```

Update active context:
```
mcp__conport__update_active_context --patch_content '{
  "last_pr": {"title": "TITLE", "url": "URL", "created": "TIMESTAMP"},
  "last_commit": "COMMIT_SHA"
}'
```

---

## Phase 6: Success Summary

Show final result:
```
✅ Commit & PR Complete!
═══════════════════════════════════════════

Commit: [commit SHA]
PR: [PR URL]

Zen Validation: ✅ [status]
Test Coverage: XX% (target: >60%)
Docs: ✅ [updated/validated]

PR logged to ConPort (Decision #XXX)

Next steps:
• Review PR in GitHub
• Wait for checks to complete
• Merge when ready

Great work! 🎉
═══════════════════════════════════════════
```

---

## Error Handling

**If Zen precommit fails**:
- Show validation errors
- Offer to fix or skip
- Continue if user chooses skip

**If tests fail**:
- Show test failures
- Ask: "Fix tests now? (y/n/skip)"
- Commit only if user confirms skip

**If gh CLI not installed**:
- Show: "GitHub CLI not found. Install with: brew install gh"
- Show: "Or create PR manually at: [GitHub URL]"
- Continue without PR creation

**If no remote branch**:
- Ask: "Push branch to remote? (y/n)"
- Execute: `git push -u origin BRANCH_NAME`

---

## Success Criteria

- ✅ Zen precommit analysis complete (no critical issues OR user acknowledged)
- ✅ Documentation validated or updated
- ✅ Test coverage checked (>60% OR user acknowledged)
- ✅ Commit created successfully
- ✅ PR created (if requested)
- ✅ ConPort decision logged

---

## ADHD Accommodations

**Visual Feedback**: Progress bars for each phase
**Gentle Validation**: Non-blocking checks, user controls proceed/fix decisions
**Celebration**: Celebrate successful commit + PR
**Context Preservation**: Log PR to ConPort for future reference
**Reduced Friction**: Automate tedious validation steps

---

## Notes for Claude

- Be encouraging throughout validation process
- Don't overwhelm with too many issues at once (show top 3-5)
- Allow user to proceed even with warnings (their choice)
- Celebrate completion regardless of coverage %
- Make PR creation feel easy and rewarding
