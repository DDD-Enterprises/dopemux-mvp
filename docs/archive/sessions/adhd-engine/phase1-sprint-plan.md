---
id: phase1-sprint-plan
title: Phase1 Sprint Plan
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Phase 1 Sprint Plan - macOS + Slack MVP

**Duration**: 4 weeks
**Goal**: Validate core interruption prevention concept with ADHD beta testers
**Team**: 3 engineers

---

## Week 1: Core Infrastructure ✅ (Setup Complete)

### Day 1-2: Project Setup
- [x] Create service directory structure
- [x] Set up core modules (`core/`, `integrations/`, `triage/`)
- [x] Create data models (`ShieldState`, `ShieldConfig`, etc.)
- [x] Set up requirements.txt
- [x] Create testing infrastructure (pytest, fixtures)
- [ ] Set up development environment documentation
- [ ] Configure pre-commit hooks (black, flake8, mypy)

### Day 3-4: ShieldCoordinator Implementation
- [ ] Implement `ShieldCoordinator.__init__` with dependency injection
- [ ] Implement `start()` method with ADHD Engine subscription
- [ ] Implement `on_attention_state_changed()` callback
- [ ] Implement `activate_shields()` with parallel component coordination
- [ ] Implement `deactivate_shields()` with queued message delivery
- [ ] Write unit tests for coordinator (85% coverage target)
- [ ] Integration with ADHD Engine (localhost:8095)

### Day 5: Productivity Monitoring
- [ ] Implement `_monitor_productivity()` background task
- [ ] Implement `_check_code_activity()` with Serena integration
- [ ] Implement false positive detection (15min threshold)
- [ ] Implement `_periodic_metrics_log()` for ConPort
- [ ] Write tests for monitoring logic

**Week 1 Deliverables**:
- ✅ Project structure and scaffolding
- [ ] Fully functional `ShieldCoordinator`
- [ ] ADHD Engine integration working
- [ ] Unit tests passing (85%+ coverage)

---

## Week 2: macOS Integration

### Day 6-7: DNDManager - macOS Focus Mode
- [ ] Implement `enable_macos_focus_mode()` with AppleScript
- [ ] Test Focus Mode activation on actual macOS system
- [ ] Implement `disable_macos_focus_mode()`
- [ ] Implement `_run_applescript()` helper
- [ ] Handle AppleScript errors gracefully
- [ ] Write unit tests for DNDManager
- [ ] Test on multiple macOS versions (Monterey, Ventura, Sonoma)

### Day 8: Desktop Commander Integration
- [ ] Integrate with Desktop Commander API (localhost:8099)
- [ ] Implement window minimization fallback
- [ ] Implement screenshot capture for context snapshots
- [ ] Test window management across multiple applications
- [ ] Write integration tests

### Day 9: Productivity Indicators
- [ ] Implement Serena file modification queries
- [ ] Implement git uncommitted changes detection
- [ ] Implement activity scoring (code changes + git activity)
- [ ] Test false positive detection threshold (15min)
- [ ] Write tests for productivity indicators

### Day 10: Week 2 Testing & Integration
- [ ] End-to-end test: FOCUSED state → Focus Mode activation
- [ ] End-to-end test: 15min no activity → auto-deactivation
- [ ] Performance testing (shield activation < 500ms)
- [ ] Fix bugs discovered during testing
- [ ] Code review and documentation

**Week 2 Deliverables**:
- [ ] macOS Focus Mode integration working
- [ ] Desktop Commander integration
- [ ] False positive detection functional
- [ ] Integration tests passing

---

## Week 3: Slack Integration

### Day 11-12: Slack Client Setup
- [ ] Set up Slack app in workspace
- [ ] Configure OAuth scopes (users.profile:write, users:write, etc.)
- [ ] Implement `SlackIntegration` class with async client
- [ ] Implement Socket Mode listener for incoming messages
- [ ] Test Slack API connectivity and rate limits
- [ ] Write integration tests with test Slack workspace

### Day 13: Slack Status Management
- [ ] Implement `set_slack_status()` with expiration
- [ ] Implement `clear_slack_status()`
- [ ] Implement presence management (away/active)
- [ ] Test status updates in real Slack workspace
- [ ] Handle Slack API errors gracefully

### Day 14-15: Message Triage System
- [ ] Implement `MessageTriage` class
- [ ] Implement `handle_incoming_message()` callback
- [ ] Implement `MessageQueue` with Redis backend
- [ ] Implement `UrgencyScorer` (rule-based, Phase 1)
- [ ] Implement urgency scoring logic (keywords, VIP users, etc.)
- [ ] Implement queued message delivery
- [ ] Write unit tests for triage system

**Week 3 Deliverables**:
- [ ] Slack Socket Mode working
- [ ] Slack status updates functional
- [ ] Message queuing operational
- [ ] Urgency scoring accurate (validate with test data)

---

## Week 4: Beta Testing & Iteration

