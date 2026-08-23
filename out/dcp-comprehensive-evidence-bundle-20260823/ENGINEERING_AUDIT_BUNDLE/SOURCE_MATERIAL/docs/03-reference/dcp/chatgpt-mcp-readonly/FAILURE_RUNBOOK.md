---
id: dcp-mcp-readonly-failure-runbook
title: DCP Read-Only MCP Facade — Failure-Mode Runbook
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-10'
last_review: '2026-06-10'
next_review: '2026-09-08'
prelude: Failure modes, symptoms, and fail-closed recovery for the Secure MCP Tunnel + read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Failure-Mode Runbook

> **Status.** `PROPOSED` operator runbook. Recovery steps preserve the facade's
> **fail-closed** invariants ([`SECURITY_MODEL.md`](SECURITY_MODEL.md) §8): unknown
> project, disabled project, denied route, path/symlink escape, or unreachable
> backend resolve to `PARTIAL`/`BLOCKED` — never fabricated data, never silent
> success. When a failure is ambiguous, **fail closed**: stop the tunnel rather
> than expose a degraded surface.

## Severity key

- 🔴 **Security-critical** — stop the tunnel immediately; do not expose.
- 🟡 **Degraded** — facade still safe; a tool returns `PARTIAL`/`BLOCKED`.
- 🟢 **Operational** — local setup/connectivity; no exposure risk.

## 1. 🔴 Facade bound to a non-loopback interface

- **Symptom:** bind check ([`TUNNEL_INTEGRATION.md`](TUNNEL_INTEGRATION.md) §2)
  shows `0.0.0.0:<FACADE_PORT>` or a LAN IP.
- **Cause:** transport switched to HTTP without pinning host; the scaffold passes
  no host/port (`server.py:102-104`), so the runtime default applied.
- **Recovery:** stop the facade and tunnel. Set the loopback host env
  (`FASTMCP_HOST=127.0.0.1` — verify the name for your runtime), restart, re-run
  the bind check, and only then start the tunnel. Treat any prior exposure window
  as an incident.

## 2. 🔴 Tunnel ingress points at a backend service

- **Symptom:** tunnel config `ingress` lists a backend port (`:3004`, `:3020`,
  `:3010`, `:8000`, `:3016`) instead of the facade endpoint.
- **Cause:** misconfigured `service:` target.
- **Recovery:** rewrite ingress so the only `service:` is
  `http://127.0.0.1:<FACADE_PORT>`, with a catch-all `http_status:404`
  ([`TUNNEL_INTEGRATION.md`](TUNNEL_INTEGRATION.md) §3). Backends are never tunnel
  targets — direct backend exposure bypasses the read-only denylist entirely.

## 3. 🔴 A write/mutating tool is reachable from the connector

- **Symptom:** the connector lists or can call a transition / `manage_*` /
  `memory_correct` / `index_*` / `sync_*` tool, or §5.1 of
  [`MANUAL_VALIDATION.md`](MANUAL_VALIDATION.md) fails.
- **Cause:** a backend MCP server was tunneled directly, or the wrong endpoint was
  connected — **not** the facade.
- **Recovery:** disconnect the connector immediately. Confirm the connector URL
  resolves to the facade endpoint only. The facade exposes read tools only and
  denies mutating/proxy/side-effect routes structurally
  ([`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §2); if a write tool is visible, you are
  not talking to the facade.

## 4. 🟡 `search_progress` returns `BLOCKED`

- **Symptom:** every `search_progress` call is `BLOCKED`.
- **Cause:** **intended** fail-closed default. ConPort's default enhanced server
  auto-forks (writes) progress rows when a workspace has none
  (`DOPEMUX_AUTO_FORK_PROGRESS=1`), so the read can mutate
  ([`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §1b note †).
- **Recovery:** leave blocked unless you have set `DOPEMUX_AUTO_FORK_PROGRESS=0` on
  that ConPort backend **first**, then set
  `service_profiles.conport.progress_readonly_safe: true` in the registry. Do not
  enable the flag without the backend change — that re-introduces write-on-read.

## 5. 🟡 `search_decisions(query=…)` returns `PARTIAL`

- **Symptom:** query mode returns `PARTIAL` with a deferral note; list mode works.
- **Cause:** **intended.** ConPort `GET /api/search/{ws}` returns HTTP 500 on the
  default backend (UUID not serialized) ([`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §1b
  note ‡). The facade refuses to surface a broken read.
- **Recovery:** use list mode (`GET /api/decisions`) until the backend serializes
  ids. No facade change needed.

## 6. 🟡 dope-context tools (`search_code_docs`, `get_index_status`) return `BLOCKED`

- **Symptom:** these always `BLOCKED`.
- **Cause:** **intended** Phase-1 posture. dope-context exposes MCP JSON-RPC at
  `/mcp`; the facade's `ReadOnlyHttpClient` speaks REST only — no transport bridge
  yet ([`ARCHITECTURE.md`](ARCHITECTURE.md) §20, [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §1c).
- **Recovery:** none for Phase 1; the fail-closed `BLOCKED` is correct. Transport
  bridge + formal inventory are Phase-2 work.

## 7. 🟡 Backend unreachable / timeout

- **Symptom:** a service-backed tool returns `PARTIAL`/`BLOCKED` with a backend
  error reason.
- **Cause:** backend not running, wrong `base_url`, or non-2xx response (only 2xx
  bodies are parsed; `SECURITY_MODEL.md` + `FACADE_LOCAL_RUN.md` §5).
- **Recovery:** confirm the backend is up on its loopback port; the facade fails
  closed and must **not** be "fixed" by relaxing validation. Loopback-only
  `base_url` is enforced (SSRF guard) — a non-loopback `base_url` is rejected by
  design.

## 8. 🔴 Secret scan finds a real credential

- **Symptom:** the scan flags a value that is **not** an env-var name or placeholder.

  ```bash
  rg -n "CONTROL_PLANE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN: [REDACTED]" \
    docs/03-reference/dcp/chatgpt-mcp-readonly services/dcp-readonly-facade
  ```

- **Cause:** a registry, tunnel config, or credentials file was committed, or a
  real value was pasted into docs.
- **Recovery:** **stop.** Do not commit. Remove the value, rotate the credential
  out of band, and keep registry/tunnel/credential files outside the repo
  ([`FACADE_LOCAL_RUN.md`](FACADE_LOCAL_RUN.md) §1). Hits that are clearly env-var
  **names** or `<PLACEHOLDER>` tokens are documentation references, not secrets —
  but verify each before proceeding.

## 9. 🟢 Tunnel client won't connect

- **Symptom:** connector cannot reach the facade; tunnel client errors.
- **Cause:** facade not started, transport still `stdio` (no network endpoint),
  wrong port, or tunnel credentials/token missing.
- **Recovery:** confirm `DCP_FACADE_TRANSPORT` is an HTTP-class transport and the
  facade is listening on `127.0.0.1:<FACADE_PORT>`; confirm the tunnel token is
  supplied out of band; re-run [`MANUAL_VALIDATION.md`](MANUAL_VALIDATION.md) §0.

## 10. Escalation

If a failure cannot be made to fail closed — e.g. official tunnel behavior
contradicts this runbook, the tunnel requires root, or it requires storing
credentials unencrypted in the repo — **stop and reconcile** (these are STOP-IF
conditions for TP-DCP-MCP-RO-0007). Do not work around a security invariant to
restore connectivity.
