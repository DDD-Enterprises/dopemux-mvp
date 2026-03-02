# Dopemux Architecture Documentation

## System Overview

Dopemux implements a **hub-and-spoke architecture** with the CLI as the central orchestrator, designed specifically for ADHD developers requiring context preservation, attention adaptation, and task decomposition.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Dopemux Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  Terminal UI    │    │   Rich Console  │                │
│  │   (Click CLI)   │───▶│   Visualization │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                                                 │
│  ┌─────────▼─────────────────────────────────────────┐     │
│  │                Central Orchestrator                │     │
│  │              (Dopemux CLI Core)                    │     │
│  └─────────┬─────────┬─────────┬─────────┬─────────┘     │
│            │         │         │         │                 │
│ ┌──────────▼──┐ ┌────▼────┐ ┌──▼───┐ ┌──▼─────────┐       │
│ │Context Mgmt │ │ADHD Core│ │Config│ │Claude Integ│       │
│ └─────────────┘ └─────────┘ └──────┘ └────────────┘       │
└─────────────────────────────────────────────────────────────┘
           │                                  │
┌──────────▼──────────┐           ┌──────────▼──────────┐
│   Local Storage     │           │   Claude Code       │
│                     │           │   + MCP Servers     │
│ ├─ SQLite Context   │           │                     │
│ ├─ YAML Config      │           │ ├─ claude-context   │
│ ├─ Session Backups  │           │ ├─ mas-seq-thinking │
│ └─ Attention Metrics│           │ ├─ context7         │
└─────────────────────┘           │ └─ morphllm-apply   │
                                  └─────────────────────┘
```

## Component Architecture

### 1. CLI Layer (`src/dopemux/cli.py`)

**Central Orchestrator** - Coordinates all system components

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Commands                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  init    │  start   │  save    │  restore │  status    │
│    │     │    │     │    │     │    │     │     │      │
│    ▼     │    ▼     │    ▼     │    ▼     │     ▼      │
│  Setup   │ Launch   │ Context  │ Session  │ Metrics    │
│  Project │ Claude   │ Capture  │ Restore  │ Display    │
│          │   Code   │          │          │            │
│          │          │          │          │            │
├──────────┼──────────┼──────────┼──────────┼────────────┤
│          │          │          │          │            │
│     ┌────▼────┐ ┌───▼───┐ ┌────▼────┐ ┌──▼──┐          │
│     │Config   │ │Context│ │ ADHD    │ │Rich │          │
│     │Manager  │ │Manager│ │Features │ │ UI  │          │
│     └─────────┘ └───────┘ └─────────┘ └─────┘          │
└─────────────────────────────────────────────────────────┘
```

**Command Flow:**
1. **init** → ConfigManager → Create project structure
2. **start** → ContextManager + ClaudeLauncher → Restore & Launch
3. **save** → ContextManager → Capture current state
4. **restore** → ContextManager → Load previous session
5. **status** → AttentionMonitor → Show metrics
6. **task** → TaskDecomposer → Manage ADHD tasks

### 2. ADHD Core Components (`src/dopemux/adhd/`)

**Attention-Aware Processing** - Real-time cognitive state adaptation

