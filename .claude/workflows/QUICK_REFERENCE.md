# MCP Workflow Quick Reference

**Purpose**: Fast lookup for which MCP server to use in any situation
**Format**: Problem → Tool → Command

---

## 🎯 Quick Decision Tree

```
What are you doing?
├── Learning/Research → pal apilookup or dope-context
├── Designing/Planning → pal planner or task-orchestrator
├── Writing Code → serena-v2 + dope-context
├── Reviewing Code → pal codereviewer
├── Debugging → serena-v2 + pal debug
└── Making Decision → pal consensus + conport
```

---

## ⚡ One-Line Rules

| Situation | Use This | NOT That |
|-----------|----------|----------|
| Need library docs | `pal apilookup` | exa, web search |
| Find code in project | `dope-context` | grep, manual search |
| Navigate to definition | `serena-v2` | manual file search |
| Break down task | `task-orchestrator` | manual TODO list |
| Review code | `pal codereviewer` | self-review only |
| Log decision | `conport` | markdown file only |
| Deep research | `gpt-researcher` | quick web search |

---

## 📚 By Task Type

### "How do I use X?"
```bash
pal apilookup: "X documentation and examples"
```

### "Where is X defined?"
```bash
serena-v2 find_symbol: "X"
serena-v2 goto_definition: "navigate to X"
```

### "Find examples of X in our code"
```bash
dope-context search_code: "X implementation examples"
```

### "Why did we decide X?"
```bash
conport semantic_search: "X decision rationale"
```

### "Plan how to implement X"
```bash
pal planner: "design approach for X"
task-orchestrator: "break down X into subtasks"
```

### "Review my X code"
```bash
pal codereviewer: "review X changes for quality/bugs"
```

### "Debug X error"
```bash
serena-v2 find_symbol: "locate X error source"
pal debug: "analyze X error systematically"
```

---

## 🔄 Workflow Templates

### Feature: `.claude/workflows/templates/feature-implementation.md`
**6 phases**: Research → Design → Plan → Implement → Review → Commit
**Time**: 30 min (simple) to 6 hrs (complex)

### Bug Fix: `.claude/workflows/templates/bug-fix.md`
**6 phases**: Investigate → Analyze → Plan → Fix → Verify → Commit
**Time**: 10 min (simple) to 4 hrs (complex)

---

## 🎨 By File Type

### Python Files (*.py)
```bash
# Navigate
serena-v2 find_symbol: "[class/function]"

# Find examples
dope-context search_code: "[pattern] language:python"

# Get docs
pal apilookup: "Python [library] API"

# Review
pal codereviewer: "[file.py]"
```

### JavaScript/TypeScript (*.js, *.ts, *.tsx)
```bash
# Navigate
serena-v2 goto_definition: "[component]"

# Find examples
dope-context search_code: "[pattern] language:typescript"

# Get docs
pal apilookup: "React/TypeScript [topic]"

# Review
pal codereviewer: "[file.tsx]"
```

### Documentation (*.md)
```bash
# Search existing docs
dope-context docs_search: "[topic]"

# Find related docs
conport semantic_search: "[topic] documentation"
```

### Config Files (*.yaml, *.json, *.env)
```bash
# Find examples
dope-context search_code: "[config pattern]"

# Check syntax
pal codereviewer: "[config-file]"
```

---

## 🧠 By Complexity

### Simple (1-2 steps)
```bash
Primary: pal apilookup, serena-v2
Skip: task-orchestrator, pal consensus
```

### Moderate (3-5 steps)
```bash
Primary: task-orchestrator, dope-context, serena-v2
Consider: pal planner, conport
```

### Complex (6+ steps)
```bash
Required: task-orchestrator, conport
Primary: pal planner, pal consensus, dope-context
```

---

## 🎯 Always/Never Rules

### ALWAYS Use
- `pal apilookup` FIRST for library questions
- `task-orchestrator` for multi-step work
- `conport` to log architectural decisions
- `pal codereviewer` before committing
- `pre-commit` before every commit

### NEVER Use
- `exa` for code in our project (use `dope-context`)
- `gpt-researcher` for simple lookups (use `pal apilookup`)
- Manual grep for code search (use `dope-context`)
- Skip code review (always use `pal codereviewer`)
- Skip decision logging (always use `conport`)

---

## ⚡ Performance Tips

### Run in Parallel
```bash
# These can run simultaneously:
pal apilookup + dope-context (research)
serena-v2 + dope-context (code exploration)
```

### Run in Sequence
```bash
# These MUST run in order:
pal planner → task-orchestrator (design before plan)
implement → pal codereviewer (code before review)
pal codereviewer → commit (review before commit)
```

---

## 🆘 Common Problems

### "I don't know where to start"
```bash
1. pal apilookup: "get documentation"
2. dope-context search_code: "find examples"
3. pal planner: "design approach"
4. task-orchestrator: "break down work"
```

### "Code not working, don't know why"
```bash
1. serena-v2 find_symbol: "locate error"
2. pal debug: "systematic analysis"
3. dope-context search_code: "find similar fixes"
```

### "Need to make architectural decision"
```bash
1. gpt-researcher: "research options"
2. pal consensus: "evaluate trade-offs"
3. conport log_decision: "document choice"
```

### "Code works but want to improve it"
```bash
1. serena-v2 analyze_complexity: "check complexity"
2. pal codereviewer: "get improvement suggestions"
3. dope-context search_code: "find better patterns"
```

---

## 📊 Tool Comparison

| Need | Option A | Option B | Best Choice |
|------|----------|----------|-------------|
| Library docs | pal apilookup | exa | **pal apilookup** (faster, accurate) |
| Code search | dope-context | serena-v2 | **dope-context** (semantic) |
| Navigation | serena-v2 | dope-context | **serena-v2** (LSP-based) |
| Task breakdown | task-orchestrator | pal planner | **task-orchestrator** (37 tools) |
| Code review | pal codereviewer | manual | **pal codereviewer** (comprehensive) |
| Deep research | gpt-researcher | exa | **gpt-researcher** (multi-source) |

---

## 🎓 Learning Path

### Week 1: Master Core Tools
- `pal apilookup` - Practice doc lookups
- `serena-v2` - Practice code navigation
- `dope-context` - Practice code search

### Week 2: Master Planning
- `task-orchestrator` - Break down 5 tasks
- `pal planner` - Design 3 features
- `conport` - Log 10 decisions

### Week 3: Master Workflows
- Complete 3 features using feature-implementation template
- Fix 5 bugs using bug-fix template
- Review 10 PRs using review template

### Week 4: Master Automation
- Recognize workflow phases automatically
- Use correct tool without thinking
- Parallel tool usage where appropriate

---

## 🔗 Related Documents

- **Full Automation Rules**: `.claude/workflows/WORKFLOW_AUTOMATION.md`
- **Feature Template**: `.claude/workflows/templates/feature-implementation.md`
- **Bug Fix Template**: `.claude/workflows/templates/bug-fix.md`
- **Server Registry**: `/docker/mcp-servers/SERVER_REGISTRY.md`
- **Health Report**: `/docker/mcp-servers/MCP_HEALTH_REPORT.md`

---

**Quick Ref Version**: 1.0
**Last Updated**: 2026-02-05
**Print This**: Keep handy until tools become automatic
