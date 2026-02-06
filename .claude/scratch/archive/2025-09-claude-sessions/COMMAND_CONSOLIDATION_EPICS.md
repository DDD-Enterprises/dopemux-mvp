# Command Consolidation - Epic Breakdown

**Project**: Consolidate 46 commands → 29 dx: commands with layered architecture
**Duration**: 5 weeks (25 working days)
**Strategy**: Incremental rollout with validation gates
**Target**: 37% reduction + 100% ADHD optimization coverage

---

## Epic Overview

| Epic | Title | Duration | Tasks | Story Points |
|------|-------|----------|-------|--------------|
| E1 | Foundation & Pattern Templates | Week 1 (5d) | 10 | 13 |
| E2 | Session Commands Migration | Week 2 (5d) | 9 | 21 |
| E3 | Analysis Tools Migration | Week 3 (5d) | 10 | 13 |
| E4 | Quality & Documentation | Week 4 (5d) | 11 | 13 |
| E5 | Cleanup & Migration | Week 5 (5d) | 9 | 8 |
| **Total** | | **25 days** | **49 tasks** | **68 SP** |

---

## Epic 1: Foundation & Pattern Templates

**Goal**: Create reusable patterns and validate with pilot commands
**Duration**: Week 1 (5 working days)
**Story Points**: 13
**Owner**: Primary developer
**Dependencies**: None (foundation epic)

### User Stories

**US-1.1**: As a developer, I want pattern templates for Type A/B/C commands so I can consistently implement ADHD-optimized commands
**Acceptance Criteria**:
- 3 template files exist (type-a, type-b, type-c)
- Templates include placeholders for customization
- ADHD Engine integration documented with graceful degradation
- All 3 pilots use templates successfully

**US-1.2**: As a user, I want backward compatibility via aliases so my existing workflows don't break
**Acceptance Criteria**:
- sc-aliases.md functional with redirect logic
- Deprecation warnings display clearly
- All pilot aliases work (sc:explain, sc:improve, sc:build)

**US-1.3**: As a developer, I want validation that patterns work before scaling so we avoid rework
**Acceptance Criteria**:
- All 3 pilots pass functional tests
- Performance targets met (< 5s Type B, < 30s Type A setup, Type C handles 30-60min)
- Gate decision documented with pass/fail

### Task Breakdown

#### Day 1-2: Template Creation (3 tasks, 9 hours)

**E1-T1: Create Type A Pattern Template** [3 SP]
**Estimate**: 4 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/templates/type-a-pattern.md`
**Description**: 4-phase pattern (ADHD Assessment → Session Setup → Technical Execution → Session Complete)
**Subtasks**:
1. Define Phase 1 structure (ADHD Engine energy check, complexity assessment, suitability confirmation)
2. Define Phase 2 structure (ConPort status update, 25-min timer, session start message)
3. Define Phase 3 placeholder (technical execution - varies by command)
4. Define Phase 4 structure (status check, ConPort update, break reminder, celebration)
5. Add ADHD Engine graceful degradation notes
6. Document customization points

**Acceptance**:
- Template file exists with all 4 phases
- Placeholders clearly marked
- Graceful degradation documented
- Ready for pilot implementation

---

**E1-T2: Create Type B Pattern Template** [2 SP]
**Estimate**: 2 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/templates/type-b-pattern.md`
**Description**: 2-phase lightweight pattern (Quick Check → Technical Execution with ADHD Presentation)
**Subtasks**:
1. Define Phase 1 structure (session check, brief energy awareness - no ADHD Engine call)
2. Define Phase 2 structure (technical execution with visual formatting)
3. Define Phase 3 structure (ADHD presentation layer - emojis, progressive disclosure)
4. Document performance target: < 5s total
5. Document when to use Type B vs Type A

**Acceptance**:
- Template file exists with 2-phase structure
- Performance target documented (< 5s)
- Clear guidance on Type B use cases
- Ready for dx:explain pilot

---

**E1-T3: Create Type C Pattern Template** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/templates/type-c-pattern.md`
**Description**: Extended multi-chunk pattern with break reminders every 25 minutes
**Subtasks**:
1. Define extended assessment phase (duration estimate, chunk calculation, hyperfocus warning)
2. Define chunked session setup (multi-chunk ConPort tracking, break reminder intervals)
3. Define progress tracking across chunks ("Chunk 2/3", auto-save every 25min)
4. Define extended completion phase (actual duration, all chunks update, 5-15min break reminder)
5. Document hyperfocus risk mitigation (warn at 90min tasks)
6. Document when to use Type C vs Type A

**Acceptance**:
- Template file exists with chunk-based structure
- Break reminders at 25-min intervals
- Hyperfocus warnings documented
- Ready for dx:build pilot

---

#### Day 3: Pilot Implementation (3 tasks, 11 hours)

**E1-T4: Implement dx:explain (Type B Pilot)** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/explain.md`
**Source**: Merge sc:explain with ADHD presentation layer
**Description**: Quick code explanation with visual formatting
**Subtasks**:
1. Copy type-b-pattern.md as starting point
2. Add Phase 2: Code analysis with Serena LSP (if available) or native analysis
3. Add Phase 3: ADHD presentation (progressive disclosure, max 3 levels, visual formatting)
4. Test: Response time < 5s
5. Test: Quality of explanations maintained
6. Validate: Pattern works, visual formatting effective

**Acceptance**:
- dx:explain command functional
- Response time < 5s consistently
- Visual formatting (emojis, structure) working
- sc:explain alias redirects with deprecation warning

---

**E1-T5: Implement dx:improve (Type A Pilot)** [5 SP]
**Estimate**: 4 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/improve.md`
**Source**: Merge sc:improve with full 4-phase ADHD pattern
**Description**: Code improvement with session management
**Subtasks**:
1. Copy type-a-pattern.md as starting point
2. Add Phase 1: ADHD Engine assessment (complexity of refactoring work)
3. Add Phase 2: ConPort session setup
4. Add Phase 3: sc:improve logic (code analysis, improvement suggestions, optional implementation)
5. Add Phase 4: Status update, break reminder
6. Test: With ADHD Engine available
7. Test: ADHD Engine unavailable (graceful degradation)
8. Test: Session management, break reminders at 25min
9. Validate: Full session pattern works end-to-end

**Acceptance**:
- dx:improve command functional
- Works WITH and WITHOUT ADHD Engine
- Session setup < 30s
- Break reminder at 25min mark
- sc:improve alias redirects

---

**E1-T6: Implement dx:build (Type C Pilot)** [5 SP]
**Estimate**: 4 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/build.md`
**Source**: Merge sc:build with extended chunk pattern
**Description**: Build/compile with multi-chunk session tracking
**Subtasks**:
1. Copy type-c-pattern.md as starting point
2. Add extended assessment: Estimate build duration, calculate chunks
3. Add chunked session setup with 25-min break intervals
4. Add Phase 3: sc:build logic (build/compile, error handling)
5. Add progress updates every 25min ("Chunk 2/3 complete")
6. Add extended completion with session summary
7. Test: 30-min build (2 chunks)
8. Test: 60-min build (3 chunks) with hyperfocus warning
9. Validate: Long-running pattern handles extended tasks

