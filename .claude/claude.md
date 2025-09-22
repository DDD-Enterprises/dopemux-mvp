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
