---
id: DOPECONBRIDGE_ZEN_INTEGRATION_PLAN
title: Dopeconbridge_Zen_Integration_Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopeconbridge_Zen_Integration_Plan (explanation) for dopemux documentation
  and developer workflows.
---
# DopeconBridge: Zen Integration Master Plan

**Status**: Planning Phase
**Date**: 2025-11-13
**Objective**: Complete comprehensive DopeconBridge integration across all touchpoints

---

## 🎯 Integration Scope Discovery

### Phase 1: Core Infrastructure ✅ (COMPLETED)
- [x] Shared client library (`services/shared/dopecon_bridge_client/`)
- [x] ADHD Engine integration
- [x] Task Orchestrator migration
- [x] Serena v2 migration
- [x] Voice Commands migration
- [x] Experimental services documentation

### Phase 2: CLI & Command Integration 🔄 (IN PROGRESS)

#### 2.1 Main CLI Entry Points
**Files to audit:**
- `src/dopemux/cli/main.py` - Main CLI commands
- `src/dopemux/cli/commands/` - All subcommands
- `scripts/*.sh` - Shell wrapper scripts
- `Makefile` - Build & deployment commands

**Integration Points:**
- [ ] `dopemux start` - Should initialize DopeconBridge connection
- [ ] `dopemux status` - Should query bridge for system status
- [ ] `dopemux context` - Should use bridge for context operations
- [ ] `dopemux workspace` - Should use bridge for workspace state
- [ ] `dopemux session` - Should use bridge for session management

#### 2.2 Hook System Integration
**Files to audit:**
- `src/dopemux/hooks/claude_code_hooks.py`
- `src/dopemux/hooks/hook_manager.py`
- `src/dopemux/hooks/shell_hook_installer.py`
- `hooks/*.sh` - Shell hooks

**Integration Points:**
- [ ] Pre-commit hooks - Log to bridge event bus
- [ ] Post-command hooks - Publish completion events
- [ ] Context switch hooks - Update bridge workspace state
- [ ] Session lifecycle hooks - Manage bridge connections

#### 2.3 Implicit Bridge Calls
**Hidden integration points:**
- [ ] Tmux session initialization - Bridge context setup
- [ ] Profile loading - Bridge workspace configuration
- [ ] Instance state restoration - Bridge state queries
- [ ] Background health checks - Bridge service monitoring

### Phase 3: Documentation Integration 🔄 (IN PROGRESS)

#### 3.1 Primary Documentation
**Files to update:**
- [ ] `README.md` - Add DopeconBridge overview
- [ ] `QUICK_START.md` - Update setup instructions
- [ ] `INSTALL.md` - Add bridge installation steps
- [ ] `docs/00-MASTER-INDEX.md` - Add bridge references

#### 3.2 Architecture Documentation
**Files to update:**
- [ ] `docs/04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md`
- [ ] `docs/04-explanation/architecture/ARCHITECTURE_3.0_COMPLETE.md`
- [ ] `docs/94-architecture/system-bible.md`
- [ ] `docs/94-architecture/unified-architecture-guide.md`

**Content updates:**
- [ ] Add DopeconBridge as central integration layer
- [ ] Update architecture diagrams
- [ ] Document two-plane model with bridge
- [ ] Show event flow through bridge

#### 3.3 Service-Specific Docs
**Files to update:**
- [ ] `docs/systems/conport/CONPORT_README.md`
- [ ] `docs/systems/adhd-intelligence/ADHD_STACK_README.md`
- [ ] `docs/services/adhd-engine-api.md`
- [ ] `services/task-orchestrator/README.md`
- [ ] `services/serena/v2/README.md`

#### 3.4 Integration Guides
**Files to update:**
- [ ] `docs/02-how-to/integrations/CLAUDE_CODE_INTEGRATION.md`
- [ ] `docs/02-how-to/integrations/LEANTIME_API_SETUP_GUIDE.md`
- [ ] `docs/04-explanation/COMPONENT_3_INTEGRATION_BRIDGE_WIRING.md`

