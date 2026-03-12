# TRANSPORT AND RUNBOOK — dope-memory

## 1. HTTP Transport (PRIMARY — active)

### Registration

| Property | Value | Evidence |
|----------|-------|----------|
| Framework | FastAPI 0.104.1 + uvicorn 0.24.0 | `dope_memory_main.py:33-34`, `requirements.txt:1-2` |
| Port | 3020 | `dope_memory_main.py:51`, `Dockerfile.dope-memory:18` |
| Host | `0.0.0.0` | `dope_memory_main.py:1308` |
| CORS | Configurable via `ALLOWED_ORIGINS` | `dope_memory_main.py:60` |

### Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/health` | Health check | None |
| GET | `/` | Service info + tool listing (lists 7 of 10) | None |
| POST | `/tools/memory_search` | Search work log entries | None |
| POST | `/tools/memory_store` | Store manual entry | None |
| POST | `/tools/memory_recap` | Get work recap | None |
| POST | `/tools/memory_mark_issue` | Mark entry as issue | None |
| POST | `/tools/memory_link_resolution` | Link issue to resolution | None |
| POST | `/tools/memory_replay_session` | Replay session chronologically | None |
| POST | `/tools/memory_correct` | Supersede with correction | None |
| POST | `/tools/memory_generate_reflection` | Generate reflection card | None |
| POST | `/tools/memory_reflections` | Fetch reflection cards | None |
| POST | `/tools/memory_trajectory` | Get trajectory state | None |

### Required Security Controls

The HTTP surface is unauthenticated in the service itself. For any non-local deployment, operators must front dope-memory with a trusted control plane that terminates TLS, authenticates callers, enforces workspace and instance authorization, and blocks direct access to port 3020 from untrusted networks. Direct unauthenticated exposure is only acceptable for tightly scoped local development.

### Request/Response Format

- Content-Type: `application/json`
- All tool endpoints accept a JSON body matching the Pydantic request model
- Success responses return `data` dict directly (ToolResponse.data unwrapped)
- Failure responses return HTTP 400 with `{"detail": "error message"}`
- 503 returned if `mcp_server` not initialized (pre-lifespan)

### Health Check Response

```json
{
  "status": "healthy",
  "service": "dope-memory",
  "version": "1.0.0",
  "timestamp": "2026-03-06T20:22:43.000000Z"
}
```

## 2. SSE Transport (CONFIGURED BUT NOT IMPLEMENTED)

### Configuration

Source: `.claude.json`

```json
{
  "dopemux-dope-memory": {
    "type": "sse",
    "url": "http://localhost:3020/mcp",
    "env": {
      "DOPE_MEMORY_WORKSPACE_ID": "dopemux",
      "DOPE_MEMORY_INSTANCE_ID": "A"
    }
  }
}
```

### Code Evidence

**No `/mcp` endpoint exists in `dope_memory_main.py`.** The server only exposes REST endpoints under `/tools/` plus `/health` and `/`.

**Status: NOT IMPLEMENTED.** The `.claude.json` SSE configuration is either aspirational or requires an external MCP proxy (e.g., `mcp-proxy`) to bridge REST to SSE/MCP protocol.

## 3. Stdio JSON-RPC Transport (ACTIVE — thin proxy, targets WRONG port)

### Registration

Source: `services/dope-memory/mcp_stdio_adapter.py`

| Property | Value |
|----------|-------|
| Protocol | Line-delimited JSON-RPC over stdin/stdout |
| Backend URL | `http://localhost:8096/tools` (**NOT** 3020) |
| Tools | 3: `memory_recap`, `memory_search`, `memory_store` |

### Discrepancy

This adapter proxies to port **8096** (legacy WMA service), not port **3020** (canonical dope-memory server). The adapter is functionally incompatible with the current dope-memory service.

## 4. Redis Streams Transport (INTERNAL — event ingestion)

### Configuration

Source: `eventbus_consumer.py`

