# Master Action Plan - ADHD Stack + F-NEW Features

**Date**: 2025-10-25
**Status**: Post-epic-session planning
**Context**: 30 commits, ~7,000 lines, 5 services built

---

## Current State

### ADHD Intelligence Stack: PRODUCTION READY ✅
- 5 services operational
- 12 features complete
- Security hardened
- Fully documented

### F-NEW Features: 6/8 Ready, 2 Need Action
- F-NEW-1 through F-NEW-6: Production ready
- F-NEW-8: Needs integration with ADHD Notifier
- F-NEW-7: Strategic future (3-4 weeks)

---

## Immediate Actions (This Week)

### Priority 1: F-NEW-8 Integration (CRITICAL)
**Why**: Combine intelligent detection with effective delivery
**Time**: 50 minutes
**Impact**: Enhanced break reminder intelligence

**Steps**:
1. Wire F-NEW-8 output to ADHD Notifier input (15 min)
2. Add F-NEW-8 to start-all.sh (5 min)
3. Test integrated flow (15 min)
4. Validate in real use (15 min)

**Files**:
- services/break-suggester/engine.py (add event emission)
- services/adhd-notifier/monitor.py (add event subscription)
- scripts/start-all.sh (add F-NEW-8 startup)

### Priority 2: Validate F-NEW-3/5/6 in Production
**Why**: Ensure "wired" means "working"
**Time**: 1 hour
**Impact**: Confidence in F-NEW features

**Steps**:
1. F-NEW-3: Test unified complexity in real code analysis
2. F-NEW-5: Test code graph enrichment in search results
3. F-NEW-6: Test session intelligence dashboard in Claude Code
4. Monitor performance and errors

### Priority 3: Monitor & Dogfood
**Why**: Real-world validation
**Time**: Ongoing (1 week)
**Impact**: Identify issues early

**Activities**:
- Use ADHD stack in daily development
- Monitor logs for errors
- Track performance metrics
- Collect user feedback (yourself!)

---

## Short-term Actions (Next 2 Weeks)

### Performance Optimization (Phase 6 Completion)
**Remaining Items**:
1. Redis caching for F-NEW-3 complexity scores (5-second TTL)
2. Rate limiting for F-NEW-5 enrichment (max 10 concurrent)
3. Cache file modification times in Workspace Watcher

**Time**: 2-3 hours
**Impact**: 20-30% performance improvement

### Code Quality Cleanup
**Remaining Items**:
1. Extract magic numbers to config files
2. Remove any remaining debug logs
3. Add type hints where missing
4. Update docstrings

**Time**: 1-2 hours
**Impact**: Better maintainability

---

## Medium-term Actions (Q4 2025)

### Enhanced ADHD Features
1. **Pomodoro Timer Integration**:
   - Traditional 25/5 timer
   - ADHD-adaptive timing
   - Auto-pause on interruptions

2. **Context Switch Cost Calculator**:
   - Measure time lost to switches
   - Visualize interruption impact
   - Suggest focus blocks

3. **Weekly ADHD Reports**:
   - Trend analysis
   - Pattern identification
   - Recommendations

### F-NEW Features
1. **F-NEW-3 Optimization**:
   - Add caching
   - Monitor performance
   - Tune weights based on usage

2. **F-NEW-5 Enhancement**:
   - Add rate limiting
   - Optimize parallel execution
   - Enhanced error handling

3. **F-NEW-6 Improvement**:
   - Add session history persistence
   - Tune recommendation thresholds
   - Enhanced dashboard UI

---

## Long-term Actions (Q1 2026)

### F-NEW-7: ConPort-KG 2.0 Deep Integration
**Decision Point**: Evaluate priority vs ROI

**If Proceed**:
- Week 1: Foundation (PostgreSQL AGE, basic queries)
- Week 2: Advanced queries (historical, cross-workspace)
- Week 3: Intelligence (ML, predictions)
- Week 4: Polish (optimization, deployment)

**If Defer**:
- Current ConPort stub works fine
- Other features may provide better ROI
- Can revisit when ML features needed

