---
id: architecture-revision
title: Architecture Revision
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Architecture Revision (reference) for dopemux documentation and developer
  workflows.
---
# Architecture Revision: Use Zen MCP for Multi-Model Access
**Date**: 2025-10-15
**Finding**: CLI spawning has TTY limitations
**Solution**: Leverage Zen MCP's multi-model capabilities

---

## Discovery: CLI Spawning Challenges

### Test Results:
- ✅ **Claude**: Spawned successfully (PID 60644)
- ⚠️ **Gemini**: Requires `--prompt` or interactive mode
- ❌ **Codex**: Requires TTY ("stdout is not a terminal")

### Root Cause:
AI CLIs expect interactive terminals (TTY) but subprocess.Popen provides pipes.

**Options**:
1. Use PTY (pseudo-terminal) - complex, platform-specific
1. Use non-interactive CLI modes - limited functionality
1. **Use Zen MCP** - already provides multi-model access!

---

## Revised Architecture: Dopemux + Zen MCP

### Current Session IS the Primary AI
- **You're already IN Claude Code** (this conversation!)
- **Dopemux orchestrator** sends commands TO current Claude session
- **Claude uses Zen MCP** for multi-model access

### New Flow:

```
User types in Dopemux Chat (Pane 3)
         ↓
Dopemux Command Parser
         ↓
    Routing Decision:
    ├─ Research? → Use zen/thinkdeep with Gemini
    ├─ Planning? → Stay in Claude, use zen/planner
    ├─ Implement? → Use zen/chat with Grok Code
    ├─ Consensus? → Use zen/consensus with multiple models
    └─ Debug? → Use zen/debug with Gemini
         ↓
   Zen MCP Tools
         ↓
   Multiple AI Models
   (Gemini, Grok, GPT-5, Claude, etc.)
```

### Advantages:

**1. Leverages Existing Infrastructure**
- ✅ Zen already coordinates multiple models
- ✅ Zen's clink tool can invoke other CLIs if needed
- ✅ No TTY issues
- ✅ No process management complexity

**2. Simpler Architecture**
- ❌ Don't spawn separate Claude instance (you're IN Claude!)
- ❌ Don't spawn Gemini/Codex (Zen provides access)
- ✅ Dopemux = workflow orchestrator
- ✅ Zen = model coordinator

**3. Better Multi-Model Coordination**
- Zen already handles conversation continuity
- Zen's consensus tool for multi-model decisions
- Zen's clink for CLI bridging when needed

---

## Refined Component Roles

### Dopemux Orchestrator:
**Role**: ADHD-optimized workflow management
- Parse user commands (research/plan/implement modes)
- Energy-aware task routing
- Auto-save to ConPort every 30s
- Session restoration with gentle re-orientation
- Break reminders and hyperfocus protection
- **Sends work to**: Zen MCP tools

### Zen MCP:
**Role**: Multi-model AI coordination
- Execute reasoning tasks (thinkdeep, planner, consensus)
- Bridge to other CLIs via clink if needed
- Handle model selection and conversation continuity
- **Returns results to**: Dopemux for presentation

### ConPort:
**Role**: Persistent context and knowledge graph
- Store decisions, checkpoints, progress
- Provide context to AI models
- Enable session restoration

---

## Implementation Changes

### Agent Spawner → Zen MCP Client

**Before** (Spawning separate CLIs):
```python
# spawn_er.py - Complex process management
spawner.start_all()  # Launch 3 separate AI processes
spawner.send_to_agent(AgentType.GEMINI, "question")
```

**After** (Using Zen MCP):
```python
# zen_client.py - Simple MCP tool calls
zen.thinkdeep(step="question", model="gemini")
zen.consensus(step="decision", models=[...])
zen.chat(prompt="question", model="grok-code")
```

### Message Bus → Zen Event Responses

**Before** (Tmux capture complexity):
```python
bus.capture_pane_output(pane_id, agent_name)
```

**After** (Direct responses):
```python
response = zen.chat(prompt="question")
bus.publish(Event(type=AGENT_OUTPUT, payload=response))
```

