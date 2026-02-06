# Feature Implementation Workflow Template

**Use this template when**: Adding new features or significant functionality

## Phase 1: Research (5-15 min)

### MCP Servers to Use
- ✅ `pal apilookup` - Library documentation
- ✅ `dope-context` - Find similar features in codebase
- ✅ `gpt-researcher` - Deep research (only if complex/unfamiliar domain)

### Actions
```bash
# 1. Get library documentation
pal apilookup: "query library APIs and patterns for [feature]"

# 2. Find existing similar code
dope-context search_code: "query similar feature implementations"

# 3. Review existing patterns
serena-v2 find_symbol: "locate related functions/classes"
```

### Output
- [ ] Library APIs understood
- [ ] Existing patterns identified
- [ ] Rough mental model of implementation

---

## Phase 2: Design (10-20 min)

### MCP Servers to Use
- ✅ `pal planner` - Design approach
- ✅ `pal consensus` - Evaluate trade-offs (if multiple approaches)
- ✅ `conport` - Log architectural decisions

### Actions
```bash
# 1. Plan approach
pal planner: "design [feature] with these requirements: [requirements]"

# 2. Evaluate trade-offs (if needed)
pal consensus: "compare [approach A] vs [approach B] for [feature]"

# 3. Log decision
conport log_decision:
  summary: "[feature] implementation approach"
  rationale: "[why this approach]"
  implementation_details: "[key technical decisions]"
  tags: ["feature", "architecture"]
```

### Output
- [ ] Design approach documented
- [ ] Trade-offs understood
- [ ] Decision logged in ConPort

---

## Phase 3: Planning (5-10 min)

### MCP Servers to Use
- ✅ `task-orchestrator` - Break down work
- ✅ `leantime-bridge` - Create tickets (if team visibility needed)

### Actions
```bash
# 1. Break down implementation
task-orchestrator create_task:
  name: "[feature] implementation"
  description: "[detailed requirements]"

task-orchestrator breakdown_task:
  task_id: "[task-id]"
  # Returns subtasks with complexity scores

# 2. Create tickets (optional)
leantime-bridge create_ticket:
  project: "[project-name]"
  title: "[feature] implementation"
  tasks: "[subtasks from orchestrator]"
```

### Output
- [ ] Tasks broken down with complexity scores
- [ ] Clear implementation sequence
- [ ] Team visibility (if needed)

---

## Phase 4: Implementation (Variable time)

### MCP Servers to Use
- ✅ `serena-v2` - Code navigation
- ✅ `dope-context` - Find examples
- ✅ `pal apilookup` - Quick docs lookup
- ✅ `conport` - Track progress

### Actions Per Subtask
```bash
# 1. Navigate to implementation location
serena-v2 goto_definition: "[symbol]"
serena-v2 find_references: "[check usage]"

# 2. Find examples if needed
dope-context search_code: "[specific pattern needed]"

# 3. Lookup API if needed
pal apilookup: "[specific API question]"

# 4. Implement the code
# [Write actual code here]

# 5. Track progress
conport update_progress:
  task_id: "[task-id]"
  status: "IN_PROGRESS" or "DONE"
  notes: "[what was completed]"
```

### Output
- [ ] Code written and working
- [ ] Progress tracked
- [ ] Ready for review

---

## Phase 5: Review (5-10 min)

### MCP Servers to Use
- ✅ `pal codereviewer` - Comprehensive review
- ✅ `serena-v2` - Complexity check
- ✅ `pal secaudit` - Security check (if handling auth/data)

### Actions
```bash
# 1. Code review
pal codereviewer:
  files: "[changed files]"
  focus: "quality, bugs, maintainability"

# 2. Check complexity
serena-v2 analyze_complexity:
  file: "[implementation file]"
  # Should be <0.6 for ADHD-friendly

# 3. Security audit (if needed)
pal secaudit:
  files: "[files handling sensitive data]"
```

### Output
- [ ] Code review feedback addressed
- [ ] Complexity acceptable
- [ ] Security validated (if applicable)

---

## Phase 6: Commit (2-5 min)

### MCP Servers to Use
- ✅ `pre-commit` - Automated checks
- ✅ `pal codereviewer` - Final review
- ✅ `conport` - Close tasks

### Actions
```bash
# 1. Pre-commit checks
pre-commit run --all-files

# 2. Final review
pal codereviewer: "quick final check before commit"

# 3. Commit
git add [files]
git commit -m "[feature]: brief description

[Detailed changes]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 4. Update task status
conport update_progress:
  task_id: "[task-id]"
  status: "DONE"
```

### Output
- [ ] Clean commit with good message
- [ ] All tasks marked DONE
- [ ] Feature complete!

---

## Checklist

**Research**
- [ ] Library APIs researched
- [ ] Existing patterns found
- [ ] Approach understood

**Design**
- [ ] Design documented
- [ ] Trade-offs evaluated
- [ ] Decision logged in ConPort

**Planning**
- [ ] Work broken down
- [ ] Complexity assessed
- [ ] Tickets created (if needed)

**Implementation**
- [ ] Code written
- [ ] Tests added
- [ ] Progress tracked

**Review**
- [ ] Code reviewed
- [ ] Complexity checked
- [ ] Security validated

**Commit**
- [ ] Pre-commit passed
- [ ] Committed with good message
- [ ] Tasks closed

---

## Time Estimates

| Phase | Simple | Moderate | Complex |
|-------|--------|----------|---------|
| Research | 5 min | 10 min | 15-30 min |
| Design | 5 min | 15 min | 20-40 min |
| Planning | 5 min | 10 min | 15-20 min |
| Implementation | 15 min | 1-2 hrs | 2-4 hrs |
| Review | 5 min | 10 min | 15-20 min |
| Commit | 2 min | 5 min | 5-10 min |
| **TOTAL** | **~30 min** | **~2 hrs** | **~4-6 hrs** |

**ADHD Tip**: For complex features, break into multiple 25-minute focus sessions with breaks.

---

## Common Pitfalls

❌ **Don't**:
- Skip research phase (leads to wrong implementation)
- Skip task breakdown (leads to scope creep)
- Skip decision logging (forget why choices were made)
- Skip code review (merge bugs)

✅ **Do**:
- Use pal apilookup FIRST for library questions
- Log decisions with rationale to ConPort
- Break work into <25min chunks for ADHD
- Track progress after each subtask

---

**Template Status**: Active
**Last Updated**: 2026-02-05
**Use Count**: [Track usage to refine]
