---
id: EXHAUSTIVE-AUDIT-PLAN
title: Exhaustive Audit Plan
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Exhaustive Audit Plan (reference) for dopemux documentation and developer
  workflows.
---
# Exhaustive Line-by-Line Code Audit Plan
**Date**: 2025-10-16
**Requirement**: Every line of code reviewed, every doc claim verified against actual behavior
**Estimated Time**: 80-120 hours (2-3 weeks full-time)
**Method**: Automated + Manual Hybrid

---

## Critical Requirement: Documentation Accuracy

**USER MANDATE**: "Docs must reflect actual functionality and behavior of the code"

This means:
- ✅ Every code example must actually run
- ✅ Every API endpoint claim must exist in code
- ✅ Every feature claim must be implemented
- ✅ Every architecture diagram must match current code
- ✅ Every configuration setting must work

**NOT acceptable**:
- ❌ Outdated documentation
- ❌ Aspirational claims (planned but not built)
- ❌ Code examples that don't work
- ❌ Architecture diagrams of ideal state (not current state)

---

## Phase 1: Complete Codebase Inventory (6 hours)

### 1A: Line Count and File Inventory (1h)

**Objective**: Know EXACTLY what we're auditing

```bash
# Total line count by language
cloc . --exclude-dir=node_modules,__pycache__,.git,venv --by-file-by-lang > INVENTORY-lines-by-file.txt

# File count by type
find . -type f -name "*.py" | wc -l > python_file_count.txt
find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" | wc -l > js_file_count.txt
find . -type f -name "*.md" | wc -l > doc_file_count.txt

# Service inventory
for svc in services/*/; do
    echo "=== $(basename $svc) ===" >> SERVICE-INVENTORY.txt
    cloc "$svc" --quiet >> SERVICE-INVENTORY.txt
done
```

**Deliverable**:
- INVENTORY-lines-by-file.txt (every file with line count)
- SERVICE-INVENTORY.txt (per-service metrics)
- Total lines to review: X Python, Y TypeScript, Z total

---

### 1B: Dependency Mapping (2h)

**Objective**: Understand all dependencies and call graphs

```bash
# Python dependencies
pipdeptree > python-dependencies.txt
pip list --format=freeze > requirements-actual.txt

# Find all imports
grep -rn "^import \|^from " --include="*.py" src/ services/ > all-imports.txt

# Service-to-service calls
grep -rn "http://\|https://\|localhost:" --include="*.py" > service-calls.txt

# Database access points
grep -rn "execute\|fetch\|commit\|cursor" --include="*.py" > database-access.txt

# File I/O operations
grep -rn "open(\|read(\|write(\|Path(" --include="*.py" > file-operations.txt
```

**Deliverable**:
- Complete dependency graph
- All service-to-service communication points
- All database access points
- All file I/O operations

---

### 1C: Entry Point and API Catalog (1h)

**Objective**: Find every way code can be executed

```bash
# Python entry points
grep -rn "if __name__ == '__main__'" --include="*.py" > main-entry-points.txt
grep -rn "async def main\|def main" --include="*.py" > main-functions.txt

# API endpoints
grep -rn "@router\.\|@app\.\|@api\." --include="*.py" > api-decorators.txt

# MCP tools
grep -rn "@mcp\|mcp.types.Tool\|Tool(" --include="*.py" > mcp-tools.txt

# CLI commands
grep -rn "click\.\|argparse\|sys.argv" --include="*.py" > cli-interfaces.txt
```

**Deliverable**: Complete catalog of execution entry points

---

### 1D: Configuration Inventory (1h)

**Objective**: Find all configuration points

```bash
# Environment variables
grep -rn "os.getenv\|os.environ\|getenv" --include="*.py" > env-vars.txt

# Config files
find . -name "*.toml" -o -name "*.ini" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" | grep -v node_modules > config-files.txt

# Hardcoded values
grep -rn "= \".*\"\|= '.*'" --include="*.py" | grep -i "host\|port\|url\|password\|key\|secret" > hardcoded-configs.txt
```

