# Authority Matrix Module

**Module Version**: 2.0.0 (Simplified Architecture)
**Purpose**: Clear System Authority Boundaries Reference
**Usage**: Quick reference for preventing authority violations
**Decision Reference**: #132, #133, #134 (Simplified architecture)

## 🚨 CRITICAL AUTHORITY BOUNDARIES

### System Authority Matrix

| System | OWNS (Exclusive Authority) | NEVER Does |
|--------|---------------------------|------------|
| **ConPort (PostgreSQL AGE)** | Task storage (progress_entry)<br/>Task metadata (custom_data)<br/>Dependencies (link_conport_items)<br/>Architectural decisions<br/>Knowledge graph queries<br/>Context preservation (product & active) | PRD parsing<br/>ADHD metric calculation<br/>LSP operations<br/>Real-time session management |
| **SuperClaude** | PRD parsing via `/dx:prd-parse`<br/>25 standard commands execution<br/>15 specialized agents<br/>`/dx:` custom command routing<br/>Human review workflow (Approach C) | Task storage<br/>Decision logging<br/>Code navigation<br/>ADHD state tracking |
| **Python ADHD Engine** | Energy tracking & matching<br/>Cognitive load calculation (0-1)<br/>Break monitoring (25/60/90min)<br/>Attention state analysis<br/>Smart task recommendation<br/>Hyperfocus protection | Task storage<br/>PRD parsing<br/>LSP operations<br/>Knowledge graph management |
| **Serena LSP** | LSP protocol operations<br/>Code navigation & completion<br/>Symbol search & analysis<br/>Semantic code understanding<br/>Tree-sitter parsing<br/>Navigation caching | Task management<br/>Decision storage<br/>PRD decomposition<br/>Session timing |
| **React Ink Dashboard** | Visual task progress display<br/>ADHD metric visualization<br/>Real-time event rendering<br/>User interaction (task selection)<br/>Break reminders & notifications | Task data storage<br/>Business logic<br/>Authority decisions<br/>Data persistence |
| **Integration Bridge** | Async event routing (Redis Streams)<br/>Event bus pub/sub coordination<br/>MetaMCP role enforcement<br/>Multi-instance isolation | Task storage<br/>Decision logic<br/>PRD parsing<br/>ADHD calculations |

## 🔄 Communication Flow Patterns

### Allowed Communication Paths (Simplified Architecture)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ SuperClaude │────>│ Python Validator │────>│   ConPort   │
│/dx:prd-parse│     │ (ADHD metadata)  │     │ (batch imp) │
└─────────────┘     └──────────────────┘     └─────────────┘
                                                     │
                                                     v
                                              ┌──────────────┐
                                              │ Integration  │
                                              │    Bridge    │
                                              │ (event pub)  │
                                              └──────────────┘
                                                     │
                          ┌──────────────────────────┼──────────────┐
                          v                          v              v
                   ┌─────────────┐          ┌────────────┐  ┌──────────┐
                   │   ADHD      │          │  Dashboard │  │  Serena  │
                   │   Engine    │          │  (React)   │  │   LSP    │
                   └─────────────┘          └────────────┘  └──────────┘
```

### Implementation Flow Example

```
1. User: /dx:implement
   └─> ADHD Engine queries ConPort for optimal task
       └─> ConPort returns task with metadata
           └─> ADHD Engine starts 25min session
               └─> Integration Bridge publishes "session_started"
                   ├─> Dashboard shows timer
                   └─> ConPort updates active_context

2. Every 5 minutes: Auto-save
   └─> ConPort.update_progress(task_id, status)
       └─> Integration Bridge publishes "progress_updated"
           └─> Dashboard updates progress bar

3. At 25 minutes: Break reminder
   └─> ADHD Engine triggers break
       └─> Integration Bridge publishes "break_reminder"
           └─> Dashboard shows notification: "Great work! Time for 5min break"
               └─> ConPort logs break in custom_data
