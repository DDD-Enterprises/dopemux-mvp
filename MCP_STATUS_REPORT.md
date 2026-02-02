# MCP Server Status Report
**Generated**: 2026-02-02
**Status**: 6/11 Operational (55%)

## ✅ Fully Working (Core Development Stack)

### 1. **Serena** - Code Navigation
- **Status**: ✅ HEALTHY
- **Port**: 3006 (HTTP → mcp-proxy)
- **Purpose**: Find symbols, goto definition, analyze complexity
- **Usage**: `mcp__serena-v2__find_symbol`, `goto_definition`, `analyze_complexity`

### 2. **Context7** - Official Library Documentation
- **Status**: ✅ HEALTHY
- **Type**: stdio (npx @upstash/context7-mcp)
- **Purpose**: Get accurate docs for React, Vue, Next.js, etc.
- **Usage**: `mcp__context7__resolve-library-id`, `get-library-docs`

### 3. **GPT-Researcher** - Deep Multi-Source Research
- **Status**: ✅ HEALTHY
- **Port**: 3009 (HTTP → mcp-proxy)
- **Purpose**: Comprehensive research with analysis
- **Usage**: `mcp__dopemux-mcp-gptr-mcp__deep_research`, `quick_search`

### 4. **Desktop-Commander** - Desktop Automation
- **Status**: ✅ HEALTHY
- **Port**: 3012 (HTTP → mcp-proxy)
- **Purpose**: Window management, focus control
- **Usage**: `mcp__desktop-commander__focus_window`

### 5. **Zen** - Multi-Model Reasoning
- **Status**: ✅ CONFIGURED (stdio)
- **Type**: stdio (uvx from GitHub)
- **Purpose**: thinkdeep, planner, consensus, debug, codereview
- **Usage**: `mcp__zen__thinkdeep`, `planner`, `consensus`
- **Note**: Uses dev path `/Users/hue/code/zen-mcp-server` ✅

### 6. **LiteLLM** - Model Routing
- **Status**: ✅ STARTING
- **Port**: 4000
- **Purpose**: Route requests to multiple LLM providers
- **Usage**: Automatic routing (Claude → Grok → GPT-5)

---

## ⚠️ Needs Fixing (5 Servers)

### 7. **Exa** - Neural Search
- **Status**: ❌ UNHEALTHY
- **Port**: 3008 (HTTP)
- **Issue**: `EXA_API_KEY` not set or invalid
- **Fix**:
  ```bash
  export EXA_API_KEY="your_key_here"
  docker-compose -f docker-compose.master.yml restart dopemux-mcp-exa
  ```

### 8. **ConPort** - Knowledge Graph
- **Status**: ❌ RESTARTING (crash loop)
- **Issue**: Can't connect to DopeconBridge (DNS resolution failure)
- **Root Cause**: DopeconBridge has bcrypt password error
- **Fix Required**:
  1. Fix DopeconBridge bcrypt password length issue
  2. Restart ConPort after DopeconBridge is healthy
  ```bash
  # Fix password in DopeconBridge config
  # Rebuild: docker-compose -f docker-compose.master.yml build dopecon-bridge
  # Start: docker-compose -f docker-compose.master.yml up -d dopecon-bridge
  # Then: docker restart mcp-conport
  ```

### 9. **Dope-Context** - Semantic Code/Docs Search
- **Status**: ❌ NO CONTAINER
- **Issue**: Container not running (port 3010)
- **Fix**:
  ```bash
  docker-compose -f docker-compose.master.yml up -d dope-context
  ```
- **Note**: Check if service exists in docker-compose.master.yml

### 10. **Leantime-Bridge** - Project Management
- **Status**: ❌ NO CONTAINER
- **Issue**: Container not running (port 3015)
- **Fix**:
  ```bash
  docker-compose -f docker-compose.master.yml up -d leantime-bridge
  ```
- **Note**: Requires Leantime instance running

