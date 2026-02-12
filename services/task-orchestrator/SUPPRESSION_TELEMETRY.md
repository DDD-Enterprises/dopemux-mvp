# Event Coordinator Suppression Telemetry

**Status**: ✅ Implemented and Tested
**Purpose**: Answer PM Phase 2 open question: "What is the measured event-rate reduction after suppression rules?"

## Overview

Added comprehensive telemetry to the EventCoordinator to track which suppression rules suppress what events, and measure the overall signal/noise ratio.

## Implementation

### 1. SuppressionTelemetry Dataclass

New dataclass tracking:
- **Lifetime counters**: `events_received`, `events_passed`, `events_suppressed`
- **Per-rule counters**: Tracks all 6 suppression rules:
  - `suppressed_by_custom_filter`
  - `suppressed_by_deep_focus_priority`
  - `suppressed_by_deep_focus_interrupt`
  - `suppressed_by_energy_level`
  - `suppressed_by_flood`
  - `suppressed_by_expiry`
- **Per-event-type breakdown**: `{event_type: {"received": N, "suppressed": N}}`
- **Per-priority breakdown**: `{priority: {"received": N, "suppressed": N}}`
- **Start timestamp**: For rate calculations

### 2. Instrumentation

Modified `_should_process_event()` to track:
- Event reception at entry
- Per-type and per-priority tracking
- Rule-specific suppression on each return path
- Pass-through on final `return True`

Added `_record_suppression()` helper:
- Increments `events_suppressed`
- Updates per-rule counter
- Updates per-event-type and per-priority dicts

Modified `_process_event()`:
- Added `suppressed_by_expiry` counter on expiry path

### 3. Reporting

New `get_suppression_report()` method returns:

```python
{
    "summary": {
        "events_received": int,
        "events_passed": int,
        "events_suppressed": int,
        "signal_noise_ratio": float,      # passed / received
        "suppression_rate_pct": float,     # (suppressed / received) * 100
        "runtime_minutes": float
    },
    "per_rule_breakdown": {
        "custom_filter": int,
        "deep_focus_priority": int,
        "deep_focus_interrupt": int,
        "energy_level": int,
        "flood": int,
        "expiry": int
    },
    "per_event_type": {
        "task_created": {"received": N, "suppressed": N},
        ...
    },
    "per_priority": {
        "CRITICAL": {"received": N, "suppressed": N},
        ...
    },
    "adhd_state": {
        "focus_mode": str,
        "energy_level": str,
        "context_switches": int
    }
}
```

### 4. Health Endpoint Integration

Added `"suppression_telemetry": self.get_suppression_report()` to `get_coordination_health()`.

### 5. Background Logging

New `_telemetry_logger()` task:
- Logs summary every 60 seconds
- Started automatically with workers
- Format: `received=N, passed=N, suppressed=N, signal/noise=X.XX, suppression_rate=X.X%`

## Testing

Created comprehensive test suite (`tests/test_suppression_telemetry.py`) with 14 test cases:

1. ✅ **Baseline pass-through** - No suppression
2. ✅ **Custom filter suppression** - Custom filter rule
3. ✅ **Deep focus priority suppression** - Low priority in deep focus
4. ✅ **Deep focus interrupt suppression** - Non-interrupting events
5. ✅ **Energy level suppression** - High cognitive load when low energy
6. ✅ **Flood suppression** - Event flooding detection
7. ✅ **Expiry suppression** - Expired events
8. ✅ **Per-event-type tracking** - Event type breakdown
9. ✅ **Per-priority tracking** - Priority breakdown
10. ✅ **Report structure** - Correct fields present
11. ✅ **Signal/noise ratio calculation** - Math accuracy
12. ✅ **Zero events edge case** - No division by zero
13. ✅ **Rule short-circuit ordering** - First match wins
14. ✅ **Telemetry in health endpoint** - Integration

All tests pass: `14 passed in 0.09s`

## Usage

### Query Current State

```python
coordinator = await create_event_coordinator()
report = coordinator.get_suppression_report()

print(f"Signal/Noise Ratio: {report['summary']['signal_noise_ratio']:.2f}")
print(f"Suppression Rate: {report['summary']['suppression_rate_pct']:.1f}%")
print(f"Top suppression rule: {max(report['per_rule_breakdown'], key=report['per_rule_breakdown'].get)}")
```

### Monitor via Health Endpoint

```python
health = await coordinator.get_coordination_health()
telemetry = health["suppression_telemetry"]
```

### Check Logs

The telemetry logger outputs every 60 seconds:
```
INFO: 📊 Suppression Telemetry: received=150, passed=120, suppressed=30, signal/noise=0.80, suppression_rate=20.0%
```

## Performance

- **Hot path overhead**: Minimal (~3 dict increments per event)
- **Memory**: O(unique_event_types + unique_priorities) - typically < 100 entries
- **No external dependencies**: Pure in-memory counters

## Open Question Answer

**Q**: "What is the measured event-rate reduction after suppression rules?"

**A**: Now measurable via `suppression_rate_pct` in the report:
- 0% = No suppression (all events processed)
- 50% = Half of events suppressed
- 100% = All events suppressed

**Per-rule breakdown** shows which rules contribute most to suppression.

## Future Enhancements

Potential additions:
1. Persist telemetry to Redis for historical analysis
2. Add time-series tracking (hourly/daily rates)
3. Alert on excessive suppression (> 80%)
4. Dashboard visualization
5. Per-worker telemetry breakdown

## Files Modified

1. `services/task-orchestrator/event_coordinator.py`:
   - Added imports: `field`, `deque`
   - New `SuppressionTelemetry` dataclass
   - Modified `_should_process_event()` with tracking
   - New `_record_suppression()` helper
   - Modified `_process_event()` for expiry tracking
   - New `get_suppression_report()` method
   - Updated `get_coordination_health()`
   - New `_telemetry_logger()` background task
   - Modified `_start_event_workers()` to start telemetry logger

2. `services/task-orchestrator/tests/__init__.py`:
   - Created empty package init

3. `services/task-orchestrator/tests/test_suppression_telemetry.py`:
   - Created comprehensive test suite (14 tests, ~220 lines)
