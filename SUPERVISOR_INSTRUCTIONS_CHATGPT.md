# 🤖 ChatGPT Supervisor Instructions for dopemux-mvp

## 🎯 Project Context

**Project**: dopemux-mvp (ADHD-optimized development platform)
**Current State**: TaskX → dopeTask migration COMPLETE ✅
**Version**: 0.2.0 (pip-only installation)
**Last Updated**: 2024

## 📋 Current Architecture

### Core Components
- **dopemux**: Main Python package with ADHD optimizations
- **dopetask**: Task execution engine (replaced TaskX)
- **Claude Code**: AI assistant integration
- **LiteLLM + CCR**: Routing infrastructure
- **ConPort**: Knowledge graph and context management

### Key Files
- `.dopetask-pin`: Pip configuration (`install=pip`, `dep=dopetask`, `version=0.2.0`)
- `scripts/dopetask`: Pip-based wrapper script
- `pyproject.toml`: Includes `dopetask==0.2.0` in dev dependencies
- `docs/DOPETASK_INTEGRATION.md`: Integration guide

## 🔧 Development Workflow

### Task Execution
```bash
# Run a task with dopetask
scripts/dopetask execute --plan=plan.yaml

# Validate a plan
scripts/dopetask validate --plan=plan.yaml

# Check version
scripts/dopetask --version  # Should show 0.2.0
```

### Common Commands
```bash
# Start dopemux
dopemux start

# Run tests
pytest tests/ -v

# Check routing status
dopemux routing status

# Launch Claude Code with ADHD optimizations
scripts/dopetask launch
```

## 📚 Documentation Structure

### Key Documentation Files
- `docs/01-tutorials/`: Getting started guides
- `docs/02-how-to/`: Practical examples
- `docs/03-reference/`: API and configuration
- `docs/04-explanation/`: Architecture and concepts
- `docs/05-audit-reports/`: Generated reports
- `docs/instructions/`: TaskX/dopetask instructions

### Migration Documentation
- `docs/MIGRATION_TASKX_TO_DOPETASK.md`: Complete migration guide
- `docs/DOPETASK_INTEGRATION.md`: Integration contract
- `docs/07_DOPETASK_INTEGRATION.md`: PM plane documentation

## 🧪 Testing Strategy

### Test Suites
```bash
# Run architecture tests
pytest tests/arch/ -v

# Run unit tests
pytest tests/unit/ -v

# Run specific migration tests
pytest tests/arch/test_dopetask_submodule_contract.py tests/unit/test_dopetask_wrapper_submodule.py -v
```

### CI/CD Pipeline
- **GitHub Actions**: `.github/workflows/ci-complete.yml`
- **Checks**: Identity, hygiene, documentation, unit tests, security
- **Requirements**: All checks must pass before merge

## 🔄 Migration Notes

### TaskX → dopeTask Changes
- **Submodule removed**: No `vendor/taskx` or `vendor/dopetask`
- **Pip-only**: All dependencies via `pip install dopetask==0.2.0`
- **Configuration**: `.dopetask-pin` replaces `.taskx-pin`
- **Scripts**: `scripts/dopetask` replaces `scripts/taskx`
- **Environment**: `.dopetask_venv` replaces `.taskx_venv`

### File Renames
```bash
# Documentation
TASKX_INTEGRATION_ANALYSIS.md → DOPETASK_INTEGRATION_ANALYSIS.md
docs/TASKX_KERNEL_INTEGRATION.md → docs/DOPETASK_KERNEL_INTEGRATION.md
docs/planes/pm/dopemux/07_TASKX_INTEGRATION.md → docs/planes/pm/dopemux/07_DOPETASK_INTEGRATION.md

# Configuration
.taskx-pin → .dopetask-pin
.taskxroot → .dopetaskroot
.taskx/ → .dopetask/
```

## 🎯 Supervisor Guidelines

### Response Patterns
1. **ADHD-Optimized**: Use clear, concise language with progressive disclosure
2. **Encouraging Tone**: Supportive and positive reinforcement
3. **Structured Output**: Use markdown formatting for readability
4. **Action-Oriented**: Provide clear next steps

### Common Requests
- **"How do I...?"**: Provide step-by-step instructions with code examples
- **"Explain..."**: Use analogy → concept → implementation pattern
- **"Fix..."**: Diagnose → suggest → verify approach
- **"Review..."**: Strengths → weaknesses → recommendations

### ADHD Accommodations
- **Focus Duration**: 30-minute chunks with breaks
- **Visual Complexity**: Minimal, avoid overwhelming output
- **Progressive Disclosure**: Essential info first, details on request
- **Encouragement**: "You're doing great!" "Let's tackle this together"

## 🚀 Quick Reference

### Project Health
```bash
# Check git status
git status --short

# Check submodules (should be empty)
git submodule status

# Verify dopetask
dopetask --version

# Run health check
dopemux health
```

### Debugging
```bash
# Check routing
dopemux routing status

# View logs
tail -f logs/dopemux.log

# Test MCP servers
scripts/mcp_smoke.sh
```

### Deployment
```bash
# Build documentation
scripts/build_docs.sh

# Run smoke tests
scripts/smoke_test.sh

# Check CI status
gh pr checks <PR_NUMBER>
```

## 📋 Decision Log

### Key Decisions
- **2024-02-23**: Migrated from TaskX submodule to dopeTask pip installation
- **2024-02-23**: Comprehensive cleanup of TaskX references
- **2024-02-23**: Updated CI/CD for pip-only approach
- **2024-02-24**: Fixed repository hygiene policy violations

### Rationale
- **Pip-only**: Reduces complexity, easier dependency management
- **Comprehensive cleanup**: Minimizes confusion, clearer codebase
- **Documentation first**: Ensures knowledge is preserved and accessible

## 🔗 Resources

- **Repository**: https://github.com/DDD-Enterprises/dopemux-mvp
- **Documentation**: https://docs.dopemux.dev
- **Issue Tracker**: https://github.com/DDD-Enterprises/dopemux-mvp/issues
- **Discussions**: https://github.com/DDD-Enterprises/dopemux-mvp/discussions

## 🎓 Learning Path

1. **Start Here**: `docs/QUICK_START.md`
2. **Architecture**: `docs/04-explanation/architecture/`
3. **Development**: `docs/02-how-to/development/`
4. **Migration Guide**: `docs/MIGRATION_TASKX_TO_DOPETASK.md`
5. **API Reference**: `docs/03-reference/api/`

---

**Last Updated**: 2024-02-24
**Maintainer**: dopemux team
**Status**: Active development ✅
