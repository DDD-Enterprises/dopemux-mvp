# Claude-Mem Techniques (Evidence-Anchored)

## Source Acquisition Notes
- [VERIFIED] Direct `git clone` from shell failed in this environment (`Could not resolve host: github.com`), so evidence was harvested via docs URLs + GitHub raw paths with line-level citations.
  - Clone attempt evidence: `_audit_out/_sources/claude_mem_clone_attempt.txt:1-3`

---

## Technique Card 1: Lifecycle Hook Orchestration
- Technique: lifecycle hooks + pre-hook command chaining
- Problem solved: capture/inject memory at stable session boundaries without modifying host runtime.
- Implementation: docs define lifecycle events (`SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `SessionEnd`) and smart-install pre-hook; plugin hook config wires chained commands per event.
- Why robust: explicit phase boundaries and externalized commands reduce hidden state.
- Failure modes: if hooks fail, context may be stale or incomplete; docs describe safety/fallback behavior.
- What to steal for Dopemux: explicit event-phase contracts and declarative hook-chain config.
- Evidence:
  - Docs: [Hook Lifecycle](https://docs.claude-mem.ai/architecture/hook-lifecycle) lines 133-142, 181-189
  - Docs: [Architecture Overview](https://docs.claude-mem.ai/architecture/overview) lines 198-207
  - GitHub: `plugin/hooks/hooks.json:1-1` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/plugin/hooks/hooks.json))

## Technique Card 2: Background Worker + Fire-and-Forget Hooks
- Technique: hooks enqueue/forward work; Bun-managed worker processes async.
- Problem solved: avoid hook timeouts and keep interactive UX responsive.
- Implementation: docs describe worker HTTP API and fire-and-forget model; code has process manager with start/wait/restart checks and server routes.
- Why robust: worker lifecycle controls + health/restart path isolate failures from hooks.
- Failure modes: worker down/unreachable causes degraded memory writes/readbacks.
- What to steal for Dopemux: strict separation of capture path from processing path; process manager with health-based restart policy.
- Evidence:
  - Docs: [Hook Lifecycle](https://docs.claude-mem.ai/architecture/hook-lifecycle) lines 244-246, 289-294
  - Docs: [Worker Service](https://docs.claude-mem.ai/architecture/worker-service) lines 95-102, 124-139
  - GitHub: `src/services/infrastructure/ProcessManager.ts:3-7` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/infrastructure/ProcessManager.ts))
  - GitHub: `src/services/server/Server.ts:2-8` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/server/Server.ts))

## Technique Card 3: 3-Layer Progressive Disclosure Search
- Technique: `search` -> `timeline` -> `get_observations` staged retrieval.
- Problem solved: token blow-up from eager context expansion.
- Implementation: docs define workflow and token economics; MCP server tool contract encodes the sequence.
- Why robust: deterministic staged narrowing before detailed fetch; predictable cost envelope.
- Failure modes: skipping layer 1 can overfetch irrelevant details.
- What to steal for Dopemux: lane-aware staged retrieval API with hard caps and explicit expansion calls.
- Evidence:
  - Docs: [Search Architecture](https://docs.claude-mem.ai/architecture/search-architecture) lines 137-139, 188-193
  - Docs: [Progressive Disclosure](https://docs.claude-mem.ai/progressive-disclosure) lines 60-65, 133-139
  - GitHub: `src/servers/mcp-server.ts:4-6` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/servers/mcp-server.ts))
  - GitHub: `README.md:393-401` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/README.md))

## Technique Card 4: SQLite + FTS5 + Trigger Sync + Query Escaping
- Technique: normalized SQLite schema with FTS virtual tables and trigger maintenance.
- Problem solved: fast text retrieval with stable local persistence and low ops burden.
- Implementation: docs describe core tables and FTS5; migration runner defines FTS tables/triggers; search code escapes user input.
- Why robust: data + index consistency enforced by triggers; injection hardening at query construction.
- Failure modes: trigger drift/migration defects can desync FTS tables.
- What to steal for Dopemux: deterministic schema/migration ownership and mandatory query escaping in all text search surfaces.
- Evidence:
  - Docs: [Database Architecture](https://docs.claude-mem.ai/architecture/database) lines 97-112
  - GitHub: `src/services/sqlite/migrations/runner.ts:62-112` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/sqlite/migrations/runner.ts))
  - GitHub: `src/services/sqlite/migrations/runner.ts:298-304` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/sqlite/migrations/runner.ts))

## Technique Card 5: Privacy Tags + Dual Write-Safety
- Technique: explicit private tags (`<private>...</private>`, `<private></private>`) removed before persistence.
- Problem solved: keep sensitive snippets out of long-term memory.
- Implementation: docs define tag behavior and edge cases; MCP server strips tags and checks privacy toggles.
- Why robust: user-authored explicit controls + preprocessing before storage.
- Failure modes: malformed tags/escaping edge cases; docs include no-space and close-tag caveats.
- What to steal for Dopemux: explicit per-entry privacy markers and pre-storage scrub stage with observable metrics.
- Evidence:
  - Docs: [Private Tags](https://docs.claude-mem.ai/private-tags) lines 62-74, 88-111
  - GitHub: `src/servers/mcp-server.ts:3-3` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/servers/mcp-server.ts))

## Technique Card 6: Context Configuration as First-Class Contract
- Technique: explicit settings for what gets injected and how much.
- Problem solved: prevent global one-size-fits-all context stuffing.
- Implementation: docs enumerate core context knobs; config loader and context builder apply include/exclude/show flags and typed filters.
- Why robust: deterministic knobs in settings file, not hidden heuristics.
- Failure modes: bad defaults can still over/under-inject; requires profile calibration.
- What to steal for Dopemux: lane-by-lane injection policy file with defaults + per-mode overrides.
- Evidence:
  - Docs: [Configuration](https://docs.claude-mem.ai/configuration) lines 59-65, 159-164
  - GitHub: `src/services/context/ContextConfigLoader.ts:10-20` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/context/ContextConfigLoader.ts))
  - GitHub: `src/services/context/ContextBuilder.ts:10-15` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/context/ContextBuilder.ts))

## Technique Card 7: IDE Integration via Rule Files + Hook Installer
- Technique: installer writes Cursor hooks and rule files (`.cursor/rules`).
- Problem solved: move memory behavior into IDE-native control surfaces.
- Implementation: docs cover Cursor integration paths; installer generates rules and user instructions for activation.
- Why robust: declarative IDE rules are auditable and portable across repos.
- Failure modes: rules drift or missing install step after upgrades.
- What to steal for Dopemux: generated rules templates per memory lane and role/mode.
- Evidence:
  - Docs: [Cursor Integration](https://docs.claude-mem.ai/cursor) lines 80-95
  - GitHub: `src/services/integrations/CursorHooksInstaller.ts:3-18` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/integrations/CursorHooksInstaller.ts))

## Technique Card 8: Operational Recovery Surfaces (Queue + Health)
- Technique: explicit manual recovery endpoints/commands and queue inspection.
- Problem solved: recover from dropped/stuck processing without data loss.
- Implementation: docs provide queue triage and manual replay flows.
- Why robust: deterministic operator runbook rather than opaque retry loops.
- Failure modes: replay on corrupt payloads may re-fail; needs dead-letter/poison handling.
- What to steal for Dopemux: first-class recovery APIs + audit logs for every recovery action.
- Evidence:
  - Docs: [Manual Recovery](https://docs.claude-mem.ai/manual-recovery) lines 66-75, 159-166
  - Docs: [Worker Service](https://docs.claude-mem.ai/architecture/worker-service) lines 333-338
  - GitHub: `src/services/infrastructure/ProcessManager.ts:5-7` ([raw](https://raw.githubusercontent.com/thedotmack/claude-mem/main/src/services/infrastructure/ProcessManager.ts))

---

## Remaining Unknowns (Claude-Mem)
- [UNKNOWN] Exact current internal queue persistence model (beyond documented endpoints) could not be fully code-walked due inability to local-clone full repo in this environment.
- [UNKNOWN] Any unreleased branch behavior not reflected in published docs/main branch.
