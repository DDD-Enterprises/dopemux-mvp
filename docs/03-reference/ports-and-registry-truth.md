---
id: ports_and_registry_truth
title: Ports and Registry - Single Source of Truth
type: reference
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
date: '2026-02-01'
author: Platform Team
tags:
- infrastructure
- registry
- ports
- health-checks
- smoke-stack
prelude: Ports and Registry - Single Source of Truth (reference) for dopemux documentation
  and developer workflows.
---
<!-- PRELUDE: Registry.yaml is the canonical source of truth for service ports and health endpoints, eliminating silent drift between compose files and runtime configuration through automated validation. -->

# Ports and Registry: Single Source of Truth

## Overview

The Dopemux service registry (`services/registry.yaml`) is the **single source of truth** for:
- Service ports (host and container)
- Health check endpoints and expectations
- Service metadata (category, description)
- Smoke stack membership

All other configurations (Docker Compose, environment files, health check tools) **derive from or validate against** the registry.

## The Problem This Solves

**Before G31**, port configuration suffered from silent drift:
- Docker Compose hardcoded ports
- Service code used different default ports
- Health check tools probed wrong endpoints
- No validation that they agreed

**Result**: Services failed to start or connect, with debugging time wasted on port conflicts.

**After G31**: Registry is the truth, all tools validate against it, drift fails tests immediately.

## Architecture

```
services/registry.yaml  (TRUTH SOURCE)
         ↓
         ├─→ .env.smoke (generated)
         │        ↓
         │   docker-compose.smoke.yml (uses env vars)
         │
         ├─→ tools/ports_health_audit.py (validates runtime)
         │
         └─→ tests/arch/test_registry_compose_alignment.py (enforces alignment)
```

## Workflow: Making Changes

### 1. Edit Registry
```bash
vim services/registry.yaml
```

### 2. Regenerate Environment
```bash
python tools/generate_smoke_env.py
```

### 3. Validate
```bash
pytest tests/arch/test_registry_compose_alignment.py
python tools/ports_health_audit.py --mode static
```

### 4. Deploy
```bash
docker compose -f docker-compose.smoke.yml up -d --build
python tools/ports_health_audit.py --mode runtime
```

## Related Documentation

- [Docker Compose Smoke Stack](../../docker-compose.smoke.yml)
- [Service Registry](../../services/registry.yaml)
