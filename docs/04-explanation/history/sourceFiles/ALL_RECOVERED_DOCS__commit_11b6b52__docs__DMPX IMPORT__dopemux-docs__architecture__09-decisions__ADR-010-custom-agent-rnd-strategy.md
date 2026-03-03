# ADR-010: Custom Agent R&D Strategy

## Status
**Accepted** - Hybrid approach: Claude-flow today, custom agents long-term

## Context

Dopemux requires a sophisticated multi-agent system for development orchestration. Current research reveals:

- **Claude-flow**: Achieves 84.8% SWE-Bench solve rate with 64 specialized agents
- **Awesome-Claude-Code**: Shows 5 distinct orchestration patterns with proven effectiveness
- **ChatX & CCPM**: Demonstrate advanced hook systems and 89% context switching reduction

The decision involves balancing immediate capability (using Claude-flow) with long-term strategic control (custom agent system) while maintaining ADHD accommodations and performance requirements.

## Decision

**Hybrid Development Strategy**:
1. **Phase 1**: Deploy Claude-flow as primary agent orchestrator (immediate capability)
2. **Phase 2**: Develop custom agent framework alongside Claude-flow (parallel development)
3. **Phase 3**: Gradual migration from Claude-flow to custom agents (selective replacement)
4. **Phase 4**: Full custom agent system with Claude-flow patterns integrated

## Custom Agent Architecture Design

### Core Architecture Pattern
```yaml
orchestration_pattern:
  primary: Hub-and-Spoke (proven in Claude-flow)
  fallback: Mesh (for complex multi-agent consensus)
  resilience: Automatic pattern switching based on task complexity

agent_framework:
  base: Custom AbstractAgent with LangGraph patterns
  communication: JSON-RPC over Redis pub/sub
  memory: Letta Framework + custom tiers
  spawning: Dynamic agent creation based on workload
```

### Agent Communication System
```python
class AgentCommunicationBus:
    """Central communication hub inspired by Claude-flow patterns"""

    async def request_consensus(self, topic: str, proposer: str, proposal: Any):
        """Byzantine consensus pattern from Claude-flow research"""
        votes = []
        consensus_msg = AgentMessage(
            type=MessageType.CONSENSUS_REQUEST,
            sender=proposer,
            recipient="broadcast",
            payload={"topic": topic, "proposal": proposal}
        )

        await self.publish(consensus_msg)
        return await self.tally_votes(votes)  # PBFT-style consensus
```

### Memory Architecture Integration
```yaml
multi_tier_memory:
  L1_cache: In-memory Redis (< 10ms access)
  L2_session: SQLite persistence (< 100ms)
  L3_project: Letta Framework (< 500ms)
  L4_global: Knowledge Graph DB (< 1s)

cross_agent_sharing:
  blackboard_pattern: Common memory space for all agents
  mcp_resources: Point-to-point memory sharing
  context_inheritance: Hierarchical context propagation
```

## Specialized Agent Types

### Core Agent Specializations
```yaml
agent_specializations:
  CodeAgent:
    purpose: Code generation and implementation
    mcp_servers: [serena, claude-context, morphllm]
    capabilities: [pattern_search, code_generation, validation]

  TestAgent:
    purpose: Test generation and execution
    mcp_servers: [playwright, context7]
    capabilities: [test_case_generation, coverage_analysis, execution]

  ReviewAgent:
    purpose: Code review and quality assurance
    mcp_servers: [serena, sequential-thinking]
    capabilities: [diff_analysis, security_review, performance_check]

  ResearchAgent:
    purpose: Research and documentation
    mcp_servers: [exa, context7, sequential-thinking]
    capabilities: [web_research, pattern_discovery, documentation]

  PlannerAgent:
    purpose: Task decomposition and orchestration
    mcp_servers: [zen-mcp, task-master-ai]
    capabilities: [task_breakdown, dependency_analysis, resource_allocation]
```

