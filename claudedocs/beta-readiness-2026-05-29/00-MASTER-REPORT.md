# Dopemux Beta-Readiness — Master Report (CONSOLIDATED v1+v2)

| Field | Value |
|-------|-------|
| HEAD | `755bf38460…` (`755bf3846`) · branch `claude/hopeful-shirley-656b07` |
| Date | 2026-05-29 |
| Coverage | **11/11 domains** (v1: MCP · v2: CLI, INSTALL, SERVICES, HOOKS, UI, DOCS, WORKFLOWS, TESTS, SECURITY) + agent-wrapping (spec deferred) · **15/15 re-verify** |
| Method | Read-only multi-agent audit; every inherited claim re-checked at HEAD; CRIT/HIGH + removals adversarially verified. Consolidation done in main loop after the v2 consolidation agent hit a session limit. |
| Evidence | v1 detail → `00-MASTER-REPORT.v1.bak`; v2 full digest → `claudedocs/beta-readiness-2026-05-29/` raw + session output `wz7nopunw.output` + `tool-results/b3n6t053w.txt` (all path:line) |
| Backlog + orchestrator | `01-SEQUENCED-BACKLOG.md` → loaded to task-orchestrator root `b5960763` |

## Executive Summary

**Verdict: NOT public-ready. Internal dogfood is reachable after Waves 0–1.** The v2 audit found the platform materially rougher than v1 implied, concentrated in **install, security, and docs**:

