---
id: role-persona-comprehensive-guide
title: Comprehensive Role & Persona Guide
type: how-to
owner: '@hu3mann'
date: '2025-10-30'
last_review: '2025-10-30'
next_review: '2026-01-30'
adhd_score: 9.0
tags:
  - personas
  - roles
  - mcp-servers
  - workflow
  - adhd-optimization
---

# Dopemux Roles & Personas - Comprehensive Guide

**TL;DR:** Roles control which MCP tools you have access to. Personas are behavioral guidelines that tell Claude Code how to approach tasks. Switch roles based on what you're doing (coding vs planning vs research). Let the persona guide Claude's behavior automatically.

---

## Quick Reference Table

| Role | MCP Servers | Complexity | Best For | Energy Level | Session Length |
|------|-------------|------------|----------|--------------|----------------|
| **quickfix** | 3 (ConPort, Serena, PAL apilookup) | 0.3-0.5 | Quick fixes, simple tasks | Low-Medium | 15-25 min |
| **act** | 4 (+ Zen) | 0.5-0.7 | Implementation, coding | Medium-High | 25-45 min |
| **research** | 7+ (+ GPT-R, Exa, Magic) | 0.4-0.6 | Deep research, learning | Medium | 30-60 min |
| **plan** | 5 (+ Task Orchestrator) | 0.6-0.8 | Strategic planning | High | 45-90 min |
| **architect** | 5 (+ Zen, Task Orch) | 0.7-0.9 | System design, ADRs | High | 60+ min |
| **reviewer** | 4 (Standard + Zen) | 0.4-0.6 | Code review, QA | Medium | 30-45 min |
| **debugger** | 4 (Standard + Zen) | 0.5-0.7 | Bug investigation | Medium-High | 30-60 min |
| **ops** | 5 (+ Deployment tools) | 0.6-0.8 | DevOps, deployment | High | 45-90 min |
| **all** | All available | 0.5-0.8 | Flexible work | Any | Any |
| **developer** | 4 (Standard set) | 0.5-0.7 | General development | Medium | 30-60 min |

**Standard Set:** ConPort, Serena, PAL apilookup, Zen

---

## Role Details

### 🏃 QUICKFIX - ADHD Quick Wins Mode

**MCP Servers:** 3
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)

**When to Use:**
- 🔥 Low energy / scattered attention
- 🔥 Quick bug fixes (< 30 min)
- 🔥 Simple documentation updates
- 🔥 Code formatting/cleanup
- 🔥 Adding comments/docstrings
- 🔥 Small refactors (single file)

**Why 3 Tools?**
- Minimal cognitive load
- Fast task switching
- No analysis paralysis
- Perfect for ADHD "I just need to fix this quick" moments

**ADHD Optimization:**
- **Complexity:** 0.3-0.5 (easy wins)
- **Session:** 15-25 minutes max
- **Break Frequency:** Every 20 min
- **Interruption Tolerance:** High (easy to resume)

**Typical Commands:**
```bash
dopemux start --role quickfix

# Inside Claude Code:
"Fix the bug in auth.py line 42"
"Add type hints to user_service.py"
"Update README with new setup steps"
```

**Example Workflow:**
1. Notice small bug or TODO
2. Switch to quickfix mode
3. Use Serena to find file/function
4. Make quick change
5. Use ConPort to log what you fixed
6. Done in 10-15 minutes

**Success Metrics:**
- ✅ Task completed in < 30 min
- ✅ No analysis paralysis
- ✅ Quick win dopamine hit
- ✅ Momentum maintained

---

### 🛠️ ACT - Implementation Mode

**MCP Servers:** 4
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (multi-model analysis)

**When to Use:**
- 💻 Implementing new features
- 💻 Writing tests
- 💻 Multi-file refactoring
- 💻 API endpoint development
- 💻 Service integration
- 💻 Database migrations

**Why Add Zen?**
- Deeper analysis capability
- Multi-model consensus for complex decisions
- Better architecture validation
- Still focused on execution (not endless planning)

**ADHD Optimization:**
- **Complexity:** 0.5-0.7 (moderate challenge)
- **Session:** 25-45 minutes
- **Break Frequency:** Every 30-40 min
- **Interruption Tolerance:** Medium (needs some flow)