### Agent State Management
```python
class AbstractAgent(ABC):
    """Base class inspired by Claude-flow agent architecture"""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.state = "idle"
        self.memory = AgentMemory(agent_id)
        self.token_budget = config.get("token_budget", 5000)
        self.mcp_servers = []

    async def checkpoint(self):
        """Save agent state for recovery (ADHD requirement)"""
        checkpoint_data = {
            "agent_id": self.agent_id,
            "state": self.state,
            "tokens_used": self.tokens_used,
            "memory_snapshot": await self.memory.snapshot(),
            "timestamp": time.time()
        }
        await save_checkpoint(checkpoint_data)

    async def restore(self, checkpoint_data: Dict):
        """Restore from checkpoint"""
        self.state = checkpoint_data["state"]
        self.tokens_used = checkpoint_data["tokens_used"]
        await self.memory.restore(checkpoint_data["memory_snapshot"])
```

## ADHD-Optimized Agent Features

### Attention Management
```yaml
adhd_optimizations:
  context_preservation:
    automatic_checkpointing: Every task completion or 30 minutes
    seamless_restoration: Zero cognitive overhead on return
    decision_history: Track and restore mental models

  cognitive_load_reduction:
    automatic_task_chunking: Break large tasks into 25-minute focus blocks
    priority_highlighting: Visual emphasis on critical tasks
    distraction_filtering: Hide non-essential information

  executive_function_support:
    automated_planning: AI-powered task decomposition
    dependency_visualization: Clear relationship mapping
    energy_pattern_recognition: Optimal work time scheduling
```

### Agent Coordination for ADHD
```python
class ADHDAgentCoordinator:
    """Coordinates agents with ADHD accommodations"""

    async def manage_attention_flow(self, user_context: Dict):
        """Manage agent interactions to reduce cognitive switching"""
        if user_context["focus_state"] == "deep":
            # Minimize interruptions, batch notifications
            await self.enable_focus_mode()
        elif user_context["energy_level"] == "low":
            # Simplify tasks, provide more support
            await self.activate_assistance_mode()

    async def preserve_context_switches(self, from_task: str, to_task: str):
        """Seamless context preservation during task switches"""
        context_bridge = await self.create_context_bridge(from_task, to_task)
        await self.notify_relevant_agents(context_bridge)
```

## Integration with Existing Systems

### Claude-flow Integration (Phase 1)
```yaml
claude_flow_integration:
  deployment: Docker Compose with Dopemux services
  communication: JSON-RPC over HTTP/WebSocket
  memory_sharing: Shared Redis instance for context
  gradual_replacement: Individual agent replacement strategy

agent_mapping:
  claude_flow_to_custom:
    "code-generator": CustomCodeAgent
    "test-runner": CustomTestAgent
    "code-reviewer": CustomReviewAgent
    "research-assistant": CustomResearchAgent
```

### MCP Server Coordination
```yaml
mcp_integration_strategy:
  primary_servers:
    zen-mcp: Multi-model orchestration and consensus
    context7: Documentation and pattern lookup
    serena: Code operations and project memory

  agent_server_mapping:
    CodeAgent: [serena, context7, morphllm]
    TestAgent: [playwright, context7]
    ResearchAgent: [exa, context7, sequential-thinking]
    PlannerAgent: [zen-mcp, task-master-ai]
```

## Migration Strategy

### Phase 1: Claude-flow Foundation (Weeks 1-8)
```yaml
objectives:
  - Deploy Claude-flow for immediate multi-agent capability
  - Integrate with Dopemux hub-and-spoke architecture
  - Establish baseline performance metrics
  - Create MCP bridge for Claude-flow agents

deliverables:
  - Working Claude-flow integration
  - Performance baselines
  - MCP bridging layer
  - ADHD accommodation wrapper
```

### Phase 2: Custom Agent Development (Weeks 9-16)
```yaml
objectives:
  - Develop AbstractAgent base class and framework
  - Implement first custom agents (CodeAgent, TestAgent)
  - Create agent communication bus
  - Build memory management system

deliverables:
  - Custom agent framework
  - 2-3 working custom agents
  - Communication bus implementation
  - Memory tier integration
```

### Phase 3: Selective Migration (Weeks 17-24)
```yaml
objectives:
  - Replace Claude-flow agents one-by-one
  - Maintain performance parity or improvement
  - Validate ADHD accommodations
  - Performance optimization

deliverables:
  - 50% custom agent replacement
  - Performance validation
  - ADHD accommodation testing
  - Migration tooling
```

