---
id: rfc-2026-10-30-foundations-wave-1
title: Foundations Wave 1 - Contract Tests in CI, ADHD Engine MCP Repair, dopemux adhd status, Port Drift Tests
type: rfc
status: draft
author: claude-code
date: '2026-10-30'
created: 2026-10-30
updated: 2026-10-30
last_review: '2026-10-30'
next_review: '2027-01-28'
owner: '@hu3mann'
derived_from:
- claudedocs/dopemux-mods-plugins-opportunity-map-2026-10-16.md (items S1, C1, C4)
- recon of origin/main at 93050d135 on 2026-10-30
prelude: Design for the first Foundations wave. Offline-verifiable Python and CI work that makes existing contracts enforced, repairs the ADHD engine's MCP tools on the real engine, adds a read-only dopemux adhd status command, and catches service port drift.
summary: One MacroPacket, five workstreams, one final independent L2 audit. No changes to files owned by open PR 1472, no MCP manifest changes, no new mods.
---
# Foundations Wave 1

Status: **draft, for operator approval.** Nothing is built until this is approved. All facts below were read from `origin/main` at `93050d135` on 2026-10-30 unless a line says otherwise.

## 1. Why this wave, and why now

The Dopemux engines exist, but the last mile is broken in ways nothing catches:

- Contract tests that guard the service registry, compose, the MCP fleet catalog, personas and the PAL model catalog live in `tests/arch/` (9 files, 184 tests, all passing in the repo venv). **No CI job runs them.** `.github/workflows/ci-complete.yml` runs only named paths: `tests/unit` plus two named files (`:183-189`), the dope-memory endpoint test (`:197`), `tests/dcp` (`:203-206`), extractor tests and `tests/integration` (`:490`).
- The ADHD engine's MCP server exposes two tools (`services/adhd_engine/main.py:63-90`). Both call engine methods (`get_energy_level`, `get_attention_state`, `get_cognitive_load`, `assess_task`) that exist **only** on the fallback engine class in `main.py` (`:154-244`). The real engine, `services/adhd_engine/core/engine.py`, defines none of them. With a healthy engine, both MCP tools raise.
- There is no `dopemux adhd` command, and the engine's address is described four different ways:
  - compose publishes it on `127.0.0.1:${ADHD_ENGINE_PORT:-3025}` (`compose.yml`, `adhd-engine` service), and the registry agrees (`services/registry.yaml:183-186`);
  - run directly, the engine listens on `API_PORT`, default `8095` (`services/adhd_engine/config.py:65`);
  - `src/dopemux/config/manager.py:200` and `:621` default to `http://localhost:3008`, and nothing in `src/` reads it;
  - two resolvers (`src/dopemux/ui/service_endpoints.py:102-117`, `src/dopemux/profile_detector.py:379-384`) try `DOPEMUX_ADHD_ENGINE_BASE_URL`, then `DOPEMUX_ADHD_ENGINE_PORT`, then probe sockets on `5448` and `8095`. `5448` has no source anywhere in the repo.
- Ports are hard-coded in several scripts and disagree with the registry (section 6, W4).

The three Claude Code mods built last week (Pulse, Route Ledger, Memory Bridge) have never run in a real session. Building more host-dependent mods on top of unverified host assumptions adds risk. This wave is the opposite: every deliverable can be verified offline and in CI.

## 2. Goals

| ID | Goal | Done when |
|---|---|---|
| G1 | `tests/arch` runs in CI on every PR. | A CI step runs `tests/arch` inside the required `🧪 Unit Tests` job and is green on this PR. |
| G2 | The ADHD engine's MCP tools work on the real engine. | Both tools return data with the real engine class; a CI-run test fails if a tool calls a method the real engine lacks. |
| G3 | A person or agent can read the engine's state from the CLI. | `dopemux adhd status` and `dopemux adhd status --json` work against a mocked engine in tests and report unreachable and malformed states clearly. |
| G4 | Service port drift between the registry, compose, the catalog and hard-coded scripts is caught. | A CI-run test fails on an injected drift, passes on this branch, and every existing difference is either fixed or listed with a reason. |
| G5 | Every new feature is documented, including usage in the agent docs. | Reference docs and agent-doc entries exist for G1-G4 and pass the docs gates. |

