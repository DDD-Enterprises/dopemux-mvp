---
id: env_support_matrix
title: Env_Support_Matrix
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# G33 Phase 0: Environment Variable Support Matrix

## Unified Contract Env Vars (Proposed)

| Variable | Purpose | Current Usage |
|----------|---------|---------------|
| `DATABASE_URL` | PostgreSQL connection string | 0 services: None |
| `ENVIRONMENT` | Deployment environment (dev, staging, prod) | 0 services: None |
| `HEALTH_CHECK_PATH` | Health check endpoint path | 0 services: None |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | 3 services: conport, dopecon-bridge, task-orchestrator |
| `METRICS_ENABLED` | Enable Prometheus metrics (true/false) | 0 services: None |
| `PORT` | Service HTTP port (container-internal) | 2 services: conport, task-orchestrator |
| `REDIS_URL` | Redis connection string | 5 services: activity-capture, dopecon-bridge, serena, task-orchestrator,... |

## Current Env Var Usage Across Services

| Service | Smoke | Env Vars Used | Port Support | Log Level Support |
|---------|-------|---------------|--------------|-------------------|
| conport | ✅ | 8 | ✅ | ✅ |
| dopecon-bridge | ✅ | 26 | ❌ | ✅ |
| task-orchestrator | ✅ | 10 | ✅ | ✅ |
| activity-capture | ❌ | 7 | ❌ | ❌ |
| adhd-dashboard | ❌ | 0 | ❌ | ❌ |
| adhd-engine | ❌ | 0 | ❌ | ❌ |
| adhd-notifier | ❌ | 2 | ❌ | ❌ |
| adhd_engine | ❌ | 3 | ❌ | ❌ |
| agents | ❌ | 0 | ❌ | ❌ |
| break-suggester | ❌ | 0 | ❌ | ❌ |
| claude-brain | ❌ | 0 | ❌ | ❌ |
| claude_brain | ❌ | 0 | ❌ | ❌ |
| complexity_coordinator | ❌ | 0 | ❌ | ❌ |
| conport-bridge | ❌ | 0 | ❌ | ❌ |
| conport-kg | ❌ | 0 | ❌ | ❌ |
| conport_kg | ❌ | 0 | ❌ | ❌ |
| conport_kg_ui | ❌ | 0 | ❌ | ❌ |
| context-switch-tracker | ❌ | 0 | ❌ | ❌ |
| context7 | ❌ | 0 | ❌ | ❌ |
| dddpg | ❌ | 0 | ❌ | ❌ |
| dope-context | ❌ | 0 | ❌ | ❌ |
| dopemux-gpt-researcher | ❌ | 0 | ❌ | ❌ |
| energy-trends | ❌ | 0 | ❌ | ❌ |
| genetic-agent | ❌ | 0 | ❌ | ❌ |
| genetic_agent | ❌ | 0 | ❌ | ❌ |
| intelligence | ❌ | 0 | ❌ | ❌ |
| interruption-shield | ❌ | 0 | ❌ | ❌ |
| litellm | ❌ | 0 | ❌ | ❌ |
| mcp-client | ❌ | 6 | ❌ | ❌ |
| mcp-conport | ❌ | 0 | ❌ | ❌ |
| mcp-integration-bridge | ❌ | 0 | ❌ | ❌ |
| ml-predictions | ❌ | 0 | ❌ | ❌ |
| ml-risk-assessment | ❌ | 0 | ❌ | ❌ |
| monitoring | ❌ | 0 | ❌ | ❌ |
| monitoring-dashboard | ❌ | 0 | ❌ | ❌ |
| orchestrator | ❌ | 0 | ❌ | ❌ |
| roast-engine | ❌ | 0 | ❌ | ❌ |
| serena | ❌ | 12 | ❌ | ❌ |
| session-intelligence | ❌ | 0 | ❌ | ❌ |
| session_intelligence | ❌ | 0 | ❌ | ❌ |
| slack-integration | ❌ | 0 | ❌ | ❌ |
| task-router | ❌ | 0 | ❌ | ❌ |
| taskmaster | ❌ | 10 | ❌ | ❌ |
| taskmaster-mcp-client | ❌ | 0 | ❌ | ❌ |
| voice-commands | ❌ | 0 | ❌ | ❌ |
| working-memory-assistant | ❌ | 10 | ❌ | ❌ |
| workspace-watcher | ❌ | 0 | ❌ | ❌ |
| zen | ❌ | 0 | ❌ | ❌ |

## Most Common Env Vars

| Variable | Usage Count | Services |
|----------|-------------|----------|
| `REDIS_URL` | 5 | activity-capture, dopecon-bridge, serena, task-orchestrator, taskmaster |
| `WORKSPACE_ID` | 4 | adhd_engine, serena, task-orchestrator, taskmaster |
| `DOPEMUX_INSTANCE` | 4 | dopecon-bridge, serena, task-orchestrator, taskmaster |
| `HOST` | 3 | conport, dopecon-bridge, task-orchestrator |
| `LOG_LEVEL` | 3 | conport, dopecon-bridge, task-orchestrator |
| `OPENAI_API_KEY` | 3 | dopecon-bridge, mcp-client, taskmaster |
| `ADHD_ENGINE_URL` | 2 | activity-capture, adhd-notifier |
| `PORT` | 2 | conport, task-orchestrator |
| `POSTGRES_DB` | 2 | conport, working-memory-assistant |
| `POSTGRES_HOST` | 2 | conport, working-memory-assistant |

## Compliance Status

- **Total Services**: 48
- **Smoke-Enabled**: 3
- **Using PORT env var**: 2
- **Using LOG_LEVEL**: 3
- **Using REDIS_URL**: 5
- **Using DATABASE_URL**: 0

## Compliance Gap Analysis

- **dopecon-bridge**: Missing PORT