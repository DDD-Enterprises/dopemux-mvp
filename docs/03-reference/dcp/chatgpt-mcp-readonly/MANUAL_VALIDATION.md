---
id: dcp-mcp-readonly-manual-validation
title: DCP Read-Only MCP Facade — Manual Validation Checklist
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-10'
last_review: '2026-06-10'
next_review: '2026-09-08'
prelude: Manual validation checklist (MCP inspector + ChatGPT connector) covering exposure, read tools, fail-closed denials, and freshness warnings for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Manual Validation Checklist

> **Status.** `PROPOSED` operator procedure. Expected behaviors are `OBSERVED` from
> the facade tools ([`FACADE_LOCAL_RUN.md`](FACADE_LOCAL_RUN.md),
> [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md)) and the fail-closed model
> ([`SECURITY_MODEL.md`](SECURITY_MODEL.md)). This checklist is **manual** — no
> tunnel client and no connector automation runs in CI (packet invariant: *"No
> running tunnel-client in CI", "No connector creation automation"*). Run it after
> any tunnel or connector change.

## 0. Preconditions

- Registry configured with at least one `enabled` project
  ([`FACADE_LOCAL_RUN.md`](FACADE_LOCAL_RUN.md) §1); `DCP_FACADE_REGISTRY` set.
- Facade bind **verified loopback** ([`TUNNEL_INTEGRATION.md`](TUNNEL_INTEGRATION.md) §2).
- The automated suite is green first (this is the structural baseline; the manual
  steps below add live + connector coverage):

  ```bash
  python -m pytest -q services/dcp-readonly-facade/tests
  ```

You can drive the tools two ways:

- **MCP inspector** — point an MCP inspector/dev client at the facade endpoint
  (stdio locally, or the loopback HTTP endpoint when transport is switched). Verify
  against your inspector's current docs; tool names below are the contract surface.
- **ChatGPT connector** — once the tunnel + connector are wired
  ([`TUNNEL_INTEGRATION.md`](TUNNEL_INTEGRATION.md) §4), issue the same calls from
  ChatGPT.

Each call returns the canonical envelope (`project_id`, `branch`, `head_sha`,
`dirty`, `source_system`, `authority_label`, `freshness`, `limitations`,
`warnings`, `redactions`, `blocked_reasons`, `data`) — see
[`RESPONSE_ENVELOPE_SCHEMA.md`](RESPONSE_ENVELOPE_SCHEMA.md). Confirm the envelope
shape on every result.

## 1. Exposure — `list_projects`

| # | Action | Expected | Pass |
| --- | --- | --- | --- |
| 1.1 | Call `list_projects` (no args) | Returns **only** `enabled: true` registry projects; disabled/unlisted projects absent | ☐ |
| 1.2 | Disable a project in the registry, restart facade, call again | The project disappears from the list (exposure = registry entry + `enabled`, not eligibility) | ☐ |
| 1.3 | Inspect a returned entry | No absolute host paths leak; capabilities reflect configured backends | ☐ |

## 2. Repo evidence — `get_repo_state_snapshot`

| # | Action | Expected | Pass |
| --- | --- | --- | --- |
| 2.1 | Call `get_repo_state_snapshot` with a valid `project_id` | Envelope carries `branch`, `head_sha`, `dirty` from a read-only git snapshot | ☐ |
| 2.2 | Make the worktree dirty (touch a file), call again | `dirty: true` and a dirty-state `warning` is present (surfaced, not hidden) | ☐ |
| 2.3 | Call with an **unknown** `project_id` | `BLOCKED` envelope with explicit `blocked_reasons`; no git data | ☐ |

## 3. Proof bundles — `list_proof_bundles` / `fetch_proof_bundle`

| # | Action | Expected | Pass |
| --- | --- | --- | --- |
| 3.1 | `list_proof_bundles(project_id)` | Bundle ids under `<workspace>/proof/`, capped at 20 | ☐ |
| 3.2 | `list_proof_bundles(project_id, packet_id_filter="TP-DCP-MCP-RO-0007")` | Literal-substring match only (no regex semantics) | ☐ |
| 3.3 | `fetch_proof_bundle(project_id, bundle_id)` for a real bundle | Returns bundle files; absolute paths redacted | ☐ |
| 3.4 | `fetch_proof_bundle` with `../`, a symlink, or a cross-project id | `BLOCKED` (containment + symlink-escape prevention) | ☐ |

## 4. Stale-proof + freshness warnings

| # | Action | Expected | Pass |
| --- | --- | --- | --- |
| 4.1 | Fetch a proof bundle whose recorded `head_sha` ≠ current `head_sha` | Result includes a **stale-proof `warning`** (head_sha mismatch); data still returned, flagged not hidden | ☐ |
| 4.2 | Fetch any bundle on a dirty worktree | A dirty-state `warning` accompanies the result | ☐ |
| 4.3 | Confirm `freshness` is populated on every envelope | Present on success, partial, and blocked results | ☐ |

## 5. Denied / fail-closed routes (the security gate)

These confirm the mandatory denylist — the control that does **not** depend on the
tunnel ([`SECURITY_MODEL.md`](SECURITY_MODEL.md) §3, [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) §2).

| # | Action | Expected | Pass |
| --- | --- | --- | --- |
| 5.1 | Confirm no write/transition tool is offered to the connector | Tool list contains read tools only; no `transition`, `manage_*`, `advance_item`, `claim_item`, `memory_correct`, `index_*`, `sync_*` | ☐ |
| 5.2 | `search_progress` without `progress_readonly_safe: true` | `BLOCKED` (auto-fork write hazard — fail-closed by default) | ☐ |
| 5.3 | `search_decisions(project_id, query="…")` (query mode) | `PARTIAL` with deferral note (ConPort `/api/search` 500s); list mode unaffected | ☐ |
| 5.4 | `search_code_docs` / `get_index_status` (dope-context) | `BLOCKED` — MCP JSON-RPC transport not bridged in Phase 1 (fail-closed, not fabricated) | ☐ |
| 5.5 | Any attempt to pass a raw path / URL / port / route / SQL / shell | Rejected — no tool accepts such input; only `project_id` + typed params | ☐ |
| 5.6 | Confirm `search_all` and `dopecon-bridge` are unreachable | Not in the tool surface (side-effect / proxy denials) | ☐ |

## 6. Authority + redaction spot-check

| # | Action | Expected | Pass |
| --- | --- | --- | --- |
| 6.1 | Inspect `authority_label` on ConPort / task-orchestrator results | `CANONICAL`; facade never labels itself an authority | ☐ |
| 6.2 | Inspect any result containing a path or token-like string | Absolute paths and secret patterns redacted before leaving the facade | ☐ |
| 6.3 | Confirm task-orchestrator results carry the **workflow-view-only** limitation | Present on every task-orchestrator envelope | ☐ |

## 7. Sign-off

- [ ] Sections 1–6 pass.
- [ ] Bind verified loopback; no backend port reachable through the tunnel.
- [ ] No secrets in any committed file (run the scan in
  [`FAILURE_RUNBOOK.md`](FAILURE_RUNBOOK.md) §6).
- Record date, operator, facade `head_sha`, and any deviations in the run notes.

> Any `FAIL` on §5 is a **blocking** result — do not expose the connector. Route
> recovery through [`FAILURE_RUNBOOK.md`](FAILURE_RUNBOOK.md).
