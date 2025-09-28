## Task: Embedding model hot-swapping and runtime reconfiguration
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [5], [6], [7], [9]

### Description
Enable switching active embedding models at runtime with minimal disruption, using feature flags, file-watch, and safe provider swaps.

### Implementation Details
Implementation:
- Config source: settings file (e.g., config.yaml/.env) + env; watch for changes with watchdog Observer
- Use an AsyncRWLock to swap provider chain atomically
- Provide a CLI/API command to trigger swap (e.g., chatripper models switch --to stella)
- On swap: warm-up new provider (lazy get), then atomically replace current provider handle; old provider.close()
- Respect cache: cache key includes model_id so old entries remain valid for backfilled docs
Pseudocode:
class ProviderManager:
  def __init__(self, registry): self._prov = None; self._lock = AsyncRWLock()
  async def current(self):
    async with self._lock.read_lock: return self._prov
  async def switch(self, name):
    async with self._lock.write_lock:
      new = build_provider(name)
      await new.embed(["ping"])  # warm
      old = self._prov; self._prov = new
      if old: await old.close()
- Emit events/logs for observability; integrate with ProblemDetails on failure


### Test Strategy
- Unit test switch path: after switch, subsequent calls use new provider; old provider closed
- Simulate failed warm-up -> no swap occurs, error surfaced
- File-watch test modifies config; manager receives event and swaps
- Concurrency test: ongoing queries unaffected by swap (readers/writers lock correctness)

### Migration Notes
- Originally Task ID: 10
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [5, 6, 7, 9]

### Related Files
- Original: .taskmaster/tasks/tasks.json