```
┌─────────────────────────────────────────────────────────────┐
│                    ADHD Components                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────┐   ┌─────────────────┐   ┌─────────────┐ │
│ │ Context Manager │   │Attention Monitor│   │Task Decomp. │ │
│ │                 │   │                 │   │             │ │
│ │ ┌─────────────┐ │   │ ┌─────────────┐ │   │ ┌─────────┐ │ │
│ │ │Auto-save    │ │   │ │Keystroke    │ │   │ │25-min   │ │ │
│ │ │every 30s    │ │   │ │Pattern      │ │   │ │Chunks   │ │ │
│ │ └─────────────┘ │   │ │Analysis     │ │   │ └─────────┘ │ │
│ │                 │   │ └─────────────┘ │   │             │ │
│ │ ┌─────────────┐ │   │ ┌─────────────┐ │   │ ┌─────────┐ │ │
│ │ │Session      │ │   │ │Attention    │ │   │ │Progress │ │ │
│ │ │Restoration  │ │   │ │State        │ │   │ │Tracking │ │ │
│ │ │< 500ms      │ │   │ │Classify     │ │   │ │         │ │ │
│ │ └─────────────┘ │   │ └─────────────┘ │   │ └─────────┘ │ │
│ └─────────────────┘   └─────────────────┘   └─────────────┘ │
│          │                       │                   │      │
│          ▼                       ▼                   ▼      │
│ ┌─────────────────┐   ┌─────────────────┐   ┌─────────────┐ │
│ │   SQLite DB     │   │   Metrics       │   │   Task DB   │ │
│ │                 │   │   Storage       │   │             │ │
│ │ ├─Sessions      │   │ ├─Keystroke     │   │ ├─Active    │ │
│ │ ├─Files         │   │ ├─Errors        │   │ ├─Completed │ │
│ │ ├─Cursor Pos    │   │ ├─Context Switch│   │ ├─Progress  │ │
│ │ └─Mental Model  │   │ └─Focus Score   │   │ └─Duration  │ │
│ └─────────────────┘   └─────────────────┘   └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Context Manager Data Flow

```
User Activity ──┐
                │
                ▼
┌─────────────────────────────────────┐
│         Activity Capture            │
│                                     │
│ ┌─File Operations─┐ ┌─Cursor Pos─┐  │
│ │ ├─ opens        │ │ ├─ line    │  │
│ │ ├─ closes       │ │ ├─ column  │  │
│ │ ├─ edits        │ │ └─ selection│  │
│ │ └─ saves        │ └────────────┘  │
│ └────────────────┘                  │
│                                     │
│ ┌─Mental Model──┐ ┌─Decisions────┐  │
│ │ ├─ current goal│ │ ├─ choices   │  │
│ │ ├─ approach    │ │ ├─ rationale │  │
│ │ └─ blockers    │ │ └─ outcomes  │  │
│ └───────────────┘ └──────────────┘  │
└─────────────────────────────────────┘
                │
                ▼ (every 30 seconds)
┌─────────────────────────────────────┐
│          SQLite Storage             │
│                                     │
│  CREATE TABLE sessions (            │
│    id TEXT PRIMARY KEY,             │
│    timestamp DATETIME,              │
│    current_goal TEXT,               │
│    open_files JSON,                 │
│    cursor_positions JSON,           │
│    git_branch TEXT,                 │
│    mental_model JSON,               │
│    decisions JSON                   │
│  );                                 │
└─────────────────────────────────────┘
                │
                ▼ (on restore)
┌─────────────────────────────────────┐
│        Context Restoration          │
│                                     │
│ 1. Query latest session             │
│ 2. Parse file positions             │
│ 3. Restore mental model             │
│ 4. Set current goal                 │
│ 5. ✅ Ready in <500ms               │
└─────────────────────────────────────┘
```

#### Attention State Classification

```
Input Signals ────────────┐
                          │
┌─Keystroke Rate─┐         │
│ ├─ velocity    │         │
│ ├─ consistency │         ▼
│ └─ patterns    │ ┌─────────────────┐
└────────────────┘ │  Classification  │
                   │     Engine       │
┌─Error Patterns─┐  │                 │
│ ├─ frequency   │ │ ┌─────────────┐ │
│ ├─ correction  │ │ │   Rules     │ │
│ └─ types       │ │ │             │ │
└────────────────┘ │ │ focused:    │ │
                   │ │ >50kps,     │ │
┌─Context Switch─┐  │ │ <5% error   │ │
│ ├─ file changes│ │ │             │ │
│ ├─ tab switches│ │ │ scattered:  │ │
│ └─ app focus   │ │ │ <20kps,     │ │
└────────────────┘ │ │ >20% error  │ │
                   │ └─────────────┘ │
                   └─────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                Attention States                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 🎯 focused      │ High velocity, low errors, stable   │
