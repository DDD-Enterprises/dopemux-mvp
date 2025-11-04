# Python Project - Dopemux Configuration

Project-specific Claude Code instructions for python development with ADHD accommodations.

## ADHD Accommodations Active
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

---

**Focus**: python development with ADHD accommodations
**Goal**: Maintain productivity while respecting neurodivergent needs
## MCP Servers (Auto‑Wired)
- Global servers available in Claude Desktop:
  - mas-sequential-thinking, zen, context7 (stdio)
  - serena (SSE), exa (SSE), leantime-bridge (SSE)
  - task-orchestrator (stdio on-demand), gptr-researcher-stdio (stdio)
- Project ConPort is auto‑wired per worktree as `conport` (stdio via docker exec).

ConPort provides project‑local decisions and progress; the Dope Decision Graph mirrors and links these for cross‑project discovery.
