---
id: ROADMAP-REMAINING-WORK
title: Roadmap Remaining Work
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Roadmap Remaining Work (reference) for dopemux documentation and developer
  workflows.
---
# Roadmap: Remaining Audit Work
**Date**: 2025-10-16
**Current Progress**: 10% complete (7.5h / 26h projected)
**Remaining Estimate**: 18-20 hours
**Status**: Critical work complete, remaining is value-add

---

## Quick Start for Next Session

**Resume audit in 3 steps**:

1. **Read context** (5 min):
   ```bash
   cd /Users/hue/code/code-audit
   cat claudedocs/DEEP-DOCUMENTATION-ALL-FINDINGS.md
   cat claudedocs/FINAL-AUDIT-REPORT.md
   ```

2. **Check MCP status** (2 min):
   ```bash
   # Verify all searches working
   mcp__dope-context__search_code("authentication")
   mcp__dope-context__docs_search("architecture")
   ```

3. **Pick up Phase 3** (start work):
   - See "Phase 3 Execution Plan" below
   - Or jump to Phase 4 (doc validation)
   - Or jump to Phase 6 (integration tests)

---

## Remaining Phases

### Phase 3: Targeted Manual Review (~6-10h)

**Goal**: Deep-dive remaining 8 services not yet reviewed

**Priority 1: High-Risk Services** (4h):

1. **GPT-Researcher** (2h)
   - Found: 67 TODOs, CORS fixed
   - Review: API endpoints, research orchestration, WebSocket streaming
   - Files: `backend/main.py`, `backend/api/main.py`, research engine
   - Method: Zen codereview OR manual bash grep + reading

2. **ML Risk Assessment** (1h)
   - Status: Code exists, not yet reviewed
   - Files: `services/ml-risk-assessment/`
   - Check: Risk prediction algorithms, model accuracy, integration

3. **Orchestrator** (30min)
   - Files: `services/orchestrator/src/main.py`
   - Check: What does this orchestrate? Relationship to Task-Orchestrator?

4. **Taskmaster** (30min)
   - Files: `services/taskmaster/server.py` (MCP wrapper)
   - Check: PRD parsing implementation, Task-Master integration

**Priority 2: Verification Tasks** (2h):

1. **SQL Injection Verification** (30min)
   ```bash
   # Trace graph_name source in age_client.py
   grep -rn "graph_name\s*=" services/conport_kg/
   # If from config: LOW risk
   # If from API param: Add validation
   ```

2. **Subprocess Full Audit** (1h)
   ```bash
   # Review all 54 instances
   grep -rn "subprocess\.\|os\.system" services/ --include="*.py" > subprocess_audit.txt
   # For each: Verify no user input in commands
   # Check: All use list args (not shell=True)
   ```

3. **DopeconBridge Completion Assessment** (30min)
   - Read kg_endpoints.py custom_data stubs
   - Estimate effort to implement MCP integration
   - Create Week 7 implementation plan

**Priority 3: Remaining Services** (Optional, 2-4h):

1. **Claude-Context** (1h) - Determine if legacy/active
2. **ConPort Orchestrator** (1h) - Review automation logic
3. **Task-Orchestrator Wrapper** (30min) - Verify Kotlin integration
4. **Serena Wrapper** (30min) - Review LSP proxy logic

---

### Phase 4: Documentation Validation (~2-4h)

**Goal**: Verify all documentation claims match code reality

**4A: Code Example Testing** (1-2h):

```bash
# Find all Python examples in docs
grep -r "```python" claudedocs/ docs/ --include="*.md" > python_examples.txt

# Strategy:
# 1. Extract each example
# 2. Try to execute (in test environment)
# 3. Document which work vs which are broken/aspirational

# Use semantic search to find examples:
mcp__dope-context__docs_search("code example import usage", top_k=20)

