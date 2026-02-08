# TODO - Dopemux MVP

**Last Updated**: 2026-02-02  
**Session Context**: ADHD Features Implementation Sprint

This document consolidates all planned features, fixes, recommendations, and technical debt from `.copilot` session state.

---

## 🎯 Current Status

**Completed**:
- ✅ **15 ADHD features** implemented (Phase 1-3 + Quick Wins + P1)
- ✅ **Documentation** comprehensive (user guide, API reference, P2 design)
- ✅ **Service standardization** complete (6 services)
- ✅ **Critical bugs** fixed (datetime, Zen→Pal, duplicates)

**In Progress**:
- 🔄 **Task Decomposition Integration** - Phase 1 code complete, needs wiring

**Next Priority**:
- 🎯 **P2 Features** - 7 features designed, ready to implement
- 🎯 **Testing & Integration** - End-to-end testing for all features

---

## 📋 Immediate TODOs (P0 - Critical)

### ✅ Task Decomposition - Phase 1 Wiring (COMPLETE)

**Status**: ✅ **WIRED AND TESTED** (2026-02-02)

- [x] Wire actual instances in `task-orchestrator/app.py` `/api/decompose` endpoint
  - [x] Created singleton factories in `core.py`
  - [x] Get `task_coordinator`, `pal_client`, `conport_adapter` from factories
  - [x] Replaced placeholder response with actual `handle_decomposition_request()` call
  - [x] Added error handling for missing dependencies
- [x] Added task storage and retrieval methods to TaskCoordinator
  - [x] `get_task(task_id)` - retrieve from memory or ConPort
  - [x] `store_task(task)` - store with background sync
  - [x] `schedule_subtasks(subtasks, adhd_context)` - ADHD-aware scheduling
- [x] Fixed imports: migrated from deprecated `enhanced_orchestrator` to `task_orchestrator.models`
- [x] Fixed field name migration: `estimated_duration` → `estimated_minutes`
- [x] Fixed enum migration: `AgentType.ZEN` → `AgentType.PAL`
- [x] All wiring tests passing (4/4)

**Next Steps** (Ready for integration testing):
- [ ] Start Task Orchestrator service: `uvicorn task_orchestrator.app:app --port 3014`
- [ ] Test end-to-end flow: ADHD Engine → Task Orchestrator → Pal → ConPort
- [ ] Verify ConPort persistence (parent BLOCKED, subtasks TODO)
- [ ] Verify Leantime child ticket creation (if configured)
- [ ] Test auto-detection triggers (5 patterns)

**Files Changed**: 8 files, ~140 lines
**Documentation**: `services/task-orchestrator/DECOMPOSITION_WIRING.md`

**Success Criteria**:
- ✅ All singleton instances initialize correctly
- ✅ `/api/decompose` endpoint accepts requests
- ✅ TaskCoordinator can store/retrieve tasks
- ⏳ User creates task in Leantime (>2h estimate) - *needs integration test*
- ⏳ ADHD Engine auto-detects complexity - *needs integration test*
- ⏳ User consents to decomposition - *needs integration test*
- ⏳ Task Orchestrator calls Pal planner - *needs Pal MCP running*
- ⏳ 6 subtasks created in ConPort (status: TODO) - *needs integration test*
- ⏳ Leantime shows child tickets - *needs Leantime configured*
- ⏳ User can start first subtask - *needs integration test*

---

## 🚀 P1 Priority Features (High Impact)

### Already Implemented ✅

1. ✅ **Task Decomposition Assistant** (21.5KB)
2. ✅ **Medication Effectiveness Tracker** (21.8KB)
3. ✅ **Social Battery Monitor** (22.9KB)
4. ✅ **Working Memory Support** (25.2KB)

### From Further Features Analysis (24-32h)

5. [ ] **Transition Coach** (4-6h) - *NOW P2 DESIGNED*
   - Context switch management
   - Pre/post transition protocols
   - Transition quality metrics
   - See: `docs/04-explanation/adhd-features-p2-design.md`

