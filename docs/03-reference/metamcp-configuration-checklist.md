# MetaMCP Configuration Checklist - Step-by-Step

**URL:** http://localhost:12008
**API Key:** sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY
**Time:** 30-40 minutes

---

## ✅ Pre-Flight Check

- [ ] MetaMCP running: http://localhost:12008 (should load)
- [ ] Logged in to MetaMCP
- [ ] 7 MCP servers healthy (run: `bash mcp_server_health_report.sh`)

---

## Step 1: Add 7 MCP Servers (15 min)

### Server 1: conport ✅
- [ ] Click "MCP Servers" → "Add Server"
- [ ] Name: `conport`
- [ ] Type: `STDIO`
- [ ] Command: `curl`
- [ ] Args (one per line):
  ```
  -X
  POST
  http://localhost:3004/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- [ ] Click "Save"
- [ ] Verify: Should show "conport" in server list

### Server 2: context7 ✅
- [ ] Click "Add Server"
- [ ] Name: `context7`
- [ ] Type: `STDIO`
- [ ] Command: `curl`
- [ ] Args:
  ```
  -X
  POST
  http://localhost:3002/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- [ ] Click "Save"

### Server 3: zen ✅
- [ ] Click "Add Server"
- [ ] Name: `zen`
- [ ] Type: `STDIO`
- [ ] Command: `curl`
- [ ] Args:
  ```
  -X
  POST
  http://localhost:3003/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- [ ] Click "Save"

### Server 4: serena ✅
- [ ] Click "Add Server"
- [ ] Name: `serena`
- [ ] Type: `STDIO`
- [ ] Command: `curl`
- [ ] Args:
  ```
  -X
  POST
  http://localhost:3006/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- [ ] Click "Save"

### Server 5: mas-sequential-thinking ✅
- [ ] Click "Add Server"
- [ ] Name: `mas-sequential-thinking`
- [ ] Type: `STDIO`
- [ ] Command: `docker`
- [ ] Args:
  ```
  exec
  -i
  mcp-mas-sequential-thinking
  python
  -m
  mcp_server_mas_sequential_thinking
  ```
- [ ] Click "Save"

### Server 6: exa ✅
- [ ] Click "Add Server"
- [ ] Name: `exa`
- [ ] Type: `STDIO`
- [ ] Command: `curl`
- [ ] Args:
  ```
  -X
  POST
  http://localhost:3008/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- [ ] Click "Save"

### Server 7: desktop-commander ✅
- [ ] Click "Add Server"
- [ ] Name: `desktop-commander`
- [ ] Type: `STDIO`
- [ ] Command: `curl`
- [ ] Args:
  ```
  -X
  POST
  http://localhost:3012/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- [ ] Click "Save"

**Checkpoint:** You should now have 7 servers in the MCP Servers list

---

## Step 2: Create QUICKFIX Namespace (5 min)

- [ ] Click "Namespaces" → "Create Namespace"
- [ ] Name: `dopemux-quickfix`
- [ ] Description: `ADHD quick wins - 8 tools, minimal cognitive load`
- [ ] Select servers: ☑ conport, ☑ serena, ☑ context7

### Configure Tool Filtering:

**For conport server:**
- [ ] Click tool configuration/settings
- [ ] **Enable ONLY:** log_progress, get_active_context, update_active_context
- [ ] Disable all other 22+ tools
- [ ] Save

**For serena server:**
- [ ] Click tool configuration/settings
- [ ] **Enable ONLY:** find_symbol, read_file, get_symbols_overview
- [ ] Disable all other 23 tools
- [ ] Save

**For context7 server:**
- [ ] Keep both tools enabled (only 2 tools total)
- [ ] Save

- [ ] Click "Save Namespace"
- [ ] **Verify:** Namespace shows "8 tools" or similar count

---

## Step 3: Create ACT Namespace (5 min)

- [ ] Click "Create Namespace"
- [ ] Name: `dopemux-act`
- [ ] Description: `Implementation mode - 10 tools for coding and debugging`
- [ ] Select servers: ☑ conport, ☑ serena, ☑ zen, ☑ context7

### Configure Tool Filtering:

**For serena:**
- [ ] **Enable ONLY:** find_symbol, find_referencing_symbols, get_symbols_overview, read_file, search_for_pattern
- [ ] Disable all others

**For conport:**
- [ ] **Enable ONLY:** log_progress, update_progress, get_active_context
- [ ] Disable all others

**For zen:**
- [ ] **Enable ONLY:** debug, codereview
- [ ] Disable: chat, thinkdeep, planner, consensus, precommit

**For context7:**
- [ ] Keep both enabled

- [ ] Save Namespace
- [ ] **Verify:** Should show ~10 tools

---

## Step 4: Create PLAN Namespace (5 min)

- [ ] Click "Create Namespace"
- [ ] Name: `dopemux-plan`
- [ ] Description: `Strategic planning - 9 tools for architecture and decisions`
- [ ] Select servers: ☑ conport, ☑ zen, ☑ context7

### Configure Tool Filtering:

**For conport:**
- [ ] **Enable ONLY:** log_decision, get_decisions, search_decisions_fts, log_custom_data, semantic_search_conport
- [ ] Disable all progress/pattern tools

**For zen:**
- [ ] **Enable ONLY:** planner, consensus, thinkdeep, chat
- [ ] Disable: debug, codereview, precommit

**For context7:**
- [ ] Keep both enabled

- [ ] Save Namespace
- [ ] **Verify:** Should show 9 tools

---

## Step 5: Create RESEARCH Namespace (5 min)

- [ ] Click "Create Namespace"
- [ ] Name: `dopemux-research`
- [ ] Description: `Research mode - 10 tools for investigation and learning`
- [ ] Select servers: ☑ conport, ☑ zen, ☑ context7, ☑ serena

### Configure Tool Filtering:

**For zen:**
- [ ] **Enable ONLY:** thinkdeep, chat, consensus
- [ ] Disable: planner, debug, codereview, precommit

**For conport:**
- [ ] **Enable ONLY:** log_decision, semantic_search_conport, log_custom_data, link_conport_items, get_linked_items
- [ ] Disable progress tools

**For serena:**
- [ ] **Enable ONLY:** search_for_pattern, read_file
- [ ] Disable all navigation/editing tools

**For context7:**
- [ ] Keep both enabled

- [ ] Save Namespace

---

## Step 6: Create ALL Namespace (2 min)

- [ ] Click "Create Namespace"
- [ ] Name: `dopemux-all`
- [ ] Description: `All tools mode - 60+ tools with automatic filtering`
- [ ] Select servers: ☑ ALL 7 SERVERS
- [ ] **Enable ALL tools** for all servers
- [ ] Enable middleware: ☑ "Filter inactive tools"
- [ ] Save Namespace

---

## Step 7: Create 5 Endpoints (5 min)

### Endpoint 1: quickfix-endpoint
- [ ] Click "Endpoints" → "Create Endpoint"
- [ ] Endpoint ID: `quickfix-endpoint`
- [ ] Namespace: Select `dopemux-quickfix`
- [ ] Transport: `SSE`
- [ ] Authentication: `API Key`
- [ ] API Key: `sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY`
- [ ] Save

### Endpoint 2: act-endpoint
- [ ] Create Endpoint
- [ ] Endpoint ID: `act-endpoint`
- [ ] Namespace: `dopemux-act`
- [ ] Transport: `SSE`
- [ ] Auth: `API Key`
- [ ] Same API key
- [ ] Save

### Endpoint 3: plan-endpoint
- [ ] Create Endpoint
- [ ] Endpoint ID: `plan-endpoint`
- [ ] Namespace: `dopemux-plan`
- [ ] Transport: `SSE`
- [ ] Auth: `API Key`
- [ ] Same API key
- [ ] Save

### Endpoint 4: research-endpoint
- [ ] Create Endpoint
- [ ] Endpoint ID: `research-endpoint`
- [ ] Namespace: `dopemux-research`
- [ ] Transport: `SSE`
- [ ] Auth: `API Key`
- [ ] Same API key
- [ ] Save

### Endpoint 5: all-endpoint
- [ ] Create Endpoint
- [ ] Endpoint ID: `all-endpoint`
- [ ] Namespace: `dopemux-all`
- [ ] Transport: `SSE`
- [ ] Auth: `API Key`
- [ ] Same API key
- [ ] Save

---

## Step 8: Test in Inspector (5 min)

- [ ] Click "Inspector"
- [ ] Select `quickfix-endpoint`
- [ ] Click "Connect"
- [ ] **Verify:** Should see exactly 8 tools (conport:3, serena:3, context7:2)
- [ ] Repeat for other endpoints

---

## Step 9: Enable Idle Server Initialization (1 min)

- [ ] Click "Settings"
- [ ] Find "Idle Server Initialization"
- [ ] ☑ Enable
- [ ] Save

---

## Step 10: Test Role Switching (5 min)

```bash
# Switch to QUICKFIX
~/.claude/switch-role.sh quickfix

# Exit and restart Claude Code
exit
claude

# Check tools
/mcp
# Should see: 8 tools from conport, serena, context7

# Try ACT mode
~/.claude/switch-role.sh act
# Restart Claude
# Should see: 10 tools

# Try ALL mode
~/.claude/switch-role.sh all
# Should see: 60+ tools
```

---

## ✅ Completion Checklist

- [ ] 7 servers added to MetaMCP
- [ ] 5 namespaces created with tool filtering
- [ ] 5 endpoints created with API key
- [ ] Tested in Inspector (tool counts verified)
- [ ] Idle server initialization enabled
- [ ] Role switching tested in Claude Code
- [ ] All 5 modes work (<2s switching confirmed)

---

**When complete, you'll have:**
- ✅ 5 role modes with optimal tool exposure
- ✅ <2 second role switching
- ✅ ADHD-optimized cognitive load management
- ✅ 60+ tools available across all modes

**Start here:** http://localhost:12008

**Reference:** `METAMCP_TOOL_MAPPING_FINAL.md` for exact tool lists

Let me know when you're ready to test! 🚀
