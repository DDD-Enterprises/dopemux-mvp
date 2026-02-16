# 01 Global Service Inventory

## Canonical compose inventory (`compose.yml`)
Total services discovered: **21**

| service | line | ports | depends_on | key env/store hints |
|---|---:|---|---|---|
| `postgres` \| 49 \| `5432:5432` \| `-` \| `POSTGRES_*`, AGE init SQL volume |
| `redis-events` \| 73 \| `6379:6379` \| `-` | event-stream Redis |
| `redis-primary` \| 89 \| `-` \| `-` | cache Redis |
| `mysql_leantime` \| 102 \| `-` \| `-` \| `MYSQL_*` |
| `redis_leantime` \| 127 \| `-` \| `-` \| `REDIS_PASSWORD` |
| `leantime` \| 150 \| `8080:80` \| `mysql_leantime`, `redis_leantime` | PM app |
| `redis-ui` \| 198 \| `8081:5540` \| `-` | Redis insight UI |
| `mcp-qdrant` \| 209 \| `6333:6333`, `6334:6334` \| `-` | Qdrant volume |
| `conport` \| 226 \| `3004:3004`, `4004:4004` \| `postgres`, `redis-primary`, `mcp-qdrant`, `dopecon-bridge` \| `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL` |
| `pal` \| 261 \| `3003:3003` \| `-` | planner service |
| `litellm` \| 283 \| `4000:4000` \| `postgres` | LLM gateway |
| `dope-context` \| 310 \| `3010:3010` \| `mcp-qdrant` \| `QDRANT_URL`, embeddings |
| `dopecon-bridge` \| 345 \| `3016:3016` \| `postgres`, `redis-events`, `mcp-qdrant` \| `REDIS_URL`, `POSTGRES_URL` |
| `task-orchestrator` \| 383 \| `-` \| `redis-primary`, `conport`, `leantime` \| `CONPORT_URL`, `REDIS_URL` |
| `adhd-engine` \| 425 \| `-` \| `redis-primary` \| `CONPORT_URL`, `REDIS_URL` |
| `dope-memory` \| 464 \| `8096:3020` \| `postgres`, `redis-events` \| `DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite` |
| `genetic-agent` \| 504 \| `8000:8000` \| `pal`, `conport` | links to Serena + dope-context |
| `serena` \| 538 \| `3006:3006`, `4006:4006` \| `-` | MCP + info server ports |
| `gptr-mcp` \| 561 \| `3009:3009` \| `-` | researcher MCP |
| `desktop-commander` \| 582 \| `3012:3012` \| `-` | MCP desktop automation |
| `leantime-bridge` \| 602 \| `3015:3015` \| `mcp-qdrant`, `leantime` | leantime integration |

## Compose variants discovered
Found variants (service sets differ from `compose.yml`):
- `compose/legacy/docker-compose.master.yml` (21)
- `compose/legacy/docker-compose.staging.yml` (15)
- `docker-compose.unified.yml` (7)
- `docker-compose.smoke.yml` (7)
- `docker/mcp-servers/docker-compose.yml` (12)
- plus targeted integration/test variants

## Registry files
- `services/registry.yaml`: canonical ops registry (ports, health, category, compose mapping)
- `src/dopemux/mcp/registry.yaml`: MCP transport/name registry (includes `serena`, `conport`, `dope-context`, etc.)

## Service directories (`services/`)
Top-level directories found: **39** (`services/.claude` and `services/__pycache__` included by filesystem listing).

Entrypoint candidates detected (sample, full command in evidence):
- `services/dope-context/src/mcp/server.py`
- `services/dopecon-bridge/main.py`
- `services/task-orchestrator/task_orchestrator/app.py`
- `services/working-memory-assistant/main.py`
- `services/serena`: `UNKNOWN` (no direct `main.py`/`server.py` match in top scan)

