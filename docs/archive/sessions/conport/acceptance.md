# ConPort Acceptance Criteria

## Overview
ConPort is the central knowledge graph and context management service for Dopemux.

## Health Check
Verify the service is operational and connected to the database.

**Command**:
```bash
curl -f http://localhost:8005/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "conport",
  "database": "connected"
}
```

## Minimal Success Criteria (MSC)
Retrieve recent decisions from the knowledge graph to prove the retrieval logic and database integration.

**Command**:
```bash
curl -f http://localhost:8005/api/adhd/decisions/recent?limit=1
```

**Expected Response**:
```json
{
  "count": 1,
  "decisions": [...],
  "workspace_id": "dopemux-mvp",
  "source": "database",
  "timestamp": "..."
}
```

## Cleanup
If running via docker-compose:
```bash
docker compose stop conport
```
