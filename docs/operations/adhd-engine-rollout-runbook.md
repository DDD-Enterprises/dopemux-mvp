# ADHD Engine Integration - Production Rollout Runbook

**Task**: IP-001 Production Rollout
**Date**: 2025-10-16
**Owner**: Development Team
**Duration**: 4 phases over 7-14 days
**Risk Level**: LOW (feature flags provide instant rollback)

---

## Pre-Rollout Checklist

**Prerequisites**:
- [ ] ADHD Engine service is running (services/adhd_engine/)
- [ ] Redis db=5 is accessible (ADHD Engine storage)
- [ ] All services have been rebuilt with new code
- [ ] Feature flags are OFF by default (safe state)
- [ ] Monitoring alerts configured
- [ ] Rollback procedure tested

**Validation**:
```bash
# Verify ADHD Engine running
docker ps | grep adhd-engine
# Should show container running

# Verify Redis db=5 accessible
redis-cli -h localhost -p 6379 -n 5 PING
# Should return: PONG

# Verify feature flags default to OFF
redis-cli -h localhost -p 6379 -n 5 KEYS "adhd:feature_flags:*"
# Should return: (empty array) or all values are "false"
```

---

## Phase 1: Beta Test (Days 1-2)

**Goal**: Enable for ONE developer to verify integration works in production

**Steps**:

1. **Select Beta Tester**:
   - Choose willing ADHD developer
   - Brief them on what to expect
   - Ask for detailed feedback

2. **Enable for Beta User**:
```bash
# Enable ADHD Engine integration for beta user only
redis-cli -h localhost -p 6379 -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_serena:user:developer1" "true"

redis-cli -h localhost -p 6379 -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_conport:user:developer1" "true"

redis-cli -h localhost -p 6379 -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_dope_context:user:developer1" "true"
```

3. **Monitor for 48 Hours**:
```bash
# Watch logs for ADHD Engine queries
tail -f /var/log/serena/mcp.log | grep "ADHD Engine"
# Should see: "✅ ADHD Code Navigator connected to ADHD Engine"

# Monitor for errors
tail -f /var/log/*/mcp.log | grep -i "error.*adhd\|failed.*adhd"
# Should see: minimal or no errors

# Check query patterns
redis-cli -h localhost -p 6379 -n 5 MONITOR | grep "adhd:"
# Should see occasional queries (not excessive - caching working)
```

4. **Collect Feedback**:
   - Does result count feel right? (5 when scattered, 15 when focused)
   - Are break suggestions helpful and timely?
   - Any unexpected behavior?
   - Performance issues?

**Success Criteria**:
- [ ] Beta user reports positive experience
- [ ] No errors in logs
- [ ] Performance acceptable (<10ms overhead)
- [ ] Accommodations adapt as expected

**Rollback if Needed**:
```bash
# Disable for beta user
redis-cli -h localhost -p 6379 -n 5 DEL \
  "adhd:feature_flags:adhd_engine_integration_serena:user:developer1"

# User immediately reverts to hardcoded defaults
```

---

## Phase 2: Serena Service Rollout (Days 3-5)

**Goal**: Enable for ALL users of Serena (first service-wide rollout)

**Why Serena First**: Most ADHD-critical service (code navigation with complexity)

**Steps**:

1. **Enable Serena Globally**:
```bash
redis-cli -h localhost -p 6379 -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_serena:global" "true"

# All Serena users now get ADHD Engine accommodations
```

2. **Announce to Team**:
```
📢 Serena now adapts to your ADHD state!

- Scattered? See 5 results (not 10)
- Focused? See 15 results
- Hyperfocused? See 40 results

Your code navigation now personalizes to YOUR cognitive state in real-time.

Questions? Contact: [your contact]
```

3. **Monitor for 72 Hours**:
```bash
# Check logs across all users
grep "ADHD Engine" /var/log/serena/mcp.log | tail -50

# Monitor error rates
grep -c "error.*adhd" /var/log/serena/mcp.log
# Should be: 0 or very low

# Check cache hit rates
redis-cli -h localhost -p 6379 -n 5 INFO stats | grep keyspace_hits
# Should show good cache performance
```

