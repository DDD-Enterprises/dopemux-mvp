# Dopemux Beta-Readiness — Sequenced Backlog (CONSOLIDATED v1+v2)

**HEAD** `755bf3846` · **2026-05-29** · Beta bar: **Mixed/Staged** (internal-dogfood gate → public-clone gate delta)
Evidence for every item: `00-MASTER-REPORT.md` + raw digest `tool-results/b3n6t053w.txt` + workflow output `wz7nopunw.output` (all path:line).
Coverage: 11/11 domains (v1 MCP + v2 CLI/INSTALL/SERVICES/HOOKS/UI/DOCS/WORKFLOWS/TESTS/SECURITY) · 14/15 re-verify (RV-8 closed inline; wrapping spec deferred — see epic).

## Verdict

**NOT public-ready. Internal dogfood is reachable after Wave 0–1.** The v2 audit surfaced materially worse install/security/docs state than v1: a **CRIT install blocker** (`dopemux-network` never created → every fresh `docker compose up` fails), a **broken `ui-dashboard` build**, **5 network/secret exposures**, **first-touch docs that describe the wrong product**, and a **CI gate that runs a fraction of the suite**. Re-verification also *cleared* several stale fears (RV-1 shell-injection, RV-4 code-agent, RV-5 mcp status, RV-15 RTE gates all RESOLVED). The agent-wrapping live-run path (codex/copilot/claude+vanilla — all in-beta per your call) remains **un-specced** (the spec agent hit a session limit) and is carried as a sized epic.

---

## Wave 0 — Restore / unblock (pure recovery, do first)

