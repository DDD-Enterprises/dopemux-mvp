---
id: dcp-mcp-readonly-tunnel-integration
title: DCP Read-Only MCP Facade — Secure MCP Tunnel Integration
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-10'
last_review: '2026-06-10'
next_review: '2026-09-08'
prelude: Local Secure MCP Tunnel integration, redacted client config, loopback-only runtime posture, and ChatGPT connector wiring for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Secure MCP Tunnel Integration

> **Status.** This guide is `PROPOSED` operator procedure. The facade runtime
> facts it relies on are `OBSERVED` from `services/dcp-readonly-facade/src/mcp/server.py`
> and [`FACADE_LOCAL_RUN.md`](FACADE_LOCAL_RUN.md); the security constraints are
> `OBSERVED`/`PROPOSED` from [`SECURITY_MODEL.md`](SECURITY_MODEL.md). Tunnel-client
> and ChatGPT-connector specifics change with vendor releases — every vendor-specific
> example below is a **placeholder** and **must be verified against the current
> official tunnel and ChatGPT connector documentation** before use. If official
> tunnel behavior contradicts anything here, **stop and reconcile the docs** (this is
> a STOP-IF condition for TP-DCP-MCP-RO-0007). **No real tunnel IDs, hostnames,
> tokens, or credentials are committed to this repository.**

## 1. What the tunnel is (and is not)

A *Secure MCP Tunnel* is the transport that lets a remote ChatGPT connector reach
the facade's **loopback-only** MCP endpoint. It exists only to forward MCP traffic
to the facade and nothing else.

- The tunnel client connects to the **facade endpoint only** — never to a backend
  service (ConPort `:3004`, dope-memory `:3020`, dope-context `:3010`,
  task-orchestrator `:8000`, dopecon-bridge `:3016`).
- The tunnel does **not** provide the security boundary. ChatGPT developer mode
  can expose read **and write** MCP tools, and a tunnel forwards whatever the
  endpoint serves. The mandatory control is the **facade's own read-only surface +
  route denylist** ([`TOOL_CONTRACT.md`](TOOL_CONTRACT.md),
  [`SECURITY_MODEL.md`](SECURITY_MODEL.md) §3), not tunnel trust.
- The facade holds **no write authority**; it is an evidence projection layer
  ([`ARCHITECTURE.md`](ARCHITECTURE.md) §1).

### Topology

```
ChatGPT (untrusted client)
   → Secure MCP Tunnel (public edge → encrypted tunnel)
      → tunnel-client (on the operator host)
         → 127.0.0.1:<FACADE_PORT>   ← facade endpoint ONLY
            → DCP Read-Only Facade (loopback bind, read-only tools)
               → backend adapters (route/method allowlist)

NEVER:  tunnel-client → 127.0.0.1:3004 / :3020 / :3010 / :8000 / :3016
        (backend services are not tunnel targets)
```

## 2. Runtime posture — loopback binding is operator-enforced