**Deliverable**: All configuration points documented

---

### 1E: Documentation Inventory (1h)

**Objective**: Catalog all documentation claims

```bash
# All markdown files with metadata
for file in $(find docs -name "*.md"); do
    echo "FILE: $file" >> DOC-INVENTORY.txt
    head -20 "$file" | grep -E "^#|Features:|API:|Endpoints:" >> DOC-INVENTORY.txt
    echo "---" >> DOC-INVENTORY.txt
done

# Extract all code examples
grep -B 2 -A 15 '```python' docs/**/*.md > python-examples-from-docs.txt
grep -B 2 -A 15 '```bash' docs/**/*.md > bash-examples-from-docs.txt
grep -B 2 -A 15 '```typescript' docs/**/*.md > ts-examples-from-docs.txt

# Feature claims
grep -rn "provides\|supports\|enables\|implements" docs/ --include="*.md" -i > feature-claims.txt
```

**Deliverable**:
- Complete documentation inventory
- All code examples extracted
- All feature claims cataloged

---

## Phase 2: Automated Security & Quality Scan (8-10 hours)

### 2A: Comprehensive Security Scan (4h)

**Every Vulnerability Type**:

```bash
# 1. SQL Injection (all patterns)
grep -rn "execute.*f\"\|execute.*f'\|execute.*%" --include="*.py" > sql-injection-candidates.txt
grep -rn "cursor.*format\|query.*format" --include="*.py" >> sql-injection-candidates.txt

# 2. Command Injection
grep -rn "subprocess.run\|subprocess.Popen\|os.system\|os.popen" --include="*.py" > command-injection-risks.txt

# 3. Path Traversal
grep -rn "open(.*input\|Path(.*request\|joinpath.*user" --include="*.py" > path-traversal-risks.txt

# 4. ReDoS (all regex)
grep -rn "re.compile\|re.match\|re.search\|=~" --include="*.py" > regex-patterns.txt

# 5. Deserialization
grep -rn "pickle.load\|yaml.load\|eval(\|exec(" --include="*.py" > deserialization-risks.txt

# 6. Authentication bypass
grep -rn "@router\|@app" --include="*.py" | grep -v "Depends\|Security\|auth" > unprotected-endpoints.txt

# 7. Secrets in code
grep -rn "password\|api_key\|secret\|token" --include="*.py" | grep "= \"\|= '" > potential-secrets.txt

# 8. CORS/XSS (if web interfaces)
grep -rn "CORSMiddleware\|allow_origins\|innerHTML\|dangerouslySetInnerHTML" > web-security.txt
```

**Manual Review**: Every flagged line must be manually reviewed for actual vulnerability

---

### 2B: Code Quality Deep Scan (3h)

```bash
# Full pylint (every rule)
pylint src/ services/ --rcfile=.pylintrc --output-format=parseable > pylint-complete.txt

# Full flake8 (all rules)
flake8 src/ services/ --max-line-length=100 --statistics > flake8-complete.txt

# Type coverage
mypy src/ services/ --strict --html-report mypy-coverage > mypy-strict.txt

# Complexity metrics
radon cc src/ services/ -a -s -j > complexity-by-file.json
radon mi src/ services/ -s -j > maintainability-by-file.json

# Cyclomatic complexity (find complex functions)
radon cc src/ services/ -n C -s > high-complexity-functions.txt  # C rating = needs review

# Code duplication
pylint src/ services/ --disable=all --enable=R0801 > code-duplication.txt
```

**Manual Review**: Every high-complexity function, every duplication

---

### 2C: Pattern Analysis (2h)

```bash
# Error handling patterns
grep -rn "try:\|except:\|raise\|throw" --include="*.py" > error-handling.txt

# Async patterns
grep -rn "async def\|await\|asyncio" --include="*.py" > async-patterns.txt

# Database transactions
grep -rn "begin\|commit\|rollback\|transaction" --include="*.py" > transactions.txt

