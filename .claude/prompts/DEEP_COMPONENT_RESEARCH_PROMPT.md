# Enhanced Prompt: Deep Component Research & Documentation

**Purpose**: Generate comprehensive, source-validated technical analysis of Dopemux components for integration design, validation, and living documentation.

**Target Components**: Serena v2, ConPort, dope-context, ADHD Engine, DopeconBridge, Task Orchestrator, Dope-Memory, Desktop Commander, Leantime Bridge, Plane Coordinator, Workspace Watcher, Activity Capture, Voice Commands, ADHD Notifier, ADHD Dashboard, LiteLLM, Exa, Genetic Agent, MCP Client, PAL, GPT Researcher

---

## RESEARCH PROTOCOL (Aligned with PRIMER.md)

### Phase 0: Scope Lock (5 min)
Before starting research on a component, explicitly define:
- **Plane under analysis**: (Memory, PM, ADHD, Search, Bridge, etc.)
- **In-scope / out-of-scope**: Specific sub-modules or integration points.
- **Success criteria**: What constitutes a "complete" deep dive for this component.
- **Stop conditions**: When to halt (e.g., missing specific source files).

### Phase 1: Inventory (15-20 min)
Produce an evidence-based inventory of the component's structure. No opinions or analysis yet.

**Step 1.1: Historical Decision Mining**
- Tool: `mcp__conport__search_decisions_fts`
- Extract: Strategic decisions, architecture evolution, performance benchmarks.

**Step 1.2: Source Code Architecture Analysis**
- Tool: `mcp__serena-v2__read_file` + `mcp__serena-v2__find_symbol`
- Extract: Module structure, public API surface, dependency graph.

**Step 1.3: File System Validation**
- Tool: Bash commands (`find`, `wc -l`, `ls -la`, `git log`)
- Extract: Exact file counts, line counts (prod vs. test), directory organization.

### Phase 2: Failure & Drift Analysis (10-15 min)
Identify and label gaps between specification and implementation.

**Labeling Requirement**:
- **[Observed]**: Direct evidence from code, logs, or command output.
- **[Inferred]**: Reasoned conclusion, but lacks direct primary source verification.

**Focus Areas**:
- Determinism leaks, provenance breaks, trust boundary violations.

### Phase 3: Design Delta (Research Context)
In the context of research, this phase identifies:
- What the current shape of the component enables vs. what the spec intended.
- Constraints imposed by the existing implementation on future integrations.

### Phase 4: Reports (Technical Deep Dive)
Compose the final research report following the "Report Structure" below.

---

## QUALITY STANDARDS (Non-Negotiable)

1. **Protocol over Cleverness**: Follow the phases in order. Do not skip to Phase 4.
2. **Current Implementation Wins**: Documentation is wrong if it contradicts current code behavior.
3. **Auditability**: Every claim must have a citation (File:Line, Decision ID, Command Output).
4. **Final Rule**: **If it is not auditable, it does not exist.**

---

## REPORT STRUCTURE

```markdown
# {Component Name}: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT
### Executive Summary & Strategic Intent
### Architecture & Core Components (Validated)
### Advanced Features & Intelligence
### Integration Patterns & Data Flow
### Testing, Performance, Limitations & Opportunities

## SECTION 2: EVIDENCE TRAIL
### Inventory Evidence (Phase 1)
- Source code snippets
- Decision IDs
- File system counts
### Failure & Drift Findings (Phase 2)
### Cross-Validation Summary

## SECTION 3: LIVING DOCUMENTATION METADATA
- Last Validated: {timestamp}
- Confidence Level: {percentage}
- Evidence Quality Score: {score}
- Evolution Log: [Chronological list of updates]
```

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

### Dope-Memory:
- **Focus Areas**: Temporal spine, working context, reflection cards, trajectory boosting
- **Key Evidence**: docs/spec/dope-memory/v1/ (Full Spec), 00_overview.md, 07_mcp_contracts.md
- **Critical Files**: store.py (implied), memory_graph.py (implied)
- **Integration**: DopeQuery (facts), DopeContext (semantic), EventBus (activity)