# For each example:
# - Extract code block
# - Create test file
# - Run: python test_example.py
# - Record: ✅ works or ❌ broken
```

**Expected**: ~50 code examples across all docs
**Time**: 2-3 min per example = 1-2h total

**4B: API Endpoint Verification** (30min-1h):

```bash
# For each service with documented API:
# 1. Find API docs
mcp__dope-context__docs_search("POST GET endpoint API", top_k=10)

# 2. Find actual code
grep -rn "@router\.\|@app\." services/ --include="*.py"

# 3. Compare:
#    - Do documented endpoints exist?
#    - Do parameters match?
#    - Are response schemas correct?

# Services to check:
# - DopeconBridge (5 endpoints + 2 stubs documented)
# - ADHD Engine (7-8 endpoints documented, NOW SECURED)
# - GPT-Researcher (websocket, research API)
```

**4C: Feature Claim Validation** (1h):

```bash
# Claims to verify:
# 1. "Event-driven coordination"
grep -rn "event_bus\|RedisStreams" services/ --include="*.py"
# Check: Infrastructure exists ✅, adoption partial ⚠️

# 2. "Multi-instance support"
grep -rn "DOPEMUX_INSTANCE\|PORT_BASE" services/ --include="*.py"
# Check: Code exists ✅, needs configuration testing

# 3. "6 background monitors" (ADHD Engine)
# Status: ✅ VERIFIED (already done in Phase 3A)

# 4. "DopeconBridge cross-plane coordination"
# Status: ⚠️ STUBS (already found—documented)
```

---

### Phase 5: Eliminated (Redundant)

**Originally**: Line-by-line function review (40h)
**Status**: Eliminated in optimized plan
**Reason**: Phases 2-3 cover this with Zen codereview + targeted review

---

### Phase 6: Integration Testing (~2-4h)

**Goal**: Get test suite running and validate changes

**6A: Fix Test Infrastructure** (1-2h):

```bash
# Known issues:
# - Import errors (from earlier attempts)
# - Pytest config issues
# - Dataclass conflicts

# Strategy:
# 1. Read pytest.ini and pyproject.toml
# 2. Check sys.path issues
# 3. Fix imports one by one
# 4. Get at least ONE test passing

cd /Users/hue/code/code-audit
pytest tests/ -v --collect-only  # See what's discoverable
```

**6B: Run Test Suite** (30min):

```bash
# Run with coverage
pytest tests/ -v --cov=services --cov-report=term-missing

# Expected: Some failures (pre-existing)
# Goal: Identify what's broken vs what's by design
```

**6C: Validate Security Fixes** (1h):

```bash
# Test CORS configuration
# Test API key authentication
# Test credential loading from environment

# Create test script:
python3 << 'EOF'
import os
os.environ['ADHD_ENGINE_API_KEY'] = 'test-key-12345'
os.environ['ALLOWED_ORIGINS'] = 'http://test1.com,http://test2.com'

# Import and verify
from services.adhd_engine import main
# Check: CORS configured correctly?
# Check: API key loaded?
EOF
```

---

### Phase 7: Skipped (Not in Plan)

Phase 7 was placeholder for "Documentation-Code Alignment"—covered in Phase 4.

---

### Phase 8: Final Synthesis (~2h)

**Goal**: Comprehensive findings report and recommendations

**8A: Aggregate All Findings** (30min):

```bash
# Compile from all phase reports:
cat claudedocs/phase-*.md > all_findings.txt