# Resource cleanup
grep -rn "close(\|cleanup(\|__exit__\|finally:" --include="*.py" > resource-cleanup.txt

# State management
grep -rn "self\.\|state\|status" --include="*.py" | grep "= " > state-changes.txt
```

**Manual Review**: Verify patterns are correct (error handling complete, resources cleaned up, etc.)

---

### 2D: Test Coverage Analysis (1h)

```bash
# After fixing imports:
pytest --cov=src --cov=services --cov-report=json --cov-report=html --cov-report=term-missing

# Parse coverage report to find:
# - Untested functions
# - Uncovered branches
# - Missing edge case tests

python << 'EOF'
import json
with open('coverage.json') as f:
    cov = json.load(f)
    for file, data in cov['files'].items():
        if data['summary']['percent_covered'] < 80:
            print(f"LOW COVERAGE: {file} - {data['summary']['percent_covered']}%")
EOF
```

**Manual Review**: Write tests for all uncovered code

---

## Phase 3: Manual Code Review (30-40 hours)

### 3A: Service-by-Service Deep Dive (24-32h, ~2h per service)

**For EACH of 14 services**:

**Step 1: Review Main Entry Point** (20 min)
- Read main.py or server.py line-by-line
- Understand initialization sequence
- Verify error handling
- Check resource cleanup

**Step 2: Review Core Business Logic** (60 min)
- Read every function in src/
- Verify algorithms are correct
- Check edge case handling
- Validate state transitions
- Test error paths mentally (or actually)

**Step 3: Review Integration Points** (20 min)
- Check all service-to-service calls
- Verify event bus usage
- Review database operations
- Check API clients

**Step 4: Review Tests** (20 min)
- Read test files
- Verify tests actually test the code
- Check for missing test cases
- Validate mocks are realistic

**Per Service**: ~2 hours × 14 services = 28 hours

---

### 3B: Cross-Service Integration Review (4h)

**Review Integration Patterns**:
- ConPort ↔ ADHD Engine (direct SQLite - already flagged)
- ConPort ↔ DopeconBridge (TODOs - already flagged)
- Serena ↔ ConPort (integration status)
- Dope-Context ↔ Services (search integration)
- Event Bus usage across all services

**Verify**:
- Authority boundaries respected
- Event routing works
- Error propagation handled
- Timeouts configured

---

### 3C: Algorithm Correctness Review (4h)

**Focus on Complex Logic**:
- ML risk prediction algorithms (Task-Orchestrator)
- Complexity scoring algorithms (Serena, Dope-Context)
- Pattern learning (Serena intelligence)
- Search relevance scoring (Dope-Context)
- Cognitive load calculation (multiple services)

**For Each Algorithm**:
- Read implementation line-by-line
- Verify math is correct
- Check boundary conditions
- Test with sample inputs (mentally or actually)

---

## Phase 4: Documentation Validation (15-20 hours)

### 4A: Code Example Verification (8-10h)

**For EVERY code example in docs**:

```python
# Extract example
example_code = extract_from_markdown("docs/some-guide.md", block_num=1)

# Try to run it
try:
    exec(example_code)
    print("✅ Example works")
except Exception as e:
    print(f"❌ Example broken: {e}")
    # Document discrepancy
