# Command Consolidation Implementation Plan

**Date**: 2025-10-04
**Planning Tool**: Zen planner (3 steps completed, 3 remaining)
**Status**: Phases 1-2 detailed, Phases 3-5 tactical planning in progress

---

## Plan Overview

**Duration**: 5 weeks
**Phases**: 5 sequential phases with validation gates
**Resources**: 1 developer (full-time for Phases 1-2, part-time for Phases 3-5)
**Risk Level**: Medium (high impact on user workflows, manageable with phased rollout)

---

## Phase 1: Foundation & Pattern Templates (Week 1, 5 days)

### Objectives
- Create reusable pattern templates for Type A/B/C commands
- Validate templates with 3 pilot commands
- Establish alias infrastructure for backward compatibility
- Set up testing framework for consolidated commands

### Detailed Tasks

**Day 1-2: Pattern Template Creation**

1. **Create Type A Pattern Template** (4 hours)
   - File: `/Users/hue/code/dopemux-mvp/.claude/templates/type-a-pattern.md`
   - Structure: 4-phase (ADHD Assessment → Session Setup → Technical Execution → Session Complete)
   - Placeholders: Persona activation, MCP coordination, ConPort integration
   - ADHD Engine integration with graceful degradation
   - Deliverable: Template file with clear instructions for adaptation

2. **Create Type B Pattern Template** (2 hours)
   - File: `/Users/hue/code/dopemux-mvp/.claude/templates/type-b-pattern.md`
   - Structure: 2-phase (Quick Check → Technical Execution with ADHD Presentation)
   - Performance target: < 5s total
   - Visual formatting layer only (no session overhead)
   - Deliverable: Lightweight template for quick commands

3. **Create Type C Pattern Template** (3 hours)
   - File: `/Users/hue/code/dopemux-mvp/.claude/templates/type-c-pattern.md`
   - Structure: Extended multi-chunk session with break reminders
   - Progress tracking across 25-minute chunks
   - Hyperfocus warning for > 90min tasks
   - Deliverable: Template for long-running tasks

**Day 3: Pilot Command Implementation**

4. **Implement dx:explain (Type B Pilot)** (3 hours)
   - Source: Merge sc:explain with ADHD presentation layer
   - Test: Response time < 5s
   - Validate: Quick pattern works, visual formatting effective
   - File: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/explain.md`

5. **Implement dx:improve (Type A Pilot)** (4 hours)
   - Source: Merge sc:improve with full 4-phase pattern
   - Test: Energy assessment, session management, break reminders
   - Validate: Full session pattern works end-to-end
   - File: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/improve.md`

6. **Implement dx:build (Type C Pilot)** (4 hours)
   - Source: Merge sc:build with extended pattern
   - Test: Multi-chunk session, break reminders at 25-min intervals
   - Validate: Long-running pattern handles 30-60 min tasks
   - File: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/build.md`

**Day 4: Alias Infrastructure**

7. **Create Alias System** (3 hours)
   - File: `/Users/hue/.claude/commands/sc-aliases.md`
   - Aliases: sc:explain → dx:explain, sc:improve → dx:improve, sc:build → dx:build
   - Deprecation warnings: "sc: commands deprecated, use /dx:[command] instead"
   - Deliverable: Working redirect system

8. **Test Alias Redirects** (2 hours)
   - Test: User types /sc:explain → redirects to dx:explain
   - Validate: Warning message appears
   - Validate: Full functionality preserved
   - Edge case: What if user types /sc:nonexistent?

**Day 5: Validation & Gate**

9. **Comprehensive Pilot Testing** (4 hours)
   - Functional: All 3 pilots work correctly
   - Performance: Type B < 5s, Type A setup < 30s, Type C handles long tasks
   - ADHD: Energy assessment, break reminders, visual formatting
   - Error handling: ConPort unavailable, ADHD Engine down, Serena unavailable
   - Deliverable: Test report with pass/fail for each criterion

10. **Gate Decision** (1 hour)
    - Review: Are templates validated with real commands?
    - Decision: Proceed to Phase 2 OR iterate on templates
    - If no: Document issues, revise templates, re-test
    - If yes: Document success, greenlight Phase 2

### Phase 1 Dependencies
- None (foundation phase)

### Phase 1 Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Pattern templates too rigid | Medium | High | Keep minimal, allow customization |
| Alias infrastructure breaks | Low | High | Thorough testing Day 4 |
| Pilot commands reveal template flaws | Medium | Medium | That's the point - fix before scaling |
| ADHD Engine unavailable in tests | Medium | Low | Test graceful degradation explicitly |

### Phase 1 Deliverables
- ✅ 3 pattern template files (type-a, type-b, type-c)
- ✅ 3 working pilot commands (dx:explain, dx:improve, dx:build)
- ✅ Alias infrastructure functional (sc-aliases.md)
- ✅ Validation report with gate decision

### Phase 1 Success Criteria
- All 3 pilots pass functional tests
- Performance targets met (< 5s for Type B, < 30s setup for Type A)
- Alias redirects work with deprecation warnings
- Templates proven adaptable to different command needs

---

## Phase 2: Session Commands - Highest Impact (Week 2, 5 days)

### Objectives
- Merge dx:implement + sc:implement (most critical command)
- Merge dx:load/save + sc:load/save (context preservation)
- Rename dx:commit → dx:git with sc:git features
- Validate session lifecycle works end-to-end

### Detailed Tasks

**Day 1-2: dx:implement Merger (CRITICAL PATH)**

1. **Create Merged dx:implement** (8 hours across 2 days)
   - File: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/implement.md`
   - Phase 1 (from dx:): ADHD Engine energy check, task complexity, suitability confirmation
   - Phase 2 (from dx:): ConPort status → IN_PROGRESS, 25-minute timer, session start message
   - Phase 3 (from sc:): Persona activation (architect, frontend, backend, security, qa), PAL apilookup framework patterns, Magic UI generation, Zen analysis, Playwright testing
   - Phase 4 (from dx:): Status check, ConPort update, break reminder, celebration
   - Backup: Keep original as `dx/implement.md.bak`

