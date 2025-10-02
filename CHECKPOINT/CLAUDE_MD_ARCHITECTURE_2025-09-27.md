

# CLAUDE.md Modular Architecture Checkpoint

**Date**: September 27, 2025
**Status**: Design Complete, Implementation Pending
**Version**: 2.0.0
**Lead**: Claude + User collaborative design

## Executive Summary

This checkpoint documents the complete redesign of the CLAUDE.md ecosystem from a monolithic structure (1,337 lines across 2 files) to a modular, token-efficient architecture that achieves **90% token reduction** through hierarchical loading and bounded contexts.

## Current State Analysis

### Problems Identified
- **Token Waste**: 20,000 tokens loaded per interaction regardless of context
- **Monolithic Growth**: Project file (1,117 lines) vs Global file (220 lines) = 5x size difference
- **Poor Separation**: ConPort commands, sprint templates, Python rules all mixed
- **No Lazy Loading**: Everything loads even for simple tasks
- **ADHD Challenges**: Overwhelming information density, no progressive disclosure

### Research Foundation
Based on extensive research of CLAUDE.md best practices from 2024-2025:
- **CLAUDE.md Supremacy Principle**: System-level rules override user prompts
- **Token Economy**: Every character consumes finite token budget
- **Hierarchical Memory**: Scope resolution from global → project → module → local
- **Modular Monolith Pattern**: Single deployment, modular architecture
- **"Nouns vs Verbs"**: Static knowledge (CLAUDE.md) vs executable actions (commands)

## Proposed Architecture

### 1. Hierarchical Structure

```
~/.claude/CLAUDE.md                    (50 lines) - Global ADHD principles
~/projects/CLAUDE.md                   (50 lines) - Organization standards
./CLAUDE.md                           (100 lines) - Project orchestrator
.claude/modules/                      (Focused components)
├── adhd.md                          (50 lines) - ADHD accommodations
├── conport.md                       (100 lines) - ConPort tool reference
├── serena.md                        (75 lines) - Serena code navigation & memory
├── mcp-servers.md                   (75 lines) - MCP configurations
├── python.md                        (50 lines) - Python conventions
├── sprint.md                        (150 lines) - mem4sprint templates
└── docker.md                        (50 lines) - Container workflows
.claude/commands/                     (Executable workflows)
├── _index.md                        (Command registry)
├── sprint-init.md                   (30 lines) - Sprint initialization
├── morning-standup.md               (30 lines) - Daily routine
├── test-gen.md                      (30 lines) - Test generation
└── security-review.md               (30 lines) - Security audit
src/CLAUDE.md                        (30 lines) - Python code context
docker/CLAUDE.md                     (30 lines) - Container context
docs/CLAUDE.md                       (30 lines) - Documentation context
```

### 2. Token Optimization Strategy

| Component | Current | Target | Reduction |
|-----------|---------|---------|-----------|
| Global Load | 1,337 lines (20K tokens) | 150 lines (2K tokens) | 90% |
| Command Load | All context | Specific context only | 95% |
| Module Load | Everything | On-demand only | 85% |

**Loading Patterns**:
- **Base**: Global + Project orchestrator (2K tokens)
- **Command**: Base + relevant modules (2.5K tokens)
- **Subdirectory**: Base + local context (2.2K tokens)

### 3. Multi-Model Integration

#### llm.md - Model Selection Logic
```yaml
task_routing:
  architecture: gemini-2.5-pro  # Deep reasoning + thinking mode
  debug: o3                     # Strong logical reasoning
  quick_query: gemini-2.5-flash # Ultra-fast responses
  documentation: claude-3.5-sonnet # Creative writing

adhd_adaptations:
  scattered_attention: gemini-2.5-flash  # Fast responses
  focused_attention: gemini-2.5-pro      # Comprehensive analysis
  hyperfocus: o3                         # Deep analysis
```

#### llms.md - Multi-Model Orchestration
```yaml
consensus_patterns:
  architectural_decisions:
    models: [gemini-2.5-pro, o3, claude-3.5-sonnet]
    process: independent_analysis → comparison → synthesis

validation_chains:
  code_review:
    flow: gemini-2.5-flash → o3-mini → gemini-2.5-pro
    escalation: complexity_based
```

