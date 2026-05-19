---
id: dopemux-quickstart
title: Dopemux MVP Quick Start
type: tutorial
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-20'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Shortest repo-grounded path to install and smoke-check the Dopemux multi-system stack locally.
---
# Dopemux MVP Quick Start

This guide is the shortest repo-grounded path to install Dopemux, start the
compose-backed services, and run first checks. It describes the observed
defaults in `compose.yml` and `services/registry.yaml`; local `.env` overrides
can change ports.

Dopemux is a composed workspace, not a monolithic application. The operator
entrypoint, execution handoff, PM metadata, workflow transitions, structured
context, chronicle memory, retrieval, bridge/proxy routing, and operator support
are split across different systems.

## Prerequisites

- Python 3.11 or newer.
- `uv` for Python dependency management.
- Docker with `docker compose`.
- Node.js only if you are working on UI packages.
- Access to any provider API keys required by services you choose to run.

## 1. Clone And Install

```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp
uv sync --frozen --extra dev
```

Optional workspace config render:

```bash
python scripts/render_workspace_configs.py --set-default
source "$(python scripts/workspace_env_path.py)"
```

## 2. Prepare The Compose Network

`compose.yml` declares `dopemux-network` as an external Docker network. Create
it before manual compose startup when it does not already exist:

```bash
docker network inspect dopemux-network >/dev/null 2>&1 \
  || docker network create dopemux-network
```

This packet did not run a live full-stack startup. If another operator profile
creates this network automatically, that behavior remains
`NEEDS_REPO_VERIFICATION` here.

## 3. Start The Compose Stack

```bash
docker compose -f compose.yml up -d --build
```

Check container state:

```bash
docker compose -f compose.yml ps
```

Stop the stack when finished:

```bash
docker compose -f compose.yml down
```

## 4. Run The Operator CLI

```bash
dopemux start
```

The inspected CLI entrypoint starts the operator cockpit path and handles
routing, MCP/server coordination, workspace context, and launch behavior. It is
not documented here as a complete replacement for explicit compose startup,
because this packet did not validate every runtime profile.

## 5. First Health Checks

Use compose-backed default ports unless your `.env` overrides them:

| Service | Default host port | Health path |
| --- | ---: | --- |
| dopecon-bridge | `3016` | `/health` |
| ConPort HTTP | `3004` | `/health` |
| dope-context | `3010` | `/health` |
| dope-memory | `3020` | `/health` |
| task-orchestrator | `8000` | `/health` |
| ADHD Engine | `3025` | `/health` |

```bash
curl -fsS http://localhost:3016/health
curl -fsS http://localhost:3004/health
curl -fsS http://localhost:3010/health
curl -fsS http://localhost:3020/health
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:3025/health
```

If a check fails, inspect the service directly:

```bash
docker compose -f compose.yml logs --tail=100 dopecon-bridge
docker compose -f compose.yml logs --tail=100 conport
docker compose -f compose.yml logs --tail=100 task-orchestrator
```

## 6. Authority Notes For Operators

- `dopemux` controls operator startup, routing, and coordination.
- `dopetask` owns execution after `dopemux` hands off through
  `scripts/dopetask`.
- Leantime owns passive PM metadata and project/ticket snapshots.
- task-orchestrator owns workflow-significant transitions, queue state, and
  blockers.
- ConPort owns structured decision, progress, project context, and custom-data
  context.
- dope-memory owns historical chronicle receipts.
- dope-context owns derived code/docs retrieval.
- dopecon-bridge is only bridge/proxy/event transport.
- ADHD Engine is operator support only.
- Repo Truth Extractor produces evidence artifacts; runtime truth still wins.

## Common Failures

- Missing external network: create `dopemux-network`, then rerun compose.
- Port already in use: inspect your `.env`, existing containers, and local
  processes before changing docs or code.
- Bridge route unavailable: check upstream service health; the bridge is not
  source truth.
- ConPort confusion: use the HTTP health port for HTTP checks and preserve
  separate MCP/SSE surfaces in architecture docs.
- Runtime drift: do not mark drift closed unless a live validation actually
  proves it.

## Next Reading

- [Root Quick Start](../../QUICK_START.md)
- [README](../../README.md)
- [Developer Onboarding](../02-how-to/developer-onboarding.md)
- [Architecture](../../ARCHITECTURE.md)
- [PM Plane](../../PM_PLANE.md)
- [System Boundaries](../03-reference/systems/system-boundaries.md)
- [Documentation Gap Register](../03-reference/governance/documentation-gap-register.md)