**Acceptance**:
- dx:build command functional
- Break reminders at 25-min intervals
- Chunk progress displayed
- Hyperfocus warning for 60+ min builds
- sc:build alias redirects

---

#### Day 4: Alias Infrastructure (2 tasks, 5 hours)

**E1-T7: Create Alias System** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/.claude/commands/sc-aliases.md`
**Description**: Redirect sc: commands to dx: with deprecation warnings
**Subtasks**:
1. Create sc-aliases.md structure
2. Add redirect logic: sc:explain → dx:explain
3. Add redirect logic: sc:improve → dx:improve
4. Add redirect logic: sc:build → dx:build
5. Add deprecation warning template ("sc: commands deprecated, use /dx:[command] instead")
6. Document 30-day deprecation timeline
7. Add error handling for sc:nonexistent commands

**Acceptance**:
- Alias file exists and functional
- All 3 pilot aliases redirect correctly
- Deprecation warnings display
- Error handling for invalid commands

---

**E1-T8: Test Alias Redirects** [2 SP]
**Estimate**: 2 hours
**Description**: Validate alias system works correctly
**Test Cases**:
1. User types /sc:explain → redirects to dx:explain, shows warning
2. User types /sc:improve → redirects to dx:improve, shows warning
3. User types /sc:build → redirects to dx:build, shows warning
4. User types /sc:nonexistent → shows helpful error message
5. Deprecation warning is clear and actionable

**Acceptance**:
- All test cases pass
- Warnings are user-friendly
- Error messages helpful

---

#### Day 5: Validation & Gate (2 tasks, 5 hours)

**E1-T9: Comprehensive Pilot Testing** [3 SP]
**Estimate**: 4 hours
**Test Matrix**:

| Test Dimension | dx:explain | dx:improve | dx:build |
|----------------|------------|------------|----------|
| Functional | ✓ Explains code | ✓ Suggests improvements | ✓ Builds project |
| Performance | < 5s | Setup < 30s | Handles 30-60min |
| ADHD - Energy | N/A (Type B) | ✓ Assessment works | ✓ Duration estimate |
| ADHD - Breaks | N/A (too quick) | ✓ 25min reminder | ✓ Every 25min |
| ADHD - Visual | ✓ Formatting | ✓ Progress indicators | ✓ Chunk progress |
| Error - No ADHD Engine | N/A | ✓ Graceful degradation | ✓ Graceful degradation |
| Error - No ConPort | N/A (Type B) | ✓ Works without | ✓ Works without |
| Alias | ✓ sc:explain → dx:explain | ✓ sc:improve → dx:improve | ✓ sc:build → dx:build |

**Deliverable**: Test report with pass/fail for each cell

**Acceptance**:
- All functional tests pass
- Performance targets met
- ADHD features validated
- Error handling confirmed
- Aliases working

---

**E1-T10: Gate Decision** [1 SP]
**Estimate**: 1 hour
**Description**: Review results and decide to proceed or iterate
**Criteria**:
- Are templates validated with real commands? (Yes/No)
- Do all 3 pilots work correctly? (Yes/No)
- Are performance targets met? (Yes/No)
- Is alias infrastructure functional? (Yes/No)

**Decision Matrix**:
- All Yes → Proceed to Epic 2
- Any No → Document issues, revise templates, re-test

**Deliverable**: Gate decision document with:
- Test results summary
- Issues found (if any)
- Decision: Proceed or Iterate
- If proceed: Greenlight Epic 2
- If iterate: List of fixes needed

**Acceptance**:
- Decision documented
- If proceed: Epic 2 approved to start
- If iterate: Fix plan created

---

### Epic 1 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Pattern templates too rigid | Medium | High | Keep minimal, allow customization, validate with 3 diverse pilots |
| Alias infrastructure breaks existing workflows | Low | High | Thorough testing Day 4, user communication |
| Pilot commands reveal template flaws | Medium | Medium | That's the point - fix before scaling to 29 commands |
| ADHD Engine unavailable during tests | Medium | Low | Test graceful degradation explicitly |

---

### Epic 1 Dependencies

**External**:
- None (foundation epic)

**Internal**:
- Access to existing sc: and dx: command files
- ADHD Engine running (optional, test degradation)
- ConPort operational

---

### Epic 1 Success Metrics

- ✅ 3 pattern templates created and validated
- ✅ 3 pilot commands functional
- ✅ Alias infrastructure working
- ✅ All tests passing
- ✅ Gate approval to proceed to Epic 2

---

## Epic 2: Session Commands Migration

**Goal**: Migrate critical session lifecycle commands (implement, load, save, git)
**Duration**: Week 2 (5 working days)
**Story Points**: 21
**Owner**: Primary developer
**Dependencies**: Epic 1 complete (patterns validated)

### User Stories

**US-2.1**: As a user, I want dx:implement with full ADHD session management and technical execution so I can focus effectively
**Acceptance Criteria**:
- Works WITH and WITHOUT ADHD Engine
- Merges dx: ADHD features + sc: technical execution (personas, MCPs)
- Session setup < 30s
- All 5 test scenarios pass (see E2-T2)

**US-2.2**: As a user, I want dx:load and dx:save to preserve full context across sessions so I never lose progress
**Acceptance Criteria**:
- Round-trip test passes (save → load → all data preserved)
- Works with ConPort only OR Serena only (graceful degradation)
- Performance: load < 2s, save < 3s
- Git state, ADHD metrics, decisions all preserved

**US-2.3**: As a user, I want dx:git to handle all git operations with ADHD-friendly presentation so I don't avoid version control
**Acceptance Criteria**:
- Combines dx:commit precommit validation + sc:git comprehensive features
- ADHD-friendly git status presentation
- Commit, branch, PR workflows all functional

### Task Breakdown

#### Day 1-2: dx:implement Merger (2 tasks, 14 hours - CRITICAL PATH)

**E2-T1: Create Merged dx:implement** [8 SP]
**Estimate**: 8 hours across 2 days (4h/day)
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/implement.md`
**Backup**: Keep original as `dx/implement.md.bak`
**Description**: Merge dx: ADHD assessment + sc: technical execution (most complex command)
**Subtasks**:
1. Backup existing dx:implement to dx/implement.md.bak
2. Copy type-a-pattern.md as foundation
3. **Phase 1 (from dx:)**: ADHD Engine energy check, task complexity (0.0-1.0), suitability confirmation
4. **Phase 2 (from dx:)**: ConPort status → IN_PROGRESS, 25-minute timer, session start message
5. **Phase 3 (from sc:)**: Persona activation logic
   - Architect persona: System design analysis
   - Frontend persona: React/Vue/Angular detection, Magic MCP for UI
   - Backend persona: API/service implementation
   - Security persona: Auth, validation, security review
   - QA persona: Test generation