6. [ ] **Sensory Overload Detection** (5-7h) - *NOW P2 DESIGNED*
   - Visual/auditory/notification overload detection
   - Automatic circuit breaker (3 levels)
   - Environment state save/restore
   - See: `docs/04-explanation/adhd-features-p2-design.md`

**P1 Total Remaining**: 9-13 hours (if implementing non-P2-designed features)

---

## 📊 P2 Priority Features (Medium Impact)

### Fully Designed & Ready to Implement (39-51h total)

All 7 features have complete design documents in `docs/04-explanation/adhd-features-p2-design.md`:

1. [ ] **Transition Coach** (4-6h)
   - Structured context switching
   - Pre/post transition support
   - Quality tracking & optimization

2. [ ] **Sensory Overload Detection** (5-7h)
   - Multi-dimensional overload detection
   - 3-level circuit breaker
   - Sensory profile calibration

3. [ ] **Habit Streak Tracker** (4-5h)
   - ADHD-friendly (NO daily streaks!)
   - Grace periods & flexible goals
   - Celebration without pressure

4. [ ] **Sleep Pattern Analysis** (4-6h)
   - Sleep-energy correlation
   - Circadian rhythm detection
   - Medication-sleep interaction tracking

5. [ ] **Code Review Accommodations** (8-10h)
   - PR complexity assessment
   - Review chunking (20min sessions)
   - Focus aids (line-by-line, checklists)
   - Energy-aware scheduling

6. [ ] **Meeting Accommodations** (6-8h)
   - Pre-meeting support (30min + 5min alerts)
   - During-meeting capture (action items, thoughts)
   - Post-meeting protocol (context restoration)
   - Meeting analytics

7. [ ] **Emergency Reset Protocol** (8-9h)
   - Auto-detect emergency situations
   - One-button reset (save all, close all, DND)
   - 4-phase recovery (immediate, assessment, recovery, return)
   - Post-emergency analysis

**Implementation Order Recommendation**:
- **Phase 1** (18-23h): Transition Coach, Meeting Accommodations, Emergency Reset
- **Phase 2** (17-23h): Sensory Overload, Sleep Analysis, Code Review
- **Phase 3** (4-5h): Habit Streak Tracker

### From Further Features (Not Yet Designed)

8. [ ] **Task Difficulty Prediction** (6-8h)
   - NLP task analyzer
   - Similar task matcher using embeddings
   - Historical time estimate learning

9. [ ] **Dynamic Pomodoro Adaptation** (4-6h)
   - Learn optimal work duration per user
   - Adaptive break timing
   - Break quality tracking

10. [ ] **Calendar Integration** (6-8h)
    - Google Calendar / Outlook sync
    - Meeting preparation assistant
    - Energy-aware scheduling

11. [ ] **Slack/Discord Integration** (5-6h)
    - Focus mode sync (auto-DND)
    - Notification filtering
    - Energy status sharing (optional)

12. [ ] **ADHD-Friendly Achievement System** (4-6h)
    - Micro-achievements (no streaks!)
    - Visual progress
    - Rewards without pressure

**P2 Total**: 60-75 hours (including designed + undesigned)

---

## 🔮 P3 Priority Features (Nice to Have)

### Research & Advanced Features (22-27h)

1. [ ] **Git Activity Analysis** (4-5h)
   - Commit pattern insights
   - Focus session correlation
   - Quality metrics by cognitive state

2. [ ] **Accountability Buddy System** (10-12h)
   - Virtual co-working (body doubling)
   - Gentle accountability
   - Progress sharing (optional)

3. [ ] **A/B Testing Framework** (8-10h)
   - Experiment manager for accommodations
   - Objective metrics tracking
   - Personalized recommendations

**P3 Total**: 22-27 hours

---

## 🧪 Testing & Quality Assurance

### Unit Tests (Current State)

