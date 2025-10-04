# Dopemux MVP - ADHD-Optimized Development Platform

**Real-time context awareness, knowledge graphs, and cognitive load management for developers with ADHD**

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## 🎯 What is Dopemux?

Dopemux is a comprehensive development platform designed specifically for developers with ADHD. It combines real-time statusline awareness, persistent knowledge graphs, and adaptive accommodations to reduce cognitive load and maximize productivity.

### Key Features

- **🧠 ADHD-Optimized Statusline** - Real-time context awareness without breaking focus
- **📊 ConPort Knowledge Graph** - Persistent memory and decision logging across sessions
- **⚡ Adaptive Energy Tracking** - Monitor and adapt to your energy levels
- **👁️ Attention State Management** - Detect and accommodate different attention states
- **☕ Smart Break Reminders** - Context-aware break suggestions
- **🔄 Session Continuity** - Resume work exactly where you left off

---

## 🖥️ The Statusline - Your Development HUD

The Dopemux statusline provides instant visibility into your development context without requiring mental effort:

### 🌟 Complete Statusline Display (All Fields)

```
dopemux-mvp main | ✅ Implementing auth system [2h 15m] | 🧠 ⚡= 👁️● 🛡️ ☕ | 128K/200K (64%) | Sonnet 4.5
```

**Full breakdown with ALL possible fields:**

| Position | Component | Example | What It Shows | Why It Matters |
|----------|-----------|---------|---------------|----------------|
| 1️⃣ | **Directory** 📁 | `dopemux-mvp` | Current working directory | Quick context anchor |
| 2️⃣ | **Git Branch** 🌿 | `main` or `feature/auth` | Active git branch | Know what branch you're on |
| 3️⃣ | **Connection** 🔗 | 📊 or 📴 | ConPort knowledge graph status | Your context is (not) preserved |
| 4️⃣ | **Current Focus** 🎯 | `Implementing auth system` | What you're working on right now | No need to remember your task |
| 5️⃣ | **Session Time** ⏱️ | `[2h 15m]` | Time since session start | Gentle time awareness |
| 6️⃣ | **Energy Level** ⚡ | `High ↑` or `Medium •` | Current cognitive energy state | Match tasks to your energy |
| 7️⃣ | **Attention State** 👁️ | `Focused 👁️` or `Scattered 👁️🌀` | How focused you are right now | Self-awareness support |
| 8️⃣ | **Accommodations** 🛡️ | `🛡️` (optional) | Hyperfocus protection active | Flow state protected |
| 9️⃣ | **Break Warning** ☕ | ☕ or ☕! (optional) | Break needed (soon/urgently) | Prevent burnout |
| 🔟 | **Token Usage** 📊 | `128K/200K (64%)` | Context window usage (raw + %) | Avoid surprise autocompact |
| 1️⃣1️⃣ | **Active Model** 🤖 | `Sonnet 4.5` | Which Claude model is active | Context window awareness |

### 🎨 What Each Component Looks Like

#### 📁 Directory & 🌿 Branch
```
dopemux-mvp main
dopemux-mvp feature/auth-system
my-project bugfix/login-redirect
```

#### 🔗 Connection Status
| Display | Meaning | Your Action |
|---------|---------|-------------|
| 📊 | **Connected** - ConPort active | ✅ Work freely, context preserved |
| 📴 | **Disconnected** - ConPort offline | ⚠️ Fix ConPort, context at risk |

#### 🎯 Current Focus (max 35 chars)
```
📊 Implementing JWT tokens
📊 Debugging production login i...
📊 Code review - auth module
```

#### ⏱️ Session Time
```
[15m]           → Under 1 hour
[1h 23m]        → Over 1 hour
[3h 45m]        → Long session (watch for breaks!)
```

#### ⚡ Energy Levels
| Display | State | Best For 🎯 |
|---------|-------|-------------|
| **⚡⚡** | Hyperfocus - Peak energy | 🔥 Complex architecture, deep debugging, system design |
| **⚡↑** | High - Above baseline | 🚀 New features, challenging problems, learning |
| **⚡=** | Medium - Balanced/level | 💻 Regular development, bug fixes, testing |
| **⚡↓** | Low - Below baseline | 📝 Documentation, simple edits, code review |
| **⚡⇣** | Very Low - Depleted | 🛑 **TAKE A BREAK!** |

#### 👁️ Attention States
| Display | State | What It Means | Your Action 💡 |
|---------|-------|---------------|----------------|
| **👁️✨** | Hyperfocused - Deep flow | 🎉 Celebrate! Protect this precious state |
| **👁️●** | Focused - On task | ✅ Keep going, you're productive |
| **👁️~** | Transitioning - Shifting | 🌊 Be gentle, allow the shift |
| **👁️🌀** | Scattered - Fragmented | 🎯 Simplify current task, reduce complexity |
| **👁️💥** | Overwhelmed - Overload | 🚨 **STOP! Break time NOW** |

#### 🛡️ Accommodations (Optional)
| Symbol | Meaning | Effect |
|--------|---------|--------|
| 🛡️ | Hyperfocus protection | 🔕 Interruptions minimized, warnings delayed |