#### Agent Configurations
```
.claude/agents/
├── architect.md      # System architecture specialist
├── debugger.md       # Root cause analysis expert
├── reviewer.md       # Code quality specialist
└── security.md       # Security audit specialist
```

## ADHD-Specific Features

### 1. Progressive Disclosure
- **Level 1**: Essential context only (project + task)
- **Level 2**: Relevant modules (lazy loaded)
- **Level 3**: Deep context (on request)
- **Level 4**: Expert analysis (special commands)

### 2. Attention-Aware Routing
```python
def select_model(attention_state, task_complexity):
    if attention_state == "scattered":
        return "gemini-2.5-flash"  # Fast, concise
    elif attention_state == "focused":
        return "gemini-2.5-pro"    # Comprehensive
    elif attention_state == "hyperfocus":
        return "o3"                # Deep analysis
```

### 3. Visual Progress Indicators
- Sprint burndown: `[████░░░░] 4/8 complete ✅`
- Task status: `🎯 Ready for work: 3 items`
- Blockers: `🚨 Blockers: 1 open`

### 4. Serena ADHD Memory Features
- **Context Switching Support**: Navigation breadcrumbs preserve mental model
- **Overwhelm Prevention**: Search results limited to 10 items maximum
- **Complexity Management**: Context depth limited to 3 levels by default
- **Gentle Guidance**: Supportive feedback language throughout interactions
- **Session Continuity**: State preserved across interruptions and context switches
- **Risk-Aware Suggestions**: Refactoring categorized by complexity and risk level

## Implementation Phases

### Phase 0: Pre-Implementation (Current State)
**Duration**: Until task management and memory systems are locked in
**Activities**:
- Continue using monolithic CLAUDE.md
- Document patterns and pain points in ConPort
- Track token usage metrics
- Identify most common command patterns

**Success Criteria**:
- [ ] Task management system fully operational
- [ ] Memory systems (ConPort, Serena) stable
- [ ] Clear understanding of usage patterns
- [ ] All subsystems properly integrated

### Phase 1: Foundation (Week 1)
**Day 1-2**: Structure Creation
```bash
mkdir -p .claude/{modules,commands,agents}
mkdir -p ~/.claude/modules
touch .claude/commands/_index.md
```

**Day 3-4**: Content Extraction
- Extract ADHD principles (220 lines → 50 lines)
- Extract ConPort reference (300 lines → 100 lines)
- Extract Serena memory behaviors (integration patterns → 75 lines)
- Extract sprint templates (400 lines → 150 lines)
- Extract Python conventions (100 lines → 50 lines)

**Day 5**: Command Migration
- Convert bash functions to slash commands
- Create command orchestrators
- Update command index

### Phase 2: Integration (Week 2)
**Day 1-2**: LLM Configuration
- Create llm.md with model selection logic
- Create llms.md with orchestration patterns
- Test model routing

**Day 3-4**: Agent Creation
- Create architect agent
- Create debugger agent
- Create reviewer agent
- Test agent switching

**Day 5**: Testing
- Measure token reduction
- Validate lazy loading
- Test command discovery

### Phase 3: Polish (Week 3-4)
**Polish Priorities**:
1. Token optimization (target <2K average)
2. ADHD enhancement (attention state detection)
3. Command refinement (usage pattern analysis)
4. Documentation polish (examples, troubleshooting)
5. Automation enhancement (pre-commit hooks, metrics)

## Governance Framework

### Pre-commit Validation
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: claude-md-lint
        name: CLAUDE.md structure validator
        entry: scripts/claude-md-lint.py
        language: python
        files: '\.claude/.*\.md$|CLAUDE\.md$'

      - id: token-counter
        name: Token usage analyzer
        entry: scripts/count-tokens.py
        language: python

      - id: import-validator
        name: Import statement checker
        entry: scripts/validate-imports.sh
        language: bash
