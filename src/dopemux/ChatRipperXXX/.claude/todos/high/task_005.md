## Task: Embedding provider abstraction, selection, and fallback
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [1], [3], [4]

### Description
Design a unified interface for multiple SOTA embedding providers with provider registry, selection logic, allow-cloud gating, and graceful fallback.

### Implementation Details
Implementation:
- Define interface:
class EmbeddingProvider(Protocol):
  name: str
  model_id: str
  dim: int
  async def embed(self, texts: list[str], input_type: str = 'search_document') -> list[list[float]]: ...
  async def close(self): ...
- Registry + config-driven selection and ordered fallbacks from settings.fallback_chain
- Feature flags: settings.allow_cloud gate any network-based provider
- Provider health check: lightweight self test (e.g., embed(["ping"])) with timeout
- Add exceptions ProviderUnavailable(AppError subclass)
- Selection pseudocode:
async def get_provider_chain(primary: str, registry: dict[str, EmbeddingProvider]):
  order = [primary] + [p for p in settings.fallback_chain if p != primary]
  for name in order:
    prov = registry.get(name)
    if not prov: continue
    try:
      await asyncio.wait_for(prov.embed(["ping"], 'search_document'), timeout=5)
      yield prov
    except Exception as e:
      log.warn("provider_unavailable", provider=name, err=str(e))
      continue
- Backward compatibility: include legacy provider wrapper exposing current embedding implementation
- Ensure deterministic fingerprint for caching: model_id + provider_version + input_type + norm setting


### Test Strategy
- Unit tests for selection ordering and fallback when primary fails
- Test allow_cloud=False blocks Cohere provider with explicit ProblemDetails
- Ensure legacy provider remains selectable and functions
- Contract tests: all providers implement embed close and return correct dims

### Migration Notes
- Originally Task ID: 5
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [1, 3, 4]

### Related Files
- Original: .taskmaster/tasks/tasks.json