```

**Process**:
1. Extract all Python/TypeScript/Bash examples
2. Attempt to run each one
3. Document which ones fail
4. Either fix code OR update documentation

**Est**: 50+ code examples × 10 min each = 8-10 hours

---

### 4B: API Documentation Validation (3-4h)

**For EVERY documented API endpoint**:

1. **Find in Docs**: `POST /api/assess-task`
2. **Find in Code**: Search for `@router.post("/assess-task")`
3. **Verify Match**:
   - Parameters match?
   - Response format matches?
   - Status codes documented?
   - Error cases covered?

**For Each Service API**:
- Read API docs
- Find actual endpoints in code
- Compare request/response schemas
- Test with actual requests (or manual trace)
- Document discrepancies

---

### 4C: Feature Claim Validation (2-3h)

**For EVERY feature claim** (e.g., "Provides real-time risk prediction"):

1. **Extract Claim**: From README or docs
2. **Find Implementation**: Trace through code
3. **Verify**:
   - Feature actually exists?
   - Works as described?
   - Has tests?
   - No TODOs/stubs?

**Categories**:
- ADHD features (energy tracking, attention monitoring, etc.)
- ML capabilities (risk prediction, pattern learning)
- Integration features (event bus, API calls)
- Performance claims (< 200ms, etc.)

---

### 4D: Architecture Diagram Validation (2-3h)

**For EVERY architecture diagram**:

1. **Read Diagram**: Two-plane architecture, service boundaries, etc.
2. **Trace in Code**: Find actual service calls, database access, event routing
3. **Verify**: Does code match diagram?
4. **Document Gaps**: Where does reality differ from diagrams?

**Examples**:
- Two-plane diagram shows DopeconBridge coordination
- Code shows direct database access (ADHD Engine)
- **Action**: Update diagram OR fix code

---

## Phase 5: Line-by-Line Code Logic Review (40-50 hours)

### 5A: Function-by-Function Review (30-40h)

**For EVERY function in the codebase**:

**Review Checklist** (5-10 min per function):
```
[ ] Function name describes behavior accurately?
[ ] Parameters validated/typed correctly?
[ ] Return type matches docstring?
[ ] Error cases handled?
[ ] Edge cases covered?
[ ] State changes are intentional?
[ ] Resource cleanup (if applicable)?
[ ] Thread-safe (if concurrent)?
[ ] Async patterns correct (if async)?
[ ] Comments explain WHY not WHAT?
[ ] Complexity reasonable (<10 cyclomatic)?
[ ] Has tests covering main paths?
```

**Estimation**:
- Average: 50-100 functions per service
- 14 services = 700-1400 functions
- @ 5 min each = 58-117 hours

**Optimization**: Focus on:
- High complexity functions (radon C/D/F ratings)
- Security-sensitive functions (auth, DB, file I/O)
- Core business logic (skip obvious getters/setters)

**Realistic**: 30-40 hours for critical functions

---

### 5B: State Machine Validation (4h)

**For services with state**:
- ADHD Engine (energy states, attention states)
- Task-Orchestrator (task status transitions)
- DopeconBridge (connection states)

**Validate**:
- All state transitions are valid
- No orphan states
- Exit conditions exist
- Error states handled

---

### 5C: Concurrency Correctness (4h)

**Review all async code**:
- Proper await usage
- No race conditions
- Lock/semaphore usage correct
- Deadlock prevention
- Task cancellation handled

---

### 5D: Database Query Correctness (2h)

**Beyond security (which we did)**:
- Queries return expected data?
- Indexes exist for performance?
- Transactions used appropriately?
- Migrations are reversible?
- Connection pooling configured correctly?

---

## Phase 6: Integration Testing & Validation (10-15 hours)

### 6A: Fix Testing Infrastructure (4h)

```bash
# Fix import issues
# - Resolve ../dopemux-mvp/ dependency
# - Make code-audit self-contained OR
# - Fix parent workspace dataclass issues

# Consolidate pytest config
# - Choose pytest.ini OR pyproject.toml
# - Register all markers properly
```

---

### 6B: Run All Tests (2h)

```bash
# Run complete suite
pytest tests/ -v --cov=src --cov=services --cov-report=html

# Expected: 785 tests
# Target: >80% pass rate initially
```

---

### 6C: Fix Test Failures (4-6h)

**For each failing test**:
1. Understand what's being tested
2. Check if code changed (breaking test)
3. Check if test is wrong
4. Fix code OR update test
5. Re-run until passing

---

### 6D: Write Missing Tests (2-3h)

**Based on coverage report**:
- Untested functions
- Uncovered branches
- Edge cases not tested

---

## Phase 7: Documentation-Code Alignment (15-20 hours)

### 7A: Run Every Code Example (8-10h)

**Process** (for ~50 examples):
```bash
# For each code example in docs:
python << 'EOF'
# Example code from docs
from some_service import SomeClass
result = SomeClass().some_method()
# Does this work?
EOF

