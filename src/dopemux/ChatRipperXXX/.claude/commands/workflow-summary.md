# Feature Development Workflow - Summary

## 🎯 **Complete End-to-End Process**

### **Phase 1: Planning & Design**
1. **Task Setup**: `task-master next` → `task-master show <id>` → `task-master set-status in-progress`
2. **Branch Isolation**: `git checkout -b feature/name-$(date +%s)` *(multi-session safe)*
3. **Research**: `/research` *(context7 + Exa → ConPort)*
4. **Requirements**: `/story` *(user story + AC + NFR → ConPort)*
5. **Design**: `/plan` *(sequential_thinking → ≤5 steps with files/tests → ConPort)*

### **Phase 2: Implementation (TDD)**
6. **TDD Loop**: `/implement` *(tests first → minimal code → refactor)*
7. **Quality Checks**: *Continuous (tests, lint, types, coverage ≥90%)*
8. **Progress**: *ConPort logging during development*

### **Phase 3: Completion & Integration**
9. **Final Quality Gates**: `/complete` OR `/tm/complete-task`
   - ✅ **Tests**: All passing, ≥90% coverage
   - ✅ **Code**: Lint clean, types clean
   - ✅ **Branch**: Feature branch created
   - ✅ **Commit**: Conventional format
   - ✅ **PR**: Detailed with quality status
10. **Memory Updates**:
    - ✅ **TaskMaster**: Task marked done
    - ✅ **ConPort**: Implementation decisions logged
    - ✅ **OpenMemory**: Personal insights preserved
11. **Git Flow**: Automated commit → push → PR creation

### **Phase 4: Post-Implementation**
12. **PR Review**: `gh pr checks` → `gh pr merge --squash`
13. **Cleanup**: `git branch -d feature/completed-branch`
14. **Retrospective**: `/retrospect` → `/switch` *(lessons → ConPort/OpenMemory)*

## 🔄 **Integration Points**

### **TaskMaster Integration**
- ✅ Task selection and status tracking
- ✅ Progress logging during development
- ✅ Automated completion with `/tm/complete-task`
- ✅ Cross-session task coordination

### **Sequential Thinking Integration**
- ✅ Design phase complex reasoning
- ✅ Step-by-step problem breakdown
- ✅ Risk analysis and decision documentation
- ✅ Implementation planning validation

### **Memory Systems Integration**
- ✅ **ConPort**: Project decisions, progress, context summaries
- ✅ **OpenMemory**: Personal preferences, cross-project patterns
- ✅ **Search**: Query past implementations for consistency
- ✅ **Logging**: Decision rationale and implementation details

## 🚀 **Multi-Session Support**

### **Branch Isolation Strategy**
```bash
# Concurrent sessions working independently:
Session 1: feature/auth-system-001     → /complete → PR #101
Session 2: feature/payment-integration-002 → /complete → PR #102
Session 3: feature/ui-redesign-003     → /complete → PR #103

# Zero conflicts when sessions modify different files
# Independent quality gates and PR reviews
# Main branch stays stable until controlled merges
```

### **Session Coordination**
- Each session works on separate feature branches
- Independent completion workflows
- Shared ConPort for design decisions
- TaskMaster for overall project tracking

## 📋 **Quality Gates (Automated)**

| Gate | Command | Criteria | Automation |
|------|---------|----------|------------|
| Tests | `pytest` | ≥90% coverage, all passing | ✅ `/complete` |
| Lint | `ruff check .` | No violations | ✅ `/complete` |
| Types | `mypy src` | Clean type checking | ✅ `/complete` |
| Docs | Manual | README/docs updated | ✅ Checklist |
| ADR | Manual | Decision record created | ✅ Checklist |
| Git | Auto | Feature branch + commit + PR | ✅ `/complete` |
| Memory | Auto | ConPort/OpenMemory updated | ✅ `/complete` |

## 🎖️ **Definition of Done**

✅ **Planning**: Task selected, research complete, design via sequential_thinking
✅ **Implementation**: TDD completed with comprehensive tests
✅ **Quality**: All automated gates passing (tests/lint/types/coverage)
✅ **Documentation**: README updated, ADR created for decisions
✅ **Git Flow**: Feature branch, conventional commit, detailed PR
✅ **Integration**: TaskMaster done, ConPort/OpenMemory updated
✅ **Multi-Session**: Branch isolation maintained, conflicts prevented

## 🛠️ **Command Reference**

| Command | Purpose | Integration |
|---------|---------|-------------|
| `/research` | Requirements gathering | ConPort logging |
| `/story` | User story + AC + tests | ConPort storage |
| `/plan` | Design via sequential_thinking | ConPort decisions |
| `/implement` | TDD loop + testing | ConPort progress |
| `/complete` | Full quality gates + git flow | All integrations |
| `/tm/complete-task` | TaskMaster + quality + git | TaskMaster focused |
| `/commit-pr` | Quick automated workflow | Basic automation |
| `/workflow-end-to-end` | Complete guide reference | Documentation |

## ⚡ **Quick Start Commands**

```bash
# Start new feature
task-master next && task-master show <id>
git checkout -b "feature/$(basename $(pwd))-feature-$(date +%s)"

/research && /story && /plan
/implement && /complete
```

This workflow ensures **rigorous quality standards**, **full traceability**, and **multi-session capability** while automating repetitive tasks and maintaining comprehensive documentation through integrated memory systems.