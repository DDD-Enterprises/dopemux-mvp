---
id: dcp-mcp-readonly-security-model
title: DCP Read-Only MCP Facade — Security Model
type: reference
owner: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Security model — tunnel posture, redaction, prompt-injection, stale-proof, and side-effect controls for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Security Model

> **Status.** Controls are `PROPOSED` design constraints, grounded in `OBSERVED` per-surface `security_notes` from [`READ_ONLY_SURFACE_INVENTORY.json`](READ_ONLY_SURFACE_INVENTORY.json) and the load-pack global invariants. The threat model assumes ChatGPT (and any content it relays) is **untrusted**.

## 1. Transport / Tunnel Posture

- The facade binds **loopback only**. No public ingress.
- A Secure MCP Tunnel client connects ChatGPT to the facade endpoint **only** — never to a backend service (ConPort, dope-memory, dope-context, task-orchestrator, dopecon-bridge).
- ChatGPT developer mode can expose read **and write** MCP tools; therefore the facade's own denylist is the mandatory control, not the tunnel's trust. (Detailed setup + warnings in TP-DCP-MCP-RO-0007.)

## 2. Input Constraints (no arbitrary control)

The facade accepts **no** caller-supplied filesystem path, URL, port, backend route, `workspace_id`, SQL, or shell command. Callers supply only a `project_id` and tool-specific, typed/validated parameters. `OBSERVED` security notes that drive this:

- ConPort search: *"Ensure workspace parameter is strictly sanitized to prevent query injection."* → workspace binding is registry-owned, never caller-set.
- dope-context `search_code`: *"Ensure search query does not trigger file path traversal attacks."* → query is treated as opaque; no path semantics.

## 3. Read-Only / Side-Effect Controls

- Only routes classified `CONFIRMED_READ_ONLY` are reachable. All `MUTATING` routes are denied (ConPort `POST /api/decisions`, dope-memory `POST /tools/memory_correct`, task-orchestrator `POST .../transition`).
- `search_all` is denied: `OBSERVED` — it *"calls an external HTTP client that sends a network request to dopecon-bridge, which triggers Redis operations."* Read-with-side-effect-risk is treated as not-read-only for Phase 1.
- POST is permitted **only** for the explicitly classified side-effect-free dope-memory reads (`memory_search`, `memory_replay_session`) — method alone does not grant access.
- task-orchestrator `pm_tools` routes are denied **by route**, not by relying on the `OBSERVED` red-lane finding that they are currently unregistered in `app/main.py` (code drift could re-register them).

## 4. Redaction

Before any payload leaves the facade:
- Absolute filesystem paths redacted by default (`redactions: ["absolute_paths"]`).
- Secret/token patterns (API keys, bearer tokens, passwords) stripped.
- ConPort `custom_data` is redaction-sensitive: `OBSERVED` — *"Custom data may contain unstructured metadata; ensure sensitive items are redacted."* (and is deferred from Phase-1 exposure regardless).
- No secrets are ever committed to the repo (docs use placeholders only).

## 5. Prompt-Injection Controls

All content retrieved from any backend is **untrusted** and is wrapped/marked as untrusted in the envelope `data` before returning to ChatGPT. Retrieved text must not be interpreted by the facade as instructions. Hardening tests for injection wrapping are required in TP-DCP-MCP-RO-0008.

## 6. Authority / Proxy Confusion

- dopecon-bridge `/ddg/decisions` is denied even though read-only: `OBSERVED` authority label `PROXY` — *"Introducing proxy layers in the tunnel increases transport confusion risks."* The facade reads ConPort directly to preserve the canonical-writer boundary.
- The facade is never presented as an authority; every envelope labels its `source_system` and `authority_label` so ChatGPT cannot mistake a `DERIVED`/`PROXY` result for canonical truth.

## 7. Freshness / Stale-Proof and Dirty-State Detection

- Every envelope carries `freshness` and (where available) `branch`/`head_sha`/`dirty`.
- A stale proof bundle (head_sha mismatch) emits a `warning`; a dirty worktree emits a `warning`. These are surfaced, not hidden. Stale-proof and dirty-state warnings are regression-tested in 0004/0008.

## 8. Fail-Closed Behavior

Unknown project, disabled project, denied route, path/symlink escape, or unavailable backend all resolve to `PARTIAL`/`BLOCKED` with explicit `blocked_reasons` — never to fabricated data and never to a silent success. Least privilege and operator visibility are preserved throughout.
