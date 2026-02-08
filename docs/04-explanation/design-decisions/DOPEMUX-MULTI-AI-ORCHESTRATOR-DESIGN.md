---
id: DOPEMUX-MULTI-AI-ORCHESTRATOR-DESIGN
title: Dopemux Multi Ai Orchestrator Design
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopemux Multi Ai Orchestrator Design (explanation) for dopemux documentation
  and developer workflows.
---
# Dopemux Multi-AI Orchestrator Visual Design
**Mission Control for AI-Assisted Development**

**Version**: 1.0
**Date**: 2025-10-15
**Purpose**: Chat-driven orchestration of multiple AI instances with multi-pane monitoring

---

## Executive Summary

Dopemux Multi-AI Orchestrator is a **chat-driven mission control** for coordinating multiple AI CLI instances (Claude Code, Gemini CLI, Codex CLI) with real-time monitoring, ADHD optimizations, and seamless workflow transitions between research → planning → implementation phases.

**Key Innovation**: First ADHD-optimized multi-agent development system combining chat orchestration + tmux integration + knowledge graph memory + energy-aware task routing.

---

## Complete Visual Design

### Main Layout - Multi-AI Coordination Mode

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ ◆ DOPEMUX MISSION CONTROL │ Multi-AI Mode │ Energy: High ●● │ 22m │ Phase: IMPLEMENT   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 💬 MAIN CHAT ORCHESTRATOR                                                        │  │
│  │──────────────────────────────────────────────────────────────────────────────────│  │
│  │                                                                                   │  │
│  │ You: Research OAuth2 PKCE flow, design architecture, then implement              │  │
│  │                                                                                   │  │
│  │ Orchestrator: 📋 I've broken this down into 3 phases:                            │  │
│  │                                                                                   │  │
│  │   Phase 1: RESEARCH (Gemini + GPT-Researcher) - 20 min                          │  │
│  │   └─ Status: ✅ Complete - 15 sources analyzed                                   │  │
│  │   └─ Result: OAuth2 PKCE best practices documented                               │  │
│  │   └─ Saved to: ConPort Decision #145                                             │  │
│  │                                                                                   │  │
│  │   Phase 2: PLAN (Claude + Zen Planner) - 25 min                                 │  │
│  │   └─ Status: 🔄 In Progress (Step 3/5)                                           │  │
│  │   └─ Current: Designing token refresh strategy                                   │  │
│  │   └─ Agents: Claude (lead), Gemini (validator)                                   │  │
│  │                                                                                   │  │
│  │   Phase 3: IMPLEMENT (Codex + Claude Review) - 30 min                           │  │
│  │   └─ Status: ⏳ Pending (waiting for Phase 2)                                    │  │
│  │                                                                                   │  │
│  │ Claude (Pane 0): Currently analyzing session management patterns...              │  │
│  │ Gemini (Pane 1): Validating architecture against security best practices...      │  │
│  │                                                                                   │  │
│  │ [c] Continue  [p] Pause  [s] Skip to Phase 3  [r] Restart  [?] Help            │  │
│  │                                                                                   │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
├─────────────────────────────────────────┬────────────────────────────────────────────────┤
│                                         │                                                │
│  AI INSTANCES (Split View)              │  MONITORING DASHBOARD                         │
│                                         │                                                │
│  ┌────────────────────────────────────┐ │  ┌──────────────────────────────────────────┐ │
│  │ 🤖 Claude Code (Pane 0)            │ │  │ 📊 System Stats                          │ │
│  │────────────────────────────────────│ │  │──────────────────────────────────────────│ │
│  │ Status: 🟢 Active                  │ │  │ CPU: 45% ████░░░░                        │ │
│  │ Task: Architecture design          │ │  │ MEM: 4.2/16 GB ██░░░░░░                  │ │
│  │ Model: Claude Sonnet 4.5           │ │  │ API Tokens: 12K/50K used today           │ │
│  │                                    │ │  │                                          │ │
│  │ Recent output:                     │ │  │ 🏥 Service Health                        │ │
│  │ > Analyzing session.py:120...      │ │  │ ✅ ConPort (5455)        2ms             │ │
│  │ > Found 3 patterns to reuse        │ │  │ ✅ Serena LSP            78ms            │ │
│  │ > Complexity: 0.6 (medium)         │ │  │ ✅ Redis Pub/Sub         1ms             │ │
│  │                                    │ │  │ ⚠️  Zen MCP (3003)       350ms (slow)    │ │
│  │ [v] View full  [i] Interrupt      │ │  │ ✅ GPT-Researcher        -               │ │
│  └────────────────────────────────────┘ │  │ ✅ DopeconBridge    5ms             │ │
│                                         │  │                                          │ │
│  ┌────────────────────────────────────┐ │  │ 📋 Current Task                          │ │
│  │ 🤖 Gemini CLI (Pane 1)             │ │  │ #T-234: Implement OAuth system           │ │
│  │────────────────────────────────────│ │  │ Progress: ████████░░ 80%                 │ │
│  │ Status: 🟢 Active                  │ │  │ Phase: Planning (2/3)                    │ │
│  │ Task: Security validation          │ │  │ Complexity: High (0.8) 🔴                │ │
│  │ Model: Gemini 2.5 Pro              │ │  │ Est. remaining: 28 minutes               │ │
│  │                                    │ │  │                                          │ │
│  │ Recent output:                     │ │  │ 📂 Project: dopemux-mvp                  │ │
│  │ > Checking PKCE implementation...  │ │  │ Branch: feature/oauth                    │ │
│  │ > ✅ Meets security standards      │ │  │ Modified: 5 files                        │ │
│  │ > ⚠️  Consider rate limiting       │ │  │ Tests: 87% coverage                      │ │
│  │                                    │ │  │                                          │ │
│  │ [v] View full  [i] Interrupt      │ │  └──────────────────────────────────────────┘ │
│  └────────────────────────────────────┘ │                                                │
│                                         │                                                │
│  ┌────────────────────────────────────┐ │                                                │
│  │ 🤖 Codex CLI (Pane 2)              │ │                                                │
│  │────────────────────────────────────│ │                                                │
│  │ Status: ⏸️ Standby                  │ │                                                │
│  │ Task: Awaiting Phase 3             │ │                                                │
│  │ Model: GPT-5 Codex                 │ │                                                │
│  │                                    │ │                                                │
│  │ Ready for:                         │ │                                                │
│  │ • Code generation                  │ │                                                │
│  │ • JWT token implementation         │ │                                                │
│  │                                    │ │                                                │
│  │ [v] View config  [w] Wake up      │ │                                                │
│  └────────────────────────────────────┘ │                                                │
│                                         │                                                │
├─────────────────────────────────────────┴────────────────────────────────────────────────┤
│ Commands: /mode research|plan|implement  /pause  /agent <name>  /status  /help          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## AI Model Arsenal (Now Available!)

