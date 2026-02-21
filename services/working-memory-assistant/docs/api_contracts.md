---
id: api_contracts
title: Api Contracts
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Api Contracts (explanation) for dopemux documentation and developer workflows.
---
# Working Memory Assistant - API Contracts

## Overview

The Working Memory Assistant (WMA) provides persistent context snapshots for ADHD-optimized development workflows. This document outlines the interface contracts for external API consumers.

## Core Classes

### DevelopmentSnapshot

Represents a complete development context snapshot.

**Fields:**
- `id: str` - Unique snapshot identifier
- `session_id: str` - Associated development session
- `timestamp: datetime` - When snapshot was created
- `interruption_type: str` - Type of interruption (manual, context_switch, etc.)

**Context Data:**
- `current_file: Dict[str, Any]` - Currently active file with cursor position
- `open_files: List[Dict[str, Any]]` - All open files with last access times
- `tmux_state: Dict[str, Any]` - Terminal multiplexer state
- `navigation_history: List[Dict[str, Any]]` - Code navigation history from LSP

**Cognitive Context:**
- `current_task: str` - Current development task description
- `thought_process: str` - Current thought process
- `cognitive_load: float` - Current cognitive load (0.0-1.0)
- `energy_level: float` - Current energy level (0.0-1.0)
- `attention_state: str` - Current attention state
- `session_duration: int` - Session duration in seconds

**Recovery Context:**
- `next_action: str` - Suggested next action for recovery
- `critical_reminders: List[str]` - Critical reminders for session

### SnapshotResult

Result of snapshot capture operation.

**Fields:**
- `snapshot_id: str` - ID of captured snapshot
- `capture_time_ms: float` - Time taken to capture (milliseconds)
- `data_size_bytes: int` - Compressed size in bytes
- `compression_ratio: float` - Compression achieved
- `success: bool` - Whether capture succeeded
- `error: Optional[str]` - Error message if failed

### RecoveryResult

Result of context recovery operation.

**Fields:**
- `recovery_time_ms: float` - Time taken to recover (milliseconds)
- `context_restored_percentage: float` - Percentage of context restored
- `user_ready_time_seconds: float` - Time until user can resume work
- `success: bool` - Whether recovery succeeded

## Core Interfaces

### SnapshotEngine

Handles automatic context capture with performance optimization.

**Methods:**
- `async capture_snapshot(trigger_type, allow_incremental) -> SnapshotResult`
  - Captures complete or incremental development context
  - `trigger_type`: Type of trigger (manual, auto, context_switch)
  - `allow_incremental`: Whether to create incremental snapshots

- `async should_trigger_snapshot(user_id) -> bool`
  - Determines if snapshot should be triggered based on ADHD state
  - `user_id`: User identifier for ADHD context lookup

- `async getLatestSnapshot(session_id) -> Optional[DevelopmentSnapshot]`
  - Retrieves most recent snapshot for a session
  - `session_id`: Target session identifier

### RecoveryEngine

Handles instant recovery with progressive disclosure.

**Methods:**
- `async initiate_recovery(snapshot_id, user_id) -> RecoveryResult`
  - Initiates instant recovery process
  - `snapshot_id`: Snapshot to recover from
  - `user_id`: User identifier for personalization

### MemoryManager

Manages snapshot storage and optimization.

**Methods:**
- `async store_snapshot(snapshot, compression) -> Dict[str, Any]`
  - Stores compressed snapshot with configurable compression
  - `snapshot`: DevelopmentSnapshot to store
  - `compression`: Algorithm ('lz4', 'zstd')

- `async retrieve_snapshot(snapshot_id, compression) -> Optional[DevelopmentSnapshot]`
  - Retrieves and decompresses snapshot
  - `snapshot_id`: Snapshot identifier
  - `compression`: Decompression algorithm

- `async cleanup_expired_snapshots(max_age_days) -> Dict[str, Any]`
  - Cleans up snapshots older than specified days
  - Returns cleanup statistics

- `get_storage_stats() -> Dict[str, Any]`
  - Returns current storage statistics

### WorkingMemoryAssistant

Main WMA coordinator combining all components.

**Methods:**
- `async initialize() -> None`
  - Initializes WMA components and connections

- `async trigger_snapshot(trigger_type, allow_incremental) -> SnapshotResult`
  - Triggers automatic snapshot with incremental support

- `async instant_recovery(snapshot_id) -> RecoveryResult`
  - Performs instant recovery from snapshot

