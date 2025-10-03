# MetaMCP Configuration - Post Claude Code Restart

**Status:** Ready to configure after Claude Code restart
**Time Required:** 15-20 minutes
**Prerequisites:** MetaMCP broker running on localhost:8091

---

## 🎯 Quick Start

After restarting Claude Code:

1. **Check MetaMCP is accessible:**
   ```bash
   curl http://localhost:8091/health
   ```

2. **Open MetaMCP Web UI:**
   ```
   http://localhost:12008
   ```

3. **Configure 5 role-based namespaces** (instructions below)

---

## 📋 Namespace Configuration Guide

### Namespace 1: `dopemux-quickfix` (8 Tools)
**Purpose:** 5-15 min quick wins, scattered attention, minimal cognitive load

**Servers to Add:**
- ✅ conport (HTTP: http://localhost:3004)
- ✅ serena (stdio: python /Users/hue/code/dopemux-mvp/services/serena/server.py)
- ✅ context7 (stdio: npx -y @context7/mcp-server)

**Tool-Level Filtering:**
- **ConPort** - Enable ONLY:
  - `log_progress`
  - `get_active_context`
  - `update_active_context`
- **Serena** - Enable ONLY:
  - `find_symbol`
  - `read_file`
  - `get_symbols_overview`
- **Context7** - Enable BOTH tools:
  - `resolve-library-id`
  - `get-library-docs`

**Total:** 8 tools ✅

---

### Namespace 2: `dopemux-act` (10 Tools)
**Purpose:** Coding, debugging, testing, refactoring

**Servers to Add:**
- ✅ conport (HTTP: http://localhost:3004)
- ✅ serena (stdio: python /Users/hue/code/dopemux-mvp/services/serena/server.py)
- ✅ zen (stdio via Claude Code config)
- ✅ context7 (stdio: npx -y @context7/mcp-server)

**Tool-Level Filtering:**
- **Serena** - Enable ONLY:
  - `find_symbol`
  - `find_referencing_symbols`
  - `get_symbols_overview`
  - `read_file`
  - `search_for_pattern`
- **ConPort** - Enable ONLY:
  - `log_progress`
  - `update_progress`
  - `get_active_context`
- **Zen** - Enable ONLY:
  - `debug`
  - `codereview`
- **Context7** - Both tools (optional, lower priority)

**Total:** 10 core tools ✅

---

### Namespace 3: `dopemux-plan` (9 Tools)
**Purpose:** Sprint planning, architecture decisions, ADR creation

**Servers to Add:**
- ✅ conport (HTTP: http://localhost:3004)
- ✅ zen (stdio via Claude Code config)
- ✅ context7 (stdio: npx -y @context7/mcp-server)

**Tool-Level Filtering:**
- **ConPort** - Enable ONLY:
  - `log_decision`
  - `get_decisions`
  - `search_decisions_fts`
  - `log_custom_data`
  - `semantic_search_conport`
- **Zen** - Enable ONLY:
  - `planner`
  - `consensus`
  - `thinkdeep`
  - `chat`
- **Context7** - Both tools

**Total:** 9 tools (11 with Context7) ✅

---

### Namespace 4: `dopemux-research` (10 Tools)
**Purpose:** Learning frameworks, technical research, exploration

**Servers to Add:**
- ✅ conport (HTTP: http://localhost:3004)
- ✅ zen (stdio via Claude Code config)
- ✅ context7 (stdio: npx -y @context7/mcp-server)
- ✅ serena (stdio: python /Users/hue/code/dopemux-mvp/services/serena/server.py)
- ✅ gpt-researcher (stdio: python /Users/hue/code/dopemux-mvp/services/dopemux-gpt-researcher/mcp-server/server.py)

**Tool-Level Filtering:**
- **Zen** - Enable ONLY:
  - `thinkdeep`
  - `chat`
  - `consensus`
- **ConPort** - Enable ONLY:
  - `log_decision`
  - `semantic_search_conport`
  - `log_custom_data`
  - `link_conport_items`
  - `get_linked_items`
- **Context7** - Both tools
- **Serena** - Enable ONLY:
  - `search_for_pattern`
  - `read_file`

**Total:** 10 core tools ✅

---

### Namespace 5: `dopemux-all` (60+ Tools)
**Purpose:** Exploratory work, multi-role tasks, full flexibility

**Servers to Add:**
- ✅ ALL 6 MCP servers (conport, serena, zen, context7, gpt-researcher, exa)

**Tool-Level Filtering:**
- **Enable ALL TOOLS** from all servers
- **Middleware:** Enable "Filter inactive tools" for automatic management

**Total:** 60+ tools with automatic filtering ✅

---

## 🔧 Step-by-Step Web UI Configuration

### Step 1: Access MetaMCP Web UI
1. Open browser: `http://localhost:12008`
2. Log in (if authentication enabled)

### Step 2: Create First Namespace (dopemux-quickfix)
1. Click **"Namespaces"** → **"Create Namespace"**
2. Name: `dopemux-quickfix`
3. Description: "ADHD-optimized quick wins (8 tools, scattered attention)"
4. Click **"Add Server"**
5. For ConPort:
   - Server Type: HTTP
   - URL: `http://localhost:3004`
   - Click **"Configure Tools"**
   - **Disable all** except: `log_progress`, `get_active_context`, `update_active_context`
   - Save
6. For Serena:
   - Server Type: stdio
   - Command: `python`
   - Args: `/Users/hue/code/dopemux-mvp/services/serena/server.py`
   - Click **"Configure Tools"**
   - **Disable all** except: `find_symbol`, `read_file`, `get_symbols_overview`
   - Save
7. For Context7:
   - Server Type: stdio
   - Command: `npx`
   - Args: `-y @context7/mcp-server`
   - Keep both tools enabled
   - Save
8. Click **"Create Namespace"**

### Step 3: Repeat for Other Namespaces
Follow same pattern for:
- `dopemux-act` (10 tools)
- `dopemux-plan` (9 tools)
- `dopemux-research` (10 tools)
- `dopemux-all` (60+ tools, all enabled)

### Step 4: Verify Tool Counts
1. Go to **"Namespaces"** → **"Inspector"**
2. Select each namespace
3. Verify tool count matches expected:
   - quickfix: 8 tools ✅
   - act: 10 tools ✅
   - plan: 9 tools ✅
   - research: 10 tools ✅
   - all: 60+ tools ✅

---

## 🎯 Usage After Configuration

**Quick Wins (Scattered Attention):**
```bash
# Switch to quickfix mode
sr quickfix
```

**Coding/Implementation:**
```bash
# Switch to act mode
sr act
```

**Planning/Architecture:**
```bash
# Switch to plan mode
sr plan
```

**Research/Learning:**
```bash
# Switch to research mode
sr research
```

**Full Flexibility:**
```bash
# Switch to all mode
sr all
```

---

## ⚠️ Troubleshooting

**MetaMCP not accessible:**
```bash
# Check if broker is running
docker ps | grep metamcp

# If not running, start it
docker-compose -f docker-compose.unified.yml up -d

# Check logs
docker logs dopemux-metamcp-broker
```

**Tool filtering not working:**
- Ensure you clicked "Configure Tools" for EACH server in EACH namespace
- Verify disabled tools show as greyed out in UI
- Re-save namespace after making changes

**Wrong tool count:**
- Use Inspector to list all tools in namespace
- Re-check tool filtering settings
- Disable tools that shouldn't be there

---

## 📊 Expected Results

After configuration:
- ✅ 5 namespaces created
- ✅ QUICKFIX: 8 tools (minimal cognitive load)
- ✅ ACT: 10 tools (code-focused)
- ✅ PLAN: 9 tools (strategic thinking)
- ✅ RESEARCH: 10 tools (investigation)
- ✅ ALL: 60+ tools (full flexibility)
- ✅ ADHD-optimized: Each role prevents tool overwhelm

**Configuration Complete!** 🎉

You can now use `sr <mode>` to switch between optimized toolsets based on your current attention state and task type.
