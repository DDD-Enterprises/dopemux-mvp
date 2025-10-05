# Enhanced Prompt: Deep Component Research & Documentation

**Purpose**: Generate comprehensive, source-validated technical analysis of Dopemux components for integration design, validation, and living documentation.

**Target Components**: Serena v2, ConPort, dope-context, ADHD Engine, Integration Bridge, Task Orchestrator

---

## RESEARCH PROTOCOL

### Phase 1: Evidence Gathering (15-20 min)

**Step 1.1: Historical Decision Mining**
```
Tool: mcp__conport__search_decisions_fts
Queries:
  - "{component_name} architecture"
  - "{component_name} design"
  - "{component_name} performance"
  - "{component_name} integration"
  - "{component_name} testing"

Extract:
  - Strategic decisions and rationale
  - Architecture evolution timeline
  - Performance benchmarks (actual measurements)
  - Integration patterns
  - Known issues and resolutions
  - Design trade-offs
```

**Step 1.2: Source Code Architecture Analysis**
```
Tool: mcp__serena-v2__read_file + mcp__serena-v2__find_symbol

Files to Read:
  - {component_root}/__init__.py (module structure, exports)
  - {component_root}/README.md (if exists)
  - {component_root}/ARCHITECTURE.md (if exists)
  - {component_root}/*_COMPLETION_SUMMARY.md (feature status)
  - tests/{component}/*.py (test structure, coverage)

Extract:
  - Component count and organization
  - Class/module hierarchy
  - Public API surface (__all__ exports)
  - Dependency graph (imports)
  - Type definitions
  - Performance targets (from comments/docstrings)
```

**Step 1.3: File System Validation**
```
Tool: Bash commands

Commands:
  - find {component_root} -name "*.py" | wc -l
  - find {component_root} -name "*.py" -exec wc -l {} + | tail -1
  - find {component_root} -name "test_*.py" | wc -l
  - ls -la {component_root}/ (directory structure)
  - git log --oneline {component_root}/ --since="30 days ago" | wc -l

Extract:
  - Exact file counts
  - Total line counts (production vs test)
  - Recent commit activity
  - Directory organization
```

**Step 1.4: Runtime Validation**
```
Tool: Bash (Docker, health checks)

Commands:
  - docker ps --filter "name={component}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  - curl -s http://localhost:{port}/health (if applicable)
  - curl -s http://localhost:{port}/metrics (if applicable)

Extract:
  - Container status (if Dockerized)
  - Health check status
  - Runtime metrics (if exposed)
  - Port mappings
```

**Step 1.5: Test Coverage Analysis**
```
Tool: mcp__serena-v2__read_file + Bash

Files to Read:
  - tests/{component}/conftest.py (fixtures, setup)
  - tests/{component}/test_*.py (all test files)
  - pytest.ini or pyproject.toml (test config)
  - .coverage or htmlcov/ (coverage reports)

Commands:
  - pytest tests/{component}/ -v --tb=short
  - pytest tests/{component}/ --cov={component} --cov-report=term

Extract:
  - Total test count
  - Test organization (unit, integration, E2E)
  - Coverage percentage
  - Test execution time
  - Common fixtures and patterns
```

**Step 1.6: Performance Data Mining**
```
Tool: mcp__conport__search_decisions_fts + Grep

Search for:
  - "performance", "benchmark", "timing", "latency"
  - "{component_name} test", "{component_name} validation"
  - Numeric patterns: "ms", "seconds", "faster", "slower"

Grep patterns:
  - Performance-related comments in code
  - Timing decorators (@timed, @performance_monitor)
  - Logging statements with timing

Extract:
  - Measured performance data (not targets)
  - Comparison metrics (X times faster than Y)
  - Performance regression notes
  - Optimization history
```

**Step 1.7: Integration Pattern Analysis**
```
Tool: Grep + mcp__serena-v2__find_symbol

Search for:
  - Import statements from other components
  - MCP tool calls (mcp__*)
  - Database queries (PostgreSQL, Redis, ConPort)
  - API calls (HTTP, gRPC)
  - Event emissions/subscriptions

Extract:
  - Direct dependencies
  - Integration patterns (how components connect)
  - Data flow paths
  - Event-driven interactions
  - API contracts
```

---

### Phase 2: Cross-Validation (5-10 min)