6. **Phase 3 (from sc:)**: MCP coordination
   - PAL apilookup: Framework patterns (React, Next.js, Vue, Express)
   - Magic: UI component generation for frontend tasks
   - Zen: Analysis for complex features
   - Playwright: E2E test generation
7. **Phase 4 (from dx:)**: Status check, ConPort update, break reminder, celebration
8. Document persona selection logic (auto vs manual)
9. Document framework detection logic
10. Add error handling for all MCPs unavailable

**Acceptance**:
- Merged command functional
- All personas work correctly
- All MCPs integrate properly
- ADHD features preserved
- sc: technical capabilities preserved

---

**E2-T2: Extensive dx:implement Testing** [8 SP]
**Estimate**: 6 hours across 2 days (3h/day)
**Description**: Validate most critical command works in all scenarios
**Test Scenarios**:

1. **Test 1: With ADHD Engine available**
   - Full assessment flow works
   - Energy matching functional
   - Suitability score calculated correctly

2. **Test 2: ADHD Engine unavailable**
   - Graceful degradation: Session still works
   - Warning displayed
   - No blocking errors

3. **Test 3: React component implementation**
   - Frontend persona activated
   - Magic MCP generates UI
   - PAL apilookup provides React patterns
   - Result: Working component code

4. **Test 4: API service implementation**
   - Backend + Security personas activated
   - No UI generation attempted
   - Zen analysis for complex logic
   - Result: API endpoint with validation

5. **Test 5: Full-stack feature**
   - Multi-persona coordination
   - PAL apilookup + Magic + Zen all used
   - Frontend + Backend integration
   - Result: Complete feature

**Performance Targets**:
- Setup < 30s
- Execution works correctly
- Break reminder at 25min mark

**Deliverable**: Test results for all 5 scenarios

**Acceptance**:
- All 5 tests pass
- Performance targets met
- No regressions from original commands

---

#### Day 3: dx:load/save Merger (2 tasks, 9 hours)

**E2-T3: Create Merged dx:load** [5 SP]
**Estimate**: 4 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/load.md`
**Description**: Merge ConPort + Serena context loading with ADHD presentation
**Subtasks**:
1. **Phase 1 (from dx:)**: ConPort retrieval
   - `mcp__conport__get_active_context`
   - `mcp__conport__get_recent_activity_summary --hours_ago 24 --limit_per_type 10`
   - Visual formatting (progressive disclosure)
2. **Phase 2 (from sc:)**: Serena memory retrieval
   - `mcp__serena__activate_project` (workspace auto-detection)
   - `mcp__serena__list_memories`
   - `mcp__serena__read_memory` for active tasks
3. **Phase 3 (both)**: ADHD presentation
   - Essential info first (current focus, next steps)
   - Recent activity (max 10 items, recent-first)
   - Encouraging message ("Welcome back! You were working on X...")
4. Add performance target: < 2s total
5. Add graceful degradation: ConPort only OR Serena only
6. Test: Round-trip with dx:save (data preservation)

**Acceptance**:
- dx:load command functional
- Performance < 2s
- Works with ConPort only
- Works with Serena only
- ADHD presentation clear
- sc:load alias redirects

---

**E2-T4: Create Merged dx:save** [5 SP]
**Estimate**: 5 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/save.md`
**Description**: Comprehensive context saving with auto-capture and user prompts
**Subtasks**:
1. **Phase 1 (from dx:)**: Auto-capture git state
   - `git branch --show-current`
   - `git status --porcelain`
   - `git log --oneline -5`
   - Open files list
   - ADHD metrics (energy, attention levels)
2. **Phase 2 (from dx:)**: Prompt user for work summary
   - "What did you accomplish this session?"
   - "Any decisions made?" (suggest ConPort logging)
   - "What's next?" (update active_context)
3. **Phase 3 (from sc:)**: Serena memory operations
   - `mcp__serena__write_memory` (session summary)
   - `mcp__serena__summarize_changes` (code changes)
   - `mcp__serena__think_about_collected_information`
4. **Phase 4 (from dx:)**: ConPort save
   - `mcp__conport__update_active_context` with:
     - current_focus
     - completed_tasks
     - next_steps
     - git_state: {branch, changed_files, recent_commits}
     - adhd_metrics: {final_energy, final_attention}
   - `mcp__conport__log_progress` for completed tasks
   - Session backup file in `.claude/sessions/`
5. Add performance target: < 3s total
6. Test: Save all fields, load back, verify match

**Acceptance**:
- dx:save command functional
- All data captured (git, ADHD, decisions)
- Performance < 3s
- Round-trip test passes
- sc:save alias redirects

---

#### Day 4: dx:git Consolidation (2 tasks, 5 hours)