**Already Have Tests**:
- ✅ `adhd_engine/` - Full test coverage
- ✅ `energy-trends/tests/` - 3 test cases
- ✅ `context-switch-tracker/tests/` - 3 test cases
- ✅ `adhd-dashboard/tests/` - 4 test cases
- ✅ `adhd-notifier/tests/` - 2 test cases
- ✅ `break-suggester/tests/` - 4 test cases

**Need Tests** (P1 Features):
- [ ] `adhd_engine/task_decomposition_assistant.py`
- [ ] `adhd_engine/medication_effectiveness_tracker.py`
- [ ] `adhd_engine/social_battery_monitor.py`
- [ ] `adhd_engine/working_memory_support.py`
- [ ] `adhd_engine/decomposition_coordinator.py`
- [ ] `task-orchestrator/task_decomposition_endpoint.py`

**Effort**: 6-8 hours for P1 feature tests

### Integration Tests

- [ ] **Task Decomposition End-to-End**
  - [ ] Leantime task creation → auto-detection
  - [ ] User consent flow
  - [ ] Pal planner integration
  - [ ] ConPort persistence
  - [ ] Leantime sync

- [ ] **Social Battery + Calendar**
  - [ ] Calendar event import
  - [ ] Battery drain prediction
  - [ ] Recovery recommendations

- [ ] **Working Memory + Context Preserver**
  - [ ] Thought capture → ConPort
  - [ ] Breadcrumb → context restoration
  - [ ] Interruption detection

**Effort**: 8-10 hours

### Performance & Load Testing

- [ ] Energy predictor with 1000+ samples
- [ ] Correlation engine with multi-service data
- [ ] Social battery calendar prediction (100+ events)
- [ ] Working memory with 1000+ thoughts

**Effort**: 4-6 hours

---

## 📚 Documentation TODOs

### User Documentation

- [ ] Update README.md
  - [ ] Change feature count: 13 → 15
  - [ ] Add P1 features to main list
  - [ ] Link to new user guide sections

- [ ] Update `docs/00-MASTER-INDEX.md`
  - [ ] Add P1 features to ADHD section
  - [ ] Link to P2 design document
  - [ ] Update feature counts

- [ ] Create CLI command reference
  - [ ] `dopemux adhd task-decompose <task-id>`
  - [ ] `dopemux adhd medication log <dose>`
  - [ ] `dopemux adhd social-battery status`
  - [ ] `dopemux adhd memory capture "<thought>"`

- [ ] Add troubleshooting guide
  - [ ] Common issues with ADHD features
  - [ ] ConPort connection problems
  - [ ] DopeconBridge event debugging

**Effort**: 2-3 hours

### API Documentation

- [ ] Generate OpenAPI/Swagger spec
  - [ ] All 15 features documented
  - [ ] Request/response schemas
  - [ ] Error codes

- [ ] Create Postman collection
  - [ ] Example requests for all endpoints
  - [ ] Environment variables setup
  - [ ] Pre-request scripts

- [ ] Add authentication section (when implemented)
- [ ] Document rate limiting (when implemented)

**Effort**: 4-5 hours

### Developer Documentation

- [ ] Architecture decision records (ADRs)
  - [ ] Why task decomposition uses event-driven architecture
  - [ ] Social battery drain calculation rationale
  - [ ] Working memory < 2 second capture design

- [ ] Component interaction diagrams
  - [ ] Full ADHD Engine architecture
  - [ ] Task decomposition flow
  - [ ] DopeconBridge event routing

**Effort**: 3-4 hours

---

## 🔧 Technical Debt & Refactoring

### Code Quality

- [ ] **Add type hints** to all P1 features
  - [ ] task_decomposition_assistant.py
  - [ ] medication_effectiveness_tracker.py
  - [ ] social_battery_monitor.py
  - [ ] working_memory_support.py

- [ ] **Extract common patterns**
  - [ ] ConPort client wrapper (used in 15+ places)
  - [ ] DopeconBridge event publishing
  - [ ] ADHD-friendly error messages