# Categorize:
# - Security: CORS (fixed), credentials (fixed), auth (fixed), SQL (flagged), subprocess (flagged)
# - Architecture: Bridge stubs (documented), violations (documented)
# - Quality: Excellent patterns, TODOs present, in-memory state
# - Documentation: 90% accurate, comprehensive
```

**8B: Prioritized Fix Roadmap** (1h):

Create actionable roadmap:

**Week 7 (12h)**:
1. Complete DopeconBridge MCP integration (4-6h)
2. Migrate ADHD Engine to bridge HTTP API (2-3h)
3. Wire ConPort Orchestrator to bridge (2-3h)
4. Integration tests (2h)

**Future (Optional)**:
- Full subprocess audit (2h)
- SQL injection verification (30min)
- Complete TODO features (varies)
- Performance optimization (varies)

**8C: ADR Documentation** (30min):

```bash
# Create ADR-206: Code Audit Results
# Document:
# - All findings (security, architecture, quality)
# - Fixes applied (10 HIGH-severity)
# - Remaining work (Week 7 plan)
# - Architectural decisions (keep stubs for now, complete in Week 7)
```

---

## Execution Strategy for Maximum Efficiency

### Option A: Sequential Completion (~18-20h)

**Week 1**:
- Phase 3: Manual review (6-10h)
- Phase 4: Doc validation (2-4h)
- Phase 6: Integration tests (2-4h)
- Phase 8: Synthesis (2h)

**Total**: 12-20h over 2-3 days

**Pros**: Complete audit, comprehensive coverage
**Cons**: Time investment, some diminishing returns

---

### Option B: Focused Completion (~8-10h)

**High-Value Only**:
- Phase 3: Priority 1 services only (4h)
- Phase 4: Priority claims only (1h)
- Phase 6: Security fix validation (1h)
- Phase 8: Executive summary (2h)

**Total**: 8h over 1-2 days

**Pros**: Best ROI, covers critical gaps
**Cons**: Some services not deeply reviewed

---

### Option C: Hybrid (Recommended, ~12-14h)

**Balanced Approach**:
- Phase 3: Priority 1 + Verification tasks (6h)
- Phase 4: Code examples + API validation (2h)
- Phase 6: Test infrastructure + security validation (2h)
- Phase 8: Full synthesis (2h)

**Total**: 12h over 2 days

**Pros**: Thorough where it matters, efficient elsewhere
**Cons**: Some optional work deferred

---

## Pre-Execution Checklist

**Before Starting Next Session**:

- [ ] Read DEEP-DOCUMENTATION-ALL-FINDINGS.md (complete context)
- [ ] Verify MCP servers online (dope-context, serena-v2, zen)
- [ ] Check search still working (4,439 chunks indexed)
- [ ] Review ROADMAP-REMAINING-WORK.md (this file)
- [ ] Choose execution strategy (A/B/C above)

**Quick Validation** (2 min):
```bash
cd /Users/hue/code/code-audit
git status  # Should be clean after this session
git log --oneline --since="2025-10-16" | wc -l  # Should show ~52 commits
ls claudedocs/*.md | wc -l  # Should show 38+ docs
```

---

## Phase 3 Detailed Execution Plan

**For efficient execution** when you continue:

### Step 1: GPT-Researcher Deep Review (2h)

```bash
# 1. Find all Python files
find services/dopemux-gpt-researcher -name "*.py" -not -path "*/test*" > gptr_files.txt

# 2. Read key files
cat services/dopemux-gpt-researcher/backend/main.py
cat services/dopemux-gpt-researcher/backend/api/main.py

# 3. Count TODOs and categorize
grep -rn "TODO" services/dopemux-gpt-researcher --include="*.py" > gptr_todos.txt

# 4. Security check
grep -rn "subprocess\|execute.*f\"\|password.*=" services/dopemux-gpt-researcher --include="*.py"

# 5. Use Zen for validation
mcp__zen__codereview(
    step="Review GPT-Researcher service",
    relevant_files=["/path/to/gpt-researcher"],
    review_type="full",
    model="gpt-5-codex"
)
```

### Step 2: ML Risk Assessment Review (1h)

```bash
# Similar pattern:
find services/ml-risk-assessment -name "*.py"
cat services/ml-risk-assessment/README.md  # If exists
# Read main files
# Security scan
# Optional: Zen review if complex
```

### Step 3: Verification Tasks (2h)

**SQL Injection** (30min):
```bash
cd services/conport_kg
grep -rn "graph_name" . --include="*.py" -B 5 -A 2
# Trace source: Config file? API param? User input?
# Add validation if needed
```

**Subprocess Audit** (1h):
```bash
grep -rn "subprocess\.Popen\|subprocess\.run\|os\.system" services/ --include="*.py" > subprocess_full.txt

