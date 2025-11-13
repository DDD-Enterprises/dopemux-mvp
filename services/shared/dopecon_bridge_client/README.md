# DopeconBridge Client

Shared Python client for accessing the Dopemux DopeconBridge from all services.

## Overview

The DopeconBridge is the **single authority point** for:
- Cross-plane coordination (PM ↔ Cognitive)
- ConPort/Knowledge Graph access
- Event bus publishing
- Decision and progress tracking

All Dopemux services **must** use this client instead of direct ConPort/database access.

## Installation

```bash
pip install httpx pydantic
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

## Quick Start

### Sync Client

```python
from services.shared.dopecon_bridge_client import (
    DopeconBridgeClient,
    DopeconBridgeConfig,
)

# Auto-configure from environment
config = DopeconBridgeConfig.from_env()
client = DopeconBridgeClient(config=config)

# Publish an event
response = client.publish_event(
    event_type="task.completed",
    data={"task_id": "123", "status": "done"},
    source="my-service",
)

print(f"Event published: {response.message_id}")

# Close when done
client.close()
```

### Async Client

```python
from services.shared.dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

async def main():
    config = DopeconBridgeConfig.from_env()
    async with AsyncDopeconBridgeClient(config=config) as client:
        # Publish event
        response = await client.publish_event(
            event_type="task.started",
            data={"task_id": "456"},
            source="my-service",
        )
        
        # Get recent decisions
        decisions = await client.recent_decisions(limit=10)
        print(f"Found {decisions.count} recent decisions")
        
        # Save custom data
        success = await client.save_custom_data(
            workspace_id="/workspace",
            category="my_service_state",
            key="latest_checkpoint",
            value={"checkpoint_id": "chk_789", "timestamp": "2024-01-15T10:30:00Z"},
        )
```

## Configuration

### Environment Variables

```bash
# Required
DOPECON_BRIDGE_URL=http://localhost:3016

# Optional
DOPECON_BRIDGE_TOKEN=<auth-token>
DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane  # or pm_plane
```

### Programmatic Configuration

```python
config = DopeconBridgeConfig(
    base_url="http://dopecon-bridge:3016",
    token="my-secret-token",
    source_plane="cognitive_plane",
    timeout=30.0,
)
client = DopeconBridgeClient(config=config)
```

## API Reference

### Event Publishing

```python
# Publish event to event bus
response = client.publish_event(
    event_type="service.action",
    data={"key": "value"},
    stream="dopemux:events",  # optional
    source="my-service",  # optional
)

# Get stream info
info = client.get_stream_info(stream="dopemux:events")

# Get event history
history = client.get_event_history(stream="dopemux:events", count=100)
```

### Cross-Plane Routing

```python
# Route to PM plane
response = client.route_pm(
    operation="leantime.create_task",
    data={"title": "New task", "project_id": "proj_123"},
    requester="task-orchestrator",
)

if response.success:
    print(f"Task created: {response.data}")
else:
    print(f"Error: {response.error}")

# Route to cognitive plane
response = client.route_cognitive(
    operation="serena.navigate",
    data={"target": "decision_graph"},
    requester="pm-sync",
)
```

### Decision Management

```python
# Create decision
decision = client.create_decision(
    summary="Architecture decision",
    rationale="Chosen for scalability",
    implementation_details="Using microservices architecture",
    tags=["architecture", "scalability"],
    workspace_id="/workspace",
)

# Search decisions
results = client.search_decisions(
    query="authentication",
    workspace_id="/workspace",
    limit=20,
)

# Get recent decisions
recent = client.recent_decisions(workspace_id="/workspace", limit=10)

# Get related decisions
related = client.related_decisions(decision_id="dec_123", k=10)

# Semantic search
similar = client.related_text(
    query="How do we handle user authentication?",
    workspace_id="/workspace",
    k=10,
)
```

### Progress Tracking

```python
# Create progress entry
progress = client.create_progress_entry(
    description="Implement authentication module",
    status="IN_PROGRESS",
    metadata={
        "estimated_duration": 120,
        "complexity": 0.7,
        "energy_level": "high",
    },
    workspace_id="/workspace",
)

# Get progress entries
entries = client.get_progress_entries(
    workspace_id="/workspace",
    limit=50,
    status="IN_PROGRESS",  # optional filter
)
```

### Custom Data (KG Storage)

```python
# Save custom data
success = client.save_custom_data(
    workspace_id="/workspace",
    category="service_state",
    key="checkpoint_001",
    value={"data": "value", "timestamp": "2024-01-15T10:30:00Z"},
)

# Get custom data
data = client.get_custom_data(
    workspace_id="/workspace",
    category="service_state",
    key="checkpoint_001",  # optional
    limit=50,
)
```

### Links (Relationships)

```python
# Create link between items
link = client.create_link(
    source_item_type="decision",
    source_item_id="dec_123",
    target_item_type="progress_entry",
    target_item_id="prog_456",
    relationship_type="implements",
    description="This progress entry implements the decision",
)
```

## Service-Specific Adapters

For common use cases, use service-specific bridge adapters:

### Voice Commands
```python
from services.voice_commands.bridge_adapter import VoiceCommandsBridgeAdapter

