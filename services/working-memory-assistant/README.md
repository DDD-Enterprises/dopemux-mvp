# Working Memory Assistant (WMA) Service

**Version**: 2.0.0
**Purpose**: 20-30x faster interrupt recovery for ADHD developers through intelligent context preservation
**Port**: 8096 (configurable via WMA_PORT environment variable)

## Overview

The Working Memory Assistant provides revolutionary interrupt recovery for ADHD developers by automatically capturing and restoring work context. Traditional recovery takes 10-15 minutes; WMA reduces this to under 2 seconds through:

- **Automatic Context Snapshots**: Captures mental model, active focus, and current tasks
- **Progressive Disclosure Recovery**: Essential info first, details on demand
- **ADHD-Aware Prioritization**: Emotional weight and complexity scoring
- **Intelligent Caching**: Redis hot cache + PostgreSQL persistence

## Quick Start

### 1. Install Dependencies
```bash
cd services/working-memory-assistant
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5455
export POSTGRES_DB=dopemux_knowledge_graph
export POSTGRES_USER=dopemux_age
export POSTGRES_PASSWORD=dopemux_age_dev_password
export REDIS_HOST=localhost
export REDIS_PORT=6379
export WMA_PORT=8096
```

### 3. Run the Service
```bash
python main.py
# Or with uvicorn directly:
# uvicorn main:app --host 0.0.0.0 --port 8096 --reload
```

### 4. Test the Service
```bash
python test_wma_service.py
```

## API Endpoints

### Context Management

#### `POST /snapshot`
Create a new context snapshot
```json
{
  "user_id": "developer_123",
  "context_type": "work",
  "mental_model": {
    "project": "My App",
    "goal": "Implement user authentication"
  },
  "active_focus": {
    "file": "auth.py",
    "cursor": {"line": 45, "column": 10}
  },
  "current_task": {
    "description": "Debugging login issue",
    "progress": 0.6
  }
}
```

#### `POST /recover`
Recover context with progressive disclosure
```json
{
  "user_id": "developer_123",
  "snapshot_id": "optional_specific_snapshot",
  "recovery_stage": "essential"  // essential | detailed | complete
}
```

#### `GET /contexts/{user_id}`
Get user's recent contexts (prioritized)
```json
{
  "contexts": [
    {
      "id": "snapshot_123",
      "context_type": "work",
      "priority": 0.8,
      "last_accessed": "2025-11-09T10:30:00Z"
    }
  ]
}
```

### Preferences Management

#### `GET /preferences/{user_id}`
Get user preferences
```json
{
  "user_id": "developer_123",
  "auto_snapshot_enabled": true,
  "privacy_level": "balanced",
  "retention_days": 30,
  "max_memory_mb": 50,
  "notification_style": "gentle"
}
```

#### `POST /preferences`
Update user preferences
```json
{
  "user_id": "developer_123",
  "privacy_level": "comprehensive",
  "retention_days": 60
}
```

### Monitoring & Stats

#### `GET /health`
Service health check
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "timestamp": "2025-11-09T10:30:00Z"
}
```

#### `GET /stats/{user_id}`
User statistics
```json
{
  "total_contexts": 25,
  "active_contexts": 18,
  "avg_recovery_time": 450,
  "success_rate": 0.95,
  "total_recoveries": 42
}
```

### ADHD-Aware Endpoints

#### `POST /adhd-snapshot`
Create ADHD-aware snapshot with real-time state correlation
```json
{
  "user_id": "developer_123",
  "context_type": "work",
  "mental_model": {"project": "My App"},
  "active_focus": {"file": "auth.py", "cursor": {"line": 45, "column": 10}},
  "current_task": {"description": "Debugging login issue"}
}
// Returns: ADHD-enhanced snapshot with priority adjustment
```

#### `POST /adhd-recover`
Recover context adapted to current ADHD state
```json
{
  "user_id": "developer_123",
  "recovery_stage": "essential"
}
// Returns: Context adapted based on energy level, attention state, cognitive load
```

#### `GET /adhd-context/{user_id}`
Get current ADHD context for user
```json
{
  "timestamp": "2025-11-09T10:30:00Z",
  "is_available": true,
  "energy_level": {"level": 0.7, "timestamp": "..."},
  "attention_state": {"state": "focused", "timestamp": "..."},
  "cognitive_load": {"load": 0.4, "timestamp": "..."},
  "break_recommendation": {"recommended": false, "reason": "..."}
}
```

#### `POST /should-snapshot/{user_id}`
Determine if snapshot should be created based on ADHD state
```json
// Returns: {"should_snapshot": true/false}
// Based on energy changes, attention state, cognitive load
```

## Architecture

### Data Flow
```
Interrupt Occurs → Auto-snapshot (<200ms) → Redis Cache + PostgreSQL
       ↓
