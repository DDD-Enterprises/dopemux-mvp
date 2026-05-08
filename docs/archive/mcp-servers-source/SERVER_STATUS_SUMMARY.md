# MCP Server Status Summary
**Last Updated**: 2026-02-06
**Overall Health**: 14/17 servers running (82%)

## 🎯 Quick Status Overview

| Category | Count | Status |
|----------|-------|--------|
| **Running & Healthy** | 14 | ✅ Operational |
| **Removed/Deprecated** | 1 | ❌ Cleaned up |
| **Needs Investigation** | 1 | ⚠️ Review required |
| **Optional/Unimplemented** | 1 | 🔵 Future consideration |

---

## ✅ Running & Healthy (14 servers)

### Critical Path Servers
| Server | Container | Port | Status | Purpose |
|--------|-----------|------|--------|---------|
| **pal** | dopemux-mcp-pal | 3003 | ✅ Healthy | Multi-tool analysis (apilookup, planner, thinkdeep, consensus, debug, codereviewer, secaudit) |
| **litellm** | dopemux-mcp-litellm | host | ✅ Healthy | LLM proxy with routing |

### Workflow Servers
| Server | Container | Port | Status | Purpose |
|--------|-----------|------|--------|---------|
| **task-orchestrator** | dopemux-mcp-task-orchestrator | 3014 | ✅ Healthy | 37 workflow tools for task management |
| **leantime-bridge** | dopemux-mcp-leantime-bridge | 3015 | ✅ Healthy | Project management integration |
| **plane-coordinator** | dopemux-mcp-plane-coordinator | 8090 | ✅ Healthy | Two-plane coordination API |

### Knowledge & Navigation
| Server | Container | Port | Status | Purpose |
|--------|-----------|------|--------|---------|
| **conport** | dope-decision-graph-bridge | 3016 | ✅ Healthy | Memory & decision graph |
| **serena-v2** | dopemux-mcp-serena | 3006, 4006 | ✅ Healthy | Code navigation (LSP) |
| **dope-context** | dopemux-mcp-dope-context | 3010 | ✅ Healthy | Semantic code/doc search |
| **context7** | dopemux-mcp-context7 | 3002 | ✅ Healthy | Official documentation |

### Research & Search
| Server | Container | Port | Status | Purpose |
|--------|-----------|------|--------|---------|
| **exa** | dopemux-mcp-exa | 3008 | ✅ Healthy | Neural web search |
| **gptr-mcp** | dopemux-mcp-gptr-mcp | 3009 | ✅ Healthy | GPT-Researcher bridge |

### Utilities
| Server | Container | Port | Status | Purpose |
|--------|-----------|------|--------|---------|
| **desktop-commander** | dopemux-mcp-desktop-commander | 3012 | ✅ Healthy | Desktop automation |
| **activity-capture** | dopemux-activity-capture | 8096 | ✅ Healthy | ADHD metrics tracking |

### Infrastructure
| Server | Container | Port | Status | Purpose |
|--------|-----------|------|--------|---------|
| **qdrant** | mcp-qdrant | 6333-6334 | ✅ Running | Vector database |

---

## ❌ Removed/Deprecated (1 server)

| Server | Reason | Replacement | Removed Date |
|--------|--------|-------------|--------------|
| **mas-sequential-thinking** | Incomplete implementation (only .env, no code) | Zen/pal multi-step reasoning | 2026-02-05 |

**Details**: Server was configured in docker-compose.yml but implementation never existed. Functionality provided by Zen and pal servers.

---

## ⚠️ Needs Investigation (1 server)

### mcp-client
- **Status**: Running but unstable (constant restarts)
- **Error**: "No response from MCP server"
- **Issue**: Trying to connect to stdio MCP servers that may not be configured
- **Required for**: task-master-ai and other stdio transport servers
- **Decision needed**: Mark as optional OR remove if not needed
- **Recommendation**: Mark as optional/experimental in docker-compose.yml

## 🔵 Optional/Experimental (1 server)

### task-master-ai
- **Status**: Not started (definition complete)
- **Type**: External wrapper (github.com/eyaltoledano/claude-task-master)
- **Purpose**: AI-powered task management and PRD processing
- **Tools**: decompose_task, score_complexity, suggest_order, estimate_time
- **Transport**: stdio (requires mcp-client)
- **Recommendation**: Can start for evaluation with `docker-compose up -d task-master-ai`
- **Note**: Not a duplicate of task-orchestrator (different tools, different transport)

---

## 🔧 How to Check Server Status

### Quick Health Check
```bash
# All servers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep dopemux

# Specific server
docker logs dopemux-mcp-pal --tail 20

# Health endpoint (for HTTP servers)
curl http://localhost:3003/health
```

### Common Commands
```bash
# Start all servers
docker-compose up -d

# Start specific server
docker-compose up -d pal

# Restart server
docker-compose restart pal

# View logs
docker-compose logs -f pal

# Stop all servers
docker-compose down
```

---

## 📊 Performance Metrics (Current)

| Metric | Value | Status |
|--------|-------|--------|
| **Total Servers Configured** | 17 | - |
| **Servers Running** | 13 | ✅ 76% |
| **Servers Healthy** | 13 | ✅ 100% of running |
| **Average Startup Time** | ~45s | 🟡 Could optimize |
| **Total Memory Usage** | ~2.5GB | ✅ Acceptable |
| **Response Time (avg)** | <1s | ✅ Fast |

---

## 🎯 Server Health Checklist

### Daily Health Check
- [ ] Run `docker ps | grep dopemux` - all expected containers running
- [ ] Check `docker-compose logs --tail 100` - no error patterns
- [ ] Verify critical path servers (pal, litellm) are healthy
- [ ] Test key workflow: pal apilookup → serena navigation → conport logging

### Weekly Maintenance
- [ ] Review server logs for warnings
- [ ] Check disk usage: `docker system df`
- [ ] Clean up old containers: `docker system prune`
- [ ] Update dependencies if needed
- [ ] Review and update this status summary

### Monthly Audit
- [ ] Performance profiling of all servers
- [ ] Review docker-compose.yml for zombie definitions
- [ ] Update server documentation
- [ ] Test disaster recovery procedures

---

## 🚨 Troubleshooting Quick Reference

| Issue | Quick Fix | Documentation |
|-------|-----------|---------------|
| Server won't start | Check logs: `docker logs <container>` | TROUBLESHOOTING.md (Section 2) |
| Port conflict | Check `docker ps` for port usage | TROUBLESHOOTING.md (Section 3) |
| Connection refused | Verify network: `docker network inspect dopemux-network` | TROUBLESHOOTING.md (Section 4) |
| High memory usage | Check `docker stats`, consider resource limits | OPERATIONS.md (Section 5) |
| Server unhealthy | Run health check endpoint, check dependencies | TROUBLESHOOTING.md (Section 6) |

---

## 📁 Related Documentation

- **Detailed Registry**: `SERVER_REGISTRY.md` - Complete server specifications
- **Troubleshooting**: `docs/TROUBLESHOOTING.md` - Common issues and solutions
- **Operations**: `docs/OPERATIONS.md` - Start/stop procedures and runbook
- **Audit Report**: `SERVER_AUDIT_2026-02-05.md` - Investigation findings
- **Completion Report**: `PRIORITY1_COMPLETE.md` - Fix summary and metrics

---

**Next Review**: 2026-02-12 (weekly)
**Maintained By**: Dopemux Infrastructure Team
**Report Issues**: Create GitHub issue with `infrastructure` label
