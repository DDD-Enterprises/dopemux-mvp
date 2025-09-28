# MetaMCP Multi-Instance Integration Architecture
**Date**: September 27, 2025
**Status**: Design Complete - Ready for Implementation
**Decision**: Hierarchical Broker Architecture with Instance Coordination Layer
**Analysis**: Deep thinking validation with O3 reasoning complete

## Executive Summary

This document defines the integration architecture between MetaMCP's role-aware tool brokering system and Dopemux's multi-instance Claude Code management. The solution implements a **Hierarchical Broker Architecture** that preserves ADHD accommodations while enabling advanced multi-instance coordination.

**Key Innovation**: Instance Coordination Broker (port 8089) sits between multiple Claude Code instances and MetaMCP (port 8090), providing resource coordination, context handoff, and ADHD-optimized experience across instances.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         TMUX ORCHESTRATOR               │
│    dopemux-multi-instance-manager       │
│   Commands: /switch /handoff /status    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│       INSTANCE COORDINATION BROKER      │ ← NEW COMPONENT
│           localhost:8089                │
│  • Resource locking & workspace mgmt    │
│  • Context handoff protocols           │
│  • Instance-specific role assignment   │
│  • Cross-instance ADHD coordination    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│           METAMCP BROKER                │ ← EXISTING (OPERATIONAL)
│           localhost:8090                │
│  • Role-aware tool orchestration       │
│  • Token budget management             │
│  • Progressive disclosure               │
│  • 8/10 MCP servers operational        │
└─────────────┬───────────────────────────┘
              │
      ┌───────┼───────┐
      │       │       │
┌─────▼─┐ ┌───▼───┐ ┌─▼─────┐
│Dev-01 │ │Arch-02│ │Debug-3│
│UDS    │ │UDS    │ │UDS    │
│Role:  │ │Role:  │ │Role:  │
│dev    │ │arch   │ │debug  │
└───────┘ └───────┘ └───────┘
```

## Core Components

### 1. Instance Coordination Broker (NEW - Port 8089)

**Purpose**: Coordinates multiple Claude Code instances with MetaMCP while preserving ADHD accommodations.

**Key Responsibilities**:
- Resource locking and workspace isolation
- Context handoff between instances
- Instance-specific role assignment
- Cross-instance break reminder coordination
- Resource conflict prevention

**Implementation Structure**:
```python
class InstanceCoordinationBroker:
    """Coordinates multiple instances with MetaMCP integration"""

    def __init__(self):
        self.instances = {}  # instance_id -> InstanceState
        self.resource_locks = {}  # resource -> instance_id
        self.metamcp_client = MetaMCPClient("localhost:8090")
        self.socket_base = "/tmp/dopemux"

    async def allocate_instance(self, instance_id: str, role: str):
        """Allocate new instance with MetaMCP integration"""
        # 1. Register with Instance Broker
        # 2. Create workspace isolation
        # 3. Configure MetaMCP role mapping
        # 4. Setup resource locking
        pass

    async def handoff_context(self, from_instance: str, to_instance: str):
        """Seamless context transfer between instances"""
        # 1. Extract context from source instance
        # 2. Lock shared resources during handoff
        # 3. Transfer session state
        # 4. Update MetaMCP role assignment
        pass

    async def escalate_role(self, instance_id: str, target_role: str, duration: str):
        """Temporary role escalation for cross-role tool access"""
        pass