4. **Collect Metrics**:
   - User satisfaction scores
   - Task completion rates (should improve)
   - Break compliance (should improve)
   - Cognitive overload incidents (should decrease)

**Success Criteria**:
- [ ] No increase in error rates
- [ ] Positive user feedback
- [ ] Performance metrics stable
- [ ] Cache hit rate >95%

**Rollback if Needed**:
```bash
# Emergency disable for all Serena users
redis-cli -h localhost -p 6379 -n 5 DEL \
  "adhd:feature_flags:adhd_engine_integration_serena:global"

# All users immediately revert to hardcoded defaults
# No service restart required!
```

---

## Phase 3: ConPort + Dope-Context Rollout (Days 6-10)

**Goal**: Enable remaining services

**Steps**:

1. **Enable ConPort** (Day 6):
```bash
redis-cli -h localhost -p 6379 -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_conport:global" "true"
```

2. **Monitor ConPort** (Days 6-7):
   - Check semantic search quality
   - Verify result limits adapt
   - Monitor performance

3. **Enable Dope-Context** (Day 8):
```bash
redis-cli -h localhost -p 6379 -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_dope_context:global" "true"
```

4. **Monitor Dope-Context** (Days 8-10):
   - Check code search results
   - Verify top_k adaptation
   - Monitor cache performance

**Success Criteria (Each Service)**:
- [ ] No errors in logs
- [ ] User feedback positive
- [ ] Performance stable
- [ ] Accommodations working

---

## Phase 4: Full Production (Days 11-14)

**Goal**: All services fully integrated, remove feature flag checks (optional)

**Steps**:

1. **Validate All Services** (Day 11):
```bash
# Verify all flags enabled
redis-cli -h localhost -p 6379 -n 5 KEYS "adhd:feature_flags:*:global"

# Should show:
# adhd:feature_flags:adhd_engine_integration_serena:global
# adhd:feature_flags:adhd_engine_integration_conport:global
# adhd:feature_flags:adhd_engine_integration_dope_context:global
```

2. **Monitor System-Wide** (Days 11-13):
   - Aggregate metrics across all services
   - User satisfaction survey
   - Performance dashboard review

3. **Optional: Remove Feature Flag Code** (Day 14):
   - Once stable for 2+ weeks, can remove feature flag checks
   - Simplifies code (no more if/else branches)
   - Only if 100% confident in ADHD Engine stability

**Code Cleanup** (Optional):
```python
# BEFORE (with feature flags):
if await self.feature_flags.is_enabled(...):
    return await self.adhd_config.get_max_results(user_id)
return self._default_max_initial_results

# AFTER (feature flags removed):
return await self.adhd_config.get_max_results(user_id)
# Keep fallback for when ADHD Engine unavailable
```

---

## Monitoring & Metrics

**Key Metrics to Track**:

1. **Technical Health**:
   - ADHD Engine uptime: >99.9%
   - Redis query latency: <5ms
   - Cache hit rate: >95%
   - Error rate: <0.1%

2. **User Experience**:
   - Result count satisfaction: Survey
   - Overwhelm incidents: Should decrease
   - Task completion rate: Should increase
   - Break compliance: Should improve

3. **System Performance**:
   - Service response times: Should be unchanged
   - Redis load: Should be minimal (caching working)
   - Memory usage: Should be stable

**Dashboards**:
```yaml
Grafana Dashboard:
  - ADHD Engine connection status
  - Feature flag status per service
  - Query latency (p50, p95, p99)
  - Cache hit/miss rates
  - Error rates by service
```

**Alerts**:
```yaml
Critical Alerts:
  - ADHD Engine down >5 minutes
  - Error rate >1%
  - Redis connection failures

Warning Alerts:
  - Cache hit rate <90%
  - Query latency >10ms
  - Feature flag disabled unexpectedly
```

---

## Rollback Procedures

### Emergency Rollback (Instant)