### Desktop Commander:
- **Focus Areas**: Desktop automation, window management, screenshots, cross-platform (macOS/Linux)
- **Key Evidence**: server.py (FastAPI), integration_bridge_connector.py
- **Critical Files**: server.py, Dockerfile
- **Integration**: ADHD Engine (enforcing breaks), PAL (executing actions)

### Leantime Bridge:
- **Focus Areas**: Project management synchronization, ticket creation, status updates
- **Key Evidence**: test_contract_api_tools.py, leantime_bridge/ directory
- **Critical Files**: leantime_client.py, http_server.py
- **Integration**: Task Orchestrator (sync), Leantime Container (HTTP API)

### Plane Coordinator:
- **Focus Areas**: Two-plane architecture coordination (PM Plane <-> Cognitive Plane)
- **Key Evidence**: services/task-orchestrator/Dockerfile.coordination, app/coordination/
- **Critical Files**: main.py (port 8090)
- **Integration**: ConPort, ADHD Engine, Redis Events

### Workspace Watcher:
- **Focus Areas**: Passive file activity detection, coding vs reading distinction
- **Key Evidence**: file_activity_checker.py, workspace_mapper.py
- **Critical Files**: file_activity_checker.py
- **Integration**: Activity Capture (reports), ADHD Engine (inference)

### Activity Capture:
- **Focus Areas**: Aggregating development metrics (switches, edits) for ADHD Engine
- **Key Evidence**: activity_tracker.py, event_subscriber.py
- **Critical Files**: activity_tracker.py
- **Integration**: Workspace Watcher (input), ADHD Engine (output via HTTP)

### Voice Commands:
- **Focus Areas**: Voice-to-task decomposition, ADHD context awareness
- **Key Evidence**: voice_task_decomposer.py, voice_api.py
- **Critical Files**: voice_task_decomposer.py
- **Integration**: Zen/PAL (decomposition), ADHD Engine (context)

### ADHD Notifier:
- **Focus Areas**: Desktop notifications, break reminders, hyperfocus alerts
- **Key Evidence**: notify.py (osascript/notify-send), mobile_push.py
- **Critical Files**: notify.py
- **Integration**: ADHD Engine (triggers), Desktop OS (delivery)

### ADHD Dashboard:
- **Focus Areas**: Real-time visualization of cognitive state, WebSocket updates
- **Key Evidence**: services/adhd-dashboard/backend.py, Redis PubSub
- **Critical Files**: backend.py
- **Integration**: Redis (events), Activity Capture (metrics), ADHD Engine (state)

### LiteLLM:
- **Focus Areas**: Universal LLM proxy, model routing (Grok, O3, GPT-5)
- **Key Evidence**: litellm.config.yaml
- **Critical Files**: litellm.config.yaml
- **Integration**: All MCP servers (as model provider), PAL

### Exa:
- **Focus Areas**: Neural web search, content extraction, similar finding
- **Key Evidence**: docker/mcp-servers/exa/exa_server.py
- **Critical Files**: exa_server.py
- **Integration**: PAL (research fallback), GPT Researcher

### Genetic Agent:
- **Focus Areas**: Auto-code repair, genetic programming evolution, dual-agent mode
- **Key Evidence**: services/genetic_agent/main.py, genetic/genetic_agent.py
- **Critical Files**: main.py, genetic_agent.py
- **Integration**: PAL (LLM), DopeContext (RAG), Unit Tests (fitness function)

### MCP Client:
- **Focus Areas**: Custom MCP client implementation, stdio + HTTP transport
- **Key Evidence**: services/mcp-client/main.py
- **Critical Files**: main.py
- **Integration**: All MCP Servers (connection)

### PAL (Zen):
- **Focus Areas**: Primary reasoning engine, multi-model support, tool orchestration
- **Key Evidence**: docker/mcp-servers/pal/pal_http_wrapper.py, pal-mcp-server/
- **Critical Files**: server.py (upstream), pal_http_wrapper.py
- **Integration**: All other components (orchestrator)

### GPT Researcher:
- **Focus Areas**: Deep recursive research, report generation
- **Key Evidence**: docker/mcp-servers/gptr-mcp/wrapper.py
- **Critical Files**: wrapper.py, server.py (upstream)
- **Integration**: Exa (search source), PAL (triggers)

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
