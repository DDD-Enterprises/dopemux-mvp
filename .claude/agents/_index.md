# Agent Configuration System

**Purpose**: Curated set of 4 specialized agents used by `/dx:` and `/sc:` flows
**Design**: ADHD-optimized task specialization with clear authority boundaries
**Fleet truth**: MCP fleet per `mcp_catalog.yaml` (ADR-MCPINT-001); model lanes per `config/ai/model-routing.policy.yaml` (advisory)

> **agents/** is the curated active set. The full persona library (42 active files across `*.agent.md` and `*-dopemux.md`, plus `archive/`) lives in `../personas/` — see `personas/PERSONA_INDEX.md` for the domain-grouped decision tree.

## Agent Ecosystem

| Agent | Mode | Tools | Specialization |
|---|---|---|---|
| `developer.md` | ACT | read, edit, write, grep, glob, bash | Code implementation, debugging, testing, task-packet execution |
| `architect.md` | PLAN | read, grep, glob, web | System design, trade-off analysis, ADRs (read-only) |
| `researcher.md` | Both | read, grep, glob, web | Investigation, technology evaluation, synthesis (read-only) |
| `project-manager.md` | PLAN | read, grep, glob | Status, task-packet flow, coordination (read-only) |

## Selection Matrix

### By Work Type
```
Code implementation    → developer
System architecture    → architect
Information research   → researcher
Status / coordination  → project-manager
Bug investigation      → developer + researcher
Technology evaluation  → researcher + architect
```

### By Mode Context
```
PLAN: architect, project-manager (support: researcher)
ACT:  developer (support: researcher)
```

## Coordination Patterns

```
architect (design) → project-manager (sequencing) → developer (implementation)
researcher (evidence) → architect (decision) → developer (execution)
developer (blockers) → project-manager (coordination) → resolution path
```

Cross-surface truth: Leantime (PM metadata), task-orchestrator (workflow transitions), ConPort (decisions/progress/context), dope-memory (chronicle), dope-context (read-only retrieval). Agents are helpers — never canonical owners of any plane (AGENTS.md §6).

## ADHD-Optimized Behaviors

- Essential output first, details on request (progressive disclosure)
- Maximum 3 options in any decision
- Single clear next action when attention is scattered
- State summarized before handoffs (under 10 lines)

## Model Guidance

Model selection follows `config/ai/model-routing.policy.yaml` stage lanes (advisory governance): cheap lanes for reads/status, standard for implementation, strong for design/audit. Agents never invent model ids; unverifiable ids are removed, not guessed.
