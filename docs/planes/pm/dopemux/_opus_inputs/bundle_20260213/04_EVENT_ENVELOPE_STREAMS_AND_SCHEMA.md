# 04 Event Envelope Streams And Schema

## Canonical envelope summary (implementation-derived)
There is **no single shared envelope** across all services. Confirmed variants:

| surface | fields observed | event_id computation |
|---|---|---|
| dope-memory capture emit | `id`, `ts`, `workspace_id`, `instance_id`, `session_id`, `type`, `source`, `data` | deterministic SHA256 over fields |
| dope-memory derived output | `id`, `ts`, `workspace_id`, `instance_id`, `type`, `source`, `data` | UUID v4 at publish time |
| dopecon-bridge event bus | `event_type`, `timestamp`, `source`, `data` | no explicit `event_id` |
| dopecon_bridge package | `type`, `data`, `source`, `timestamp` | no explicit `event_id` |
| core dopemux typed event | `type`, `timestamp`, `priority`, `data`, `source` | no computed id field |

## Stream names (exact strings)

| stream | producers (proven) | consumers (proven) |
|---|---|---|
| `dopemux:events` | dopecon-bridge convenience publishers; dopecon-bridge `/events`; ADHD engine emitter | dopecon-bridge SSE `/events/stream` subscribers |
| `activity.events.v1` | dope-memory capture client default emit | dope-memory eventbus consumer group `dope-memory-ingestor` |
| `memory.derived.v1` | dope-memory eventbus consumer | UNKNOWN (consumer not proven in repo scan) |

## Publisher/consumer map (proven only)
- dope-memory consumer reads via `XREADGROUP` on `activity.events.v1`, publishes derived events to `memory.derived.v1`.
- dopecon-bridge supports generic publish to any stream via HTTP `POST /events` with request field `stream` defaulting to `dopemux:events`.

## Evidence excerpts
- `src/dopemux/memory/capture_client.py:303-320`
```text
    Fingerprint formula: event_type | session_id_or_empty | ts_bucket | stable_json(payload)
    Note: session_id_or_empty MUST be empty string ("") when session_id is None,
    not a sentinel value, to keep event_id stable across adapters and environments.
    ts_bucket = ts_utc[:19]
    session_id_normalized = session_id or ""
    fingerprint = "|".join([
            event_type,
            session_id_normalized,
            ts_bucket,
            _stable_json(payload),
        ])
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
```
- `src/dopemux/memory/capture_client.py:332-347`
```text
    stream_name = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
    redis_password = os.getenv("REDIS_PASSWORD")

    try:
        client = redis.Redis.from_url(redis_url, password=redis_password, decode_responses=True)
    envelope = {
        "id": event["id"],
        "ts": event["ts_utc"],
        "workspace_id": event["workspace_id"],
        "instance_id": event["instance_id"],
        "session_id": event.get("session_id") or "",
        "type": event["event_type"],
        "source": event["source"],
        "data": _stable_json(event["payload"]),
    }
```
- `services/working-memory-assistant/eventbus_consumer.py:36-38`
```text
INPUT_STREAM = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
OUTPUT_STREAM = os.getenv("DOPE_MEMORY_OUTPUT_STREAM", "memory.derived.v1")
CONSUMER_GROUP = os.getenv("DOPE_MEMORY_CONSUMER_GROUP", "dope-memory-ingestor")
```
- `services/working-memory-assistant/eventbus_consumer.py:507-517`
```text
            event_envelope = {
                b"id": str(uuid.uuid4()).encode(),
                b"ts": datetime.now(timezone.utc).isoformat().encode(),
                b"workspace_id": workspace_id.encode(),
                b"instance_id": instance_id.encode(),
                b"type": event_type.encode(),
                b"source": b"dope-memory",
                b"data": json.dumps(data).encode(),
            }
            msg_id = await self.redis_client.xadd(self.output_stream, event_envelope)
```
- `services/dopecon-bridge/event_bus.py:145-152`
```text
    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to Redis Stream message format"""
        return {
            "event_type": self.type,
            "timestamp": self.timestamp,
            "source": self.source or "dopecon-bridge",
            "data": json.dumps(self.data)
        }
```
- `services/dopecon-bridge/dopecon_bridge/routes.py:42-47`
```text
class PublishEventRequest(BaseModel):
    """Request to publish an event."""
    stream: str = Field(default="dopemux:events", description="Redis Stream name")
    event_type: str = Field(..., description="Event type (e.g., tasks_imported)")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    source: Optional[str] = Field(None, description="Event source identifier")
```