`OBSERVED` (`server.py:102-104`): the facade reads `DCP_FACADE_TRANSPORT`
(default `stdio`) and calls `mcp.run(transport=transport)`. **The scaffold does
not pin a host or port.** Loopback binding is therefore the **operator's
responsibility** (`SECURITY_MODEL.md` §1: *"Loopback-only binding is the
operator's responsibility … this scaffold defaults to stdio transport"*).

A tunnel needs a network endpoint, so the operator switches the facade to an
HTTP-class transport. Because the scaffold passes no host/port, you **must**
constrain the bind to loopback explicitly and **verify** it before exposing a
tunnel:

```bash
cd services/dcp-readonly-facade

# Switch to an HTTP-class transport for tunneling (verify the exact transport
# name your installed MCP/FastMCP version accepts — e.g. streamable-http or sse).
export DCP_FACADE_TRANSPORT="streamable-http"   # PLACEHOLDER — verify against your runtime

# Constrain the listener to loopback. The scaffold does not set these; the
# operator MUST. (Names are runtime-version dependent — verify.)
export FASTMCP_HOST="127.0.0.1"                 # PLACEHOLDER — verify env name
export FASTMCP_PORT="<FACADE_PORT>"             # e.g. a high local port

export DCP_FACADE_REGISTRY=~/.dopemux/dcp-facade-registry.yaml
python -m src.mcp.server
```

> **`UNKNOWN`/verify:** the exact transport string and the host/port env-var names
> depend on the installed `fastmcp` version. Do not assume a default of
> `127.0.0.1`. If your runtime defaults to `0.0.0.0`, an unconstrained switch
> publishes the facade on all interfaces — a public-exposure regression. Confirm
> the bind with the verification step below **before** starting any tunnel.

### Verify the bind is loopback (mandatory gate)

```bash
# Expect ONLY 127.0.0.1:<FACADE_PORT> (or ::1). Any 0.0.0.0 / LAN IP = STOP.
lsof -nP -iTCP -sTCP:LISTEN | grep "<FACADE_PORT>"
# or:
#   ss -ltnp | grep "<FACADE_PORT>"      (Linux)
#   netstat -an -p tcp | grep "<FACADE_PORT>"
```

If the listener is on anything other than loopback, **do not start the tunnel** —
fix the bind first. (`FORBIDDEN`: no public ingress; STOP-IF on backend/public
exposure per the packet invariants.)

## 3. Tunnel-client config (redacted examples)

The tunnel client's ingress must route a single hostname to the **facade loopback
endpoint only**. The repository already uses a cloudflared tunnel for the
extraction webhook (`ops/cloudflared/config.yml`); use that as the *pattern*, with
its own credentials, kept **outside** this repo.

### Generic ingress (placeholder)

```yaml
# Store OUTSIDE the repo (e.g. ~/.dopemux/dcp-tunnel.example.yaml).
# Every value here is a PLACEHOLDER. NEVER commit a populated tunnel config.
tunnel: "<TUNNEL_ID>"                        # opaque tunnel id — NOT committed
credentials-file: "~/.dopemux/<TUNNEL_ID>.json"   # secret material — NOT committed

ingress:
  # The ONLY backend target is the facade loopback endpoint.
  - hostname: "<your-facade-host.example.com>"
    service: "http://127.0.0.1:<FACADE_PORT>"
  # Catch-all: refuse everything else (no backend services exposed).
  - service: "http_status:404"
```

### Auth token (when the tunnel client takes one)

Provide any tunnel auth token **out of band** — environment or secret store, never
a repo file:

```bash
# Exported from your secret store at runtime; the value is NEVER written to the repo.
export TUNNEL_TOKEN   # value injected out-of-band; do not assign it in a committed file
```

> Do **not** add backend service ports to `ingress`. The catch-all `404` rule is
> the fail-closed default: a misconfigured hostname returns 404 rather than
> falling through to a service.

## 4. ChatGPT connector wiring

`PROPOSED` — verify against the current ChatGPT connector / developer-mode docs;
the UI and capability model change over time.

1. In ChatGPT, add a **remote MCP server / custom connector** pointing at the
   tunnel's public URL (`https://<your-facade-host.example.com>`), **not** at any
   backend.
2. The connector will discover the facade's tools (`list_projects`,
   `get_repo_state_snapshot`, `list_proof_bundles`, `fetch_proof_bundle`,
   `search_decisions`, `search_progress`, `search_chronicle`,
   `replay_chronicle_session`; service-backed dope-context tools are Phase-1
   **BLOCKED** per [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §1c).
3. **Developer-mode warning.** ChatGPT developer mode can call read **and write**
   MCP tools on a connector. The facade is the boundary: it exposes only read
   tools and structurally denies every mutating/proxy/side-effect route
   ([`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §2, [`SECURITY_MODEL.md`](SECURITY_MODEL.md) §3).
   Never tunnel a backend MCP server directly to a connector — its write tools
   would be reachable.
4. Validate the connector against [`MANUAL_VALIDATION.md`](MANUAL_VALIDATION.md)
   before treating it as trusted.

## 5. Secrets posture

- The registry (`~/.dopemux/dcp-facade-registry.yaml`), the tunnel config, and the
  tunnel credentials file all live **outside** the repo. None is ever committed
  (`FACADE_LOCAL_RUN.md` §1; packet invariant *"No secrets committed"*).
- Docs use placeholders only (`<TUNNEL_ID>`, `<FACADE_PORT>`,
  `<your-facade-host.example.com>`).
- Backend service credentials (e.g. a ConPort/control-plane API key) are never
  surfaced to the facade caller and never written to docs. Any literal env-var
  **name** appearing in this guide is a reference, not a value.

## 6. Related

- [`FACADE_LOCAL_RUN.md`](FACADE_LOCAL_RUN.md) — registry config, local run, tests.
- [`MANUAL_VALIDATION.md`](MANUAL_VALIDATION.md) — connector validation checklist.
- [`FAILURE_RUNBOOK.md`](FAILURE_RUNBOOK.md) — failure modes and recovery.
- [`SECURITY_MODEL.md`](SECURITY_MODEL.md), [`ARCHITECTURE.md`](ARCHITECTURE.md),
  [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) — boundary, topology, tool surface.
