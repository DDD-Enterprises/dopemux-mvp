---
id: 002-mcp-service-discovery
title: 002 Mcp Service Discovery
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 002 Mcp Service Discovery (explanation) for dopemux documentation and developer
  workflows.
---
# ADR-002: Configuration Drift Detection & Service Discovery

## Context
A common infrastructure problem was identified where client configs lag behind deployment refactors (e.g., local → Docker, stdio → HTTP).
Signals of this drift included:
1. Symptom mismatch: Servers "healthy" in Docker, but clients can't connect.
1. Protocol misalignment: Config expects stdio/files, servers provide HTTP.
1. Commit gap: Infrastructure changes without corresponding config commits.

## Decision
We favored **HTTP/SSE over stdio** for containerized MCP servers.
**Benefits:**
- Health checks work via standard tools (`curl /health`).
- Network debugging tools apply (tcpdump, logs).
- Port isolation prevents conflicts.
- Removes need for complex wrapper scripts.

## Strategic Evolution: Service Discovery
To prevent manual sync and drift, the next evolution of the platform will implement **Service Discovery**:
1. Servers advertise connection details via an `/info` endpoint.
1. A script consumes these endpoints to generate `.claude.json` automatically.

## Status
- **Lesson Learned**: Feb 2026
- **Implementation**: Scheduled for Infrastructure Hardening phase.