### Intelligence Rankings (After Adding Grok)

```
┌─────────────────────────────────────────────────────────────────┐
│ AVAILABLE AI MODELS (Ranked by Intelligence)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🥇 Score 18 - ELITE TIER                                       │
│  ├─ Gemini 2.5 Pro (1M context) - Analysis, research           │
│  └─ Grok Code Fast 1 (2M context) - Code generation, FREE!     │
│                                                                 │
│  🥈 Score 17 - EXPERT TIER                                      │
│  └─ GPT-5 Codex (400K context) - Code-specialized              │
│                                                                 │
│  🥉 Score 16 - STRONG TIER                                      │
│  ├─ GPT-5 (400K context) - General reasoning                   │
│  └─ Grok 4 Fast (2M context) - Multi-modal, reasoning, FREE!   │
│                                                                 │
│  Score 15 - ADVANCED TIER                                       │
│  ├─ O3 Pro - Professional reasoning                            │
│  ├─ DeepSeek R1 - Thinking mode                                │
│  ├─ Grok 4 - Multi-modal with vision                           │
│  └─ Opus 4.1 - Claude's flagship                               │
│                                                                 │
│  Score 14 - CAPABLE TIER                                        │
│  ├─ O3 - Balanced reasoning                                    │
│  └─ Grok 3 - Previous gen with vision                          │
│                                                                 │
│  Score 12-13 - EFFICIENT TIER                                   │
│  ├─ Sonnet 4.5 - Fast Claude                                   │
│  ├─ O3-Mini High - Complex problems                            │
│  ├─ O3-Mini - Balanced performance                             │
│  └─ Grok 3 Mini - Fast variant                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Cost Optimization**: Grok 4 Fast + Grok Code Fast are **FREE** right now via OpenRouter!

---

## Workflow Phase Assignments (Multi-Model Strategy)

### Phase 1: RESEARCH

**Primary**: Gemini 2.5 Pro (Score: 18, 1M context)
**Tools**: GPT-Researcher, Zen thinkdeep, Exa search
**Why**: Highest intelligence, massive context for multi-source synthesis
**Backup**: Grok 4 Fast (FREE, 2M context for large research)

```
User: "Research authentication best practices for SaaS"