- [ ] **Reduce duplication**
  - [ ] Multiple services have similar health check logic
  - [ ] Repeated Redis connection patterns
  - [ ] Common FastAPI startup/shutdown

**Effort**: 6-8 hours

### Dependencies

- [ ] **Add missing dependencies to requirements.txt**
  - [ ] `sklearn` (energy predictor)
  - [ ] `spacy` or `transformers` (NLP for task analysis)
  - [ ] `google-calendar-api` (calendar integration)
  - [ ] `slack-sdk` (Slack integration)

- [ ] **Pin dependency versions**
  - [ ] All production services
  - [ ] Lock file generation

- [ ] **Audit security vulnerabilities**
  - [ ] `pip-audit` on all requirements
  - [ ] Update vulnerable packages

**Effort**: 2-3 hours

### Infrastructure

- [ ] **Add health check endpoints** to all services
  - [ ] Standardize response format
  - [ ] Include dependency checks (Redis, ConPort)

- [ ] **Prometheus metrics**
  - [ ] Feature usage counters
  - [ ] API endpoint latency
  - [ ] Error rates

- [ ] **Logging standardization**
  - [ ] Structured logging (JSON format)
  - [ ] Log levels consistent
  - [ ] Trace IDs for distributed tracing

**Effort**: 8-10 hours

---

## 🐛 Known Issues & Bugs

### Critical (P0)

*None currently*

### High Priority (P1)

- [ ] **Voice assistant macOS-only**
  - Linux/Windows need TTS alternatives
  - Solution: `pyttsx3` cross-platform TTS

- [ ] **Mobile push requires API keys**
  - Ntfy is free but requires topic setup
  - Document setup process

- [ ] **Social battery calendar integration not implemented**
  - Predict functionality exists but no calendar API
  - Need Google Calendar / Outlook integration

**Effort**: 4-6 hours

### Medium Priority (P2)

- [ ] **Energy predictor needs more features**
  - Currently 9 features, could add 5-10 more
  - Weather, time of month, sleep quality

- [ ] **Context preserver Git integration partial**
  - Only captures branch name
  - Could capture uncommitted changes, stash state

- [ ] **Correlation engine cache invalidation**
  - Fixed 5-minute TTL, should be smarter
  - Invalidate on new data arrival

**Effort**: 6-8 hours

### Low Priority (P3)

- [ ] **Procrastination detector gamification incomplete**
  - Badges defined but not awarded
  - Need badge unlock logic

- [ ] **Weekly report email delivery**
  - Currently only API, no email
  - Add email/Slack delivery options

**Effort**: 3-4 hours

---

## 🏗️ Phase 4: Core Services Exploration

### Services Audit Checklist

- [ ] **ConPort** (`services/conport-graph-memory/`, ~15 files)
  - [ ] Code quality and structure
  - [ ] Test coverage
  - [ ] Error handling
  - [ ] Performance bottlenecks
  - [ ] Security considerations
  - [ ] Documentation completeness
  - [ ] Integration points
  - [ ] Improvement opportunities

- [ ] **Task-Orchestrator** (`services/task-orchestrator/`, ~20 files)
  - [ ] Code quality and structure
  - [ ] Test coverage (37 tools)
  - [ ] Error handling
  - [ ] Performance bottlenecks
  - [ ] Security considerations
  - [ ] Documentation completeness
  - [ ] Integration points
  - [ ] Improvement opportunities

- [ ] **Serena-v2** (`docker/mcp-servers/serena-v2/`, ~10 files)
  - [ ] LSP integration quality
  - [ ] Complexity scoring accuracy
  - [ ] Test coverage
  - [ ] Error handling
  - [ ] Performance bottlenecks
  - [ ] Documentation completeness

- [ ] **dope-context** (`services/dope-context/`, ~10 files)
  - [ ] Vector search performance
  - [ ] Indexing strategy
  - [ ] Test coverage
  - [ ] Error handling
  - [ ] Documentation completeness

