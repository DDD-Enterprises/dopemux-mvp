---
id: DOPEMUX_ARCHITECTURE_OVERVIEW
title: Dopemux Architecture Overview
type: explanation
owner: '@hu3mann'
date: '2025-10-01'
author: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
prelude: "Comprehensive architecture documentation for the Dopemux platform, an ADHD-optimized development environment with multi-layer cognitive services."
---
# 🧠 Dopemux Architecture Overview
## The Complete Guide to ADHD-Optimized Development

**Version**: 2.0
**Created**: October 2025
**Purpose**: Comprehensive documentation of the Dopemux platform

---

## 📚 Table of Contents

1. [What is Dopemux?](#what-is-dopemux)
1. [High-Level Architecture](#high-level-architecture)
1. [Core Layers](#core-layers)
1. [Major Subsystems](#major-subsystems)
1. [MCP Servers](#mcp-servers)
1. [Services](#services)
1. [Data Flow](#data-flow)
1. [Technology Stack](#technology-stack)

---

## 🎯 What is Dopemux?

Dopemux is a **development platform designed specifically for developers with ADHD**. It wraps Claude Code (Anthropic's AI coding assistant) with intelligent context management, persistent memory, and ADHD-optimized accommodations.

### The Problem It Solves

**Traditional Development Pain Points for ADHD Developers:**
- 😵 Forgetting what you were working on after interruptions
- 🌀 Context switching destroys flow state
- 🔥 Hyperfocus sessions lead to burnout (no break reminders)
- 📉 Energy crashes make complex tasks impossible
- 🧩 Too many scattered tools and windows
- 💭 Mental overhead of tracking everything manually

**Dopemux Solution:**
- 🧠 Automatic context capture and restoration
- 📊 Persistent knowledge graph across sessions
- ⚡ Real-time energy and attention state tracking
- 🛡️ Hyperfocus protection and break management
- 🎯 Unified dashboard in your terminal (tmux)
- 🤖 AI that adapts to your cognitive state

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         👤 DEVELOPER (You!)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    🖥️  TERMINAL INTERFACE (tmux)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Statusline  │  │  Dashboard   │  │  Panes/Logs  │                  │
│  │  (Top Bar)   │  │  (Metrics)   │  │  (Output)    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       🧠 CORE DOPEMUX PLATFORM                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                  CLI & Command Layer                            │    │
│  │         (dopemux start, dopemux init, etc.)                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   ADHD      │  │   Instance  │  │   Profile   │  │   Worktree   │  │
│  │   Engine    │  │   Manager   │  │   Manager   │  │   Manager    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘  │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   Claude    │  │   LiteLLM   │  │    Event    │  │  Embeddings  │  │
│  │   Config    │  │   Proxy     │  │    Bus      │  │   Engine     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        🔌 MCP SERVERS LAYER                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ ConPort │  │ Serena  │  │   Zen   │  │   Exa   │  │  GPTR   │      │
│  │   KG    │  │  LSP    │  │  Agent  │  │ Search  │  │Research │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                   │
│  │Desktop  │  │Leantime │  │PAL apilookup │  │Sequential│                   │
│  │Commander│  │ Bridge  │  │  MCP    │  │Thinking │                   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       🛠️  SERVICES LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ADHD Engine   │  │Task Router   │  │Orchestrator  │                  │
│  │(Monitoring)  │  │(Priorities)  │  │(Coordination)│                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │Break         │  │Session Intel │  │Energy Trends │                  │
│  │Suggester     │  │(Learning)    │  │(Tracking)    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      🌐 EXTERNAL SERVICES                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Claude API   │  │ OpenRouter   │  │     XAI      │                  │
│  │(Anthropic)   │  │(Multi-Model) │  │   (Grok)     │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Postgres    │  │  ChromaDB    │  │   Voyage AI  │                  │
│  │(ConPort DB)  │  │(Embeddings)  │  │ (Embeddings) │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Philosophy

**Layered Design:**
1. **Interface Layer** - What you see (tmux, statusline)
1. **Core Platform** - Dopemux logic and orchestration
1. **MCP Servers** - AI tools and capabilities
1. **Services** - Background intelligence and automation
1. **External** - Third-party APIs and databases

**Key Principles:**
- 🔌 **Modular** - Each component is independent
- 🔄 **Event-Driven** - Components communicate via event bus
- 🎯 **ADHD-First** - Every feature designed for neurodivergent brains
- 📊 **Context-Aware** - Everything knows your current state
- 🛡️ **Fault-Tolerant** - Graceful degradation if services fail

---

## 🎯 Core Layers - Deep Dive

### Layer 1: Interface Layer (What You See)

```
┌─────────────────────────────────────────────────────────────────┐
│  🖥️  TMUX - Your Command Center                                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  STATUSLINE (Top Bar - Always Visible)                    │ │
│  │  dopemux-mvp main | 📊 Auth system [2h] | ⚡= 👁️● | 64%  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────┬────────────┬──────────┬──────────┐                │
│  │ Pane 1  │  Pane 2    │  Pane 3  │  Pane 4  │                │
│  │         │            │          │          │                │
│  │ Claude  │ Dashboard  │  Logs    │  Shell   │                │
│  │ Code    │ (Metrics)  │ (Debug)  │  (Cmd)   │                │
│  │         │            │          │          │                │
│  │ AI      │ Energy:    │ ConPort: │ git      │                │
│  │ Chat    │  ⚡↑ High  │ ✅ Active│ status   │                │
│  │         │ Focus:     │ Serena:  │          │                │
│  │ [edit]  │  👁️● On   │ ✅ Ready │ $        │                │
│  └─────────┴────────────┴──────────┴──────────┘                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  SESSION INFO (Bottom - Optional)                         │ │
│  │  Session: feature-auth | Started: 2h 15m ago              │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**What Happens Here:**
- **Statusline**: Updates every 5 seconds with current context
- **Claude Pane**: Where you interact with AI
- **Dashboard Pane**: Real-time metrics (energy, focus, breaks)
- **Logs Pane**: Debug output from services
- **Shell Pane**: Normal terminal commands

**Key Files:**
- `src/dopemux/tmux/` - Tmux integration
- `scripts/statusline/` - Statusline rendering
- `dashboard/` - Dashboard widgets

---

### Layer 2: Core Dopemux Platform

This is the brain of Dopemux - the orchestration layer that makes everything work together.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CORE DOPEMUX COMPONENTS                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CLI (Command Line Interface)                            │  │
│  │  • dopemux start                                         │  │
│  │  • dopemux init                                          │  │
│  │  • dopemux tmux start                                    │  │
│  │  • dopemux profile                                       │  │
│  │  • dopemux worktree                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐  │
│  │              │              │              │             │  │
│  │ ADHD ENGINE  │   INSTANCE   │   PROFILE    │  WORKTREE   │  │
│  │              │   MANAGER    │   MANAGER    │  MANAGER    │  │
│  │ Monitor      │              │              │             │  │
│  │ attention,   │ Multi-       │ Python-ML,   │ Git branch  │  │
│  │ energy,      │ instance     │ Rust-Fast,   │ isolation   │  │
│  │ breaks,      │ isolation    │ Web-React    │ for         │  │
│  │ context      │ (port mgmt)  │ profiles     │ parallel    │  │
│  │              │              │              │ work        │  │
│  └──────────────┴──────────────┴──────────────┴─────────────┘  │
│                           ↓                                     │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐  │
│  │              │              │              │             │  │
│  │ CLAUDE       │   LITELLM    │    EVENT     │ EMBEDDINGS  │  │
│  │ CONFIG       │   PROXY      │    BUS       │  ENGINE     │  │
│  │              │              │              │             │  │
│  │ Generate     │ Route to     │ Pub/sub      │ Semantic    │  │
│  │ .claude.json │ alternative  │ for loose    │ search      │  │
│  │ with MCP     │ providers    │ coupling     │ across      │  │
│  │ servers      │ (Grok, OR)   │ of services  │ codebase    │  │
│  │              │              │              │             │  │
│  └──────────────┴──────────────┴──────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.1 ADHD Engine

**Purpose**: Real-time monitoring and accommodation for ADHD-specific needs

**Components:**
```
adhd/
├── attention_monitor.py     # Track focus/scatter states
├── context_manager.py       # Save/restore work context
├── task_decomposer.py       # Break down big tasks
└── break_scheduler.py       # Smart break reminders
```

**What It Does:**
- 👁️ Monitors your attention state (focused, scattered, hyperfocus)
- ⚡ Tracks energy levels over time
- ☕ Suggests breaks based on your patterns
- 📊 Learns your optimal work rhythms
- 🛡️ Protects hyperfocus from interruptions

**Data Flow:**
1. Monitors keystrokes, git commits, Claude interactions
1. ML model predicts attention state
1. Updates statusline in real-time
1. Triggers accommodations (break alerts, task simplification)

---

#### 2.2 Instance Manager

**Purpose**: Run multiple isolated Dopemux sessions in parallel

**Why?**
ADHD developers often work on multiple things simultaneously. Instance Manager lets you:
- �� Switch between projects without losing context
- 🎯 One Claude session per feature branch
- 🚀 Separate environments (dev, staging, production)

**How It Works:**
```
Instance A (port 3000)          Instance B (port 3030)
├── Claude on port 3456         ├── Claude on port 3486
├── ConPort on port 3004        ├── ConPort on port 3034
├── Serena on port 3006         ├── Serena on port 3036
├── LiteLLM on port 4000        ├── LiteLLM on port 4030
└── Worktree: feature-auth      └── Worktree: bugfix-login
```

**Key Files:**
- `src/dopemux/instance_manager.py` - Port allocation
- `src/dopemux/instance_state.py` - State persistence
- `.dopemux/instances_cache.json` - Active instances

---

#### 2.3 Profile Manager

**Purpose**: Pre-configured setups for different project types

**Available Profiles:**
```
python-ml           → Python + ML libraries + Jupyter
rust-fast           → Rust + cargo + performance tools
web-react           → React + Node + TypeScript
backend-api         → FastAPI + PostgreSQL + REST
fullstack           → All of the above combined
minimal             → Just the basics
```

**What Profiles Configure:**
- 📦 Which MCP servers to enable
- 🤖 Default model selection
- ⚙️ Claude Code settings
- 🛠️ Tool availability
- 📊 Dashboard layout

**Key Files:**
- `src/dopemux/profile_manager.py` - Profile logic
- `profiles/*.yaml` - Profile definitions
- `src/dopemux/profile_wizard.py` - Interactive setup

---

#### 2.4 Worktree Manager

**Purpose**: Git worktree integration for parallel work

**Traditional Git Problem:**
```
You're in feature-auth branch, halfway through coding...
Boss: "Fix production bug NOW!"
You: 😱 Stash? Commit WIP? Switch branches? Lose context?
```

**Dopemux Worktree Solution:**
```
main/ (production codebase)
├── feature-auth/              ← Worktree 1 (Instance A)
│   └── [your WIP code intact]
└── hotfix-prod-bug/           ← Worktree 2 (Instance B)
    └── [emergency fix]
```

**Commands:**
```bash
dopemux worktree create feature-auth   # New worktree + instance
dopemux worktree list                  # Show all worktrees
dopemux worktree switch feature-auth   # Jump between contexts
dopemux worktree recover               # Resume orphaned sessions
```

**Key Files:**
- `src/dopemux/worktree_manager_enhanced.py` - Core logic
- `src/dopemux/worktree_recovery.py` - Session restoration
- `src/dopemux/protection_interceptor.py` - Prevent main branch edits

---

#### 2.5 Claude Config Generator

**Purpose**: Dynamically generate Claude Code configuration

**Problem:**
Claude Code uses a static `.claude.json` config file. Dopemux needs to:
- Enable/disable MCP servers based on profile
- Pass environment variables
- Configure different models per instance

**Solution:**
```python
# Dopemux generates this on-the-fly:
{
  "mcpServers": {
    "conport": {
      "command": "docker exec -i mcp-conport ...",
      "env": {
        "WORKSPACE_ID": "/Users/hue/code/dopemux-mvp",
        "INSTANCE_ID": "A"
      }
    },
    "serena": { ... },
    "zen": { ... }
  },
  "env": {
    "ADHD_FOCUS_DURATION": "45",
    "ADHD_BREAK_INTERVAL": "15"
  }
}
```

**Key Files:**
- `src/dopemux/claude_config.py` - Config generation
- `src/dopemux/claude/launcher.py` - Claude Code launching
- `src/dopemux/claude/configurator.py` - MCP server setup

---

#### 2.6 LiteLLM Proxy

**Purpose**: Route Claude requests to alternative providers

**Why?**
- 💰 Claude Pro Max expired? Use Grok/GPT-5/Minimax
- 🔄 Automatic fallbacks if primary model fails
- 💸 Cost optimization (free models available)

**How It Works:**
```
Claude Code Request
    ↓
http://localhost:4000 (LiteLLM)
    ↓
┌─────────────┐
│ LiteLLM     │  Checks config:
│ Router      │  • What model did they request?
└─────────────┘  • Is it available?
    ↓            • Any fallbacks?
    ├─→ Direct XAI (Grok)
    ├─→ OpenRouter (GPT-5, O3, Minimax)
    └─→ Anthropic (if API key present)
```

**Configuration:**
- `.dopemux/litellm/A/litellm.config.yaml` - Model routing
- `src/dopemux/litellm_proxy.py` - Proxy manager
- See `QUICK_START_ROUTING.md` for setup

---

#### 2.7 Event Bus

**Purpose**: Decouple services via publish/subscribe

**Example Flow:**
```
1. User commits code
   ↓
1. Git hook publishes "code_committed" event
   ↓
1. Subscribers react:
   ├─→ ConPort: Index new code in knowledge graph
   ├─→ ADHD Engine: Update productivity metrics
   ├─→ Break Suggester: "Good stopping point?"
   └─→ Session Intel: Learn from commit patterns
```

**Benefits:**
- 🔌 Services don't need to know about each other
- 🚀 Parallel processing of events
- 🛡️ Services can fail independently

**Key Files:**
- `src/dopemux/events/` - Event bus implementation
- `services/*/event_handlers.py` - Event subscribers

---

#### 2.8 Embeddings Engine

**Purpose**: Semantic search across your codebase

**What It Does:**
- 📝 Converts code to vector embeddings
- 🔍 Find similar code by meaning (not just keywords)
- 🧠 Powers ConPort's "related code" suggestions

**Providers:**
- Voyage AI (high quality, paid)
- OpenAI embeddings (fallback)
- Local models (planned)

**Key Files:**
- `src/dopemux/embeddings/` - Embedding pipeline
- `src/dopemux/embeddings/providers/voyage.py` - Voyage integration
- `src/dopemux/embeddings/storage/` - Vector storage

---

## 🔌 MCP Servers - AI Capabilities Layer

MCP (Model Context Protocol) servers are AI tools that Claude Code can use. Each server provides specific capabilities.

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP SERVERS ECOSYSTEM                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ConPort - Context Portal & Knowledge Graph             │   │
│  │  The brain - persistent memory of your codebase         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐     │
│  │          │          │          │          │          │     │
│  │  Serena  │   Zen    │   Exa    │   GPTR   │Desktop   │     │
│  │   LSP    │  Agent   │  Search  │Research  │Commander │     │
│  │          │          │          │          │          │     │
│  │ Code     │ Multi-   │ Web      │ Deep     │ Computer │     │
│  │ Intel    │ provider │ search   │ research │ control  │     │
│  │          │ routing  │ engine   │ reports  │          │     │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘     │
│                                                                 │
│  ┌──────────┬──────────┬──────────┬──────────────┐             │
│  │          │          │          │              │             │
│  │Leantime  │PAL apilookup  │Sequential│   (More)     │             │
│  │ Bridge   │   MCP    │Thinking  │              │             │
│  │          │          │          │              │             │
│  │ PM       │ Semantic │ Chain of │  Extensible  │             │
│  │ integration│ context │ thought │  via Docker  │             │
│  └──────────┴──────────┴──────────┴──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 🧠 ConPort - Context Portal (The Crown Jewel)

**What It Is:**
A persistent knowledge graph that remembers EVERYTHING about your codebase across sessions.

**Capabilities:**
```
┌─────────────────────────────────────────────────────────┐
│  ConPort Knowledge Graph (PostgreSQL + AGE Extension)   │
│                                                         │
│  📁 Code Structure          🔗 Relationships           │
│  • Files & directories      • Function calls           │
│  • Classes & functions      • Import dependencies      │
│  • Variables & types        • Inheritance chains       │
│                                                         │
│  📊 Decision Log            🎯 Context Tracking        │
│  • Why you made changes     • What you're working on   │
│  • Trade-offs considered    • Current focus area       │
│  • Alternative approaches   • Recent file edits        │
│                                                         │
│  🔍 Semantic Search         ⏳ History                 │
│  • Find by meaning          • Code evolution over time │
│  • Similar patterns         • Decision backtracking    │
│  • Related concepts         • Who changed what when    │
└─────────────────────────────────────────────────────────┘
```

**Example Queries ConPort Can Answer:**
- "Show me all authentication-related code"
- "What files depend on UserService?"
- "Why did we choose JWT over sessions?" (from decision log)
- "What was I working on before the interrupt?"
- "Find code similar to this function"

**Architecture:**
```
┌──────────────┐
│ Claude Code  │  "Find all auth code"
└──────────────┘
       ↓
┌──────────────┐
│ ConPort MCP  │  Receives request
│   Server     │
└──────────────┘
       ↓
┌──────────────┐
│   GraphQL    │  Query engine
│   Resolver   │
└──────────────┘
       ↓
┌──────────────┐
│ PostgreSQL   │  SELECT * FROM code_graph
│  + AGE       │  WHERE type = 'auth'
└──────────────┘
       ↓
  [Results back to Claude]
```

**Files:**
- `docker/mcp-servers/conport/` - MCP server
- `services/conport/` - Core service
- `services/conport_kg/` - Knowledge graph engine
- `services/conport-bridge/` - HTTP API bridge

**Docker Container:**
- Name: `mcp-conport` (or `mcp-conport_B` for instance B)
- Port: 3004 (base) + instance offset
- Database: `dopemux-postgres-age`

---

### 🔍 Serena - LSP Intelligence

**What It Is:**
Language Server Protocol integration for deep code understanding.

**Capabilities:**
- 💡 Go-to-definition across files
- 🔎 Find all references to a symbol
- 📝 Hover documentation
- ✨ Auto-completion suggestions
- 🎨 Semantic highlighting
- 🔧 Refactoring support

**Supported Languages:**
- Python (Pyright)
- TypeScript/JavaScript (TS Server)
- Rust (rust-analyzer)
- Go (gopls)
- More via LSP protocol

**Architecture:**
```
Claude asks: "Show me all usages of UserModel"
    ↓
Serena MCP Server
    ↓
Language Server (Pyright)
    ↓
Scans codebase with AST
    ↓
Returns all locations
    ↓
Claude formats response
```

**Files:**
- `docker/mcp-servers/serena/` - MCP wrapper
- `services/serena/` - Core LSP integration

**Why It's Important:**
Without Serena, Claude can only "see" files you show it. With Serena, Claude can navigate your entire codebase like an IDE.

---

### 🎭 Zen - Multi-Provider Routing Agent

**What It Is:**
Intelligent routing to different AI providers based on task type.

**Routing Logic:**
```
┌─────────────────────────────────────────────────┐
│  Task Type              → Best Provider         │
├─────────────────────────────────────────────────┤
│  Code generation        → GPT-5-Codex           │
│  Deep reasoning         → O3-Deep-Research      │
│  Fast responses         → Grok-4-Fast           │
│  Cost optimization      → Minimax-M2-Free       │
│  Research/analysis      → Claude Opus           │
└─────────────────────────────────────────────────┘
```

**Capabilities:**
- 🔄 Auto-fallback if provider fails
- 💰 Cost tracking per provider
- ⚡ Performance monitoring
- 🎯 Task-specific model selection

**Files:**
- `docker/mcp-servers/zen/` - MCP server
- `zen/providers/` - Provider implementations

---

### 🌐 Exa - Web Search Engine

**What It Is:**
AI-powered web search for research and documentation.

**Use Cases:**
- 📚 Find up-to-date API documentation
- 🐛 Search Stack Overflow for similar bugs
- 📰 Get latest news on technologies
- 🔍 Research best practices

**Example:**
```
Claude: "How do I use React Server Components?"
    ↓
Exa MCP: Search web for "React Server Components tutorial"
    ↓
Returns: Top 5 articles with summaries
    ↓
Claude: Synthesizes answer from multiple sources
```

**Files:**
- `docker/mcp-servers/exa/` - MCP server
- API: Exa.ai search API

---

### 📝 GPTR - GPT Researcher

**What It Is:**
Autonomous research agent that generates comprehensive reports.

**What It Does:**
1. Takes a research question
1. Breaks it down into sub-questions
1. Searches web for each sub-question
1. Synthesizes findings into structured report
1. Includes citations and sources

**Example Output:**
```
Research: "Best practices for PostgreSQL performance in Python"

Report Generated:
1. Connection Pooling
- Use pgbouncer or SQLAlchemy pool
- Recommended pool size: 2x CPU cores
- Source: [PostgreSQL Docs]

1. Query Optimization
- Always use prepared statements
- Index foreign keys
- Source: [High Performance PostgreSQL]

1. Async I/O
- Use asyncpg for async Python
- 3x faster than psycopg2
- Source: [Benchmark Study]

[Full 2000-word report with citations]
```

**Files:**
- `docker/mcp-servers/gptr-mcp/` - MCP wrapper
- Uses GPT Researcher library

---

### 🖥️ Desktop Commander

**What It Is:**
Control your computer from Claude Code (macOS/Linux).

**Capabilities:**
- 📂 File operations (create, move, delete)
- 🚀 Launch applications
- 📸 Take screenshots
- ⌨️ Send keystrokes
- 🖱️ Control mouse
- 📋 Clipboard management

**Safety:**
- ⚠️ Requires explicit permissions
- 🔒 Sandboxed operations
- 📝 Audit log of all actions

**Use Cases:**
- "Open browser and navigate to localhost:3000"
- "Take screenshot of error message"
- "Create project directory structure"

**Files:**
- `docker/mcp-servers/desktop-commander/` - MCP server

**⚠️ Security Note:**
Only enable this if you trust Claude. It has significant computer control.

---

### 📊 Leantime Bridge

**What It Is:**
Integration with Leantime project management software.

**Capabilities:**
- 📋 Create tasks from Claude
- ✅ Update task status
- 📊 View project timeline
- 👥 Assign tasks to team members
- 💬 Add comments to tasks

**Workflow:**
```
Claude: "Create task: Implement user authentication"
    ↓
Leantime Bridge MCP
    ↓
Leantime API: POST /api/task
    ↓
Task created with ID #123
    ↓
Claude: "Task #123 created. Ready to start?"
```

**Files:**
- `docker/mcp-servers/leantime-bridge/` - MCP server
- Leantime instance (self-hosted or cloud)

---

### 🧩 PAL apilookup MCP

**What It Is:**
Advanced semantic context management (by Zilliz/Milvus team).

**Capabilities:**
- 📊 Semantic chunking of code
- 🔍 Vector similarity search
- 🧠 Context-aware code retrieval
- 🎯 Intelligent context windows

**Files:**
- `docker/mcp-servers/claude-context/` - MCP server
- Uses Chroma/Milvus vector DB

---

### 🤔 Sequential Thinking MCP

**What It Is:**
Multi-agent system for complex reasoning.

**How It Works:**
```
Complex Problem
    ↓
Break into steps (Planner Agent)
    ↓
Execute each step (Executor Agent)
    ↓
Verify results (Validator Agent)
    ↓
Synthesize solution (Integrator Agent)
```

**Use Cases:**
- Architecture design
- Complex debugging
- Multi-step refactoring
- System analysis

**Files:**
- `docker/mcp-servers/mas-sequential-thinking/` - MCP server

---

## 🛠️ Services Layer - Background Intelligence

Services run continuously in the background, monitoring and learning from your work patterns.

```
┌──────────────────────────────────────────────────────────────┐
│                    SERVICES ECOSYSTEM                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           ADHD Engine (Central Intelligence)           │ │
│  │  • Attention monitoring  • Energy tracking             │ │
│  │  • Context preservation  • Pattern learning            │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │          │          │          │          │          │  │
│  │   Task   │   Break  │ Session  │  Energy  │Activity  │  │
│  │  Router  │Suggester │  Intel   │  Trends  │ Capture  │  │
│  │          │          │          │          │          │  │
│  │ Priority │ Prevent  │ Learn    │ Track    │ Log what │  │
│  │ mgmt     │ burnout  │ patterns │ cycles   │ you did  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                                                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │          │          │          │          │          │  │
│  │Orchestra-│Workspace │Interrupt │  DDDPG   │Monitoring│  │
│  │  tor     │ Watcher  │  Shield  │ Engine   │Dashboard │  │
│  │          │          │          │          │          │  │
│  │ Coord    │ File     │ Protect  │Decision  │ Visual   │  │
│  │ all svcs │ monitor  │ focus    │ graphs   │ metrics  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 🧠 ADHD Engine (services/adhd_engine/)

**The Central Intelligence System**

```
┌─────────────────────────────────────────────────────────┐
│                    ADHD ENGINE                          │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  INPUT SIGNALS                                │     │
│  │  • Keystrokes/min                            │     │
│  │  • Git commits (frequency & size)            │     │
│  │  • Claude interactions                        │     │
│  │  • File switches                              │     │
│  │  • Time of day                                │     │
│  │  • Break history                              │     │
│  └───────────────────────────────────────────────┘     │
│                      ↓                                  │
│  ┌───────────────────────────────────────────────┐     │
│  │  MACHINE LEARNING MODEL                       │     │
│  │  • Attention state classifier                 │     │
│  │  • Energy level predictor                     │     │
│  │  • Optimal break time finder                  │     │
│  │  • Pattern recognition                        │     │
│  └───────────────────────────────────────────────┘     │
│                      ↓                                  │
│  ┌───────────────────────────────────────────────┐     │
│  │  OUTPUTS                                      │     │
│  │  • Statusline updates                        │     │
│  │  • Break suggestions                          │     │
│  │  • Accommodation triggers                     │     │
│  │  • Dashboard metrics                          │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

**Key Components:**
- `attention_tracker.py` - Focus/scatter detection
- `energy_estimator.py` - Cognitive energy prediction
- `rhythm_analyzer.py` - Learn your work patterns
- `accommodation_engine.py` - Trigger supports

**Data Storage:**
- SQLite: `.dopemux/adhd_engine.db`
- Metrics history (7 days by default)

---

### 📋 Task Router (services/task-router/)

**What It Does:**
Intelligently prioritizes and routes tasks based on current state.

**Routing Logic:**
```
Incoming Task: "Implement authentication"
    ↓
Check Current State:
• Energy: Low ⚡↓
• Attention: Scattered 👁️🌀
• Time to break: 10 minutes
    ↓
Decision: "Task too complex for current state"
    ↓
Alternatives Suggested:
1. "Write tests for existing auth (simpler)"
1. "Review auth requirements (no coding)"
1. "Take a break, tackle this after"
```

**Priority Algorithm:**
```python
priority = (
    task_urgency * 0.4 +
    energy_match * 0.3 +    # High energy for complex tasks
    context_fit * 0.2 +     # Related to current work
    time_estimate * 0.1     # Fits in remaining time
)
```

**Files:**
- `services/task-router/router_api.py` - HTTP API
- `services/task-router/priority_engine.py` - Scoring logic

---

### ☕ Break Suggester (services/break-suggester/)

**What It Does:**
Prevents burnout with intelligent break suggestions.

**Break Types:**
```
┌──────────────────────────────────────────────────┐
│  Micro-break (2-5 min)                           │
│  • Look away from screen                         │
│  • Stretch                                       │
│  • Triggered: Every 25-30 minutes                │
├──────────────────────────────────────────────────┤
│  Short break (10-15 min)                         │
│  • Walk around                                   │
│  • Hydrate/snack                                 │
│  • Triggered: Every 90 minutes                   │
├──────────────────────────────────────────────────┤
│  Long break (30-60 min)                          │
│  • Meal                                          │
│  • Exercise                                      │
│  • Triggered: After 3-4 hours                    │
├──────────────────────────────────────────────────┤
│  Hyperfocus cooldown (15-20 min)                 │
│  • Decompress                                    │
│  • Process what you learned                      │
│  • Triggered: After hyperfocus detected          │
└──────────────────────────────────────────────────┘
```

**Smart Features:**
- 🎯 Respects natural stopping points (after commits, test passes)
- 🛡️ Never interrupts during hyperfocus (unless urgent)
- 📊 Learns your preferred break patterns
- ⚠️ Escalates warnings if ignored

**Notification Levels:**
```
Level 1: ☕ (gentle suggestion in statusline)
Level 2: ☕! (stronger suggestion + dashboard alert)
Level 3: ☕!! (popup notification)
Level 4: ☕!!! (screen dim + mandatory break)
```

**Files:**
- `services/break-suggester/suggester.py` - Core logic
- `services/break-suggester/patterns.py` - Pattern learning

---

### 🧠 Session Intelligence (services/session_intelligence/)

**What It Does:**
Learns from your work sessions to improve future suggestions.

**What It Tracks:**
```
Session Data:
• What you worked on
• How long you focused
• When you took breaks
• Energy patterns throughout day
• Productive vs. struggling times
• Context switches
• Interruption sources
```

**Machine Learning:**
```
Training Data: Past 30 days of sessions
    ↓
Models Trained:
• Optimal work duration predictor
• Best time-of-day for complex tasks
• Break timing optimizer
• Energy pattern forecaster
    ↓
Predictions:
• "You're most productive 10am-12pm"
• "Take breaks every 45 minutes"
• "Avoid complex tasks after 3pm"
```

**Files:**
- `services/session_intelligence/learner.py` - ML models
- `services/session_intelligence/analyzer.py` - Pattern analysis

---

### ⚡ Energy Trends (services/energy-trends/)

**What It Does:**
Long-term tracking of cognitive energy patterns.

**Visualizations:**
```
Energy Over Time (7 days):
⚡⚡ |     ▄▄
⚡↑ |   ▄▄  ▀▀▄▄
⚡= | ▄▄        ▀▀▄
⚡↓ |              ▀▄
    Mon Tue Wed Thu Fri Sat Sun

Patterns Detected:
• Highest energy: Tue/Wed 10am-1pm
• Crashes: Daily around 3pm
• Recovery: After 30min walks
```

**Insights:**
- 📈 Trend analysis (improving or declining)
- 🔍 Correlation detection (sleep, exercise, breaks)
- ⚠️ Burnout prediction
- 💡 Optimization suggestions

**Files:**
- `services/energy-trends/tracker.py` - Data collection
- `services/energy-trends/analyzer.py` - Trend analysis

---

### 🎯 Activity Capture (services/activity-capture/)

**What It Does:**
Logs everything you do for accountability and analysis.

**Captured Activities:**
```
08:45 - Session started (project: dopemux-mvp)
08:47 - File edited: src/dopemux/cli.py
08:52 - Git commit: "Add profile command"
08:55 - Claude query: "How to validate YAML?"
09:10 - Break taken (5 minutes)
09:15 - File edited: src/dopemux/profile_manager.py
09:30 - Tests run: pytest tests/test_profile.py
09:35 - Context switch: Checked Slack
09:40 - Focus resumed: Back to profile work
```

**Reports Generated:**
- Daily summary
- Weekly productivity report
- Context switch analysis
- Time tracking per project

**Privacy:**
- All data stored locally
- No external transmission
- Can be disabled per-profile

**Files:**
- `services/activity-capture/logger.py` - Event logging
- `services/activity-capture/reporter.py` - Report generation

---

### 🎼 Orchestrator (services/orchestrator/)

**What It Does:**
Coordinates all services and ensures they work together.

**Responsibilities:**
```
┌───────────────────────────────────────────┐
│  Service Health Monitoring                │
│  • Check if services are running          │
│  • Restart crashed services               │
│  • Report status to dashboard             │
├───────────────────────────────────────────┤
│  Event Routing                            │
│  • Distribute events to subscribers       │
│  • Handle event ordering                  │
│  • Manage event queue                     │
├───────────────────────────────────────────┤
│  Resource Management                      │
│  • Prevent resource conflicts             │
│  • Throttle heavy operations              │
│  • Load balancing                         │
└───────────────────────────────────────────┘
```

**Service Dependencies:**
```
Orchestrator starts:
1. Database (Postgres)
1. ConPort (needs DB)
1. Serena (independent)
1. ADHD Engine (needs ConPort)
1. Task Router (needs ADHD Engine)
1. Break Suggester (needs ADHD Engine)
1. All other services
```

**Files:**
- `services/orchestrator/coordinator.py` - Main orchestrator
- `services/orchestrator/health.py` - Health checks

---

### 🔒 Interruption Shield (services/interruption-shield/)

**What It Does:**
Protects your focus from interruptions.

**Protection Modes:**
```
┌─────────────────────────────────────────────┐
│  Normal Mode                                │
│  • Notifications: Allowed                   │
│  • Alerts: Shown                            │
├─────────────────────────────────────────────┤
│  Focus Mode (Focused 👁️●)                  │
│  • Notifications: Delayed 15 minutes        │
│  • Non-urgent alerts: Hidden                │
├─────────────────────────────────────────────┤
│  Deep Focus (Hyperfocus 👁️✨)              │
│  • All notifications: BLOCKED               │
│  • Only critical alerts (system errors)     │
│  • Auto-responses: "In deep focus"          │
└─────────────────────────────────────────────┘
```

**Features:**
- 🔕 Do Not Disturb integration (macOS/Linux)
- 📧 Email auto-responder
- 💬 Slack status updater
- 🎯 Whitelist for critical contacts

**Files:**
- `services/interruption-shield/shield.py` - Core protection
- `services/interruption-shield/rules.py` - Filtering rules

---

### 📊 DDDPG - Decision-Driven Development Planning Graph (services/dddpg/)

**What It Does:**
Knowledge graph of architectural decisions and their relationships.

**Structure:**
```
Decision: "Use PostgreSQL for ConPort"
    ↓
    ├─→ Why: Need graph database (AGE extension)
    ├─→ Alternatives: Neo4j, ArangoDB
    ├─→ Trade-offs:
    │   ├─→ Pro: Familiar SQL interface
    │   ├─→ Pro: ACID guarantees
    │   └─→ Con: Graph queries less elegant than Cypher
    ├─→ Impact:
    │   ├─→ Affects: ConPort architecture
    │   └─→ Requires: AGE extension setup
    └─→ Related Decisions:
        └─→ "Use Docker for services" (enables Postgres)
```

**Queries You Can Make:**
- "Why did we choose X over Y?"
- "What decisions depend on this one?"
- "Show me all database-related decisions"
- "What are the consequences of changing this?"

**Files:**
- `services/dddpg/graph_builder.py` - Graph construction
- `services/dddpg/query_engine.py` - Query interface

---

## 🔄 Data Flow - How Everything Connects

### Complete Request Flow Example

Let's trace what happens when you ask Claude: **"Show me all authentication code"**

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: You type in Claude Code                               │
│  👤 → "Show me all authentication code"                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Claude Code processes request                         │
│  • Analyzes intent: Code search query                          │
│  • Checks available MCP servers                                │
│  • Decides: Use ConPort + Serena                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Claude calls ConPort MCP                              │
│  Request: GET /search?query="authentication"&type="code"       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: ConPort queries knowledge graph                       │
│  GraphQL Query:                                                │
│  {                                                             │
│    codeNodes(                                                  │
│      where: { semanticSearch: "authentication" }              │
│    ) {                                                         │
│      path, name, type, dependencies                           │
│    }                                                           │
│  }                                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Postgres + AGE executes graph query                  │
│  SELECT * FROM ag_catalog.cypher('dopemux_graph', $$          │
│    MATCH (n:Code)                                              │
│    WHERE n.embedding <-> embed('authentication') < 0.3         │
│    RETURN n                                                    │
│  $$) as (n agtype);                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Results returned                                      │
│  Found:                                                        │
│  • src/auth/jwt_manager.py                                    │
│  • src/auth/user_model.py                                     │
│  • src/middleware/auth_middleware.py                          │
│  • tests/test_auth.py                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: Claude calls Serena for detailed info                │
│  For each file:                                               │
│  • Get function signatures                                    │
│  • Get class definitions                                      │
│  • Get documentation                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 8: Claude synthesizes response                           │
│  "I found 4 files related to authentication:                  │
│                                                                │
│  1. jwt_manager.py - JWT token generation & validation        │
│     • create_token(user_id, expires)                          │
│     • verify_token(token)                                     │
│                                                                │
│  2. user_model.py - User data model                           │
│     • class User(BaseModel)                                   │
│     • hash_password(password)                                 │
│     • verify_password(password, hash)                         │
│                                                                │
│  3. auth_middleware.py - Request authentication               │
│     • require_auth() decorator                                │
│     • get_current_user() helper                               │
│                                                                │
│  4. test_auth.py - Authentication tests                       │
│     • test_login()                                            │
│     • test_token_validation()                                 │
│                                                                │
│  Would you like me to show the code for any of these?"        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 9: Response displayed to you                            │
│  [Claude's formatted response in terminal]                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 10: Background tracking                                 │
│  • ADHD Engine logs interaction                               │
│  • Activity Capture records query                             │
│  • Session Intel learns you're working on auth                │
│  • Statusline updates: "📊 Reviewing auth code"               │
└─────────────────────────────────────────────────────────────────┘
```

**Total Time:** ~2-3 seconds (most time in LLM processing)

---

### Event Flow - Real-Time Updates

```
┌─────────────────────────────────────────────────────────────────┐
│  EVENT: You commit code                                        │
│  $ git commit -m "Add JWT validation"                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Git Hook: post-commit                                         │
│  Publishes: "code_committed" event                            │
│  Payload: {                                                    │
│    files: ["src/auth/jwt_manager.py"],                        │
│    message: "Add JWT validation",                             │
│    hash: "abc123",                                            │
│    timestamp: "2025-10-29T02:00:00Z"                          │
│  }                                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                     Event Bus (Redis)
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   ConPort    │   │ ADHD Engine  │   │   Activity   │
│              │   │              │   │   Capture    │
│ Updates KG:  │   │ Records:     │   │              │
│ • Index new  │   │ • Productivity│  │ Logs:        │
│   code       │   │ • Focus time │   │ "Commit      │
│ • Update     │   │ • Good       │   │  made at     │
│   graph      │   │   stopping   │   │  10:45am"    │
│              │   │   point      │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
        ↓                   ↓                   ↓
┌──────────────────────────────────────────────────┐
│  Break Suggester checks:                        │
│  "Good commit - natural stopping point"         │
│  "You've been working 90 minutes"               │
│  → Suggestion: ☕ "Time for a break?"           │
└──────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────┐
│  Statusline updates:                            │
│  Before: "Implementing JWT validation [1h 30m]" │
│  After:  "Completed JWT validation [1h 45m] ☕" │
└──────────────────────────────────────────────────┘
```

---

### Startup Flow - What Happens When You Run `dopemux start`

```
$ dopemux start
    ↓
┌─────────────────────────────────────────────────────────────┐
│  1. Pre-flight Checks                                       │
│  ✓ Check if .dopemux/ exists (if not, run `dopemux init`)  │
│  ✓ Check if git repository                                 │
│  ✓ Check if on main branch (warn if yes)                   │
│  ✓ Detect running instances                                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Instance Allocation                                     │
│  • Scan for running instances (A, B, C...)                  │
│  • Allocate next available (e.g., A if none running)        │
│  • Calculate port offsets (port_base = 3000 + offset)       │
│  • Create instance directory: .dopemux/instances/A/         │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Docker Services Startup                                 │
│  • Start Postgres (if not running)                          │
│  • Start ConPort container (mcp-conport)                    │
│  • Start Serena container (mcp-serena)                      │
│  • Start Zen container (mcp-zen)                            │
│  • Start other MCP servers based on profile                 │
│  • Wait for health checks (max 30s)                         │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  4. LiteLLM Proxy (if --litellm flag)                       │
│  • Load config: .dopemux/litellm/A/litellm.config.yaml      │
│  • Start proxy on port 4000 + offset                        │
│  • Verify health: http://localhost:4000/health              │
│  • Set ANTHROPIC_BASE_URL=http://localhost:4000             │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Claude Code Configuration                               │
│  • Generate .claude.json:                                   │
│    - Add all enabled MCP servers                            │
│    - Set environment variables                              │
│    - Configure ADHD-specific settings                       │
│  • Set ANTHROPIC_API_KEY (master key or real)               │
│  • Create temporary settings file                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  6. Background Services                                     │
│  • Start ADHD Engine (monitoring)                           │
│  • Start Task Router (priority mgmt)                        │
│  • Start Break Suggester (health)                           │
│  • Start Activity Capture (logging)                         │
│  • Start Orchestrator (coordination)                        │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  7. Tmux Session                                            │
│  • Create session: dopemux-A                                │
│  • Create panes:                                            │
│    ├─ Pane 0: Claude Code                                   │
│    ├─ Pane 1: Dashboard                                     │
│    ├─ Pane 2: Logs                                          │
│    └─ Pane 3: Shell                                         │
│  • Start statusline in background                           │
│  • Attach to session                                        │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  8. Launch Claude Code                                      │
│  • Execute: claude --settings <temp-file> <project-path>    │
│  • Claude starts with MCP servers enabled                   │
│  • Statusline shows: "Starting session..." → "Ready!"       │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  9. Context Restoration (if previous session exists)        │
│  • Load from ConPort: "What was I working on?"              │
│  • Restore:                                                 │
│    - Last file edited                                       │
│    - Current task/focus                                     │
│    - Open tabs                                              │
│  • Display: "📊 Resuming: Implement JWT validation"         │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  ✅ READY!                                                  │
│  You see:                                                   │
│  • Statusline: dopemux-mvp main | 📊 Ready | ⚡= 👁️●       │
│  • Claude Code: "How can I help you today?"                 │
│  • Dashboard: Showing current metrics                       │
└─────────────────────────────────────────────────────────────┘
```

**Total Startup Time:** ~15-30 seconds (depending on what's already running)

---