```

## ⚡ Event Flow Authority

### Task Lifecycle Events

| Event Type | Authoritative Source | Can Update | Can Read | Event Flow |
|------------|---------------------|------------|----------|-----------|
| **Task Storage** | ConPort | ConPort only | All systems | ConPort → Integration Bridge → All subscribers |
| **Task Creation** | SuperClaude + Human | SuperClaude validates → ConPort stores | All systems | SuperClaude → Validator → ConPort → Bridge → All |
| **Decisions** | ConPort | ConPort only | All systems | ConPort → Bridge → All |
| **ADHD State** | Python ADHD Engine | ADHD Engine only | Dashboard, ConPort | ADHD Engine → Bridge → Dashboard |
| **Code Navigation** | Serena LSP | Serena only | ADHD Engine (for context) | Serena → (optional) ConPort decision → Bridge |
| **Session State** | ADHD Engine | ADHD Engine updates → ConPort stores | Dashboard, ConPort | ADHD Engine → ConPort → Bridge → Dashboard |

## 🛡️ Violation Prevention

### Common Violations to Prevent

❌ **Serena modifying task status**
- **Why wrong**: Serena is for code navigation, ConPort owns task data
- **Correct**: Serena reads ConPort for context, never modifies tasks

❌ **SuperClaude directly storing decisions**
- **Why wrong**: SuperClaude parses PRDs, ConPort stores decisions
- **Correct**: SuperClaude generates JSON → Human approves → ConPort stores

❌ **ADHD Engine storing task data**
- **Why wrong**: ADHD Engine recommends, ConPort stores
- **Correct**: ADHD Engine queries ConPort → recommends → user selects → ConPort updates

❌ **Dashboard modifying ConPort directly**
- **Why wrong**: Dashboard is view layer only
- **Correct**: Dashboard triggers user action → Python service → ConPort update → Bridge event → Dashboard re-render

❌ **Integration Bridge storing data**
- **Why wrong**: Bridge is routing only, not storage
- **Correct**: Bridge routes events, ConPort/Serena/ADHD Engine store data

### Authority Enforcement Checks

```python
# Integration Bridge enforces these rules
def check_authority(operation: str, requester: str) -> bool:
    AUTHORITY_RULES = {
        "update_task_status": ["conport"],
        "store_decision": ["conport"],
        "parse_prd": ["superclaude"],
        "calculate_adhd_metrics": ["adhd_engine"],
        "lsp_operations": ["serena"],
        "route_events": ["integration_bridge"],
    }

    allowed_systems = AUTHORITY_RULES.get(operation, [])
    if requester not in allowed_systems:
        raise AuthorityViolationError(
            f"{requester} cannot perform {operation}. "
            f"Only {allowed_systems} have authority."
        )
    return True
```

## 🎯 Quick Decision Guide

**Need to store a task?** → ConPort `log_progress`
**Need to parse a PRD?** → SuperClaude `/dx:prd-parse`
**Need to calculate energy level?** → Python ADHD Engine
**Need code navigation?** → Serena LSP
**Need to log a decision?** → ConPort `log_decision`
**Need to route events?** → Integration Bridge
**Need to show UI?** → React Ink Dashboard

**Need to coordinate multiple systems?** → Integration Bridge publishes event → All subscribers react

## 📊 Authority Decision Tree

```
┌─ Need to interact with tasks?
│
├─ Store/Update task data?
│  └─> ConPort (progress_entry + custom_data)
│
├─ Parse PRD into tasks?
│  └─> SuperClaude /dx:prd-parse → Human review → ConPort batch import
│
├─ Recommend which task to work on?
│  └─> Python ADHD Engine queries ConPort → recommends → user selects
│
└─ Display tasks in UI?
   └─> React Ink Dashboard subscribes to Integration Bridge events

┌─ Need to interact with code?
│
├─ Navigate/search code?
│  └─> Serena LSP (go-to-definition, find-references, etc.)
│
├─ Store architectural decision about code?
│  └─> ConPort log_decision (Serena NEVER stores decisions)
│
└─ Analyze code complexity for ADHD?
   └─> Serena provides code context → Python ADHD Engine calculates

┌─ Need to manage ADHD accommodations?
│
├─ Calculate energy/attention state?
│  └─> Python ADHD Engine (owns all ADHD calculations)
│
├─ Store ADHD metadata about tasks?
│  └─> ConPort custom_data category "task_metadata"
│
├─ Track session timing?
│  └─> Python ADHD Engine (25min timer) → ConPort (stores history)
│
└─ Show break reminders?
   └─> Python ADHD Engine triggers → Integration Bridge → Dashboard displays
```

## 🔐 MetaMCP Role-Based Boundaries

Integration Bridge enforces tool-level access per role:

| Role | Max Tools | Allowed Operations | Authority Enforcement |
|------|-----------|-------------------|---------------------|
| **QUICKFIX** | 8 tools | Basic code fixes, simple task updates | Limited ConPort + Serena access |
| **ACT** | 10 tools | Full implementation, code nav, progress tracking | Full Serena + ConPort progress |
| **PLAN** | 9 tools | Architecture, consensus, decision logging | Zen + ConPort decisions |
| **RESEARCH** | 10 tools | Deep research, analysis, investigation | Zen + Exa + GPT-Researcher |
| **ALL** | 60+ tools | Full access (use sparingly - cognitive overload) | All systems |

**ADHD Principle**: Limit tools per role to reduce cognitive load while maintaining necessary capabilities.

---

**Migration Notes:**

**What Changed from v1.0:**
- ❌ Removed: Two-Plane architecture (PM Plane vs Cognitive Plane)
- ❌ Removed: Leantime (status authority)
- ❌ Removed: Task-Master-AI (PRD parsing)
- ❌ Removed: jpicklyk Task-Orchestrator (37 tools)
- ✅ Simplified: ConPort as single source of truth for tasks AND decisions
- ✅ Added: SuperClaude for PRD parsing with human review
- ✅ Added: Python ADHD Engine for cognitive optimization
- ✅ Kept: Integration Bridge (now simpler event routing, not cross-plane coordination)
- ✅ Kept: Serena LSP (code intelligence)

---

**See Also:**
- `.claude/modules/coordination/integration-bridge.md` - Event routing details
- `.claude/modules/superclaude-integration.md` - SuperClaude configuration
- `.claude/modules/pm-plane/task-orchestrator.md` - ConPort task management
