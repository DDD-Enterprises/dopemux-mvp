---
id: DOPECONBRIDGE_CONPORT_UPDATE
title: Dopeconbridge_Conport_Update
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopeconbridge_Conport_Update (explanation) for dopemux documentation and
  developer workflows.
---
# ConPort Integration with DopeconBridge

**Version:** 2.0
**Date:** 2025-11-13
**Status:** ✅ Updated

---

## Overview

This document describes how ConPort has been updated to work seamlessly with DopeconBridge as the authoritative gateway for all cross-plane communication.

## Key Changes

### 1. No Direct ConPort Access

**Before:**
- Services accessed ConPort SQLite DB directly (`context_portal/context.db`)
- Services called ConPort HTTP API directly (`http://localhost:3010/api/...`)
- Services opened Postgres connections to ConPort database

**After:**
- All ConPort access goes through DopeconBridge
- DopeconBridge is the **only** service with direct ConPort MCP access
- Services use `DopeconBridgeClient` to interact with ConPort data

### 2. ConPort MCP Integration

DopeconBridge maintains the **single ConPort MCP connection**:

```python
# In services/dopecon-bridge/main.py
from mcp_client import ConPortMCPClient

conport_client = ConPortMCPClient(
    workspace_id=os.getenv("CONPORT_WORKSPACE_ID", os.getcwd()),
    url=os.getenv("CONPORT_URL", "http://localhost:3010")
)
```

All KG operations route through this client:
- Custom data CRUD
- Workspace queries
- Semantic search
- Decision graph operations

### 3. Event-Driven Updates

ConPort state changes now publish events:

```python
# When ConPort data changes
bridge.publish_event(
    event_type="conport.data_updated",
    data={
        "workspace_id": workspace_id,
        "category": category,
        "key": key,
        "timestamp": time.time()
    },
    source="dopecon-bridge"
)
```

Services subscribe to these events rather than polling ConPort.

---

## ConPort Endpoints in DopeconBridge

### Knowledge Graph Authority (`/kg/*`)

All KG operations are exposed via DopeconBridge REST API:

#### `/kg/custom_data` (POST)
Save custom workspace data to ConPort.

**Request:**
```json
{
  "workspace_id": "workspace-123",
  "category": "user_preferences",
  "key": "theme",
  "value": {"mode": "dark", "accent": "blue"}
}
```

**Response:**
```json
{
  "success": true,
  "workspace_id": "workspace-123",
  "category": "user_preferences",
  "key": "theme"
}
```

#### `/kg/custom_data` (GET)
Retrieve custom workspace data from ConPort.

**Query Params:**
- `workspace_id` (required)
- `category` (required)
- `key` (optional - omit to get all keys in category)
- `limit` (optional, default 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "workspace_id": "workspace-123",
      "category": "user_preferences",
      "key": "theme",
      "value": {"mode": "dark", "accent": "blue"},
      "timestamp": 1699900000.0
    }
  ]
}
```

#### `/kg/workspace/search` (POST)
Semantic search across workspace knowledge.

**Request:**
```json
{
  "workspace_id": "workspace-123",
  "query": "authentication implementation",
  "limit": 20
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Implemented JWT authentication...",
      "score": 0.95,
      "metadata": {"file": "auth.py", "line": 42}
    }
  ]
}
```

#### `/kg/workspace/context` (GET)
Get full workspace context from ConPort.

**Query Params:**
- `workspace_id` (required)

**Response:**
```json
{
  "workspace_id": "workspace-123",
  "files": [...],
  "recent_edits": [...],
  "active_tasks": [...]
}
```

---

## Migration from Direct ConPort Access

### Pattern 1: SQLite Access

**Before:**
```python
import sqlite3

conn = sqlite3.connect("context_portal/context.db")
cursor = conn.cursor()
cursor.execute("INSERT INTO custom_data ...")
conn.commit()
```

**After:**
```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient

bridge = DopeconBridgeClient.from_env()
bridge.save_custom_data(
    workspace_id=workspace_id,
    category="session_state",
    key="current_task",
    value={"task_id": "123", "status": "active"}
)
```

### Pattern 2: HTTP API Access

**Before:**
```python
import httpx

