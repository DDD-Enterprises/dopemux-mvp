## Task: Async lazy-loading infrastructure for embedding models
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [1]

### Description
Introduce a generic async lazy-loader with lifecycle hooks to load heavy models only when first used, with concurrency safety.

### Implementation Details
Implementation:
- Create AsyncLazyResource for thread-safe, once-only init across tasks
- Ensure GPU/CPU device selection and memory checks
- Provide unload hooks for hot-swap
Pseudocode:
class AsyncLazyResource[T]:
  def __init__(self, init_fn: Callable[[], Awaitable[T]]):
    self._init_fn = init_fn
    self._obj: T | None = None
    self._lock = asyncio.Lock()
  async def get(self) -> T:
    if self._obj is None:
      async with self._lock:
        if self._obj is None:
          self._obj = await self._init_fn()
    return self._obj
  async def reset(self):
    async with self._lock:
      self._obj = None
- Utilities for device:
import torch
 def pick_device():
   if torch.cuda.is_available(): return 'cuda'
   if torch.backends.mps.is_available(): return 'mps'
   return 'cpu'
- Add memory probe: torch.cuda.mem_get_info for CUDA if available; warn if insufficient
- Ensure initialization runs in a thread executor if blocking (load models via to_thread)


### Test Strategy
- Concurrency tests: launch 50 tasks calling get(); only one init must run
- Reset tests: after reset(), next get() re-initializes
- Simulate OOM: mock torch memory probe to trigger graceful failure with ProblemDetails

### Migration Notes
- Originally Task ID: 4
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [1]

### Related Files
- Original: .taskmaster/tasks/tasks.json
