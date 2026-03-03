# RFC-0043: MetaMCP Orchestration System for ADHD-Optimized Token Management

---
id: rfc-0043
title: MetaMCP Orchestration System for ADHD-Optimized Token Management
type: rfc
status: draft
author: @dopemux-core
created: 2025-01-09
last_review: 2025-01-09
sunset: 2026-01-09
feature_id: metamcp-orchestration
tags:
  - adhd-accommodation
  - mcp-integration
  - token-optimization
  - session-management
links:
  related_adrs: [ADR-007]
  related_rfc: [RFC-0042]
  research_links: []
reviewers:
  - @architecture-team
  - @adhd-experience-team
adhd_metadata:
  cognitive_load: medium
  attention_state: focused
  time_to_read: "20 minutes"
---

## Problem

**One-sentence problem statement:** Dopemux relies on many MCP servers that, when all mounted simultaneously, bloat prompts to 100k+ tokens, increase costs dramatically, and overwhelm users with cognitive complexity.

**Why it matters:**
- **Token Cost Impact**: Current approach consumes 20,000+ tokens just for tool definitions before any user interaction
- **ADHD User Impact**: Tool overwhelm creates decision paralysis and cognitive overload for neurodivergent developers
- **Performance Impact**: Large context windows cause model "context distraction" and slower response times
- **Productivity Impact**: Users struggle to find relevant tools among 100+ available options

**Current pain points:**
- Loading 20+ MCP servers consumes massive context before meaningful work begins
- Users face decision paralysis with 100+ tools visible simultaneously
- Multi-agent orchestration amplifies tool chatter and context pollution
- No role-based access control or task-scoped tool management
- Claude-flow orchestration becomes inefficient with tool sprawl
- ADHD developers lose focus switching between irrelevant tools

## Context

### Background

Dopemux integrates extensive MCP servers for comprehensive development support:
- **Core servers**: context7, exa, serena, conport, task-master-ai, zen, sequential-thinking, playwright, cli
- **Specialized servers**: claude-context, morphllm-fast-apply, leantime, github, desktop-commander
- **Current state**: All servers loaded simultaneously, consuming 100k+ tokens baseline

The sequential thinking analysis revealed this is a **well-architected, technically feasible system** with strong ADHD accommodations but significant production readiness gaps around token management and role-based access.

### Constraints

- **Technical constraints**: Must maintain Claude-flow as primary orchestrator, support stdio/HTTP MCP transports
- **Business constraints**: Target 95% token reduction (100k→5k) while maintaining full functionality
- **Regulatory constraints**: Least-privilege security model, audit logging for tool access
- **ADHD constraints**: Progressive disclosure, cognitive load reduction, context preservation across interruptions

### Dependencies

- **System dependencies**: Existing Docker MCP infrastructure, Letta memory integration, ConPort session management
- **Team dependencies**: Architecture team for design validation, ADHD experience team for accessibility review
- **Timeline dependencies**: Phase 1 behind feature flag, gradual rollout based on role validation

### Related Work

- **Research foundation**: Context bloat management research showing 95% reduction achievable
- **External frameworks**: metatool-ai/metamcp for production orchestration patterns
- **Internal systems**: Existing ADHD-optimized session management and role definitions

## Options Considered

| Option | Description | Pros | Cons | ADHD Impact | Complexity |
|--------|-------------|------|------|-------------|------------|
| **Option A: Always-on superset** | Load all MCP servers simultaneously | <ul><li>Simple implementation</li><li>All tools always available</li></ul> | <ul><li>100k+ token consumption</li><li>Cognitive overload</li><li>Performance degradation</li></ul> | Negative - overwhelming | Low |
| **Option B: Static per-profile config** | Fixed tool sets per role | <ul><li>Predictable token usage</li><li>Role-based organization</li></ul> | <ul><li>No dynamic adaptation</li><li>Limited flexibility</li></ul> | Neutral - some structure | Medium |
| **Option C: MetaMCP Role-aware Broker** | Dynamic tool mounting based on role+task | <ul><li>95% token reduction</li><li>ADHD-friendly progressive disclosure</li><li>Budget-aware controls</li></ul> | <ul><li>Implementation complexity</li><li>Broker dependency</li></ul> | Positive - optimal cognitive load | High |