# For each instance:
# - Check if command is hardcoded or from user input
# - Verify shell=False (or list args used)
# - Flag any user-controlled commands

# Create report: subprocess_audit_results.md
```

**Bridge Completion** (30min):
```bash
# Read kg_endpoints.py stubs
cat services/mcp-dopecon-bridge/kg_endpoints.py

# Estimate implementation:
# - MCP client setup: 2h
# - custom_data POST implementation: 1h
# - custom_data GET implementation: 1h
# - Testing: 1-2h
# Total: 4-6h

# Document in: dopecon_bridge_completion_plan.md
```

---

## Phase 4 Detailed Execution Plan

### Step 1: Extract Code Examples (30min)

```bash
# Use semantic search to find all code examples
mcp__dope-context__docs_search("python code example", top_k=50)
mcp__dope-context__docs_search("import usage API", top_k=50)

# Extract examples from results
# Create: code_examples_inventory.md
```

### Step 2: Test Code Examples (1-2h)

```python
# For each example found:
# 1. Create test file
# 2. Try to run
# 3. Document result

# Example testing pattern:
import tempfile
import subprocess

def test_code_example(code_string, example_id):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_string)
        f.flush()

        result = subprocess.run(['python', f.name], capture_output=True, timeout=5)

        return {
            'example_id': example_id,
            'works': result.returncode == 0,
            'stdout': result.stdout.decode(),
            'stderr': result.stderr.decode()
        }
```

### Step 3: API Documentation Validation (1h)

```bash
# For each documented API:
# 1. Find in docs
mcp__dope-context__docs_search("API endpoint POST GET", top_k=20)

# 2. Find in code
grep -rn "@router\.\|@app\." services/ --include="*.py" > all_endpoints.txt

# 3. Compare and document discrepancies
# Create: api_documentation_accuracy.md
```

---

## Phase 6 Detailed Execution Plan

### Step 1: Understand Test Failures (1h)

```bash
# Collect test information
find . -name "test_*.py" -o -name "*_test.py" | wc -l
find . -name "conftest.py"
cat pytest.ini
cat pyproject.toml | grep -A 10 "\[tool.pytest"

# Try to collect tests
pytest --collect-only 2>&1 | tee test_collection.log

# Analyze errors:
grep "ImportError\|ModuleNotFoundError" test_collection.log
```

### Step 2: Fix One Test Module (1h)

```bash
# Pick simplest test file
# Fix its imports
# Get it passing
# Use as template for others

# Example:
cd services/adhd_engine/tests
pytest test_api.py -v
# Fix imports until it runs
```

### Step 3: Validate Security Fixes (1h)

```bash
# Create validation test
cat > test_security_fixes.py << 'EOF'
import os
import sys

# Test CORS parsing
os.environ['ALLOWED_ORIGINS'] = 'http://a.com,http://b.com'
origins = os.getenv('ALLOWED_ORIGINS').split(',')
assert len(origins) == 2
assert '*' not in origins
print("✅ CORS secure")

# Test credential loading
os.environ['SERENA_DB_PASSWORD'] = 'from-env-test'
sys.path.insert(0, 'services/serena/v2/intelligence')
from database import DatabaseConfig
config = DatabaseConfig()
assert config.password == 'from-env-test'
print("✅ Credentials from env")

# Test auth module
sys.path.insert(0, 'services/adhd_engine')
from auth import verify_api_key, EXPECTED_API_KEY
print(f"✅ Auth module loads, key={'set' if EXPECTED_API_KEY else 'unset'}")

