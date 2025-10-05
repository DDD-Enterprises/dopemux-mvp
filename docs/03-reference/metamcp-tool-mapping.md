# MetaMCP Tool Mapping - Definitive Configuration

**Purpose:** Exact tool selections for each role to configure in MetaMCP Web UI
**Constraint:** 8-10 tools max per role (ADHD cognitive load optimization)
**Method:** Tool-level filtering within namespaces

---

## 🎯 QUICKFIX Mode (8 Tools) - Scattered Attention

**Purpose:** 5-15 min quick wins, minimal cognitive load, momentum building
**Attention State:** Scattered
**Complexity:** Simple tasks only

### Tool Selection

**ConPort (3 tools):**
1. `log_progress` - Track quick wins and maintain momentum
2. `get_active_context` - Understand where you left off
3. `update_active_context` - Save current state quickly

**Serena (3 tools):**
4. `find_symbol` - Fast symbol navigation
5. `read_file` - Quick code reading
6. `get_symbols_overview` - Understand file structure at a glance

**Context7 (2 tools):**
7. `resolve-library-id` - Look up library documentation
8. `get-library-docs` - Get API reference quickly

**Excluded Servers:** zen, mas-sequential-thinking, exa, desktop-commander, gptr-mcp
**Rationale:** Heavy reasoning/research tools create cognitive overload for scattered attention

---

## 💻 ACT Mode (10 Tools) - Implementation

**Purpose:** Coding, debugging, testing, refactoring
**Attention State:** Focused to Hyperfocus
**Complexity:** Moderate to Complex tasks

### Tool Selection

**Serena (5 tools):**
1. `find_symbol` - Navigate to definitions
2. `find_referencing_symbols` - Find all usages
3. `get_symbols_overview` - Understand file structure
4. `read_file` - Read code
5. `search_for_pattern` - Search across codebase

**ConPort (3 tools):**
6. `log_progress` - Track implementation progress
7. `update_progress` - Mark tasks complete
8. `get_active_context` - Maintain session context

**Zen (2 tools):**
9. `debug` - Systematic debugging assistance
10. `codereview` - Code review before committing

**Context7 (2 tools - lower priority, can access if needed):**
- `resolve-library-id`
- `get-library-docs`

**Optional:** desktop-commander tools for automation
**Excluded:** Heavy research tools (gptr-mcp, exa), heavy planning tools
**Rationale:** Focus on code intelligence and debugging, not research or planning

---

## 📐 PLAN Mode (9 Tools) - Strategic Thinking

**Purpose:** Sprint planning, architecture decisions, ADR creation
**Attention State:** Focused strategic thinking
**Complexity:** High-level design

### Tool Selection

**ConPort (5 tools):**
1. `log_decision` - Log architectural decisions
2. `get_decisions` - Review past decisions
3. `search_decisions_fts` - Full-text search decisions
4. `log_custom_data` - Store sprint goals, epics
5. `semantic_search_conport` - Semantic search across all memory

**Zen (4 tools):**
6. `planner` - Break down complex plans
7. `consensus` - Multi-model decision validation
8. `thinkdeep` - Deep architectural analysis
9. `chat` - Collaborative thinking partner

**Context7 (2 tools):**
10. `resolve-library-id` - Research framework options
11. `get-library-docs` - Evaluate library capabilities

**Optional when deployed:**
- mas-sequential-thinking (multi-step reasoning)
- gptr-mcp (deep research)
- exa (web research)

**Excluded Servers:** serena (code navigation not needed in pure planning)
**Rationale:** Strategic thinking requires decision tools and reasoning, not code navigation

---

## 🔬 RESEARCH Mode (10 Tools) - Deep Investigation

**Purpose:** Learning new frameworks, technical research, exploration
**Attention State:** Focused research mode
**Complexity:** Learning and discovery

### Tool Selection

**Zen (3 tools):**
1. `thinkdeep` - Deep analysis of concepts
2. `chat` - Explore ideas and ask questions
3. `consensus` - Validate understanding with multiple perspectives

**ConPort (5 tools):**
4. `log_decision` - Capture research findings
5. `semantic_search_conport` - Search existing knowledge
6. `log_custom_data` - Store research notes
7. `link_conport_items` - Connect findings to decisions
8. `get_linked_items` - Explore knowledge graph

**Context7 (2 tools):**
9. `resolve-library-id` - Look up libraries
10. `get-library-docs` - Study documentation

**Serena (2 tools - for studying code patterns):**
- `search_for_pattern` - Find code examples
- `read_file` - Study implementations

**Optional when deployed:**
- gptr-mcp (autonomous deep research)
- exa (web search)

**Excluded:** Heavy implementation tools, file editing
**Rationale:** Research mode focuses on learning and analysis, not implementation

---

## 🌐 ALL Mode (All Tools) - Full Flexibility