```

### 2. Enhanced MetaMCP Integration

**Current State**: MetaMCP operational on localhost:8090 with 8/10 MCP servers
**Enhancement**: Instance-aware role mapping with workspace isolation

**Integration Protocol**:
```json
{
  "instance_id": "dev-001",
  "role": "developer",
  "namespace": "instance_dev_001",
  "tool_overrides": {
    "conport.workspace_id": "/workspace/dev-001",
    "claude-context.cache_path": "/cache/claude-context/dev-001",
    "cli.working_directory": "/Users/hue/code/dopemux-instances/dev-001"
  },
  "token_budget": 10000,
  "escalation_rules": {
    "allowed_roles": ["architect", "debugger"],
    "temporary_access_duration": "1h",
    "approval_required": false
  }
}
```

**Role Mappings (from ADR-0034)**:
- **Developer**: serena, claude-context, cli (10,000 tokens)
- **Researcher**: context7, exa (15,000 tokens)
- **Planner**: task-master-ai, conport (8,000 tokens)
- **Architect**: zen, sequential-thinking (15,000 tokens)
- **Debugger**: zen, claude-context, sequential-thinking (15,000 tokens)
- **Reviewer**: claude-context, conport (12,000 tokens)
- **Ops**: cli, conport (8,000 tokens)

### 3. Resource Isolation Strategy

**Per-Instance Namespacing**:
```yaml
instance_isolation:
  conport_workspace: "/workspace/{instance_id}"
  claude_context_cache: "/cache/claude-context/{instance_id}"
  git_worktree: "/Users/hue/code/dopemux-instances/{instance_id}"
  temp_files: "/tmp/dopemux/{instance_id}"
  unix_socket: "/tmp/dopemux/instance-{instance_id}.sock"

shared_resources:
  git_repository: "mutex_lock_required"
  external_apis: "rate_limit_coordination"
  docker_containers: "shared_read_only"
  metamcp_broker: "coordinated_access"
```

**Workspace Isolation Implementation**:
```bash
# Per-instance directory structure
/Users/hue/code/dopemux-instances/
├── dev-001/           # Developer instance worktree
│   ├── .claude/
│   │   └── instance.json
│   └── workspace/     # ConPort workspace
├── arch-002/          # Architect instance worktree
│   ├── .claude/
│   │   └── instance.json
│   └── workspace/     # Isolated ConPort workspace
└── debug-003/         # Debugger instance worktree
    ├── .claude/
    │   └── instance.json
    └── workspace/     # Isolated ConPort workspace
```

## ADHD Accommodation Preservation

### Critical ADHD Features Maintained

1. **Progressive Disclosure Per Instance**
   - Each instance shows only role-appropriate tools
   - No tool overwhelm from seeing all 50+ available tools
   - Gradual reveal of additional capabilities through role escalation

2. **Context Handoff Protocol**
   - Preserves mental model during instance switching
   - Session state transfer includes active tasks, decisions, progress
   - Seamless continuation of work across instances

3. **Unified Break Management**
   - Coordinated break reminders across all instances
   - Prevents conflicting notifications
   - Respect for current focus state

4. **Instance-Aware Status Display**
   - tmux shows all instances with current focus indicator
   - Visual progress indicators per instance
   - Clear role identification

5. **Resource Conflict Prevention**
   - Automatic locking prevents lost work
   - Clear error messages when resources unavailable
   - Graceful degradation during conflicts

### Enhanced ADHD Features

**Cross-Instance Attention Management**:
```python
class ADHDCoordinator:
    """Enhanced ADHD features for multi-instance workflows"""

    def __init__(self):
        self.active_instance = None
        self.break_schedule = {}
        self.context_preservation = {}

    async def coordinate_focus_transition(self, from_instance: str, to_instance: str):
        """Smooth attention transition between instances"""
        # 1. Save current mental state
        # 2. Provide orientation summary for target instance
        # 3. Gradually reveal target instance tools
        # 4. Update unified status display
        pass

    async def manage_break_reminders(self):
        """Unified break management across instances"""
        # Respect focused instance for break timing
        # Coordinate notifications to prevent overwhelm
        pass
