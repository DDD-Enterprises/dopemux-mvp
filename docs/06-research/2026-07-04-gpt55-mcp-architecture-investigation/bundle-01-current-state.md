---
id: gpt55-mcp-architecture-bundle-01-current-state
title: GPT55 MCP Architecture Bundle 01 Current State
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 1 input bundle for current-state service and MCP inventory.
---
# Bundle 01: Current State

## Purpose

Let GPT-5.5 reconstruct the observed service/server surface before designing a target architecture.

## Required Uploads

1. `prompt-01-current-state.md`
2. Phase 0 GPT-5.5 output
3. `source-manifest.md`
4. `docs/06-research/2026-07-04-dopemux-service-investigation/research.md`
5. `docs/06-research/2026-07-04-dopemux-service-investigation/service-gap-matrix.md`

## Source Files To Attach Or Paste In Chunks

Chunk A, repo authority:

- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`

Chunk B, service/config inventory:

- `compose.yml`
- `services/registry.yaml`
- `mcp_catalog.yaml`
- `src/dopemux/mcp/default_catalog.yaml`
- `.mcp.json` with secrets redacted

Chunk C, MCP implementation:

- `src/dopemux/mcp/fleet_catalog.py`
- `src/dopemux/commands/mcp_commands.py`
- `scripts/mcp-wrappers/ensure-pal.sh`
- `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh`

## Data To Collect

```bash
python - <<'PY'
from pathlib import Path
import yaml
root = Path.cwd()
print('services_dirs', len([p for p in (root / 'services').iterdir() if p.is_dir()]))
print('compose_services', len((yaml.safe_load((root / 'compose.yml').read_text()).get('services') or {})))
print('registry_services', len(yaml.safe_load((root / 'services/registry.yaml').read_text()).get('services', [])))
PY
docker compose -f compose.yml config --services
dopemux mcp status
```

Do not upload raw command output if it contains secrets. Summarize instead.

## Expected GPT-5.5 Phase Output

- current-state service matrix
- MCP server/tool surface matrix
- generated-config and consumer map
- unknowns and stale docs
- no target architecture yet
