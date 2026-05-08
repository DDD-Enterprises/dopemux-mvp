# MCP Server Improvement - Next Steps Plan

**Current Progress**: 40% complete (2 of 5 major tasks done)
**Remaining Work**: ~7-12 hours across 3 priorities

---

## ✅ Completed (Session 2026-02-05)

1. **Health Assessment** - Identified all server statuses
2. **Critical Fix** - task-orchestrator now running (37 tools restored)
3. **Workflow System** - Complete automation framework with templates

---

## 🎯 Next: Fix Remaining Servers (2-3 hours)

### Priority: HIGH - Clarify server purposes

```bash
# 1. Investigate mas-sequential-thinking (30 min)
docker logs dopemux-mas-sequential-thinking
# Decision: Keep, replace with Zen/pal, or deprecate?

# 2. Review unclear servers (1 hour)
- task-master-ai: Duplicate of task-orchestrator?
- mcp-client: Purpose?
# Decision: Document, fix, or remove

# 3. Test activity-capture (30 min)
docker-compose up -d activity-capture
# Decision: Worth keeping for ADHD metrics?

# 4. Update health report (30 min)
# Document all decisions made
```

### Deliverables
- [ ] Updated MCP_HEALTH_REPORT.md
- [ ] Fixed or deprecated unclear servers
- [ ] Clear documentation for kept servers

---

## 📚 Then: Improve Documentation (2-4 hours)

### Priority: MEDIUM - Make servers easy to use

```bash
# 1. Update SERVER_REGISTRY.md (1 hour)
- Add current status column
- Document startup procedures
- Add health check endpoints
- Include port mappings

# 2. Create TROUBLESHOOTING.md (1 hour)
- Common issues per server
- Resolution steps
- Restart procedures

# 3. Create OPERATIONS.md (1 hour)
- How to start/stop all servers
- How to check health
- How to add new servers
- Emergency procedures

# 4. Add server README files (1 hour)
- One README per complex server
- Purpose and use cases
- Environment variables
- Dependencies
```

### Deliverables
- [ ] Updated SERVER_REGISTRY.md
- [ ] TROUBLESHOOTING.md guide
- [ ] OPERATIONS.md runbook
- [ ] Individual server docs

---

## ⚡ Finally: Optimize Performance (3-5 hours)

### Priority: LOW - Make faster and leaner

```bash
# 1. Profile current performance (1 hour)
# Measure response times, startup, resource usage
./profile-mcp-servers.sh

# 2. Create on-demand profiles (2 hours)
# docker-compose profiles for different scenarios
- minimal: Just core servers
- development: Core + dev tools
- full: All servers

# 3. Optimize Docker configs (1 hour)
# Add resource limits, tune health checks

# 4. Implement caching (1 hour)
# Add Redis caching where beneficial
```

### Deliverables
- [ ] Performance baseline report
- [ ] docker-compose profiles
- [ ] Optimized configs
- [ ] Before/after comparison

---

## 📋 Quick Checklist

**Next Session Start Here:**
- [ ] Read MCP_IMPROVEMENT_PROGRESS.md for context
- [ ] Check docker ps for current server status
- [ ] Start with: Investigate mas-sequential-thinking
- [ ] Work through fix servers → docs → performance
- [ ] Update progress file after each major milestone

**Session End:**
- [ ] Update MCP_IMPROVEMENT_PROGRESS.md
- [ ] Commit changes with clear message
- [ ] Note what to start next session

---

## 🔗 Key Files

**Context Files** (read first):
- `MCP_IMPROVEMENT_PROGRESS.md` - Full progress report
- `MCP_HEALTH_REPORT.md` - Current server status
- `MCP_NEXT_STEPS.md` - This file

**Work Files** (update as you go):
- `SERVER_REGISTRY.md` - Server documentation
- `docker-compose.yml` - Server configuration
- `docs/TROUBLESHOOTING.md` - Create this
- `docs/OPERATIONS.md` - Create this

**Reference Files** (completed work):
- `docs/TASK_ORCHESTRATOR_FIX.md` - Example of good documentation
- `.claude/workflows/*` - Workflow system (done)

---

**Time Estimate**: 7-12 hours remaining
**Suggested Split**: 2-3 sessions of 3-4 hours each
**Current Status**: Strong foundation, clear path forward
