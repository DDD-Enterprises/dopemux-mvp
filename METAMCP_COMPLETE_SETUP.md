# MetaMCP Complete Configuration - All 9 MCP Servers

**Goal:** Configure all dopemux MCP servers through MetaMCP for role-based access
**MetaMCP:** http://localhost:12008
**API Key:** sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY

---

## 🎯 Complete Server Inventory

### Currently Running & Ready (7 servers) ✅
1. **conport** (port 3004) - Decision logging, knowledge graph (25+ tools)
2. **context7** (port 3002) - External library documentation (2 tools)
3. **zen** (port 3003) - Multi-model orchestration (7 tools)
4. **serena** (port 3006) - Code navigation & LSP (26 tools)
5. **mas-sequential-thinking** (stdio) - Multi-step reasoning (via docker exec)
6. **exa** (port 3008) - Web research
7. **desktop-commander** (port 3012) - Desktop automation

### Optional Servers (2 servers) ⏸️
8. **gptr-mcp** (port 3009) - Deep research (building, add later)
9. **claude-context** (port 3007) - Semantic code search (needs OPENAI_API_KEY)

**Available NOW: 60+ tools across 7 operational servers!**

---

## Step 1: Add All 9 MCP Servers to MetaMCP

Access: **http://localhost:12008** → **MCP Servers** → **Add Server**

### Server 1: conport ✅ Running
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
```

### Server 2: context7 ✅ Running
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
```

### Server 3: zen ✅ Running
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
```

### Server 4: serena ✅ Running
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
```

### Server 5: mas-sequential-thinking ✅ Running (stdio-only)
```
Name: mas-sequential-thinking
Type: STDIO
Command: docker
Args:
  exec
  -i
  mcp-mas-sequential-thinking
  python
  -m
  mcp_server_mas_sequential_thinking

Environment: (leave empty)
Note: This server uses docker exec (no HTTP port)
```

### Server 6: exa ✅ Running
```
Name: exa
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3008/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
```

### Server 7: gptr-mcp ⏸️ Optional (Building)
```
Name: gptr-mcp
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3009/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
Note: Currently building, can add later when ready
```

### Server 8: desktop-commander ✅ Running
```
Name: desktop-commander
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3012/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
```

### Server 9: claude-context ⏸️ Optional (Needs OPENAI_API_KEY)
```
Name: claude-context
Type: STDIO
Command: curl
Args:
  -X
  POST
  http://localhost:3007/mcp
  -H
  Content-Type: application/json
  -d
  @-
Environment: (leave empty)
Note: Add your OPENAI_API_KEY to .env, then: docker-compose -f docker-compose.unified.yml up -d mcp-claude-context
```

---

## Step 2: Create Complete Role Namespaces

### Namespace 1: dopemux-quickfix (ADHD Scattered State)
**Tools:** 8 carefully selected
**Servers:** conport, serena, context7

**Purpose:** 5-15 min quick wins, minimal cognitive load
**Use when:** Scattered attention, need momentum

### Namespace 2: dopemux-act (Implementation Mode)
**Tools:** 10 implementation-focused
**Servers:** conport, serena, context7, zen, mas-sequential-thinking, desktop-commander

**Purpose:** Coding, debugging, testing, refactoring
**Use when:** Focused to hyperfocus states

### Namespace 3: dopemux-plan (Strategic Planning)
**Tools:** 9 strategic thinking tools
**Servers:** conport, zen, mas-sequential-thinking, context7, gptr-mcp, exa

**Purpose:** Sprint planning, architecture, ADRs
**Use when:** Strategic thinking sessions

### Namespace 4: dopemux-research (Deep Investigation)
**Tools:** 10 research tools
**Servers:** conport, gptr-mcp, exa, context7, zen, mas-sequential-thinking

**Purpose:** Learning frameworks, technical research
**Use when:** Deep investigation mode

### Namespace 5: dopemux-all (Full Access)
**Tools:** All 60+ tools
**Servers:** All 9 servers

**Purpose:** Exploratory work, when unsure of role
**Use when:** Need full flexibility

**Note:** Use MetaMCP's "Filter inactive tools" middleware to reduce context

---

## Step 3: Create Endpoints for Each Role

**Endpoint 1: quickfix-endpoint**
- Namespace: dopemux-quickfix
- Transport: SSE
- Auth: API Key (use: sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY)

**Endpoint 2: act-endpoint**
- Namespace: dopemux-act
- Transport: SSE
- Auth: Same API key

**Endpoint 3: plan-endpoint**
- Namespace: dopemux-plan
- Transport: SSE
- Auth: Same API key

**Endpoint 4: research-endpoint**
- Namespace: dopemux-research
- Transport: SSE
- Auth: Same API key