**Purpose:** Exploratory work, multi-role tasks, when unsure which mode to use
**Attention State:** Variable
**Complexity:** Full range

### Tool Selection

**All Servers Enabled:**
- ✅ conport - All 25+ tools
- ✅ serena - All 26 tools
- ✅ zen - All 7 tools
- ✅ context7 - All 2 tools
- ✅ mas-sequential-thinking - All reasoning tools
- ✅ exa - All web search tools
- ✅ desktop-commander - All automation tools
- ⏸️ gptr-mcp - All research tools (when healthy)
- ⏸️ claude-context - All semantic search tools (when deployed)

**Total:** 60+ tools

**Middleware:** Enable "Filter inactive tools" to reduce context automatically
**Rationale:** Maximum capability but with automatic filtering to manage cognitive load

---

## 📋 MetaMCP Configuration Instructions

### Step 1: Create Servers in MetaMCP

For each of the 7 operational servers, add to MetaMCP with configurations from METAMCP_COMPLETE_SETUP.md

### Step 2: Create Namespaces with Tool Filtering

**Namespace 1: dopemux-quickfix**
- Servers: conport, serena, context7
- **Enable ONLY these tools:**
  - ConPort: log_progress, get_active_context, update_active_context
  - Serena: find_symbol, read_file, get_symbols_overview
  - Context7: resolve-library-id, get-library-docs
- Total: 8 tools

**Namespace 2: dopemux-act**
- Servers: conport, serena, zen, context7, desktop-commander (optional)
- **Enable ONLY these tools:**
  - Serena: find_symbol, find_referencing_symbols, get_symbols_overview, read_file, search_for_pattern
  - ConPort: log_progress, update_progress, get_active_context
  - Zen: debug, codereview
  - Context7: resolve-library-id, get-library-docs (lower priority)
- Total: 10 core tools (12 with Context7)

**Namespace 3: dopemux-plan**
- Servers: conport, zen, context7, mas-sequential-thinking (optional), gptr-mcp (optional), exa (optional)
- **Enable ONLY these tools:**
  - ConPort: log_decision, get_decisions, search_decisions_fts, log_custom_data, semantic_search_conport
  - Zen: planner, consensus, thinkdeep, chat
  - Context7: resolve-library-id, get-library-docs
- Total: 9 core tools (expand when mas-sequential-thinking, gptr, exa added)

**Namespace 4: dopemux-research**
- Servers: conport, zen, context7, serena, gptr-mcp (optional), exa (optional)
- **Enable ONLY these tools:**
  - Zen: thinkdeep, chat, consensus
  - ConPort: log_decision, semantic_search_conport, log_custom_data, link_conport_items, get_linked_items
  - Context7: resolve-library-id, get-library-docs
  - Serena: search_for_pattern, read_file
- Total: 10 core tools (expand when gptr-mcp, exa added)

**Namespace 5: dopemux-all**
- Servers: ALL 7 operational servers
- **Enable:** ALL TOOLS
- Middleware: "Filter inactive tools" enabled
- Total: 60+ tools with automatic filtering

---

## 🔧 Tool-Level Filtering in MetaMCP Web UI

**How to configure:**

1. Go to Namespace → Select server
2. Click "Configure Tools" or "Tool Settings"
3. **Disable all tools EXCEPT the ones listed above**
4. Save namespace

**Example for dopemux-quickfix namespace:**
- Select conport server
- Disable all tools except: log_progress, get_active_context, update_active_context
- Select serena server
- Disable all tools except: find_symbol, read_file, get_symbols_overview
- Select context7 server
- Keep both tools enabled
- Save

---

## 📊 Tool Count Verification

After configuring each namespace, use MetaMCP Inspector to verify:

**Expected tool counts:**
- quickfix-endpoint: 8 tools
- act-endpoint: 10-12 tools
- plan-endpoint: 9 tools (11+ with optional servers)
- research-endpoint: 10-12 tools
- all-endpoint: 60+ tools

If you see more tools than expected, review the tool filtering settings in the namespace configuration.

---

## 🎯 Usage Recommendations

**Scattered Attention (5-15 min sessions):**
```bash
sr quickfix  # 8 tools, minimal load
```

**Implementation Work (25-45 min sessions):**
```bash
sr act  # 10 tools, code-focused
```

**Planning Sessions (45-90 min sessions):**
```bash
sr plan  # 9 tools, strategic thinking
```

**Research/Learning (30-60 min sessions):**
```bash
sr research  # 10 tools, investigation-focused
```

**Exploration/Multi-role Work:**
```bash
sr all  # 60+ tools, full flexibility
```

---

**Configuration Time:** 30-40 minutes with tool-level filtering
**Benefit:** Optimal cognitive load management with precise tool exposure per role
**ADHD Optimization:** Maximum tool count kept to 8-10 per focused role