2. **Extensive dx:implement Testing** (6 hours across 2 days)
   - Test 1: With ADHD Engine available → Full assessment flow
   - Test 2: ADHD Engine unavailable → Graceful degradation, session still works
   - Test 3: React component → Magic MCP activates, frontend persona
   - Test 4: API service → Backend + Security personas, no UI generation
   - Test 5: Full-stack feature → Multi-persona coordination, PAL apilookup + Magic + Zen
   - Measure: Setup < 30s, execution works, break reminder at 25min
   - Deliverable: Test results for all 5 scenarios

**Day 3: dx:load/save Merger**

3. **Create Merged dx:load** (4 hours)
   - File: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/load.md`
   - Phase 1 (from dx:): get_active_context, get_recent_activity_summary (24h, max 10), visual formatting
   - Phase 2 (from sc:): activate_project (Serena), list_memories/read_memory, restore checkpoints
   - Phase 3 (both): ADHD presentation (progressive disclosure), encouraging message
   - Performance target: < 2s total
   - Test: Round-trip with dx:save (data preservation)

4. **Create Merged dx:save** (5 hours)
   - File: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/save.md`
   - Phase 1 (from dx:): Auto-capture git state, open files, ADHD metrics
   - Phase 2 (from dx:): Prompt user for work summary, check for decisions
   - Phase 3 (from sc:): write_memory (Serena), summarize_changes, think_about_collected_information
   - Phase 4 (from dx:): update_active_context (ConPort), log_progress, session backup file
   - Performance target: < 3s total
   - Test: Save all fields, load back, verify match

**Day 4: dx:git Consolidation**

5. **Rename and Merge dx:git** (4 hours)
   - Source: Rename `/Users/hue/code/dopemux-mvp/.claude/commands/dx/commit.md` → `dx/git.md`
   - Keep: dx:commit precommit validation logic
   - Add: sc:git comprehensive features (branch, PR, rebase, log, status)
   - Add: ADHD-friendly git status presentation (visual formatting)
   - Test: commit workflow, branch creation, PR creation

6. **Update Aliases** (1 hour)
   - Add sc:implement → dx:implement
   - Add sc:load → dx:load
   - Add sc:save → dx:save
   - Add sc:git → dx:git
   - Test all redirects work

**Day 5: End-to-End Validation**

7. **Session Lifecycle Test** (3 hours)
   - Step 1: User runs `dx:load` → Context restored
   - Step 2: User runs `dx:implement "add login form"` → Session starts, work happens
   - Step 3: User runs `dx:git "commit changes"` → Precommit validation, commit succeeds
   - Step 4: User runs `dx:save` → All context saved
   - Step 5: User runs `dx:load` → Previous session restored exactly
   - Validate: ConPort updates work, git state preserved, can resume

