---
id: OPTIMIZED-AUDIT-PLAN
title: Optimized Audit Plan
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# OPTIMIZED Exhaustive Code Audit Plan (MCP-Enhanced)
**Date**: 2025-10-16
**Original**: 93 hours
**Optimized**: **44 hours** (52% reduction)
**Method**: MCP-powered automation + strategic manual review
**Status**: 3 core MCPs online (Serena-v2, Dope-Context, Zen)

---

## 🎯 Core Optimization Strategy

**Leverage MCP Capabilities**:
1. **Dope-Context**: Already has 158 code vectors indexed → instant semantic search
2. **Zen codereview**: Automate 700+ function reviews → manual review only flagged issues
3. **Serena-v2**: Complexity scoring → prioritize high-risk functions automatically
4. **PAL apilookup**: Validate framework usage → verify React/Next.js patterns instantly

**Key Insight**: Don't manually review what AI can validate. Focus human time on:
- Architecture violations
- Business logic correctness
- Documentation-code alignment
- Security vulnerabilities AI might miss

---

## Phase 1: Intelligent Inventory (6h → 2h)

### 1A: MCP-Powered Codebase Discovery (30 min)

**Use Dope-Context semantic search** instead of grep:

```python
# Instead of: find . -name "*.py" | wc -l
# Use MCP semantic search to understand codebase structure

# Find all entry points
search_code(query="main entry point __name__ == __main__", top_k=50)

# Find all API endpoints
search_code(query="API endpoint router decorator", top_k=50)

# Find all MCP tools
search_code(query="MCP tool decorator handler", top_k=50)

# Find all database operations
search_code(query="database query execute commit", top_k=50)
```

**Why faster**: Semantic search returns contextualized results immediately (< 2 sec per query)

---

### 1B: Service Catalog via Serena (20 min)

**Use Serena list_dir** + **Dope-Context search**:

```python
# Get service structure
serena.list_dir(relative_path="services", recursive=True)

# For each service, semantic search for:
# - Main functionality
# - Dependencies
# - Integration points

search_code(query="service initialization startup", filter_by_dir="services/adhd-engine")
```

**Deliverable**: Complete service map with:
- Entry points
- Core capabilities
- Integration points
- Complexity scores (from Serena)

---

### 1C: Dependency & Config Mapping (30 min)

**Smart pattern search**:

```python
# Environment variables
search_code(query="environment variable configuration getenv", top_k=30)

# Service-to-service calls
search_code(query="HTTP request client service call", top_k=30)

# Database connections
search_code(query="database connection pool configuration", top_k=20)
```

---

### 1D: Documentation Inventory (30 min)

**Already have markdown indexed in Dope-Context**:

```python
# Search all feature claims
docs_search(query="provides supports enables implements", top_k=50)

# Extract all code examples
docs_search(query="python code example snippet", top_k=50)

# Find API documentation
docs_search(query="API endpoint request response", top_k=30)
```

**Deliverable**: Cataloged claims ready for validation

---

## Phase 2: AI-Powered Security & Quality Scan (10h → 4h)

### 2A: Semantic Vulnerability Detection (2h)

**Use Dope-Context to find vulnerability patterns**:

```python
# SQL Injection (semantic, not just regex)
search_code(query="SQL query string formatting user input", profile="debugging")

# Command Injection
search_code(query="subprocess shell execution user input", profile="debugging")

# Path Traversal
search_code(query="file path user input sanitization", profile="debugging")

# Authentication bypass
search_code(query="API endpoint without authentication", profile="debugging")

# Secrets in code
search_code(query="hardcoded password API key secret token", profile="debugging")
```

**Why better than grep**:
- Finds semantic patterns, not just keyword matches
- Context-aware (distinguishes safe vs unsafe patterns)
- Complexity scoring highlights risk areas

**Manual Review**: Only verify flagged instances (AI pre-filters)

---

### 2B: Zen Codereview - Automated Quality Scan (1.5h)

**Use Zen codereview for systematic analysis**:

```python
# For each service (14 services × 6 min = 1.5h)
zen.codereview(
    step="Comprehensive quality review of {service}",
    relevant_files=["/path/to/service/**/*.py"],
    review_type="full",
    focus_on="quality, security, performance, architecture",
    model="gpt-5-codex",  # Code-specialized model
    step_number=1, total_steps=2, next_step_required=True
)
```

**Output**:
- Flagged functions with issues
- Complexity metrics
- Security concerns
- Architecture violations

**Human time**: Review only flagged issues, not entire codebase

---

### 2C: Complexity-Driven Prioritization (30 min)

**Use Serena complexity scores**:

```python
# Find high-complexity functions (>0.7)
search_code(query="high complexity business logic", top_k=50)

# Get complexity breakdown
serena.analyze_complexity(file_path="services/task-orchestrator/src/risk_prediction.py")

# Focus manual review on complexity > 0.6
```

**Deliverable**: Prioritized review list (200-300 critical functions, not 1400)

---

## Phase 3: Targeted Manual Review (40h → 15h)

### 3A: High-Risk Function Deep Dive (10h)

**Strategy**: Only manually review:
1. Complexity > 0.7 (Serena scoring)
2. Security-flagged (Phase 2A)
3. Core business logic (ML algorithms, risk prediction)
4. Zen-flagged issues

**Process per function** (5 min):
- Read Zen's analysis first
- Review actual code for correctness
- Verify edge cases
- Check tests exist

**Estimate**: 200 critical functions × 3 min = 10h

---

### 3B: Architecture Violation Detection (3h)

**Use semantic search to validate architecture**:

```python
# Find direct database access (should go through ConPort)
search_code(query="direct SQLite database write ADHD engine", profile="debugging")

# Find DopeconBridge bypasses
search_code(query="service to service direct call no bridge", profile="debugging")

# Find authority violations
search_code(query="status update not through Leantime", profile="debugging")
```

**Manual**: Trace each violation, document impact

---

### 3C: Algorithm Correctness Validation (2h)

**Focus on ML and critical algorithms**:

```python
# Find ML algorithms
search_code(query="machine learning prediction algorithm", top_k=20)

# Find risk calculation
search_code(query="risk score calculation formula", top_k=10)

# Find complexity scoring
search_code(query="cognitive complexity calculation", top_k=10)
```

**Manual**: Verify math, test with sample inputs

---

## Phase 4: Documentation-Code Alignment (18h → 6h)

### 4A: Code Example Verification (3h)

**Automated extraction + testing**:

```python
# Search for all code examples in docs
docs_search(query="python code example import", top_k=100)

# For each example:
# 1. Extract code block
# 2. Use Serena to find actual implementation
# 3. Compare: does example work with real code?

# Example workflow:
example = "mcp__conport__log_decision(...)"
actual = search_code(query="ConPort log_decision implementation", top_k=3)
# Manual: Verify parameters match
```

**Estimate**: 50 examples × 3 min = 2.5h

---

### 4B: API Documentation Validation (2h)

**Semantic search for endpoint verification**:

```python
# For each documented API:
docs_search(query="POST /assess-task endpoint")

# Find actual implementation:
search_code(query="assess-task endpoint handler router", top_k=5)

# Use Serena goto_definition to verify exact signature
serena.goto_definition(file_path="...", line=X, column=Y)
```

**Estimate**: 30 endpoints × 4 min = 2h

---

### 4C: Feature Claim Validation (1h)

**Systematic claim verification**:

```python
# Extract all feature claims
claims = docs_search(query="feature capability provides supports", top_k=50)

# For each claim:
# 1. Search for implementation
# 2. Check for TODOs/stubs
# 3. Verify tests exist

search_code(query=f"{claim_text} implementation", top_k=5)
```

**Estimate**: 40 claims × 1.5 min = 1h

---

## Phase 5: Eliminated (Phase 3 Covers This)

**Rationale**: Zen codereview + targeted manual review already covers function-level validation. Line-by-line is redundant.

**Saved**: 30-40 hours

---

## Phase 6: Integration Testing & Validation (12h → 6h)

### 6A: Zen Debug for Test Infrastructure (2h)

**Use Zen to systematically fix test issues**:

```python
# Investigate import errors
zen.debug(
    step="Analyze pytest import failures and dataclass conflicts",
    hypothesis="Code-audit workspace has circular dependency with parent",
    findings="Tests fail due to ../dopemux-mvp/ imports",
    model="gpt-5-codex"
)
```

**Output**: Root cause + fix strategy

---

### 6B: Automated Test Execution (1h)

```bash
# Fix imports based on Zen analysis
# Run tests
pytest tests/ -v --cov=src --cov=services --cov-report=json
```

---

### 6C: Zen-Assisted Failure Analysis (3h)

**For each failing test**:

```python
zen.debug(
    step="Analyze test failure: test_context_manager_initialization",
    hypothesis="Test expects old API, code changed",
    findings="[paste test output]",
    files_checked=["tests/test_context_manager.py", "src/context_manager.py"]
)
```

**Manual**: Apply fixes, re-run

---

## Phase 7: Consolidated with Phase 4

**Already covered** in Phase 4 (Documentation-Code Alignment)