│ 😊 normal       │ Moderate activity, baseline metrics │
│ 🌪️ scattered    │ Low focus, high context switches    │
│ 🔥 hyperfocus   │ Very high velocity, tunnel vision   │
│ 😵‍💫 distracted  │ Very low activity, high error rate  │
└─────────────────────────────────────────────────────────┘
```

### 3. Claude Integration (`src/dopemux/claude/`)

**MCP Server Orchestration** - Multi-model AI coordination

```
┌─────────────────────────────────────────────────────────────┐
│                Claude Integration                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────┐              ┌─────────────────┐        │
│ │ ClaudeLauncher  │              │ClaudeConfigurator│       │
│ │                 │              │                 │        │
│ │ ┌─────────────┐ │              │ ┌─────────────┐ │        │
│ │ │ Detection   │ │              │ │ MCP Server  │ │        │
│ │ │ Claude Code │ │              │ │ Config Gen  │ │        │
│ │ │ Binary      │ │              │ │             │ │        │
│ │ └─────────────┘ │              │ └─────────────┘ │        │
│ │                 │              │                 │        │
│ │ ┌─────────────┐ │              │ ┌─────────────┐ │        │
│ │ │ Environment │ │              │ │ ADHD Profile│ │        │
│ │ │ Variables   │ │              │ │ Integration │ │        │
│ │ │ Setup       │ │              │ │             │ │        │
│ │ └─────────────┘ │              │ └─────────────┘ │        │
│ │                 │              │                 │        │
│ │ ┌─────────────┐ │              │ ┌─────────────┐ │        │
│ │ │ Process     │ │              │ │ Template    │ │        │
│ │ │ Launching   │ │              │ │ Selection   │ │        │
│ │ │             │ │              │ │             │ │        │
│ │ └─────────────┘ │              │ └─────────────┘ │        │
│ └─────────────────┘              └─────────────────┘        │
│          │                                │                 │
│          ▼                                ▼                 │
└──────────┼────────────────────────────────┼─────────────────┘
           │                                │
           ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code                              │
│                  + MCP Servers                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │claude-context│ │mas-seq-think │ │   context7   │       │
│  │              │ │              │ │              │       │
│  │Milvus + BM25 │ │Complex       │ │Documentation │       │
│  │Hybrid Search │ │Reasoning     │ │Access        │       │
│  │              │ │Chains        │ │              │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
│                                                             │
│  ┌──────────────┐                                          │
│  │morphllm-apply│                                          │
│  │              │                                          │
│  │Code Transform│                                          │
│  │& Refactoring │                                          │
│  │              │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

#### MCP Server Configuration Generation

```
ADHD Profile ──┐
               │
Template Type ─┼─┐
               │ │
               ▼ ▼
┌─────────────────────────────────────┐
│     Configuration Generator         │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │        .claude/llms.md          │ │
│ │                                 │ │
│ │ # Model Selection               │ │
│ │ - focused: opus-4.1, o3-pro    │ │
│ │ - scattered: gemini-2.5-flash   │ │
│ │ - hyperfocus: sonnet-4          │ │
│ │                                 │ │
│ │ # MCP Servers                   │ │
│ │ - claude-context: hybrid search │ │
│ │ - mas-seq-thinking: reasoning   │ │
│ │ - context7: documentation       │ │
│ │ - morphllm-apply: transforms    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │       .claude/claude.md         │ │
│ │                                 │ │
│ │ # ADHD Accommodations           │ │
│ │ - Focus Duration: 25 minutes    │ │
│ │ - Break Intervals: 5 minutes    │ │
│ │ - Notification Style: gentle    │ │
│ │ - Visual Complexity: minimal    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │      .claude/context.md         │ │
│ │                                 │ │
│ │ # Context Management            │ │
│ │ - Attention State Adaptation    │ │
│ │ - Memory Augmentation           │ │
│ │ - Decision Journal              │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 4. Configuration System (`src/dopemux/config/`)

**Multi-Format Configuration Management** - YAML/TOML with validation

```
┌─────────────────────────────────────────────────────────────┐
│              Configuration Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                ConfigManager                            │ │
│ │                                                         │ │
│ │  load_config() ──┐                                      │ │
│ │                  │                                      │ │
│ │                  ▼                                      │ │
│ │  ┌──────────────────────────────────────────────────┐   │ │
│ │  │            Format Detection                      │   │ │
│ │  │                                                  │   │ │
│ │  │  .yaml/.yml ──▶ PyYAML Loader                   │   │ │
│ │  │  .toml      ──▶ TOML Loader                     │   │ │
│ │  │  .json      ──▶ JSON Loader                     │   │ │
│ │  └──────────────────────────────────────────────────┘   │ │
│ │                  │                                      │ │
│ │                  ▼                                      │ │
│ │  ┌──────────────────────────────────────────────────┐   │ │
│ │  │             Validation                           │   │ │
│ │  │                                                  │   │ │
│ │  │  • ADHD profile schema validation                │   │ │
│ │  │  • MCP server configuration check               │   │ │
│ │  │  • Path resolution and verification             │   │ │
│ │  │  • Default value injection                      │   │ │
│ │  └──────────────────────────────────────────────────┘   │ │
│ │                  │                                      │ │
│ │                  ▼                                      │ │
│ │  ┌──────────────────────────────────────────────────┐   │ │
│ │  │            Merged Configuration                  │   │ │
│ │  │                                                  │   │ │
│ │  │  Global (~/.claude/CLAUDE.md)                   │   │ │
│ │  │     ├── ADHD principles                         │   │ │
│ │  │     └── Default MCP servers                     │   │ │
│ │  │                                                  │   │ │
│ │  │  Project (.dopemux/config.yaml)                 │   │ │
│ │  │     ├── Project-specific settings               │   │ │
│ │  │     └── Override global defaults                │   │ │
│ │  └──────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Configuration Hierarchy