### Option A: Always-on Superset (Status Quo)
Current implementation loads all available MCP servers simultaneously. While simple, this creates:
- Massive token consumption (100k+ baseline)
- Decision paralysis for ADHD users
- Performance degradation from large context windows
- High cognitive load and tool overwhelm

### Option B: Static Per-Profile Configuration
Pre-defined tool sets for Developer, Researcher, Planner, Reviewer, and Ops roles. Provides:
- Predictable token usage and mental models
- Role-based organization reducing cognitive load
- Simple implementation and maintenance

However, lacks dynamic adaptation to changing task needs and context switching requirements.

### Option C: MetaMCP Role-aware Tool Broker (Recommended)
Intelligent orchestration system that:
- Dynamically mounts minimal toolsets based on current role and task type
- Enforces budget-aware pre-tool hooks to trim queries and results
- Supports session-level hot-swap of MCP servers
- Integrates with Letta for memory offload to keep prompts small
- Provides progressive disclosure UI for ADHD accommodation

## Proposed Direction

**Recommended Option:** Option C - MetaMCP Role-aware Tool Broker

**Rationale:**
- **Primary reason**: Achieves 95% token reduction (100k→5k) while maintaining full functionality
- **ADHD optimization**: Progressive disclosure and role-based toolsets reduce cognitive overload
- **Performance benefits**: Dynamic loading eliminates context pollution and improves response times
- **Cost efficiency**: Budget-aware hooks prevent runaway token consumption
- **Scalability**: Supports future role expansion and tool ecosystem growth

**Implementation Approach:**

1. **MetaMCP Tool Broker Core**
   - Policy Engine mapping (role, task_type, repo_signals) → allowed_tools[]
   - Mount Controller for lazy tool loading with stdio/HTTP transport support
   - Hot-swap capability for temporary role escalation during tasks

2. **Budget-aware PreTool Hooks**
   - Trim scope before tool calls (e.g., limit=3 for semantic searches)
   - Project token costs and warn/deny when approaching session budget
   - Auto-suggest smaller queries (observed 15-25% token savings)

3. **ADHD-Optimized Integration**
   - Memory offload via Letta (core/recall/archival tiers)
   - Progressive disclosure UI showing only 5-7 signals in status bar
   - Context preservation across role transitions

4. **Claude-flow Integration**
   - Maintain Claude-flow as primary orchestrator
   - MetaMCP constrains each agent's tools per role to prevent tool sprawl
   - Seamless agent spawning with appropriate tool constraints

## Role System Design

### Core Role Definitions

| Role | Default Tools | "Complex Reasoning" Add-ons | "UI/E2E" Add-ons | Token Budget |
|------|--------------|---------------------------|------------------|--------------|
| **Developer** | serena, claude-context, cli | sequential-thinking, zen | playwright | 10,000 |
| **Researcher** | context7, exa | sequential-thinking | — | 15,000 |
| **Planner** | task-master-ai, conport | zen | — | 8,000 |
| **Reviewer** | claude-context, conport | sequential-thinking | — | 12,000 |
| **Ops** | cli, conport | — | playwright | 8,000 |
| **Architect** | zen, sequential-thinking | consensus, challenge | — | 15,000 |
| **Debugger** | zen, claude-context | sequential-thinking | — | 15,000 |

### Dynamic Escalation Examples

- **Developer** implementing feature → test failures → temporarily mount `sequential-thinking`
- **Researcher** gathering info → architecture decision needed → temporarily mount `zen`
- **Reviewer** code review → UI testing required → temporarily mount `playwright`

## Open Questions

**Critical Questions (need resolution before decision):**
- [ ] What are optimal default token budgets per role based on usage patterns?
- [ ] How should emergency "break glass" tool access work for edge cases?
- [ ] What specific pre-tool hook policies provide best token savings vs. functionality?
- [ ] How will role transitions preserve context for ADHD users?

**Nice-to-Know Questions (can be resolved during implementation):**
- [ ] Should we support custom role definitions for advanced users?
- [ ] What observability metrics best indicate successful token optimization?
- [ ] How can we auto-suggest role escalations based on task patterns?

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| **Broker SPOF** | Medium | High | Health probes, retry logic, fallback to static profiles |
| **Policy mis-scoping** | Medium | Medium | "Break glass" ad-hoc tool mounting, user feedback loops |
| **ADHD context loss** | Low | High | Comprehensive state preservation, multiple backup mechanisms |
| **Claude-flow integration** | Medium | Medium | Robust Node bridge, extensive integration testing |
| **Token budget drift** | High | Medium | Continuous monitoring, auto-adjustment algorithms |