**If critical issues occur**:
```bash
#!/bin/bash
# Emergency rollback script

echo "🚨 EMERGENCY ROLLBACK: Disabling all ADHD Engine integration"

redis-cli -h localhost -p 6379 -n 5 <<EOF
DEL adhd:feature_flags:adhd_engine_integration_serena:global
DEL adhd:feature_flags:adhd_engine_integration_conport:global
DEL adhd:feature_flags:adhd_engine_integration_dope_context:global
EOF

echo "✅ All services reverted to hardcoded defaults"
echo "ℹ️  No service restart required - changes immediate"
```

**Impact**: All users immediately revert to original hardcoded behavior (10 results, 0.7 complexity, etc.)

### Partial Rollback (Service-Specific)

**If one service has issues**:
```bash
# Disable just Serena
redis-cli -n 5 DEL "adhd:feature_flags:adhd_engine_integration_serena:global"

# ConPort and dope-context remain integrated
```

### Rollback by User

**If specific user has issues**:
```bash
# Disable for one user
redis-cli -n 5 SET \
  "adhd:feature_flags:adhd_engine_integration_serena:user:problematic_user" "false"

# This overrides global flag for this user only
```

---

## Troubleshooting

### Issue: Accommodations Not Adapting

**Symptoms**: User always sees 10 results regardless of state

**Diagnosis**:
```bash
# Check feature flag enabled
redis-cli -n 5 GET "adhd:feature_flags:adhd_engine_integration_serena:global"
# Should return: "true"

# Check ADHD Engine has set user state
redis-cli -n 5 GET "adhd:attention_state:user_id"
# Should return: scattered/focused/hyperfocused/etc.

# Check service logs
grep "ADHD Engine" /var/log/serena/mcp.log
# Should see: "✅ connected to ADHD Engine"
```

**Fix**:
- Ensure ADHD Engine is running and monitoring user
- Verify Redis connection
- Check user_id matches between systems

### Issue: Performance Degradation

**Symptoms**: Slow response times after integration

**Diagnosis**:
```bash
# Check cache is working
# Multiple queries should not hit Redis every time

# Monitor Redis query frequency
redis-cli -n 5 MONITOR | grep "adhd:"
# Should see: Infrequent queries (5-minute cache working)
```

**Fix**:
- Verify caching is enabled (5-minute TTL)
- Check for cache invalidation bugs
- Consider increasing cache TTL if needed

### Issue: Inconsistent Behavior

**Symptoms**: Different accommodations across services

**Diagnosis**:
```bash
# All services should read same Redis keys
redis-cli -n 5 GET "adhd:attention_state:user_id"
redis-cli -n 5 GET "adhd:energy_level:user_id"

# Check cache timestamps
# If one service has stale cache, clear it
```

**Fix**:
- Ensure all services use same user_id
- Clear caches to force fresh queries
- Verify ADHD Engine is updating state correctly

---

## Success Metrics

**After Full Rollout** (30 days):

**Technical Success**:
- [ ] 100% of services using ADHD Engine
- [ ] 0 hardcoded ADHD thresholds remaining
- [ ] Feature flags stable (enabled globally)
- [ ] Error rate <0.1%
- [ ] Performance unchanged or improved

**User Success**:
- [ ] 80%+ users report positive experience
- [ ] Task completion rate +15-30%
- [ ] Overwhelm incidents -40%
- [ ] Break compliance +25%
- [ ] ADHD developer satisfaction +40%

**Business Success**:
- [ ] System differentiation (unique ADHD support)
- [ ] Reduced support tickets (ADHD-related)
- [ ] Increased user retention
- [ ] Positive market positioning

---

## Post-Rollout

**Week 1**: Daily monitoring and quick fixes
**Week 2**: Tune thresholds based on feedback
**Week 3**: Optimize cache TTL and performance
**Week 4**: Comprehensive retrospective and documentation

**Optional Enhancements** (Future):
- Machine learning to predict energy dips
- Personalized energy patterns per user
- Team-wide ADHD insights dashboard
- Integration with calendar (meeting = energy drain)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-16
**Status**: Ready for Production Rollout
