# MetaMCP PostgreSQL Debugging Guide

**Issue:** MetaMCP PostgreSQL container failing healthcheck
**Error:** "FATAL: could not write lock file 'postmaster.pid': No space left on device"
**Status:** Non-critical (MCP servers work without MetaMCP)
**Priority:** Medium (needed for role-based tool filtering)

---

## 🔍 Root Cause

**Error Message:**
```
FATAL: could not write lock file "postmaster.pid": No space left on device
PostgreSQL Database directory appears to contain a database; Skipping initialization
```

**Potential Causes:**
1. Docker Desktop disk space limit reached
2. Volume corruption from previous container
3. Filesystem permissions issue
4. MacOS specific Docker Desktop limitation

---

## 🔧 Debugging Steps (For Next Session)

### Step 1: Check Docker Desktop Disk Space

```bash
# Check Docker disk usage
docker system df

# Check Docker Desktop settings
# Open Docker Desktop → Settings → Resources → Disk image size
```

**Expected:** Should have several GB available
**If low:** Increase Docker Desktop disk allocation or clean up

### Step 2: Clean Docker System

```bash
# Remove unused images (reclaim ~22GB based on current)
docker image prune -a -f

# Remove unused volumes (reclaim ~1GB based on current)
docker volume prune -f

# Remove build cache (reclaim ~585MB based on current)
docker builder prune -af
```

### Step 3: Recreate MetaMCP Volume Fresh

```bash
cd /Users/hue/code/dopemux-mvp/metamcp

# Stop everything
docker-compose down -v

# Remove the specific volume
docker volume rm metamcp_postgres_data 2>/dev/null || true

# Recreate fresh
docker-compose up -d

# Monitor startup
docker logs -f metamcp-pg
```

**Success Indicators:**
- Should see: "database system is ready to accept connections"
- Health check: `docker ps | grep metamcp-pg` shows "(healthy)"
- Web UI: http://localhost:12008 loads

### Step 4: Check PostgreSQL Permissions

```bash
# Check volume mount permissions
docker volume inspect metamcp_postgres_data

# Check if volume is writable
docker run --rm -v metamcp_postgres_data:/data alpine sh -c "touch /data/test && rm /data/test && echo 'Volume writable' || echo 'Volume read-only'"
```

### Step 5: Alternative - Use Different Database

**Option A: Use dopemux-postgres-primary instead**

Edit `metamcp/.env`:
```
POSTGRES_HOST=dopemux-postgres-primary
# Or use IP: 172.18.0.X (check with docker inspect)
```

**Option B: Use external PostgreSQL**
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
# Point to dopemux-postgres-primary on host
```

**Option C: Skip MetaMCP entirely**
- MCP servers work great directly
- No role-based filtering, but all tools available
- Configuration already working in Claude

---

## 🎯 Recommended Debugging Order

**1. Check Docker Desktop Resources (2 min)**
- Disk image size sufficient? (need 64GB+)
- Memory allocation sufficient? (need 8GB+)

**2. Clean Docker System (5 min)**
```bash
docker system prune -af --volumes
# WARNING: This removes ALL unused Docker data
```

**3. Recreate MetaMCP Fresh (5 min)**
```bash
cd /Users/hue/code/dopemux-mvp/metamcp
docker-compose down -v
docker volume rm metamcp_postgres_data
docker-compose up -d
```

**4. If Still Fails: Use Alternative Database (10 min)**
- Point MetaMCP to dopemux-postgres-primary
- Create metamcp database manually
- Update connection string

---

## ⚠️ Important Notes

**MetaMCP is optional for basic functionality:**
- MCP servers work without it ✅
- Direct server access gives you all 60+ tools ✅
- Role-based filtering is a UX enhancement, not required ✅

**Value of fixing MetaMCP:**
- Tool-level filtering (8-10 tools per role vs 60+)
- Better ADHD cognitive load management
- Cleaner tool organization by role

**Current workaround:**
- Use Claude with all servers directly
- All functionality available
- Just more tools visible at once

---

## 📋 Debugging Checklist (Next Session)

- [ ] Check Docker Desktop disk space allocation
- [ ] Run docker system prune to reclaim space
- [ ] Remove and recreate metamcp_postgres_data volume
- [ ] Check PostgreSQL logs for detailed error
- [ ] Try alternative: point to dopemux-postgres-primary
- [ ] If all fails: Document MCP direct access as primary method

---

## 🚀 Current Working Solution

**While MetaMCP is being debugged, you have:**
- ✅ 8 MCP servers operational
- ✅ 60+ tools available directly
- ✅ ~/.claude/config/mcp_servers.json configured
- ✅ Ready to use immediately!

**Just restart Claude Code and you're live!** 🎯

---

**Estimated Debug Time:** 15-30 minutes in next session
**Current Functionality:** 100% (all MCP servers accessible)
**Priority:** Low-Medium (nice-to-have for role filtering)