| id | title | sev | gate | eff | fix |
|----|-------|-----|------|-----|-----|
| BETA-SURF-01 | Restore `/dx:` command surface (17 of 18 cmds reverted by clobber #720; only `implement.md` left) | MED | int | M | cherry-pick `.claude/commands/dx/*` from `origin/task-orchestrator-claude-surface` |
| BETA-WF-01 | Restore `.taskorchestrator/config.yaml` (deleted by same clobber → orchestrator schema layer inert) | HIGH | int+pub | S | restore from `3b39c3dfa`/`409da4edf` lineage or `origin/task-orchestrator-claude-surface` |
| BETA-UI-01 | Recover deleted React "Ultra" UI — unbuildable (App.tsx imports `CognitiveLoadGauge`/`PredictionPanel`/`TeamDashboard`, deleted by `87ea13440`) | HIGH | pub | M | `git checkout 87ea13440~1 -- ui-dashboard/{index.html,vite.config.ts,tsconfig*,src/components/{CognitiveLoadGauge,PredictionPanel,TeamDashboard}.tsx}`; this is recovery, not new build (RV-13) |

## Wave 1 — Internal-beta gate (dogfood blockers)

| id | title | sev | gate | eff | fix |
|----|-------|-----|------|-----|-----|
| BETA-INSTALL-02 | **`dopemux-network` external network never created → every fresh install fails `compose up`** | CRIT | int+pub | S | add `docker network inspect dopemux-network >/dev/null 2>&1 \|\| docker network create dopemux-network` to `ensure_docker_networks` |
| BETA-CLI-01 | `dopemux decisions` ships only `energy`+`patterns`; `review/list/show/update-outcome/query` absent | HIGH | int | M | implement the 5 subcommands against the ConPort client, mirroring energy/patterns |
| BETA-MCP-01 | `.mcp.json:5,16` SSE URLs `${CONPORT_MCP_PORT}`/`${DOPE_MEMORY_PORT}` have no `:-` default → empty-port if launcher not run first | HIGH | int+pub | S | add `:-3004`/`:-3020` defaults matching compose, or guarantee launcher exports them |
| BETA-INSTALL-05 | `verify_installation` reports FAIL on a correctly installed system | HIGH | int+pub | S | fix Check 2 (`$DOPEMUX_HOME/venv/bin/python -c "import dopemux"`) and Check 4 (point at a shipped profile) |
| BETA-INSTALL-06 | `--uninstall` backup omits the real data (Postgres/ConPort knowledge graph) → data loss | HIGH | int+pub | S | dump named volumes (`pg_dump`/`tar` of `pg_age_data`) before `down -v` |
| BETA-CLI-05 | `dopemux init` exits 0 after `.claude/` configuration fails | MED | int+pub | S | on `ClaudeConfigError`/`ProfileValidationError` print failure + `sys.exit(1)` |
| BETA-WF-02 | Split-brain: operator `dopemux mcp` manages a *different* orchestrator than the agent uses | HIGH | int+pub | M | pick one canonical orchestrator (jpicklyk MCP per 2026-05-28 docs); rename/retire the compose `task-orchestrator` FastAPI service |
| BETA-TEST-01 | CI PR-gate executes only a fraction of the suite; core flows ungated | CRIT | int+pub | M | add `test_cli.py test_cli_mcp_startup.py test_routing_*` to the PR-blocking lane |
| BETA-TEST-02 | Beta-critical suites exist but run nowhere (wiring gap, not writing gap) | HIGH | int+pub | S | add existing files to a blocking lane; triage each for local pass/fail |

## Wave 2 — Public-beta gate (external-clone delta)

**Install / packaging**
| id | title | sev | eff |
|----|-------|-----|-----|
| BETA-INSTALL-01 | `.mcp.json:25` / orchestrator launcher hardcodes per-user absolute path (`/Users/hue/plugins/...`) → dead MCP on every clone | HIGH | M |
| BETA-INSTALL-03 | core/research/full "stacks" are fictional — all boot all 39 services | HIGH | M |
| BETA-INSTALL-04 | installer assumes repo-root CWD but advertises `curl \| bash` | HIGH | M |
| BETA-INSTALL-07 | no retry on docker pulls + cosmetically false "images pulled" | MED | S |
| BETA-INSTALL-09 | core deps fully unbounded, no lockfile (reproducibility) | MED | M |

**Security (public gate)**
| id | title | sev | eff |
|----|-------|-----|-----|
| BETA-SEC-01 | LiteLLM proxy hardcoded master key on `0.0.0.0` | HIGH | S |
| BETA-SEC-02 | Unauthenticated infra/data services published to `0.0.0.0` (Postgres, Redis×2, Qdrant, Redis UI) | HIGH | M |
| BETA-SEC-03 | Postgres password hardcoded literal default in DATABASE_URLs | MED | S |
| BETA-SEC-04 | adhd-engine API auth fails *open* when key unset; ships `dev-key-123` | MED | S |
| BETA-SEC-05 | dope-memory JWT secret defaults to public placeholder (forgeable tokens) | MED | S |

**Runtime / services / CLI honesty**
| id | title | sev | eff |
|----|-------|-----|-----|
| BETA-MCP-02 | compose `service_started` (bare-list depends_on) for conport/task-orch/adhd-engine → cold-start races | MED | S |
| BETA-MCP-03 | no per-instance Redis; adhd-engine keys user-scoped only → same-user worktrees collide | MED | M |
| BETA-CLI-02 | `dopemux start` swallows routing-failure aborts and silently reroutes traffic | HIGH | S |
| BETA-CLI-03 | litellm-gated command groups vanish silently (vs `extract`'s stub pattern) | MED | S |
| BETA-CLI-04 | `orchestrator memory record_decision/progress` fabricate SUCCESS on broken instance | MED | S |
| BETA-HOOK-02 | hooks' unguarded import chain crashes on a clean checkout (degrades *vanilla* Claude Code too) | HIGH | S |
| BETA-SVC-01 | no memory/CPU limits on any of 23 services | MED | M |
| BETA-SVC-04 | multi-instance/worktree runs stomp one shared `dopemux` compose project (document single-instance) | MED | M |
| BETA-UI-03 | web backend (:3001) doesn't serve the React build & isn't containerized | MED | M |

**Docs (first-touch)**
| id | title | sev | eff |
|----|-------|-----|-----|
| BETA-DOCS-01 | Tutorials "Start Here" is a stale 2025 audit report, not onboarding | CRIT | S |
| BETA-DOCS-02 | Sole CLI reference (`cheat-sheet.md`) documents a different product (`chatx`) | CRIT | M |
| BETA-DOCS-03 | three contradictory install docs in the first-touch surface | HIGH | M |
| BETA-DOCS-04 | `docs/02-how-to/install.md` ends with leaked AI tool-call markup | HIGH | S |
| BETA-DOCS-05 | `installation.md`/`quickstart.md` reference non-existent helper scripts | HIGH | S |
| BETA-DOCS-06 | troubleshooting page cites dead ports + wrong compose path | HIGH | M |

**Tests (public confidence)**
| id | title | sev | eff |
|----|-------|-----|-----|
| BETA-TEST-03 | multi-instance isolation suite disabled (`test_event_multi_instance.py.disabled`) | HIGH | M |
| BETA-TEST-04 | branch-protection enforcement of the CI gate is UNKNOWN | HIGH | S |
| BETA-TEST-05 | installer test is push-only dry-run, not a PR/clean-machine gate | HIGH | M |
| BETA-TEST-06 | two unit-lane files unconditionally quarantined (always skip) | MED | M |

## Wave 3 — Post-beta (polish / cleanup / dead code)

`BETA-CLI-06` cli.py 6337-line monolith + dup function · `BETA-CLI-07` `switch` dropped + profile_commands shadow · `BETA-CLI-08` LiteLLM config-write swallowed · `BETA-MCP-04` shared-Postgres dev-cred doc + **RV-8** (autocommit, no write-lock; bounded by partitioning) · `BETA-HOOK-01` Stop-hook friction · `BETA-HOOK-03` hook latency/no-timeout/double-init · `BETA-SVC-03` conport always-green healthcheck · `BETA-UI-02` consolidate two ADHD HUDs (keep Textual `dopemux dashboard` canonical) · `BETA-WF-03` delete dead `wire_claude_mcp.py` · `BETA-TEST-07` surface skips + coverage floor · `BETA-TEST-08` dual pytest config · `BETA-DOCS-*` 760-file doc-dup cleanup (RV-14). Plus all removals → `02-REMOVE-CONSOLIDATE.md`.

## Agent-Wrapping Epic (all-three-in-beta per your decision)

> The spec agent hit the session limit, so the detailed enumeration is **NOT yet done** — `BETA-WRAP-00` must run first. Current state from earlier discovery: Claude = `claude/launcher.py` subprocess passthrough + MCP-config injection; Copilot = post-hoc transcript ingestion only (`memory/adapters/copilot.py`); Codex = absent; vanilla = unverified.

| id | title | sev | gate | eff |
|----|-------|-----|------|-----|
| BETA-WRAP-00 | **Spec** the wrapping layer: map current claude/codex/copilot/vanilla, define target, size the build (re-run; session-limited) | HIGH | int | M |
| BETA-WRAP-01 | Claude live-wrapping hardening (launcher exists) | — | int | M |
| BETA-WRAP-02 | Codex live wrapping (build — currently absent) | — | int | L/XL |
| BETA-WRAP-03 | Copilot live wrapping (build — only ingestion today) | — | int | L |
| BETA-WRAP-04 | Vanilla-passthrough compatibility (hooks/MCP must not break agents used outside dopemux — ties to BETA-HOOK-02) | — | int+pub | M |

## Roadmap at a glance

| Wave | Gate | Lead items | Parallelizable |
|------|------|-----------|----------------|
| 0 | Restore | SURF-01, WF-01, UI-01 | yes (independent recoveries) |
| 1 | Internal-beta | INSTALL-02 (CRIT), CLI-01, MCP-01, INSTALL-05/06, WF-02, TEST-01/02 + WRAP-00 | mostly yes |
| 2 | Public-beta | INSTALL-01/03/04, SEC-01..05, DOCS-01..06, HOOK-02, MCP-02/03, TEST-03/04/05 | yes, in domain clusters |
| 3 | Post-beta | monolith split, dead-code removals, doc-dup cleanup, WRAP-02/03 finish | yes (deferred) |