## Evidence excerpts
- `compose.yml:49-71`
```text
  postgres:
    image: apache/age:release_PG16_1.6.0
    container_name: dopemux-postgres-age
    restart: unless-stopped
    networks:
- dopemux-network

    environment:
- POSTGRES_USER=dopemux_age
- POSTGRES_PASSWORD=${AGE_PASSWORD:-dopemux_age_dev_password}
- POSTGRES_DB=dopemux_knowledge_graph
```
- `compose.yml:345-364`
```text
  dopecon-bridge:
    build:
      context: ./services/dopecon-bridge
      dockerfile: Dockerfile
    container_name: dope-decision-graph-bridge
    restart: unless-stopped
    networks:
- dopemux-network

    ports:
- "3016:3016"
    environment:
- PORT_BASE=3000
- POSTGRES_URL=postgresql+asyncpg://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph
- QDRANT_URL=http://mcp-qdrant:6333
- REDIS_URL=redis://redis-events:6379
```
- `services/registry.yaml:89-106`
```text
  # MCP Services
- name: dope-query
    port: 3004
    container_port: 3004
    health_path: /health
    health_method: GET
    health_timeout_ms: 10000
    health_expected_status: 200
    compose_service_name: conport
    enabled_in_smoke: true
    category: mcp

  # Coordination Layer
- name: dopecon-bridge
```
- `src/dopemux/mcp/registry.yaml:21-33`
```text
  serena:
    transport: http
    default_enabled: true
    required_for_auto: true
    docker:
      service: serena
      compose_file: docker/mcp-servers/docker-compose.yml
      port: 3006
      health_url: http://localhost:3006/health
    local:
      command: serena
      args:
- start-mcp-server
```

## Commands used
- `rg -n "^  [a-zA-Z0-9._-]+:\s*$" compose.yml -S`
- `find . -maxdepth 3 -type f \( -name 'compose.yml' -o -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.*.yml' \) | sort`
- `find services -maxdepth 1 -mindepth 1 -type d | sort`
- `for d in services/*; do rg --files "$d" | rg '/(main|app|server|index)\.(py|ts|js)$'; done`

## Full service directory scan

| service_dir | entrypoint_candidates |
|---|---|
| `services/.claude` | UNKNOWN |
| `services/__pycache__` | UNKNOWN |
| `services/activity-capture` \| `services/activity-capture/main.py` |
| `services/adhd-dashboard` | UNKNOWN |
| `services/adhd-engine` | UNKNOWN |
| `services/adhd-notifier` \| `services/adhd-notifier/main.py` |
| `services/adhd_engine` \| `services/adhd_engine/domains/context-switch-tracker/main.py`<br>`services/adhd_engine/domains/energy-trends/main.py`<br>`services/adhd_engine/domains/roast-engine/server.py` |
| `services/agents` | UNKNOWN |
| `services/claude_brain` \| `services/claude_brain/main.py` |
| `services/complexity_coordinator` | UNKNOWN |
| `services/conport_kg` | UNKNOWN |
| `services/conport_kg_ui` | UNKNOWN |
| `services/copilot_transcript_ingester` \| `services/copilot_transcript_ingester/main.py` |
| `services/dddpg` | UNKNOWN |
| `services/dope-context` \| `services/dope-context/src/mcp/server.py` |
| `services/dope-query` | UNKNOWN |
| `services/dopecon-bridge` \| `services/dopecon-bridge/dopecon_bridge/app.py`<br>`services/dopecon-bridge/main.py` |
| `services/dopemux-gpt-researcher` \| `services/dopemux-gpt-researcher/mcp-server/server.py`<br>`services/dopemux-gpt-researcher/research_api/api/main.py`<br>`services/dopemux-gpt-researcher/research_api/main.py` |
| `services/genetic_agent` \| `services/genetic_agent/main.py` |
| `services/intelligence` | UNKNOWN |
| `services/mcp-capture` \| `services/mcp-capture/server.py` |
| `services/mcp-client` \| `services/mcp-client/main.py` |
| `services/ml-predictions` \| `services/ml-predictions/main.py`<br>`services/ml-predictions/services/ml-predictions/main.py` |
| `services/ml-risk-assessment` | UNKNOWN |
| `services/monitoring` | UNKNOWN |
| `services/monitoring-dashboard` \| `services/monitoring-dashboard/server.py` |
| `services/serena` | UNKNOWN |
| `services/session-intelligence` | UNKNOWN |
| `services/session-manager` \| `services/session-manager/src/main.py`<br>`services/session-manager/tui/main.py` |
| `services/session_intelligence` | UNKNOWN |
| `services/shared` | UNKNOWN |
| `services/slack-integration` | UNKNOWN |
| `services/task-orchestrator` \| `services/task-orchestrator/app/main.py`<br>`services/task-orchestrator/task_orchestrator/app.py` |
| `services/task-router` | UNKNOWN |
| `services/taskmaster` \| `services/taskmaster/server.py` |
| `services/taskmaster-mcp-client` | UNKNOWN |
| `services/voice-commands` | UNKNOWN |
| `services/working-memory-assistant` \| `services/working-memory-assistant/main.py`<br>`services/working-memory-assistant/mcp/server.py` |
| `services/workspace-watcher` \| `services/workspace-watcher/main.py` |
