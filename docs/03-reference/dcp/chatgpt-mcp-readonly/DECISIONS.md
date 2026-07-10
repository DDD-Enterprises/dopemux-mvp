---
id: dcp-mcp-readonly-decisions
title: DCP Read-Only MCP Facade — Decisions
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Accepted decisions and rejected alternatives for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Decisions

> Decisions transcribe the load-pack `decision_records`, augmented with the `OBSERVED` red-lane finding and unresolved question from [`READ_ONLY_SURFACE_INVENTORY.json`](READ_ONLY_SURFACE_INVENTORY.json).

## Accepted Decisions

### D1 — One local multi-project read-only evidence router
A single local facade routes all ChatGPT evidence reads, **instead of** giving ChatGPT direct access to each MCP server.
- *Rejected alternative:* direct ChatGPT → each backend MCP. Rejected: multiplies the attack surface, leaks ports/routes, and offers no central denylist or envelope.

### D2 — Explicit project registry; `dopemux init` is eligibility, not consent
Projects are exposed only via an explicit, operator-approved registry entry. Initialization makes a workspace *eligible*, not *exposed*.
- *Rejected alternative:* auto-expose any `dopemux init` workspace. Rejected: silent exposure violates fail-closed and least-privilege.

### D3 — Phase 1 uses Dopemux-specific evidence tools; generic search/fetch deferred
Phase 1 ships the bounded tool set in [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md). Generic search/fetch is deferred.
- *Rejected alternative:* expose generic search/fetch now. Rejected: source-label integrity and side-effect isolation aren't yet implemented.

### D4 — `dopecon-bridge` denied for Phase-1 evidence reads
Read ConPort directly; do not route decisions through the bridge proxy.
- *Evidence (`OBSERVED`):* bridge `/ddg/decisions` is `CONFIRMED_READ_ONLY` but labelled `PROXY`; *"introducing proxy layers in the tunnel increases transport confusion risks."*
- *Rejected alternative:* use the bridge as a convenience aggregator. Rejected: proxy/authority confusion.

### D5 — `search_all` denied in Phase 1 (bridge/Redis side-effect risk)
- *Evidence (`OBSERVED`):* `search_all` *"calls an external HTTP client that sends a network request to dopecon-bridge, which triggers Redis operations"* → `READ_WITH_SIDE_EFFECT_RISK`, authority `DERIVED`.
- *Rejected alternative:* allow `search_all` as the unified search. Rejected: side effects + cross-project pollution risk.

### D6 — Implementation lives under `services/dcp-readonly-facade/`
The facade is a new, isolated service package.
- *Rejected alternative:* extend an existing service (ConPort/bridge/etc.). Rejected: would blur the read-only boundary and the canonical-writer separation.

### D7 — ChatGPT names opaque exposure targets, not backend runtime details
Accepted in ADR-DCP-MCP-RO-0009. New ChatGPT exposure contracts use an opaque `target_id` that resolves through an operator-authored exposure policy registry, live runtime verification, ownership evidence adjudication, and read-only adapter allowlists. Runtime registries, catalog records, ports, leases, containers, `.mcp.json` inventory, and heuristic discovery are not exposure consent and cannot make a backend callable.
- *Rejected alternative:* keep public `project_id` / static backend binding as the remote exposure identity. Rejected: it blurs consent with backend/runtime identity and cannot safely distinguish primary checkouts, sibling worktrees, reserved singletons, and stale or wrong-project listeners.
- *Implementation note:* Existing facade docs and code may still contain earlier `project_id` terminology. `TP-DCP-MCP-RO-0009` records the accepted contract; runtime/API migration remains a separate implementation slice.

## Open Items Carried Forward

- `UNKNOWN` (inventory `unresolved_questions`): *"Should dope-memory be queried directly, or should all chronicle reads be multiplexed through a facade wrapper to normalize output for ChatGPT?"* — to be resolved in 0005.
- `OBSERVED` (inventory `red_lane_findings`): unregistered task-orchestrator PM routes (`app/api/pm_tools.py`, e.g. `/api/pm/work-items/{task_id}/update`) are defined but not included in `app/main.py` — code drift. The facade denies these by route regardless.
- `UNKNOWN`: the `dopemux init` marker contract (resolved in 0003).