#### ☕ Break Warnings (Optional)
| Display | Urgency | What To Do 🎯 |
|---------|---------|----------------|
| ☕ (yellow) | **Soon** - within 10-15 min | ✋ Finish current task, then 5-min break |
| ☕! (red) | **NOW** - immediately | 🛑 **STOP EVERYTHING** - 15-min break minimum |

### Token Usage Tracking

**Never lose work to surprise autocompact:**

- 🟢 **0-60%** (Green) - Plenty of context, work freely
- 🟡 **60-80%** (Yellow) - Context filling up, wrap up soon
- 🔴 **80-100%** (Red) - Near autocompact, save decisions now

**Real-time calculation:**
- Parses Claude Code transcript file for actual usage
- Shows both raw tokens and percentage: `128K/200K (64%)`
- Auto-adapts to all Claude models (Opus 200K, Sonnet 200K/1M, Haiku 200K)

[📖 Full Statusline Documentation](./.claude/docs/STATUSLINE.md)

---

## 🚀 Quick Start

### Prerequisites

- **Claude Code** - CLI interface for Claude AI
- **Python 3.11+** - For ADHD Engine and services
- **Docker** - For ConPort and MCP servers
- **jq, sqlite3** - For statusline parsing

### Installation

```bash
# 1. Clone repository
git clone https://github.com/your-org/dopemux-mvp
cd dopemux-mvp

# 2. Start core services
docker-compose -f docker-compose.unified.yml up -d

# 3. Configure statusline in Claude Code settings
{
  "statusline": {
    "command": "bash $(pwd)/.claude/statusline.sh"
  }
}

# 4. Initialize your first session
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Setting up Dopemux\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
  }"
```

### Verify Setup

Your statusline should now show:
- 📊 Connected to ConPort
- 🎯 "Setting up Dopemux" as current focus
- ⏱️ Session time counting up
- 🧠 Energy and attention indicators (if ADHD Engine running)
- 📈 Token usage tracking

---

## 📚 Core Components

### ConPort Knowledge Graph

**Persistent memory system for development context:**

- **Product Context** - Project goals, architecture, tech stack
- **Active Context** - Current focus, session state, recent changes
- **Decision Log** - Architectural decisions with rationale
- **Progress Tracking** - Task hierarchies with ADHD metadata
- **System Patterns** - Reusable coding patterns and best practices
- **Knowledge Graph** - Relationships between decisions, tasks, patterns

**Key Features:**
- SQLite-based for sub-5ms queries
- Full-text and semantic search
- Session continuity across interruptions
- Decision genealogy tracking

[📖 ConPort Documentation](./docs/conport/)

### ADHD Engine

**Adaptive accommodation system:**

- **Energy Tracking** - Monitor cognitive energy levels
- **Attention States** - Detect focus, scattered, overwhelmed states
- **Break Management** - Smart break recommendations
- **Hyperfocus Protection** - Gentle reminders during deep work
- **Accommodation Stats** - Track what helps you be productive

**How it helps:**
- Adapts task complexity to energy level
- Suggests breaks before burnout
- Protects deep focus states
- Learns your productivity patterns

[📖 ADHD Engine Documentation](./services/adhd-engine/README.md)

### MCP Servers

**Specialized AI reasoning and tooling:**

- **Zen MCP** - Multi-model reasoning (thinkdeep, planner, consensus, debug, codereview)
- **Context7** - Official library documentation (React, Vue, Next.js, etc.)
- **GPT-Researcher** - Deep multi-source web research
- **Exa** - Neural semantic search
- **Serena LSP** - Semantic code intelligence
- **Dope-Context** - Hybrid code search with reranking

[📖 MCP Documentation](./.claude/)

---

## 💡 Usage Patterns

### Starting a Work Session

```bash
# Set your focus and start the timer
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Implementing user authentication\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
    \"mode\": \"ACT\"
  }"

# Statusline now shows:
# dopemux-mvp main | 📊 Implementing user authentication [0m] | 🧠•·👁️ 5K/200K (2%) | Sonnet 4.5
```

### Changing Focus Mid-Session

```bash
# Update focus without resetting timer
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"current_focus\": \"Fixing login redirect bug\"}"

# Session timer continues, focus updates immediately
```

### Logging Decisions

```bash
# Record important decisions for future reference
mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Use JWT for session management" \
  --rationale "Stateless, scalable, widely supported" \
  --implementation_details "HS256 algorithm, 1h expiry, refresh tokens" \
  --tags "auth,security,architecture"
```

### Managing Context Window

**Watch your statusline token percentage:**

🟢 **Green Zone (0-60%)**
```bash
# Work freely, context plenty
# Log decisions as you make them
# No urgency
```

🟡 **Yellow Zone (60-80%)**
```bash
# Wrap up current subtask
# Log key decisions now
# Prepare for potential autocompact

mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Completed auth middleware implementation" \
  --rationale "..." \
  --tags "auth,milestone"
```

