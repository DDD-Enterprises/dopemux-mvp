---
id: DOPE_CONTEXT_FIX_SUMMARY
title: Dope_Context_Fix_Summary
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Dope-Context MCP Server Fix Summary

## Issue
The `docs_search` tool was disconnecting with error:
```
Error calling tool 'docs_search': Server disconnected without sending a response.
```

## Root Cause
The issue was a **collection name mismatch** between host and container environments:

1. **Host indexing**: Documents were indexed from `/Users/hue/code/dopemux-mvp`
   - Collection hash (MD5): `3ca12e07`
   - Collection name: `docs_3ca12e07`

2. **Container runtime**: Workspace mounted at `/workspaces/dopemux-mvp`
   - Collection hash (MD5): `3f49fa17` (different!)
   - Attempted collection name: `docs_3f49fa17` (doesn't exist in Qdrant)

3. **Result**: Container tried to search non-existent collection, causing 404 errors that appeared as disconnections

## Contributing Factors
- Missing environment variables in container:
  - `QDRANT_URL` (needed for Qdrant connection)
  - `VOYAGE_API_KEY` (needed for embeddings)
  - `OPENAI_API_KEY` (needed for context generation)
- Qdrant service had restarted and wasn't immediately accessible
- Workspace path detection inside container didn't match indexing path

## Solution
Three changes were made:

### 1. Added Environment Variables
Updated `docker-compose.yml` to include all required API keys and service URLs:
```yaml
environment:
  - QDRANT_URL=mcp-qdrant
  - QDRANT_PORT=6333
  - VOYAGEAI_API_KEY=${VOYAGEAI_API_KEY}
  - VOYAGE_API_KEY=${VOYAGEAI_API_KEY}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### 2. Workspace Hash Override
Implemented `WORKSPACE_HASH_OVERRIDE` environment variable to force consistent collection names:
```yaml
environment:
  - WORKSPACE_HASH_OVERRIDE=3ca12e07
```

Modified `services/dope-context/src/utils/workspace.py`:
```python
def workspace_to_hash(workspace_path: Path) -> str:
    """Generate stable hash from workspace path.

    Supports WORKSPACE_HASH_OVERRIDE env var for Docker compatibility.
    """
    override = os.getenv("WORKSPACE_HASH_OVERRIDE")
    if override:
        logging.info(f"Using WORKSPACE_HASH_OVERRIDE={override}")
        return override

    # Normal MD5 hash generation...
```

### 3. Container Restart
Rebuilt and restarted container with new configuration:
```bash
cd services/dope-context
docker build -t mcp-servers-dope-context .
docker run -d --name mcp-dope-context \
  -e WORKSPACE_HASH_OVERRIDE=3ca12e07 \
  ... other environment variables ...
```

## Verification
After fixes, docs_search works correctly:
```
Collection: docs_3ca12e07
✅ SUCCESS! Found 3 results
1. /Users/hue/code/dopemux-mvp/CHANGELOG_v2.1.md... (score: 0.194)
2. /Users/hue/code/dopemux-mvp/CHANGELOG.md... (score: 0.174)
3. /Users/hue/code/dopemux-mvp/README.md... (score: 0.163)
```

## Files Changed
1. `docker/mcp-servers/docker-compose.yml` - Added environment variables and hash override
2. `services/dope-context/src/utils/workspace.py` - Added WORKSPACE_HASH_OVERRIDE support

## Testing
To test docs_search functionality:
```bash
docker exec mcp-dope-context python -c "
import asyncio
from src.mcp.server import _docs_search_impl

async def test():
    results = await _docs_search_impl(
        query='two-plane architecture',
        top_k=3,
    )
    print(f'Found {len(results)} results')

asyncio.run(test())
"
```

## Lessons Learned
1. **Mount path != indexing path**: When mounting volumes in Docker, the container path differs from the host path, causing hash mismatches
2. **Environment completeness matters**: Missing env vars cause silent failures that look like disconnections
3. **Hash consistency is critical**: Collection names must match between indexing and search operations
4. **Docker networking**: Container needs proper network configuration to reach Qdrant and other services

## Future Improvements
- Add health check that verifies collection existence before startup
- Document workspace hash calculation in README
- Consider storing workspace mapping in Redis for multi-instance support
- Add better error messages when collection doesn't exist
