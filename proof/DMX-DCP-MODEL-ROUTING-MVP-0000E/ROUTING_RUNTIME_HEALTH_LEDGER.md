# DMX-DCP-MODEL-ROUTING-MVP-0000E — ROUTING_RUNTIME_HEALTH_LEDGER.md

## Routing Runtime Health (Captured 2026-06-09)

### LiteLLM / CCR Status

**Command**: `uv run dopemux routing status`

```
LITELLM:
  Status: running
  Details: gui/501/com.dopemux.litellm
CCR:
  Status: running
  Details: gui/501/com.dopemux.ccr
Service Health:
  ❌ litellm: unhealthy (127.0.0.1:4000)
```

**Classification**: `UNHEALTHY`

### Routing Alias Contract

**Command**: `uv run dopemux routing doctor`

```
❌ Stale routing alias contract detected.
Missing aliases:
  - claude-opus-4-6: expected opus
```

**Classification**: `STALE`

### Live Routing Config

**Command**: `uv run dopemux routing config`

- Mode: `api`
- 14 models configured
- 11 named slots (`default`, `think`, `codex`, `opus`, `sonnet`, `arbiter`, etc.)
- Fallback chains defined

**Classification**: `CONFIGURED` (but proxy unhealthy)

### LiteLLM Health Endpoint

**Command**: `curl http://127.0.0.1:4000/health`

**Result**: Connection refused (port not responding in this session)

**Classification**: `UNHEALTHY` (confirmed)

### Summary for 0001

- LiteLLM proxy is **running but unhealthy**
- Stale alias contract exists (`claude-opus-4-6`)
- Routing config is present and well-defined
- No live health endpoint response in current session

**Recommendation**: 0001 must treat LiteLLM as `UNHEALTHY` and should not depend on it being the primary healthy router until health is restored.