#### 3.5 LLM Context Files
**Files to update (CRITICAL):**
- [ ] `claudedocs/phase-1b-service-catalog.md` - Update service dependencies
- [ ] `claudedocs/ORCHESTRATOR_IMPLEMENTATION_PLAN.md` - Add bridge calls
- [ ] `claudedocs/WEEK-7-INTEGRATION-BRIDGE-COMPLETION-PLAN.md` - Update status
- [ ] `docker/mcp-servers/zen/zen-mcp-server/CLAUDE.md` - Document bridge access
- [ ] `docker/mcp-servers/zen/zen-mcp-server/AGENTS.md` - Agent bridge usage

**Key updates needed:**
```markdown
## DopeconBridge Integration

All services MUST use DopeconBridge for cross-plane communication:

1. **Import the client:**
   ```python
   from services.shared.dopecon_bridge_client import DopeconBridgeClient
   ```

1. **Initialize:**
   ```python
   bridge = DopeconBridgeClient.from_env()
   ```

1. **Use bridge methods:**
- Events: `bridge.publish_event(...)`
- PM routing: `bridge.route_pm(...)`
- Cognitive routing: `bridge.route_cognitive(...)`
- Decisions: `bridge.recent_decisions(...)`
- Custom data: `bridge.save_custom_data(...)`

**Never:**
- Direct ConPort DB access
- Direct HTTP to ConPort
- Direct Redis for cross-plane data
```

### Phase 4: Configuration Integration 🔄 (IN PROGRESS)

#### 4.1 Global Environment Templates
**Files to update:**
- [ ] `.env.example` - Add bridge vars
- [ ] `.env.production-ready` - Add bridge config
- [ ] `.env.dopecon_bridge.example` - Comprehensive template

**Required variables:**
```bash
# DopeconBridge Configuration
DOPECONBRIDGE_URL=http://localhost:3016
DOPECONBRIDGE_TOKEN=<optional-auth-token>
DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane  # or pm_plane
DOPECONBRIDGE_TIMEOUT=10.0
DOPECONBRIDGE_RETRY_ATTEMPTS=3
DOPECONBRIDGE_RETRY_BACKOFF=2.0
```

#### 4.2 Docker Compose Files
**Files to update:**
- [ ] `docker-compose.master.yml`
- [ ] `docker-compose.prod.yml`
- [ ] `docker-compose.staging.yml`
- [ ] `docker-compose.unified.yml`
- [ ] `docker/mcp-servers/docker-compose.yml`

**Services needing bridge env vars:**
```yaml
services:
  adhd-engine:
    environment:
- DOPECONBRIDGE_URL=http://dopecon-bridge:3016
- DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane

  task-orchestrator:
    environment:
- DOPECONBRIDGE_URL=http://dopecon-bridge:3016
- DOPECONBRIDGE_SOURCE_PLANE=pm_plane

  serena-v2:
    environment:
- DOPECONBRIDGE_URL=http://dopecon-bridge:3016
- DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane

  voice-commands:
    environment:
- DOPECONBRIDGE_URL=http://dopecon-bridge:3016
- DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane

  genetic-agent:
    environment:
- DOPECONBRIDGE_URL=http://dopecon-bridge:3016
- DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane

  dope-context:
    environment:
- DOPECONBRIDGE_URL=http://dopecon-bridge:3016
- DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane
```

#### 4.3 Profile System
**Files to update:**
- [ ] `profiles/*.yaml` - Add bridge config to all profiles
- [ ] `config/*.yaml` - Update global config templates
- [ ] `docs/guides/PROFILE_USER_GUIDE.md` - Document bridge settings

**Profile additions:**
```yaml
dopecon_bridge:
  enabled: true
  url: http://localhost:3016
  source_plane: cognitive_plane
  auto_connect: true
  event_streams:
- dopemux:events
- dopemux:decisions
- dopemux:adhd
```

#### 4.4 MCP Server Configurations
**Files to update:**
- [ ] `mcp-proxy-config.yaml`
- [ ] `mcp-proxy-config.copilot.yaml`
- [ ] `docker/mcp-servers/conport-bridge/config.yaml`
- [ ] `docker/mcp-servers/zen/config.yaml`

### Phase 5: Workflow & Agent Integration 📋 (PLANNED)