**Saved**: 18 hours

---

## Phase 8: AI-Powered Synthesis (7h → 3h)

### 8A: Zen Consensus for Prioritization (1h)

**Multi-model validation of findings**:

```python
zen.consensus(
    step="Prioritize audit findings: security vs architecture vs docs",
    models=[
        {"model": "gpt-5-pro", "stance": "for", "stance_prompt": "Security first"},
        {"model": "gpt-5-codex", "stance": "against", "stance_prompt": "Architecture first"},
        {"model": "o3-mini", "stance": "neutral"}
    ],
    findings="[Summary of all audit findings]"
)
```

**Output**: AI-validated priority ranking

---

### 8B: Automated Report Generation (1h)

**Structured output from all phases**:
- Security findings (Phase 2A)
- Quality issues (Phase 2B + 3A)
- Architecture violations (Phase 3B)
- Doc discrepancies (Phase 4)

**Use Zen to synthesize** into coherent report

---

### 8C: ADR-206 Documentation (1h)

**Manual**: Write final ADR with:
- Complete findings
- Prioritized fixes
- Effort estimates
- Recommendations

---

## Optimized Timeline Comparison

| Phase | Original | Optimized | Saved | Method |
|-------|----------|-----------|-------|--------|
| 1. Inventory | 6h | 2h | 4h | Dope-Context semantic search |
| 2. Security/Quality | 10h | 4h | 6h | Zen codereview automation |
| 3. Manual Review | 40h | 15h | 25h | Complexity-driven prioritization |
| 4. Doc Validation | 18h | 6h | 12h | Semantic search + parallel ops |
| 5. Line-by-line | 40h | 0h | 40h | Eliminated (redundant) |
| 6. Integration Testing | 12h | 6h | 6h | Zen debug assistance |
| 7. Doc-Code Alignment | 18h | 0h | 18h | Consolidated with Phase 4 |
| 8. Synthesis | 7h | 3h | 4h | AI-powered consensus |
| **TOTAL** | **151h** | **36h** | **115h** | **76% reduction** |

**Corrected from original 93h estimate** (which already had optimizations):

| Phase | Original Plan | This Optimization | Saved |
|-------|---------------|-------------------|-------|
| **TOTAL** | 93h | 36h | 57h (61% reduction) |

---

## Execution Strategy

### Day 1 (8h): Foundation
- **Morning** (4h): Phase 1 complete (inventory via MCP)
- **Afternoon** (4h): Phase 2 start (security scan, first 6 services Zen review)

### Day 2 (8h): Automated Analysis
- **Morning** (4h): Phase 2 complete (remaining 8 services, complexity analysis)
- **Afternoon** (4h): Phase 3 start (high-risk function review)

### Day 3 (8h): Manual Validation
- **Morning** (4h): Phase 3 continue (architecture violations, algorithms)
- **Afternoon** (4h): Phase 3 complete + Phase 4 start (doc examples)

### Day 4 (8h): Documentation
- **Morning** (4h): Phase 4 complete (API verification, feature claims)
- **Afternoon** (4h): Phase 6 start (fix test infrastructure via Zen)

### Day 5 (4h): Testing & Synthesis
- **Morning** (2h): Phase 6 complete (run tests, fix failures)
- **Afternoon** (2h): Phase 8 complete (Zen consensus, final report)

**Total: 4.5 days instead of 11.6 days**

---

## Success Criteria (Unchanged)

✅ **Every critical function reviewed** (complexity > 0.6 OR security-flagged)
✅ **Every documentation claim verified** against actual code
✅ **Every code example tested** and working
✅ **All high-priority tests passing** (>80% of 785 tests)
✅ **Documentation aligned** to current code reality
✅ **Zero critical security vulnerabilities** unaddressed
✅ **Prioritized fix roadmap** with effort estimates

---

## Why This Works

**MCP Leverage**:
1. **Dope-Context**: Instant semantic search (2 sec vs 5 min manual search)
2. **Zen codereview**: AI validates 700+ functions (6 min per service vs 2h manual)
3. **Serena complexity**: Auto-prioritize high-risk code (no manual complexity analysis)
4. **Parallel operations**: Search code + docs simultaneously

**Strategic Focus**:
- Automate breadth (find all patterns)
- Human validates depth (verify correctness)
- AI pre-filters noise (only review flagged issues)

**Risk Mitigation**:
- Still manually review all critical/complex functions
- Still verify all architecture claims
- Still test all code examples
- AI augments, doesn't replace, human judgment

---

**This is the OPTIMIZED plan: 36 hours for exhaustive, MCP-powered audit.**

Ready to execute?