**E2-T5: Rename and Merge dx:git** [3 SP]
**Estimate**: 4 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/git.md`
**Source**: Rename `dx/commit.md` → `dx/git.md`, merge sc:git features
**Description**: Unified git interface with precommit validation + comprehensive operations
**Subtasks**:
1. Rename `/Users/hue/code/dopemux-mvp/.claude/commands/dx/commit.md` → `dx/git.md`
2. Keep: dx:commit precommit validation logic (Zen precommit)
3. Add (from sc:git): Branch operations (create, switch, list)
4. Add (from sc:git): PR operations (create, list, review)
5. Add (from sc:git): Rebase, log, status operations
6. Add: ADHD-friendly git status presentation
   - Visual formatting (✅ staged, 📝 modified, ❓ untracked)
   - Max 10 files per category (prevent overwhelm)
   - Actionable suggestions
7. Test: Commit workflow with precommit validation
8. Test: Branch creation and switching
9. Test: PR creation with auto-generated description

**Acceptance**:
- dx:git handles commit, branch, PR workflows
- Precommit validation works
- ADHD presentation clear
- sc:git alias redirects
- dx:commit alias redirects to dx:git

---

**E2-T6: Update Aliases for Session Commands** [1 SP]
**Estimate**: 1 hour
**File**: `/Users/hue/.claude/commands/sc-aliases.md`
**Description**: Add new redirects for session commands
**Subtasks**:
1. Add sc:implement → dx:implement
2. Add sc:load → dx:load
3. Add sc:save → dx:save
4. Add sc:git → dx:git
5. Test all redirects work
6. Verify deprecation warnings display

**Acceptance**:
- 4 new aliases functional
- All redirects tested
- Warnings clear

---

#### Day 5: End-to-End Validation (3 tasks, 6 hours)

**E2-T7: Session Lifecycle Test** [3 SP]
**Estimate**: 3 hours
**Description**: Validate complete user workflow
**Test Workflow**:
1. User runs `dx:load`
   - ✓ Context restored from previous session
   - ✓ ADHD presentation clear
   - ✓ Performance < 2s
2. User runs `dx:implement "add login form"`
   - ✓ ADHD assessment works
   - ✓ Session starts
   - ✓ Persona coordination works
   - ✓ Feature implemented
   - ✓ Break reminder at 25min
3. User runs `dx:git "commit changes"`
   - ✓ Precommit validation runs
   - ✓ Commit succeeds
   - ✓ Git state updated
4. User runs `dx:save`
   - ✓ All context saved
   - ✓ Performance < 3s
5. User runs `dx:load` again
   - ✓ Previous session restored exactly
   - ✓ Can resume work

**Acceptance**:
- All steps pass
- Context preservation works
- Session continuity maintained
- Can resume from any point

---

**E2-T8: Performance Validation** [2 SP]
**Estimate**: 2 hours
**Description**: Measure actual performance vs targets
**Measurements**:
- dx:load: Target < 2s
- dx:implement setup: Target < 30s
- dx:save: Target < 3s
- dx:git commit: Target < 5s

**Document**: Actual times vs targets

**Acceptance**:
- All performance targets met
- If not met: Document why, plan optimization

---

**E2-T9: Gate Decision for Epic 2** [1 SP]
**Estimate**: 1 hour
**Description**: Review Epic 2 results
**Criteria**:
- Are session commands production-ready? (Yes/No)
- Does session lifecycle work end-to-end? (Yes/No)
- Are performance targets met? (Yes/No)

**Decision**:
- All Yes → Proceed to Epic 3
- Any No → Document failures, fix, re-test

**Acceptance**:
- Decision documented
- If proceed: Epic 3 greenlit
- If iterate: Fix plan created

---

### Epic 2 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| dx:implement too complex, breaks | Medium | Critical | Keep .bak file, extensive testing (6 hours allocated) |
| Load/save mismatch causes data loss | Low | Critical | Round-trip testing mandatory |
| User workflows break during migration | Low | High | Aliases active, both namespaces work simultaneously |
| Performance targets missed | Low | Medium | Optimize or adjust targets based on empirical data |

---

### Epic 2 Success Metrics

- ✅ 4 critical merged commands functional
- ✅ Session lifecycle validated end-to-end
- ✅ Performance targets met
- ✅ No data loss in round-trip tests
- ✅ Gate approval to proceed to Epic 3

---

## Epic 3: Analysis Tools Migration

**Goal**: Migrate Zen MCP integration commands and create enhanced analysis capabilities
**Duration**: Week 3 (5 working days)
**Story Points**: 13
**Owner**: Primary developer
**Dependencies**: Epic 2 complete (session commands validated)

### User Stories

**US-3.1**: As a user, I want Zen-powered analysis commands with ADHD session management so I can investigate complex problems without burnout
**Acceptance Criteria**:
- dx:analyze (thinkdeep), dx:design (consensus), dx:troubleshoot (debug) all functional
- ADHD session management for all (energy matching, breaks)
- Zen MCP integration working correctly

**US-3.2**: As a user, I want new dx:review and dx:plan commands to fill gaps in current tooling
**Acceptance Criteria**:
- dx:review uses Zen codereview for comprehensive analysis
- dx:plan uses Zen planner for interactive planning
- Both integrate with ConPort (save findings/plans)

**US-3.3**: As a user, I want dx:research and dx:reflect for learning and reflection
**Acceptance Criteria**:
- dx:research handles 10-30 min research with break reminders (Type C)
- dx:reflect provides quick critical thinking validation (Type B)

### Task Breakdown

#### Day 1-2: Zen MCP Commands (3 tasks, 8 hours)

**E3-T1: Migrate sc:analyze → dx:analyze** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/analyze.md`
**Source**: `/Users/hue/.claude/commands/sc/analyze.md`
**Pattern**: Type A (full 4-phase session)
**Description**: Multi-step investigation with Zen thinkdeep
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check (analysis = high complexity typically)
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Zen thinkdeep integration
   - `mcp__zen__thinkdeep` with hypothesis-driven investigation
   - Multi-step reasoning with evidence gathering
   - File analysis and code inspection
   - Confidence tracking (exploring → certain)
5. **Phase 4**: Save findings to ConPort custom_data category "analyses"
6. Link analysis to relevant decisions via `link_conport_items`
7. Test: Simple analysis (3 steps)
8. Test: Complex analysis (5 steps)
9. Test: With/without ADHD Engine

**Acceptance**:
- dx:analyze functional
- Zen thinkdeep integration working
- Findings saved to ConPort
- sc:analyze alias redirects

---

**E3-T2: Migrate sc:design → dx:design** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/design.md`
**Source**: `/Users/hue/.claude/commands/sc/design.md`
**Pattern**: Type A (design decisions need focus)
**Description**: Multi-model consensus for design decisions
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Zen consensus integration
   - Define design question/proposal
   - Consult 2-5 models with different stances
   - Synthesize recommendation with trade-offs
5. **Phase 4**: Log design decision to ConPort
6. Link to related decisions via `link_conport_items`
7. Test: Architecture decisions (microservices vs monolith)
8. Test: Technology evaluation (framework comparison)
9. Test: Multi-model consensus quality

**Acceptance**:
- dx:design functional
- Zen consensus integration working
- Decisions logged to ConPort
- sc:design alias redirects

---

**E3-T3: Migrate sc:troubleshoot → dx:troubleshoot** [2 SP]
**Estimate**: 2 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/troubleshoot.md`
**Source**: `/Users/hue/.claude/commands/sc/troubleshoot.md`
**Pattern**: Type A (debugging requires focus)
**Description**: Systematic debugging with Zen debug
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Zen debug integration
   - Hypothesis-testing workflow
   - Code inspection and log analysis
   - Root cause identification
   - Fix recommendation with validation
5. **Phase 4**: Document root cause in ConPort
6. Test: Bug investigation (reproduce → identify → fix)
7. Test: Performance issues
8. Test: Mysterious errors with unclear cause

**Acceptance**:
- dx:troubleshoot functional
- Zen debug integration working
- Root causes documented in ConPort
- sc:troubleshoot alias redirects

---

#### Day 3: New Enhanced Commands (2 tasks, 5 hours)

**E3-T4: Create dx:review (NEW)** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/review.md`
**Pattern**: Type A (comprehensive review needs focus)
**Description**: Multi-dimensional code review with Zen codereview
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Zen codereview integration
   - Review type: full, security, performance, quick
   - Dimensions: quality, security, performance, architecture
   - Issue severity: critical, high, medium, low
   - Actionable recommendations
5. **Phase 4**: Log review findings to ConPort custom_data category "code_reviews"
6. Test: Full review (all dimensions)
7. Test: Security-focused review
8. Test: Performance-focused review

**Acceptance**:
- dx:review functional
- Zen codereview integration working
- Findings saved to ConPort
- All review types work

---

**E3-T5: Create dx:plan (NEW)** [2 SP]
**Estimate**: 2 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/plan.md`
**Pattern**: Type A (planning is cognitive work)
**Description**: Interactive planning with Zen planner
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Zen planner integration
   - Incremental plan building
   - Step-by-step refinement
   - Branch exploration for alternatives
   - Revision support