### ADHD-Specific Risks
- **Cognitive Overload**: Role transitions might confuse users → Clear visual indicators and context bridging
- **Context Switching**: Tool mounting delays might break flow → Pre-warming and predictive loading
- **Implementation Complexity**: System might become too complex → Progressive disclosure and safe defaults

## Timeline & Phases

### Phase 1: Foundation & Observation (3 weeks)
- [ ] Implement MetaMCP Tool Broker core
- [ ] Deploy in observe-only mode (suggest limits, log potential savings)
- [ ] Create role policy configurations
- [ ] **Milestone:** Broker observing and reporting token savings opportunities

### Phase 2: Controlled Enforcement (2 weeks)
- [ ] Enable enforcement for Researcher and Reviewer roles (lowest risk)
- [ ] Implement budget-aware pre-tool hooks
- [ ] Add Letta memory integration
- [ ] **Milestone:** Two roles running with proven token reduction

### Phase 3: Full Deployment (3 weeks)
- [ ] Roll out to Developer, Planner, and Ops roles
- [ ] Implement progressive disclosure UI
- [ ] Add hot-swap and escalation capabilities
- [ ] **Milestone:** All roles operational with optimization

### Phase 4: Optimization & Monitoring (2 weeks)
- [ ] Performance tuning and observability
- [ ] Advanced policy refinement
- [ ] User feedback integration
- [ ] **Milestone:** Production-ready with success metrics achieved

## Success Metrics

**Technical Metrics:**
- 95% token reduction: 100k → 5k average session consumption
- <200ms role switching latency
- <500ms tool mounting latency
- 15-25% additional savings from pre-tool hooks

**User Experience Metrics:**
- No regression in task completion rates under Claude-flow orchestration
- Reduced cognitive load scores in ADHD user studies
- Faster time-to-relevant-tool discovery

**ADHD Accommodation Metrics:**
- Maintained context preservation success rate (>95%)
- Reduced decision paralysis incidents
- Improved sustained attention duration during development sessions

## Feedback & Review

### Required Reviewers
- [ ] @architecture-team (focus: system design and integration)
- [ ] @adhd-experience-team (focus: cognitive load and accessibility)
- [ ] @performance-team (focus: token optimization and latency)
- [ ] @security-team (focus: least-privilege and audit requirements)

### Review Questions
1. Does the role system adequately cover development workflow needs?
2. Are the token budgets and pre-tool hooks realistic and effective?
3. Will the broker architecture scale with additional MCP servers?
4. Are ADHD accommodations comprehensive and well-integrated?
5. Is the rollout plan safe and measurable?

### Feedback Process
- **Comment deadline:** 2025-01-16
- **Review meeting:** 2025-01-17 2:00 PM PST
- **Decision target:** 2025-01-20

---

## Appendices

### Appendix A: Research Foundation

Based on comprehensive analysis of existing documentation:
- **Implementation Specification**: Detailed session orchestrator integration patterns
- **Context Bloat Management**: Production frameworks achieving 95% reduction
- **ADHD-Optimized Architecture**: Role definitions and workflow patterns
- **MCP Orchestration Research**: Complete implementation planning

### Appendix B: Configuration Examples

```yaml
# .dopemux/mcp/policy.yaml
profiles:
  developer:
    default: [serena, claude-context, cli]
    on:
      test_failure: [sequential-thinking]
      complex_arch: [zen, sequential-thinking]
  researcher:
    default: [context7, exa]
    on:
      deep_analysis: [sequential-thinking]
  planner:
    default: [task-master-ai, conport]
    on:
      architecture: [zen]

rules:
  budgets:
    default_tokens: 60_000
    hard_cap: 120_000
  trims:
    claude-context.max_results: 3
    task-master-ai.list_tasks.limit: 50
    exa.min_query_len: 12
```

### Appendix C: Integration Architecture

The MetaMCP system integrates with existing Dopemux infrastructure:
- **Docker layer**: Extends existing `/docker/mcp-servers/` infrastructure
- **Python layer**: New `/src/dopemux/orchestration/` module
- **Configuration**: Enhances `/src/dopemux/config/` with role management
- **CLI**: Extends `/src/dopemux/cli.py` with role commands

---

*RFC-0043 v1.0 - MetaMCP orchestration for token-optimized, ADHD-friendly development*