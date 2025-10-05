# MetaMCP Role-Based Configuration - Quick Start

**Status:** Ready for configuration
**MetaMCP:** Running at http://localhost:12008
**API Key:** sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY

---

## 🚀 10-Minute Setup

### Step 1: Access MetaMCP (1 min)

Open browser: **http://localhost:12008**

**First Time:**
- Click "Sign Up"
- Create account (any email/password)
- Login

**Returning:**
- Login with your credentials

---

### Step 2: Add 4 MCP Servers (5 min)

Click **"MCP Servers"** → **"Add Server"** for each:

**Server 1: conport**
```
Name: conport
Type: STDIO
Command: curl
Args (one per line):
  -X
  POST
  http://localhost:3004/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
```

**Server 2: context7**
```
Name: context7
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3002/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
```

**Server 3: zen**
```
Name: zen
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3003/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
```

**Server 4: serena**
```
Name: serena
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3006/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
```

---

### Step 3: Create 3 Namespaces (2 min)

Click **"Namespaces"** → **"Create Namespace"**

**Namespace 1: dopemux-quickfix**
- Name: `dopemux-quickfix`
- Description: `ADHD quick wins - 3 tools`
- Select servers: ☑ conport, ☑ serena, ☑ context7
- Click Save

**Namespace 2: dopemux-act**
- Name: `dopemux-act`
- Description: `Implementation mode - 4 tools`
- Select servers: ☑ conport, ☑ serena, ☑ context7, ☑ zen
- Click Save

**Namespace 3: dopemux-all**
- Name: `dopemux-all`
- Description: `All tools mode - full flexibility`
- Select servers: ☑ conport, ☑ serena, ☑ context7, ☑ zen
- Click Save

---

### Step 4: Create 3 Endpoints (2 min)

Click **"Endpoints"** → **"Create Endpoint"**

**Endpoint 1:**
- Endpoint ID: `quickfix-endpoint`
- Namespace: dopemux-quickfix
- Transport: SSE
- Authentication: API Key
- Use the API key already configured: `sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY`
- Click Save

**Endpoint 2:**
- Endpoint ID: `act-endpoint`
- Namespace: dopemux-act
- Transport: SSE
- Authentication: API Key
- Use same API key
- Click Save

**Endpoint 3:**
- Endpoint ID: `all-endpoint`
- Namespace: dopemux-all
- Transport: SSE
- Authentication: API Key
- Use same API key
- Click Save

---

### Step 5: Test Role Switching (2 min)

```bash
# Switch to QUICKFIX mode (3 tools)
~/.claude/switch-role.sh quickfix

# Restart Claude Code
exit
claude

# Verify
/mcp
# Should see: conport, serena, context7 tools

# Try ACT mode
~/.claude/switch-role.sh act
# Restart Claude Code
# Should see: conport, serena, context7, zen tools

# Try ALL mode
~/.claude/switch-role.sh all
# Should see all 4 servers
```

**Add alias for convenience:**
```bash
echo 'alias sr="~/.claude/switch-role.sh"' >> ~/.zshrc
source ~/.zshrc

# Now use: sr quickfix
```

---

## 🎯 Role Usage Guide

### QUICKFIX Mode (3 tools)
**When:** Scattered attention, 5-15 min tasks, need quick wins
**Tools:** conport (memory), serena (code nav), context7 (docs)
**Switch:** `sr quickfix`

### ACT Mode (4 tools)
**When:** Implementation, debugging, testing, focused work
**Tools:** conport, serena, context7, zen (debug/codereview)
**Switch:** `sr act`

### ALL Mode (4 tools in Phase 1A)
**When:** Exploratory work, learning, multi-role tasks
**Tools:** All 4 servers, full flexibility
**Switch:** `sr all`

---

## Verification

**Check MetaMCP is configured:**
```bash
curl -s http://localhost:12008/metamcp/quickfix-endpoint/sse \
  -H "Authorization: Bearer sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY"
```

**Check current Claude mode:**
```bash
cat ~/.claude/config/mcp_servers.json | grep "metamcp-"
# Shows: metamcp-quickfix, metamcp-act, or metamcp-all
```

---

## Troubleshooting

**Issue:** Can't access MetaMCP Web UI
```bash
# Check MetaMCP is running
docker ps | grep metamcp

# Restart if needed
cd metamcp && docker-compose restart
```

**Issue:** Role switch doesn't work
```bash
# Verify config files exist
ls -la ~/.claude/config/mcp_servers_*.json

# Check API key is set correctly
grep API_ACCESS_TOKEN ~/.claude/config/mcp_servers_quickfix.json
```

**Issue:** No tools showing after switch
```bash
# Verify MetaMCP endpoints created
# Visit: http://localhost:12008
# Check Endpoints section

# Try Inspector to test endpoint
# http://localhost:12008/inspector
```

---

**Estimated Time:** 10-15 minutes total
**Benefit:** <2 second role switching, optimized tool exposure for ADHD
**Status:** Infrastructure ready, needs Web UI clicks
