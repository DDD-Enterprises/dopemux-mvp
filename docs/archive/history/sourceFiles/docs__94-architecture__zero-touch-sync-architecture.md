# Zero-Touch Sync Architecture

**Version:** 1.0
**Status:** Proposed
**Created:** 2025-09-25
**Authors:** Dopemux Platform Team

## System Overview

The Zero-Touch Sync system maintains data consistency across three specialized systems by orchestrating a lightweight synchronization service that respects each system's authority while providing unified access to work items.

### Core Systems

- **Leantime**: Team-facing project management (authoritative for status/roadmap)
- **Task-Master**: AI-driven task planning (authoritative for subtasks/next-actions)
- **ConPort**: Project memory system (authoritative for decisions/context)

### Sync Service

A single polling-based service that reads, normalizes, reconciles, and synchronizes data across all systems using MCP and JSON-RPC protocols.

## Component Architecture

```
┌─────────────────┐       ┌──────────────────┐
│   Leantime      │       │   Task-Master    │
│  (Status/UI)    │       │ (Tasks/Planning) │
│                 │       │                  │
│ • Tickets       │       │ • PRD→Tasks      │
│ • Milestones    │       │ • Hierarchy      │
│ • Team Status   │       │ • Next Actions   │
└────────┬────────┘       └────────┬─────────┘
         │                         │
         │ JSON-RPC/MCP            │ MCP/CLI
         │ (status read/write)     │ (tasks read/write)
         │                         │
         ▼                         ▼
    ┌─────────────────────────────────────┐
    │        Sync Service Core            │
    │                                     │
    │ • Polling Loop (300s)               │
    │ • Data Normalization                │
    │ • Conflict Resolution               │
    │ • Precedence Rules                  │
    │ • Retry/Backoff Logic               │
    │ • Health Monitoring                 │
    └─────────────┬───────────────────────┘
                  │
                  │ MCP (decisions read/write)
                  │
                  ▼
    ┌─────────────────────┐
    │     ConPort         │
    │ (Memory/Decisions)  │
    │                     │
    │ • Decision Log      │
    │ • Context Store     │
    │ • Pattern Memory    │
    └─────────────────────┘

             │
             ▼
    ┌─────────────────────┐
    │   Dopemux UX        │
    │                     │
    │ • Top-3 Today       │
    │ • Daily Digest      │
    │ • Unified View      │
    └─────────────────────┘
```

## Data Flow Architecture

### Sync Loop Sequence

```
┌─────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  Timer  │    │ Data Collect │    │ Normalize & │    │   Reconcile │
│ (300s)  │───▶│   & Poll     │───▶│   Dedupe    │───▶│  & Resolve  │
└─────────┘    └──────────────┘    └─────────────┘    └─────────────┘
                       │                                      │
                       ▼                                      ▼
               ┌──────────────┐                      ┌─────────────┐
               │ • LT tickets │                      │ • Status ←LT│
               │ • TM tasks   │                      │ • Tasks ←TM │
               │ • CP decisions│                     │ • Context←CP│
               └──────────────┘                      └─────────────┘
                                                            │
                                                            ▼
                                              ┌─────────────────────┐
                                              │    Write Back       │
                                              │                     │
                                              │ • Update LT status  │
                                              │ • Link TM→LT        │
                                              │ • Log CP decisions  │
                                              │ • Generate Top-3    │
                                              └─────────────────────┘
```

## Data Model & Authority

### Entity Mapping

| Entity Concept | Leantime Field    | Task-Master Field | ConPort Field     | Authority Source |
|----------------|-------------------|-------------------|-------------------|------------------|
| **Identity**   | ticket_id         | task_id          | entity_id         | Generated hash   |
| **Title**      | headline          | title            | summary           | LWW              |
| **Status**     | status            | status           | —                 | **Leantime**     |
| **Subtasks**   | (limited)         | subtasks[]       | —                 | **Task-Master**  |
| **Decisions**  | comments          | notes            | log_decision()    | **ConPort**      |
| **Assignee**   | userId/assignee   | assignee         | author            | Leantime         |
| **Modified**   | timestamp         | updated_at       | timestamp         | LWW              |

### Deduplication Strategy

1. **Primary**: Normalize titles using fuzzy matching (Levenshtein distance < 3)
2. **Secondary**: Content hash of description + key metadata
3. **Fallback**: Manual review queue for ambiguous cases

## Interface Specifications

### Leantime Integration (JSON-RPC over HTTP)

```typescript
interface LeantimeSync {
  // Read Operations
  listTickets(filter: {status: 'active'|'in_progress'|'blocked'}): Ticket[]
  getTicket(id: string): Ticket

  // Write Operations
  updateTicketStatus(id: string, status: string): boolean
  addTicketComment(id: string, comment: string, type: 'sync'): boolean
  createTicket(ticket: NewTicket): string
}

interface Ticket {
  id: string
  headline: string
  status: 'open'|'in_progress'|'completed'|'blocked'
  assignee: string
  updated_at: string
  project_id: string
}
```

### Task-Master Integration (MCP)

```typescript
interface TaskMasterSync {
  // Read Operations
  list_tasks(filter: {active: boolean}): Task[]
  get_next_task(context?: string): Task

  // Write Operations
  set_status(task_id: string, status: string): boolean
  expand_task(task_id: string, prd: string): Task[]
  parse_prd(content: string): Task[]
}

interface Task {
  id: string
  title: string
  status: 'todo'|'in_progress'|'done'|'blocked'
  subtasks: Task[]
  assignee: string
  updated_at: string
  parent_id?: string
}
```

### ConPort Integration (MCP)