- [ ] **DopeconBridge** (`services/dopecon-bridge/`, ~8 files)
  - [ ] Event routing reliability
  - [ ] Authority boundary enforcement
  - [ ] Test coverage
  - [ ] Error handling
  - [ ] Performance at scale

- [ ] **Pal MCP** (`docker/mcp-servers/pal/`, ~5 files)
  - [ ] 18 tools quality review
  - [ ] Multi-model integration
  - [ ] Test coverage
  - [ ] Error handling
  - [ ] Documentation completeness

**Effort**: 4-6 hours per service = 24-36 hours total

---

## 🎨 UI/UX Enhancements

### Terminal UI (Textual/Rich)

- [ ] **ADHD Dashboard TUI**
  - [ ] Real-time energy/attention visualization
  - [ ] Social battery meter
  - [ ] Active thoughts list
  - [ ] Quick action buttons

- [ ] **Task Decomposition UI**
  - [ ] Interactive consent dialog
  - [ ] Subtask progress visualization
  - [ ] Energy-aware task ordering

- [ ] **Working Memory UI**
  - [ ] Quick capture hotkey
  - [ ] Thought list with filtering
  - [ ] Breadcrumb timeline

**Effort**: 12-15 hours

### Web Dashboard (Optional)

- [ ] React/Vue frontend for ADHD Dashboard
- [ ] Real-time updates via WebSocket
- [ ] Mobile-responsive design

**Effort**: 20-30 hours

---

## 🔌 Integration Enhancements

### Calendar Integration (P2 Feature)

- [ ] Google Calendar OAuth setup
- [ ] Outlook Calendar integration
- [ ] Event sync (meetings → social battery)
- [ ] Calendar-based scheduling recommendations

**Effort**: 6-8 hours

### Slack/Discord Integration (P2 Feature)

- [ ] Slack app setup
- [ ] Discord bot setup
- [ ] Status sync (focus mode → DND)
- [ ] Notification batching
- [ ] Weekly report delivery

**Effort**: 5-6 hours

### GitHub Integration

- [ ] PR review accommodations
- [ ] Commit pattern analysis
- [ ] Issue complexity scoring
- [ ] Auto-decompose GitHub issues

**Effort**: 8-10 hours

---

## 📈 Analytics & Metrics

### Feature Usage Tracking

- [ ] Implement event tracking
  - [ ] Feature enable/disable
  - [ ] API endpoint usage
  - [ ] User interactions

- [ ] Analytics dashboard
  - [ ] Most-used features
  - [ ] Feature adoption rates
  - [ ] User retention

**Effort**: 6-8 hours

### ADHD Impact Metrics

- [ ] **Effectiveness Metrics**
  - [ ] Task completion rate (decomposed vs. not)
  - [ ] Context restoration time
  - [ ] Social battery prediction accuracy
  - [ ] Medication adherence improvement

- [ ] **User Satisfaction**
  - [ ] Feature usefulness ratings
  - [ ] ADHD burden reduction (self-reported)
  - [ ] Would recommend metric

**Effort**: 4-5 hours

---

## 🚢 Deployment & Operations

### CI/CD

- [ ] GitHub Actions workflows
  - [ ] Run tests on PR
  - [ ] Lint + type check
  - [ ] Build Docker images
  - [ ] Deploy to staging

- [ ] Pre-commit hooks
  - [ ] Black formatting
  - [ ] isort imports
  - [ ] flake8 linting
  - [ ] pytest quick tests

**Effort**: 4-6 hours

### Monitoring

- [ ] Prometheus metrics export
- [ ] Grafana dashboards
  - [ ] Service health
  - [ ] Feature usage
  - [ ] Error rates

- [ ] Alerting
  - [ ] Service down
  - [ ] High error rate
  - [ ] ConPort connection failures

**Effort**: 6-8 hours

### Documentation

- [ ] Deployment guide
- [ ] Scaling recommendations
- [ ] Backup/restore procedures
- [ ] Disaster recovery plan

**Effort**: 4-5 hours

---

