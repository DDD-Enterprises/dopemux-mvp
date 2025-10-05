# Role Switching Quick Start - Phase 1A

## Status: Ready for Testing

All scripts and configs created! You just need to:
1. Configure MetaMCP Web UI (10 min)
2. Paste API keys into config files (2 min)
3. Test role switching (<2s per switch!)

---

## Step 1: Access MetaMCP Web UI

**URL:** http://localhost:12008

**Login:**
- First time: Click "Sign Up" and create account
- Returning: Login with your credentials

---

## Step 2: Configure MCP Servers (5 min)

Click **"MCP Servers"** → **"Add Server"** and add these 4:

| Server Name | Port | Command | Args |
|-------------|------|---------|------|
| conport | 3004 | curl | -X, POST, http://localhost:3004/mcp, -H, Content-Type: application/json, -d, @- |
| context7 | 3002 | curl | -X, POST, http://localhost:3002/mcp, -H, Content-Type: application/json, -d, @- |
| zen | 3003 | curl | -X, POST, http://localhost:3003/mcp, -H, Content-Type: application/json, -d, @- |
| serena | 3006 | curl | -X, POST, http://localhost:3006/mcp, -H, Content-Type: application/json, -d, @- |

**For each server:**
- Type: STDIO
- Environment Variables: (leave empty)
- Click Save

---

## Step 3: Create Namespaces (2 min)

Click **"Namespaces"** → **"Create Namespace"**

### Namespace 1: dopemux-quickfix
- Name: `dopemux-quickfix`
- Description: `ADHD-optimized quick wins mode (3 tools)`
- Select servers: ☑ conport, ☑ serena, ☑ context7
- Click Save

### Namespace 2: dopemux-act
- Name: `dopemux-act`
- Description: `Implementation mode (4 tools)`
- Select servers: ☑ conport, ☑ serena, ☑ context7, ☑ zen
- Click Save

---

## Step 4: Create Endpoints (2 min)

Click **"Endpoints"** → **"Create Endpoint"**

### Endpoint 1: quickfix-endpoint
- Endpoint ID: `quickfix-endpoint`
- Namespace: Select `dopemux-quickfix`
- Transport: SSE
- Authentication: API Key
- Click **Generate API Key** → **COPY THE KEY!**
- Click Save

### Endpoint 2: act-endpoint
- Endpoint ID: `act-endpoint`
- Namespace: Select `dopemux-act`
- Transport: SSE
- Authentication: API Key
- Click **Generate API Key** → **COPY THE KEY!**
- Click Save

---

## Step 5: Update Config Files with API Keys (1 min)

**Edit these files and paste your API keys:**

File: `~/.claude/config/mcp_servers_quickfix.json`
```
Replace: "PASTE_YOUR_QUICKFIX_API_KEY_HERE"
With: Your actual quickfix-endpoint API key
```

File: `~/.claude/config/mcp_servers_act.json`
```
Replace: "PASTE_YOUR_ACT_API_KEY_HERE"
With: Your actual act-endpoint API key
```

---

## Step 6: Test Role Switching!

### Switch to QUICKFIX mode:
```bash
~/.claude/switch-role.sh quickfix
```

Then restart Claude Code:
```bash
exit  # or Ctrl+D
claude
/mcp  # Should see 3 tools from conport, serena, context7
```

### Switch to ACT mode:
```bash
~/.claude/switch-role.sh act
```

Restart Claude Code and verify 4 servers!

---

## What You Get

### QUICKFIX Mode (3 tools)
**Purpose:** 5-15 min quick wins, minimal cognitive load

Tools:
- conport - Track wins, maintain context
- serena - Fast code navigation (single-file focus)
- context7 - Quick API lookups

**When to use:** Scattered attention, need quick momentum

---

### ACT Mode (4 tools)
**Purpose:** Implementation, debugging, testing

Tools:
- conport - Progress tracking, decision linking
- serena - Full code navigation & LSP (max 10 results, 3-level depth)
- context7 - API documentation
- zen - Debug & code review (thinkdeep, debug, codereview tools)

**When to use:** Focused to hyperfocus, deep implementation work

---

### ALL Mode (4 tools in Phase 1A)
**Purpose:** Full flexibility, exploratory work, multi-role tasks

Tools (Phase 1A):
- conport - Decision logging & memory
- serena - Code navigation & LSP
- context7 - Documentation & API references
- zen - Multi-model orchestration (all tools)

**When to use:**
- Learning/exploring new areas
- Tasks that span multiple role types
- When you're not sure which mode you need
- Full flexibility needed

**Note:** More cognitive load than focused modes, but maximum capability

---

## Troubleshooting

**Issue: "No procedure found" error**
- MetaMCP requires authentication for API access
- Use Web UI instead (it's faster anyway!)

**Issue: Role switch doesn't work**
- Make sure you replaced API key placeholders in config files
- Restart Claude Code after switching
- Check: ls -la ~/.claude/config/mcp_servers*.json

**Issue: Can't access MetaMCP Web UI**
- Check MetaMCP is running: docker ps | grep metamcp
- Try: docker-compose -f metamcp/docker-compose.yml restart
- Logs: docker logs metamcp --tail 50

---

## Phase 1B & 1C (Coming Soon)

**When mas-sequential-thinking finishes building:**
- Add PLAN mode (6 tools)
- Enhance ACT mode (5 tools)

**When exa/gptr-mcp finish building:**
- Add RESEARCH mode (6 tools)
- Complete all 4 roles

---

## Quick Reference

**Role Switching Command:**
```bash
~/.claude/switch-role.sh [quickfix|act|all]
```

**Add Alias (optional):**
```bash
echo 'alias sr="~/.claude/switch-role.sh"' >> ~/.zshrc
source ~/.zshrc
# Now use: sr quickfix
```

**Available Modes (Phase 1A):**
- `quickfix` - 3 tools, minimal cognitive load
- `act` - 4 tools, implementation focus
- `all` - 4 tools, full flexibility

**Check Current Mode:**
```bash
cat ~/.claude/config/mcp_servers.json | grep "metamcp-"
# Shows: "metamcp-quickfix" or "metamcp-act"
```

---

Estimated Setup Time: 10-15 minutes total
Role Switch Time: <2 seconds (instant config swap!)