### Day 16-17: Beta Preparation
- [ ] Recruit 10-20 ADHD beta testers from community
- [ ] Create onboarding documentation
- [ ] Create configuration guide (VIP users, keywords)
- [ ] Set up feedback collection (daily surveys)
- [ ] Set up telemetry (opt-in, privacy-preserving)
- [ ] Create beta tester Slack channel

### Day 18: Beta Deployment
- [ ] Deploy to beta tester machines
- [ ] Help users configure Slack integration
- [ ] Help users set VIP users and critical keywords
- [ ] Monitor initial usage and errors
- [ ] Fix critical bugs discovered on Day 1

### Day 19-20: Beta Feedback & Iteration
- [ ] Collect daily feedback surveys
- [ ] Analyze telemetry data:
  - Shield activation frequency
  - Average focus session duration
  - Messages queued vs delivered immediately
  - False positive/negative rates
- [ ] Implement top 3 user-requested features
- [ ] Fix reported bugs
- [ ] Adjust default thresholds based on data

**Week 4 Deliverables**:
- [ ] 10-20 ADHD beta testers actively using
- [ ] Feedback collected (daily surveys)
- [ ] Telemetry analysis report
- [ ] Bug fixes and improvements deployed
- [ ] Phase 1 retrospective document

---

## Success Criteria (Phase 1)

### Functional Requirements
- ✅ Shields activate automatically when ADHD Engine reports FOCUSED
- ✅ macOS Focus Mode enables successfully
- ✅ Slack status updates correctly
- ✅ Messages queued during focus sessions
- ✅ False positive detection working (15min threshold)
- ✅ Queued messages delivered on shield deactivation

### Performance Requirements
- Shield activation latency: <500ms ✅
- Urgency scoring latency: <100ms ✅
- Memory usage: <100MB ✅
- CPU usage: <5% during active monitoring ✅

### Quality Requirements
- Unit test coverage: >85% ✅
- Integration tests passing: 100% ✅
- No critical bugs in beta testing ✅
- User satisfaction: >70% (NPS) 🎯

### User Experience Requirements
- Beta testers report reduced interruptions: >50% 🎯
- False positive rate: <20% 🎯
- False negative rate: <10% 🎯
- Manual override usage: <30% (shouldn't fight system) 🎯

---

## Risk Mitigation

### Technical Risks

**Risk**: macOS Focus Mode AppleScript breaks on system updates
- **Mitigation**: Desktop Commander fallback, test on multiple macOS versions
- **Owner**: Engineer 1

**Risk**: Slack API rate limiting
- **Mitigation**: Implement exponential backoff, batch status updates
- **Owner**: Engineer 2

**Risk**: ADHD Engine integration failures
- **Mitigation**: Graceful degradation, manual activation option
- **Owner**: Engineer 3

### User Experience Risks

**Risk**: Beta testers ignore auto-DND (habituation)
- **Mitigation**: Randomized DND messages, effectiveness reports
- **Owner**: UX Lead

**Risk**: Important messages incorrectly queued (false positives)
- **Mitigation**: User feedback loop, urgency scoring tuning
- **Owner**: Engineer 2

**Risk**: Anxiety about missing messages
- **Mitigation**: Transparent filtering, reassuring message counts
- **Owner**: UX Lead

---

## Daily Standup Template

**What did I do yesterday?**
- [Completed tasks]

**What am I doing today?**
- [Planned tasks from sprint plan]

**Blockers?**
- [Any impediments]

**Metrics**:
- Unit test coverage: X%
- Integration tests passing: X/Y
- Beta tester count: X
- Critical bugs: X

---

## Retrospective Questions (End of Week 4)

1. **What went well?**
   - Which components were easier than expected?
   - What processes worked effectively?

2. **What didn't go well?**
   - Which components took longer than estimated?
   - What technical challenges were unexpected?

3. **What should we change for Phase 2?**
   - Process improvements?
   - Technical approach adjustments?
   - Timeline adjustments?

4. **User Feedback Themes**:
   - Top 3 positive feedback items
   - Top 3 improvement requests
   - Critical bugs encountered

5. **Metrics Review**:
   - Interruption reduction: Actual vs Target
   - Task completion improvement: Actual vs Target
   - User satisfaction: Actual vs Target

---

## Next Steps After Phase 1

**If Phase 1 is successful** (>70% user satisfaction, >50% interruption reduction):
- Proceed to Phase 2: Calendar integration and AI summarization
- Expand beta tester pool to 50-100 users
- Begin Windows/Linux platform support investigation

**If Phase 1 needs iteration**:
- Analyze root causes of user dissatisfaction
- Implement critical improvements
- Extend Phase 1 by 1-2 weeks for validation
- Re-assess Phase 2 timeline

---

**Document Status**: Ready for Week 1 kickoff
**Last Updated**: 2025-10-20
**Owner**: Component 7 Implementation Team
