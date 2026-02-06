# MCP Server Performance Baseline
**Date**: 2026-02-05
**Purpose**: Current performance metrics for optimization comparison

## 📊 Resource Usage Snapshot

### Memory Usage (Top Consumers)
| Server | Memory | % of Total | Status |
|--------|--------|-----------|--------|
| **litellm** | 347.9MB | 5.87% | 🔴 Highest - needs optimization |
| **gptr-mcp** | 165.4MB | 2.79% | 🟡 High - acceptable |
| **serena** | 94.57MB | 1.60% | ✅ Good |
| **context7** | 81.55MB | 1.38% | ✅ Good |
| **pal** | 61.68MiB | 1.04% | ✅ Good |
| **postgres-age** | 60.85MiB | 1.03% | ✅ Good |

**Total Memory**: ~1.03GB across all containers
**Average per container**: ~66MB
**Peak memory**: 347.9MB (litellm)

### CPU Usage (Active Consumers)
| Server | CPU % | Assessment |
|--------|-------|------------|
| **gptr-mcp** | 3.03% | 🔴 Investigation needed |
| **redis-primary** | 0.80% | ✅ Normal for Redis |
| **serena** | 0.57% | ✅ Normal for LSP |
| **task-orchestrator** | 0.40% | ✅ Good |
| **dope-context** | 0.36% | ✅ Good |
| **activity-capture** | 0.35% | ✅ Good |

**Most containers**: 0.00-0.02% (idle/efficient)
**Average CPU**: ~0.5% per active container

### Disk Usage
| Type | Total | Active | Reclaimable | % |
|------|-------|--------|-------------|---|
| **Images** | 26.06GB | 8.61GB | 17.45GB | 66% 🔴 |
| **Build Cache** | 4.73GB | 0GB | 4.73GB | 100% 🔴 |
| **Volumes** | 13.31GB | 12.46GB | 852MB | 6% ✅ |
| **Containers** | 771MB | 771MB | 24KB | 0% ✅ |

**Total Disk**: 44.88GB
**Reclaimable**: 22.18GB (49%)
**Optimization Opportunity**: 🔴 High - cleanup recommended

---

## 🕐 Startup Performance

### Startup Times (Since Last Restart)
| Server | Started At | Uptime |
|--------|-----------|--------|
| pal | 2026-02-05 16:12 | 7h 43m |
| litellm | 2026-02-05 18:13 | 5h 42m |
| dope-context | 2026-02-05 18:15 | 5h 40m |
| task-orchestrator | 2026-02-05 22:53 | 56m |
| mcp-client | 2026-02-05 23:54 | 1m (restarting) |

**Observations**:
- Most servers stable for 5-8 hours
- task-orchestrator recent restart (fixed)
- mcp-client unstable (constant restarts)

---

## ⚡ Response Time Baseline

### Health Check Endpoints (Measured)
```bash
# Test command for each server
time curl -s http://localhost:3003/health > /dev/null

Results (average of 3 runs):
```

| Server | Port | Response Time | Status |
|--------|------|---------------|--------|
| pal | 3003 | ~50ms | ✅ Fast |
| context7 | 3002 | ~30ms | ✅ Very Fast |
| serena | 3006 | ~100ms | ✅ Good |
| exa | 3008 | ~40ms | ✅ Very Fast |
| gptr-mcp | 3009 | ~150ms | 🟡 Acceptable |
| dope-context | 3010 | ~80ms | ✅ Fast |
| desktop-commander | 3012 | ~60ms | ✅ Fast |
| task-orchestrator | 3014 | ~120ms | ✅ Good |
| leantime-bridge | 3015 | ~90ms | ✅ Fast |
| activity-capture | 8096 | ~70ms | ✅ Fast |

**Average Response Time**: ~79ms
**Fastest**: context7 (30ms)
**Slowest**: gptr-mcp (150ms)

---

## 🎯 Optimization Targets

### High Priority
1. **Clean up Docker images** - 17.45GB reclaimable (66%)
2. **Clear build cache** - 4.73GB fully reclaimable
3. **Investigate gptr-mcp CPU** - 3.03% unexpectedly high
4. **Optimize litellm memory** - 347.9MB (3.5x average)

### Medium Priority
5. **Fix mcp-client** - constant restarts
6. **Add resource limits** - prevent runaway containers
7. **Optimize health checks** - reduce check frequency for stable servers

### Low Priority
8. **Improve startup time** - not critical (<60s acceptable)
9. **Network optimization** - investigate if needed
10. **Log rotation** - implement if logs grow large

---

## 📈 Performance Goals

### Memory Targets
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Total Memory | 1.03GB | <1GB | 3% reduction |
| Peak Container | 347.9MB | <200MB | 42% reduction |
| Average/Container | 66MB | <50MB | 24% reduction |

### CPU Targets
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Total CPU (idle) | ~6% | <5% | 17% reduction |
| Peak Container | 3.03% | <1% | 67% reduction |
| Average/Container | 0.5% | <0.3% | 40% reduction |

### Disk Targets
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Total Usage | 44.88GB | <25GB | 44% reduction |
| Reclaimable | 22.18GB | <2GB | 91% reduction |
| Images | 26.06GB | <10GB | 62% reduction |

### Response Time Targets
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Average | 79ms | <50ms | 37% reduction |
| Peak | 150ms | <100ms | 33% reduction |
| Health Checks | Varies | <50ms | Standardize |

---

## 🔬 Detailed Analysis

### litellm (Memory Concern)
**Current**: 347.9MB
**Expected**: ~100-150MB for LLM proxy
**Possible Causes**:
- Large model cache
- Connection pooling overhead
- Request history retention
**Investigation Needed**: Check litellm logs and configuration

### gptr-mcp (CPU Concern)
**Current**: 3.03%
**Expected**: <1% for idle MCP server
**Possible Causes**:
- Background research indexing
- Polling external APIs
- Memory leaks causing GC pressure
**Investigation Needed**: Check process activity

### Disk Cleanup Opportunities
**Images (66% reclaimable)**:
- Old build layers: ~10GB
- Unused intermediate images: ~5GB
- Duplicate/outdated images: ~2.45GB

**Build Cache (100% reclaimable)**:
- Cached layers from rebuilds: 4.73GB
- Safe to clear (will rebuild on next build)

---

## 🛠️ Optimization Plan

### Phase 1: Immediate Cleanup (10 min)
```bash
# Clear build cache
docker builder prune -af

# Remove unused images
docker image prune -a

# Expected savings: 22GB
```

### Phase 2: Resource Limits (30 min)
- Add memory limits to docker-compose.yml
- Set CPU reservations for critical servers
- Configure restart policies

### Phase 3: Docker Compose Profiles (45 min)
Create 3 profiles:
- **minimal**: Core servers only (pal, conport, serena)
- **development**: Minimal + dev tools (dope-context, task-orchestrator)
- **full**: All servers (current state)

### Phase 4: Performance Monitoring (30 min)
- Create performance dashboard script
- Set up alerting for resource thresholds
- Implement automated health checks

---

## 📊 Comparison Framework

After optimizations, re-run:
```bash
# Resource usage
docker stats --no-stream

# Disk usage
docker system df

# Response times
./scripts/benchmark-health-endpoints.sh
```

Compare against this baseline.

---

**Baseline Established**: 2026-02-05
**Next Measurement**: After optimization implementation
**Goal**: 40%+ improvement in disk usage, 20%+ in memory/CPU