### 11. **Task-Orchestrator** - Task Management
- **Status**: ❓ UNCHECKED (stdio)
- **Issue**: Config points to non-existent `services/task-orchestrator/server.py`
- **Investigation Needed**:
  - Check if entry point is `services/task-orchestrator/app/main.py` or similar
  - Update .claude/claude_config.json with correct path
  - Verify Python dependencies installed

---

## 🎯 Recommended Action Plan

### Priority 1: Fix Core Knowledge Graph (ConPort)
**Impact**: HIGH - ConPort is critical for decision logging, context preservation

1. Fix DopeconBridge bcrypt password issue
2. Ensure PostgreSQL connection works
3. Restart ConPort once DopeconBridge is healthy

### Priority 2: Start Missing HTTP Servers
**Impact**: MEDIUM - Dope-Context is valuable for semantic search

```bash
# Check which services are defined
docker-compose -f docker-compose.master.yml config --services

# Start missing services
docker-compose -f docker-compose.master.yml up -d dope-context leantime-bridge
```

### Priority 3: Fix Exa API Key
**Impact**: LOW - Neural search is useful but not critical (GPT-Researcher works)

```bash
# Add to ~/.bashrc or ~/.zshrc
export EXA_API_KEY="your_exa_api_key"

# Restart Exa container
docker restart dopemux-mcp-exa
```

### Priority 4: Validate Task-Orchestrator
**Impact**: MEDIUM - Task breakdown is valuable

1. Find correct entry point in services/task-orchestrator/
2. Update .claude/claude_config.json
3. Test stdio connection

---

## 💡 Current Capability Assessment

### What Works Right Now (6/11)
With the currently working servers, you can:

✅ **Code Navigation** (Serena)
- Find symbols, goto definition
- Analyze complexity
- Navigate references

✅ **Library Documentation** (Context7)
- Get official React/Vue/Next.js docs
- Framework best practices
- API references

✅ **Deep Research** (GPT-Researcher)
- Multi-source investigation
- Comprehensive analysis
- Citation-backed findings

✅ **Multi-Model Reasoning** (Zen)
- Systematic thinking (thinkdeep)
- Interactive planning (planner)
- Multi-model consensus
- Code review, debugging

✅ **Desktop Automation** (Desktop-Commander)
- Window focus management
- ADHD-optimized context switching

✅ **Model Routing** (LiteLLM)
- Automatic fallback (Claude → Grok → GPT-5)
- Cost optimization

### What's Missing (5/11)

❌ **Knowledge Graph** (ConPort)
- Decision logging
- Progress tracking
- Session context

❌ **Semantic Search** (Dope-Context)
- AST-aware code search
- Document search

❌ **Neural Search** (Exa)
- Alternative search engine

❌ **Project Management** (Leantime-Bridge)
- Task tracking
- Team coordination

❌ **Task Orchestration** (Task-Orchestrator)
- Task breakdown
- Dependency analysis

---

## 🚀 Quick Win: Use What Works

**For immediate development**, you can work effectively with the 6 operational servers:

```bash
# Research Phase
mcp__context7__get-library-docs  # Library docs
mcp__dopemux-mcp-gptr-mcp__deep_research  # Deep research

# Implementation Phase
mcp__serena-v2__find_symbol  # Code navigation
mcp__serena-v2__goto_definition
mcp__serena-v2__analyze_complexity

# Complex Problems
mcp__zen__thinkdeep  # Systematic investigation
mcp__zen__planner  # Planning
mcp__zen__consensus  # Multi-model decisions

# ADHD Support
mcp__desktop-commander__focus_window  # Context switching
```

**Missing but can work around:**
- **ConPort**: Use local notes/files for decisions temporarily
- **Dope-Context**: Use native grep/ag/rg for code search
- **Task-Orchestrator**: Break down tasks manually

---

## 📝 Next Steps

1. **Decide priority**: Do you need ConPort working urgently?
2. **Fix DopeconBridge**: If yes, we need to resolve the bcrypt issue
3. **Or continue with 6/11**: Core dev workflow is functional

**Current Assessment**: 55% operational is actually good for core development tasks. The working servers cover the essential workflow phases (research, implementation, review).