Orchestrator routes to:
→ Gemini 2.5 Pro (primary research)
→ GPT-Researcher (multi-engine search)
→ Saves findings to ConPort Decision #146
```

### Phase 2: PLANNING

**Primary**: Claude Sonnet 4.5 (Score: 12, architectural thinking)
**Validator**: Gemini 2.5 Pro (multi-model consensus)
**Tools**: Zen planner, Zen consensus, Serena navigate
**Why**: Claude excels at system design, Gemini validates
**Backup**: GPT-5 (if complex architecture needs deep reasoning)

```
User: "Design the authentication system based on research"

Orchestrator routes to:
→ Claude (creates architecture plan via zen/planner)
→ Gemini (validates plan via zen/consensus)
→ Saves architecture to ConPort Decision #147
```

### Phase 3: IMPLEMENTATION

**Primary**: Grok Code Fast 1 (Score: 18, code-specialized, FREE!)
**Reviewer**: Claude Sonnet 4.5 (architecture compliance)
**Tester**: Gemini 2.5 Pro (test generation)
**Tools**: Serena edit, ConPort log_progress, Zen codereview
**Why**: Grok Code Fast is #1 for code, Claude ensures quality, Gemini writes tests
**Backup**: GPT-5 Codex (if Grok unavailable)

```
User: "Implement the JWT token generation and validation"

Orchestrator routes to:
→ Grok Code Fast (generates implementation)
→ Claude (reviews architecture compliance via zen/codereview)
→ Gemini (generates test cases)
→ All results aggregated and presented
```

### Phase 4: DEBUG/FIX

**Primary**: Gemini 2.5 Pro (Score: 18, analysis strength)
**Assistants**: Claude (hypothesis generation), Grok (code fixes)
**Tools**: Zen debug, Serena find_symbol, ConPort get_decisions
**Why**: Gemini's analytical strength, Claude's reasoning, Grok's code fixes

```
User: "Authentication failing intermittently"

