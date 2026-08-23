# Embedded Audit Report

- Packet: `TP-DMX-MCP-DOCTOR-FORMULA-RESERVED-001` PR 1256
- Audited content head: `f40fe398a3502b103ae7cab16b4f015b66d26a4f`
- Implementer: Grok 4.6
- Auditor: agy `gemini-3.1-pro-high` / display `Gemini 3.1 Pro (High)` / session `cc11f380-fd73-4701-a267-40970954d78f`
- Verdict: **PASS**
- Supersedes earlier AGY PASS on `806a9a7317` after P1/P2 fixes.

## Findings
1. **p1-compose-ignore INFO RESOLVED** — P1: doctor/CLI ignore compose.yml not owned by the target repo. The `_owned_compose` helper correctly ensures that explicit `compose_path` resolves to a child of `repo_path`. Foreign `compose.yml` files are correctly ignored, preventing product-compose convention hazards.
1. **p2-empty-service-list INFO RESOLVED** — P2: mcp up returns without docker compose up if empty service list. If `task-orchestrator` is removed due to a missing `DOPECON_BRIDGE_TOKEN` and the `svc_list` becomes empty, the CLI correctly returns early with a warning rather than running an empty `docker compose up`.
1. **p3-none-narrowing INFO RESOLVED** — P3: configured_ports None-narrowing. Safe-guard logic added to check `configured_ports is not None` before querying it, preventing potential TypeErrors/KeyErrors during diagnostic generation.
1. **p4-test-line-wrap INFO RESOLVED** — P4: test line wrap. Test line wrap formatting fixes implemented, tests pass.
1. **formula-reserved-warn INFO RESOLVED** — Original Formula-Reserved WARN Behavior. Formula collisions correctly downgrade from `FAIL` to `WARN` if `source_label == "formula"` and the user has safely overridden the collision with a non-reserved port via `.envrc`. Configured reserved collisions remain `FAIL`.
1. **secrets-check INFO RESOLVED** — Secrets handling. No secrets are written to `.mcp.json` or `.env`. The fix for compose interpolation injects a dummy string `dopemux-compose-interpolation-only` which is safe.
1. **scope-check INFO RESOLVED** — Scope constraint validation. All changes were restricted to the allowlist provided in TP-DMX-MCP-DOCTOR-FORMULA-RESERVED-001.json.

## Remaining risks
- If a user bypasses dopemux and directly invokes `docker compose up task-orchestrator` with the fake token `dopemux-compose-interpolation-only`, it could parse successfully but fail at runtime. This is an expected side effect of the fix.
- The `_owned_compose` check relies on `repo_path` being accurate. Symlinked worktrees could potentially cause edge cases.

## Summary
Embedded independent audit completed successfully. All fixes implemented by Grok for PR #1256 (TP-DMX-MCP-DOCTOR-FORMULA-RESERVED-001) meet the packet's invariants and are verified working. No secrets leaked. Remaining risks are acceptable.