```typescript
interface ConPortSync {
  // Read Operations
  get_decisions(filter: {tag: 'WIP'|'active'}): Decision[]
  search_decisions(query: string): Decision[]

  // Write Operations
  log_decision(decision: Decision): string
  batch_log_items(items: LogItem[]): boolean
}

interface Decision {
  id: string
  summary: string
  context: string
  options: string[]
  decision: string
  rationale: string
  author: string
  timestamp: string
  tags: string[]
}
```

## Conflict Resolution Engine

### Resolution Matrix

| Conflict Type | Resolution Strategy | Fallback |
|---------------|-------------------|----------|
| Status Divergence | Leantime Precedence | Manual Review if TM significantly newer |
| Subtask Changes | Task-Master Authority | Link-back to Leantime |
| Decision Updates | ConPort Authority | Batch logging |
| Title/Description | Last-Write-Wins | Manual Review if simultaneous |
| Assignment Changes | Last-Write-Wins | Audit log |

### Conflict Detection

```python
def detect_conflict(entity_a, entity_b, threshold_seconds=60):
    """Detect conflicts requiring manual review"""
    time_diff = abs(entity_a.updated_at - entity_b.updated_at)

    # Simultaneous edits
    if time_diff < threshold_seconds:
        return ConflictType.SIMULTANEOUS_EDIT

    # Authority override conditions
    if entity_a.source == 'taskmaster' and entity_b.source == 'leantime':
        if entity_b.status_unchanged_for > 30 * 60:  # 30 minutes
            return ConflictType.STALE_AUTHORITY

    return ConflictType.NONE
```

## Deployment Architecture

### Container Specifications

```yaml
# docker-compose.yml
services:
  sync-service:
    image: dopemux/zero-touch-sync:latest
    environment:
      - SYNC_INTERVAL_SEC=300
      - LEANTIME_URL=${LEANTIME_URL}
      - LEANTIME_TOKEN=${LEANTIME_TOKEN}
      - TASKMASTER_CMD=uvx task-master-ai
      - CONPORT_CMD=uvx --from context-portal-mcp conport-mcp --mode stdio
      - TOP3_TODAY_ENABLED=true
      - DAILY_DIGEST_TIME=09:00
      - BATCH_LOG_ENABLED=true
    volumes:
      - sync_logs:/app/logs
      - sync_data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 60s
      timeout: 10s
      retries: 3
```

### Configuration Management

Environment variables with validation:

```python
class SyncConfig:
    sync_interval_sec: int = 300
    leantime_url: str
    leantime_token: SecretStr
    taskmaster_cmd: str = "uvx task-master-ai"
    conport_cmd: str = "uvx --from context-portal-mcp conport-mcp --mode stdio"

    # ADHD Features
    top3_today_enabled: bool = True
    daily_digest_time: str = "09:00"
    batch_log_enabled: bool = True

    # Reliability
    max_retries: int = 3
    backoff_multiplier: float = 1.5
    health_check_interval: int = 60
```

## Monitoring & Observability

### Key Metrics

```python
# Prometheus metrics
sync_pass_duration_seconds = Histogram('sync_pass_duration_seconds')
sync_entities_processed_total = Counter('sync_entities_processed_total')
sync_conflicts_total = Counter('sync_conflicts_total', ['type', 'source'])
sync_errors_total = Counter('sync_errors_total', ['system', 'operation'])
review_queue_length = Gauge('review_queue_length')
```

### Health Checks

1. **Service Health**: HTTP endpoint returning sync service status
2. **System Connectivity**: Test MCP/JSON-RPC connections to all systems
3. **Data Integrity**: Sample entity consistency checks
4. **Queue Health**: Review queue length and age of oldest item

### Alerting Rules

```yaml
# Alerting conditions
- alert: SyncServiceDown
  expr: up{job="zero-touch-sync"} == 0
  for: 2m

- alert: SyncConflictsHigh
  expr: review_queue_length > 10
  for: 5m

- alert: SyncLatencyHigh
  expr: sync_pass_duration_seconds > 60
  for: 3m
```

## Security Model

### Authentication & Authorization

- **Leantime**: Personal Access Token with project read/write scope
- **Task-Master**: Local CLI execution (user context)
- **ConPort**: MCP over stdio (process isolation)

### Data Protection

```python
# Secret handling
class SecretManager:
    def get_token(self, system: str) -> str:
        """Retrieve token from secure store"""
        return os.getenv(f"{system.upper()}_TOKEN") or vault.get(f"sync/{system}/token")

    def redact_logs(self, message: str) -> str:
        """Remove sensitive data from logs"""
        patterns = [r'token=\w+', r'password=\w+', r'key=\w+']
        for pattern in patterns:
            message = re.sub(pattern, 'token=***', message)
        return message
```

### Audit Trail

All sync operations logged with:
- Correlation ID per sync pass
- Entity changes with before/after state
- Conflict resolution decisions
- Error details and retry attempts

## Performance Characteristics

### Baseline Performance

- **Sync Duration**: <30 seconds for typical dataset (100 active entities)
- **Memory Usage**: <512MB RSS under normal load
- **CPU Usage**: <10% average, <50% during sync passes
- **Storage**: ~1GB for 6 months of audit logs

### Scaling Considerations

- **Horizontal**: Multiple instances with leader election (future)
- **Vertical**: Configurable parallelism for system polling
- **Data**: Archival of old audit logs and resolved conflicts

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [ADR-037: Status Source of Truth](../90-adr/037-status-source-leantime.md)
- [ADR-040: Sync Mechanism](../90-adr/040-sync-mechanism-polling-mcp.md)
- [ADR-041: Conflict Resolution](../90-adr/041-conflict-resolution-lww-precedence.md)
- [Runbook: Zero-Touch Sync Operations](../92-runbooks/runbook-zero-touch-sync.md)