### Phase 4: Full Custom System (Weeks 25-32)
```yaml
objectives:
  - Complete migration to custom agents
  - Advanced coordination patterns
  - Performance optimization
  - Enterprise deployment readiness

deliverables:
  - 100% custom agent system
  - Advanced orchestration patterns
  - Production-ready deployment
  - Documentation and tutorials
```

## Performance and Scalability

### Agent Performance Targets
```yaml
performance_requirements:
  agent_spawn_time: < 500ms
  task_handoff_latency: < 100ms
  consensus_time: < 2s (for 5-10 agents)
  memory_access: < 50ms (ADHD critical)

scalability_targets:
  concurrent_agents: 64+ (matching Claude-flow)
  task_throughput: 1000+ tasks/hour
  memory_efficiency: < 100MB per agent
  horizontal_scaling: 10x capacity increase
```

### Resource Management
```yaml
resource_optimization:
  token_budgeting: Per-agent limits with overflow handling
  memory_pooling: Shared memory tiers across agents
  cpu_scheduling: Priority-based agent execution
  network_efficiency: Connection pooling for MCP servers
```

## Quality and Testing Strategy

### Agent Testing Framework
```yaml
testing_strategy:
  unit_tests: Individual agent behavior validation
  integration_tests: Multi-agent coordination patterns
  performance_tests: Latency and throughput benchmarks
  adhd_tests: Cognitive load and accommodation validation

validation_metrics:
  task_success_rate: > 95% (compared to Claude-flow baseline)
  performance_improvement: 20%+ over Claude-flow
  adhd_satisfaction: User-reported effectiveness
  system_reliability: 99.9% uptime
```

### Monitoring and Observability
```yaml
observability:
  metrics:
    - agent_health_status
    - task_completion_rates
    - consensus_success_rates
    - memory_usage_patterns

  alerting:
    - agent_failure_detection
    - performance_degradation
    - memory_leak_detection
    - consensus_timeout_warnings
```

## Strategic Benefits

### Immediate (Claude-flow Integration)
- **Proven Multi-Agent Capability**: 84.8% SWE-Bench solve rate
- **Rapid Deployment**: Existing Docker infrastructure
- **ADHD Enhancement**: Wrapper layer for accommodations
- **Learning Opportunity**: Understand multi-agent patterns

### Long-term (Custom Agent System)
- **Full Control**: Complete customization for ADHD needs
- **Performance Optimization**: Eliminate Claude-flow overhead
- **Strategic Independence**: No dependency on external systems
- **Continuous Improvement**: AI-powered agent enhancement

## Consequences

### Positive
- **Best of Both Worlds**: Immediate capability + long-term control
- **Risk Mitigation**: Gradual migration reduces deployment risk
- **Learning Integration**: Claude-flow patterns inform custom design
- **ADHD Optimization**: Purpose-built accommodations throughout
- **Scalable Architecture**: Designed for growth and adaptation

### Negative
- **Complexity**: Managing two agent systems during transition
- **Resource Overhead**: Additional development and infrastructure costs
- **Integration Challenges**: Bridging between Claude-flow and custom agents
- **Timeline Extension**: Longer development cycle for full capability

### Risks and Mitigations
- **Performance Regression**: Continuous benchmarking and rollback capability
- **Feature Gaps**: Systematic feature parity validation
- **Integration Failures**: Comprehensive testing and gradual rollout
- **Resource Constraints**: Cloud-native scaling and optimization

## Related Decisions
- **ADR-006**: MCP server selection enables agent tool integration
- **ADR-009**: Session persistence supports agent state management
- **ADR-008**: Task management integration coordinates with agent planning
- **Future ADR-011**: ADHD accommodations guide agent behavior design

## References
- Custom Agent R&D Strategy: `/research/findings/DOPEMUX_CUSTOM_AGENT_RND.md`
- Claude-flow Integration: `/research/integrations/claude-flow-dopemux-integration.md`
- Multi-Agent Research: `/research/findings/multi-agent-coding-systems.md`
- Agent Architecture: `/research/architecture/DOPEMUX_CUSTOM_AGENT_RND.md`