---

## Benefits of Revision

**Simplicity**:
- ✅ Eliminate complex process spawning
- ✅ Eliminate TTY/PTY handling
- ✅ Eliminate pane capture logic
- ✅ Eliminate agent health checking

**Reliability**:
- ✅ Zen handles model coordination (proven)
- ✅ Zen handles retries and errors
- ✅ Zen handles conversation continuity

**Capabilities**:
- ✅ Access to 27+ models via Zen
- ✅ Multi-model consensus built-in
- ✅ CLI bridging via clink when needed

**ADHD Focus**:
- ✅ Dopemux focuses on workflow + ADHD features
- ✅ Zen focuses on AI coordination
- ✅ Clear separation of concerns

---

## What Stays from Original Design

**Keep (Still Valuable)**:
- ✅ Tmux layout manager (energy-adaptive panes)
- ✅ Command parser (100% accurate routing)
- ✅ Checkpoint manager (auto-save to ConPort)
- ✅ Session restoration (gentle re-orientation)
- ✅ Message bus (for Dopemux internal events)
- ✅ Context protocol (ConPort sharing)

**Replace**:
- ❌ Agent Spawner → Zen MCP Client
- ❌ Tmux capture → Direct responses
- ❌ Process health checking → Zen reliability

---

## Updated Pane Layout

### Simplified 2-Pane Design:

```
┌────────────────────────────────────────────────┐
│ Pane 0: Dopemux Chat Interface (You)          │
│ • User input                                   │
│ • Command routing                              │
│ • ADHD features (energy, breaks, progress)    │
│ • Calls Zen MCP for AI work                   │
├────────────────────────────────────────────────┤
│ Pane 1: Monitoring Dashboard                  │
│ • Task status, energy level                   │
│ • System metrics (CPU, memory, API usage)     │
│ • Service health (ConPort, Zen, Redis)        │
│ • Recent activity log                          │
└────────────────────────────────────────────────┘
```

**Benefits**:
- Simpler (2 panes vs 4)
- Current Claude session continues in Pane 0
- No redundant AI instances
- All AI access via Zen MCP

---

## Implementation Path Forward

### Immediate (Next 2-3 Hours):

1. **Create Zen MCP Client** (replaces agent_spawner.py)
- Wrap Zen tools (thinkdeep, planner, consensus, chat, debug, codereview)
- Handle model selection based on mode
- Return structured responses

1. **Update Router** (use Zen instead of subprocess agents)
- Route research → zen.thinkdeep with Gemini
- Route planning → zen.planner with Claude
- Route implement → zen.chat with Grok Code
- Route consensus → zen.consensus with multiple models

1. **Test End-to-End**
- User command → Dopemux parse → Zen execute → Display result
- Verify auto-save works
- Test session restoration

### Benefits:

**Faster**: 2-3 hours vs 2-3 days to get working
**Simpler**: Use existing Zen infrastructure
**Better**: Proven multi-model coordination
**ADHD**: Focus on workflow features, not infrastructure

---

## Confidence Assessment

**Original Architecture** (Spawn separate CLIs):
- Complexity: High (process management, TTY, health checking)
- Risk: Medium (TTY issues, race conditions)
- Timeline: 2-3 days integration
- Confidence: 0.65 (Medium)

**Revised Architecture** (Use Zen MCP):
- Complexity: Low (call MCP tools)
- Risk: Low (Zen is proven)
- Timeline: 2-3 hours integration
- Confidence: 0.90 (Very High)

**Recommendation**: Adopt Zen MCP approach

---

## Next Steps

1. Create `src/zen_client.py` (Zen MCP wrapper)
1. Update `src/router.py` to use Zen client
1. Test `/mode research` → Zen thinkdeep with Gemini
1. Test `/consensus` → Zen consensus with multiple models
1. Integrate ConPort for real checkpoints
1. End-to-end demo

**Timeline**: Today! (2-3 hours to working demo)

---

**This is actually BETTER than the original plan!** 🎉
