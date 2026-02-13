# 08 ADHD Cognitive Plane Surfaces

## Verdict: advisory vs policy
**Policy-influencing (not advisory-only)** based on confirmed write surfaces:
- Writes ConPort custom data (`system_metrics`, `adhd_state`)
- Writes ConPort progress entries (break recommendations)
- Publishes events to Redis stream `dopemux:events`

## Surface map

| surface | type | effect | determinism note |
|---|---|---|---|
| ADHD API auth middleware | control | optional auth in dev if env key absent | behavior differs by env |
| ADHD API cache layer | state/cache | serves cached responses; fallback to in-memory cache | cache-hit/fallback changes outputs over time |
| `event_emitter` | write | publishes to `dopemux:events` with `maxlen=10000` | older events may be trimmed |
| `bridge_integration.write_custom_data` | write | persists ADHD/cognitive data via bridge/ConPort | authority mutation |
| `engine._handle_cognitive_overload` | write | creates ConPort progress entry when load > 0.8 | threshold/time based |
| `engine._update_adhd_state_in_conport` | write | persists user ADHD state in ConPort | policy data update |

## Evidence excerpts
- `services/adhd_engine/auth.py:24-30`
```text
    # If no API key configured in environment, skip auth (development mode)
    if not EXPECTED_API_KEY:
        return None

    # Check if API key provided
    if not api_key:
        raise HTTPException(
```
- `services/adhd_engine/api/routes.py:115-125`
```text
    force_memory = os.getenv("ADHD_FORCE_INMEMORY_CACHE", "").lower() in {"1", "true", "yes"}
    if force_memory:
        if not isinstance(_cache_instance, _InMemoryCache):
            _cache_instance = _InMemoryCache()
        return _cache_instance
    if _cache_instance is None:
        try:
            _cache_instance = await get_cache()
        except Exception as exc:
            logger.warning("Cache unavailable (%s); using in-memory fallback", exc)
```
- `services/adhd_engine/event_emitter.py:135-139`
```text
            await self._redis.xadd(
                self.stream_name,
                event.to_redis_dict(),
                maxlen=10000  # Keep reasonable stream length
            )
```
- `services/adhd_engine/bridge_integration.py:145-153`
```text
        if self._client:
            try:
                self._client.publish_event(
                    event_type="adhd.progress.entry",
                    data={"entry_id": entry_id, **entry},
                    stream="dopemux:events",
                    source="adhd-engine",
                )
```
- `services/adhd_engine/core/engine.py:1396-1403`
```text
        if self.conport and total_load > 0.8:  # Overload threshold
            try:
                # Create high-priority break task
                entry_id = self.conport.log_progress_entry(
                    status="TODO",
                    description=f"🧠 BREAK RECOMMENDED - System cognitive load: {total_load:.1%}. "
                                f"Consider taking a 5-10 minute break to prevent burnout."
                )
```
- `services/adhd_engine/core/engine.py:1444-1449`
```text
                # Write to ConPort
                self.conport.write_custom_data(
                    category="adhd_state",
                    key=f"user_{user_id}",
                    value=state_data
                )
```