```
Configuration Precedence (highest to lowest):

1. Command Line Arguments
   --debug, --session, --template, etc.
   │
   ▼
2. Environment Variables
   DOPEMUX_*, CLAUDE_*, etc.
   │
   ▼
3. Project Configuration
   .dopemux/config.yaml
   │
   ▼
4. User Configuration
   ~/.dopemux/config.yaml
   │
   ▼
5. Global ADHD Principles
   ~/.claude/CLAUDE.md
   │
   ▼
6. Built-in Defaults
   Hardcoded in ConfigManager
```

## Data Flow Architecture

### Session Lifecycle

```
User Command ────────────────┐
                             │
                             ▼
┌─────────────────────────────────────────┐
│              CLI Router                 │
│                                         │
│  init ──▶ Project Setup                 │
│  start ─▶ Session Restore + Launch      │
│  save ──▶ Context Capture               │
│  restore▶ Session Selection             │
│  status ▶ Metrics Display               │
│  task ──▶ Task Management               │
└─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────┐
│           Component Router              │
│                                         │
│ ┌─────────────┐ ┌─────────────────────┐ │
│ │Context Mgmt │ │ ADHD Components     │ │
│ │             │ │                     │ │
│ │ ├─Save      │ │ ├─Attention Monitor │ │
│ │ ├─Restore   │ │ ├─Task Decomposer   │ │
│ │ └─List      │ │ └─Progress Tracking │ │
│ └─────────────┘ └─────────────────────┘ │
│                                         │
│ ┌─────────────┐ ┌─────────────────────┐ │
│ │Claude Integ │ │ Config Management   │ │
│ │             │ │                     │ │
│ │ ├─Launch    │ │ ├─Load/Merge       │ │
│ │ ├─Configure │ │ ├─Validate         │ │
│ │ └─Monitor   │ │ └─Default Injection │ │
│ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────┐
│            Storage Layer                │
│                                         │
│ ┌─SQLite Context DB─┐ ┌─File System───┐ │
│ │ ├─Sessions        │ │ ├─Config Files │ │
│ │ ├─Files/Positions │ │ ├─Claude Config│ │
│ │ ├─Mental Models   │ │ ├─Session Logs │ │
│ │ └─Decision History│ │ └─MCP Configs  │ │
│ └───────────────────┘ └───────────────┘ │
└─────────────────────────────────────────┘
```

### ADHD Adaptation Pipeline

