---
id: integration-next-session
title: Integration Next Session
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Integration Checklist for Next Session
**Focus**: Real ConPort MCP + End-to-End Testing

---

## ConPort MCP Integration Points

### 1. checkpoint_manager.py (Line 163)

**Current**: Saves to `/tmp/dopemux_checkpoint_*.json`
**Replace with**:
```python
# Import ConPort MCP
# (Assuming mcp__conport functions are available)

def _save_to_conport(self, checkpoint: Checkpoint) -> str:
    checkpoint_id = f"checkpoint_{self.session_id}_{checkpoint.timestamp.timestamp()}"

    # Real ConPort save
    result = mcp__conport__log_custom_data(
        workspace_id=self.workspace_id,
        category="adhd_checkpoints",
        key=checkpoint_id,
        value=asdict(checkpoint)
    )

    return checkpoint_id
```

### 2. checkpoint_manager.py (Line 187)

**Current**: Loads from `/tmp/` JSON file
**Replace with**:
```python
def load_latest_checkpoint(self) -> Optional[Checkpoint]:
    # Query ConPort for latest checkpoint
    checkpoints = mcp__conport__get_custom_data(
        workspace_id=self.workspace_id,
        category="adhd_checkpoints",
        limit=1,
        # Need order_by parameter - check ConPort API
    )

    if not checkpoints:
        return None

    # Reconstruct from ConPort data
    data = checkpoints[0].value
    return Checkpoint(**data)
```

### 3. context_protocol.py (Line 87)

**Current**: Placeholder publish_artifact
**Replace with**:
```python
def publish_artifact(...) -> str:
    artifact_id = f"artifact_{timestamp}"

    mcp__conport__log_custom_data(
        workspace_id=self.workspace_id,
        category="ai_artifacts",
        key=artifact_id,
        value={
            "artifact_type": artifact_type,
            "agent_type": agent_type,
            "content": content,
            "confidence": confidence,
            "metadata": metadata,
            "session_id": self.session_id
        }
    )

    return artifact_id
```

### 4. context_protocol.py (Line 120)

**Current**: Returns empty list
**Replace with**:
```python
def query_artifacts(...) -> list[AIArtifact]:
    results = mcp__conport__get_custom_data(
        workspace_id=self.workspace_id,
        category="ai_artifacts",
        limit=limit
    )

    # Convert to AIArtifact objects
    artifacts = [
        AIArtifact(
            artifact_type=r.value["artifact_type"],
            agent_type=r.value["agent_type"],
            content=r.value["content"],
            confidence=r.value["confidence"],
            timestamp=datetime.fromisoformat(r.timestamp),
            metadata=r.value.get("metadata", {})
        )
        for r in results
    ]

    return artifacts
```

### 5. context_protocol.py (Line 145)

**Current**: Returns empty list
**Replace with**:
```python
def semantic_search(query: str, top_k: int = 5) -> list[AIArtifact]:
    results = mcp__conport__semantic_search_conport(
        workspace_id=self.workspace_id,
        query_text=query,
        top_k=top_k,
        filter_item_types=["custom_data"]
    )

    # Convert and filter for ai_artifacts category
    artifacts = [...]
    return artifacts
```

---

## Testing Checklist

### Phase 1: Basic ConPort Integration
- [ ] Import ConPort MCP functions (check availability)
- [ ] Test checkpoint save to ConPort
- [ ] Test checkpoint load from ConPort
- [ ] Verify auto-save works with real database
- [ ] Test across process restarts

### Phase 2: Context Sharing
- [ ] Test publish_artifact to ConPort
- [ ] Test query_artifacts from ConPort
- [ ] Test semantic search
- [ ] Verify agents can share context

### Phase 3: End-to-End
- [ ] Full workflow: research → plan → implement
- [ ] Test with real AI responses
- [ ] Verify session restoration
- [ ] Test energy adaptation
- [ ] Test break reminders

---

## Quick Start Next Session

```bash
cd /Users/hue/code/ui-build/services/orchestrator

# 1. Check ConPort MCP availability
# (Assuming you can call mcp__conport functions)

# 2. Update checkpoint_manager.py with real ConPort calls

# 3. Test
python3 src/checkpoint_manager.py

# 4. If working, update context_protocol.py

# 5. End-to-end test
python3 demo_orchestrator.py
```

---

**Estimated Time**: 2-3 hours to full ConPort integration
**Deliverable**: Production-ready auto-save + context sharing
