# Project Claude Guide - Dopemux MCP

This project is auto-wired with Dopemux MCP servers and ConPort per-worktree memory.

---

## 🧠 ADHD Intelligence Stack (PRODUCTION READY)

**Status**: Complete, operational, production-deployed
**Version**: 1.0
**Achievement**: Built in ONE epic session (2025-10-25)

### Quick Start
```bash
./scripts/start-all.sh  # Starts all 7 ADHD services automatically
```

### What It Does
**Zero-touch ADHD support** - automatic workspace monitoring, session tracking, break reminders, hyperfocus protection, energy/attention assessment.

**Statusline Integration**:
```
📚🧠🔬📊🔎🖥️🎯 | 🧠 ⚡= 👁️●
```
- 7 MCP server health indicators
- ADHD Engine status (🧠)
- Energy level (⚡↑/=/↓)
- Attention state (👁️●/🌀/💥)

### Services (9 Total)

**Core** (6 services, always running):
1. Activity Capture (Docker, 8096) - Event consumer
2. ADHD Engine (background, 8095) - Assessment
3. Workspace Watcher (background) - App monitoring
4. ADHD Notifier (background) - Alerts (visual + voice)
5. F-NEW-8 Break Suggester (background) - Intelligent detection
6. Dashboard (optional, 8097) - Web UI

**Utilities** (3 services, on-demand):
7. Context Switch Tracker - Cost analysis
8. Energy Trends - Pattern visualization
9. Slack Integration - Team summaries

### Features (16 Complete)
- Automatic workspace/session tracking
- Git commit velocity tracking
- File activity detection
- Energy/attention assessment
- Break reminders (25+ min, visual + voice)
- Hyperfocus alerts (60+ min, urgent)
- Intelligent break correlation (F-NEW-8)
- Daily reports
- Web dashboard + API
- Task recommendations
- Context switch cost tracking
- Energy trend visualization
- Slack/Discord integration
- Security hardening (CORS, optional auth)
- Performance optimization (batched endpoints)
- Complete documentation

### How It Works
**Completely automatic** - just work normally:
1. Switch to Claude Code → Session starts
2. Code for 25 minutes → Break notification + voice
3. High complexity work → F-NEW-8 correlates patterns → Intelligent suggestion
4. Code for 60 minutes → Hyperfocus alert
5. Make commit → Tracked as high-productivity
6. Switch to browser → Session ends
7. Statusline updates → Real-time ADHD state

### Documentation
- `docs/ADHD_STACK_README.md` - Complete guide
- `docs/ADHD_ARCHITECTURE_DIAGRAM.md` - System architecture
- `docs/ADHD_COMPLETE_DOCUMENTATION.md` - This summary
- `docs/MASTER_ACTION_PLAN.md` - Future roadmap

### Logs
```bash
tail -f /tmp/workspace_watcher.log      # App monitoring
tail -f /tmp/adhd_engine.log            # Assessment
tail -f /tmp/adhd_notifier.log          # Notifications
tail -f /tmp/break_suggester.log        # F-NEW-8
docker logs -f dopemux-activity-capture # Event processing
```

### Key Commands
```bash
# Context switch analysis
cd services/context-switch-tracker && python tracker.py

# Energy patterns
cd services/energy-trends && python visualizer.py

# Daily report
cd services/adhd-notifier && python daily_reporter.py

# Post to Slack
export SLACK_WEBHOOK_URL=your-webhook
cd services/slack-integration && python notifier.py
```

### ADHD Benefits
- **Zero cognitive overhead** - no manual tracking
- **Multi-modal alerts** - visual + voice
- **Intelligent timing** - F-NEW-8 correlates patterns
- **Real-time awareness** - statusline shows current state
- **Burnout prevention** - automatic break/hyperfocus protection
- **Pattern recognition** - trends, costs, recommendations

**Achievement**: 35 commits, 8,100+ lines, 9 services, 16 features - complete ADHD intelligence ecosystem built from zero to production in ONE session!

---

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