#### 5.1 Zen MCP Agent Tools
**Files to audit:**
- `docker/mcp-servers/zen/zen-mcp-server/src/tools/*.py`

**Tools needing bridge access:**
- [ ] `planner.py` - Use bridge for decision storage
- [ ] `thinkdeep.py` - Query bridge for context
- [ ] `consensus.py` - Cross-plane decision queries
- [ ] `analyze.py` - Use bridge for pattern analysis
- [ ] `docgen.py` - Query bridge for documentation context
- [ ] `refactor.py` - Log refactoring decisions to bridge

**Implementation pattern:**
```python
# In each tool file
from services.shared.dopecon_bridge_client import DopeconBridgeClient

class PlannerTool:
    def __init__(self):
        self.bridge = DopeconBridgeClient.from_env()

    async def plan(self, request):
        # Store planning decisions in bridge
        await self.bridge.publish_event(
            event_type="zen.planning.decision",
            data={"plan": plan_data},
            source="zen_planner"
        )
```

#### 5.2 Genetic Agent Integration
**Files to update:**
- [ ] `services/genetic_agent/genetic_agent/agent.py`
- [ ] `genetic_agent/genetic_agent/genetic_agent/core/evolution.py`

**Integration points:**
- [ ] Store genetic patterns in bridge KG
- [ ] Query historical evolution data via bridge
- [ ] Publish evolution events to bridge event bus

#### 5.3 Workflow Orchestration
**Files to update:**
- [ ] `services/orchestrator/core/workflow_engine.py`
- [ ] `services/orchestrator/adapters/pm_adapter.py`
- [ ] `services/orchestrator/adapters/cognitive_adapter.py`

**Use bridge for:**
- [ ] Task state transitions
- [ ] Cross-plane coordination
- [ ] Workflow event publishing

#### 5.4 DDDPG Integration
**Files to audit:**
- [ ] `services/dddpg/src/core/graph_manager.py`
- [ ] `services/dddpg/src/api/routes.py`

**Integration needs:**
- [ ] Store decision patterns in bridge KG
- [ ] Query via bridge instead of direct DB

### Phase 6: Testing Infrastructure 🧪 (PLANNED)

#### 6.1 Update Existing Tests
**Directories to audit:**
- `tests/` - Root test directory
- `services/*/tests/` - Service-specific tests
- `services/shared/tests/` - Shared library tests

**Test updates needed:**
- [ ] Mock DopeconBridge in unit tests
- [ ] Add integration tests for bridge client
- [ ] Update service tests to use bridge mocks
- [ ] Add end-to-end bridge tests

#### 6.2 New Test Categories
- [ ] `tests/integration/test_dopecon_bridge_e2e.py` - Full flow tests
- [ ] `tests/integration/test_cross_plane_routing.py` - PM ↔ Cognitive tests
- [ ] `tests/performance/test_bridge_throughput.py` - Load tests
- [ ] `tests/security/test_bridge_auth.py` - Security tests

### Phase 7: Operational Integration 🚀 (PLANNED)

#### 7.1 Monitoring & Observability
**Files to create/update:**
- [ ] `services/dopecon-bridge/prometheus_metrics.py` - Add metrics
- [ ] `docker/prometheus/config.yml` - Scrape bridge
- [ ] `services/dopecon-bridge/health_check.py` - Health endpoints
- [ ] `scripts/mcp_server_health_report.sh` - Include bridge checks

#### 7.2 Deployment Scripts
**Files to update:**
- [ ] `install.sh` - Install bridge client
- [ ] `launch_dope_full.sh` - Start bridge service
- [ ] `scripts/deploy_*.sh` - Deploy bridge configs
- [ ] `verify_dopecon_bridge.sh` - Verification script

#### 7.3 Troubleshooting
**Files to create:**
- [ ] `docs/02-how-to/troubleshooting/DOPECONBRIDGE_DEBUG.md`
- [ ] `scripts/debug_bridge_connection.sh`
- [ ] `scripts/bridge_health_check.sh`

### Phase 8: Migration Paths 🔄 (PLANNED)

#### 8.1 Legacy Service Migration Guide
**Create:** `docs/guides/DOPECONBRIDGE_MIGRATION_GUIDE.md`