async with VoiceCommandsBridgeAdapter(workspace_id="/workspace") as adapter:
    result = await adapter.store_voice_decomposition(
        user_id="user_123",
        original_task="Implement authentication",
        decomposition={...},
    )
```

### Task Orchestrator
```python
from services.task_orchestrator.adapters.bridge_adapter import TaskOrchestratorBridgeAdapter

async with TaskOrchestratorBridgeAdapter(workspace_id="/workspace") as adapter:
    result = await adapter.push_task_to_conport(task)
```

### Serena
```python
from services.serena.v2.bridge_adapter import SerenaBridgeAdapter

adapter = SerenaBridgeAdapter(workspace_id="/workspace")
decisions = await adapter.search_decisions(query="authentication")
```

### GPT-Researcher
```python
from services.dopemux_gpt_researcher.research_api.adapters.bridge_adapter import ResearchBridgeAdapter

adapter = ResearchBridgeAdapter(workspace_id="/workspace")
success = await adapter.save_research_state(task_id="task_123", state_data={...})
```

## Testing

### Unit Tests

```python
import pytest
from httpx import MockTransport, Response
from services.shared.dopecon_bridge_client import DopeconBridgeClient

def test_publish_event():
    def handler(request):
        assert request.url.path == "/events"
        return Response(200, json={
            "status": "published",
            "message_id": "msg_123",
            "stream": "dopemux:events",
            "event_type": "test.event",
            "timestamp": "2024-01-15T10:30:00Z",
        })
    
    transport = MockTransport(handler)
    client = DopeconBridgeClient(transport=transport)
    
    response = client.publish_event(
        event_type="test.event",
        data={"test": "data"},
    )
    
    assert response.message_id == "msg_123"
```

### Run Tests

```bash
python3 -m pytest tests/shared/test_dopecon_bridge_client.py -v
```

## Migration Guide

### Before (Direct ConPort Access)

```python
# DON'T DO THIS
import httpx

conport_url = "http://localhost:3004"
response = httpx.post(f"{conport_url}/api/v1/decisions", json={...})
```

### After (DopeconBridge)

```python
# DO THIS
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

async with AsyncDopeconBridgeClient.from_env() as client:
    decision = await client.create_decision(
        summary="Decision summary",
        rationale="Decision rationale",
    )
```

## Architecture

```
┌─────────────────┐
│   Your Service  │
└────────┬────────┘
         │
         ├─── DopeconBridgeClient (this package)
         │
         v
┌─────────────────────────┐
│  DopeconBridge     │  (PORT 3016)
│  (Coordination Layer)   │
└────────┬────────────────┘
         │
         ├─── ConPort (KG/Decisions)
         ├─── Redis (Events)
         ├─── PM Plane (Leantime, Task-Master)
         └─── Cognitive Plane (Serena, ADHD Engine)
```

## Error Handling

```python
from services.shared.dopecon_bridge_client import DopeconBridgeError

try:
    client.publish_event(event_type="test", data={})
except DopeconBridgeError as e:
    print(f"Bridge error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use environment configuration:**
   ```python
   config = DopeconBridgeConfig.from_env()
   ```

2. **Use async client for async services:**
   ```python
   async with AsyncDopeconBridgeClient(config) as client:
       # async operations
   ```

3. **Close sync clients explicitly:**
   ```python
   client = DopeconBridgeClient(config)
   try:
       # operations
   finally:
       client.close()
   ```

4. **Use service-specific adapters when available:**
   ```python
   # Instead of raw client calls
   from services.my_service.bridge_adapter import MyServiceBridgeAdapter
   ```

5. **Set source_plane correctly:**
   - `cognitive_plane`: For ADHD, Serena, research, orchestration
   - `pm_plane`: For Leantime, Task-Master, PM-facing services

6. **Always specify workspace_id:**
   ```python
   workspace_id = os.getenv("WORKSPACE_ID", "/workspace")
   ```

## Troubleshooting

### Connection Errors

```
DopeconBridgeError: DopeconBridge error (503): ...
```

**Solution:** Check that DopeconBridge is running at configured URL.

### Authentication Errors

```
DopeconBridgeError: DopeconBridge error (401): ...
```

**Solution:** Set `DOPECON_BRIDGE_TOKEN` environment variable.

### Authority Errors

```
DopeconBridgeError: DopeconBridge error (403): ...
```

**Solution:** Check `DOPECON_BRIDGE_SOURCE_PLANE` is correct for your operation.

## Contributing

When adding new endpoints to DopeconBridge:

1. Add endpoint to `services/mcp-dopecon-bridge/kg_endpoints.py`
2. Add method to `DopeconBridgeClient` (sync)
3. Add method to `AsyncDopeconBridgeClient` (async)
4. Add tests to `tests/shared/test_dopecon_bridge_client.py`
5. Update this README

## License

Part of the Dopemux project.