**Typical Commands:**
```bash
dopemux start --role act

# Inside Claude Code:
"Implement user authentication endpoint"
"Add Redis caching to product service"
"Write integration tests for API"
"Refactor database query layer"
```

**Example Workflow:**
1. Check ConPort for current task context
2. Use Zen to analyze approach
3. Use Serena to navigate codebase
4. Implement feature with TDD
5. Log decisions to ConPort
6. Complete in 30-45 minutes

**Success Metrics:**
- ✅ Feature implemented and tested
- ✅ Design decisions logged
- ✅ Code quality maintained
- ✅ Flow state achieved

---

### 🔬 RESEARCH - Deep Learning Mode

**MCP Servers:** 7+
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (multi-model analysis)
- ✅ GPT-Researcher (web search + synthesis)
- ✅ Exa (semantic web search)
- ✅ Magic (additional tools)

**When to Use:**
- 📚 Learning new technology/framework
- 📚 Evaluating architectural approaches
- 📚 Competitive analysis
- 📚 Literature review for features
- 📚 Best practices research
- 📚 Problem space exploration

**Why Full Research Stack?**
- GPT-Researcher does autonomous multi-source research
- Exa provides semantic search (not just keywords)
- Zen synthesizes findings from multiple sources
- PAL apilookup provides authoritative documentation

**ADHD Optimization:**
- **Complexity:** 0.4-0.6 (interesting but not overwhelming)
- **Session:** 30-60 minutes (with structure)
- **Break Frequency:** Every 45 min
- **Interruption Tolerance:** Medium-High (research can pause)

**Typical Commands:**
```bash
dopemux start --role research

# Inside Claude Code:
"Research ADHD-optimized UX patterns for dashboards"
"Compare Redis vs Memcached for our use case"
"Find best practices for Python async error handling"
"What are the latest ADHD intervention studies (2023-2025)?"
```

**Example Workflow:**
1. Define research question clearly
2. Use GPT-Researcher for comprehensive web search
3. Use Exa for semantic paper/article search
4. Use PAL apilookup for official docs
5. Use Zen to synthesize findings
6. Log research summary to ConPort
7. Complete with actionable insights

**Success Metrics:**
- ✅ Clear answer to research question
- ✅ Multiple sources cited
- ✅ Actionable recommendations
- ✅ Research saved to ConPort

