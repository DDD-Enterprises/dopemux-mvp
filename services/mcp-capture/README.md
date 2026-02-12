# MCP Capture Server

**Version**: 1.0.0
**Blueprint**: OPUS-CLI-INT-02 Phase 3 (CLI-INT-002)
**Purpose**: Expose Chronicle capture pipeline as MCP tool for cross-adapter integration

## Overview

The MCP Capture Server provides a Model Context Protocol (MCP) interface to the Dopemux Chronicle capture system. It enables MCP-based adapters (like Codex or future tools) to emit events with the same content-addressed deduplication and lane-based policy enforcement as CLI adapters.

## Features

- **Content-Addressed Deduplication**: Same semantic event from different adapters → one Chronicle row
- **Lane Policy Enforcement**: Respects `.dopemux/config.yaml` lane configuration
- **Audit Logging**: All policy decisions logged to `.dopemux/capture_audit.log`
- **Mode Support**: plugin, cli, mcp, auto
- **Structured Results**: Returns event_id, insertion status, ledger path

## Tool: `capture/emit`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event` | object | Yes | Event envelope with event_type, ts_utc, session_id, source, payload |
| `mode` | string | No | Capture mode: "plugin", "cli", "mcp", "auto" (default: "mcp") |
| `lane` | string | No | Lane identifier for policy enforcement (e.g., "agent:primary") |
| `repo_root` | string | No | Repository root path (auto-detected if not provided) |

### Event Envelope Schema

```json
{
  "event_type": "string (required)",
  "ts_utc": "ISO 8601 timestamp (optional, defaults to now)",
  "session_id": "string (optional)",
  "source": "string (optional, defaults based on mode)",
  "payload": {
    "key": "value (arbitrary JSON)"
  }
}
```

### Response Schema

**Success:**
```json
{
  "success": true,
  "event_id": "sha256 hash of event content",
  "inserted": true,
  "ledger_path": "/path/to/.dopemux/chronicle.sqlite",
  "repo_root": "/path/to/repo",
  "mode": "mcp",
  "source": "mcp",
  "event_type": "codex:session:start"
}
```

**Policy Denied (lane disabled):**
```json
{
  "success": true,
  "event_id": "",
  "inserted": false,
  "ledger_path": "/path/to/.dopemux/chronicle.sqlite",
  "repo_root": "/path/to/repo",
  "mode": "mcp",
  "source": "mcp",
  "event_type": "codex:session:start"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Running the Server

### Standalone (stdio)
```bash
python services/mcp-capture/server.py
```

### With Claude Code

Add to `.claude/claude_config.json`:
```json
{
  "mcpServers": {
    "capture": {
      "type": "stdio",
      "command": "python",
      "args": [
        "/absolute/path/to/dopemux-mvp/services/mcp-capture/server.py"
      ]
    }
  }
}
```

### With Docker

```json
{
  "mcpServers": {
    "capture": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "dopemux-capture",
        "python",
        "/app/services/mcp-capture/server.py"
      ]
    }
  }
}
```

## Usage Examples

### Example 1: Emit Codex Session Start

```python
# Via MCP tool call
{
  "tool": "capture/emit",
  "arguments": {
    "event": {
      "event_type": "codex:session:start",
      "session_id": "abc-123-def",
      "payload": {
        "mode": "chat",
        "model": "gpt-4"
      }
    },
    "mode": "mcp",
    "lane": "agent:primary"
  }
}

# Response:
{
  "success": true,
  "event_id": "7f3a9b2c...",  # SHA-256 of event content
  "inserted": true,
  "ledger_path": "/Users/hue/code/dopemux-mvp/.dopemux/chronicle.sqlite",
  "repo_root": "/Users/hue/code/dopemux-mvp",
  "mode": "mcp",
  "source": "mcp",
  "event_type": "codex:session:start"
}
```

### Example 2: Emit with Auto-Repo Detection

```python
{
  "tool": "capture/emit",
  "arguments": {
    "event": {
      "event_type": "codex:tool:invoke_complete",
      "payload": {
        "tool": "read_file",
        "duration_ms": 45
      }
    }
  }
  # mode defaults to "mcp"
  # repo_root auto-detected from cwd
}
```

### Example 3: Cross-Adapter Deduplication

**Copilot CLI adapter emits:**
```python
# Via CLI: dopemux memory capture copilot session-123
{
  "event_type": "copilot:session:start",
  "session_id": "session-123",
  "payload": {"mode": "chat"}
}
# → event_id: 7f3a9b2c... (SHA-256 of normalized content)
```

**Hypothetical Copilot MCP adapter emits same event:**
```python
# Via MCP capture/emit
{
  "event": {
    "event_type": "copilot:session:start",
    "session_id": "session-123",
    "payload": {"mode": "chat"}
  }
}
# → event_id: 7f3a9b2c... (SAME SHA-256)
# → inserted: false (deduplicated by INSERT OR IGNORE)
```

**Result**: Chronicle contains ONE row, proving cross-adapter convergence.

## Testing

### Manual Test

```bash
# Start server
python services/mcp-capture/server.py

# Send MCP request via stdin (JSON-RPC format)
echo '{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "capture/emit",
    "arguments": {
      "event": {
        "event_type": "test:manual",
        "payload": {"test": true}
      }
    }
  },
  "id": 1
}' | python services/mcp-capture/server.py
```

### Integration Test (CLI-INT-009)

See Phase 3 testing plan for comprehensive cross-adapter deduplication tests.

## Lane Policy Integration

The server respects `.dopemux/config.yaml`:

```yaml
capture:
  lanes:
    "agent:primary":
      enabled: true
      event_types:
        - "codex:session:start"
        - "codex:tool:invoke_complete"
```

**Behavior:**
- Event with `lane="agent:primary"` and `event_type="codex:session:start"` → ALLOW
- Event with `lane="agent:primary"` and `event_type="codex:debug"` → SKIP (not in allowlist)
- Event with `lane="sandbox:shell"` → SKIP (lane disabled)
- Event with no lane → SKIP (fail-closed security)

All decisions logged to `.dopemux/capture_audit.log`.

## Architecture

```
MCP Client (Codex, future tools)
    ↓
capture/emit tool (MCP protocol)
    ↓
emit_capture_event() (src/dopemux/memory/capture_client.py)
    ↓
Lane Policy Enforcement (src/dopemux/memory/lane_policy.py)
    ↓
Chronicle Database (.dopemux/chronicle.sqlite)
```

## Error Handling

- **CaptureError**: User-facing errors (invalid mode, repo not found)
- **Exception**: Internal errors (wrapped with generic message)
- **Lane Policy Denial**: Returns success=true, inserted=false (not an error)

## Dependencies

- `mcp` - MCP Python library
- `dopemux.memory.capture_client` - Chronicle capture functions
- `dopemux.memory.lane_policy` - Policy enforcement

## Logging

Logs written to stderr (stdout reserved for MCP protocol):
- INFO: Successful captures
- ERROR: Capture errors
- EXCEPTION: Unexpected internal errors

## Next Steps

- **CLI-INT-009**: Integration tests for cross-adapter deduplication
- **CLI-INT-013**: Dual-capture safety tests (concurrent adapters)
- Phase 4: Retrieval queries and polish
- Phase 5: Documentation

## References

- Blueprint: OPUS-CLI-INT-02
- Ticket: CLI-INT-002 (MCP Capture Server)
- Chronicle Schema: `services/working-memory-assistant/chronicle/schema.sql`
- Capture Client: `src/dopemux/memory/capture_client.py`
- Lane Policy: `src/dopemux/memory/lane_policy.py`