# If fails:
# - Fix code? OR
# - Update documentation?
# - Document decision
```

---

### 7B: Verify Every API Endpoint (3-4h)

**For each documented endpoint**:
```bash
# Example: POST /assess-task documented
# 1. Find in code
grep -rn "assess-task" services/

# 2. Compare schemas
# Docs say: {user_id, task_data, ...}
# Code expects: ???

# 3. Test (if running) or trace manually
curl -X POST localhost:8095/assess-task -d '{"user_id": "test"}'

# 4. Document matches/mismatches
```

---

### 7C: Verify Architecture Claims (2-3h)

**Claims in .claude/CLAUDE.md and docs/94-architecture/**:

**Example Claims**:
- "ConPort is the single source of truth for decisions"
  - **Verify**: Does ADHD Engine write to ConPort DB directly? (YES - violation)
- "DopeconBridge handles all cross-plane communication"
  - **Verify**: Do services use it? (NO - they bypass it)
- "ADHD Engine provides energy tracking"
  - **Verify**: Does it? (YES - implementation exists)

**For Each Claim**:
1. Find claim in documentation
2. Trace through code
3. Verify or document discrepancy
4. Update docs OR flag as architectural debt

---

### 7D: Service README Accuracy (2-3h)

**For each service's README**:
- Features listed → Verify in code
- Installation steps → Actually follow them
- Usage examples → Run them
- Configuration → Check if options work
- Architecture described → Match against code

---

## Phase 8: Final Synthesis & Reporting (6-8 hours)

### 8A: Create Discrepancy Report (2h)

**Document EVERY mismatch**:
- Code vs docs
- Claimed vs actual features
- Architecture diagrams vs reality
- API docs vs endpoints

---

### 8B: Prioritize Fixes (1h)

**Categorize**:
- Critical: Security, broken features
- High: Documentation misleading users
- Medium: Minor discrepancies
- Low: Typos, formatting

---

### 8C: Create Fix Roadmap (2h)

**For each discrepancy**:
- Should we fix code?
- Should we update docs?
- Is it architectural debt to document?
- What's the effort estimate?

---

### 8D: Final Report & ADR (1h)

- ADR-206: Exhaustive Audit Results
- Complete findings document
- Prioritized fix list
- Updated ConPort decisions

---

## Estimated Timeline

| Phase | Hours | Deliverable |
|-------|-------|-------------|
| 1. Inventory | 6 | Complete codebase map |
| 2. Automated Scan | 10 | Vulnerability + quality reports |
| 3. Manual Code Review | 40 | Every function validated |
| 4. Documentation Validation | 18 | Docs-code alignment verified |
| 5. Integration Testing | 12 | All tests passing |
| 6. Final Synthesis | 7 | Complete audit report |
| **TOTAL** | **93 hours** | **Exhaustive audit** |

---

## Execution Strategy

**Week 1** (40h): Phases 1-2 + Start Phase 3
- Complete automated analysis
- Begin manual service reviews

**Week 2** (40h): Phase 3 + Phase 4
- Complete service deep dives
- Documentation validation

**Week 3** (13h): Phase 5 + Phase 6
- Integration testing
- Final synthesis

---

## Success Criteria

✅ **Every line of code reviewed manually**
✅ **Every function's correctness validated**
✅ **Every documentation claim verified against code**
✅ **Every code example tested and working**
✅ **All 785 tests passing**
✅ **Documentation 100% accurate to current code**
✅ **No discrepancies between docs and reality**

---

**This is the plan for TRUE exhaustive audit.**

Ready to execute? This is a **93-hour commitment** for absolute thoroughness.
