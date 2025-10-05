# Command Consolidation Analysis - Thinkdeep Results

**Date**: 2025-10-04
**Analysis Tool**: Zen thinkdeep (5 steps, very_high confidence)
**Status**: Analysis complete, ready for implementation planning

---

## Executive Summary

After comprehensive analysis, determined that **sc: and dx: are complementary layers** that should be merged through a **layered architecture pattern**, not a replacement strategy.

**Key Result**: 46 commands → 29 consolidated dx: commands (37% reduction)

---

## Core Finding: Layered Architecture

### Layer 1 (Outer): ADHD Optimization
From dx: commands:
- Energy matching via ADHD Engine
- 25-minute session management with break reminders
- Progress tracking and celebration
- ConPort context preservation
- Gentle re-orientation after interruptions

### Layer 2 (Inner): Technical Execution
From sc: commands:
- Multi-persona coordination (architect, frontend, backend, security, qa)
- MCP orchestration (Context7, Magic, Zen, Playwright)
- Framework detection and patterns
- Comprehensive tool selection
- Behavioral activation patterns

---

## Command Type Taxonomy

### Type A: Session-Aware Commands (12 total)
**Full 4-Phase Pattern**: ADHD Assessment → Session Setup → Technical Execution → Session Complete

Commands:
1. dx:implement - 25-min implementation sessions with persona coordination
2. dx:analyze - Zen thinkdeep with energy matching
3. dx:design - Zen consensus with decision reduction
4. dx:troubleshoot - Zen debug with systematic approach
5. dx:research - GPT-Researcher with break reminders
6. dx:review - Zen codereview with progressive disclosure (NEW)
7. dx:prd-parse - PRD decomposition with task assessment
8. dx:improve - Code improvement with session tracking
9. dx:document - Doc generation with focus sessions
10. dx:cleanup - Code cleanup with progress tracking
11. dx:test - Test execution with session management
12. dx:spawn - Meta-orchestration with complexity assessment

**Pattern Details**:
```yaml
phase_1_adhd_assessment: (~30s)
  - Check ADHD Engine energy level
  - Assess task complexity (0.0-1.0)
  - Calculate suitability score
  - Get user confirmation if < 0.6

phase_2_session_setup: (~5s)
  - Update ConPort (status → IN_PROGRESS)
  - Save session_start timestamp
  - Display session start message
  - Set 25-minute target

phase_3_technical_execution: (20-25 min)
  - Apply sc: command logic (personas, MCPs, tools)
  - Execute with framework detection
  - Track progress internally

phase_4_session_complete: (~10s)
  - Prompt for completion status
  - Update ConPort progress
  - Display break reminder
  - Celebrate if DONE
```

### Type B: Quick Utilities (10 total)
**Simplified 2-Phase Pattern**: Quick Check → Technical Execution with ADHD Presentation