```

## Alternative Architectures Considered

### Option 1: Direct Instance-to-MetaMCP Connection
```
Instance-dev.sock → MetaMCP:8090 (role: developer)
Instance-arch.sock → MetaMCP:8090 (role: architect)
```

**Pros**: Simplest implementation
**Cons**: Resource conflicts, no coordination, difficult context handoffs
**Verdict**: ❌ Rejected due to conflict risks

### Option 2: MetaMCP-Per-Instance Model
```
Instance-dev.sock → MetaMCP-dev:8091
Instance-arch.sock → MetaMCP-arch:8092
```

**Pros**: Complete isolation
**Cons**: Resource duplication, no coordination, complex maintenance
**Verdict**: ❌ Rejected due to resource waste

### Option 3: Hierarchical Broker Architecture (SELECTED)
```
Instances → Instance Broker:8089 → MetaMCP:8090
```

**Pros**: Resource coordination, ADHD preservation, role flexibility
**Cons**: Additional complexity
**Verdict**: ✅ **SELECTED** - Optimal balance

## Implementation Roadmap

### Week 1: Instance Coordination Broker Core
**Tasks**:
- [ ] Create InstanceCoordinationBroker base class
- [ ] Implement resource locking mechanisms
- [ ] Add Unix socket allocation system
- [ ] Create MetaMCP client integration
- [ ] Basic instance registration and tracking

**Key Files**:
```
src/dopemux/mcp/
├── instance_coordinator.py     # NEW - Core coordination logic
├── resource_manager.py         # NEW - Resource locking
└── metamcp_integration.py      # NEW - MetaMCP client