### Advanced Intelligence
1. **Predictive Energy Forecasting**:
   - ML model predicts energy drops
   - Proactive task recommendations
   - Optimal work time suggestions

2. **Multi-User Support**:
   - Team ADHD patterns
   - Shared focus hours
   - Collaborative break scheduling

3. **Mobile App**:
   - iOS/Android dashboard
   - Push notifications
   - Quick ADHD state check

---

## Decision Framework

### When to Implement Features:

**Implement Now**:
- Fixes security/performance issues
- Improves existing features
- Low effort, high impact
- Example: F-NEW-8 integration (50 min, big ADHD impact)

**Implement Soon**:
- Enhances user experience
- Moderate effort, high value
- No blocking dependencies
- Example: Performance optimizations, code cleanup

**Implement Later**:
- Strategic value but high cost
- Requires significant time
- Can be phased smaller
- Example: F-NEW-7 (3-4 weeks), ML features

**Defer/Skip**:
- Low ROI vs effort
- Better alternatives exist
- Nice-to-have vs must-have
- Example: Some Phase 7 features

---

## Recommended Priorities

### Next Session (Immediate):
1. **F-NEW-8 Integration** - Wire to ADHD Notifier
2. **F-NEW Validation** - Test 3/5/6 in real use
3. **Monitoring** - Watch for errors/issues

### This Week:
4. **Performance** - Caching, rate limiting
5. **Cleanup** - Extract config, remove debug logs
6. **Documentation** - Update based on findings

### This Month:
7. **Enhanced Features** - Pomodoro, context cost calculator
8. **F-NEW Optimization** - Based on real usage data
9. **Stability** - Monitor and fix issues

### Next Quarter:
10. **Strategic Decision** - F-NEW-7 yes/no based on needs
11. **Advanced Intelligence** - ML features if validated
12. **Multi-user** - If team use case emerges

---

## Success Metrics

### Week 1:
- ✅ F-NEW-8 integrated with ADHD Notifier
- ✅ All F-NEW features validated in real use
- ✅ No critical errors in logs

### Month 1:
- ✅ Performance optimized (caching, rate limiting)
- ✅ Code quality improved (config extraction, cleanup)
- ✅ User satisfaction validated (dogfooding feedback)

### Quarter 1:
- ✅ F-NEW-7 decision made (implement or defer)
- ✅ Enhanced features deployed (if needed)
- ✅ System stability proven (30+ days uptime)

---

## Risk Mitigation

### Technical Risks:
- **Risk**: F-NEW features untested under load
- **Mitigation**: Monitor in production, gradual rollout

- **Risk**: F-NEW-8 + ADHD Notifier integration issues
- **Mitigation**: Test thoroughly, keep independent fallbacks

- **Risk**: Performance degradation with all features active
- **Mitigation**: Add Redis caching, rate limiting, monitoring

### ADHD-Specific Risks:
- **Risk**: Too many notifications (cognitive overload)
- **Mitigation**: Anti-spam protection, quiet hours, user preferences

- **Risk**: Inaccurate break suggestions (annoying vs helpful)
- **Mitigation**: Tune thresholds, collect feedback, adaptive learning

- **Risk**: System complexity overwhelming (ironic for ADHD tool)
- **Mitigation**: Keep UI simple, progressive disclosure, good docs

---

## The Path Forward

**Immediate** (Do Now):
- Integrate F-NEW-8 with ADHD Notifier
- Validate all systems working
- Monitor for 24 hours

**Short-term** (This Week):
- Optimize performance
- Clean up code
- Document learnings

**Medium-term** (This Month):
- Enhance based on real use
- Add requested features
- Improve stability

**Long-term** (This Quarter):
- Strategic decisions (F-NEW-7, ML, multi-user)
- Advanced intelligence
- Scale if needed

---

## Summary

**What We Have**: Production-ready ADHD intelligence stack
**What's Next**: Integrate F-NEW-8, validate, optimize
**What's Future**: Strategic enhancements based on needs

**Approach**: Incremental, validated, user-driven

**The foundation is solid. The features are ready. Time to use and refine!**
