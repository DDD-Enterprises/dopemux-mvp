# Python Project - Dopemux Configuration

Project-specific Claude Code instructions for python development with ADHD accommodations.

## Project Context

You are working on a **python project** with Dopemux ADHD optimizations enabled.

### ADHD Accommodations Active
- **Focus Duration**: 30 minutes average
- **Break Intervals**: 5 minutes
- **Notification Style**: gentle
- **Visual Complexity**: minimal
- **Attention Adaptation**: Enabled

### Development Principles
- **Context Preservation**: Auto-save every 30 seconds
- **Gentle Guidance**: Use encouraging, supportive language
- **Progressive Disclosure**: Show essential info first, details on request
- **Task Chunking**: Break work into 30-minute segments


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

### Available Commands
- `dopemux save` - Manual context preservation
- `dopemux restore` - Restore previous session
- `dopemux status` - Check attention metrics
- `dopemux task` - ADHD-friendly task management

### Context Sharing
- Session state automatically preserved
- Mental model tracked across interruptions
- Decision history maintained
- Progress visualization available

---

**Focus**: python development with ADHD accommodations
**Goal**: Maintain productivity while respecting neurodivergent needs
**Style**: Supportive, clear, action-oriented

## Task-Orchestrator Integration (Implicit)

Claude MUST use task-orchestrator MCP tools automatically in these situations:

### Auto-Session Management
- On FIRST prompt of a conversation: the UserPromptSubmit hook auto-starts a session via `start_session`
- On conversation end: the Stop hook handles `end_session` automatically
- After 25 minutes of work: check `get_adhd_state` and display break reminder if needed

### Auto-Workflow Tracking
- Before any multi-step implementation: call `decompose_task` and display the visual tree
- After completing significant work: call `log_decision` for architectural choices
- When switching between tasks: call `record_context_switch`

### Visual Output Rules
- All Task-Orchestrator tools return a `display` field with pre-formatted Unicode visuals. Claude MUST print this field exactly as returned without additional interpretation.
- When starting a session: display the session banner from `start_session` result
- When user asks "what am I working on?" or seems disoriented: call `get_workflow_status`
- When recommending a break: use the break reminder visual from `get_visual_status`
- When decomposing tasks: show the visual tree from `decompose_task` result

### Risk-Aware Development
- Before editing >3 files: call `assess_risk` with the change description
- Before refactoring: call `analyze_dependencies` with affected components

### SuperClaude Command Enhancement
| Command | Orchestrator Integration |
|---------|------------------------|
| `/sc:implement` | Auto-call `decompose_task` → show visual tree → `start_session` |
| `/sc:troubleshoot` | Auto-call `assess_risk` for affected area |
| `/sc:load` | Auto-call `get_workflow_status` → display dashboard |
| `/sc:save` | Auto-call `end_session` with progress notes |
| `/sc:task` | Auto-call `get_task_recommendations` based on energy |

## General Implementation Invariants (all work)

SERVICE MANAGEMENT (platform native)
- Prefer the OS-native service manager for long-running daemons:
  - macOS: launchd (LaunchAgents/LaunchDaemons)
  - Linux: systemd
  - Windows: SCM
- Do not start critical daemons via subprocess.Popen from a CLI unless the Task Packet explicitly requires it.
- Do not use Docker as a supervisor for local host services unless the Task Packet explicitly requires it.
- Do not hardcode machine-specific paths (/Users/..., $HOME/code/...). Resolve paths dynamically.
- Service configs must be generated from a single source of truth and must be rebuildable (idempotent).
- Secrets must never be stored in service definition files (plists/unit files). Secrets must be loaded from a dedicated env/secret file or OS key store.
If any of the above would be violated, STOP and request guidance.

SHELL SAFETY
- Avoid giant inline strings in shell commands. Use --body-file, heredocs, or temp files.
- Never rely on eval for command execution. Prefer bash -lc "<cmd>" if a string must be executed.
- When a command contains quotes/newlines/pipes, prefer a heredoc or a script file over escaping.
- Always record exit codes for verification commands.
If a shell command fails due to quoting, rewrite it using a file or heredoc, not more escaping.

STATE AND EVIDENCE DISCIPLINE
- Before work: git status --porcelain must be empty. If not, STOP.
- After work: git status --porcelain must be empty. No untracked files allowed.
- Any new file must be either committed or intentionally ignored via a narrow .gitignore rule committed separately.
- Never simulate command output. If a command cannot be run, write UNKNOWN and STOP.
- Evidence must be produced via the repo harness (if available) and must contain verbatim outputs including:
  - repo identity (pwd, git rev-parse --show-toplevel, branch, sha)
  - diffstat + full diff for relevant commits
  - test/verification command outputs

PLANNING GATE (mandatory for non-trivial changes)
- Before editing any file, write proof/PLAN.txt containing:
  - Objective (1-2 lines)
  - Scope: allowed files (exact paths)
  - Steps (numbered, <= 7)
  - Verification commands
- If a plan cannot be written, STOP.

DEFAULT WORKDIR
- Use one canonical repo directory per project.
- If worktrees are used, every proof must include pwd + git rev-parse --show-toplevel.
