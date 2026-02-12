# Copilot Transcript Ingester

Parses JSONL event logs from Copilot CLI (`~/.copilot/session-state/{SESSION_ID}/events.jsonl`) and ingests them into Dope-Memory Chronicle for ADHD-optimized development memory.

## Architecture

**Strategy A: Transcript Ingestion** (Decision #2)
- Source: `~/.copilot/session-state/{UUID}/events.jsonl`
- Format: JSONL (one event per line, JSON objects)
- Target: Chronicle `raw_activity_events` table
- No external dependencies or hook APIs

## Module Structure

```
services/copilot-transcript-ingester/
├── __init__.py          # Module initialization and exports
├── __main__.py          # CLI entry point (python -m)
├── main.py              # CLI command handlers
├── parser.py            # JSONL parser and event extraction
├── mapper.py            # Copilot → Chronicle event type mapping
├── ingester.py          # Database insertion logic
└── README.md            # This file
```

## Event Type Mapping

Copilot event types map to Chronicle event types:

| Copilot Type | Chronicle Type | Purpose |
|--------------|----------------|---------|
| `session.start` | `copilot:session:start` | Session initialization |
| `user.message` | `copilot:input:user_message` | User prompt |
| `assistant.turn_start` | `copilot:ai:turn_start` | AI response beginning |
| `assistant.message` | `copilot:ai:response_start` | AI response content |
| `tool.execution_start` | `copilot:tool:invoke_start` | Tool call started |
| `tool.execution_result` | `copilot:tool:invoke_complete` | Tool result received |

Additional types: `session.end`, `assistant.turn_end`, `tool.error`, `context.window_updated`, `error`, `checkpoint`

## Usage

### List Available Sessions

```bash
python -m copilot_transcript_ingester list
```

Output:
```
Found 3 sessions:

  550e8400-e29b-41d4-a716-446655440000
    Events: 24
    Started: 2025-02-12T10:15:30Z

  550e8400-e29b-41d4-a716-446655440001
    Events: 18
    Started: 2025-02-11T14:22:15Z
```

### Ingest Session Transcript

```bash
# Basic usage (uses defaults)
python -m copilot_transcript_ingester ingest \
  --session-id 550e8400-e29b-41d4-a716-446655440000

# With custom workspace/instance IDs
python -m copilot_transcript_ingester ingest \
  --session-id 550e8400-e29b-41d4-a716-446655440000 \
  --workspace-id /Users/hue/code/my-project \
  --instance-id copilot-cli-linux

# Filter events after specific timestamp
python -m copilot_transcript_ingester ingest \
  --session-id 550e8400-e29b-41d4-a716-446655440000 \
  --since 2025-02-12T10:30:00Z
```

Output:
```
Using database: /Users/hue/code/dopemux-mvp/.dopemux/chronicle.sqlite
Ingesting events from: /Users/hue/.copilot/session-state/550e8400-e29b-41d4-a716-446655440000/events.jsonl
Session metadata: {
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_timestamp": "2025-02-12T10:15:30Z",
  "data": {...}
}
Parsed 24 events
✅ Ingested 23/24 events into Chronicle

Event type distribution:
  copilot:ai:response_start: 8
  copilot:input:user_message: 6
  copilot:tool:invoke_complete: 4
  copilot:session:start: 1
```

### View Ingestion Statistics

```bash
python -m copilot_transcript_ingester stats \
  --session-id 550e8400-e29b-41d4-a716-446655440000
```

Output:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "/Users/hue/code/dopemux-mvp",
  "instance_id": "copilot-cli-macos",
  "event_counts": {
    "copilot:ai:response_start": 8,
    "copilot:input:user_message": 6,
    "copilot:tool:invoke_complete": 4,
    "copilot:session:start": 1
  },
  "total_events": 23
}
```

## Python API

```python
from copilot_transcript_ingester import JSONLParser, ChronicleIngester

# Parse events from JSONL file
parser = JSONLParser("~/.copilot/session-state/{SESSION_ID}/events.jsonl")
events = list(parser.parse_events())

# Ingest into Chronicle
ingester = ChronicleIngester(
    db_path="/path/to/.dopemux/chronicle.sqlite",
    workspace_id="/Users/hue/code/dopemux-mvp",
    instance_id="copilot-cli-macos"
)
ingester.connect()
inserted = ingester.ingest_events(events, session_id="{SESSION_ID}")
ingester.disconnect()

print(f"Inserted {inserted} events")
```

## File Paths

- **Copilot sessions**: `~/.copilot/session-state/`
- **JSONL transcripts**: `~/.copilot/session-state/{SESSION_ID}/events.jsonl`
- **Chronicle database**: `.dopemux/chronicle.sqlite` (or `DOPEMUX_CAPTURE_LEDGER_PATH`)

## Chronicle Schema

Events are written to the `raw_activity_events` table:

```sql
CREATE TABLE raw_activity_events (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,
  event_type TEXT NOT NULL,
  source TEXT NOT NULL,

  payload_json TEXT NOT NULL,
  redaction_level TEXT DEFAULT 'strict',

  ttl_days INTEGER DEFAULT 7,
  created_at_utc TEXT NOT NULL
);
```

## Data Flow

```
~/.copilot/session-state/{UUID}/events.jsonl
           ↓
    JSONLParser.parse_events()
           ↓
  EventTypeMapper.map_event_type()
           ↓
 ChronicleIngester.ingest_events()
           ↓
  raw_activity_events table
           ↓
   (7-day retention TTL)
```

## Design Decisions

1. **No hooks or wrappers**: Reads stable JSONL files, immune to Copilot updates
2. **Content-addressed dedup**: Uses Copilot event IDs to prevent duplicates
3. **Automatic timestamp extraction**: ISO 8601 timestamps from event stream
4. **Flexible filtering**: Optional `--since` flag for incremental ingestion
5. **Database auto-discovery**: Searches common paths for Chronicle database

## Testing

Generate a new Copilot session to test:

```bash
# Create a new session with a simple prompt
copilot -p 'What is ADHD-optimized development?'

# Get the session ID from ~/.copilot/session-state (most recent)
ls -lt ~/.copilot/session-state/ | head -1

# Ingest the session
python -m copilot_transcript_ingester ingest --session-id <SESSION_UUID>

# Verify in Chronicle database
sqlite3 .dopemux/chronicle.sqlite \
  "SELECT event_type, COUNT(*) FROM raw_activity_events WHERE source='copilot-cli' GROUP BY event_type;"
```

## Performance

- **Parsing**: ~10-50ms per session (100 events)
- **Database insertion**: ~100-500ms per session (100 events)
- **Total end-to-end**: ~200-600ms for typical session

## Error Handling

- **Missing transcript file**: Raises `FileNotFoundError`
- **Invalid JSONL**: Skips malformed lines, prints warning
- **Unmapped event types**: Skips with informational message
- **Database connection**: Errors if database not found or not writable

## Dependencies

- Python 3.8+
- sqlite3 (standard library)
- json (standard library)
- pathlib (standard library)

**No external dependencies required.**