```

### Quality Standards
- **Line Limits**: Global (50), Project (100), Modules (50-150), Commands (30)
- **Token Budgets**: Base load (<2K), Command load (<2.5K)
- **Import Validation**: No circular dependencies, valid paths
- **Content Rules**: No duplication, clear separation of concerns

## Success Metrics

### Quantitative Targets
| Metric | Current | Target | Measurement |
|--------|---------|---------|-------------|
| Avg Token Usage | 20,000 | 2,000 | Per interaction |
| Response Time | 3-5s | <1s | Time to first token |
| Command Discovery | Manual | <3s | Time to find command |
| Error Rate | Unknown | <5% | Failed commands/total |
| ADHD Task Completion | 60% | 85% | Tasks completed in session |

### Qualitative Indicators
- Reduced cognitive load reports
- Improved focus duration
- Better context retention
- Fewer context-related errors
- More consistent development patterns

## Risk Assessment

### High Risk
- **Breaking existing workflows**: Mitigation through backwards compatibility
- **Team adoption resistance**: Mitigation through gradual rollout

### Medium Risk
- **Import resolution issues**: Mitigation through thorough testing
- **Over-modularization**: Mitigation by keeping cohesive concepts together

### Low Risk
- **Performance degradation**: Unlikely given token reduction
- **Maintenance overhead**: Offset by better organization

## Integration Points

### Memory Systems
- **ConPort**: Foundational graph store for decision logging, progress tracking, and knowledge graph persistence across all systems
- **Serena**: ADHD-optimized LSP server with comprehensive code intelligence and memory behaviors:
  - Full LSP capabilities (code completion, diagnostics, go-to-definition)
  - Progressive disclosure (max 10 search results to prevent overwhelm)
  - Context limiting (3 levels max to reduce complexity)
  - Navigation breadcrumbs (track context switches)
  - Session persistence (maintains state across interruptions)
  - Intelligent refactoring categorized by complexity/risk
  - Event bus integration for attention coordination

### Task Management Systems (Project Management Plane)
- **Task-Master-AI**: PRD parsing and intelligent task decomposition with AI-powered analysis
- **Task-Orchestrator**: Advanced dependency analysis and task orchestration with 37 specialized tools
- **Leantime**: Master task owner and status authority for team coordination

### External Systems
- **Git**: Version control, branching strategies
- **Docker**: Container orchestration

## Future Roadmap

### Version 2.0 Features (After Polish)
- Semantic command discovery
- Adaptive loading based on usage patterns
- Predictive module loading
- Multi-project coordination

### Version 3.0 Vision (6 months)
- AI-generated modules from usage patterns
- Distributed team support
- Plugin ecosystem with community modules
- Self-optimizing token usage

## Dependencies & Prerequisites

### Must Be Complete Before Implementation
1. **Task Management Systems**: Complete Two-Plane Architecture stable and locked in
   - Task-Master-AI: PRD decomposition functionality complete
   - Task-Orchestrator: Dependency analysis with 37 tools operational
   - Leantime: Master task ownership and status authority established
2. **Memory Systems**: ConPort graph store and Serena LSP server operational
   - ConPort: Decision logging and knowledge graph functionality complete
   - Serena: Full LSP capabilities with ADHD accommodations working
3. **MCP Ecosystem**: All servers configured and stable
4. **Team Consensus**: Agreement on Two-Plane Architecture structure

### Supporting Infrastructure
- Pre-commit hooks infrastructure
- Metrics collection system
- Backup and recovery procedures
- Documentation generation tools

## Implementation Checklist

### Pre-Implementation
- [ ] Task management features nailed down
- [ ] Memory systems locked in
- [ ] All subsystems integrated
- [ ] Current patterns documented
- [ ] Team training completed

### Phase 1: Foundation
- [ ] Directory structure created
- [ ] Content extracted and modularized
- [ ] Commands converted from bash functions
- [ ] Initial testing completed

### Phase 2: Integration
- [ ] llm.md and llms.md created
- [ ] Agent configurations implemented
- [ ] Model routing tested
- [ ] Token reduction validated

### Phase 3: Polish
- [ ] Token optimization achieved (<2K average)
- [ ] ADHD features enhanced
- [ ] Documentation polished
- [ ] Automation implemented
- [ ] Success metrics achieved

## Conclusion

This architecture represents a paradigm shift from monolithic configuration to a sophisticated, modular cognitive architecture for AI-assisted development. The 90% token reduction, combined with ADHD-optimized progressive disclosure and multi-model orchestration, creates a foundation for highly efficient, neurodivergent-friendly development workflows.

The phased implementation ensures we can build incrementally while maintaining backwards compatibility, validating each component before proceeding to the next phase.

---

**Next Action**: Monitor current usage patterns and wait for task management and memory systems to stabilize before beginning Phase 1 implementation.