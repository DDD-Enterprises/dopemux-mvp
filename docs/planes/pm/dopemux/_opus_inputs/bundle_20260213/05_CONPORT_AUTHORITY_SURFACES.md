---
id: 05_CONPORT_AUTHORITY_SURFACES
title: 05 Conport Authority Surfaces
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: 05 Conport Authority Surfaces (explanation) for dopemux documentation and
  developer workflows.
---
# 05 ConPort Authority Surfaces

## Official ConPort write API surface (containerized runtime)
Source implementation: `docker/mcp-servers/conport/enhanced_server.py`

| route | purpose | write target |
|---|---|---|
| `POST /api/context/{workspace_id}` \| update active context/session fields \| `workspace_contexts` |
| `POST /api/decisions` \| log decision record \| `decisions` |
| `POST /api/progress` \| create progress entry \| `progress_entries` |
| `PUT /api/progress/{progress_id}` \| update progress entry \| `progress_entries` |
| `POST /api/custom_data` \| upsert custom key/value \| `custom_data` |
| `DELETE /api/custom_data` \| delete custom key/value \| `custom_data` |

## Auth expectations (evidence-backed)
- In `enhanced_server.py`, no bearer/API-key validation was found on the write handlers above.
- Compose env for `conport` contains DB/cache URLs but no explicit API auth secret variable.

## Direct DB write bypass surfaces
Confirmed direct SQL writers outside ConPort HTTP route handlers:
- `services/shared/conport_client/adapters/postgresql_adapter.py`
- `INSERT INTO ag_catalog.decisions`
- `INSERT INTO ag_catalog.workspace_contexts` with `ON CONFLICT (workspace_id, session_id)`
- `INSERT INTO ag_catalog.progress_entries`
- `INSERT INTO ag_catalog.custom_data` with `ON CONFLICT (workspace_id, category, key)`

## Evidence excerpts
- `docker/mcp-servers/conport/enhanced_server.py:245-272`
```text
        self.app.router.add_get('/api/context/{workspace_id}', self.get_context)
        self.app.router.add_post('/api/context/{workspace_id}', self.update_context)

        # Decision logging endpoints
        self.app.router.add_post('/api/decisions', self.log_decision)
        self.app.router.add_get('/api/decisions', self.get_decisions)

        # Progress tracking endpoints
        self.app.router.add_post('/api/progress', self.log_progress)
        self.app.router.add_get('/api/progress', self.get_progress)
        self.app.router.add_put('/api/progress/{progress_id}', self.update_progress)

        # Custom data endpoints (generic key-value store)
        self.app.router.add_post('/api/custom_data', self.save_custom_data)
```
- `docker/mcp-servers/conport/enhanced_server.py:581-588`
```text
                await conn.execute("""
                    UPDATE workspace_contexts
                    SET active_context = COALESCE($2, active_context),
                        last_activity = COALESCE($3, last_activity),
                        session_time = COALESCE($4, session_time),
                        focus_state = COALESCE($5, focus_state),
                        session_milestone = COALESCE($6, session_milestone),
                        updated_at = NOW()
```
- `docker/mcp-servers/conport/enhanced_server.py:1414-1419`
```text
                await conn.execute("""
                    INSERT INTO custom_data (workspace_id, category, key, value, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (workspace_id, category, key)
                    DO UPDATE SET value = $4, updated_at = NOW()
                """, workspace_id, category, key, json.dumps(value))
```
- `services/shared/conport_client/adapters/postgresql_adapter.py:72-76`
```text
                INSERT INTO ag_catalog.decisions
                (workspace_id, summary, rationale, implementation_details, tags)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, summary, rationale, implementation_details, tags, timestamp
```
- `services/shared/conport_client/adapters/postgresql_adapter.py:175-178`
```text
                INSERT INTO ag_catalog.workspace_contexts (workspace_id, session_id, active_context)
                VALUES ($1, $2, $3)
                ON CONFLICT (workspace_id, session_id)
                DO UPDATE SET active_context = $3, updated_at = NOW()
```
- `compose.yml:235-244`
```text
    environment:
- MCP_SERVER_PORT=3004
- DOPECON_BRIDGE_URL=http://dope-decision-graph-bridge:3016
- DATABASE_URL=postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph
- POSTGRES_URL=postgresql+asyncpg://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph
- AGE_HOST=dopemux-postgres-age
- AGE_PORT=5432
- AGE_PASSWORD=${AGE_PASSWORD:-dopemux_age_dev_password}
- REDIS_URL=redis://redis-primary:6379
- QDRANT_URL=http://mcp-qdrant:6333
```

## Command used for auth search
- `rg -n "Authorization|Bearer|X-API-Key|API_KEY|auth" docker/mcp-servers/conport/enhanced_server.py -S || true`
- Result: no matches