| Property | Env Var | Default |
|----------|---------|---------|
| Redis URL | `REDIS_URL` | `redis://localhost:6379` |
| Input Stream | `DOPE_MEMORY_INPUT_STREAM` | `activity.events.v1` |
| Output Stream | `DOPE_MEMORY_OUTPUT_STREAM` | `memory.derived.v1` |
| Consumer Group | `DOPE_MEMORY_CONSUMER_GROUP` | `dope-memory-ingestor` |
| Feature Flag | `ENABLE_EVENTBUS` | `false` |

### Flow

```
Redis stream: activity.events.v1
  │
  ▼ (EventBusConsumer reads with consumer group)
  │
  ├── Parse event envelope
  ├── Normalize event type
  ├── Check promotability
  ├── Redact payload
  ├── Promote to work_log_entry
  ├── Store in SQLite canonical ledger
  ├── Update trajectory state
  ├── Update session tracking (idle/pulse)
  ├── Trigger reflection at boundaries
  │
  ▼
Redis stream: memory.derived.v1 (emitted after promotion)
```

## 5. Startup Commands

### Docker Compose (primary)

```bash
# Full stack
docker compose up dope-memory -d

# Smoke stack
docker compose -f docker-compose.smoke.yml up dope-memory -d

# Validate compose
docker compose config
```

### Direct Python (development)

```bash
cd services/working-memory-assistant
pip install -r requirements.txt
python dope_memory_main.py
```

### Docker Build

```bash
docker build \
  -f services/working-memory-assistant/Dockerfile.dope-memory \
  -t dope-memory:dev \
  services/working-memory-assistant/
```

## 6. Health Checks

### Docker HEALTHCHECK

Source: `Dockerfile.dope-memory:60`

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1
```

### Compose Health Check (compose.yml)

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3020/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Manual Verification

```bash
curl -s http://localhost:3020/health | jq .
curl -s http://localhost:3020/ | jq .
```

## 7. Port Mappings

| Service | Internal Port | External Port | Evidence |
|---------|--------------|---------------|----------|
| dope-memory HTTP | 3020 | 3020 | `compose.yml`, `registry.yaml` |
| Legacy WMA HTTP | 8096 | — | `Dockerfile`, `main.py` |

## 8. Docker Compose Configuration

### compose.yml (production)

| Setting | Value |
|---------|-------|
| Build context | `./services/working-memory-assistant` |
| Dockerfile | `Dockerfile.dope-memory` |
| Port mapping | `3020:3020` |
| Networks | `dopemux-network` |
| Volumes | `./.dopemux:/data` |
| Depends on | `postgres` (healthy), `redis-events` (healthy) |
| Restart | `unless-stopped` |
| Key env vars | `DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite`, `ENABLE_EVENTBUS=true`, `DOPEMUX_SQLITE_JOURNAL_MODE=DELETE` |

### docker-compose.smoke.yml (smoke test)

| Setting | Value |
|---------|-------|
| Container name | `smoke-dope-memory` |
| Environment | `ENVIRONMENT=smoke` |
| Instance ID | `smoke` |
| Depends on | `redis` |
| Volumes | named volume `dope_memory_data` |

### Key Difference: compose.yml uses `JOURNAL_MODE=DELETE` (not WAL)

In compose.yml, `DOPEMUX_SQLITE_JOURNAL_MODE=DELETE` is set, overriding the default WAL mode. This is likely because the Docker volume mount (`.dopemux:/data`) uses bind-mount which may have WAL compatibility issues.

## 9. Test Commands

```bash
# Unit tests (from service directory)
cd services/working-memory-assistant
pytest tests/ -v

# Specific test file
pytest tests/unit/test_supersession_semantics.py -v

# Repo-level integration tests
cd <REPO_ROOT>
pytest tests/integration/test_canonical_ledger_convergence.py -v
```

## 10. Registry Entry

Source: `services/registry.yaml`

```yaml
- name: dope-memory
  port: 3020
  container_port: 3020
  health_path: /health
  compose_service_name: dope-memory
  enabled_in_smoke: true
  category: mcp
  description: "Dope-Memory"
```
