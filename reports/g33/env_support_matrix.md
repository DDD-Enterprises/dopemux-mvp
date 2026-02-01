# Service Environment Support Matrix

## Python Services (smoke-enabled)

| Service | Entry Point | HOST | PORT | LOG_LEVEL | BASE_URL | Config File | Notes |
|---------|------------|------|------|-----------|----------|-------------|-------|
| conport | app.py | ✅ | ✅ | ❌ | ❌ | N/A | Uses dopemux.settings.ConPortSettings |
| dopecon-bridge | main.py | ✅ | ✅ | ❌ | ✅ | N/A | Uses PORT_BASE + 16 pattern |
| task-orchestrator | server.py | ✅ | ✅ | ❌ | ❌ | N/A | N/A |

## Infrastructure Services

| Service | Type | Env Contract Applies |
|---------|------|---------------------|
| postgres | Database | ❌ (native config) |
| redis | Cache | ❌ (native config) |
| qdrant | Vector DB | ❌ (native config) |

