## Task: Integrate Cohere v3.0 embedding provider with allow-cloud gating
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [5]

### Description
Add Cohere embeddings (embed-english-v3.0 / embed-multilingual-v3.0) with robust error handling, rate limiting, and privacy gate.

### Implementation Details
Implementation:
- SDK: cohere>=5.5.0
- Client init lazily, read COHERE_API_KEY from env via settings; refuse to init when settings.allow_cloud=False
- Parameters: model='embed-english-v3.0' or 'embed-multilingual-v3.0'; input_type in {'search_document','search_query','classification','clustering'}; truncate='END'
- Implement backoff on 429/5xx with exponential jitter (e.g., 100ms -> 2s, max 5 retries)
Pseudocode:
import cohere, asyncio, time, random
class CohereProvider(EmbeddingProvider):
  name = 'cohere'
  def __init__(self, model_id: str): self.model_id = model_id; self.dim = 1024  # per v3 models
  async def embed(self, texts: list[str], input_type='search_document'):
    if not settings.allow_cloud: raise ProviderUnavailable('Cloud disabled', status=412)
    def call():
      client = cohere.Client(api_key=settings.cohere_api_key)
      return client.embed(texts=texts, model=self.model_id, input_type=input_type, truncate='END')
    for attempt in range(5):
      try:
        resp = await asyncio.to_thread(call)
        return resp.embeddings
      except cohere.RateLimitError:
        await asyncio.sleep(min(2 ** attempt / 10 + random.random()/10, 2.0))
      except Exception as e:
        if attempt==4: raise ProviderUnavailable('Cohere error', detail=str(e))
- Ensure no PII is logged; mask API key


### Test Strategy
- Mock cohere.Client in unit tests; simulate 429 then success to verify backoff
- Verify allow_cloud=False raises ProblemDetails/ProviderUnavailable
- Dimension sanity check for returned vectors
- Contract tests same as other providers

### Migration Notes
- Originally Task ID: 7
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [5]

### Related Files
- Original: .taskmaster/tasks/tasks.json
