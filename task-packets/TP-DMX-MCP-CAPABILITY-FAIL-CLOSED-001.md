---
id: TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001
title: Tp Dmx Mcp Capability Fail Closed 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Tp Dmx Mcp Capability Fail Closed 001 (explanation) for dopemux documentation
  and developer workflows.
---
# TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001

## MCP Resolver Provenance and Mandatory Capability Gate Repair

Repairs `DMX-W1-04-F018` and `DMX-W1-04-F019`:

- **F018**: an environment endpoint override could silently replace a repo-profile
  service's `provenance` with `env_var`, downgrading its mandatory classification
  in the downstream discovery gate.
- **F019**: when discovery reported `"transport active, handshake required"`, the
  gate suppressed required-tool-glob validation entirely, letting a mandatory
  service with zero proven matching tools reach `PASS`.

Target invariant: an endpoint override may change *where* Dopemux connects, but
not *who declared the service authoritative*, and transport reachability is
never proof of required MCP capability.

Full packet specification, risk classification (L3), authority model, and
execution stages: see the task-packet handoff that authorized this
implementation (`TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001`, campaign
`DMX-REPO-DEEP-AUDIT-001`).

Machine-readable companion: `task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.json`.

Proof bundle: `proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/`.
