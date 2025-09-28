Complete feature implementation with full quality gates and git/PR workflow.

## Pre-Flight Quality Gates

### 1. Completeness Verification
```bash
# Run all quality checks
python -m pip install -e .[dev]
ruff check .                          # Lint clean
mypy src                             # Type clean
pytest --cov=src/chatx --cov-fail-under=90  # 90% coverage
pytest --cov-report=term-missing      # Show missing coverage
```

### 2. Code Quality Validation
- ✅ **Lint**: No style violations (`ruff check .`)
- ✅ **Types**: No type errors (`mypy src`)
- ✅ **Coverage**: ≥90% (`pytest --cov-fail-under=90`)
- ✅ **Tests**: All tests passing

### 3. Thoroughness Checklist
- ✅ **Documentation**: README/docs updated for new features
- ✅ **ADR**: Architecture Decision Record stub if design changed
- ✅ **TODO**: Update project TODO with completed items
- ✅ **ConPort**: Log implementation decisions/completion
- ✅ **Memory**: Update project context if significant changes

## Git Workflow (Feature Branch Strategy)

### Branch Management for Multi-Session Support
```bash
# Create feature branch (multi-session friendly)
git checkout -b feature/your-feature-name
# or for concurrent sessions:
git checkout -b feature/session-1-feature-a
git checkout -b feature/session-2-feature-b
```

### Commit with Conventional Format
```bash
git add -A
git commit -m "feat(scope): implement feature with tests

- Add feature implementation
- Comprehensive test coverage
- Update documentation
- Quality gates: lint ✓, mypy ✓, cov ≥90% ✓"
```

### PR Creation and Management
```bash
# Create detailed PR
gh pr create \
  --title "feat: implement feature name" \
  --body "Feature implementation with complete quality gates.

## Implementation
- Feature details
- Architecture decisions
- Test coverage

## Quality Gates
- ✅ Lint clean (ruff)
- ✅ Type clean (mypy)
- ✅ Coverage ≥90%
- ✅ All tests passing

## Documentation
- ✅ README updated
- ✅ ADR stub created (if applicable)
- ✅ ConPort decisions logged

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>" \
  --label "enhancement,testing"

# Monitor CI and merge when ready
gh pr checks
gh pr merge --squash
```

## Workflow Steps

1. **Quality Gates**: Run completeness verification
2. **Documentation**: Update docs, create ADR if needed
3. **Memory Update**: Log to ConPort, update project context
4. **Branch Strategy**: Create feature branch for multi-session support
5. **Commit**: Conventional commit with detailed message
6. **PR**: Create comprehensive PR with quality gate status
7. **Monitor**: Track CI checks and merge when ready

## Multi-Session Branch Strategy

For concurrent Claude Code sessions:
```
main
├── feature/auth-system (Session 1)
├── feature/payment-integration (Session 2)
└── feature/ui-redesign (Session 3)
```

Each session works independently on its feature branch, maintaining isolation until PR ready.

## Definition of Done

✅ **Code Quality**: Lint, types, tests clean with ≥90% coverage
✅ **Documentation**: Updated for feature changes
✅ **Architecture**: ADR stub if design decisions made
✅ **Testing**: Complete test coverage for new functionality
✅ **Git Flow**: Feature branch → conventional commit → detailed PR
✅ **Multi-Session**: Branch isolation maintained for concurrent work
✅ **Memory**: ConPort decisions logged, project context updated