## 🎯 Success Criteria (Validation)

### Phase 1-3 Complete ✅

- ✅ No duplicate service directories
- ✅ All imports work without errors
- ✅ No "Zen" references in active code
- ✅ All 6 services have standard structure
- ⚠️ Test coverage ≥ 80% for all services (needs P1 feature tests)
- ✅ All 15 features implemented
- ⚠️ 6 core service audits incomplete (Phase 4)

### Task Decomposition Integration

- [ ] Auto-detection works (5 trigger patterns)
- [ ] User consent flow functional
- [ ] Pal planner generates quality breakdowns
- [ ] ConPort persistence verified
- [ ] Leantime sync working
- [ ] >80% user acceptance of decomposition suggestions

### P2 Features (When Implemented)

- [ ] Transition time reduced by 50% (15min → 7min avg)
- [ ] Meeting stress reduced by 30% (user-reported)
- [ ] Emergency recoveries 100% successful (no data loss)
- [ ] Code review completion +40% (vs. without accommodations)

---

## 📊 Effort Summary

| Category | Effort | Priority |
|----------|--------|----------|
| **Task Decomposition Wiring** | 2-3h | P0 |
| **P1 Features (remaining)** | 9-13h | P1 |
| **P2 Features (designed)** | 39-51h | P2 |
| **P2 Features (undesigned)** | 25-34h | P2 |
| **P3 Features** | 22-27h | P3 |
| **Testing** | 18-24h | P1 |
| **Documentation** | 9-12h | P1 |
| **Technical Debt** | 16-21h | P2 |
| **Core Services Audit** | 24-36h | P2 |
| **UI/UX** | 12-15h | P3 |
| **Integrations** | 19-24h | P2 |
| **Analytics** | 10-13h | P2 |
| **Deployment** | 14-19h | P2 |
| **TOTAL** | **219-292h** | |

---

## 🎯 Recommended Implementation Sequence

### Sprint 1: Complete Current Work (2-3h)
1. Wire task decomposition integration
2. End-to-end testing
3. Fix any critical bugs

### Sprint 2: Testing & Documentation (27-36h)
1. Add P1 feature tests (6-8h)
2. Integration tests (8-10h)
3. Update documentation (9-12h)
4. Performance testing (4-6h)

### Sprint 3: P2 Phase 1 - Safety Features (18-23h)
1. Transition Coach (4-6h)
2. Meeting Accommodations (6-8h)
3. Emergency Reset Protocol (8-9h)

### Sprint 4: P2 Phase 2 - Protection Features (17-23h)
1. Sensory Overload Detection (5-7h)
2. Sleep Pattern Analysis (4-6h)
3. Code Review Accommodations (8-10h)

### Sprint 5: P2 Phase 3 - Quality of Life (25-35h)
1. Habit Streak Tracker (4-5h)
2. Calendar Integration (6-8h)
3. Slack/Discord Integration (5-6h)
4. Task Difficulty Prediction (6-8h)
5. Dynamic Pomodoro (4-6h)

### Sprint 6: Operations & Scale (30-40h)
1. Technical debt (16-21h)
2. Deployment automation (14-19h)

---

## 📝 Notes

- **User Control**: All features follow consent-first, transparent, overridable design
- **ADHD Lens**: Every feature addresses specific ADHD challenges
- **Integration**: Features work together synergistically
- **Scalability**: Architecture supports future growth
- **Testing**: Comprehensive test coverage required before production

---

**Document Source**: Consolidated from `.copilot/session-state/` files:
- `plan.md` - Original implementation plan
- `further_features.md` - 20 additional features analysis
- `phase1_complete.md` - Task decomposition Phase 1
- `task_decomposition_architecture.md` - Full architecture design
- `session_complete_summary.md` - Implementation summary
- `documentation_summary.md` - Documentation status
- Checkpoint files (001-003)

**Last Review**: 2026-02-02  
**Status**: Active - Track progress with checkboxes  
**Maintainer**: Update after each feature implementation