5. **Phase 4**: Save plan to ConPort custom_data category "implementation_plans"
6. Test: Simple project planning (3 steps)
7. Test: Complex planning with branching (5+ steps)
8. Test: Plan revision

**Acceptance**:
- dx:plan functional
- Zen planner integration working
- Plans saved to ConPort
- Branching and revision work

---

#### Day 4: Research and Reflection (2 tasks, 5 hours)

**E3-T6: Migrate sc:research → dx:research** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/research.md`
**Source**: `/Users/hue/.claude/commands/sc/research.md`
**Pattern**: Type C (research can take 10-30 minutes)
**Description**: Deep research with GPT-Researcher and chunk-based sessions
**Subtasks**:
1. Copy type-c-pattern.md as foundation
2. **Extended Assessment**: Estimate research depth, calculate chunks (25-min intervals)
3. **Chunked Session**: Break reminders every 25 minutes
4. **Phase 3**: GPT-Researcher integration
   - `mcp__gpt-researcher__deep_research` with multi-source synthesis
   - Progress updates during research ("Analyzing source 5/15...")
   - Auto-save checkpoints every 25min
5. **Extended Completion**: Save research_id to ConPort for later reference
6. Test: Quick research (< 10 min)
7. Test: Deep research (20-30 min, 2-3 chunks)
8. Test: Report generation

**Acceptance**:
- dx:research functional
- Type C pattern working (break reminders)
- GPT-Researcher integration working
- research_id saved to ConPort
- sc:research alias redirects

---

**E3-T7: Migrate sc:reflect → dx:reflect** [2 SP]
**Estimate**: 2 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/reflect.md`
**Source**: `/Users/hue/.claude/commands/sc/reflect.md`
**Pattern**: Type B (reflection should be quick)
**Description**: Critical thinking validation with Zen challenge
**Subtasks**:
1. Copy type-b-pattern.md as foundation
2. **Phase 1**: Quick session check
3. **Phase 2**: Zen challenge integration
   - Prevents reflexive agreement
   - Forces critical evaluation
   - Truth-seeking over compliance
4. **Phase 3**: ADHD presentation (visual formatting)
5. Test: Task reflection (validate implementation choices)
6. Test: Decision validation (challenge assumptions)

**Acceptance**:
- dx:reflect functional
- Zen challenge integration working
- Quick response (< 5s)
- sc:reflect alias redirects

---

#### Day 5: Validation and Gate (3 tasks, 5 hours)

**E3-T8: Comprehensive Testing of Analysis Tools** [3 SP]
**Estimate**: 3 hours
**Test Matrix**:

| Command | Functional | ADHD | Zen MCP | Performance | ConPort |
|---------|-----------|------|---------|-------------|---------|
| dx:analyze | ✓ thinkdeep | ✓ session | ✓ working | < 30s setup | ✓ findings saved |
| dx:design | ✓ consensus | ✓ session | ✓ working | < 30s setup | ✓ decisions logged |
| dx:troubleshoot | ✓ debug | ✓ session | ✓ working | < 30s setup | ✓ root cause saved |
| dx:review | ✓ codereview | ✓ session | ✓ working | < 30s setup | ✓ reviews saved |
| dx:plan | ✓ planner | ✓ session | ✓ working | < 30s setup | ✓ plans saved |
| dx:research | ✓ GPT-Researcher | ✓ chunks, breaks | N/A | Handles 30min | ✓ research_id saved |
| dx:reflect | ✓ challenge | ✓ quick | ✓ working | < 5s | N/A |

**Acceptance**:
- All tests pass
- Zen MCP integration validated
- ADHD features working
- ConPort integration confirmed

---

**E3-T9: Update Aliases for Analysis Tools** [1 SP]
**Estimate**: 1 hour
**Subtasks**:
1. Add sc:analyze → dx:analyze
2. Add sc:design → dx:design
3. Add sc:troubleshoot → dx:troubleshoot
4. Add sc:research → dx:research
5. Add sc:reflect → dx:reflect
6. Test all redirects

**Acceptance**:
- 5 new aliases functional
- All tested

---

**E3-T10: Gate Decision for Epic 3** [1 SP]
**Estimate**: 1 hour
**Criteria**:
- Are analysis tools production-ready? (Yes/No)
- Is Zen MCP integration working for all tools? (Yes/No)
- Are performance targets met? (Yes/No)

**Decision**:
- All Yes → Proceed to Epic 4
- Any No → Fix and re-test

**Acceptance**:
- Decision documented
- If proceed: Epic 4 greenlit

---

### Epic 3 Success Metrics

- ✅ 7 commands functional (5 migrated + 2 new)
- ✅ Zen MCP integration validated
- ✅ ADHD features working across all
- ✅ ConPort integration confirmed
- ✅ Gate approval to proceed to Epic 4

---

## Epic 4: Quality & Documentation

**Goal**: Consolidate documentation commands and migrate quality/specialized tools
**Duration**: Week 4 (5 working days)
**Story Points**: 13
**Owner**: Primary developer
**Dependencies**: Epic 3 complete (analysis tools validated)

### User Stories

**US-4.1**: As a user, I want a single dx:document command that handles all documentation types so I don't need to remember 9 different commands
**Acceptance Criteria**:
- dx:document --type adr|rfc|how-to|reference|explanation works
- Consolidates adr-new, rfc-new, doc-new, doc-pull, doc-ensure-frontmatter
- All templates and standards preserved

**US-4.2**: As a user, I want dx:test and dx:cleanup with ADHD session management so quality work doesn't exhaust me
**Acceptance Criteria**:
- dx:test handles test execution with session tracking
- dx:cleanup handles code cleanup with progress indicators
- Both use Type A pattern (session management)

**US-4.3**: As a user, I want specialized tools (business-panel, spec-panel, spawn, estimate) migrated to dx: namespace
**Acceptance Criteria**:
- All 4 specialized tools functional
- ADHD patterns applied appropriately
- Integration with Zen/ConPort preserved

### Task Breakdown

#### Day 1-2: dx:document Consolidation (3 tasks, 8 hours)

