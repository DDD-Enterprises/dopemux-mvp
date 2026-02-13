---
title: "MCP Lifecycle and Reliability"
plane: "pm"
component: "dopemux"
status: "proposed"
---

# MCP Lifecycle and Circuit Breakers

## Purpose
How MCP servers start, fail, recover, and how the system degrades gracefully. This document defines the resilience layer for tool integration.

## Scope
- Startup/Shutdown orchestration of MCP servers.
- Health monitoring and heartbeats.
- Automatic restart policies.
- Fallback routing when tools fail.

## Non-negotiable invariants
1. **No Zombie Processes**: When Dopemux exits, ALL child MCP servers must be terminated.
2. **Fail-Safe**: If a required MCP server is down, operations dependent on it MUST fail explicitly, not hang or return garbage.
3. **Circuit Breaking**: A failing server MUST be isolated after N failures to prevent system-wide latency.

## FACT ANCHORS (Repo-derived)
- **OBSERVED: Server Manager**: `src/dopemux/mcp/manager.py` (referenced in ADRs, to be verified).
- **OBSERVED: Config**: `config/mcp_servers.yaml`.
- **OBSERVED: Active MCP Servers** (from `compose.yml`):
  - `conport` (3004): Knowledge Graph / Context Management.
  - `pal` (3003): Multi-model reasoning (Zen).
  - `serena` (3006): ADHD Engine interface / Intelligence.
  - `gptr-mcp` (3009): Deep Research / Tavily.
  - `dope-context` (3010): Semantic Search (Voyage/Qdrant).
  - `desktop-commander` (3012): Desktop Automation (X11/Display).
  - `leantime-bridge` (3015): Project Management Integration.
  - `litellm` (4000): Model Proxy/Router.
- **OBSERVED: Task-Orchestrator Tools**: "37 specialized tools" mentioned in `ADR-203`, located in `services/task-orchestrator/tools/`.
- **OBSERVED: ML Risk**: `services/ml-risk-assessment/` (Extracted from Orchestrator).

## Open questions
- **Dynamic Discovery**: Can we auto-discover new MCP servers?
  - *Resolution*: No. Usage must be explicit in `mcp_servers.yaml` for security and determinism.

## MCPServerManager responsibilities
- **Startup**: Launch servers in dependency order.
- **Health**: Periodically ping servers (JSON-RPC `ping` or equivalent).
- **Routing**: Maintain a map of `Tool Name -> Server ID`.
- **Recovery**: Attempt restarts with exponential backoff.

## Startup order
1. **Core**: `dopemux-conport` (Memory/State) - **BLOCKING**. System cannot start without this.
2. **Context**: `dopemux-context` (RAG/Knowledge) - **REQUIRED**.
3. **Tools**: `dopemux-serena` (Web), `dopemux-zen` (Browser), etc. - **ASYNC**. Can start in background.

## Circuit breaker triggers
- **Unreachable**: Connection refused > 3 times.
- **Latency**: P95 response time > 5000ms over 1 minute.
- **Error Rate**: > 20% JSON-RPC errors.
- **Broken Pipe**: Process crash.

**Action**: state transitions to `UNHEALTHY`. Supervisor stops routing requests to this server.

## Degradation and fallback behavior
If a server is `UNHEALTHY` or `STOPPED`:

1. **Tool Substitution**:
   - IF `dopemux-serena` (Web Search) is down AND `dopemux-zen` (Browser) is up: Use `zen` for search.
   - IF `dopemux-context` (Vector DB) is down: Fall back to `grep`/`ripgrep` (dumb keyword search).

2. **Refusal**:
   - If a **Mandate** requires a specific tool (e.g., "Must save to ConPort") and that server is down: **STOP** and Refuse. "Cannot execute: ConPort is unavailable and required for this task."

## Acceptance criteria
1. **Kill Test**: Kill an MCP server process manually. Ensure Dopemux detects it within 10s and marks it unhealthy.
2. **Restart Test**: Ensure Dopemux attempts to restart the killed server.
3. **Fallback Test**: Disable `dopemux-context`. Ask a question. Ensure it answers using fallback search (or refuses if strict).