- `async cleanup_expired_sessions(max_session_age_days) -> Dict[str, Any]`
  - Cleans up expired sessions and associated snapshots

- `get_system_status() -> Dict[str, Any]`
  - Returns comprehensive system status and metrics

## Error Handling

### Exception Hierarchy

```
WMAError (base)
├── SnapshotError
├── RecoveryError
├── StorageError
├── ValidationError
└── ConnectionError
```

### Error Response Format

```json
{
  "error_code": "SNAPSHOT_ERROR",
  "message": "Detailed error description",
  "details": {
    "field": "optional_field_name",
    "value": "optional_invalid_value"
  }
}
```

## Performance Contracts

### Timing Guarantees

- **Snapshot Capture**: <200ms for typical development context
- **Context Recovery**: <2000ms for full recovery
- **Storage Retrieval**: <50ms for cached snapshots

### Scalability Limits

- **Concurrent Sessions**: 100+ simultaneous sessions
- **Snapshot Size**: <50MB per snapshot (compressed)
- **Storage Retention**: 30 days automatic expiration

## Security Contracts

### Data Protection

- **Encryption**: Sensitive data encrypted at rest using Fernet
- **Access Control**: JWT-based authentication required
- **Input Validation**: Comprehensive malicious input detection
- **Rate Limiting**: Configurable per-endpoint limits

### Privacy Guarantees

- **Data Ownership**: Users control their snapshot data
- **Deletion**: Complete data removal on request
- **No External Sharing**: Data never shared with third parties

## Integration Contracts

### Required Dependencies

- **Redis**: Key-value storage for snapshots (with fallback)
- **PostgreSQL**: Relational storage for metadata (optional)
- **ADHD Engine**: Real-time ADHD state integration (optional)

### Optional Integrations

- **Serena LSP**: Code-aware context capture
- **ConPort**: Knowledge graph enrichment
- **tmux**: Terminal state preservation

## Usage Examples

### Basic Snapshot Capture

```python
from wma_core import WorkingMemoryAssistant

wma = WorkingMemoryAssistant()
await wma.initialize()

# Trigger snapshot
result = await wma.trigger_snapshot("manual")
if result.success:
    print(f"Snapshot captured: {result.snapshot_id}")
else:
    print(f"Capture failed: {result.error}")
```

### Context Recovery

```python
# Recover from latest snapshot
result = await wma.instant_recovery()
if result.success:
    print(f"Recovery completed in {result.recovery_time_ms}ms")
    print(f"Context restored: {result.context_restored_percentage}%")
```

### Cleanup Operations

```python
# Clean expired snapshots
cleanup_result = await wma.memory_manager.cleanup_expired_snapshots(max_age_days=30)
print(f"Cleaned {cleanup_result['cleaned_snapshots']} snapshots")

# Clean expired sessions
session_cleanup = await wma.cleanup_expired_sessions(max_session_age_days=7)
print(f"Cleaned {session_cleanup['expired_sessions']} sessions")
```

## Monitoring Contracts

### Key Metrics

- **Performance**: Capture/recovery times, compression ratios
- **Storage**: Memory usage, snapshot counts, cleanup statistics
- **Errors**: Error rates by type, recovery success rates
- **Usage**: Session counts, snapshot frequency, feature adoption

### Logging Format

Structured JSON logging with consistent field names:
- `event_type`: Type of operation (snapshot_stored, snapshot_retrieved, etc.)
- `snapshot_id`: Associated snapshot identifier
- `user_id`: User identifier (when available)
- `session_id`: Session identifier
- `duration_ms`: Operation duration
- `size_bytes`: Data size information
- `error_code`: Error classification (when applicable)

## Version Compatibility

### API Versioning

- **Major Version**: Breaking changes to core interfaces
- **Minor Version**: New features and enhancements
- **Patch Version**: Bug fixes and performance improvements

### Backward Compatibility

- **Data Format**: Snapshots remain compatible across minor versions
- **API Contracts**: Non-breaking changes maintain compatibility
- **Migration**: Automatic migration for configuration changes

## Support Contracts

### Error Reporting

- **Structured Errors**: All errors include error codes and details
- **Recovery Guidance**: Error messages include suggested actions
- **Debug Information**: Optional debug mode for detailed diagnostics

### Performance Monitoring

- **Health Checks**: Built-in health check endpoints
- **Metrics Export**: Prometheus-compatible metrics
- **Alerting**: Configurable thresholds for performance degradation