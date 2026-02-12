# Phase 1 Foundation Summary

**Status**: ✅ COMPLETE  
**Date**: 2026-02-11  
**Model**: Claude Sonnet 4.5

## What We Built

Integrated Copilot transcript ingestion with Dopemux canonical capture pipeline:

1. **CopilotCaptureAdapter** (`src/dopemux/memory/adapters/copilot.py`)
   - Wraps copilot_transcript_ingester module
   - Uses `emit_capture_event()` for content-addressed deduplication
   - Stores Copilot-native IDs as payload metadata (not event_id)

2. **CLI Commands** (`src/dopemux/cli.py`)
   - `dopemux memory capture copilot <SESSION_ID>` - Ingest session
   - `dopemux memory capture copilot-list` - List available sessions

3. **Event Type Mapping** (`services/copilot_transcript_ingester/mapper.py`)
   - Added `session.error → copilot:session:error`
   - Now 15 total event type mappings

## Key Architectural Wins

**Content-Addressed Event IDs**: Copilot events use SHA-256 hashing (not Copilot UUIDs) for cross-adapter deduplication. This enables future Phase 3 scenarios where same semantic event from Claude Code and Copilot produces one Chronicle row.

**Adapter Pattern**: CopilotCaptureAdapter is now a first-class capture source alongside future Codex/Claude adapters. All converge to same `emit_capture_event()` function.

**Idempotency Verified**: `INSERT OR IGNORE` confirmed working - re-running ingestion deduplicates all events.

## Files Modified

```
src/dopemux/cli.py                               +140 lines
src/dopemux/memory/adapters/__init__.py          +3 lines (new)
src/dopemux/memory/adapters/copilot.py           +164 lines (new)
services/copilot_transcript_ingester/mapper.py   +1 line (session.error)
reports/cli-int-p1-foundation.log                +105 lines (new)
reports/cli-int-p1-foundation.summary.md         (this file)
```

## Testing Evidence

- ✅ 63 Copilot sessions detected
- ✅ 5/5 events ingested successfully
- ✅ Content-addressed IDs verified (SHA-256)
- ✅ Idempotency confirmed (0 inserted on re-run)
- ✅ Chronicle schema compatible (no changes needed)

## Deferred to Phase 2

**CLI-INT-004 (Config Validation)**: Deferred opt-in/opt-out policy to Phase 2 where lane-level configuration makes more sense with Claude Code hooks.

**CLI-INT-015 (Schema)**: No schema changes needed - existing `raw_activity_events` table handles all Copilot event types.

## Next Steps

Phase 2: Claude Code Integration
- CLI-INT-001: Harden Claude Code hooks
- CLI-INT-005: Lane opt-in policy
- CLI-INT-012: Test framework
- CLI-INT-007: Redaction config
