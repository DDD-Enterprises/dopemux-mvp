---
title: "MCP Lifecycle and Reliability"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# MCP Lifecycle and Circuit Breakers

## Purpose

How MCP servers start, fail, recover, and how the system degrades gracefully.

## Scope

TODO: Define the scope of MCP management in Dopemux.

## Non-negotiable invariants

TODO: List MCP-related invariants (e.g., "no tool access without server health").

## FACT ANCHORS (Repo-derived)

TODO: Link to the MCPServerManager and health check implementations.

## Open questions

TODO: List MCP-related unknowns and how to resolve them.

## MCPServerManager responsibilities
- startup orchestration
- health checks
- timeouts
- restart/backoff policy
- tool routing on failure

TODO: Confirm existing implementation and cite file paths.

## Startup order

### Required servers

TODO: list required.

### Optional servers

TODO: list optional.

## Health checks and timeouts
- heartbeat endpoint or tool ping
- latency thresholds
- error rate thresholds

TODO: Define default timeout values and where configured.

## Circuit breaker triggers
- server unreachable
- latency spike
- schema violations
- bad outputs

TODO: Define what constitutes “bad output” and how detected.

## Degradation and fallback behavior
- tool substitution ladder (example: Serena -> Dope-Context -> raw fallback)
- refuse if a mandate cannot be met

TODO: Define explicit mandates and refusal wording rules.

## Acceptance criteria

TODO: Provide 5 tests or simulated scenarios for MCP outages and recovery.