**Perfect For:**
- 🎯 HYPERFOCUS REVIVAL research (like we're doing now!)
- 🎯 Technology evaluation
- 🎯 Architecture decision research
- 🎯 Learning new domains

---

### 📋 PLAN - Strategic Planning Mode

**MCP Servers:** 5
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (multi-model analysis)
- ✅ Task Orchestrator (task management)

**When to Use:**
- 📅 Sprint planning
- 📅 Feature breakdown
- 📅 Roadmap creation
- 📅 Technical debt prioritization
- 📅 Release planning
- 📅 Architecture planning (with architect role)

**Why Add Task Orchestrator?**
- Integrates with Leantime PM system
- Manages task dependencies
- Tracks progress across sprints
- Maintains two-plane architecture (cognitive + PM)

**ADHD Optimization:**
- **Complexity:** 0.6-0.8 (requires focus)
- **Session:** 45-90 minutes
- **Break Frequency:** Every 45-60 min
- **Interruption Tolerance:** Low (planning needs continuity)

**Typical Commands:**
```bash
dopemux start --role plan

# Inside Claude Code:
"Break down HYPERFOCUS REVIVAL feature into tasks"
"Create implementation roadmap for F001"
"Prioritize technical debt for next sprint"
"Plan Week 4 development schedule"
```

**Example Workflow:**
1. Review current project state (ConPort)
2. Use Zen to analyze feature complexity
3. Break down into tasks (Task Orchestrator)
4. Estimate effort and dependencies
5. Create implementation timeline
6. Log planning decisions to ConPort
7. Export to Leantime for PM tracking

**Success Metrics:**
- ✅ Clear task breakdown
- ✅ Dependencies identified
- ✅ Timeline realistic
- ✅ Team can execute from plan

**Best Practices:**
- 🎯 Plan when energy is high
- 🎯 Use timeboxes (45 min planning, 15 min break)
- 🎯 Don't over-plan (diminishing returns)
- 🎯 Focus on next 1-2 weeks, not months

---

### 🏗️ ARCHITECT - System Design Mode

**MCP Servers:** 5
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (multi-model analysis)
- ✅ Task Orchestrator (planning)

**When to Use:**
- 🏛️ Designing new systems/services
- 🏛️ Writing Architecture Decision Records (ADRs)
- 🏛️ System refactoring planning
- 🏛️ Evaluating architectural patterns
- 🏛️ Database schema design
- 🏛️ API design

**Why This Configuration?**
- Zen provides deep architectural analysis
- ConPort logs all design decisions (ADRs)
- Serena explores existing codebase patterns
- PAL apilookup references best practices

**ADHD Optimization:**
- **Complexity:** 0.7-0.9 (high cognitive load)
- **Session:** 60+ minutes (needs flow)
- **Break Frequency:** Every 60 min
- **Interruption Tolerance:** Very Low (requires deep focus)

**Typical Commands:**
```bash
dopemux start --role architect

# Inside Claude Code:
"Design the HYPERFOCUS REVIVAL service architecture"
"Create ADR for event-driven detection system"
"Design database schema for untracked work storage"
"Evaluate event sourcing vs CRUD for this feature"
```

**Example Workflow:**
1. Define problem space (ConPort context)
2. Research patterns (PAL apilookup + Zen)
3. Explore existing architecture (Serena)
4. Design solution with trade-offs
5. Create ADR documenting decision
6. Review with Zen for validation
7. Log to ConPort for future reference

**Success Metrics:**
- ✅ Clear architecture design
- ✅ Trade-offs documented
- ✅ ADR written and reviewed
- ✅ Implementation path clear

**Best Practices:**
- 🎯 Schedule during hyperfocus windows
- 🎯 Protect from interruptions (ADHD critical!)
- 🎯 Use design-first approach (don't code yet)
- 🎯 Document decisions immediately

**Perfect For:**
- 🎯 HYPERFOCUS REVIVAL system design
- 🎯 Major refactoring planning
- 🎯 New service creation
- 🎯 Performance optimization design

---

### 👁️ REVIEWER - Code Review Mode

**MCP Servers:** 4
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (analysis)

**When to Use:**
- 🔍 Code review (PRs)
- 🔍 Security audit
- 🔍 Performance review
- 🔍 Test coverage analysis
- 🔍 Documentation review
- 🔍 Technical debt assessment

**ADHD Optimization:**
- **Complexity:** 0.4-0.6 (analytical, not creative)
- **Session:** 30-45 minutes
- **Break Frequency:** Every 30-40 min
- **Interruption Tolerance:** High (review can pause/resume)

**Typical Commands:**
```bash
dopemux start --role reviewer

# Inside Claude Code:
"Review the auth service changes"
"Check test coverage for user module"
"Security review of API endpoints"
"Assess performance of database queries"
```

**Example Workflow:**
1. Load PR context (Serena)
2. Review code changes systematically
3. Check against best practices (PAL apilookup)
4. Use Zen for deeper analysis
5. Log findings to ConPort
6. Provide constructive feedback

**Success Metrics:**
- ✅ Comprehensive review completed
- ✅ Issues identified with solutions
- ✅ Positive feedback given
- ✅ Learning opportunities noted

---

### 🐛 DEBUGGER - Root Cause Analysis Mode

**MCP Servers:** 4
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (analysis)

**When to Use:**
- 🔬 Complex bug investigation
- 🔬 Production incident analysis
- 🔬 Performance debugging
- 🔬 Memory leak investigation
- 🔬 Race condition hunting
- 🔬 Integration failures

**ADHD Optimization:**
- **Complexity:** 0.5-0.7 (detective work)
- **Session:** 30-60 minutes
- **Break Frequency:** Every 40-50 min
- **Interruption Tolerance:** Low (lose investigation thread)

**Typical Commands:**
```bash
dopemux start --role debugger

# Inside Claude Code:
"Investigate authentication failures in production"
"Find root cause of memory leak in worker"
"Debug why API response times spiked"
"Trace why tests are flaky"
```

**Example Workflow:**
1. Reproduce the issue
2. Gather symptoms and logs
3. Form hypotheses (Zen analysis)
4. Navigate code systematically (Serena)
5. Test hypotheses
6. Identify root cause
7. Log findings and fix to ConPort

**Success Metrics:**
- ✅ Root cause identified
- ✅ Fix implemented/planned
- ✅ Prevention strategy documented
- ✅ Learning captured

**ADHD Tips:**
- 🎯 Timebox investigation (don't spiral)
- 🎯 Document hypotheses as you go
- 🎯 Take breaks when stuck
- 🎯 Celebrate finding the bug!

---

### ⚙️ OPS - DevOps/Deployment Mode

**MCP Servers:** 5+
- ✅ ConPort (context/decisions)
- ✅ Serena (code navigation)
- ✅ PAL apilookup (documentation)
- ✅ Zen (analysis)
- ✅ Deployment tools (Docker, K8s access)

**When to Use:**
- 🚀 Production deployment
- 🚀 Infrastructure updates
- 🚀 CI/CD configuration
- 🚀 Monitoring setup
- 🚀 Incident response
- 🚀 Scaling operations

**ADHD Optimization:**
- **Complexity:** 0.6-0.8 (high stakes)
- **Session:** 45-90 minutes
- **Break Frequency:** Every 45-60 min
- **Interruption Tolerance:** Very Low (deployment critical)

**Typical Commands:**
```bash
dopemux start --role ops

# Inside Claude Code:
"Deploy HYPERFOCUS REVIVAL service to production"
"Update Kubernetes configs for scaling"
"Set up monitoring for new service"
"Investigate production incident"
```

**Success Metrics:**
- ✅ Deployment successful
- ✅ Rollback plan ready
- ✅ Monitoring configured
- ✅ Runbook updated

**Best Practices:**
- 🎯 Deploy during low-traffic windows
- 🎯 Have rollback plan ready
- 🎯 Monitor actively after deploy
- 🎯 Document everything

---

### 🌟 ALL - Flexible Mode (All Tools)

**MCP Servers:** All available (10+)
- ✅ All cognitive tools
- ✅ All research tools
- ✅ All development tools
- ✅ All deployment tools

**When to Use:**
- 🔄 Exploratory work (don't know what you need)
- 🔄 Full-stack feature development
- 🔄 Rapid prototyping
- 🔄 Emergency fixes (need everything)

**ADHD Warning:**
- ⚠️ Too many tools = decision paralysis
- ⚠️ Use sparingly, prefer specific roles
- ⚠️ Easy to get distracted with all options

**Best For:**
- Experienced users who know what they need
- Short sessions with clear goals
- When role-switching overhead is too high

---

### 💻 DEVELOPER - General Development Mode

**MCP Servers:** 4 (Standard set)
- ✅ ConPort
- ✅ Serena
- ✅ PAL apilookup
- ✅ Zen

**When to Use:**
- 🔧 General development work
- 🔧 When other roles don't fit
- 🔧 Mixed tasks in one session

**ADHD Optimization:**
- **Complexity:** 0.5-0.7 (moderate)
- **Session:** 30-60 minutes
- **Break Frequency:** Every 40 min
- **Interruption Tolerance:** Medium

**Note:** This is the default fallback role.

---

## Persona Behavioral Guidelines

Each role has associated **persona guidelines** that Claude Code follows automatically. These are NOT separate agents - they're instructions for how Claude should behave.

### Available Personas:

1. **Backend Architect** - APIs, databases, scalability
2. **Frontend Architect** - UI, UX, React/Vue patterns
3. **DevOps Architect** - Infrastructure, deployment, monitoring
4. **Performance Engineer** - Optimization, profiling, benchmarking
5. **Quality Engineer** - Testing, test automation, quality assurance
6. **Security Engineer** - Security review, vulnerability assessment
7. **Refactoring Expert** - Code cleanup, technical debt
8. **Requirements Analyst** - Feature analysis, user stories
9. **Root Cause Analyst** - Debugging, investigation
10. **Technical Writer** - Documentation, guides, tutorials
11. **System Architect** - System design, architectural patterns
12. **Socratic Mentor** - Teaching, explaining, guiding
13. **Learning Guide** - Learning paths, skill development
14. **Statusline Setup** - Dopemux statusline configuration

**How Personas Work:**

When you use a role, Claude Code applies relevant persona guidelines:

```markdown
## Backend Architect Persona Guidelines

When working on backend tasks:
- ✅ Use Serena for code navigation (never bash cat/grep)
- ✅ Log design decisions to ConPort
- ✅ Use PAL apilookup for official docs
- ✅ Use Zen for architectural analysis
- ✅ Apply SOLID principles
- ✅ Consider scalability and performance
- ✅ Write comprehensive tests
```

Claude reads these guidelines and applies them contextually. You don't "activate" a persona - Claude applies the relevant guidelines based on your task.

---

## Role Selection Decision Tree

```
START: What are you doing?

├─ Quick fix/simple task? → QUICKFIX
├─ Implementing feature? → ACT
├─ Need to research something? → RESEARCH
├─ Planning sprint/feature? → PLAN
├─ Designing architecture? → ARCHITECT
├─ Reviewing code? → REVIEWER
├─ Debugging issue? → DEBUGGER
├─ Deploying/ops work? → OPS
├─ Don't know/mixed tasks? → DEVELOPER
└─ Need everything? → ALL (use sparingly!)
```

---

## ADHD-Specific Role Recommendations

### Low Energy (⚡↓)
**Best Roles:**
1. QUICKFIX (3 tools, easy wins)
2. REVIEWER (analytical, not creative)
3. DEVELOPER (moderate complexity)

**Avoid:**
- ARCHITECT (too demanding)
- PLAN (requires sustained focus)

### Medium Energy (⚡=)
**Best Roles:**
1. ACT (balanced implementation)
2. DEVELOPER (general work)
3. DEBUGGER (interesting detective work)
4. RESEARCH (structured exploration)

### High Energy (⚡↑)
**Best Roles:**
1. ARCHITECT (deep design work)
2. PLAN (strategic thinking)
3. ACT (complex implementation)
4. OPS (critical deployment)

### Hyperfocus (⚡⚡)
**Best Roles:**
1. ARCHITECT (channel energy into design)
2. ACT (flow state implementation)
3. DEBUGGER (deep investigation)

**Protect with:**
- Hyperfocus protection mode
- Break reminders disabled temporarily
- ConPort logging active (capture insights)

### Scattered Attention (👁️🌀)
**Best Roles:**
1. QUICKFIX (quick wins, easy resume)
2. REVIEWER (can pause/resume)

**Avoid:**
- ARCHITECT (requires deep focus)
- DEBUGGER (lose investigation thread)
- PLAN (needs continuity)

---

## How to Switch Roles

### Method 1: CLI (Recommended)
```bash
# Start with specific role
dopemux start --role quickfix
dopemux start --role act
dopemux start --role research

# Preview changes without applying
dopemux start --role act --dry-run

# Switch within tmux orchestrator
dopemux tmux agent switch-role research
dopemux tmux agent switch-role plan --target secondary
```

### Method 2: Manual Script (Legacy)
```bash
~/.claude/switch-role.sh quickfix
~/.claude/switch-role.sh act
```

### Method 3: Environment + Config Verification
1. Confirm role env var: `echo "$DOPEMUX_AGENT_ROLE"`
2. Inspect generated config: `cat ~/.claude/config/mcp_servers.json`
3. Restart Claude Code to apply the updated tool set

---

## Best Practices

### ✅ DO:
- **Match role to task** - Use quickfix for quick tasks, architect for design
- **Match role to energy** - Low energy → quickfix, high energy → architect
- **Switch roles during session** - As tasks change
- **Use ConPort** - Log what you did in each role
- **Timebox sessions** - Especially for high-complexity roles
- **Protect hyperfocus** - Disable notifications in architect/debugger modes

### ❌ DON'T:
- **Use ALL role by default** - Too many tools = analysis paralysis
- **Force architect role when tired** - Recipe for frustration
- **Switch roles too frequently** - Switching has overhead (2-5 min)
- **Ignore energy levels** - Forcing high-complexity work when tired backfires
- **Skip ConPort logging** - Lose context between sessions

---

## Common Role Combinations (Multi-Pane)

Dopemux supports multiple agent panes in tmux. Common combinations:

### Research + Implementation
```bash
# Pane 1: Research mode
dopemux tmux agent switch-role research --pane 1

# Pane 2: Act mode
dopemux tmux agent switch-role act --pane 2

# Workflow: Research in pane 1, implement in pane 2
```

### Architect + Developer
```bash
# Pane 1: Architect (design)
dopemux tmux agent switch-role architect --pane 1

# Pane 2: Developer (implement design)
dopemux tmux agent switch-role developer --pane 2
```

### Reviewer + Refactoring
```bash
# Pane 1: Review code
dopemux tmux agent switch-role reviewer --pane 1

# Pane 2: Fix issues found
dopemux tmux agent switch-role act --pane 2
```

---

## Example: HYPERFOCUS REVIVAL Implementation

**Phase 1: Research**
```bash
dopemux start --role research

# Task: Research ADHD neuroscience, interventions, UX patterns
# MCP servers: GPT-Researcher, Exa, Zen, PAL apilookup
# Energy: Medium
# Duration: 60 minutes
# Output: Research document with citations
```

**Phase 2: Architecture Design**
```bash
dopemux start --role architect

# Task: Design HYPERFOCUS REVIVAL system architecture
# MCP servers: Zen (analysis), ConPort (ADR storage), Serena
# Energy: High (hyperfocus ideal)
# Duration: 90 minutes
# Output: ADR, system design, database schema
```

**Phase 3: Planning**
```bash
dopemux start --role plan

# Task: Break down implementation into tasks
# MCP servers: Task Orchestrator, ConPort, Zen
# Energy: High
# Duration: 60 minutes
# Output: Task breakdown, timeline, dependencies
```

**Phase 4: Implementation**
```bash
dopemux start --role act

# Task: Implement detection engine
# MCP servers: Serena, ConPort, PAL apilookup, Zen
# Energy: Medium-High
# Duration: 45 minutes per session (multiple sessions)
# Output: Working code, tests, decisions logged
```

**Phase 5: Review & Polish**
```bash
dopemux start --role reviewer

# Task: Code review, test coverage, documentation
# MCP servers: Serena, ConPort, PAL apilookup, Zen
# Energy: Medium
# Duration: 30 minutes
# Output: Reviewed code, updated docs
```

---

## Troubleshooting

### "Too many tools, can't decide what to use"
→ Switch to more specific role (quickfix, act)
→ ADHD brain overwhelmed by choice
→ Fewer tools = clearer path

### "Role doesn't have tool I need"
→ Use `--role all` temporarily
→ Or switch roles mid-task
→ Example: Start with `act`, switch to `research` when stuck

### "Switching roles breaks my flow"
→ Plan role switches during natural breaks
→ Use multi-pane setup (different roles in different panes)
→ Cache common roles in tmux windows

### "Forgot which role I'm in"
→ Check statusline (shows active role)
→ Run `/mcp` in Claude Code to see tools
→ `dopemux status` shows current configuration

---

## Quick Start Cheat Sheet

```bash
# LOW ENERGY - Quick wins only
dopemux start --role quickfix

# MEDIUM ENERGY - General development
dopemux start --role act

# HIGH ENERGY - Architecture or planning
dopemux start --role architect
dopemux start --role plan

# NEED TO LEARN - Research mode
dopemux start --role research

# DEBUGGING - Root cause analysis
dopemux start --role debugger

# CODE REVIEW - Analytical work
dopemux start --role reviewer

# DEPLOYMENT - High-stakes ops
dopemux start --role ops

# EVERYTHING - When in doubt (use sparingly)
dopemux start --role all
```

---

## Summary

**Roles = MCP Tool Access**
- Controls which servers you can use
- Reduces cognitive load by limiting choices
- Optimized for ADHD energy levels

**Personas = Behavioral Guidelines**
- Tells Claude how to approach tasks
- Applied automatically based on context
- Not separate agents to manage

**Best Practice:**
1. Match role to task complexity
2. Match role to energy level
3. Switch roles as needed
4. Use ConPort to preserve context
5. Timebox high-complexity roles

**For HYPERFOCUS REVIVAL:**
- Research phase: `research` role
- Design phase: `architect` role
- Planning phase: `plan` role
- Implementation: `act` role
- Review: `reviewer` role

---

**Document Status:** Comprehensive Guide - Ready to Use
**Next Steps:** Practice switching roles based on your current energy/task
**Tip:** Start with `quickfix` or `act` until you're comfortable with role-switching