Orchestrator routes to:
→ Gemini (runs zen/debug for root cause analysis)
→ Claude (reviews architecture for design flaws)
→ Grok Code Fast (implements fixes)
→ Saves findings to ConPort
```

---

## Complete Interface Mockup

### Window 1: Development Environment with AI Instances

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Window 1: AI Development Environment                                               │
├────────────────────────────────────┬────────────────────────────────────────────────┤
│                                    │                                                │
│  ┌──────────────────────────────┐  │  ┌──────────────────────────────────────────┐ │
│  │ Pane 0: Claude Code          │  │  │ Pane 1: Gemini CLI                       │ │
│  │──────────────────────────────│  │  │──────────────────────────────────────────│ │
│  │ 🟢 Active: Architecture      │  │  │ 🟢 Active: Security Validation           │ │
│  │                              │  │  │                                          │ │
│  │ Claude: Analyzing session    │  │  │ Gemini: Checking OAuth2 PKCE flow...     │  │
│  │ management patterns...       │  │  │                                          │ │
│  │                              │  │  │ Analysis: ✅ Implementation meets OWASP  │  │
│  │ Found 3 similar patterns:    │  │  │ standards                                │  │
│  │ • JWT rotation in auth.py    │  │  │                                          │  │
│  │ • Session store in cache.py  │  │  │ Recommendations:                         │  │
│  │ • Token validation utils     │  │  │ • Add rate limiting (429 responses)      │  │
│  │                              │  │  │ • Implement token refresh endpoint       │  │
│  │ Complexity: 0.6 (medium) 🟡  │  │  │ • Add audit logging                      │  │
│  │                              │  │  │                                          │ │
│  └──────────────────────────────┘  │  └──────────────────────────────────────────┘ │
│                                    │                                                │
├────────────────────────────────────┴────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │ Pane 2: Grok Code Fast         │  │ Pane 3: MAIN CHAT ORCHESTRATOR           │  │
│  │────────────────────────────────│  │──────────────────────────────────────────│  │
│  │ ⏸️ Standby: Awaiting Phase 3   │  │ > Coordinating research → plan workflow  │  │
│  │                                │  │                                          │  │
│  │ Ready for:                     │  │ Phase 2 (PLAN) Progress:                 │  │
│  │ • JWT token generation         │  │ [████████████░░░░░░] 60%                 │  │
│  │ • Refresh token logic          │  │                                          │  │
│  │ • Middleware integration       │  │ Agents Active: 2/3                       │  │
│  │                                │  │ • Claude: Architecture design            │  │
│  │ Model: 2M context              │  │ • Gemini: Security validation            │  │
│  │ Cost: FREE (limited time!)     │  │ • Codex: Standby                         │  │
│  │                                │  │                                          │  │
│  │ [w] Wake  [c] Configure       │  │ Next: Implement token generation         │  │
│  │                                │  │                                          │  │
│  │                                │  │ > _                                      │  │
│  └────────────────────────────────┘  └──────────────────────────────────────────┘  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Window 2: Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Window 2: Monitoring & Status Dashboard                                            │
├────────────────────────────────────┬────────────────────────────────────────────────┤
│                                    │                                                │
│  ┌──────────────────────────────┐  │  ┌──────────────────────────────────────────┐ │
│  │ 📋 Current Task Status       │  │  │ 🎯 Sprint Overview (PM Plane)            │ │
│  │──────────────────────────────│  │  │──────────────────────────────────────────│ │
│  │                              │  │  │                                          │ │
│  │ #T-234: OAuth Implementation │  │  │ Sprint: S-2025.10                        │ │
│  │                              │  │  │ Progress: ████████████░░ 75%             │ │
│  │ Overall: 80% complete        │  │  │                                          │ │
│  │ [████████████████░░░░] 80%   │  │  │ ✅ 12 completed                          │ │
│  │                              │  │  │ 🔄 3 in progress                         │ │
│  │ Sub-tasks:                   │  │  │ ⏳ 1 pending                             │ │
│  │ ✅ Research (100%)            │  │  │                                          │ │
│  │ 🔄 Planning (60%)             │  │  │ Due: 2025-10-31 (16 days)                │ │
│  │ ⏳ Implementation (0%)        │  │  │                                          │ │
│  │                              │  │  │ Focus blocks used: 8/12                  │ │
│  │ Active for: 22 minutes       │  │  │                                          │ │
│  │ Energy: High ●●              │  │  │ [d] Details  [t] Tasks                   │ │
│  │                              │  │  │                                          │ │
│  └──────────────────────────────┘  │  └──────────────────────────────────────────┘ │
│                                    │                                                │
├────────────────────────────────────┼────────────────────────────────────────────────┤
│                                    │                                                │
│  ┌──────────────────────────────┐  │  ┌──────────────────────────────────────────┐ │
│  │ 📊 System Metrics            │  │  │ 🏥 Service Health Monitor                │ │
│  │──────────────────────────────│  │  │──────────────────────────────────────────│ │
│  │                              │  │  │                                          │ │
│  │ CPU:  45% ████░░░░            │  │  │ MCP Servers:                             │ │
│  │ MEM:  4.2/16GB ██░░░░░░       │  │  │ ✅ ConPort (5455)      2.1ms p95         │ │
│  │ DISK: 45/500GB ░░░░░░░░       │  │  │ ✅ Serena LSP          78ms p95          │ │
│  │                              │  │  │ ✅ Zen MCP (3003)      120ms p95         │ │
│  │ API Usage (Today):           │  │  │ ✅ PAL apilookup            -                 │  │
│  │ OpenAI:  12K/50K tokens      │  │  │ ✅ Exa Search          -                 │  │
│  │ Anthropic: 8K/100K tokens    │  │  │ ✅ GPT-Researcher      -                 │  │
│  │ Google: 15K/1M tokens        │  │  │                                          │  │
│  │ xAI: 0K/∞ tokens (FREE!)     │  │  │ Infrastructure:                          │  │
│  │                              │  │  │ ✅ Redis Pub/Sub       0.8ms             │  │
│  │ Network: 2.3 Mbps ▂▄▆█▆▃▁    │  │  │ ✅ PostgreSQL AGE      4.2ms             │  │
│  │                              │  │  │ ✅ DopeconBridge  5.1ms             │  │
│  │                              │  │  │                                          │ │
│  └──────────────────────────────┘  │  └──────────────────────────────────────────┘ │
│                                    │                                                │
├────────────────────────────────────┼────────────────────────────────────────────────┤
│                                    │                                                │
│  ┌──────────────────────────────┐  │  ┌──────────────────────────────────────────┐ │
│  │ 🔀 Git Status                │  │  │ 🧪 Test Coverage                         │ │
│  │──────────────────────────────│  │  │──────────────────────────────────────────│ │
│  │                              │  │  │                                          │ │
│  │ Branch: feature/oauth        │  │  │ Overall: 87% ████████░░                  │  │
│  │ Commits: 3 ahead of main     │  │  │                                          │ │
│  │                              │  │  │ By Module:                               │  │
│  │ Modified: 5 files            │  │  │ ✅ auth.py         92%                   │  │
│  │ • src/auth.py                │  │  │ ⚠️  session.py      68% (needs work)     │  │
│  │ • src/session.py             │  │  │ ✅ middleware.py   95%                   │  │
│  │ • src/utils/crypto.py        │  │  │ ✅ models/user.py  89%                   │  │
│  │ • tests/test_auth.py         │  │  │ ✅ utils/crypto.py 100%                  │  │
│  │ • tests/test_session.py      │  │  │                                          │  │
│  │                              │  │  │ Tests: 156/178 passing                   │  │
│  │ Last commit: 45m ago         │  │  │ ❌ 22 failing (mostly new code)          │  │
│  │ "Add OAuth2 token generator" │  │  │                                          │  │
│  │                              │  │  │ [r] Run tests  [c] Coverage details      │  │
│  └──────────────────────────────┘  │  └──────────────────────────────────────────┘ │
│                                    │                                                │
└────────────────────────────────────┴────────────────────────────────────────────────┘
```

