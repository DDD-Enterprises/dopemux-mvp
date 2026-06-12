# DMX-DCP-MODEL-ROUTING-MVP-0000 — AGENT_SURFACE_INVENTORY.md

## GitHub Agents

| Surface | Path | Runtime? | Authority | Tools | Model config | Invocation path | Evidence | Unknowns |
|---------|------|----------|-----------|-------|--------------|-----------------|----------|----------|
| dopemux-implementer | .github/agents/dopemux-implementer.agent.md | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | ls | Runtime authority UNKNOWN |
| dopemux-planner | .github/agents/dopemux-planner.agent.md | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | ls | Runtime authority UNKNOWN |
| dopemux-reviewer | .github/agents/dopemux-reviewer.agent.md | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | ls | Runtime authority UNKNOWN |
| dopemux-testgen | .github/agents/dopemux-testgen.agent.md | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | ls | Runtime authority UNKNOWN |

## Claude Agents/Personas

| Surface | Path | Runtime? | Authority | Tools | Model config | Invocation path | Evidence | Unknowns |
|---------|------|----------|-----------|-------|--------------|-----------------|----------|----------|
| 8 Claude agents | .claude/agents/ | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | ls (8 files) | Runtime authority UNKNOWN |
| 51 personas | .claude/personas/ | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | ls (51 files) | Runtime authority UNKNOWN |

## Agent Authority Finding

**AGENT RUNTIME AUTHORITY**: UNKNOWN across:
- services/agents/
- src/dopemux/agent_orchestrator.py
- services/task-orchestrator/task_orchestrator/agents/

No runtime path verified. Per AGENTS.md §6: "Agents do not own PM truth. Repo-wide agent runtime authority remains UNKNOWN."

**Total Agent Surfaces**: 63 (4 GitHub + 8 Claude + 51 personas)
**Runtime Verified**: 0
**Authority Verified**: 0