## 3. Non-goals

- **No edits to `services/adhd_engine/api/routes.py` or `services/adhd_engine/tests/test_state_contract.py`.** Open PR #1472 (Pulse) changes both. Touching them would turn the Pulse re-audit into a conflict. This rules out a break-writer endpoint (map item P2) and the `dopemux adhd break|focus|ack` verbs; they come after #1472 merges.
- **No MCP manifest changes.** The engine's MCP app is mounted at `/mcp` (`main.py:479`), but adding it to `.mcp.json` or `mcp_catalog.yaml` is a contract-sensitive change. Follow-up.
- **No fix for the ADHD engine's own test suite.** `services/adhd_engine/tests/` is not run by CI and is unhealthy: 88 passed, 28 failed, 4 files fail to import (repo venv, 2026-10-30). Wiring it into CI would make CI red. Follow-up with its own triage.
- **No task-orchestrator unification.** Registry port `8000` (`services/registry.yaml:152-156`) and catalog/`.mcp.json` port `7890` (`mcp_catalog.yaml:616-620`, `.mcp.json:23-25`) are two different processes sharing one name (map item S2). W4 records this as an explained exception, not a bug to fix.
- **No change to `.claude/statusline.sh` behavior.** It is the operator's live status line. Its stale probe is recorded as an exception with a follow-up (W4).
- **No proof-only closure change** (the validator mode that would let a clean merge of `main` keep a signed proof). It changes the audit gate itself and needs its own operator decision.
- **No new mods and no edits under `plugins/`.**
- `services/adhd_engine/cli/adhd.py` (unregistered, calls endpoints that do not exist) is left in place. Retiring it is a follow-up.

## 4. Anti-goals (would be failure even if it "works")

- A CI step that is red on day one, or that passes only because tests were skipped or deselected.
- A drift test so broad it flags legitimate differences, such as container port versus host port, and gets silenced with a blanket exception.
- An exception list that becomes a dumping ground. Every entry needs a reason and a follow-up reference.
- A port "fix" that breaks a script someone runs in a context the test did not consider, for example inside a container where the container port is correct.
- `dopemux adhd status` inventing precision the engine does not have, such as showing `session 0 min` as if it were measured. Main never sets `_session_start_times` on the real engine, so `/state` always reports `session_minutes: 0`.

## 5. Constraints

