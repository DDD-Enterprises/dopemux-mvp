# Authority Matrix Module

**Module Version**: 1.0.0
**Purpose**: Clear System Authority Boundaries Reference
**Usage**: Quick reference for preventing authority violations

## 🚨 CRITICAL AUTHORITY BOUNDARIES

### System Authority Matrix

| System | OWNS (Exclusive Authority) | NEVER Does |
|--------|---------------------------|------------|
| **Leantime** | Task status updates (planned→active→blocked→done)<br/>Team dashboards and reporting<br/>Milestone tracking and roadmap visibility<br/>Stakeholder communication | Task decomposition<br/>Architectural decisions<br/>Code navigation |
| **Task-Master** | PRD parsing and analysis<br/>AI-driven task decomposition<br/>Subtask hierarchy creation<br/>Complexity scoring | Status updates<br/>Decision storage<br/>Code exploration |
| **Task-Orchestrator** | Dependency analysis<br/>37 specialized orchestration tools<br/>Risk assessment and mitigation<br/>Workflow optimization | Initial task creation<br/>Status management<br/>Architectural decisions |
| **Serena** | Code navigation and LSP operations<br/>Symbol search and analysis<br/>Session memory (breadcrumbs)<br/>Developer interruption recovery | Task management<br/>Status updates<br/>Decision storage |
| **ConPort** | Architectural decisions and rationale<br/>Knowledge graph maintenance<br/>Progress logging (not status)<br/>Context preservation | Task status authority<br/>Task hierarchy creation<br/>LSP operations |
| **Integration Bridge** | Cross-plane coordination<br/>Event routing<br/>Authority boundary enforcement<br/>Multi-instance coordination | Direct system operations<br/>Business logic<br/>Data storage |

## 🔄 Communication Flow Patterns

### Allowed Communication Paths

```
Project Management Plane ↔ Integration Bridge ↔ Cognitive Plane
    ↕                              ↕                    ↕
Task-Master                 Event Routing            Serena
Task-Orchestrator          Authority Enforcement     ConPort
Leantime
```

### PROHIBITED Direct Communication
❌ **Serena ↔ Task-Master** (different planes)
❌ **ConPort ↔ Leantime** (different authorities)
❌ **Task-Orchestrator ↔ Serena** (different planes)

## ⚡ Event Flow Authority

### Task Lifecycle Events
```
1. Task Created: Task-Master → Integration Bridge → ConPort → Serena
2. Status Changed: Leantime → Integration Bridge → ConPort (log only)
3. Code Changed: Serena → ConPort → Integration Bridge → Leantime
4. Decision Made: ConPort → Integration Bridge (broadcast) → All systems
```

### Authority for Each Event Type

| Event Type | Authoritative Source | Can Update | Can Read |
|------------|---------------------|------------|----------|
| **Task Status** | Leantime | Leantime only | All systems |
| **Task Hierarchy** | Task-Master | Task-Master only | All systems |
| **Decisions** | ConPort | ConPort only | All systems |
| **Code Changes** | Serena | Serena only | All systems |
| **Dependencies** | Task-Orchestrator | Task-Orchestrator only | All systems |

## 🛡️ Violation Prevention

### Common Violations to Prevent

**Status Update Violations:**
```bash
# ❌ WRONG - Direct status update from non-Leantime system
task_orchestrator.update_task_status("active")

# ✅ CORRECT - Route through Integration Bridge to Leantime
integration_bridge.route_status_change("task-id", "active", "task-orchestrator")
```

**Decision Storage Violations:**
```bash
# ❌ WRONG - Storing decisions outside ConPort
leantime.log_architectural_decision("Use microservices")

# ✅ CORRECT - Store decisions in ConPort with proper authority
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
  --summary "Use microservices architecture" \
  --rationale "Supports multi-instance scaling requirements"
```

**Cross-Plane Communication Violations:**
```bash
# ❌ WRONG - Direct communication between planes
serena.request_task_breakdown()

# ✅ CORRECT - Route through Integration Bridge
integration_bridge.route_request("serena", "task-master", "task_breakdown")
```