response = httpx.post(
    "http://localhost:3010/api/v1/workspace/search",
    json={"query": "bug fix", "workspace_id": ws_id}
)
results = response.json()
```

**After:**
```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient

bridge = DopeconBridgeClient.from_env()
results = bridge.search_workspace(
    workspace_id=ws_id,
    query="bug fix",
    limit=20
)
```

### Pattern 3: Postgres/AGE Direct Access

**Before:**
```python
import asyncpg

conn = await asyncpg.connect(
    host="localhost",
    port=5432,
    database="conport",
    user="conport",
    password="secret"
)
rows = await conn.fetch("SELECT * FROM decisions ...")
```

**After:**
```python
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

async with AsyncDopeconBridgeClient.from_env() as bridge:
    decisions = await bridge.recent_decisions(
        workspace_id=ws_id,
        limit=50
    )
```

---

## ConPort Configuration

### Environment Variables

ConPort itself doesn't change - it continues to run as before:

```bash
# ConPort service (unchanged)
CONPORT_PORT=3010
CONPORT_DB_PATH=/data/conport.db
CONPORT_WORKSPACE_ID=/workspace

# For Postgres/AGE mode
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=conport
POSTGRES_USER=conport
POSTGRES_PASSWORD=secret
```

### DopeconBridge Configuration

DopeconBridge connects to ConPort:

```bash
# In DopeconBridge service
CONPORT_URL=http://localhost:3010
CONPORT_WORKSPACE_ID=/workspace
```

### Client Services Configuration

Services no longer need ConPort config:

```bash
# Remove these (no longer needed):
# CONPORT_URL=...
# CONPORT_DB_PATH=...
# POSTGRES_HOST=...

# Add DopeconBridge config instead:
DOPECONBRIDGE_URL=http://localhost:3016
DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane
```

---

## Docker Compose Updates

### Before

```yaml
services:
  conport:
    image: conport:latest
    ports:
      - "3010:3010"
    networks:
      - dopemux

  my-service:
    environment:
      - CONPORT_URL=http://conport:3010  # Direct access ❌
    depends_on:
      - conport
```

### After

```yaml
services:
  conport:
    image: conport:latest
    ports:
      - "3010:3010"
    networks:
      - dopemux

  dopecon-bridge:
    build: ./services/dopecon-bridge
    ports:
      - "3016:3016"
    environment:
      - CONPORT_URL=http://conport:3010  # Only bridge accesses ConPort
    depends_on:
      - conport
    networks:
      - dopemux

  my-service:
    environment:
      - DOPECONBRIDGE_URL=http://dopecon-bridge:3016  # Via bridge ✅
    depends_on:
      - dopecon-bridge
    networks:
      - dopemux
