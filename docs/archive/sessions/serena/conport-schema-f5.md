# F5: Pattern Learning - ConPort Schema

**Purpose**: Document ConPort storage schema for pattern learning system

## Custom Data Categories

### 1. `pattern_learning` - Learned Pattern Storage

**Category**: `pattern_learning`
**Key Format**: `{pattern_type}:{pattern_value}`
**Example Key**: `file_extension:.py`

**Value Schema**:
```json
{
  "pattern_type": "file_extension|directory|branch_prefix",
  "pattern_value": ".py|services/auth|feature",
  "total_observations": 42,
  "first_seen": "2025-10-04T10:30:00Z",
  "last_seen": "2025-10-04T14:22:00Z",
  "probability": 0.75,
  "metadata": {
    "file_count_avg": 3.2,
    "common_branches": ["feature/api", "feature/auth"],
    "user_confirmed_count": 12,
    "user_ignored_count": 2
  }
}
```

**ConPort Operations**:
```python
# Store/update pattern
await conport_client.log_custom_data(
    workspace_id=workspace_id,
    category="pattern_learning",
    key="file_extension:.py",
    value={
        "pattern_type": "file_extension",
        "pattern_value": ".py",
        "total_observations": 42,
        "probability": 0.75,
        # ... rest of schema
    }
)

# Retrieve pattern
patterns = await conport_client.get_custom_data(
    workspace_id=workspace_id,
    category="pattern_learning",
    key="file_extension:.py"  # Optional: omit to get all patterns
)

# Search patterns
results = await conport_client.search_custom_data_value_fts(
    workspace_id=workspace_id,
    query_term="services",
    category_filter="pattern_learning"
)
```

### 2. `pattern_events` - Pattern Event Log

**Category**: `pattern_events`
**Key Format**: `{event_type}_{timestamp}`
**Example Key**: `pattern_observed_1728048600.123`

**Value Schema**:
```json
{
  "event_type": "pattern_observed|pattern_confirmed|pattern_ignored",
  "timestamp": "2025-10-04T14:30:00.123Z",
  "pattern": {
    "type": "file_extension",
    "value": ".py",
    "frequency": 3,
    "context": {
      "branch": "feature/api",
      "total_files": 5
    }
  },
  "metadata": {
    "detection_id": "detect_1728048600",
    "confidence_score": 0.72,
    "user_action": "tracked|dismissed|ignored",
    "session_id": "session_2025-10-04_14"
  }
}
```

**Event Types**:
- **pattern_observed**: Pattern detected in uncommitted work
- **pattern_confirmed**: User acted on suggestion (created ConPort task)
- **pattern_ignored**: User dismissed suggestion or took no action

**ConPort Operations**:
```python
# Log pattern event
event_key = f"pattern_observed_{datetime.now().timestamp()}"
await conport_client.log_custom_data(
    workspace_id=workspace_id,
    category="pattern_events",
    key=event_key,
    value={
        "event_type": "pattern_observed",
        "timestamp": datetime.now().isoformat(),
        "pattern": {...},
        "metadata": {...}
    }
)

# Query recent events (last 90 days)
from datetime import datetime, timedelta
events = await conport_client.get_custom_data(
    workspace_id=workspace_id,
    category="pattern_events"
)

# Filter events by timestamp (application-level filtering)
cutoff = datetime.now() - timedelta(days=90)
recent_events = [
    e for e in events
    if datetime.fromisoformat(e["value"]["timestamp"]) > cutoff
]
```

## Pattern Probability Calculation

**Formula**: Time-decayed frequency
```
decay_factor = 0.5^(days_ago / 30)
weighted_count = Σ(event * decay_factor)
probability = weighted_count / total_events
```

**Implementation**:
```python
async def calculate_pattern_probability(
    pattern_type: str,
    pattern_value: str,
    lookback_days: int = 90
) -> float:
    # 1. Query pattern_events
    events = await conport_client.get_custom_data(
        workspace_id=workspace_id,
        category="pattern_events"
    )

    # 2. Filter by pattern type/value and lookback window
    cutoff = datetime.now() - timedelta(days=lookback_days)
    matching_events = [
        e for e in events
        if (e["value"]["pattern"]["type"] == pattern_type and
            e["value"]["pattern"]["value"] == pattern_value and
            datetime.fromisoformat(e["value"]["timestamp"]) > cutoff)
    ]

    # 3. Calculate time-decayed frequency
    weighted_count = 0.0
    for event in matching_events:
        timestamp = datetime.fromisoformat(event["value"]["timestamp"])
        days_ago = (datetime.now() - timestamp).days
        decay_factor = 0.5 ** (days_ago / 30)  # 30-day half-life
        weighted_count += decay_factor

    # 4. Calculate probability
    total_events = len(matching_events)
    probability = weighted_count / total_events if total_events > 0 else 0.0

    # 5. Update pattern_learning with latest probability
    await conport_client.log_custom_data(
        workspace_id=workspace_id,
        category="pattern_learning",
        key=f"{pattern_type}:{pattern_value}",
        value={
            "pattern_type": pattern_type,
            "pattern_value": pattern_value,
            "total_observations": total_events,
            "probability": probability,
            "last_calculated": datetime.now().isoformat()
        }
    )

    return probability
```

## Migration and Maintenance

### Initial Setup
No migrations required - ConPort custom_data supports arbitrary categories.

### Data Retention
- **pattern_events**: Keep last 180 days (configurable)
- **pattern_learning**: Keep indefinitely (updated on each calculation)

### Cleanup Strategy
```python
# Periodic cleanup (run weekly)
async def cleanup_old_pattern_events(days_to_keep: int = 180):
    events = await conport_client.get_custom_data(
        workspace_id=workspace_id,
        category="pattern_events"
    )

    cutoff = datetime.now() - timedelta(days=days_to_keep)

    for event in events:
        timestamp = datetime.fromisoformat(event["value"]["timestamp"])
        if timestamp < cutoff:
            # Delete old event
            await conport_client.delete_custom_data(
                workspace_id=workspace_id,
                category="pattern_events",
                key=event["key"]
            )
```

## Performance Optimization

### Caching Strategy
1. **Pattern Probability Cache**: 1-hour TTL, max 1000 entries
2. **Recent Events Cache**: 5-minute TTL for hot paths
3. **Top Patterns Cache**: 10-minute TTL, refreshed on write

### Query Optimization
- Use `category_filter` to limit FTS queries
- Batch pattern event writes when possible
- Pre-calculate probabilities during low-traffic periods

## ADHD Accommodations

### Performance Targets
- Pattern lookup: < 100ms (cache hit)
- Pattern calculation: < 1s (with ConPort query)
- Event logging: < 50ms (async, non-blocking)

### Result Limiting
- Max 10 patterns per query (enforced in `get_top_patterns()`)
- Progressive disclosure: Essential patterns first, details on request
- Visual indicators for high-confidence patterns (P > 0.7)

---

**Schema Version**: 1.0
**Last Updated**: 2025-10-04
**Author**: Serena v2 F5 Implementation