**Validation Matrix**:
```
For each major claim, verify with 2+ sources:

Example:
Claim: "31 components in Serena v2"
Source 1: __init__.py header comment ✓
Source 2: Count of imports in __all__ ✓
Source 3: ConPort Decision #109 ✓
Confidence: 100%

If sources conflict:
  - Document discrepancy
  - Investigate further (read actual code)
  - Note which source is likely outdated
  - Update confidence level
```

**Cross-Validation Checklist**:
- [ ] Component count matches imports
- [ ] Performance claims have measured data
- [ ] Architecture description matches code structure
- [ ] Test coverage claims match pytest output
- [ ] Integration points verified in source code
- [ ] Container status matches deployment claims

---

### Phase 3: Report Composition (20-30 min per part)

**Part Structure** (repeat for each part):

```markdown
## Part {N}: {Section Title}

### {N}.1 {Subsection}

**Purpose**: [What this component/feature does]

**File(s)**: [Exact file paths]

**Core Capabilities**:
- [Capability 1 with code example/snippet]
- [Capability 2 with code example/snippet]
- [Capability 3 with code example/snippet]

**Architecture**:
```
[ASCII diagram or structured description]
```

**Data Flow**:
```
[Step-by-step data flow with file references]
```

**Integration Points**:
- **{Other Component}**: [How they interact, file:line references]
- **{External Service}**: [Connection method, configuration]

**Performance Characteristics**:
- **Typical**: [Median/average from measurements]
- **Best Case**: [Optimal scenario]
- **Worst Case**: [Degraded scenario]
- **ADHD Target**: [Required performance for ADHD users]
- **Actual vs Target**: [Multiplier comparison]

**Testing**:
- **Coverage**: [Percentage from pytest --cov]
- **Test Count**: [Unit/Integration/E2E breakdown]
- **Key Tests**: [Most important test scenarios]
- **Test Execution Time**: [How long tests take]

**Strengths**:
- [What this component does exceptionally well]
- [Unique capabilities or optimizations]

**Limitations**:
- [Known constraints or bottlenecks]
- [Areas needing improvement]
- [Dependencies causing issues]

**Opportunities**:
- [Future enhancement possibilities]
- [Integration opportunities]
- [Performance optimization potential]

**ADHD Accommodations**:
- [Specific ADHD features in this component]
- [How it reduces cognitive load]
- [Progressive disclosure patterns]

---

### {N}.2 [Next Subsection]
[Repeat structure]
```

---

### Phase 4: Evidence Documentation (10-15 min per part)

**Evidence Structure**:

```markdown
## Part {N}: Evidence Trail

### Source 1: ConPort Decisions
**Query**: [Exact search query used]
**Results**: {count} decisions found
**Decision IDs**: [List of decision IDs with summaries]

**Extracted Data**:
- [Claim 1] → Decision #{id}, timestamp {date}
  - Quote: "[exact quote from decision]"
  - Confidence: [High/Medium/Low based on decision completeness]

- [Claim 2] → Decision #{id}, timestamp {date}
  - Quote: "[exact quote]"
  - Confidence: [High/Medium/Low]

**Validation Notes**:
- [Any discrepancies found]
- [Cross-references to other decisions]

---

### Source 2: Source Code Files
**Files Read**: [List of file paths]

**File 1**: {path}
**Lines**: {start}-{end}
**Extracted**:
```
[Relevant code snippet or structure]
```
**Data Points**:
- [Component count, class names, etc.]
- [Performance targets from comments]

**File 2**: {path}
[Repeat]

---

### Source 3: File System Queries
**Commands**:
```bash
[Exact command executed]
```
**Output**:
```
[Raw output]
```
**Extracted Data**:
- File count: {number}
- Line count: {number}
- [Other metrics]

---

### Source 4: Runtime Validation
[Container status, health checks, etc.]

---

### Source 5: Test Execution
**Command**:
```bash
pytest tests/{component}/ -v
```
**Output Summary**:
- Tests passed: {count}
- Tests failed: {count}
- Coverage: {percentage}

**Key Test Results**:
[Relevant test output showing performance, functionality]

---

### Cross-Validation Summary
**Claims Validated**: {count}
**Confidence Levels**:
- High (2+ sources): {count} claims
- Medium (1 source): {count} claims
- Low (inferred): {count} claims

**Conflicts Found**: {count}
[Details of any conflicting information]

**Evidence Quality Score**: {percentage}
[Based on source reliability, cross-validation, recency]
```