```

---

## ConPort MCP Protocol

DopeconBridge uses the ConPort MCP protocol for operations:

### MCP Operations

```python
# In DopeconBridge
class ConPortMCPClient:
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call ConPort MCP tool"""

    async def write_custom_data(self, workspace_id, category, key, value):
        return await self.call_tool("write_custom_data", {
            "workspace_id": workspace_id,
            "category": category,
            "key": key,
            "value": value
        })

    async def read_custom_data(self, workspace_id, category, key=None):
        return await self.call_tool("read_custom_data", {
            "workspace_id": workspace_id,
            "category": category,
            "key": key
        })
```

### Available MCP Tools

DopeconBridge exposes these ConPort MCP tools:

- `write_custom_data` - Store custom workspace data
- `read_custom_data` - Retrieve custom workspace data
- `search_workspace` - Semantic search
- `get_workspace_context` - Full workspace state
- `create_decision` - Add decision to graph
- `search_decisions` - Query decision graph
- `link_decisions` - Create decision relationships

---

## Event-Driven Architecture

### ConPort Events

DopeconBridge publishes events for ConPort operations:

#### Custom Data Updated
```json
{
  "event_type": "conport.custom_data.updated",
  "data": {
    "workspace_id": "workspace-123",
    "category": "session_state",
    "key": "current_task",
    "operation": "write",
    "timestamp": 1699900000.0
  },
  "source": "dopecon-bridge"
}
```

#### Workspace Search Performed
```json
{
  "event_type": "conport.search.performed",
  "data": {
    "workspace_id": "workspace-123",
    "query": "authentication",
    "result_count": 15,
    "timestamp": 1699900000.0
  },
  "source": "dopecon-bridge"
}
```

#### Decision Created
```json
{
  "event_type": "conport.decision.created",
  "data": {
    "decision_id": "decision-789",
    "workspace_id": "workspace-123",
    "title": "Use JWT for auth",
    "timestamp": 1699900000.0
  },
  "source": "dopecon-bridge"
}
```

### Subscribing to Events

```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient

bridge = DopeconBridgeClient.from_env()

# Get recent ConPort events
history = bridge.get_event_history("dopemux:events", count=100)
conport_events = [
    event for event in history.events
    if event["type"].startswith("conport.")
]

for event in conport_events:
    print(f"ConPort event: {event['type']}")
    print(f"Data: {event['data']}")
```

---

## Testing ConPort Integration

### Unit Tests

```python
# Test DopeconBridge ConPort integration
def test_save_custom_data(mock_bridge):
    bridge = DopeconBridgeClient(config=mock_config)

    success = bridge.save_custom_data(
        workspace_id="test-ws",
        category="test",
        key="foo",
        value={"bar": "baz"}
    )

    assert success is True
    # Verify MCP call was made
```

### Integration Tests

```bash
# Start ConPort
cd context_portal
python3 server.py

# Start DopeconBridge
cd services/dopecon-bridge
python3 main.py

# Test ConPort operations via bridge
curl -X POST http://localhost:3016/kg/custom_data \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "test",
    "category": "test",
    "key": "test",
    "value": {"test": true}
  }'

# Verify in ConPort
curl http://localhost:3010/api/v1/workspace/test/custom_data
```

### Validation Script

```bash
# Comprehensive validation
./verify_dopecon_bridge.sh

# Specifically test ConPort integration
./verify_dopecon_bridge.sh --conport-only
```

---

## Monitoring ConPort Integration

### Health Checks

DopeconBridge health endpoint includes ConPort status:

```bash
curl http://localhost:3016/health?detailed=true
```

```json
{
  "status": "healthy",
  "timestamp": 1699900000.0,
  "dependencies": {
    "conport": {
      "status": "healthy",
      "url": "http://localhost:3010",
      "response_time_ms": 15
    },
    "redis": {
      "status": "healthy"
    }
  }
}
```

### Metrics

Prometheus metrics for ConPort operations:

```
# ConPort request counter
conport_requests_total{operation="write_custom_data",status="success"} 1234

# ConPort request duration
conport_request_duration_seconds{operation="write_custom_data",quantile="0.95"} 0.05

# ConPort errors
conport_errors_total{operation="write_custom_data",error_type="timeout"} 5
```

### Logs

DopeconBridge logs all ConPort operations:

```
[2025-11-13 14:53:00] INFO - ConPort write_custom_data: workspace=workspace-123 category=session_state key=current_task
[2025-11-13 14:53:01] INFO - ConPort MCP call successful: 50ms
[2025-11-13 14:53:01] INFO - Published event: conport.custom_data.updated
```

---

## Troubleshooting

### ConPort Not Responding

**Symptom:** `DopeconBridgeError: ConPort unavailable`

**Solutions:**
1. Check ConPort is running: `curl http://localhost:3010/health`
2. Verify `CONPORT_URL` in DopeconBridge config
3. Check ConPort logs for errors
4. Restart ConPort: `cd context_portal && python3 server.py`

### MCP Connection Failed

**Symptom:** `DopeconBridgeError: MCP connection failed`

**Solutions:**
1. Verify ConPort MCP endpoint is available
2. Check ConPort workspace ID is valid
3. Review ConPort MCP protocol version compatibility
4. Check network connectivity between bridge and ConPort

### Custom Data Not Persisting

**Symptom:** Data saved but not retrievable

**Solutions:**
1. Check ConPort database integrity
2. Verify workspace ID matches
3. Check category/key spelling
4. Review ConPort logs for write errors
5. Verify ConPort has write permissions to DB

### Search Not Working

**Symptom:** Workspace search returns no results

**Solutions:**
1. Check ConPort indexing is enabled
2. Verify workspace has indexed content
3. Try simpler search query
4. Check ConPort logs for indexing errors
5. Rebuild ConPort search index

---

## Best Practices

### 1. Always Use Bridge for ConPort Access

❌ **Don't:**
```python
# Direct ConPort access
import httpx
response = httpx.get("http://localhost:3010/api/...")
```

✅ **Do:**
```python
# Via DopeconBridge
from services.shared.dopecon_bridge_client import DopeconBridgeClient
bridge = DopeconBridgeClient.from_env()
result = bridge.get_custom_data(...)
```

### 2. Publish Events for ConPort Changes

```python
# After modifying ConPort data
bridge.save_custom_data(...)
bridge.publish_event(
    event_type="conport.data_updated",
    data={"workspace_id": ws_id, "category": cat, "key": key}
)
```

### 3. Use Workspace-Scoped Operations

```python
# Always scope to workspace
bridge.save_custom_data(
    workspace_id=current_workspace,  # ✅ Workspace-scoped
    category="session",
    key="state",
    value={...}
)

# Avoid global keys
bridge.save_custom_data(
    workspace_id="global",  # ❌ Avoid
    category="settings",
    key="theme",
    value={...}
)
```

### 4. Handle ConPort Errors Gracefully

```python
from services.shared.dopecon_bridge_client import DopeconBridgeError

try:
    data = bridge.get_custom_data(workspace_id, category, key)
except DopeconBridgeError as e:
    logger.warning(f"ConPort access failed: {e}")
    # Use cached data or fallback
    data = load_from_cache(key)
```

### 5. Cache ConPort Data When Appropriate

```python
import time

class ConPortCache:
    def __init__(self, bridge, ttl_seconds=300):
        self.bridge = bridge
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, workspace_id, category, key):
        cache_key = f"{workspace_id}:{category}:{key}"

        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return data

        # Fetch from ConPort via bridge
        data = self.bridge.get_custom_data(workspace_id, category, key)
        self.cache[cache_key] = (data, time.time())
        return data
```

---

## Security Considerations

### 1. No Direct ConPort Access

Services should **never** have direct ConPort credentials:

```yaml
# ❌ Don't do this
services:
  my-service:
    environment:
      - POSTGRES_PASSWORD=conport_secret
      - CONPORT_DB_PATH=/data/conport.db
```

### 2. Bridge Authentication

All ConPort access is authenticated via DopeconBridge:

```python
# Bridge validates token before forwarding to ConPort
bridge = DopeconBridgeClient(config=DopeconBridgeConfig(
    base_url="http://localhost:3016",
    token="service-specific-token"  # ✅ Bridge token, not ConPort token
))
```

### 3. Workspace Isolation

DopeconBridge enforces workspace boundaries:

```python
# Bridge validates workspace access
try:
    data = bridge.get_custom_data(
        workspace_id="other-workspace",  # User may not have access
        category="secrets",
        key="api_key"
    )
except DopeconBridgeError as e:
    # Returns 403 if not authorized
    pass
```

---

## Migration Checklist

When migrating ConPort usage to DopeconBridge:

- [ ] Identify all direct ConPort access points
- [ ] Remove SQLite connection code
- [ ] Remove Postgres/asyncpg imports
- [ ] Remove direct HTTP calls to ConPort
- [ ] Add `dopecon_bridge_client` dependency
- [ ] Replace ConPort calls with bridge client methods
- [ ] Add DopeconBridge environment variables
- [ ] Remove ConPort environment variables
- [ ] Update Docker Compose dependencies
- [ ] Test ConPort operations via bridge
- [ ] Add event publishing for state changes
- [ ] Update service documentation
- [ ] Remove ConPort credentials from service

---

## Resources

- [DopeconBridge Master Guide](./DOPECONBRIDGE_MASTER_GUIDE.md)
- [ConPort Documentation](./context_portal/README.md)
- [MCP Protocol Spec](./docs/mcp-protocol.md)
- [Event Bus Documentation](./services/dopecon-bridge/EVENTBUS_VALIDATION.md)

---

**Last Updated:** 2025-11-13
**Maintained By:** Dopemux Core Team