8. **Performance Validation** (2 hours)
   - dx:load: < 2s ✓
   - dx:implement setup: < 30s ✓
   - dx:save: < 3s ✓
   - dx:git commit: < 5s ✓
   - Document: Actual times vs targets

9. **Gate Decision** (1 hour)
   - Review: Are session commands production-ready?
   - Decision: Proceed to Phase 3 OR fix issues
   - If no: Document failures, fix, re-test
   - If yes: Greenlight Phase 3

### Phase 2 Dependencies
- Phase 1 templates validated ✓
- ConPort MCP operational (check before starting)
- Serena MCP operational (check before starting)
- ADHD Engine optional (graceful degradation tested)

### Phase 2 Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| dx:implement too complex, breaks | Medium | Critical | Keep .bak file, extensive testing |
| Load/save mismatch (data loss) | Low | Critical | Round-trip testing mandatory |
| User workflows break | Low | High | Aliases active, both namespaces work |
| Performance targets missed | Low | Medium | Optimize or adjust targets |

### Phase 2 Deliverables
- ✅ 4 critical merged commands (implement, load, save, git)
- ✅ 4 corresponding sc: aliases
- ✅ End-to-end validation report
- ✅ Performance benchmarks

### Phase 2 Success Criteria
- dx:implement works with AND without ADHD Engine
- dx:load and dx:save round-trip successfully (no data loss)
- dx:git handles commit, branch, PR workflows
- Session lifecycle test passes completely
- All performance targets met

---

## Phase 3: Analysis Tools (Week 3)

**Status**: Tactical planning in progress

### Objectives
- Migrate sc:analyze, sc:design, sc:troubleshoot (Zen MCP integration)
- Create new dx:review, dx:plan (enhanced capabilities)
- Migrate sc:research, sc:reflect

### High-Level Tasks (to be detailed)
- Day 1-2: Zen MCP integration commands (analyze, design, troubleshoot)
- Day 3: New enhanced commands (review, plan)
- Day 4: Research and reflection commands (research, reflect)
- Day 5: Validation and gate

---

## Phase 4: Quality & Documentation (Week 4)

**Status**: Tactical planning in progress

### Objectives
- Consolidate documentation commands (adr-new, rfc-new, doc-* → dx:document)
- Migrate quality commands (sc:test, sc:cleanup, sc:explain already done in Phase 1)
- Migrate specialized tools (business-panel, spec-panel, spawn, estimate)

### High-Level Tasks (to be detailed)
- Day 1-2: dx:document consolidation (all doc types)
- Day 3: Quality commands (test, cleanup)
- Day 4: Specialized tools (panels, spawn, estimate)
- Day 5: Validation and gate

---

## Phase 5: Cleanup & Migration (Week 5)

**Status**: Tactical planning in progress

### Objectives
- Remove deprecated commands (17 total)
- 30-day deprecation period with warnings
- Update all documentation
- Final validation and rollout

### High-Level Tasks (to be detailed)
- Day 1: Remove deprecated command files, update indexes
- Day 2-3: Documentation updates (CLAUDE.md, command reference)
- Day 4: Final comprehensive testing
- Day 5: Production rollout preparation

---

## Overall Project Tracking

### Completion Status
- Phase 1: Planned (5 days) ⏳
- Phase 2: Planned (5 days) ⏳
- Phase 3: High-level outline 📝
- Phase 4: High-level outline 📝
- Phase 5: High-level outline 📝

### Risk Summary
| Phase | Risk Level | Critical Risks |
|-------|-----------|----------------|
| Phase 1 | Low | Template design flaws |
| Phase 2 | Medium | dx:implement complexity, load/save data loss |
| Phase 3 | Low | Zen MCP integration issues |
| Phase 4 | Low | Documentation consolidation edge cases |
| Phase 5 | Medium | User adoption, migration resistance |

### Next Steps
1. Complete Zen planner steps 4-6 (Phases 3-5 tactical details)
2. Get approval from user for consolidation strategy
3. Begin Phase 1 implementation when approved

---

**Plan Status**: All 5 phases detailed with epic breakdown
**Confidence**: High for all phases
**Epic Breakdown**: See COMMAND_CONSOLIDATION_EPICS.md for granular task breakdown (49 tasks, 68 story points)
**Recommendation**: Review complete plan and epic breakdown, approve to begin Epic 1 implementation
