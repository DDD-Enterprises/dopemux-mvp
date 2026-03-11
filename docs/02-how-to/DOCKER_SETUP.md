---
id: DOCKER_SETUP
title: Docker Setup
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Docker Setup (explanation) for dopemux documentation and developer workflows.
---
# Docker Setup for Dopemux

`compose.yml` at the repository root is the only supported runtime compose file.
Use `scripts/smoke_up.sh` for the core smoke profile, or `docker compose -f compose.yml ...` for full stack control.

## Files

- **compose.yml** — canonical stack definition
- **Dockerfile** — base image for Python services
- **Dockerfile.frontend** — frontend image build
- **.dockerignore** — Docker context hygiene
- **.env.example** — configuration template
- **.env.smoke** — smoke profile env file (used by smoke scripts)

## Quick Start (Core Smoke Stack)

```bash
# Start core smoke services (build included)
scripts/smoke_up.sh

# Validate runtime ports and health against registry
python tools/ports_health_audit.py --mode runtime

# Stop smoke services
scripts/smoke_down.sh
```

## Full Stack Commands

```bash
# Start all services from canonical compose
docker compose -f compose.yml up -d

# Check status and logs
docker compose -f compose.yml ps
docker compose -f compose.yml logs -f

# Stop all services
docker compose -f compose.yml down
```

## Port Overrides

`compose.yml` supports environment-driven host port overrides. Common examples:

- `POSTGRES_PORT` (default `5432`)
- `QDRANT_PORT` (default `6333`)
- `QDRANT_GRPC_PORT` (default `6334`)
- `TASK_ORCHESTRATOR_PORT` (default `8000`)
- `DOPE_MEMORY_PORT` (default `3020`)

Set these in `.env` (full stack) or `.env.smoke` (smoke profile).

## Troubleshooting

```bash
# Validate compose syntax
docker compose -f compose.yml config

# Recreate smoke stack with volume cleanup
scripts/smoke_down.sh --volumes
scripts/smoke_up.sh

# Diagnose port/health drift from registry
python tools/ports_health_audit.py --mode both
```