User Returns → Progressive Recovery (<2s) → Context Restored
       ↓
Gentle Re-orientation → Flow State Resumed
```

### Storage Strategy
- **Redis (Hot Cache)**: <200ms access, 24h TTL, frequently accessed contexts
- **PostgreSQL (Persistent)**: ACID compliance, complex queries, historical data
- **Filesystem (Archives)**: Cost-effective long-term storage

### Performance Targets
- **Snapshot Creation**: <200ms (achieves 20-30x improvement baseline)
- **Context Recovery**: <2s (achieves 20-30x improvement)
- **Memory Footprint**: <50MB sustained
- **Cache Hit Rate**: >90% for optimal performance

### Chronicle Store Write Semantics

`insert_work_log_entry` (in `chronicle/store.py`) validates enum fields before the INSERT and raises `ValueError` if any value is outside the allowed set. This mirrors the CHECK constraints in `schema.sql` and prevents the `INSERT OR IGNORE` clause from silently swallowing constraint violations while returning a phantom `entry_id`.

Fields validated at write time:

| Field | Allowed values (mirrors `schema.sql`) |
|---|---|
| `category` | `architecture`, `debugging`, `deployment`, `documentation`, `implementation`, `planning`, `research`, `review` |
| `entry_type` | `blocker`, `decision`, `error`, `manual_note`, `milestone`, `resolution`, `task_event`, `workflow_transition` |
| `workflow_phase` | `audit`, `deployment`, `implementation`, `maintenance`, `planning`, `review` (or `None`) |
| `outcome` | `abandoned`, `blocked`, `failed`, `in_progress`, `partial`, `success` |
| `importance_score` | integer 1–10 |

**Idempotent replay**: if the INSERT is silently ignored (`rowcount == 0`) and the computed `entry_id` already exists in the database, the existing `id` is returned without error. This is the only legitimate case for `OR IGNORE` — a retry of an identical provenance tuple.

**MCP tool effect**: the `memory_store` MCP tool returns `success=false` with the validation error message when any of the above checks fail. Callers should not treat a returned `entry_id` as evidence of a successful write without also checking `success`.

### Promotion-Time Validation for Manual Events

`manual.memory_store` events carry caller-controlled `category`, `entry_type`, `outcome`, and `workflow_phase`. The promotion handler (`promotion/promotion.py:_promote_manual_memory_store`) validates these fields before constructing a `PromotedEntry`:

- **`category`**: must be in `VALID_CATEGORIES` (same set as above).
- **`entry_type`**: restricted to the manual subset — `manual_note`, `decision`, `blocker`, `resolution`, `milestone`. Machine-generated types (`error`, `workflow_transition`, `task_event`) are not accepted via manual events.
- **`outcome`**: must be in `VALID_OUTCOMES`. Invalid values cause the handler to return `None`.
- **`workflow_phase`**: must be in `VALID_WORKFLOW_PHASES` if provided. `None` is accepted.

When the handler returns `None`, the eventbus consumer treats the event as not-promotable and acks it, leaving only a raw event record. This prevents a poison-message loop: if validation were deferred to the store layer, the store's `ValueError` would propagate to the consumer, which never acks on exception, causing indefinite retries.

Regression tests: `tests/test_store_fail_closed.py` (12 tests, including schema-parity assertions that parse `schema.sql` CHECK constraints and compare them to the module-level frozensets) and `tests/test_promotion_allowlist.py::TestManualMemoryStoreFieldValidation` (4 tests).

## Integration Points

### ADHD Engine Integration
- **Real-time Energy Monitoring**: Adapts recovery based on current energy levels
- **Attention State Correlation**: Adjusts disclosure based on focus state
- **Cognitive Load Assessment**: Prevents overwhelming with complexity scoring
- **ADHD-Aware Snapshots**: Automatic priority adjustment based on energy and attention
- **Adaptive Recovery**: Recovery stage adjusted to current ADHD state (essential/detailed/complete)
- **State Correlation**: Energy, attention, and load data embedded in snapshots

### ConPort Knowledge Graph
- **Decision Context**: Links working memory to project decisions
- **Progress Tracking**: Associates contexts with task progress
- **System Patterns**: Learns from successful recovery patterns

### Serena LSP Integration
- **Code Navigation Context**: Preserves cursor position and file state
- **Symbol Relationships**: Maintains code understanding context
- **Development Flow**: Seamless resumption of coding activities

## Configuration

### Environment Variables
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5455
POSTGRES_DB=dopemux_knowledge_graph
POSTGRES_USER=dopemux_age
POSTGRES_PASSWORD=dopemux_age_dev_password

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# Service
WMA_PORT=8096
```