**E4-T1: Create dx:document (Consolidates 9 commands)** [5 SP]
**Estimate**: 5 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/document.md`
**Replaces**:
- adr-new, rfc-new (ADR/RFC creation)
- rfc-lint, rfc-promote (RFC workflow)
- doc-new, doc-pull (How-to guides)
- doc-ensure-frontmatter (Metadata enforcement)
- docs-helper (General documentation)

**Pattern**: Type A (documentation is cognitive work)
**Description**: Unified documentation interface with type selection
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check (documentation complexity varies)
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Documentation generation logic
   - `--type adr`: Architecture Decision Record
     - Template: `.claude/templates/adr-template.md`
     - Location: `docs/90-adr/`
     - Frontmatter: id, title, type, owner, date, status
   - `--type rfc`: Request for Comments
     - Template: `.claude/templates/rfc-template.md`
     - Location: `docs/91-rfc/`
     - Workflow: lint → promote to ADR
   - `--type how-to`: How-to Guide
     - Location: `docs/02-how-to/`
     - Structure: Problem → Solution → Validation
   - `--type reference`: Technical Reference
     - Location: `docs/03-reference/`
     - Structure: API docs, configuration, schemas
   - `--type explanation`: Deep-Dive Explanation
     - Location: `docs/04-explanation/`
     - Structure: Conceptual understanding
5. Add frontmatter enforcement (always add required fields)
6. Add cross-referencing (link from feature hubs, update _manifest.yaml)
7. **Phase 4**: Log documentation to ConPort custom_data category "documentation"
8. Test: Create ADR
9. Test: Create RFC, lint, promote to ADR
10. Test: Create how-to guide

**Acceptance**:
- dx:document functional for all 5 types
- Templates and standards preserved
- Frontmatter enforcement working
- All old aliases redirect

---

**E4-T2: Create Aliases for Deprecated Doc Commands** [2 SP]
**Estimate**: 2 hours
**Subtasks**:
1. Add adr-new → dx:document --type adr
2. Add rfc-new → dx:document --type rfc
3. Add rfc-lint → dx:document --type rfc --lint
4. Add rfc-promote → dx:document --type rfc --promote
5. Add doc-new → dx:document --type how-to
6. Add doc-pull → dx:document --pull
7. Add doc-ensure-frontmatter → dx:document --ensure-frontmatter
8. Add docs-helper → dx:document --help
9. Test all 8 redirects

**Acceptance**:
- All 8 aliases functional
- Users can still use old commands
- Deprecation warnings clear

---

**E4-T3: Test dx:document Consolidation** [2 SP]
**Estimate**: 1 hour
**Test Cases**:
1. Create ADR → Proper location, frontmatter, template
2. Create RFC → Proper location, frontmatter, template
3. Lint RFC → Validation works
4. Promote RFC to ADR → Workflow works
5. Create how-to → Proper location and structure
6. Ensure frontmatter → Adds missing fields
7. All aliases redirect correctly

**Acceptance**:
- All test cases pass
- No regressions

---

#### Day 3: Quality Commands (2 tasks, 5 hours)

**E4-T4: Migrate sc:test → dx:test** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/test.md`
**Source**: `/Users/hue/.claude/commands/sc/test.md`
**Pattern**: Type A (testing requires focus)
**Description**: Test execution with session management
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Test execution
   - Detect test framework (pytest, jest, vitest, etc.)
   - Run tests with coverage
   - Parse results
   - Format output (ADHD-friendly: failures first, summary)
5. **Phase 4**: Log test results to ConPort
6. Test: Python tests (pytest)
7. Test: JavaScript tests (jest/vitest)
8. Test: Coverage analysis

**Acceptance**:
- dx:test functional
- Multiple frameworks supported
- Coverage analysis working
- sc:test alias redirects

---

**E4-T5: Migrate sc:cleanup → dx:cleanup** [2 SP]
**Estimate**: 2 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/cleanup.md`
**Source**: `/Users/hue/.claude/commands/sc/cleanup.md`
**Pattern**: Type A (cleanup is cognitive work)
**Description**: Code cleanup with progress tracking
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. **Phase 1**: ADHD Engine energy check
3. **Phase 2**: ConPort session setup
4. **Phase 3**: Cleanup operations
   - Remove dead code
   - Fix linting issues
   - Organize imports
   - Format code
   - Progress indicators (e.g., "Cleaned 5/12 files")
5. **Phase 4**: Log cleanup summary to ConPort
6. Test: Dead code removal
7. Test: Lint fix
8. Test: Import organization

**Acceptance**:
- dx:cleanup functional
- Progress tracking working
- sc:cleanup alias redirects

---

#### Day 4: Specialized Tools (4 tasks, 5 hours)

**E4-T6: Migrate sc:business-panel → dx:business-panel** [2 SP]
**Estimate**: 1.5 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/business-panel.md`
**Source**: `/Users/hue/.claude/commands/sc/business-panel.md`
**Pattern**: Type C (business analysis 10-30 minutes)
**Description**: Multi-expert business analysis with break reminders
**Subtasks**:
1. Copy type-c-pattern.md as foundation
2. Add chunked session for 10-30 min analysis
3. Keep existing business-panel logic (9 expert personas, 3 modes)
4. Test: Discussion mode (10-15 min)
5. Test: Debate mode (15-20 min)

**Acceptance**:
- dx:business-panel functional
- Type C pattern working (breaks every 25min)
- sc:business-panel alias redirects

---

**E4-T7: Migrate sc:spec-panel → dx:spec-panel** [1 SP]
**Estimate**: 1 hour
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/spec-panel.md`
**Source**: `/Users/hue/.claude/commands/sc/spec-panel.md`
**Pattern**: Type C (spec review 10-20 minutes)
**Description**: Multi-expert specification review
**Subtasks**:
1. Copy type-c-pattern.md as foundation
2. Keep existing spec-panel logic
3. Test: Specification review

**Acceptance**:
- dx:spec-panel functional
- sc:spec-panel alias redirects

---

**E4-T8: Migrate sc:spawn → dx:spawn** [1 SP]
**Estimate**: 1 hour
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/spawn.md`
**Source**: `/Users/hue/.claude/commands/sc/spawn.md`
**Pattern**: Type A (meta-orchestration needs assessment)
**Description**: Task breakdown and delegation
**Subtasks**:
1. Copy type-a-pattern.md as foundation
2. Add complexity assessment in Phase 1
3. Keep existing spawn logic (task breakdown, agent delegation)
4. Merge with sc:task if needed
5. Test: Complex task breakdown

**Acceptance**:
- dx:spawn functional
- Complexity assessment working
- sc:spawn alias redirects

---