- **Install is BROKEN on a clean machine** — `install.sh` never creates the external `dopemux-network` that `compose.yml` requires, so *every* fresh `docker compose up` fails (BETA-INSTALL-02, CRIT). Compounded by fictional core/research/full "stacks" (all boot all 39 services), a curl|bash installer that assumes repo-root CWD, a `verify_installation` that fails on a correct install, and an `--uninstall` that backs up config but **deletes the Postgres/ConPort knowledge graph**.
- **Public-facing security gaps** — unauthenticated Postgres/Redis×2/Qdrant/Redis-UI published on `0.0.0.0`, a hardcoded LiteLLM master key, default Postgres password, a fail-*open* ADHD-engine API key, and a public-placeholder dope-memory JWT secret.
- **First-touch docs describe the wrong product** — the only CLI reference (`cheat-sheet.md`) documents `chatx`; the tutorials "Start Here" is a stale 2025 audit report; three contradictory install docs; one install doc ends in leaked AI tool-call markup.
- **The `ui-dashboard` build is broken** (App.tsx imports 3 components deleted by `87ea13440`) and **CI gates only a fraction of the suite** (core CLI/routing/multi-instance suites exist but run nowhere).
- **Two clobber regressions are live** (PR #720): the `/dx:` command surface (17 of 18 cmds) and `.taskorchestrator/config.yaml` — both **restorable** from `origin/task-orchestrator-claude-surface`.

**Re-verification cleared a lot of stale fear** (the 2026-05-01 audit aged out): RV-1 shell-injection, RV-4 code-agent exit-0, RV-5 mcp status/logs, RV-15 RTE live-gates are all **RESOLVED** at HEAD. The agent-wrapping live-run path (codex/copilot/claude+vanilla — all in-beta per decision) is **un-specced** (the spec agent was session-limited) and carried as a sized epic (`BETA-WRAP-00` gates the rest).

## Re-verification of inherited findings (15/15)

| ID | Verdict | Claim |
|----|---------|-------|
| RV-1 | **RESOLVED** | mcp/servers `up --services` shell injection — fixed `713879813` (allowlist + arg-list, no shell) |
| RV-2 | RESOLVED | routing `_set_routing_mode` NameError — fixed `f6df0bdbd` |
| RV-3 | **CONFIRMED** | `decisions` ships only energy+patterns (→ BETA-CLI-01) |
| RV-4 | RESOLVED | code-agent exit-0-on-crash — `code_commands.py` deleted in #586 |
| RV-5 | RESOLVED | mcp status/logs swallow docker errors — now `check=True`+`sys.exit(1)` |
| RV-6 | RESOLVED | mobile/tmux litellm hard-import — guarded |
| RV-7 | PARTIAL | Redis user-scoped not workspace-scoped (→ BETA-MCP-03) |
| RV-8 | **CONFIRMED (low)** | Postgres autocommit, no advisory/`FOR UPDATE` locks; bounded by (workspace,instance) partitioning (→ BETA-MCP-04) |
| RV-9 | CONFIRMED | compose `service_started` bare-list races (→ BETA-MCP-02) |
| RV-10 | PARTIAL | Stop-hook one-shot block w/ re-entry guard (→ BETA-HOOK-01, friction) |
| RV-11 | PARTIAL | dead `router`/`dope-query`; dope-memory NOT a dup (→ removals) |
| RV-12 | **PARTIAL** | `/dx` clobbered (17/18 reverted); `/sc` never existed here (→ BETA-SURF-01) |
| RV-13 | **CONFIRMED** | App.tsx imports 3 deleted components → build broken (→ BETA-UI-01) |
| RV-14 | **CONFIRMED** | docs duplication = repo-wide 760-file pattern from #226 (→ BETA-DOCS-DEDUP) |
| RV-15 | RESOLVED | RTE live-batch gates (dual-consent, spend caps, provider routing) exist + enforced |

## Confirmed findings by domain (v2)

Severity · gate · effort. Full path:line evidence in the raw digest; remediation in `01-SEQUENCED-BACKLOG.md`.

- **CLI** (MIXED): start swallows routing aborts (HIGH/pub, CLI-02) · litellm groups vanish silently (MED, CLI-03) · orchestrator memory fabricates SUCCESS (MED, CLI-04) · init exits 0 on config fail (MED/int, CLI-05) · 6337-line monolith + dup fn (consolidate, CLI-06) · switch/profile shadow + litellm cfg swallow (LOW, CLI-07/08).
- **INSTALL** (BROKEN): dopemux-network never created **(CRIT, INSTALL-02)** · fictional stacks (HIGH, INSTALL-03) · curl|bash CWD assumption (HIGH, INSTALL-04) · verify_installation false-fail (HIGH, INSTALL-05) · uninstall data loss (HIGH, INSTALL-06) · no pull retry/false success (MED, INSTALL-07) · INSTALLER_TEST_MODE no-op (doc) · unbounded deps (MED, INSTALL-09).
- **SERVICES** (MIXED): network (=INSTALL-02) · stacks (=INSTALL-03) · uninstall volumes (=INSTALL-06) · no resource limits (MED, SVC-01) · multi-instance compose stomp (MED, SVC-04) · always-green conport healthcheck (SVC-03) · start-all script drift (SVC-05/06) · 7 orphaned volumes (removal).
- **HOOKS** (MIXED): unguarded import chain crashes clean checkout / vanilla CC **(HIGH/pub, HOOK-02)** · latency/no-timeout/double-init (MED, HOOK-03) · 6 unwired dead hook scripts (removal) · silent no-op when cache stale (doc).
- **UI** (MIXED): React Ultra UI deleted, unbuildable (HIGH/pub, UI-01=RV-13) · two ADHD HUDs, undeclared canonical (consolidate, UI-02; keep Textual `dopemux dashboard`) · web backend doesn't serve build (MED, UI-03) · `dashboard/` pkg + `dopemux_dashboard.py` + stale `adhd-dashboard:8097` CORS (removals).
- **DOCS** (MIXED): stale "Start Here" **(CRIT, DOCS-01)** · `chatx` cheat-sheet **(CRIT, DOCS-02)** · 3 contradictory install docs (HIGH, DOCS-03) · leaked AI markup in install.md (HIGH, DOCS-04) · nonexistent helper scripts (HIGH, DOCS-05) · troubleshooting dead ports (HIGH, DOCS-06).
- **WORKFLOWS** (MIXED): orchestrator launcher hardcoded path (=INSTALL-01) · `.taskorchestrator/config.yaml` deleted (HIGH, WF-01 restore) · operator/agent orchestrator split-brain (HIGH, WF-02) · dead `wire_claude_mcp.py` (removal, WF-03) · 13-vs-14-tool drift (doc).
- **TESTS** (PARTIAL): CI gates fraction of suite **(CRIT, TEST-01)** · beta-critical suites unwired (HIGH, TEST-02) · multi-instance suite disabled (HIGH, TEST-03) · branch-protection UNKNOWN (HIGH, TEST-04) · installer push-only gate (HIGH, TEST-05) · 2 quarantined unit files (MED, TEST-06) · dual pytest config (removal).
- **SECURITY** (MIXED): LiteLLM hardcoded master key on 0.0.0.0 (HIGH, SEC-01) · unauth infra on 0.0.0.0 (HIGH, SEC-02) · Postgres default pw (MED, SEC-03) · adhd-engine fail-open auth + dev-key-123 (MED, SEC-04) · dope-memory public JWT secret (MED, SEC-05) · no TLS (doc). Note: compose `task-orchestrator` removal candidate **REFUTED** (cited wrong artifact).
- **MCP** (v1, MIXED): `.mcp.json` empty-port URLs (HIGH, MCP-01) · service_started races (MED, MCP-02) · per-instance Redis collision (MED, MCP-03) · shared-Postgres dev-cred posture (MCP-04). `.mcp.json` hardcoded task-orch path (HIGH/pub, INSTALL-01).

## External escalations (upstream Kotlin task-orchestrator MCP — not repo packets)
Timestamp-parse silent-zero · health-check under-report · dangling dependency edges. (Per orchestrator audit 2026-05-28.)

## Open unknowns / NOT_RUN
- **Agent-wrapping spec** — `BETA-WRAP-00` (spec agent session-limited). Current-state from discovery only: claude=launcher passthrough, copilot=transcript ingestion, codex=absent, vanilla=unverified.
- **RV-8 real-world severity** — code confirms no write-locks; practical race depends on concurrent same-instance writers (bounded by partitioning). Not load-tested.
- **TEST-04** branch protection — operator-only verification (read-only can't see repo settings).
- **INSTALL-10** `dopetask==0.5.1` index availability — unverifiable read-only.

## Process note (durable lesson)
This audit took 4 workflow attempts. v1 (38-agent fan-out) lost ~30 agents to a StructuredOutput-emission failure (heavy-tool + schema). Two gap-fill bursts (~28 agents) were instantly **rate-limited** (concurrency-triggered, not usage). A fully-sequential retry **hung** when its launching session was suspended while idle. The winning config: **batched concurrency ~3–6, no-schema markdown explorers, structuring only at consolidation, run from a live session.** Even then the final consolidation hit a session usage cap and was completed in the main loop.
