# MCP Server Audit Report
**Date**: 2026-02-05
**Auditor**: Claude (Learning Mode)
**Purpose**: Investigate "down" servers and make keep/fix/deprecate decisions

## 🔍 Investigation Summary

### Servers Investigated
1. mas-sequential-thinking
2. task-master-ai
3. mcp-client
4. plane-coordinator
5. activity-capture

## 📊 Findings & Decisions

### ❌ DEPRECATE: mas-sequential-thinking
**Status**: Incomplete - only .env file exists, no code
**Evidence**:
- Directory `/docker/mcp-servers/mcp-server-mas-sequential-thinking` has only .env
- No Dockerfile, no server implementation
- Health report notes "may be replaced by Zen"
**Recommendation**: **REMOVE** from docker-compose.yml
**Rationale**: Zen/pal provides equivalent multi-step reasoning functionality

---

### ✅ KEEP (Optional): task-master-ai
**Status**: Complete implementation, external project wrapper
**Evidence**:
- Dockerfile wraps external GitHub project: `github.com/eyaltoledano/claude-task-master`
- Different from task-orchestrator: External tool vs internal implementation
- Uses stdio transport (vs task-orchestrator's HTTP)
- Port 3005 (vs task-orchestrator's 3014)
- Purpose: AI-powered task management and PRD processing (complementary)
**Recommendation**: **KEEP** as optional experimental server
**Rationale**:
  - Not a duplicate of task-orchestrator (different implementation, different tools)
  - May provide additional task management features
  - Marked "experimental" - can be tested and evaluated
**Action**: Can start for evaluation OR mark as "optional/experimental"

---

### ✅ KEEP + FIX: mcp-client
**Status**: Complete, wrong path in docker-compose
**Evidence**:
- Full implementation exists in `/services/mcp-client/`
- docker-compose references `../../services/mcp-client` but context says `./mcp-client`
- Purpose: Custom MCP client for stdio server integration (needed for task-master-ai)
**Recommendation**: **KEEP** and fix docker-compose path
**Action**: Update build context path

---

### ✅ KEEP: plane-coordinator
**Status**: Complete, uses shared Dockerfile
**Evidence**:
- Uses `/services/task-orchestrator/Dockerfile.coordination` (exists)
- Purpose: Two-plane architecture coordination (PM + Cognitive planes)
- Part of core architecture ADR-007
**Recommendation**: **KEEP** - core architecture component
**Note**: Just needs to be started, configuration looks correct

---

### ✅ KEEP + FIX: activity-capture
**Status**: Complete, wrong path in docker-compose
**Evidence**:
- Full implementation in `/services/activity-capture/` (NOT in docker/mcp-servers/)
- Has Dockerfile, main.py, activity_tracker.py, adhd_client.py
- Purpose: ADHD metrics tracking (activity logging, workspace support)
**Recommendation**: **KEEP** and fix docker-compose path
**Action**: Update build context to `../../services/activity-capture`

## 📋 Action Items

### Immediate (Priority 1)
- [ ] **Remove mas-sequential-thinking** from docker-compose.yml
- [ ] **Fix mcp-client path** in docker-compose.yml
- [ ] **Fix activity-capture path** in docker-compose.yml
- [ ] **Start plane-coordinator** (already configured correctly)
- [ ] **Compare task-master-ai vs task-orchestrator tools**

### Documentation (Priority 2)
- [ ] Update SERVER_REGISTRY.md with current status
- [ ] Mark mas-sequential-thinking as DEPRECATED
- [ ] Document task-master-ai vs task-orchestrator decision
- [ ] Add activity-capture startup docs

### Testing (Priority 3)
- [ ] Test mcp-client after path fix
- [ ] Test activity-capture after path fix
- [ ] Test plane-coordinator startup
- [ ] Verify all services healthy

## 🎯 Expected Outcome

**Before**: 12/17 servers running (71%)
**After**:
- If keeping task-master-ai: 16/17 servers (94%)
- If deprecating task-master-ai: 15/16 servers (94%)

**Removed**: 1 (mas-sequential-thinking)
**Fixed**: 2-3 (mcp-client, activity-capture, optionally task-master-ai)
**Started**: 1 (plane-coordinator)

## 💡 Key Insights

1. **Zombie Definitions**: Several "down" servers were defined in docker-compose but code never existed
2. **Path Issues**: mcp-client and activity-capture exist but have wrong build paths
3. **Architecture Components**: plane-coordinator is core, not optional
4. **Superseded Servers**: task-master-ai appears to be experimental version of task-orchestrator
5. **Documentation Drift**: Health report was based on docker-compose.yml, not actual file system

## 📝 Next Session

Start with:
1. Compare task-master-ai and task-orchestrator tools (15 min)
2. Update docker-compose.yml with fixes (30 min)
3. Test all fixed servers (30 min)
4. Update health report (15 min)

Total: ~90 minutes to complete Priority 1