---

## Chat Commands & Slash System

### Command Reference

```
┌─────────────────────────────────────────────────────────────────┐
│ DOPEMUX CHAT COMMANDS                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WORKFLOW MODES                                                 │
│  /mode research      Switch to research mode (Gemini primary)  │
│  /mode plan          Switch to planning mode (Claude primary)  │
│  /mode implement     Switch to coding mode (Grok Code primary) │
│  /mode debug         Switch to debug mode (Gemini primary)     │
│  /mode review        Switch to review mode (Multi-model)       │
│                                                                 │
│  AGENT CONTROL                                                  │
│  /agent <name>       Send command to specific agent            │
│  /parallel           Execute with all available agents         │
│  /consensus          Get multi-model consensus on decision     │
│  /pause              Pause all agents                          │
│  /resume             Resume paused agents                      │
│                                                                 │
│  CONTEXT MANAGEMENT                                             │
│  /context save       Save current context to ConPort           │
│  /context load       Load previous session context             │
│  /context summary    Show current context summary              │
│  /memory <query>     Query ConPort knowledge graph             │
│                                                                 │
│  ADHD FEATURES                                                  │
│  /break              Start break timer (5/10/15 min)           │
│  /focus              Enter focus mode (hide dashboard)         │
│  /energy             Check current energy level                │
│  /suggest            Get energy-matched task suggestions       │
│                                                                 │
│  MONITORING                                                     │
│  /status             Show all agents and services status       │
│  /health             Service health check                      │
│  /stats              Show system metrics                       │
│  /tasks              Show current task progress                │
│                                                                 │
│  SYSTEM                                                         │
│  /help               Show this help                            │
│  /config             View/edit configuration                   │
│  /quit               Exit (with checkpoint save)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example Chat Flows

**Example 1: Complex Feature Implementation**
```
You: Build OAuth2 authentication with PKCE flow