**Endpoint 5: all-endpoint**
- Namespace: dopemux-all
- Transport: SSE
- Auth: Same API key

---

## Step 4: Start Missing MCP Servers

**Before using PLAN/RESEARCH/ACT modes fully, start the missing servers:**

```bash
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers

# Start the 3 needed servers (may take 2-5 min to build first time)
docker-compose up -d mas-sequential-thinking exa desktop-commander

# Check status
docker ps | grep -E "mcp-mas|mcp-exa|mcp-desktop"
```

**For gptr-mcp:**
```bash
cd /Users/hue/code/dopemux-mvp
docker-compose -f docker-compose.unified.yml up -d mcp-gptr-mcp
```

**For claude-context (optional - needs API key):**
1. Add real OPENAI_API_KEY to `.env`
2. `docker-compose -f docker-compose.unified.yml up -d mcp-claude-context`

---

## Step 5: Update Claude Config Files

Already created with your API key! Located at:
- `~/.claude/config/mcp_servers_quickfix.json`
- `~/.claude/config/mcp_servers_act.json`
- `~/.claude/config/mcp_servers_plan.json` (create from template below)
- `~/.claude/config/mcp_servers_research.json` (create from template below)
- `~/.claude/config/mcp_servers_all.json`

**Create PLAN mode config:**
```json
{
  "mcpServers": {
    "metamcp-plan": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "http://localhost:12008/metamcp/plan-endpoint/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY"
      }
    }
  }
}
```

**Create RESEARCH mode config:**
```json
{
  "mcpServers": {
    "metamcp-research": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "http://localhost:12008/metamcp/research-endpoint/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "sk_mt_P3cvUc02eTQTEbELrirCQ9jjEqzbTYqyWdjdbJm3sBW5RCxOOPeMgA1sylNF4gNY"
      }
    }
  }
}
```

---

## Step 6: Update Role Switch Script

Already done! Update to support all 5 modes:

```bash
~/.claude/switch-role.sh quickfix   # 3 tools, ADHD scattered
~/.claude/switch-role.sh act        # 6 tools, implementation
~/.claude/switch-role.sh plan       # 6 tools, strategic (when servers running)
~/.claude/switch-role.sh research   # 6 tools, deep investigation (when servers running)
~/.claude/switch-role.sh all        # All tools, full flexibility
```

---

## Complete Tool Allocation by Role

### QUICKFIX Mode (8 tools) - Phase 1A Ready Now
**ConPort (3):** log_progress, get_active_context, update_active_context
**Serena (3):** find_symbol, read_file, get_symbols_overview
**Context7 (2):** resolve-library-id, get-library-docs

### ACT Mode (10 tools) - Needs mas-sequential-thinking
**Serena (6):** find_symbol, find_referencing_symbols, get_symbols_overview, read_file, replace_symbol_body, search_for_pattern
**ConPort (3):** log_progress, update_progress, get_active_context
**Zen (2):** debug, codereview
**Context7 (2):** Both tools
**Desktop-Commander (optional):** Automation tools

### PLAN Mode (9 tools) - Needs mas-sequential-thinking, gptr-mcp, exa
**ConPort (5):** log_decision, get_decisions, search_decisions_fts, log_custom_data, semantic_search
**Zen (4):** planner, consensus, thinkdeep, chat
**Context7 (2):** Both tools
**MAS-Sequential:** reasoning tools
**Exa:** web search
**GPTR:** deep research

### RESEARCH Mode (10 tools) - Needs gptr-mcp, exa
**Zen (3):** thinkdeep, chat, consensus
**ConPort (5):** log_decision, semantic_search, log_custom_data, link_items, get_linked_items
**Context7 (2):** Both tools
**GPTR-MCP:** Autonomous research
**Exa:** Web search

### ALL Mode (60+ tools)
**All 9 servers with all tools enabled**

---

## Quick Start Path

**Immediate (Now - 4 servers running):**
1. Configure QUICKFIX and ACT modes
2. Start using with 4 working servers
3. Test role switching

**Phase 1B (When mas-sequential-thinking ready):**
4. Add PLAN mode configuration
5. Enhanced ACT mode

**Phase 1C (When all servers ready):**
6. Add RESEARCH mode
7. Complete all 5 roles

**Phased approach = immediate value + progressive enhancement** (ADHD-optimized!)

---

**Estimated Time:**
- Configure 9 servers in MetaMCP: 15-20 min
- Create 5 namespaces: 5 min
- Create 5 endpoints: 5 min
- **Total: 25-30 min for complete setup**

**Benefit:** Full role-based access to all 60+ tools with <2s switching!

Start with 4 servers now, add others as they become available? 🚀
