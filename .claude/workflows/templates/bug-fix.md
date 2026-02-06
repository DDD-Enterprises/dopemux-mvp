# Bug Fix Workflow Template

**Use this template when**: Fixing bugs, resolving errors, troubleshooting issues

## Quick Start (for simple bugs)

```bash
1. serena-v2 find_symbol: "locate error source"
2. dope-context search_code: "find error handling patterns"
3. Fix the code
4. pal codereviewer: "verify fix"
5. Commit
```

**Time**: 10-20 minutes for simple bugs

---

## Full Workflow (for complex bugs)

### Phase 1: Investigation (5-15 min)

#### MCP Servers
- ✅ `serena-v2` - Navigate to error location
- ✅ `dope-context` - Find related code

#### Actions
```bash
# 1. Locate error source
serena-v2 find_symbol: "[function/class from error]"
serena-v2 goto_definition: "[navigate to code]"

# 2. Understand context
serena-v2 find_references: "[see how it's used]"
serena-v2 get_context: "[surrounding code]"

# 3. Find related code
dope-context search_code: "[error type + context]"
# Example: "TypeError handling in API calls"
```

#### Output
- [ ] Error location found
- [ ] Context understood
- [ ] Related code identified

---

### Phase 2: Root Cause Analysis (10-20 min)

#### MCP Servers
- ✅ `pal debug` - Systematic debugging
- ✅ `serena-v2` - Analyze complexity/flow

#### Actions
```bash
# 1. Debug systematically
pal debug:
  error: "[full error message]"
  file: "[file path]"
  context: "[what was being done when error occurred]"

# 2. Check complexity
serena-v2 analyze_complexity: "[file with error]"
# High complexity = more likely to have bugs

# 3. Trace execution flow
serena-v2 find_references: "[trace call chain]"
```

#### Output
- [ ] Root cause identified
- [ ] Understanding of why it happened
- [ ] Clear fix strategy

---

### Phase 3: Planning (5 min)

#### MCP Servers
- ✅ `task-orchestrator` - Simple breakdown (if multi-step fix)
- ✅ `conport` - Log bug analysis

#### Actions
```bash
# Only if fix requires multiple changes
task-orchestrator create_task:
  name: "Fix [bug description]"
  description: "[root cause and fix strategy]"

task-orchestrator breakdown_task:
  # If needed for complex fixes

# Log the bug and fix plan
conport log_decision:
  summary: "Bug fix: [description]"
  rationale: "Root cause: [cause]. Fix: [strategy]"
  tags: ["bugfix", "debugging"]
```

#### Output
- [ ] Fix strategy documented
- [ ] Steps clear (if complex)

---

### Phase 4: Implementation (10-30 min)

#### MCP Servers
- ✅ `serena-v2` - Navigate code
- ✅ `dope-context` - Find fix patterns
- ✅ `pal apilookup` - API docs if needed

#### Actions
```bash
# 1. Find fix patterns
dope-context search_code: "[how similar bugs were fixed]"

# 2. Check API usage (if applicable)
pal apilookup: "[correct API usage for the fix]"

# 3. Navigate to fix location
serena-v2 goto_definition: "[code to fix]"

# 4. Apply fix
# [Write the actual fix]

# 5. Add test if missing
# [Ensure bug won't reoccur]
```

#### Output
- [ ] Bug fixed
- [ ] Test added (if needed)
- [ ] No new errors introduced

---

### Phase 5: Verification (5-10 min)

#### MCP Servers
- ✅ `pal codereviewer` - Review fix
- ✅ `serena-v2` - Check complexity didn't increase

#### Actions
```bash
# 1. Review the fix
pal codereviewer:
  files: "[changed files]"
  focus: "bug fix correctness, no regression"

# 2. Verify complexity
serena-v2 analyze_complexity: "[fixed file]"
# Should not have increased significantly

# 3. Run tests
pytest [test file]  # or appropriate test command

# 4. Verify fix works
# [Manual testing if needed]
```

