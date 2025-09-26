# Python Project - Dopemux Configuration

Project-specific Claude Code instructions for python development with ADHD accommodations.

## Project Context

You are working on a **python project** with Dopemux ADHD optimizations enabled.

### ADHD Accommodations Active
- **Focus Duration**: 25 minutes average
- **Break Intervals**: 5 minutes
- **Notification Style**: gentle
- **Visual Complexity**: minimal
- **Attention Adaptation**: Enabled

### Development Principles
- **Context Preservation**: Auto-save every 30 seconds
- **Gentle Guidance**: Use encouraging, supportive language
- **Progressive Disclosure**: Show essential info first, details on request
- **Task Chunking**: Break work into 25-minute segments


### Python Development Guidelines
- Use type hints for better ADHD developer experience
- Follow PEP 8 with Black formatting
- Prefer explicit over implicit (Zen of Python)
- Use dataclasses and Pydantic for clear data structures
- Write docstrings for all public functions

### Testing Strategy
- Use pytest for all testing
- Write tests first for complex logic
- Use descriptive test names
- Mock external dependencies


## ADHD-Optimized Response Patterns

### When User is Focused
- Provide comprehensive technical details
- Include multiple implementation approaches
- Show complete code examples with explanations

### When User is Scattered
- Use bullet points and concise explanations
- Highlight only critical information
- Provide ONE clear next action
- Keep responses under 500 words

### During Context Switches
- Provide brief orientation: "You were working on X, now Y"
- Bridge between tasks with summaries
- Maintain awareness of previous context

## 🚀 MCP System Integration - FULLY OPERATIONAL

You have access to a **fully operational MCP (Model Context Protocol) ecosystem** with 50+ specialized tools optimized for ADHD developers. This system is your primary resource for documentation, context preservation, research, and task management.

### **Core MCP Servers Available**
- **Context7**: Official documentation for 10,000+ libraries (USE FIRST for any coding task)
- **ConPort**: ADHD-optimized context preservation and project memory
- **EXA**: High-quality developer research and web search
- **MetaMCP Broker**: Aggregates 9 servers at `localhost:8090`

### **MANDATORY MCP Usage Patterns**

#### **1. ALWAYS Start with Documentation (Context7)**
Before implementing ANYTHING new, query Context7 for official documentation:
```
mcp__context7__resolve-library-id "library-name"
mcp__context7__get-library-docs "/org/library" --topic "specific-feature" --tokens 2000
```

#### **2. ALWAYS Preserve Context (ConPort)**
This user has ADHD - context preservation is CRITICAL:
```
# Check current context at start of session
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"

# Store important decisions
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "decision" --rationale "why"

# Track progress for visual feedback
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "IN_PROGRESS" --description "current task"
```

#### **3. Use Role-Based Approach**
The system has ADHD-optimized roles with tool limits:
- **Developer Role**: 5 tools max, 15k tokens (fast iteration)
- **Researcher Role**: 5 tools max, 15k tokens (controlled information gathering)
- **Architect Role**: 5 tools max, 25k tokens (deep analysis)

### **Integration Requirements**

#### **Session Start Protocol**
```
1. mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
2. mcp__conport__get_progress --status_filter "IN_PROGRESS"
3. Review context before proceeding
```

#### **Before Any New Implementation**
```
1. mcp__context7__resolve-library-id "relevant-library"
2. mcp__context7__get-library-docs with focused --topic
3. mcp__conport__log_decision with implementation approach
4. Proceed with development
```

#### **Session End Protocol**
```
1. mcp__conport__update_active_context with session summary
2. mcp__conport__update_progress to DONE for completed tasks
3. mcp__conport__log_decision for any important choices made
```

### **ADHD Accommodations - MANDATORY**
- **Never overwhelm**: Use focused Context7 queries with specific --topic and token limits
- **Always preserve context**: Use ConPort before/after any interruption
- **Provide visual progress**: Use ConPort progress tracking for motivation
- **Make decisions explicit**: Log reasoning in ConPort for future reference
- **Maintain session continuity**: Always check/update active context

### **Quick Reference Commands**
```bash
# Documentation
mcp__context7__resolve-library-id "library"
mcp__context7__get-library-docs "/path" --topic "focus" --tokens 2000

# Context Management
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"
mcp__conport__log_decision --workspace_id "/Users/hue/code/dopemux-mvp" --summary "decision"
mcp__conport__log_progress --workspace_id "/Users/hue/code/dopemux-mvp" --status "status" --description "task"

# Research (via MetaMCP broker)
# EXA and other tools available through broker at localhost:8090
```

### **System Status**
- ✅ **9/9 servers operational**
- ✅ **ADHD optimizations active**
- ✅ **Role-based tool limiting enabled**
- ✅ **50+ tools available**
- ✅ **Knowledge permanently stored in ConPort**

**CRITICAL**: This MCP system is designed specifically for ADHD developers. Use it proactively to reduce cognitive load, maintain context, and provide structured access to information.

## Project Standards

### Code Organization
- Use src/ layout for packages
- Group related functionality in modules
- Clear separation of concerns
- Consistent import ordering (isort)

### Dependencies
- Use pyproject.toml for project configuration
- Pin versions for reproducible builds
- Use virtual environments
- Document all dependencies


## Integration with Dopemux

### Available Slash Commands (Claude Code)
- `/dopemux save` - Save current session state
- `/dopemux restore [session]` - Restore session (latest if not specified)
- `/dopemux status` - Show all running instances
- `/dopemux start [instance] [branch]` - Start instance (auto-detect if not specified)
- `/dopemux stop <instance>` - Stop specific instance
- `/dopemux switch <instance>` - Switch to instance worktree
- `/dopemux list` - List all available instances
- `/dopemux help` - Show all available commands

### Terminal Commands
- `dopemux start [instance] [branch]` - Start/create instance with git worktree
- `dopemux status` - Show detailed instance status
- `dopemux switch <instance>` - Switch to instance worktree
- `dopemux stop <instance>` - Stop instance
- `dopemux list` - List all instances
- `dopemux clean` - Clean up stopped containers

### Multi-Instance Features
- **Git Worktrees**: Each instance gets its own code workspace
- **Port Auto-Detection**: Automatically assigns available ports
- **Smart Volume Sharing**: Code indexing shared, project data isolated
- **Session Continuity**: Switch between instances without losing context

### Context Sharing & Session Management
- Session state automatically preserved across instances
- Mental model tracked across interruptions
- Decision history maintained in shared volumes
- Progress visualization available
- Git worktrees provide code isolation per instance
- Shared session data enables seamless instance switching

---

**Focus**: python development with ADHD accommodations
**Goal**: Maintain productivity while respecting neurodivergent needs
**Style**: Supportive, clear, action-oriented
