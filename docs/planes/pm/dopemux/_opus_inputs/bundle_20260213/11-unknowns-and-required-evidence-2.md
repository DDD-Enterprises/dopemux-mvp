---
id: 11_UNKNOWNs_AND_REQUIRED_EVIDENCE
title: 11 Unknowns And Required Evidence
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: 11 Unknowns And Required Evidence (explanation) for dopemux documentation
  and developer workflows.
---
# 11 UNKNOWNs And Required Evidence

Only UNKNOWNs that can block a no-guess Master Contract are listed.

## UNKNOWN-1: Serena runtime read/write authority and cache behavior (compose-deployed server)
- What is unknown:
- Whether active Serena writes Redis/Qdrant/Postgres/filesystem.
- Whether Serena cache changes retrieval/ranking determinism.
- Why it matters:
- Search/cognitive contract cannot assign authoritative write boundaries or determinism guarantees without this.
- What was checked:
- `compose.yml` points Serena to `docker/mcp-servers/serena`.
- Dockerfile installs external package from GitHub at build time.
- Required evidence:
- Inspect the exact installed Serena package version/source used in image.
- Commands:
- `docker compose build serena`
- `docker run --rm dopemux-mcp-serena python -c "import serena,inspect; print(serena.__file__)"`
- `docker run --rm dopemux-mcp-serena python -m pip show serena`
- `docker run --rm dopemux-mcp-serena rg -n "redis|qdrant|postgres|sqlite|cache|rank|top_k|workspace" $(python -c 'import serena,os; print(os.path.dirname(serena.__file__))') -S`

## UNKNOWN-2: Effective ConPort auth boundary in deployment (app-level vs gateway-level)
- What is unknown:
- Whether auth is enforced externally (reverse proxy/service mesh) despite no in-file auth checks in `enhanced_server.py`.
- Why it matters:
- Master Contract Policy B requires authenticated authority writes.
- What was checked:
- `docker/mcp-servers/conport/enhanced_server.py` route handlers and auth keyword grep.
- Required evidence:
- Check ingress/proxy auth middleware and runtime network policy.
- Commands:
- `rg -n "traefik|forwardauth|oauth|jwt|api[-_ ]key|Authorization" compose.yml docker/**/*.yml -S`
- `rg -n "middleware|auth|token|apikey|bearer" docker/mcp-servers/conport -S`

## UNKNOWN-3: PM->ConPort adapter endpoint compatibility in active runtime
- What is unknown:
- Task-orchestrator adapter posts to `/api/progress/log`, but ConPort runtime exposes `POST /api/progress`.
- Unknown whether another compatibility shim is active.
- Why it matters:
- PM-plane write authority reliability and idempotency assumptions may be wrong.
- What was checked:
- `services/task-orchestrator/app/adapters/conport_adapter.py` and `docker/mcp-servers/conport/enhanced_server.py` route definitions.
- Required evidence:
- End-to-end call trace in running stack.
- Commands:
- `rg -n "/api/progress/log|/api/progress" services/task-orchestrator docker/mcp-servers/conport -S`
- `docker compose up -d conport task-orchestrator`
- `curl -i http://localhost:3004/api/progress/log`
- `curl -i -X POST http://localhost:3004/api/progress -H 'Content-Type: application/json' -d '{"workspace_id":"w","description":"d"}'`

## UNKNOWN-4: Confirmed consumers of `memory.derived.v1`
- What is unknown:
- No direct in-repo consumer was proven for `memory.derived.v1`.
- Why it matters:
- Contract event obligations should not require downstream consumers that do not exist.
- What was checked:
- Eventbus consumer producer path in `services/working-memory-assistant/eventbus_consumer.py`.
- Required evidence:
- Commands:
- `rg -n "memory\.derived\.v1|DOPE_MEMORY_OUTPUT_STREAM|xreadgroup\(.*memory" services src docs -S`

## UNKNOWN-5: Canonical deployment compose for contract scope
- What is unknown:
- Multiple compose files define different topologies; canonical contract target is not explicitly declared in evidence files.
- Why it matters:
- Contract boundaries differ if `compose.yml` vs `docker-compose.unified.yml`/legacy stacks are authoritative.
- What was checked:
- Compose inventory across 15 compose files.
- Required evidence:
- Confirm policy source file in ops doc or CI deployment script.
- Commands:
- `rg -n "compose\.yml|docker-compose\.unified\.yml|docker-compose\.prod\.yml" README.md INSTALL.md QUICK_START.md .github workflows scripts -S`

## Evidence excerpts
- `docker/mcp-servers/serena/Dockerfile:11-13`
```text
# Install dependencies (including serena from git)
# Pinning to main branch for now, ideally should be a tag
RUN pip install "git+https://github.com/oraios/serena.git" mcp-proxy fastapi uvicorn
```
- `services/task-orchestrator/app/adapters/conport_adapter.py:588-589`
```text
                url = f"{self.conport_url}/api/progress/log"
                params = {"workspace_id": self.workspace_id}
```
- `docker/mcp-servers/conport/enhanced_server.py:253-254`
```text
        self.app.router.add_post('/api/progress', self.log_progress)
        self.app.router.add_get('/api/progress', self.get_progress)
```