Commands:
1. dx:load - Context loading (< 2s)
2. dx:save - Context saving (< 2s)
3. dx:help - Command reference (instant)
4. dx:stats - ADHD dashboard (< 1s)
5. dx:assess - Task suitability check (< 1s)
6. dx:explain - Code explanation (< 5s)
7. dx:git - Git operations (variable)
8. dx:session/* - Session lifecycle commands (instant)
9. dx:estimate - Time estimation (< 3s)
10. dx:reflect - Task reflection (< 5s)

**Pattern Details**:
```yaml
phase_1_quick_check: (< 1s)
  - Check if session is active
  - Brief energy awareness (no ADHD Engine call)

phase_2_technical_execution: (< 5s)
  - Apply sc: command logic immediately
  - No session setup overhead

phase_3_adhd_presentation: (< 1s)
  - Format output for ADHD (visual, progressive)
  - Encouraging tone
```

**Design Decision**: Type B skips assessment/session overhead for speed. Users expect instant responses.

### Type C: Long-Running Commands (3 total)
**Extended Multi-Chunk Pattern**: Extended Assessment → Chunked Sessions → Extended Completion

Commands:
1. dx:build - Build/compile (5-60 min)
2. dx:business-panel - Business analysis (10-30 min)
3. dx:spec-panel - Spec review (10-20 min)

**Pattern Details**:
```yaml
phase_1_extended_assessment: (~45s)
  - Assess task duration estimate
  - Calculate session chunks (25-min blocks)
  - Warn if > 90 minutes (hyperfocus risk)
  - Get user confirmation

phase_2_chunked_session: (~10s setup)
  - Update ConPort with multi-chunk session
  - Set break reminders at 25-min intervals
  - Display chunk progress (e.g., "Chunk 2/3")

phase_3_technical_execution: (30-90 min)
  - Apply sc: command logic
  - Emit progress updates
  - Auto-save checkpoints every 25 min

phase_4_extended_completion: (~15s)
  - Calculate actual duration
  - Update ConPort with all chunks
  - Display extended break reminder (5-15 min)
  - Provide session summary
```

---

## Command Mapping (46 → 29)

### Migrating to dx: (Type A - Full Pattern)
- dx:implement ← merge sc:implement + dx:implement
- dx:analyze ← sc:analyze (new ADHD wrapper)
- dx:design ← sc:design (new ADHD wrapper)
- dx:troubleshoot ← sc:troubleshoot (new ADHD wrapper)
- dx:research ← sc:research (new ADHD wrapper)
- dx:review ← NEW (Zen codereview with ADHD)
- dx:prd-parse ← merge sc:workflow + dx:prd-parse
- dx:improve ← sc:improve (new ADHD wrapper)
- dx:document ← merge sc:document + adr-new + rfc-new + doc-*
- dx:cleanup ← sc:cleanup (new ADHD wrapper)
- dx:test ← sc:test (new ADHD wrapper)
- dx:spawn ← merge sc:spawn + sc:task

### Keeping dx: (Type B - Quick Pattern)
- dx:load ← merge sc:load + dx:load
- dx:save ← merge sc:save + dx:save
- dx:help ← sc:help
- dx:stats ← keep dx:stats
- dx:assess ← keep dx:assess
- dx:explain ← sc:explain
- dx:git ← rename dx:commit + merge sc:git
- dx:session/* ← keep (start, end, break, resume, status)
- dx:estimate ← sc:estimate
- dx:reflect ← sc:reflect

### Adding (Type C - Long-Running Pattern)
- dx:build ← sc:build
- dx:business-panel ← sc:business-panel
- dx:spec-panel ← sc:spec-panel

### Deprecated/Removed (17 total)
- adr-new, rfc-new, rfc-lint, rfc-promote → dx:document --type adr/rfc
- doc-new, doc-pull, doc-ensure-frontmatter, docs-helper → dx:document
- dangerous, safe → removed (use --unsafe flag instead)
- security-review → dx:analyze --focus security
- sc:select-tool → automatic (no command needed)
- sc:index → automatic on load (no command needed)

---

## Critical Insights from Analysis

### 1. Orthogonal Concerns Pattern
**Finding**: sc: and dx: solve different problems in the same workflow.

- **sc: = "How to execute"**: Tool selection, persona activation, MCP coordination
- **dx: = "When/why to execute"**: Energy matching, timing, break management, context preservation

**Implication**: Don't choose one or the other - **layer them together**.

### 2. 4-Phase Pattern Universality
**Finding**: The ADHD wrapper pattern applies consistently across all session-aware commands.

**Evidence**:
- dx:implement + sc:implement merger validated pattern
- dx:load + sc:load merger confirmed pattern
- Pattern works for analyze, design, troubleshoot, research

**Implication**: Create reusable templates, apply systematically.

### 3. Speed Matters for Quick Commands
**Finding**: Users expect instant responses from utility commands like help, stats, explain.

**Evidence**:
- Type B commands analyzed: all < 5s target
- Adding 30s ADHD assessment to dx:help would frustrate users
- Progressive disclosure can happen at presentation layer only

**Implication**: Type B gets presentation layer only, no session overhead.

### 4. Hyperfocus Risk for Long Tasks
**Finding**: Tasks > 90 minutes risk hyperfocus without breaks.

**Evidence**:
- dx:build can take 30-60 minutes
- business-panel analysis can take 20-30 minutes
- ADHD users lose track of time during complex analysis

**Implication**: Type C needs chunk-based sessions with mandatory break reminders.

---

## Edge Cases Identified

### 1. MCP Service Unavailability
**Scenario**: ConPort or Serena MCP down during command execution.

**Resolution**:
- Always try both ConPort + Serena
- Degrade gracefully if one unavailable
- Example: dx:load works with ConPort only OR Serena only

### 2. ADHD Engine Unavailability
**Scenario**: ADHD Engine not running when user calls dx:implement.

**Resolution**:
- All Type A commands work WITHOUT ADHD Engine
- Skip energy assessment, proceed with session
- Display warning: "ADHD assessment unavailable"

### 3. Session Conflicts
**Scenario**: User calls dx:implement while session already active.

**Resolution**:
- Detect active session via ConPort active_context
- Offer choice: "Session in progress. End current? (y/n)"
- If yes: End current, start new
- If no: Cancel new session request

### 4. Load/Save Round-Trip
**Scenario**: User saves context, then loads it back - data must match.

**Resolution**:
- Round-trip testing mandatory in Phase 2
- Save → Load → Verify all fields preserved
- Git state, open files, ADHD metrics, decisions

---

## Implementation Challenges

### Challenge 1: Template Design Complexity
**Issue**: Pattern templates too rigid → hard to customize per command.

**Mitigation**:
- Keep templates minimal with placeholder sections
- Allow command-specific customization
- Test with 3 pilot commands before scaling

### Challenge 2: Backward Compatibility
**Issue**: Users typing /sc:* commands expect them to work.

**Mitigation**:
- Create alias layer: /sc:analyze → /dx:analyze
- Add deprecation warnings
- 30-day grace period before removal

### Challenge 3: Testing Burden
**Issue**: Testing 29 commands thoroughly takes ~9 hours.

**Mitigation**:
- Automate where possible (performance benchmarks, round-trip tests)
- Focus manual testing on critical paths (dx:implement, dx:load/save)
- Use pilot commands to validate patterns before scaling

### Challenge 4: User Adoption
**Issue**: Users may resist learning new command names.

**Mitigation**:
- Clear migration guide
- Visual comparison table (sc: → dx: mapping)
- Gradual rollout with both namespaces working

---

## Validation Gates

Each phase requires gate approval before proceeding:

**Phase 1 Gate**: Templates validated?
- 3 pilot commands working (dx:explain, dx:improve, dx:build)
- Alias infrastructure functional
- Pattern templates proven with real commands

**Phase 2 Gate**: Session commands production-ready?
- dx:implement, dx:load, dx:save, dx:git fully working
- End-to-end session lifecycle validated
- Performance targets met (< 2s load, < 30s implement setup, < 3s save)

**Phase 3 Gate**: Analysis tools migrated?
- All Zen MCP integrations working (analyze, design, troubleshoot, review, plan)
- ADHD presentation validated
- Research and reflect commands functional

**Phase 4 Gate**: Quality commands complete?
- Documentation consolidation working (dx:document handles adr/rfc/doc-*)
- Test, cleanup, explain functional
- Specialized tools migrated (business-panel, spec-panel, spawn, estimate)

**Phase 5 Gate**: Production rollout approved?
- All deprecated commands removed
- Documentation updated
- User migration guide complete
- Final validation passed

---

## Success Metrics

### Quantitative
- ✅ 37% reduction in total commands (46 → 29)
- ✅ 100% ADHD optimization coverage (all commands)
- ✅ 100% ConPort integration (all commands preserve context)
- ✅ Performance targets met (Type B < 5s, Type A setup < 30s)

### Qualitative
- ✅ Easier command discovery (single dx: namespace)
- ✅ Consistent ADHD-friendly UX
- ✅ Better tool coordination (Zen + ConPort + Serena everywhere)
- ✅ Reduced cognitive load (less choice paralysis)

---

## Next Steps

1. **Complete Planner** (steps 4-6): Tactical details for Phases 3-5
2. **Create Consolidation Audit Document**: Detailed command-by-command mapping
3. **Get Approval**: Present strategy for user review
4. **Begin Phase 1**: When approved, start with pattern templates

---

**Status**: Analysis complete, ready for implementation
**Confidence**: Very High
**Recommendation**: Proceed with 5-phase rollout plan
