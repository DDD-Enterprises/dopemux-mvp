# 06 Dope-Memory Promotion Retention Provenance

## Promotion rules (implementation)
- Promotable event types are explicitly allowlisted.
- Importance scores are deterministic constants (no LLM path in Phase 1).
- Promotion path is fail-closed on missing provenance fields.

### Promotable event types
- `decision.logged`
- `task.completed`
- `task.failed`
- `task.blocked`
- `error.encountered`
- `workflow.phase_changed`
- `manual.memory_store`

## Automatic vs explicit promotion
- Automatic stream path exists: eventbus consumer reads input stream and executes promotion in its loop.
- Explicit/manual promotion exists via `manual.memory_store` type.

## Retention behavior
- Raw events are inserted with `ttl_days` (default 7).
- Retention job periodically calls `cleanup_expired_raw_events()` and deletes rows from `raw_activity_events` based on current time.
- No matched evidence of retention deletion against promoted `work_log_entries` in the shown cleanup path.

## Provenance requirements
- Promotion rejects missing/sentinel provenance (`event_id`, `event_type`, `source`, `ts_utc`).
- Promoted storage schema requires provenance columns as `NOT NULL`.

## Evidence excerpts
- `services/working-memory-assistant/promotion/promotion.py:14-35`
```text
PROMOTABLE_EVENT_TYPES = frozenset(
    [
        "decision.logged",
        "task.completed",
        "task.failed",
        "task.blocked",
        "error.encountered",
        "workflow.phase_changed",
        "manual.memory_store",
    ]
)

# Deterministic importance scores (no LLM in Phase 1)
IMPORTANCE_SCORES = {
```
- `services/working-memory-assistant/promotion/promotion.py:131-145`
```text
        # Fail-closed: validate required provenance fields (Packet D §4.5)
        if not event_id or not event_type or not source or not ts_utc:
            raise ValueError(
                f"Promotion requires complete provenance: "
                f"event_id={bool(event_id)}, event_type={bool(event_type)}, "
                f"source={bool(source)}, ts_utc={bool(ts_utc)}"
            )

        # Sentinel ban (Packet D §7.8): runtime must not accept sentinel values
        sentinel_values = {'pre_migration', 'unknown', ''}
        if event_id in sentinel_values or source in sentinel_values:
```
- `services/working-memory-assistant/promotion/promotion.py:161-167`
```text
        # Inject provenance fields (Packet D §4.3)
        promoted.source_event_id = str(event_id)
        promoted.source_event_type = str(event_type)
        promoted.source_adapter = str(source)
        promoted.source_event_ts_utc = str(ts_utc)
        promoted.promotion_rule = normalized
```
- `services/working-memory-assistant/chronicle/schema.sql:68-75`
```text
  -- Provenance fields (Packet D §4.3 - Mandatory for all post-migration promotions)
  source_event_id TEXT NOT NULL,
  source_event_type TEXT NOT NULL,
  source_adapter TEXT NOT NULL,
  source_event_ts_utc TEXT NOT NULL,
  promotion_rule TEXT NOT NULL,
  promotion_ts_utc TEXT NOT NULL,
```
- `services/working-memory-assistant/chronicle/store.py:256-269`
```text
    def insert_raw_event(
        self,
        workspace_id: str,
        instance_id: str,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        *,
        event_id: Optional[str] = None,
        ts_utc: Optional[str] = None,
        session_id: Optional[str] = None,
        redaction_level: str = "strict",
        ttl_days: int = 7,
    ) -> str:
```
- `services/working-memory-assistant/chronicle/store.py:317-328`
```text
    def cleanup_expired_raw_events(self) -> int:
        """Delete raw events past their TTL.
        Returns:
            Number of deleted rows
        """
        cursor = conn.execute(
            """
            DELETE FROM raw_activity_events
            WHERE datetime(ts_utc) < datetime('now', '-' || ttl_days || ' days')
            """
        )
```
- `services/working-memory-assistant/dope_memory_main.py:855-857`
```text
ENABLE_RETENTION_JOB = os.getenv("ENABLE_RETENTION_JOB", "true").lower() == "true"
RETENTION_INTERVAL_SEC = int(os.getenv("RETENTION_INTERVAL_SEC", "3600"))  # Default: 1 hour
```