---

## EXECUTION INSTRUCTIONS

### For New Component Research:

1. **Initialize Document**:
```bash
# Create component deep-dive doc
touch docs/{COMPONENT_NAME}-DEEP-DIVE.md

# Copy structure template
# Section 1: TECHNICAL REPORT
# Section 2: EVIDENCE TRAIL
# Section 3: EVOLUTION LOG
```

2. **Execute Research Protocol**:
- Run Phase 1 (Evidence Gathering) completely
- Document all sources and data
- Run Phase 2 (Cross-Validation)
- Note confidence levels

3. **Compose Report Part**:
- Follow Part Structure template
- Include all subsections (Purpose, Architecture, Performance, Testing, etc.)
- Reference evidence explicitly (Decision #X, File Y:line Z)

4. **Document Evidence**:
- Follow Evidence Structure template
- Include raw data (commands, outputs, quotes)
- Document validation process
- Note confidence levels

5. **Append to Document**:
```python
# Read existing document
existing = read_file(f"docs/{COMPONENT}-DEEP-DIVE.md")

# Append new report part to Section 1
section1_end = existing.find("## SECTION 2:")
new_report = existing[:section1_end] + f"\n\n### Part {N}: {title}\n{content}\n" + existing[section1_end:]

# Append evidence to Section 2
section2_end = existing.find("## Document Evolution Log")
final = new_report[:section2_end] + f"\n\n### Part {N}: Evidence\n{evidence}\n" + new_report[section2_end:]

# Write back
write_file(f"docs/{COMPONENT}-DEEP-DIVE.md", final)
```

6. **Update Evolution Log**:
```markdown
- **{timestamp}**: Part {N} added - {brief_summary} ({word_count} words, {evidence_sources} sources)
```

---

## QUALITY STANDARDS

### Report Quality Checklist:
- [ ] Every claim has evidence citation
- [ ] Performance data is measured (not estimated)
- [ ] Code examples reference actual files
- [ ] Integration points verified in source
- [ ] Limitations honestly documented
- [ ] Opportunities grounded in architecture
- [ ] ADHD features explicitly identified
- [ ] Cross-component interactions mapped

### Evidence Quality Checklist:
- [ ] 2+ sources for major claims
- [ ] Raw data included (not just summaries)
- [ ] Commands/queries documented exactly
- [ ] Timestamps on historical data
- [ ] Confidence levels justified
- [ ] Conflicts investigated
- [ ] Source reliability assessed

### Technical Accuracy Checklist:
- [ ] File paths verified to exist
- [ ] Line numbers accurate (if cited)
- [ ] Class/function names match source
- [ ] Architecture diagrams match imports
- [ ] Performance numbers from actual tests
- [ ] Test coverage from pytest output

---

## COMPONENT-SPECIFIC GUIDANCE

### Serena v2:
- **Focus Areas**: 31 components, 6 phases, ADHD optimization, performance
- **Key Evidence**: ConPort Decisions #75, #84, #119, #127, F5/F6/F7 completion docs
- **Critical Files**: __init__.py, intelligence/__init__.py, enhanced_lsp.py
- **Integration**: dope-context (semantic search), ConPort (decisions), ADHD Engine (state)

### ConPort:
- **Focus Areas**: Knowledge graph (AGE), decision logging, multi-instance, ADHD task management
- **Key Evidence**: Migration 007, Decision #179, #185, PostgreSQL schema
- **Critical Files**: migrations/, conport_client.py, knowledge_graph.py
- **Integration**: Serena (navigation links), ADHD Engine (activity tracking), Leantime (PM sync)

### dope-context:
- **Focus Areas**: Semantic search (Milvus), Voyage embeddings, hybrid search, reranking
- **Key Evidence**: Code search implementation, indexing pipeline, Voyage integration
- **Critical Files**: code_chunker.py, voyage_embedder.py, hybrid_search.py
- **Integration**: Serena (provides search results), ConPort (indexes decisions)

### ADHD Engine:
- **Focus Areas**: Cognitive load, energy matching, break recommendations, attention states
- **Key Evidence**: Task Orchestrator extraction, Week 1 migration, FastAPI service
- **Critical Files**: engine.py, activity_tracker.py, conport_client.py
- **Integration**: ConPort (task queries), Serena (complexity matching), statusline (display)

---

## INCREMENTAL RESEARCH STRATEGY

**For exceeding context windows**:

1. **Part Sizing**: Target 2,000-3,000 words per part
2. **Evidence Sizing**: Target 1,500-2,500 words per evidence section
3. **Natural Breakpoints**:
   - Part 1: Overview + Layer/Phase 1
   - Part 2: Layer/Phase 2-3
   - Part 3: Layer/Phase 4-5
   - Part 4: Integration + Testing
   - Part 5: Performance + Limitations + Opportunities

4. **Progressive Appending**:
```
Session 1: Part 1 report + evidence → Append to doc
Session 2: Part 2 report + evidence → Append to doc
Session 3: Part 3 report + evidence → Append to doc
...continue until complete
```

5. **Resumption Protocol**:
```
To resume research in new session:
1. Read docs/{COMPONENT}-DEEP-DIVE.md
2. Check Evolution Log for last completed part
3. Continue with next part number
4. Maintain same evidence quality standards
```

---

## DELIVERABLE FORMAT

**Final Document Structure**:
```
# {Component Name}: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT
### Part 1: Executive Summary & Strategic Intent
### Part 2: Architecture & Core Components
### Part 3: Advanced Features & Intelligence
### Part 4: Integration Patterns & Data Flow
### Part 5: Testing, Performance, Limitations & Opportunities

## SECTION 2: EVIDENCE TRAIL
### Part 1: Evidence Sources & Validation
### Part 2: Architecture Evidence
### Part 3: Advanced Features Evidence
### Part 4: Integration Evidence
### Part 5: Testing & Performance Evidence

## SECTION 3: COMPONENT INTERACTION MAP
[How this component interacts with all other Dopemux components]

## SECTION 4: LIVING DOCUMENTATION METADATA
- Last Validated: {timestamp}
- Source Code Version: {git commit hash}
- Test Coverage: {percentage}
- Evidence Quality Score: {score}
- Next Review Date: {date}

## Document Evolution Log
[Chronological log of all updates]
```

---

## USAGE EXAMPLES

### Example 1: Research Serena v2 Part 1
```
Prompt: "Using the DEEP_COMPONENT_RESEARCH_PROMPT, research Serena v2 Part 1 (Executive Summary & Strategic Intent). Follow the evidence gathering protocol completely, then compose the report section and evidence section. Append both to docs/SERENA-V2-DEEP-DIVE.md"

Expected Output:
- 15-20 min evidence gathering
- 2,500 word report section
- 2,000 word evidence section
- Document appended with both sections
- Evolution log updated
```

### Example 2: Research ConPort Part 2
```
Prompt: "Using the DEEP_COMPONENT_RESEARCH_PROMPT, research ConPort Part 2 (Architecture & Core Components). Read the existing docs/CONPORT-DEEP-DIVE.md, identify the last completed part, then research and append Part 2."

Expected Output:
- Resume from last part
- Complete evidence gathering for Part 2
- Compose report + evidence
- Append to existing document
- Maintain evidence quality standards
```

---

## SUCCESS CRITERIA

**Research Quality**:
- 90%+ of claims have 2+ sources
- 100% of performance claims have measured data
- All file paths verified to exist
- Cross-validation performed on major claims

**Report Utility**:
- Technical team can design integrations from this doc
- Deep thinking tools can validate source code accuracy
- Living documentation stays current with builds
- Limitations guide realistic planning
- Opportunities inform roadmap

**Evidence Transparency**:
- Anyone can re-validate claims
- Source data trail is complete
- Commands/queries are reproducible
- Confidence levels are justified

---

## MAINTENANCE PROTOCOL

**After Each Build/Deployment**:
1. Re-run validation commands (file counts, tests, health checks)
2. Update performance metrics if changed
3. Note any architectural changes
4. Update "Last Validated" timestamp
5. Append evolution log entry

**Quarterly Deep Review**:
1. Re-execute full research protocol
2. Identify outdated sections
3. Update with new evidence
4. Revalidate integration patterns
5. Update opportunities based on current roadmap

**Triggers for Immediate Update**:
- Major refactoring (>500 lines changed)
- New phase/layer added
- Performance regression detected
- Integration pattern changes
- Test coverage drops >10%

---

END OF ENHANCED PROMPT