🔴 **Red Zone (80-100%)**
```bash
# SAVE IMMEDIATELY
# Log all important context
# Consider starting new session

# Your context is about to autocompact!
```

### Respecting Break Warnings

**When statusline shows ☕ (yellow):**
- Finish current task (5-10 min)
- Log progress to ConPort
- Take 5-minute break

**When statusline shows ☕! (red):**
- Stop immediately
- Save all work
- Take 10-15 minute break
- Trust the system - it's protecting you

### Using Energy States

**Match tasks to energy level:**

⚡ **Hyperfocus** → Complex architecture, deep debugging, system design

↑ **High Energy** → New features, challenging problems, learning

• **Medium Energy** → Regular development, bug fixes, testing

↓ **Low Energy** → Documentation, code review, simple edits

⇣ **Very Low** → Take a break, don't push through

---

## 🏗️ Architecture

Dopemux uses a **two-plane architecture** for separation of concerns:

### Project Management Plane
- **Leantime** - Status authority (planned → active → blocked → done)
- **Task-Master** - PRD parsing, AI task decomposition
- **Task-Orchestrator** - 37 specialized tools, dependency analysis

### Cognitive Plane
- **Serena LSP** - Code intelligence with ADHD accommodations
- **ConPort** - Knowledge graph, decision logging, memory
- **ADHD Engine** - Energy tracking, attention management

### Integration Bridge
- Cross-plane event routing
- Authority enforcement
- Conflict resolution

[📖 Architecture Documentation](./.claude/CLAUDE.md)

---

## 🎖️ Performance Metrics

**ADHD Targets vs Actual:**

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Token reduction | 77% | ✅ 77% | **Met** |
| Context switch | < 2s | ✅ 0.37ms | **257x faster** |
| ConPort queries | < 50ms | ✅ 2ms | **25x faster** |
| Statusline refresh | < 1s | ✅ 150ms | **6.6x faster** |
| ADHD task completion | 85% | 🎯 In progress | **Tracking** |

---

## 🛠️ Troubleshooting

### Statusline shows 📴 disconnected

**Cause:** ConPort database not accessible

**Fix:**
```bash
# Check database exists
ls -la context_portal/context.db

# Initialize if missing
mcp__conport__get_active_context --workspace_id $(pwd)
```

### Statusline shows 0K/200K (0%)

**Cause:** Transcript file not accessible

**Fix:**
```bash
# Enable debug mode
# Edit .claude/statusline.sh, uncomment debug lines

# Check logs
cat /tmp/statusline_debug.json | jq .
tail -20 /tmp/statusline_debug.log
```

### Session time not showing

**Cause:** Invalid session_start timestamp

**Fix:**
```bash
# Reset session start to now
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}"
```

### ADHD Engine shows 💤

**Cause:** Service not running

**Fix:**
```bash
# Start ADHD Engine
cd services/adhd-engine
uvicorn main:app --port 8095 --reload
```

[📖 Full Troubleshooting Guide](./.claude/docs/STATUSLINE.md#troubleshooting)

---

## 📖 Documentation

- **[Statusline Guide](./.claude/docs/STATUSLINE.md)** - Complete statusline documentation
- **[ConPort Memory System](./docs/conport/)** - Knowledge graph and decision logging
- **[ADHD Patterns](./.claude/modules/shared/adhd-patterns.md)** - ADHD accommodation patterns
- **[MCP Integration](./.claude/)** - AI reasoning and tool integration
- **[Architecture Guide](./.claude/CLAUDE.md)** - System architecture overview

---

## 🤝 Contributing

Dopemux is designed by and for developers with ADHD. Contributions welcome!

**Areas of focus:**
- ADHD accommodation patterns
- Statusline improvements
- Energy/attention tracking
- Break management strategies
- Context preservation techniques

---

## 📝 Changelog

### Version 2.0 (2025-10-04)

**Statusline Improvements:**
- ✅ Real token usage tracking from transcript files
- ✅ Auto-detect context window for all Claude models
- ✅ Raw token counts: `128K/200K (64%)`
- ✅ Better energy symbol: `•` for medium
- ✅ Intuitive time: `[2h 15m]` format
- ✅ Attention state indicators
- ✅ Break warning system
- ✅ Hyperfocus protection

**Performance:**
- ✅ ConPort: 2ms queries (25x faster than target)
- ✅ Statusline: 150ms refresh (6.6x faster)
- ✅ Token calc: 30ms (3x faster)

**New Features:**
- ✅ Direct SQLite access for ConPort
- ✅ Progressive disclosure based on terminal width
- ✅ Context window optimization guidance

### Version 1.0 (2025-09-26)

- Initial release
- ConPort knowledge graph
- ADHD Engine integration
- Basic statusline

[📖 Full Changelog](./CHANGELOG.md)

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with insights from the ADHD development community and powered by Claude AI.

**Special thanks to:**
- The ADHD developer community for sharing their experiences
- Anthropic for Claude Code and Claude API
- Contributors to ADHD accommodation research

---

**Made with ❤️ and ☕ by developers with ADHD, for developers with ADHD**