#### Output
- [ ] Fix reviewed
- [ ] Tests pass
- [ ] Bug verified fixed

---

### Phase 6: Commit (2-5 min)

#### MCP Servers
- ✅ `pre-commit` - Automated checks
- ✅ `conport` - Log fix

#### Actions
```bash
# 1. Pre-commit checks
pre-commit run --all-files

# 2. Commit with clear message
git add [files]
git commit -m "fix: [brief description of bug]

Root cause: [what caused it]
Fix: [what was changed]
Tested: [how it was verified]

Fixes #[issue number if applicable]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 3. Update ConPort
conport log_progress:
  description: "Fixed [bug]"
  status: "DONE"
```

#### Output
- [ ] Clean commit
- [ ] Fix documented

---

## Bug Fix Checklist

**Investigation**
- [ ] Error location found
- [ ] Stack trace analyzed
- [ ] Related code reviewed

**Analysis**
- [ ] Root cause identified
- [ ] Fix strategy clear
- [ ] Decision logged (if complex)

**Implementation**
- [ ] Fix applied
- [ ] Test added/updated
- [ ] No new issues introduced

**Verification**
- [ ] Fix reviewed
- [ ] Tests pass
- [ ] Bug verified fixed
- [ ] No regression

**Documentation**
- [ ] Commit message explains root cause
- [ ] ConPort updated
- [ ] Issue closed (if applicable)

---

## Time Estimates by Complexity

| Bug Type | Investigation | Fix | Verify | Total |
|----------|--------------|-----|--------|-------|
| **Typo/Simple** | 2 min | 2 min | 3 min | ~10 min |
| **Logic Error** | 10 min | 15 min | 5 min | ~30 min |
| **Complex Bug** | 20 min | 30-60 min | 10 min | ~1-2 hrs |
| **Race Condition** | 30+ min | 60+ min | 20 min | ~2-4 hrs |

**ADHD Tip**: Take breaks between phases for complex bugs. Fresh eyes spot issues faster.

---

## Common Bug Patterns

### TypeError/AttributeError
```bash
# Quick fix workflow
1. serena-v2 find_symbol: "[object with error]"
2. Check type hints and usage
3. pal apilookup: "[correct API usage]"
4. Fix + test
```

### Logic Error
```bash
# Trace execution
1. serena-v2 find_references: "[function]"
2. Map call chain
3. pal debug: "logic flow analysis"
4. Fix + regression test
```

### Performance Issue
```bash
# Profile and optimize
1. serena-v2 analyze_complexity: "[slow code]"
2. dope-context search_code: "[optimization patterns]"
3. Fix + benchmark
```

### Import Error
```bash
# Dependency check
1. Check requirements.txt / package.json
2. pal apilookup: "[correct import path]"
3. Fix import + test
```

---

## Debugging Best Practices

### ✅ DO
- Read error message completely
- Check stack trace for exact location
- Search for similar bugs in codebase
- Add test to prevent recurrence
- Log root cause, not just symptoms

### ❌ DON'T
- Guess and randomly change code
- Skip understanding root cause
- Fix symptom without fixing cause
- Commit without testing
- Skip adding regression test

---

## Emergency Bug Fix (Production)

**When**: Critical production bug needing immediate fix

### Fast Track (15-30 min)
```bash
1. serena-v2: locate error ASAP
2. dope-context: find quickest safe fix
3. pal debug: verify root cause (quick)
4. Apply minimal fix
5. pal codereviewer: security check
6. Test + deploy
7. conport log_decision: document what happened
8. Create follow-up task for proper fix
```

**Rule**: Fix fast, then fix right
- Emergency fix = stop the bleeding
- Follow-up = address root cause properly

---

**Template Status**: Active
**Last Updated**: 2026-02-05
**Success Rate**: [Track to improve]
