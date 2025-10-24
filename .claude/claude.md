# Project Claude Guide - Dopemux MCP

This project is auto-wired with Dopemux MCP servers and ConPort per-worktree memory.

## 🎉 RECENT ACHIEVEMENT: ConPort-KG 2.0 Phase 2 COMPLETE

**Date**: 2025-10-24
**Status**: ✅ PRODUCTION READY
**Quality**: 120/120 tests passing (100%)
**Performance**: ALL targets exceeded by 70-1300%

**What Was Built** (12 days, ~12,320 lines):
- Event processing infrastructure (deduplication, aggregation, patterns, circuit breakers)
- 6 agent integrations (Serena, Dope-Context, Zen, ADHD Engine, Desktop Commander, Task-Orchestrator)
- 16 event types, 7 pattern detectors
- Complete documentation and integration guide

**Key Files**:
- `services/mcp-integration-bridge/` - Event system infrastructure
- `services/mcp-integration-bridge/integrations/` - 6 agent integrations
- `services/mcp-integration-bridge/patterns/` - 7 pattern detectors
- `docs/94-architecture/AGENT_INTEGRATION_GUIDE.md` - Integration guide
- `docs/94-architecture/PHASE_2_COMPLETION_SUMMARY.md` - Complete summary

**Architecture**: Agents → EventBus → Dedup → Aggregate → Patterns → ConPort (auto-insights)

See Decision #247 in ConPort for complete details.

## MCP Servers

- Project (stdio):
  - `conport`: project memory (decisions + progress)
  - `conport-admin`: instance operations (fork, promote, promote_all)

- Global:
  - `ddg-mcp`: Dope Decision Graph tools (related decisions, search, instance diff)
  - `mas-sequential-thinking`, `zen`, `context7` (stdio)
  - `serena`, `exa`, `leantime-bridge` (SSE)
  - `task-orchestrator` (stdio on-demand)
  - `gptr-researcher-stdio` (stdio)

## Quick Usage Patterns

### Related Decisions (global)

Use `ddg-mcp.related_text` to find related global decisions by free text, or `related_decisions` for a known id.

Examples:
- ddg-mcp.related_text(query="Refactor ConPort schema migrations", workspace_id="${WORKSPACE}", k=8)
- ddg-mcp.related_decisions(decision_id="<uuid>", k=10)

Sample prompt:
```
Find decisions related to "optimize ConPort Redis caching", prefer items from this project.
Then summarize 3 most relevant with links to their worktrees.

→ Call: ddg-mcp.related_text(query="optimize ConPort Redis caching", workspace_id="${WORKSPACE}", k=8)
```

### Instance Diff (worktree comparison)

- ddg-mcp.instance_diff(workspace_id="${WORKSPACE}", a="feature-A", b="main", kind="progress")

Sample prompt:
```
Compare in-progress items between feature-branch and main. Highlight items only in the branch that look risky.

→ Call: ddg-mcp.instance_diff(workspace_id="${WORKSPACE}", a="feature-branch", b="main", kind="progress")
```

### ConPort Admin Operations

- ddg-mcp.conport_fork_instance(workspace_id="${WORKSPACE}", source_instance=None)
- ddg-mcp.conport_promote(progress_id="<uuid>")
- ddg-mcp.conport_promote_all(workspace_id="${WORKSPACE}")

Alternatively, use the project-local admin server:

- conport-admin.fork_instance(workspace_id="${WORKSPACE}")
- conport-admin.promote(progress_id="<uuid>")
- conport-admin.promote_all(workspace_id="${WORKSPACE}")

Sample prompt:
```
Fork active progress from shared into this instance to continue where I left off.

→ Call: conport-admin.fork_instance(workspace_id="${WORKSPACE}")
```

### Project Memory Queries

- conport.get_progress(workspace_id="${WORKSPACE}", status="IN_PROGRESS", limit=10)
- conport.get_decisions(workspace_id="${WORKSPACE}", limit=10)

Sample prompt:
```
List in-progress tasks for this project, then propose 2 next actions that require < 25 minutes.

→ Call: conport.get_progress(workspace_id="${WORKSPACE}", status="IN_PROGRESS", limit=10)
```

Notes:
- `${WORKSPACE}` resolves to the repository root; instance id defaults from branch/folder.
- ConPort auto-seeds context from shared and auto-forks PLANNED/IN_PROGRESS on first use.