```
Real-time Input ─────────────┐
                             │
┌─Keystroke Events───┐        │
│ ├─Rate (keys/min)  │        │
│ ├─Rhythm           │        ▼
│ └─Consistency      │ ┌─────────────────┐
└────────────────────┘ │  Attention      │
                       │  Classification │
┌─Error Patterns────┐  │     Engine      │
│ ├─Frequency (/min) │  │                 │
│ ├─Correction Time  │  │ ┌─────────────┐ │
│ └─Types (syntax/   │  │ │Feature      │ │
│   logic/typos)     │  │ │Extraction   │ │
└────────────────────┘  │ └─────────────┘ │
                        │                 │
┌─Context Switches───┐  │ ┌─────────────┐ │
│ ├─File Changes     │  │ │State        │ │
│ ├─Tab Switches     │  │ │Classification│ │
│ ├─App Focus        │  │ └─────────────┘ │
│ └─Break Frequency   │  └─────────────────┘
└────────────────────┘           │
                                 ▼
┌─────────────────────────────────────────┐
│           Attention State               │
│                                         │
│ 🎯 focused    ──▶ Comprehensive Details │
│ 😊 normal     ──▶ Balanced Information  │
│ 🌪️ scattered  ──▶ Bullet Points Only   │
│ 🔥 hyperfocus ──▶ Code-Only Responses   │
│ 😵‍💫 distracted──▶ Single Action Items   │
└─────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────┐
│        Response Adaptation              │
│                                         │
│ ┌─Model Selection──┐ ┌─Format Control─┐ │
│ │ Focused: Opus4.1 │ │ Scattered:     │ │
│ │ Quick: Gemini2.5 │ │ • Bullets only │ │
│ │ Code: Sonnet-4   │ │ • <500 words   │ │
│ └──────────────────┘ │ • 1 clear act. │ │
│                      └────────────────┘ │
│ ┌─Context Injection─┐ ┌─Progress Viz──┐ │
│ │ Session history   │ │ [████░░] 67%  │ │
│ │ Previous goals    │ │ ✅ 4/6 tasks  │ │
│ │ Recent decisions  │ │ ⏱️ 23min left │ │
│ └───────────────────┘ └───────────────┘ │
└─────────────────────────────────────────┘
```

## Performance Architecture

### Response Time Targets

```
Operation Performance Requirements:

┌─────────────────────────────────────────┐
│            Critical Path                │ Target
├─────────────────────────────────────────┼─────────
│ Context Restoration                     │ <500ms
│ Auto-save Operation                     │ <50ms
│ Attention State Classification          │ <100ms
│ CLI Command Response                    │ <300ms
│ Task Decomposition                      │ <200ms
│ Claude Code Launch                      │ <5s
└─────────────────────────────────────────┴─────────
```

### Optimization Strategies