### Docker Deployment
```yaml
# Add to docker-compose.master.yml
wma-service:
  build: ./services/working-memory-assistant
  environment:
    - POSTGRES_HOST=dopemux-postgres-age
    - REDIS_HOST=dopemux-redis-primary
    - WMA_PORT=8096
  ports:
    - "8096:8096"
  depends_on:
    - dopemux-postgres-age
    - dopemux-redis-primary
```

## Testing

### Automated Tests
```bash
# Run full test suite
python test_wma_service.py

# Test specific functionality
pytest tests/ -v -k "wma"
```

### Performance Benchmarks
```bash
# Run performance tests
python -m pytest tests/performance/ -v --benchmark-only
```

### Integration Tests
```bash
# Test with ADHD Engine
python test_integration_adhd_engine.py

# Test with ConPort
python test_integration_conport.py
```

## Monitoring & Observability

### Health Checks
- **Database Connectivity**: PostgreSQL connection validation
- **Cache Performance**: Redis ping and memory usage
- **API Responsiveness**: Endpoint response time monitoring

### Metrics Collection
- **Recovery Success Rate**: Percentage of successful recoveries
- **Performance Targets**: Continuous monitoring against <200ms/<2s targets
- **User Satisfaction**: Feedback rating tracking
- **Cache Efficiency**: Hit rate and memory usage analytics

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Performance Tracing**: Request timing and bottleneck identification
- **Error Tracking**: Comprehensive error context and recovery

## Security Considerations

### Data Protection
- **Encryption**: Sensitive context data encrypted at rest
- **Access Control**: User-scoped data isolation
- **Audit Trail**: Comprehensive logging of all operations

### Privacy Controls
- **Context Classification**: public/work/personal/sensitive levels
- **Retention Policies**: Configurable data expiration
- **User Consent**: Privacy preference management

## Deployment Checklist

- [ ] Database migration completed
- [ ] Redis cache configured
- [ ] Environment variables set
- [ ] Service dependencies verified
- [ ] Health checks passing
- [ ] Performance tests completed
- [ ] Integration tests passed
- [ ] Monitoring configured
- [ ] Documentation updated

## Troubleshooting

### Common Issues
1. **Database Connection Failed**: Check PostgreSQL credentials and network
2. **Redis Connection Failed**: Verify Redis service is running and accessible
3. **Performance Degradation**: Check Redis memory usage and PostgreSQL query plans
4. **Memory Usage High**: Review context retention policies and cleanup jobs

### Debug Mode
```bash
# Enable debug logging
export WMA_DEBUG=1
python main.py

# Check service logs
docker logs wma-service
```

## dope-memory MCP Endpoint

The `dope-memory` compose service (entrypoint `dope_memory_main.py`, container port `3020`) now serves a real MCP **streamable-HTTP** endpoint at `/mcp` (shipped in PR #857). This is distinct from the WMA snapshot/recovery REST surface described above.

### Transport

- Protocol: MCP streamable HTTP
- Endpoint: `http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp`
- `.mcp.json` type: `"http"`

### Tools (10)

All 10 MCP tools and the REST `/tools/*` endpoints share the same `DopeMemoryMCPServer` backend instance and the same canonical `chronicle.sqlite` ledger:

| Tool | Purpose |
|---|---|
| `memory_search` | Search chronicle entries |
| `memory_store` | Append a work-log entry |
| `memory_recap` | Summarize recent chronicle activity |
| `memory_mark_issue` | Flag a chronicle entry as an issue |
| `memory_link_resolution` | Link a resolution to a flagged issue |
| `memory_replay_session` | Replay a chronicle session |
| `memory_correct` | Supersede or correct a chronicle entry |
| `memory_generate_reflection` | Generate a reflection card from chronicle data |
| `memory_reflections` | Retrieve stored reflections |
| `memory_trajectory` | Derive trajectory state from chronicle |

### Package naming caveat

The service-local Python package was renamed from `mcp/` to `wma_mcp/` because naming it `mcp/` caused it to shadow the pip-installed `mcp` SDK that fastmcp depends on when the container copies it to `/app/mcp`. If you add service-local packages here, do not name them `mcp/`.

## Future Enhancements

- **Predictive Context**: AI-powered context prediction for proactive snapshots
- **Collaborative Context**: Team context sharing for handoffs
- **Mobile Integration**: Mobile app for context review during breaks
- **Advanced Analytics**: Recovery pattern analysis and optimization recommendations

---

**Status**: 🏗️ **Implementation Phase** - FastAPI service created with core endpoints, database integration, and Redis caching. Ready for testing and integration with ADHD Engine and ConPort.