## 🎯 ADHD-Optimized Authority Patterns

### Progressive Authority Disclosure
```bash
# Level 1: Essential authorities only
ESSENTIAL_AUTHORITIES = {
    "Leantime": "Status updates",
    "ConPort": "Decisions",
    "Serena": "Code navigation"
}

# Level 2: Full authority matrix (on request)
# Level 3: Event flow patterns (on request)
# Level 4: Violation prevention (on request)
```

### Authority Conflict Resolution

**Principle**: Always defer to the authoritative system
```bash
RESOLVE_AUTHORITY_CONFLICT() {
    CONFLICT_TYPE="$1"
    SYSTEMS=("$@")

    case "$CONFLICT_TYPE" in
        "status_disagreement")
            echo "🏆 Leantime is authoritative for status - deferring to Leantime"
            ;;
        "decision_conflict")
            echo "🏆 ConPort is authoritative for decisions - checking ConPort"
            ;;
        "task_hierarchy_dispute")
            echo "🏆 Task-Master is authoritative for hierarchies - validating with Task-Master"
            ;;
    esac
}
```

## 📋 Quick Reference Commands

### Authority Validation
```bash
# Check if system has authority for operation
CHECK_AUTHORITY() {
    SYSTEM="$1"
    OPERATION="$2"

    case "$SYSTEM:$OPERATION" in
        "leantime:update_status") echo "✅ AUTHORIZED" ;;
        "task-master:create_hierarchy") echo "✅ AUTHORIZED" ;;
        "conport:log_decision") echo "✅ AUTHORIZED" ;;
        "serena:navigate_code") echo "✅ AUTHORIZED" ;;
        *) echo "❌ NOT AUTHORIZED - Check authority matrix" ;;
    esac
}
```

### Communication Path Validation
```bash
# Validate communication path
VALIDATE_COMMUNICATION_PATH() {
    SOURCE="$1"
    TARGET="$2"

    # Check if cross-plane
    SOURCE_PLANE=$(get_system_plane "$SOURCE")
    TARGET_PLANE=$(get_system_plane "$TARGET")

    if [ "$SOURCE_PLANE" != "$TARGET_PLANE" ]; then
        if [ "$SOURCE" != "integration-bridge" ] && [ "$TARGET" != "integration-bridge" ]; then
            echo "❌ VIOLATION: Cross-plane communication must go through Integration Bridge"
            echo "   Correct path: $SOURCE → Integration Bridge → $TARGET"
            return 1
        fi
    fi

    echo "✅ VALID: Communication path authorized"
    return 0
}
```

## 🚀 Emergency Authority Override

### When Authority is Unclear
1. **Default to Integration Bridge**: Route through central coordinator
2. **Log the Uncertainty**: Record in ConPort for future clarification
3. **Ask for Clarification**: Prompt user to confirm authority
4. **Update Matrix**: Add new patterns to authority matrix

### Authority Matrix Updates
```bash
# When new systems are added or authority changes
UPDATE_AUTHORITY_MATRIX() {
    NEW_SYSTEM="$1"
    AUTHORITY_DOMAIN="$2"

    mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" \
      --summary "Authority matrix updated: $NEW_SYSTEM owns $AUTHORITY_DOMAIN" \
      --rationale "System integration requires clear authority boundaries" \
      --tags ["authority-matrix", "system-integration"]
}
```

## 🎨 Visual Authority Reference

### System Ownership Colors
- 🟦 **Leantime**: Blue (Status and visibility)
- 🟩 **Task-Master**: Green (Creation and hierarchy)
- 🟨 **Task-Orchestrator**: Yellow (Dependencies and optimization)
- 🟪 **Serena**: Purple (Code and navigation)
- 🟧 **ConPort**: Orange (Decisions and memory)
- ⚪ **Integration Bridge**: White (Coordination and routing)

### Authority Hierarchy
```
1. 🏆 System-Specific Authority (absolute)
2. 🔄 Integration Bridge Coordination (routing)
3. 📝 ConPort Decision Logging (historical)
4. 👤 User Override (last resort)
```