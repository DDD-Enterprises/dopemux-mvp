# Legacy/wrong MCP launch paths — removal worklist (from sweep 2026-07-28)

Canonical path: `dopemux mcp` CLI (src/dopemux/mcp/lifecycle.py + commands/mcp_commands.py) →
compose_up_command() against root compose.yml (catalog-scoped, --no-deps, per-worktree override);
task-orchestrator via scripts/mcp-wrappers/task-orchestrator-http-singleton.sh ONLY.

## Root-cause name collision
- compose.yml `task-orchestrator:` block (~430-462): FastAPI service on :8000, container_name task-orchestrator,
  services/task-orchestrator/Dockerfile. DIFFERENT SYSTEM from canonical ghcr.io/jpicklyk jar on 7890.
  Documented at docs/02-how-to/manage-mcp-servers.md:230. Action: rename service+container to
  `task-orchestrator-fastapi-legacy` (or remove if operator approves retirement). Every legacy script that
  `compose up task-orchestrator` starts this wrong one.

## DELETE (legacy-duplicate start scripts)
1. scripts/start-all-mcp-servers.sh — per-service compose up loop incl. wrong TO
2. docker/mcp-servers/start-all-mcp-servers.sh — staler copy; auto-starts quarantined exa/desktop-commander;
   assumes compose file in a dir that has none
3. scripts/manage-mcp-servers.sh — wraps docker-compose in docker/mcp-servers (no compose file there)
4. scripts/mcp/manage-mcp-servers.sh — near-identical dup of #3
5. scripts/install-docker-mcp-servers.sh — generates its own third docker-compose.yml
6. scripts/deploy/deployment/start-all.sh — three compose contexts + nohup python daemons
7. scripts/deploy/deployment/start-mcp-servers.sh — reimplements catalog startup, wrong TO
8. scripts/deploy/deployment/stack_up_all.sh — references docker/docker-compose.event-bus.yml,
   docker/memory-stack/, docker/conport-kg compose, docker/leantime compose — ALL DEAD paths
9. scripts/memory/start-memory-stack.sh — dead (docker/memory-stack missing; Milvus/Zep era)
10. scripts/setup.sh — unscoped `compose up -d` of EVERYTHING (competing installer vs install.sh)

Replacement policy: delete outright OR one-line deprecation shim `exec dopemux mcp up "$@"` (decide in design).

## LEGACY compose files
- compose/legacy/conport-kg-docker-compose.yml (hardcoded ports, duplicate postgres-age)
- compose/legacy/leantime-overlay-docker-compose.yml (hardcoded 3015)
- proof/TP-DOPMUX-AUTO-MCP-PROVISION-0001/INSTANCE_OVERLAY_A/mcp.compose.override.yml (all hardcoded — proof
  artifact, leave but ensure never referenced)
- docker/mcp-servers-source/** vendored compose files (pal zen docker-compose.yml etc.) — keep Dockerfiles used
  for builds, strip executable compose/start scripts (start-all-mcp-servers.sh, start-profile.sh,
  setup-task-orchestrator.sh which sed-patches the OLD python TO)

## KEEP (canonical)
- install.sh (bootstrap-only; scoped)
- scripts/mcp-wrappers/task-orchestrator-http-singleton.sh (canonical)
- scripts/mcp-wrappers/task-orchestrator-current-stdio.sh (fallback, singleton-guarded)
- scripts/mcp-wrappers/task-orchestrator-rollback-stdio.sh (intentional rollback tool)
- mcp_server_health_report.sh (read-only diagnostic)

## AMBIGUOUS — needs decision/design treatment
- scripts/ensure_pal_stdio.sh — bypasses CLI; likely referenced by configs
- scripts/mcp-wrappers/ensure-pal.sh — off-compose pal-mcp-server for Codex docker-exec; load-bearing but
  unmanaged; design should bring under `dopemux mcp` management
- PAL 3-way divergence: ~/plugins/dopemux-mission-control/.mcp.json pal → `docker exec mcp-pal`;
  ~/.codex/config.toml pal → `docker exec pal-mcp-server`; compose has pal + pal-stdio (zero consumers,
  feature-register says retire pal-http)
- ~/plugins/dopemux-mission-control/ — repo-untracked third maintenance point; contains
  task-orchestrator-current-stdio.sh (now byte-identical to repo) + .pre-singleton-fix.bak + .bak-20260619
  (the leak-era launcher). Action: delete .baks, formalize dir as generated artifact synced from repo.
- src/dopemux/mcp/server_manager.py + broker.py — in-process stdio spawner (second code-level launch path);
  verify broker.py wiring, quarantine or fold into lifecycle
- qa/scenarios/*.sh — compose-direct test harness (intentional; exempt but document)
- .claude/hooks/mcp_health_probe.py `_SERVER_REMEDIATION` fallback string suggests raw `docker compose up -d` —
  change to `dopemux mcp up`
- ~/Library/LaunchAgents/com.dopemux.mcp-structured-content-proxy.plist — keepalive proxy 7891→7890, outside
  CLI; document or manage

## Doc fixes
- INSTALL.md:1157-1160 — remove `./scripts/start-all-mcp-servers.sh` alternative; only `dopemux mcp up --all`
- INSTALL.md:91 — extend deprecation note to cover compose/legacy/ + docker/mcp-servers-source compose files
- docs/02-how-to/mcp-integration-guide.md:193-198 — stale catch-22 workaround (fix landed #1052, 2026-07-16)
- .vibe/config.toml:131-133 — task-orchestrator entry points at :8000 shadow twin; repoint to 7890/canonical
- README/QUICK_START/AGENTS.md/GEMINI.md/.claude/** — verified clean of legacy start instructions (no changes
  needed beyond design-driven updates)