Orchestrator: 📋 Breaking this down into phases:

Phase 1: RESEARCH (Gemini + GPT-Researcher)
  └─ Search OAuth2 best practices, PKCE flow, security considerations
  └─ Estimated: 20 minutes

Phase 2: PLAN (Claude + Zen Planner)
  └─ Design architecture, data models, API endpoints
  └─ Validate with Gemini (security review)
  └─ Estimated: 30 minutes

Phase 3: IMPLEMENT (Grok Code + Claude Review)
  └─ Generate token handlers, middleware, tests
  └─ Code review for quality and security
  └─ Estimated: 45 minutes

Total: ~95 minutes (4 focus blocks)
ADHD: Recommend breaking into 2 sessions

Start Phase 1? [Y/n]: y

Orchestrator: ✅ Starting Phase 1 with Gemini...
[Routing to Pane 1: Gemini CLI]
```

**Example 2: Agent-Specific Command**
```
You: /agent gemini analyze the authentication flow for race conditions

Orchestrator: 📨 Routing to Gemini (Pane 1)...

[Gemini CLI in Pane 1 activates]

Gemini: Running zen/debug for race condition analysis...

Step 1: Hypothesis - Token generation may have race conditions
  Evidence: Multiple requests can hit /auth/token simultaneously
  Confidence: Medium (0.6)

Step 2: Checking token_generator.py:34...
  Found: No locking mechanism on token ID generation
  Risk: HIGH - Two requests could get same token ID

Step 3: Recommended fix:
  Use database-level SERIAL or atomic counter
  Add distributed lock via Redis

Confidence: High (0.85)