**E4-T9: Migrate sc:estimate → dx:estimate** [1 SP]
**Estimate**: 0.5 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/commands/dx/estimate.md`
**Source**: `/Users/hue/.claude/commands/sc/estimate.md`
**Pattern**: Type B (estimation should be quick)
**Description**: Time estimation for tasks
**Subtasks**:
1. Copy type-b-pattern.md as foundation
2. Keep existing estimate logic
3. Test: Task estimation

**Acceptance**:
- dx:estimate functional
- Quick response (< 5s)
- sc:estimate alias redirects

---

#### Day 5: Validation and Gate (2 tasks, 5 hours)

**E4-T10: Comprehensive Testing of Quality Commands** [3 SP]
**Estimate**: 3 hours
**Test Matrix**:

| Command | Functional | ADHD | Integration | Performance |
|---------|-----------|------|-------------|-------------|
| dx:document | ✓ All 5 types | ✓ Session | ✓ Templates | < 30s setup |
| dx:test | ✓ Multiple frameworks | ✓ Session | ✓ Coverage | < 30s setup |
| dx:cleanup | ✓ Dead code, lint | ✓ Session, progress | ✓ Formatting | < 30s setup |
| dx:business-panel | ✓ 3 modes | ✓ Chunks, breaks | ✓ 9 experts | Handles 30min |
| dx:spec-panel | ✓ Review | ✓ Chunks | ✓ Experts | Handles 20min |
| dx:spawn | ✓ Breakdown | ✓ Session | ✓ Delegation | < 30s setup |
| dx:estimate | ✓ Estimation | ✓ Quick | N/A | < 5s |

**Acceptance**:
- All tests pass
- No regressions

---

**E4-T11: Gate Decision for Epic 4** [1 SP]
**Estimate**: 1 hour
**Criteria**:
- Are quality/doc commands production-ready? (Yes/No)
- Is dx:document consolidation successful? (Yes/No)
- Are specialized tools working? (Yes/No)

**Decision**:
- All Yes → Proceed to Epic 5
- Any No → Fix and re-test

**Acceptance**:
- Decision documented
- If proceed: Epic 5 greenlit (final epic!)

---

### Epic 4 Success Metrics

- ✅ dx:document consolidates 9 commands successfully
- ✅ Quality commands (test, cleanup) functional
- ✅ Specialized tools migrated
- ✅ All tests passing
- ✅ Gate approval to proceed to Epic 5

---

## Epic 5: Cleanup & Migration

**Goal**: Remove deprecated commands, update documentation, final validation
**Duration**: Week 5 (5 working days)
**Story Points**: 8
**Owner**: Primary developer
**Dependencies**: Epic 4 complete (all new commands validated)

### User Stories

**US-5.1**: As a user, I want deprecated commands removed after grace period so I'm not confused by duplicate options
**Acceptance Criteria**:
- 30-day deprecation warning period complete
- All deprecated sc: commands removed
- Aliases remain functional for another 30 days
- Users communicated about changes

**US-5.2**: As a developer, I want comprehensive documentation updates so the new command structure is clear
**Acceptance Criteria**:
- CLAUDE.md updated with new dx: command reference
- Migration guide created
- Command comparison table (sc: → dx: mapping)
- Deprecation timeline documented

**US-5.3**: As a stakeholder, I want final validation confirming all 29 dx: commands work before rollout
**Acceptance Criteria**:
- All 29 commands tested
- Performance benchmarks met
- ADHD features validated across all
- Production rollout approved

### Task Breakdown

#### Day 1: Remove Deprecated Commands (2 tasks, 5 hours)

**E5-T1: Remove Deprecated sc: Command Files** [3 SP]
**Estimate**: 3 hours
**Description**: Delete deprecated command files after 30-day warning period
**Files to Remove** (17 total):
1. `/Users/hue/.claude/commands/sc/analyze.md` → dx:analyze
2. `/Users/hue/.claude/commands/sc/design.md` → dx:design
3. `/Users/hue/.claude/commands/sc/troubleshoot.md` → dx:troubleshoot
4. `/Users/hue/.claude/commands/sc/research.md` → dx:research
5. `/Users/hue/.claude/commands/sc/reflect.md` → dx:reflect
6. `/Users/hue/.claude/commands/sc/implement.md` → dx:implement
7. `/Users/hue/.claude/commands/sc/load.md` → dx:load
8. `/Users/hue/.claude/commands/sc/save.md` → dx:save
9. `/Users/hue/.claude/commands/sc/git.md` → dx:git
10. `/Users/hue/.claude/commands/sc/improve.md` → dx:improve
11. `/Users/hue/.claude/commands/sc/test.md` → dx:test
12. `/Users/hue/.claude/commands/sc/cleanup.md` → dx:cleanup
13. `/Users/hue/.claude/commands/sc/business-panel.md` → dx:business-panel
14. `/Users/hue/.claude/commands/sc/spec-panel.md` → dx:spec-panel
15. `/Users/hue/.claude/commands/sc/spawn.md` → dx:spawn
16. `/Users/hue/.claude/commands/sc/estimate.md` → dx:estimate
17. `/Users/hue/.claude/commands/sc/explain.md` → dx:explain (from Epic 1)

**Also Remove** (deprecated doc commands):
- `adr-new.md`, `rfc-new.md`, `rfc-lint.md`, `rfc-promote.md`
- `doc-new.md`, `doc-pull.md`, `doc-ensure-frontmatter.md`, `docs-helper.md`
- `dangerous.md`, `safe.md` → removed (use --unsafe flag instead)
- `security-review.md` → dx:analyze --focus security
- `sc:select-tool.md` → automatic (no command needed)
- `sc:index.md` → automatic on load (no command needed)

**Subtasks**:
1. Backup all files to `.claude/deprecated-commands/` (archive for reference)
2. Delete 17 sc: command files
3. Delete 8 doc command files
4. Delete 4 obsolete command files
5. Update command index files

**Acceptance**:
- 29 files archived
- 29 files deleted
- Command indexes updated

---

**E5-T2: Update sc-aliases.md for Extended Grace Period** [2 SP]
**Estimate**: 2 hours
**Description**: Keep aliases functional for 60 more days (total 90-day migration)
**Subtasks**:
1. Update deprecation warnings: "Command removed. Use /dx:[command] instead."
2. Add timeline: "Aliases will be removed on [DATE + 60 days]"
3. Add help message: "See migration guide: .claude/COMMAND_MIGRATION_GUIDE.md"
4. Test all aliases still work
5. Verify warnings display correctly

**Acceptance**:
- Aliases functional for 60 more days
- Warnings updated
- Help message added

---

#### Day 2-3: Documentation Updates (3 tasks, 10 hours)

**E5-T3: Update Global CLAUDE.md** [3 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/.claude/CLAUDE.md`
**Description**: Update global config with new dx: command reference
**Subtasks**:
1. Remove sc: command references
2. Add comprehensive dx: command list (29 commands)
3. Group by category:
   - Session Management: load, save, session/*
   - Implementation: implement, improve, cleanup
   - Analysis: analyze, design, troubleshoot, review, plan
   - Research: research, reflect
   - Quality: test
   - Documentation: document
   - Specialized: business-panel, spec-panel, spawn, estimate
   - Utilities: explain, help, stats, assess, git
4. Add command type indicators (Type A/B/C)
5. Add performance expectations (< 2s, < 5s, < 30s setup)
6. Document ADHD features (energy matching, breaks, visual formatting)

**Acceptance**:
- CLAUDE.md updated comprehensively
- All 29 commands documented
- Categories clear
- ADHD features highlighted

---

**E5-T4: Create Migration Guide** [3 SP]
**Estimate**: 4 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/COMMAND_MIGRATION_GUIDE.md`
**Description**: User-facing migration guide
**Sections**:
1. **Overview**: Why consolidation, benefits (37% reduction, 100% ADHD coverage)
2. **What Changed**: Summary of consolidation strategy
3. **Command Mapping Table**: sc: → dx: mapping for all commands
4. **Breaking Changes**: None (aliases preserve compatibility)
5. **New Features**: ADHD session management, energy matching, break reminders
6. **Timeline**:
   - Week 1-4: New commands available, sc: still works
   - Week 5: sc: files removed, aliases remain
   - Day 90: Aliases removed, dx: only
7. **How to Migrate**: Step-by-step for users
8. **FAQ**: Common questions and concerns
9. **Support**: Where to get help

**Acceptance**:
- Migration guide complete and clear
- Users can follow guide to migrate
- FAQ addresses concerns

---

**E5-T5: Create Command Comparison Table** [2 SP]
**Estimate**: 3 hours
**File**: `/Users/hue/code/dopemux-mvp/.claude/COMMAND_COMPARISON.md`
**Description**: Visual comparison of old vs new
**Format**:

| Old Command | New Command | Type | ADHD Features | Key Changes |
|-------------|-------------|------|---------------|-------------|
| sc:implement | dx:implement | A | Energy matching, 25-min sessions | Merges sc: + dx: features |
| sc:load | dx:load | B | Quick restore | Merges ConPort + Serena |
| ... | ... | ... | ... | ... |

**Also Include**:
- Deprecated commands and replacements
- New commands (dx:review, dx:plan)
- Performance comparisons

**Acceptance**:
- Comparison table complete
- All 46 original commands mapped
- Visual clarity high

---

#### Day 4: Final Validation (2 tasks, 5 hours)

**E5-T6: Comprehensive Final Testing** [4 SP]
**Estimate**: 4 hours
**Description**: Test all 29 dx: commands one final time
**Test Categories**:
1. **Functional**: Each command works correctly
2. **Performance**: Targets met (Type A < 30s, Type B < 5s, Type C handles long)
3. **ADHD**: Energy matching, sessions, breaks all functional
4. **Integration**: ConPort, Serena, Zen, PAL apilookup, GPT-Researcher, Magic, Playwright
5. **Error Handling**: Graceful degradation when MCPs unavailable

**Test Matrix** (29 commands × 5 dimensions = 145 test points):
- Session Management (6): load, save, session:start, session:end, session:break, session:resume, session:status
- Implementation (3): implement, improve, cleanup
- Analysis (5): analyze, design, troubleshoot, review, plan
- Research (2): research, reflect
- Quality (1): test
- Documentation (1): document (5 types)
- Specialized (4): business-panel, spec-panel, spawn, estimate
- Utilities (7): explain, help, stats, assess, git, build

**Deliverable**: Final test report with pass/fail for all 145 test points

**Acceptance**:
- ≥ 95% test points pass (138/145)
- Critical commands 100% pass (implement, load, save)
- Any failures documented with mitigation

---

**E5-T7: Performance Benchmarking** [2 SP]
**Estimate**: 1 hour
**Description**: Measure actual performance vs targets
**Benchmarks**:
- Type A commands: Setup < 30s (12 commands)
- Type B commands: Total < 5s (10 commands)
- Type C commands: Handle 30-60 min sessions (3 commands)

**Deliverable**: Performance report with actual measurements

**Acceptance**:
- All performance targets met or documented why not
- Optimization plan for any misses

---

#### Day 5: Production Rollout (2 tasks, 4 hours)

**E5-T8: Production Rollout Preparation** [2 SP]
**Estimate**: 3 hours
**Description**: Final pre-rollout checklist
**Checklist**:
1. ✅ All 29 commands tested and passing
2. ✅ Documentation complete (CLAUDE.md, migration guide, comparison table)
3. ✅ Aliases functional for grace period
4. ✅ Deprecated files archived
5. ✅ Performance benchmarks met
6. ✅ User communication prepared
7. ✅ Rollback plan documented
8. ✅ Support resources ready

**Acceptance**:
- All checklist items complete
- Rollout ready

---

**E5-T9: Final Gate Decision and Rollout Approval** [1 SP]
**Estimate**: 1 hour
**Description**: Executive decision to rollout
**Criteria**:
- Are all 29 commands production-ready? (Yes/No)
- Is documentation complete? (Yes/No)
- Are performance targets met? (Yes/No)
- Is user migration plan clear? (Yes/No)
- Is rollback plan ready? (Yes/No)

**Decision**:
- All Yes → APPROVE PRODUCTION ROLLOUT
- Any No → Address issues before rollout

**Deliverable**: Rollout approval document

**Acceptance**:
- Decision documented
- If approved: Rollout proceeds
- If not: Issues addressed

---

### Epic 5 Success Metrics

- ✅ All deprecated commands removed (29 files)
- ✅ Aliases functional for grace period
- ✅ Documentation complete and comprehensive
- ✅ All 29 commands tested and passing
- ✅ Performance benchmarks met
- ✅ Production rollout approved

---

## Overall Project Summary

### Quantitative Goals

| Metric | Target | Validation |
|--------|--------|------------|
| Command reduction | 46 → 29 (37%) | ✅ Epic 5 final validation |
| ADHD optimization | 100% coverage | ✅ All commands use Type A/B/C patterns |
| Performance (Type A) | Setup < 30s | ✅ E5-T7 benchmarking |
| Performance (Type B) | Total < 5s | ✅ E5-T7 benchmarking |
| Performance (Type C) | Handle 30-60min | ✅ E5-T7 benchmarking |
| Test coverage | ≥ 95% (138/145 points) | ✅ E5-T6 comprehensive testing |

### Qualitative Goals

- ✅ Consistent ADHD-friendly UX across all commands
- ✅ Better tool coordination (Zen + ConPort + Serena everywhere)
- ✅ Reduced cognitive load (less choice paralysis)
- ✅ Easier command discovery (single dx: namespace)

### Risk Management Summary

**Highest Risks Managed**:
1. ✅ dx:implement complexity → Extensive testing (6 hours, E2-T2)
2. ✅ Data loss in load/save → Round-trip testing mandatory (E2-T3, E2-T4)
3. ✅ User adoption resistance → Migration guide + 90-day grace period (E5-T4)
4. ✅ Pattern template rigidity → 3 pilot validation before scaling (Epic 1)

### Timeline

- **Week 1**: Foundation ✓
- **Week 2**: Session Commands ✓
- **Week 3**: Analysis Tools ✓
- **Week 4**: Quality & Documentation ✓
- **Week 5**: Cleanup & Rollout ✓

**Total**: 5 weeks (25 working days)

---

## Appendix: Epic Dependencies Diagram

```
Epic 1 (Foundation)
    ↓
Epic 2 (Session Commands) → Validates patterns work at scale
    ↓
Epic 3 (Analysis Tools) → Adds Zen MCP integration
    ↓
Epic 4 (Quality & Docs) → Consolidates documentation, adds quality tools
    ↓
Epic 5 (Cleanup) → Final validation and rollout
```

**Critical Path**: Epic 1 → Epic 2 (dx:implement) → Epic 5 (final validation)

---

**Status**: Epic breakdown complete with 49 tasks across 5 epics
**Next Step**: User approval, then begin Epic 1 implementation
**Decision Point**: Review and approve strategy before proceeding