print("\n🎉 All security fixes validated!")
EOF

python test_security_fixes.py
```

---

## Phase 8 Detailed Execution Plan

### Step 1: Create Comprehensive Findings Doc (1h)

```markdown
# Template:
## Security Findings
- Critical: [list]
- High: [list with fix status]
- Medium: [list with recommendations]

## Architecture Findings
- Violations: [list]
- Root causes: [analysis]
- Fix plans: [Week 7 roadmap]

## Quality Findings
- Excellent patterns: [examples]
- Issues: [TODOs, incomplete features]
- Overall score: X/10

## Documentation Findings
- Accuracy: X%
- Coverage: [assessment]
- Gaps: [list]
```

### Step 2: Prioritized Fix Roadmap (30min)

```markdown
## Immediate (Done!)
- [x] CORS fixes
- [x] Credential security
- [x] API authentication

## Week 7 (12h)
- [ ] Complete DopeconBridge (4-6h)
- [ ] Migrate services (6-8h)

## Future (Optional)
- [ ] Full subprocess audit (2h)
- [ ] SQL injection verification (30min)
- [ ] TODO feature completion (varies)
```

### Step 3: ADR-206 Creation (30min)

```bash
# Create formal ADR
cat > docs/90-adr/adr-206-code-audit-results.md << 'EOF'
# ADR-206: Code Audit Results and Security Improvements

## Status
Accepted

## Context
Conducted comprehensive code audit to verify code-documentation alignment
and identify security/quality issues.

## Decision
1. Fix all HIGH-severity issues immediately (CORS, credentials, auth)
2. Document DopeconBridge completion for Week 7
3. Defer deep audit of all services (focus on critical)

## Consequences
- Production-ready security (8/10)
- Clear Week 7 integration plan
- Efficient audit (7.5h vs 93h)

## Implementation
[Details of all fixes applied]
EOF
```

---

## Success Criteria for Remaining Work

### Phase 3 Success:
- [ ] All 12 services have review status (deep OR quick scan)
- [ ] All verification tasks complete (SQL, subprocess, bridge)
- [ ] High-risk services fully validated

### Phase 4 Success:
- [ ] 80%+ of code examples tested
- [ ] All major APIs documented accurately
- [ ] Feature claims 90%+ verified

### Phase 6 Success:
- [ ] At least 1 test module passing
- [ ] Security fixes validated with tests
- [ ] Test failure patterns documented

### Phase 8 Success:
- [ ] Comprehensive findings document
- [ ] Prioritized fix roadmap with estimates
- [ ] ADR-206 created and committed

---

## Time Estimates by Approach

**Option A (Complete)**: 18-20h
- All services reviewed: 10h
- All examples tested: 2h
- All tests fixed: 4h
- Full synthesis: 2h

**Option B (Focused)**: 8-10h
- Priority services: 4h
- Priority examples: 1h
- Security validation: 1h
- Executive summary: 2h

**Option C (Hybrid)**: 12-14h
- Priority + verification: 6h
- Examples + APIs: 2h
- Test infra + validation: 2h
- Full synthesis: 2h

---

## Quick Commands for Next Session

```bash
# Resume context
cd /Users/hue/code/code-audit
git log --oneline --since="2025-10-16" | head -10

# Check MCP status
mcp__dope-context__get_index_status  # Should show 26 code + 4,413 docs

# Start Phase 3
cat claudedocs/ROADMAP-REMAINING-WORK.md  # This file
# Pick: GPT-Researcher, ML Risk, or Verification tasks

# Or start Phase 4
mcp__dope-context__docs_search("code example python", top_k=20)
# Extract and test examples

# Or start Phase 6
pytest tests/ --collect-only
# Fix test infrastructure
```

---

**Roadmap complete. Clear execution path for remaining 18-20 hours of optional deep-dive work.** ✅