- **Governance.** One supervisor-issued MacroPacket with the workstreams below, a TP_ROUTE per child, write allowlists, risk lane L2, and **one** final independent audit after the content head is frozen. `scripts/governance/validate_change_contract.py` classifies these paths as L2 (`model_audit_required=True`), docs included.
- **Audit route.** The operator approves the route per run with a literal authorization line. Precedent for this repo is Grok via `grok-cli` / `grok-4.5`, tool-less, one attempt. Not assumed.
- **Merge order.** `main` requires up-to-date branches, and a signed proof binds a PR to its audited head (`docs/92-runbooks/signed-proof-merge-order.md` on PR #1484). This wave's audit should run after #1482, #1472 and #1483 have merged, or accept one re-audit per later merge. Docs PR #1484 overlaps this wave on `AGENTS.md` and `.claude/claude.md`; whichever merges second needs an update.
- **Pushing a workflow file** needs a token with the `workflow` scope. If the push is refused, the operator pushes.
- **Tooling.** `uv --frozen`, pytest with strict markers (`pytest.ini`), new CLI commands under `src/dopemux/commands/` (repo CLAUDE.md). **CI runs Python 3.12.13.** `actions/setup-python` installs 3.11 (`ci-complete.yml:173`), but `uv sync --frozen --extra test --extra services` (`ci-complete.yml:182`) has no `--python`, so uv honors `.python-version` (3.12.13). `requires-python` is `>=3.11,<3.14`. The 184-pass result for `tests/arch` is from the 3.12 repo venv. The CI-equivalent environment (`uv sync --frozen --extra test --extra services`, no `--python`) has not been tried and is the first step of W1. Every new test in this wave must pass there; none may be skipped to get green.
- **Timing (supervisor's call; the operator can override).** Build W1-W5 now. Freeze when all five are committed and their checks pass. Run the one audit after #1482, #1472 and #1483 have merged, so it is not made stale by them. If the operator wants the audit sooner, each later merge costs one re-audit.
- **Write sets are fixed at issuance.** A child that finds it needs a file outside its set stops and returns. Widening a set is a supervisor amendment to the MacroPacket, recorded with the reason (precedent: MACRO-DMX-CMD-REPAIR-001 AMENDMENT-01 and -02).

## 6. Workstreams

All write sets are disjoint. The only shared file is `src/dopemux/cli.py`, and only W3 writes to it.

### W1 - Contract tests in CI

- **Writes:** `.github/workflows/ci-complete.yml` only.
- **Decided:** add a separate pytest step for `tests/arch` inside the existing `🧪 Unit Tests` job, so it inherits that job's required-check status. Use a separate process, like the dope-memory step at `:192-198`, so `tests/arch` collection cannot shadow imports for `tests/unit`. Run it with `--no-cov`, like the other gates.
- **First step:** run `uv run --frozen pytest tests/arch` under the CI sync (`--extra test --extra services`; Python 3.12.13 from `.python-version`) and record the result. If anything fails there that passes in the repo venv, stop and return. Fixing a test is outside W1's write set and needs a supervisor amendment.
- **Consequence to note in the PR:** once #1445 merges, its command drift gate (`tests/arch/test_claude_command_references.py`) runs in CI automatically.

### W2 - ADHD engine MCP repair

- **Writes:** `services/adhd_engine/core/engine.py`; new test `tests/arch/test_adhd_engine_mcp_parity.py`.
- **Decided:**
  - Add `get_energy_level(user_id)`, `get_attention_state(user_id)`, `get_cognitive_load(user_id)` and `assess_task(title, description)` to the real engine. Return the same shapes the fallback returns: an object with `.level` (str) and `.score` (float); an object with `.state` (str); a float; an object with `.dict()`.
  - Read the same state `/api/v1/state` reads: `current_energy_levels` and `current_attention_states` (`core/engine.py:140-141`), with the same defaults (`EnergyLevel.MEDIUM`, `AttentionState.FOCUSED`). `.level` and `.state` are the enum's `.value` string, converted the way `/state` converts them. Load comes from `_calculate_cognitive_load(user_id)` (`:1918`).
  - `assess_task` wraps `assess_task_suitability(user_id, task_data)` (`:384`). Unlike the fallback (`main.py:227-244`, which hard-codes `user_id="default"`), it uses the operator user id from `resolve_operator_user_id()`, as `/state` does. It passes `title` and `description`. Any field the method needs that cannot be derived from the input (the fallback's `complexity_score: 0.5`, `estimated_minutes: 30`) is passed as a documented default and marked in the returned payload, for example `"defaults_used": ["complexity_score", "estimated_minutes"]`, so callers can tell a measured value from a placeholder.
  - `.score` comes from a fixed, documented table over the energy enum. It is not a measurement and the docstring says so.
  - The test lives in `tests/arch/`, so W1 makes CI run it. `services/adhd_engine/tests/` is not run by CI. It has two parts:
    1. **Static parity:** parse `main.py` with `ast`, collect every `engine.<name>(...)` call inside functions decorated `@mcp.tool()`, and assert each name is defined on both the real engine class and the fallback class. This needs no imports, no Redis and no network.
    2. **Behavior:** call each new method on a real-engine instance with seeded state and check the returned shapes and values. This part must also import and pass under the CI environment (Python 3.12.13 via `.python-version`, `--extra services`). If the engine module cannot be imported there, W2 stops and returns; the behavior half is not skipped.
- **Left to the builder:** how to build a real-engine instance offline (the constructor reads settings and creates a PAL client, `core/engine.py:126-137`), and the score table's values.

### W3 - `dopemux adhd status`

- **Writes:** new `src/dopemux/commands/adhd_commands.py`; `src/dopemux/cli.py` (one import and one `cli.add_command` line); new `tests/unit/test_adhd_commands.py`.
- **Decided:**
  - One read-only command, `dopemux adhd status`, with `--json` and `--url` (override).
  - **URL resolution (supervisor's call)**, first match wins: `--url`; `DOPEMUX_ADHD_ENGINE_BASE_URL`; `DOPEMUX_ADHD_ENGINE_PORT`; `ADHD_ENGINE_PORT` (the variable compose uses); the registry's host port for `adhd-engine` (`3025`). No socket probing. This follows the supported way to run the engine (compose via `dopemux`). A directly run engine on `8095` is reached with `--url` or an env var. The existing resolvers in `service_endpoints.py` and `profile_detector.py` are **not** reused, because they probe `5448`/`8095` and never yield `3025`. W4 records them.
  - Two calls, both keyless: `GET /api/v1/state` (`routes.py:1555-1570`) and `GET /health` (`main.py:563`). Do not call per-user routes, which need `X-API-Key` when one is configured (`services/adhd_engine/auth.py:12-40`).
  - **Degraded detection (supervisor's call).** `/health` reports `"mode": "fallback"` when the engine started on its fallback class (`main.py:176-180`). The command reports that as `degraded`. One case cannot be detected: when `/state` itself fails internally it still answers 200 with fixed defaults (`medium`, `focused`, 0, `routes.py:1593-1602`), the same as a healthy answer. Changing that is in `routes.py`, which this wave does not touch. The reference doc states this limit plainly.
  - Accept both response shapes, verified on `feat/pulse-001` at `ee00d3655`: #1472's `/state` returns `energy`, `attention`, `energy_level`, `attention_state`, `session_minutes` and `user_id`; main returns the same without the two aliases. Read the aliases first, then the originals. Tests use literal fixtures of both shapes.
  - Show session minutes only when the engine reports more than 0.
  - Timeout 2 s per call, matching Pulse.
  - **Exit codes (supervisor's call):** 0 ok; 1 unreachable, non-2xx or malformed body; 3 degraded (fallback engine). Code 2 is left to click's usage errors. The message says which case applies. `--json` emits `{"status": "ok" | "degraded" | "unreachable" | "malformed", "url": ..., "url_source": ..., "engine_mode": "normal" | "fallback" | "unknown", ...}`.
- **Left to the builder:** human output layout (one line, plain words, no color dependence); the HTTP client already used by `src/dopemux` and how tests mock it.

### W4 - Service port drift tests

- **Writes:** new `tests/arch/test_service_port_drift.py`; `src/dopemux/config/manager.py`. Not `scripts/dopemux_dashboard.py`, `src/dopemux/ui/service_endpoints.py` or `src/dopemux/profile_detector.py` (see the table below).
- **Comparison rules (supervisor's call):**
  - Compare host ports only. A compose mapping `"127.0.0.1:${VAR:-N}:M"` has host port `N`; resolve `${VAR:-default}` to its default.
  - A compose service with no host `ports:` entry, or with `network_mode`, is "not comparable". The test lists it in its output and does not fail on it.
  - Reuse the compose parsing in `tests/arch/test_registry_compose_alignment.py` if it fits; otherwise put one small parser in the new test.
  - An exception entry that no longer matches anything fails the test. Every file the table names is tracked, so a missing file means a stale entry.
- **Gaps to cover.** These are not checked by anything today, per a read-only sweep of `origin/main`:
  1. Registry versus catalog for services present in both.
  2. Registry versus compose for services *not* marked `enabled_in_smoke`. The existing alignment test covers only smoke-enabled services (`tests/arch/test_registry_compose_alignment.py:46-49`).
  3. Hard-coded `host:port` literals in scripts versus the registry: `.claude/statusline.sh`, `scripts/dopemux_dashboard.py`, `mcp_server_health_report.sh`, `scripts/mcp_health_check.sh`, and the `config/manager.py` default.
- **Known differences today, and what to do with each:**

| Where | Difference | Verified by | Action |
|---|---|---|---|
| `config/manager.py:192-202, 612-624` (Dope layout defaults) | `adhd_engine_url` `3008` (registry `3025`), `leantime_url` `3007` (registry `8080`), `serena_url` `3010` (registry `3006`; `3010` is dope-context). No reader in `src/`. | supervisor | Fix all three to the registry ports. `conport_url` `3009` (that is gpt-researcher) and `activity_capture_url` `3006` have no unambiguous registry service: follow-up, not a test exception. |
| `scripts/dopemux_dashboard.py` (21 lines) | `8095` (container port), `8005` and `8003` (in no registry or compose), and calls to routes the engine does not serve (`/api/v1/break/start`, a websocket stream) | supervisor | Exception per port plus a "retire or repair this script" follow-up. Changing `8095` to `3025` would leave it just as broken. Changed after plan recon; the earlier draft said "fix to 3025". |
| `src/dopemux/ui/service_endpoints.py:117`, `src/dopemux/profile_detector.py:379-384` | Resolvers probe `5448` and `8095` as bare numbers; neither is the compose host port | supervisor | Follow-up only. The literal-URL rule does not see bare numbers, and changing them changes the live dashboard. |
| `.claude/statusline.sh:224-230` | Probes `localhost:3009` as task-orchestrator; `3009` is `gptr-mcp` | supervisor | Follow-up only. `3009` is a valid port for another service, so the unknown-port rule does not flag it, and the statusline is out of scope. |
| `mcp_server_health_report.sh:168` | Probes pal at `/mcp`; the catalog says pal's health URL is `/health` | sweep (not spot-checked) | Follow-up. This wave checks ports, not paths. |
| `services/registry.yaml:152-156` vs catalog `:616-620` | task-orchestrator `8000` vs `7890` | supervisor | Exception: two processes share the name (S2). |
| registry `dopecon-bridge-alt` (`:68-72`) vs compose | Registry host port `3000`; its `compose_service_name` is `dopecon-bridge`, which publishes only `3016` | supervisor | Exception plus follow-up: the alt entry describes a port compose never publishes. |

- **Decided:** exceptions live in the test file as a table. Each entry has the file, the value, a one-line reason and a follow-up reference. The test fails on any difference that is not in the table, and also on a table entry that no longer matches anything, so stale exceptions are removed.
- **Required proof:** a mutation check. Change one port in a temporary copy, run the test, and show it fails. Record the output.

### W5 - Docs and agent docs

- **Writes:**
  - one reference page for `dopemux adhd status` and one for the CI contract gate and port drift test, both under `docs/03-reference/`;
  - index entries in `docs/00-MASTER-INDEX.md` and `docs/docs_index.yaml`;
  - agent docs: one entry each in `.claude/claude.md` ("Commands & Environment": `tests/arch` now runs in CI, run it before pushing contract edits; `dopemux adhd status` is the way to read engine state) and in `AGENTS.md` (same two facts, kept in sync).
- **Decided:** the docs say plainly what is not covered: per-user routes, break and focus verbs, engine test suite health, the MCP manifest.
- **Merge note:** PR #1484 also edits `AGENTS.md` and `.claude/claude.md`. Keep edits to separate sections so the second merge is a clean update.

### W0 - This design

Supervisor-owned. Committed on this branch so the one audit covers it.

## 7. Routing (proposed, confirmed in the MacroPacket)

| Workstream | Runner / model | Why |
|---|---|---|
| W1 | Claude Code / Haiku | One YAML step plus one validation run. Escalate to Sonnet if the CI-equivalent run fails. |
| W2 | Claude Code / Sonnet | Engine code plus an AST test. Moderate judgment. |
| W3 | Claude Code / Sonnet | New CLI command and tests. |
| W4 | Claude Code / Sonnet | Test design plus per-difference evidence. Escalate to Opus if exception decisions get contentious. |
| W5 | Claude Code / Sonnet | Docs from the merged code. Runs last. |
| Final audit | Operator-approved route | Independent of Claude. |

Order: W1-W4 can run in parallel (disjoint files). W5 starts after W1-W4 are committed. Freeze, then one audit.

## 8. Validation summary

| Workstream | Deterministic checks |
|---|---|
| W1 | CI-equivalent run of `tests/arch`; workflow syntax hook; the PR's own CI run. |
| W2 | New parity test passes; it fails when one of the four methods is removed (mutation check). |
| W3 | Unit tests for ok, degraded, unreachable, non-2xx, malformed body, both response shapes, `--json`, and each URL-resolution step in order. A manual run against a live engine is `NOT_RUN` unless the operator runs one. |
| W4 | Drift test passes on the branch; mutation check fails as expected; stale-exception check works. |
| W5 | Frontmatter guard, docs hygiene, markdownlint (`markdownlint -c .markdownlint.jsonc`), relative-link check. |
| All | `make lint` on touched Python, `make type-check` where `src/` changes, `validate_change_contract.py` lane report. |

Results are reported as PASS, FAIL or NOT_RUN. NOT_RUN is never folded into PASS.

## 9. Calls made after the builder check

An independent reader checked this design before approval and raised eight questions. Q7 (the shape of #1472's `/state`) was answered from the branch. The rest were settled as the supervisor's calls. Each is marked in the text above; check these first:

1. `dopemux adhd status` resolves env, then the registry's compose host port `3025`, with no socket probing; the existing resolvers are not reused (W3).
2. It also calls `/health` and reports `degraded` with exit code 3 for the fallback engine. The `/state` error path stays undetectable and is documented (W3).
3. The real engine's `assess_task` uses the operator user id and marks placeholder inputs in its output; `.score` is a documented table, not a measurement (W2).
4. `scripts/dopemux_dashboard.py` is too stale to fix by changing one port, so it gets per-port exceptions and a follow-up; `manager.py`'s Dope layout defaults are fixed where the registry service is unambiguous (W4; revised during plan recon).
5. Port comparison is host-port only; services without host ports are listed as not comparable; stale exceptions fail (W4).
6. CI runs Python 3.12.13 (uv honors `.python-version`); every new test must pass there with no skips, and a child that needs a file outside its write set stops for an amendment (section 5).
7. Build now, audit after #1482, #1472 and #1483 merge (section 5).

## 10. Follow-ups this wave creates (not done here)

- P2 break-writer endpoint and `dopemux adhd break|focus|ack`, after #1472 merges.
- Register the engine's MCP server in the catalog and `.mcp.json`.
- Triage `services/adhd_engine/tests/` and wire it into CI.
- Fix `.claude/statusline.sh`'s orchestrator probe.
- Retire `services/adhd_engine/cli/adhd.py`.
- Resolve the task-orchestrator name collision (S2).
- Proof-only closure mode for clean merges of `main` (operator decision).
- Retire or repair `scripts/dopemux_dashboard.py`.
- Resolver defaults `5448`/`8095` in `service_endpoints.py` and `profile_detector.py`; `manager.py` `conport_url` and `activity_capture_url`; pal health path in `mcp_server_health_report.sh`.