config/
└── instance-broker.yaml       # NEW - Broker configuration
```

### Week 2: MetaMCP Integration Protocol
**Tasks**:
- [ ] Implement instance-aware role mapping
- [ ] Add workspace isolation configuration
- [ ] Create tool override mechanisms
- [ ] Build role escalation workflows
- [ ] Add token budget coordination

### Week 3: Resource Isolation and Context Handoff
**Tasks**:
- [ ] Implement per-instance workspace creation
- [ ] Build context preservation protocols
- [ ] Add seamless handoff mechanisms
- [ ] Create resource conflict resolution
- [ ] Implement cross-instance git coordination

### Week 4: ADHD Coordination and Testing
**Tasks**:
- [ ] Enhanced break reminder coordination
- [ ] Progressive disclosure per instance
- [ ] Visual status indicator integration
- [ ] Comprehensive multi-instance testing
- [ ] Performance optimization and monitoring

## Success Criteria & Validation

### Performance Benchmarks
```python
PERFORMANCE_TARGETS = {
    'instance_allocation_time': 2000,           # milliseconds
    'context_handoff_latency': 500,            # milliseconds
    'role_escalation_time': 200,               # milliseconds
    'resource_lock_acquisition': 100,          # milliseconds
    'metamcp_integration_overhead': 50,        # milliseconds
}
```

### ADHD Accommodation Metrics
```python
ADHD_TARGETS = {
    'context_preservation_success_rate': 0.95,    # 95% successful handoffs
    'tool_overwhelm_prevention': 1.0,             # Always role-appropriate tools
    'break_reminder_coordination': 0.90,          # 90% proper coordination
    'resource_conflict_prevention': 0.98,         # 98% conflict-free operation
    'attention_fragmentation_reduction': 0.70,    # 70% improvement
}
```

### Functional Validation
- [ ] Zero ConPort workspace conflicts during concurrent operation
- [ ] Seamless context handoff between all role combinations
- [ ] Role escalation working for temporary tool access
- [ ] All ADHD accommodations preserved across instances
- [ ] 95% token reduction maintained per instance (via MetaMCP)

## Risk Mitigation

### High-Impact Risks

**1. Instance Coordination Broker Failure**
- **Risk**: Single point of failure for all instances
- **Mitigation**: Fallback to direct MetaMCP connections
- **Monitoring**: Health checks every 30 seconds
- **Recovery**: Automatic restart with state restoration

**2. Resource Lock Deadlocks**
- **Risk**: Instances deadlock on shared resources
- **Mitigation**: Timeout-based lock acquisition (5 seconds)
- **Detection**: Deadlock detection algorithms
- **Recovery**: Automatic lock breaking with user notification

**3. Context Handoff Data Loss**
- **Risk**: Mental model lost during instance switching
- **Mitigation**: Comprehensive state serialization
- **Backup**: Multiple checkpoints during handoff
- **Validation**: Integrity checks on restored context

### Medium-Impact Risks

**4. MetaMCP Integration Complexity**
- **Risk**: Integration breaks existing MetaMCP functionality
- **Mitigation**: Backward compatibility layer
- **Testing**: Comprehensive integration test suite
- **Rollback**: Feature flags for gradual deployment

**5. ADHD Feature Regression**
- **Risk**: Multi-instance complexity reduces ADHD accommodations
- **Mitigation**: Dedicated ADHD testing protocols
- **Monitoring**: User experience metrics tracking
- **Response**: Immediate rollback triggers for accommodation failures

## Decision Log

### Decision #16: Multi-Instance Integration Architecture
**Summary**: Adopt Hierarchical Broker Architecture for MetaMCP multi-instance integration
**Rationale**: Provides optimal balance of resource coordination, ADHD preservation, and implementation complexity
**Implementation**: Instance Coordination Broker on port 8089 coordinating with MetaMCP on port 8090
**Status**: Approved for implementation
**ADHD Impact**: Positive - preserves all accommodations while enabling parallel workflows

### Decision #17: Resource Isolation Strategy
**Summary**: Per-instance workspace namespacing with shared resource coordination
**Rationale**: Prevents conflicts while enabling necessary resource sharing
**Implementation**: Instance-specific directories with mutex locks for shared resources
**Status**: Approved for implementation

### Decision #18: Role Escalation Model
**Summary**: Temporary role escalation with automatic timeout
**Rationale**: Provides flexibility without compromising role-based tool management
**Implementation**: Time-limited tool access with MetaMCP integration
**Status**: Approved for implementation

## Files Created/Updated

**New Architecture Files**:
- `CHECKPOINT/METAMCP_MULTI_INSTANCE_INTEGRATION_ARCHITECTURE_2025-09-27.md`
- `src/dopemux/mcp/instance_coordinator.py` (planned)
- `src/dopemux/mcp/resource_manager.py` (planned)
- `src/dopemux/mcp/metamcp_integration.py` (planned)
- `config/instance-broker.yaml` (planned)

**Updated Documentation**:
- `docs/94-architecture/09-decisions/adr-0034-metamcp-role-aware-tool-brokering.md` (reference)
- `CHECKPOINT/MULTI_INSTANCE_ARCHITECTURE_2025-09-27_O3_VALIDATED.md` (integration)

## Next Immediate Actions

### Today
1. **Document Review and Validation**
   - Review architecture with team
   - Validate ADHD accommodation preservation
   - Confirm MetaMCP integration approach

2. **Create Implementation Issues**
   - Break down Week 1 tasks into 4-hour blocks
   - Create GitHub issues with acceptance criteria
   - Set up project board for tracking

### Week 1 Sprint Planning
3. **Start Instance Coordination Broker**
   - Implement base coordinator class
   - Add basic MetaMCP client
   - Create resource locking foundation

4. **Update Existing Components**
   - Enhance MetaMCP broker configuration
   - Update docker-compose for new service
   - Modify tmux orchestrator for multi-instance

## Conclusion

This architecture successfully integrates MetaMCP's proven role-aware tool brokering with Dopemux's O3-validated multi-instance management system. The hierarchical broker design preserves all ADHD accommodations while enabling advanced coordination capabilities including:

- ✅ **Resource Coordination**: Prevents conflicts across instances
- ✅ **ADHD Preservation**: Maintains all neurodivergent accommodations
- ✅ **Role Flexibility**: Supports escalation and temporary tool access
- ✅ **Performance**: Leverages existing MetaMCP optimizations
- ✅ **Scalability**: Supports unlimited instance addition

The design is ready for immediate implementation with a realistic 4-week timeline and comprehensive success criteria.

---

**Status**: Architecture Complete - Ready for Implementation
**Confidence**: Very High (Deep thinking + O3 validation)
**Timeline**: 4 weeks for full implementation
**Priority**: High - Enables parallel development workflows with ADHD optimization

*Document created: September 27, 2025*
*Deep thinking analysis and validation complete*
*MetaMCP integration architecture finalized*