**Contents:**
1. Identify direct ConPort usage
1. Map to bridge client methods
1. Update configuration
1. Test migration
1. Deploy updated service

#### 8.2 Rollback Procedures
**Create:** `docs/02-how-to/operations/DOPECONBRIDGE_ROLLBACK.md`

**Contents:**
- Feature flag toggle
- Environment variable fallback
- Service restart procedures
- Verification steps

---

## 📊 Implementation Tracking

### Immediate Next Steps (This Session)

1. **CLI Integration** (2 hours)
- Audit `src/dopemux/cli/` for bridge integration points
- Add bridge initialization to main CLI
- Update status/context commands to use bridge
- Test CLI commands with bridge

1. **Hook System Integration** (1 hour)
- Update `claude_code_hooks.py` to publish events
- Add bridge logging to `hook_manager.py`
- Test hook execution with bridge

1. **Documentation Sprint** (2 hours)
- Update top 10 most-read docs with bridge info
- Update LLM context files (claudedocs)
- Create migration guides
- Update architecture docs

1. **Configuration Sweep** (1 hour)
- Update all .env templates
- Update docker-compose files
- Update profile templates
- Verify no hardcoded ConPort URLs remain

### Follow-Up Sessions

**Session 2: Agent & Workflow Integration**
- Zen MCP tools
- Genetic agent
- Workflow engine
- DDDPG integration

**Session 3: Testing & Validation**
- Comprehensive test suite
- Load testing
- Security testing
- Documentation validation

**Session 4: Production Readiness**
- Monitoring setup
- Deployment automation
- Rollback procedures
- Performance optimization

---

## 🎯 Success Criteria

### Phase Completion Checklist

**Phase 2 (CLI & Hooks) Complete When:**
- [ ] All CLI commands use bridge for cross-plane ops
- [ ] Hooks publish events to bridge event bus
- [ ] No direct ConPort calls in CLI code
- [ ] CLI tests pass with bridge mocks

**Phase 3 (Documentation) Complete When:**
- [ ] All architecture docs mention DopeconBridge
- [ ] Service docs show bridge usage examples
- [ ] LLM context files updated
- [ ] Migration guides published

**Phase 4 (Configuration) Complete When:**
- [ ] All .env templates have bridge vars
- [ ] All docker-compose files configured
- [ ] All profiles include bridge config
- [ ] No hardcoded CONPORT_URL remains

**Phase 5 (Agents/Workflows) Complete When:**
- [ ] Zen tools use bridge
- [ ] Genetic agent integrated
- [ ] Workflow engine uses bridge
- [ ] All agents can query KG via bridge

**Overall Success:**
- [ ] Zero direct ConPort DB access in services
- [ ] Zero direct ConPort HTTP in services (except bridge itself)
- [ ] All cross-plane ops go through bridge
- [ ] Full test coverage
- [ ] Production deployment successful

---

## 🚨 Risk Mitigation

### Identified Risks

1. **Breaking existing functionality**
- Mitigation: Comprehensive testing at each phase
- Rollback: Feature flags for bridge usage

1. **Performance degradation**
- Mitigation: Load testing before production
- Optimization: Connection pooling, caching

1. **Documentation drift**
- Mitigation: Update docs alongside code
- Validation: Automated doc checks

1. **Configuration complexity**
- Mitigation: Sensible defaults
- Documentation: Clear examples

---

## 📝 Notes

### Naming Convention Updates
All instances of "Integration Bridge" renamed to "DopeconBridge":
- Code references ✅
- Configuration ✅
- Documentation (in progress)
- Comments (in progress)

### Critical Integration Points Discovered
1. **Implicit bridge calls** in session initialization
1. **Hook-based event publishing** needed for all context switches
1. **Profile loading** must initialize bridge connection
1. **Zen MCP tools** are heavy bridge users (discovered during audit)
1. **Genetic agent** needs KG integration via bridge

### Open Questions
- [ ] Should CLI have a `--no-bridge` flag for debugging?
- [ ] How to handle bridge unavailability gracefully?
- [ ] Should we cache bridge responses in CLI?
- [ ] Authentication strategy for multi-user setups?

---

**Next Action**: Begin Phase 2.1 - CLI Integration Audit