```
┌─────────────────────────────────────────────────────────┐
│                Performance Optimizations               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌──Context Restoration──┐ ┌──Attention Monitor────────┐ │
│ │                       │ │                           │ │
│ │ • SQLite indexing     │ │ • Async processing        │ │
│ │ • Lazy file loading   │ │ • Circular buffers        │ │
│ │ • JSON compression    │ │ • Sampling rate control   │ │
│ │ • Connection pooling  │ │ • Background classification│ │
│ │                       │ │                           │ │
│ └───────────────────────┘ └───────────────────────────┘ │
│                                                         │
│ ┌──Memory Management────┐ ┌──I/O Optimization─────────┐ │
│ │                       │ │                           │ │
│ │ • LRU caches          │ │ • Async file operations   │ │
│ │ • Object pooling      │ │ • Batch database writes   │ │
│ │ • Weak references     │ │ • Memory-mapped files     │ │
│ │ • Garbage collection  │ │ • Stream processing       │ │
│ │                       │ │                           │ │
│ └───────────────────────┘ └───────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Security Architecture

### Data Protection

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─Local Data Protection─┐                                   │
│ │                       │                                   │
│ │ • SQLite encryption   │                                   │
│ │ • File permissions    │                                   │
│ │ • No cloud storage    │                                   │
│ │ • User-only access    │                                   │
│ │                       │                                   │
│ └───────────────────────┘                                   │
│                                                             │
│ ┌─Configuration Security┐                                   │
│ │                       │                                   │
│ │ • Input validation    │                                   │
│ │ • Path sanitization   │                                   │
│ │ • Schema enforcement  │                                   │
│ │ • Safe defaults       │                                   │
│ │                       │                                   │
│ └───────────────────────┘                                   │
│                                                             │
│ ┌─Process Isolation─────┐                                   │
│ │                       │                                   │
│ │ • Sandboxed execution │                                   │
│ │ • Limited file access │                                   │
│ │ • No network exposure │                                   │
│ │ • Claude Code boundary│                                   │
│ │                       │                                   │
│ └───────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

## Extensibility Architecture

### Plugin System Design

```
┌─────────────────────────────────────────────────────────────┐
│                  Extension Points                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─ADHD Accommodations───┐  ┌─MCP Server Integration──────┐  │
│ │                       │  │                             │  │
│ │ • Custom attention    │  │ • New server types          │  │
│ │   classification      │  │ • Model orchestration       │  │
│ │ • Personalized        │  │ • Cost optimization         │  │
│ │   break patterns      │  │ • Response routing          │  │
│ │ • Biometric inputs    │  │                             │  │
│ │                       │  └─────────────────────────────┘  │
│ └───────────────────────┘                                   │
│                                                             │
│ ┌─Context Adapters──────┐  ┌─UI Customizations───────────┐  │
│ │                       │  │                             │  │
│ │ • IDE integrations    │  │ • Custom progress bars      │  │
│ │ • Version control     │  │ • Attention visualizations  │  │
│ │ • Project managers    │  │ • Notification systems      │  │
│ │ • Communication tools │  │ • Theme adaptations         │  │
│ │                       │  │                             │  │
│ └───────────────────────┘  └─────────────────────────────┘  │
│                                                             │
│ ┌─Data Export/Import────┐  ┌─Monitoring & Analytics──────┐  │
│ │                       │  │                             │  │
│ │ • Session export      │  │ • Productivity metrics      │  │
│ │ • Team context sharing│  │ • ADHD accommodation        │  │
│ │ • Backup systems      │  │   effectiveness             │  │
│ │ • Migration tools     │  │ • Usage pattern analysis    │  │
│ │                       │  │                             │  │
│ └───────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Future Architecture Evolution

### Phase 2: Enhanced Integration

```
Current Architecture ────────┐
                             │
                             ▼
┌─────────────────────────────────────────┐
│         Enhanced Platform               │
│                                         │
│ ┌─VSCode Extension─┐ ┌─Tmux Integration┐│
│ │ • Direct context │ │ • Session mgmt  ││
│ │ • Attention UI   │ │ • Pane restore  ││
│ │ • Task sidebar   │ │ • Auto layouts  ││
│ └──────────────────┘ └─────────────────┘│
│                                         │
│ ┌─Multi-Project────┐ ┌─Advanced MCP────┐│
│ │ • Context switch │ │ • Server chains ││
│ │ • Project graphs │ │ • Cost optimize ││
│ │ • Dependency map │ │ • Model routing ││
│ └──────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
```

### Phase 3: Advanced ADHD Features

```
Enhanced Platform ──────────┐
                            │
                            ▼
┌─────────────────────────────────────────┐
│        Advanced ADHD Platform          │
│                                         │
│ ┌─Biometric Monitor┐ ┌─Learning Engine─┐│
│ │ • Heart rate     │ │ • Pattern recog ││
│ │ • Eye tracking   │ │ • Personal opt  ││
│ │ • Stress levels  │ │ • Adaptation    ││
│ └──────────────────┘ └─────────────────┘│
│                                         │
│ ┌─Smart Scheduling──┐ ┌─Team Features───┐│
│ │ • Cognitive load │ │ • Shared context││
│ │ • Energy predict │ │ • Pair coding   ││
│ │ • Break optimize │ │ • ADHD pairing  ││
│ └───────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
```

---

**Architecture Summary:** Dopemux implements a modular, attention-aware development platform with SQLite-based context persistence, real-time cognitive state classification, and adaptive AI model orchestration through Claude Code and MCP servers, optimized for ADHD developers requiring context preservation and task decomposition.