[Results saved to ConPort Decision #148]

Orchestrator: ✅ Analysis complete. View full results? [y/N]
```

**Example 3: Multi-Model Consensus**
```
You: /consensus Should we use sessions or JWT tokens for authentication?

Orchestrator: 🤔 Getting multi-model perspectives...

Using zen/consensus with:
• Claude Sonnet 4.5 (for: JWT tokens)
• Gemini 2.5 Pro (against: JWT tokens, for: sessions)
• Grok 4 Fast (neutral: analyze trade-offs)

[3-way debate proceeding...]

Claude (FOR JWT):
  Stateless, scalable, works across microservices
  Mobile-friendly, no server-side session store

Gemini (AGAINST JWT):
  Revocation is complex (can't invalidate easily)
  Larger payload in every request
  Sessions give better control

Grok (NEUTRAL Analysis):
  Trade-offs depend on requirements:
  • Use JWT for: API-first, mobile apps, microservices
  • Use Sessions for: Monoliths, admin panels, simple revocation

SYNTHESIS:
✅ Recommended: Hybrid approach
  • JWT for API authentication
  • Server sessions for admin dashboard
  • Refresh tokens for long-lived auth

Confidence: High (0.82) - All models agree on hybrid

Save to ConPort? [Y/n]: y

[Saved as Decision #149: Hybrid auth strategy]
```

---

## ADHD Features in Action

### Energy-Aware Task Suggestions

```
┌─────────────────────────────────────────────────────────────────┐
│ 🌅 Energy Check                                                 │
│                                                                 │
│ Current time: 14:30 (Afternoon)                                │
│ Detected energy: MEDIUM 🟡                                      │
│                                                                 │
│ Based on your patterns:                                         │
│ • You're most focused 2-4pm                                    │
│ • Typing speed: 95% of baseline                                │
│ • Pane switches: 4/min (moderate focus)                        │
│                                                                 │
│ Recommended tasks for right now:                                │
│                                                                 │
│ 1. Implement token refresh logic                               │
│    Complexity: [█████░░░░░] 0.5 (medium)                        │
│    Energy: 25-30 minutes                                        │
│    Tools: Grok Code + Claude review                            │
│                                                                 │
│ 2. Write integration tests                                      │
│    Complexity: [███░░░░░░░] 0.3 (low)                           │
│    Energy: 20 minutes                                           │
│    Tools: Gemini (test generation)                             │
│                                                                 │
│ 3. Refactor session management                                 │
│    Complexity: [███████░░░] 0.7 (high)                          │
│    Energy: 45 minutes                                           │
│    Tools: Claude + Grok + Gemini consensus                     │
│    ⚠️ Save for high-energy time (morning recommended)          │
│                                                                 │
│ Select task [1-3] or [n] to see more: _                        │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpoint & Resume Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 💾 Auto-Checkpoint (Every 30 seconds)                           │
│                                                                 │
│ Saved at: 14:32:15                                             │
│                                                                 │
│ Current state:                                                  │
│ • Mode: PLAN                                                   │
│ • Phase: Planning OAuth architecture (Phase 2 of 3)            │
│ • Active agents: Claude (Pane 0), Gemini (Pane 1)             │
│ • Chat history: Last 15 messages                               │
│ • Open files: auth.py:45, session.py:120                       │
│ • Pending decisions: Token refresh strategy                    │
│                                                                 │
│ Checkpoint #47 saved to ConPort ✅                              │
└─────────────────────────────────────────────────────────────────┘

[30 seconds later, auto-save triggers again...]

[After interruption - next day]

┌─────────────────────────────────────────────────────────────────┐
│ 👋 Welcome Back!                                                │
│                                                                 │
│ Last session: 18 hours ago (Yesterday 14:32)                   │
│                                                                 │
│ YOU WERE:                                                       │
│ • Mode: PLAN (Phase 2: Architecture design)                    │
│ • Task: #T-234 OAuth implementation (80% complete)             │
│ • Agents: Claude analyzing, Gemini validating                  │
│ • Decision: Token refresh strategy (pending)                   │
│                                                                 │
│ WHILE YOU WERE AWAY:                                            │
│ • 12 new commits to main branch                                │
│ • 2 new decisions logged (#149, #150)                          │
│ • 1 task completed by teammate                                 │
│ • Sprint progress: 75% → 78%                                   │
│                                                                 │
│ RECOMMENDED ACTION:                                             │
│ Continue Phase 2 planning session (15 min remaining)           │
│ Current energy: MEDIUM 🟡 (good for planning)                  │
│                                                                 │
│ [Enter] Resume planning  [n] Start fresh  [d] Review updates   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Model Selection Matrix

### When to Use Which Model

```
┌────────────────────────────────────────────────────────────────────────┐
│ TASK TYPE          │ PRIMARY MODEL      │ VALIDATOR         │ COST     │
├────────────────────┼────────────────────┼───────────────────┼──────────┤
│ Research           │ Gemini 2.5 Pro     │ Grok 4 Fast       │ Low      │
│ Architecture       │ Claude Sonnet 4.5  │ Gemini Pro        │ Medium   │
│ Code Generation    │ Grok Code Fast 1   │ Claude            │ FREE!    │
│ Debugging          │ Gemini 2.5 Pro     │ Claude            │ Medium   │
│ Code Review        │ Gemini Pro         │ Claude + Grok     │ Medium   │
│ Testing            │ Gemini Pro         │ -                 │ Low      │
│ Documentation      │ Claude Sonnet      │ -                 │ Low      │
│ Refactoring        │ Claude Sonnet      │ Grok Code         │ Medium   │
│ Security Audit     │ Gemini Pro         │ Claude + GPT-5    │ High     │
│ Performance Opt    │ Grok Code          │ Gemini            │ FREE!    │
└────────────────────────────────────────────────────────────────────────┘

**Cost Legend**:
• FREE: Grok models (limited time)
• Low: < $0.10 per typical task
• Medium: $0.10-$0.50 per task
• High: $0.50-$2.00 per task
```

---

## Implementation Roadmap

### Phase 1: Basic Orchestration (Week 1)

**Deliverables**:
- ✅ Grok models added to Zen config
- 🔄 Basic tmux 4-pane layout
- 🔄 Chat orchestrator with command routing
- 🔄 Single AI coordination (Claude only)
- 🔄 ConPort checkpoint integration

**Success Criteria**:
- Can send tasks via chat to Claude
- Auto-save every 30s works
- Resume from checkpoint functional

---

### Phase 2: Multi-AI Coordination (Week 2-3)

**Deliverables**:
- Add Gemini CLI integration (Pane 1)
- Add Codex/Grok integration (Pane 2)
- Implement parallel task execution
- Add result aggregation
- Implement consensus mechanism

**Success Criteria**:
- Can coordinate 2-3 agents in parallel
- Consensus resolves conflicting recommendations
- Results properly aggregated

---

### Phase 3: Monitoring Dashboard (Week 4)

**Deliverables**:
- Window 2 monitoring dashboard
- Real-time service health
- System metrics display
- Git/test status integration
- Visual progress indicators

**Success Criteria**:
- Dashboard updates < 2s
- Service health accurate
- < 5% CPU overhead

---

### Phase 4: ADHD Optimizations (Week 5)

**Deliverables**:
- Energy-aware task suggestions
- Break reminders (25/50/90 min)
- Progressive disclosure in results
- Focus mode (hide dashboard)
- Hyperfocus protection

**Success Criteria**:
- Energy detection 85%+ accurate
- Break compliance improves
- Users report reduced overwhelm

---

## Technology Stack

**AI Models** (via Zen MCP):
- Claude Sonnet 4.5 (architecture, reasoning)
- Gemini 2.5 Pro (research, analysis, 1M context)
- Grok Code Fast 1 (code generation, 2M context, FREE!)
- Grok 4 Fast (reasoning, multi-modal, FREE!)
- GPT-5 Codex (fallback code generation)

**Coordination**:
- Redis Pub/Sub (message bus)
- ConPort (PostgreSQL AGE knowledge graph)
- DopeconBridge (authority enforcement)
- Zen MCP (multi-model reasoning)

**Monitoring**:
- Serena LSP (code intelligence)
- psutil (system metrics)
- Custom health checks (MCP servers)
- Git status monitoring

**Terminal**:
- tmux + libtmux (pane orchestration)
- Textual (monitoring dashboard)
- Rich (CLI output)

---

## Key Advantages

### 1. Multi-Model Strength
- **Grok Code Fast**: Best for code (intelligence: 18, FREE!)
- **Gemini Pro**: Best for research/analysis (1M context)
- **Claude Sonnet**: Best for architecture (reasoning)
- **Consensus**: Combine perspectives for better decisions

### 2. ADHD Optimizations
- Auto-save every 30s (never lose work)
- Energy-aware task matching (work WITH your brain)
- Break protection (prevent burnout)
- Progressive disclosure (reduce overwhelm)
- Visual progress (dopamine feedback)

### 3. Cost Efficiency
- Grok models FREE (limited time opportunity!)
- Smart model routing (cheap models for simple tasks)
- Prompt caching (reduce token usage)
- Parallel execution (faster completions)

### 4. Context Preservation
- ConPort knowledge graph (persistent memory)
- Resume from any checkpoint
- Cross-session context continuity
- No "what was I doing?" anxiety

---

`★ Insight ─────────────────────────────────────`
**Why This Design Works**: The multi-AI orchestration leverages each model's strengths while mitigating weaknesses through consensus. Grok Code Fast (2M context, FREE) handles large codebases, Gemini Pro (1M context) synthesizes research, Claude designs architecture. The chat interface coordinates them seamlessly while ADHD features prevent cognitive overload. This is **mission control for neurodivergent developers**.

**The Grok Opportunity**: Adding Grok now while it's FREE gives you premium 2M context capabilities at zero cost. The intelligence scores (Grok Code: 18, Grok 4 Fast: 16) make it competitive with GPT-5 Codex (17) and Gemini Pro (18), but without the API bill.
`─────────────────────────────────────────────────`

---

**Status**: Design complete, Grok models configured
**Next**: Implement Phase 1 basic orchestration
**Timeline**: 5 weeks to full multi-AI system
