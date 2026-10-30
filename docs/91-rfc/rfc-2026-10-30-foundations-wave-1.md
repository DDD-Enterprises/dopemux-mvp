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
- There is no `dopemux adhd` command. The only CLI default for the engine URL, `src/dopemux/config/manager.py:200` and `:621`, says `http://localhost:3008`; the registry says host port `3025` (`services/registry.yaml:183-186`). Nothing in `src/` reads that default.
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
- **Tooling.** Python 3.12, `uv --frozen`, pytest with strict markers (`pytest.ini`), new CLI commands under `src/dopemux/commands/` (repo CLAUDE.md). `tests/arch` already runs green in the repo venv; the CI-equivalent environment (`uv sync --frozen --extra test --extra services`) has not been tried and is the first step of W1.

## 6. Workstreams

All write sets are disjoint. The only shared file is `src/dopemux/cli.py`, and only W3 writes to it.

### W1 - Contract tests in CI

- **Writes:** `.github/workflows/ci-complete.yml` only.
- **Decided:** add a separate pytest step for `tests/arch` inside the existing `🧪 Unit Tests` job, so it inherits that job's required-check status. Use a separate process, like the dope-memory step at `:192-198`, so `tests/arch` collection cannot shadow imports for `tests/unit`. Run it with `--no-cov`, like the other gates.
- **First step:** run `uv run --frozen pytest tests/arch` in a CI-equivalent sync and record the result. If anything fails there that passes in the repo venv, stop and report before writing the step.
- **Consequence to note in the PR:** once #1445 merges, its command drift gate (`tests/arch/test_claude_command_references.py`) runs in CI automatically.

### W2 - ADHD engine MCP repair

- **Writes:** `services/adhd_engine/core/engine.py`; new test `tests/arch/test_adhd_engine_mcp_parity.py`.
- **Decided:**
  - Add `get_energy_level(user_id)`, `get_attention_state(user_id)`, `get_cognitive_load(user_id)` and `assess_task(title, description)` to the real engine. Return the same shapes the fallback returns: an object with `.level` (str) and `.score` (float); an object with `.state` (str); a float; an object with `.dict()`.
  - Read the same state `/api/v1/state` reads: `current_energy_levels` and `current_attention_states` (`core/engine.py:140-141`), with the same defaults (`EnergyLevel.MEDIUM`, `AttentionState.FOCUSED`). Load comes from `_calculate_cognitive_load(user_id)` (`:1918`). `assess_task` wraps `assess_task_suitability` (`:384`) the way the fallback does (`main.py:227-244`).
  - The test lives in `tests/arch/`, so W1 makes CI run it. `services/adhd_engine/tests/` is not run by CI. It has two parts:
    1. **Static parity:** parse `main.py` with `ast`, collect every `engine.<name>(...)` call inside functions decorated `@mcp.tool()`, and assert each name is defined on both the real engine class and the fallback class. This needs no imports, no Redis and no network.
    2. **Behavior:** call each new method on a real-engine instance with seeded state and check the returned shapes and values.
- **Left to the builder:** how to build a real-engine instance offline (the constructor reads settings and creates a PAL client, `core/engine.py:126-137`); whether `.score` comes from a fixed table over the energy enum or stays at the fallback's constant 0.5. The choice must be stated in a docstring and tested, and must not claim more precision than the engine has.

### W3 - `dopemux adhd status`

- **Writes:** new `src/dopemux/commands/adhd_commands.py`; `src/dopemux/cli.py` (one import and one `cli.add_command` line); new `tests/unit/test_adhd_commands.py`.
- **Decided:**
  - One read-only command, `dopemux adhd status`, with `--json` and `--url` (override).
  - Read `GET <engine>/api/v1/state`, which needs no API key (`routes.py:1555-1570`). Do not call per-user routes, which need `X-API-Key` when one is configured (`services/adhd_engine/auth.py:12-40`).
  - Resolve the engine URL the way the dashboard does (`src/dopemux/ui/service_endpoints.py:15`, `:177`), which follows the registry. Do not use the `3008` default in `config/manager.py`.
  - Accept both key sets: `energy_level` / `attention_state` (added by #1472) first, then `energy` / `attention` (main). The command must work before and after #1472 merges.
  - Show session minutes only when the engine reports more than 0.
  - Timeout 2 s, matching Pulse.
  - Exit 0 when the state is read and well-formed; exit 1 when the engine is unreachable, returns non-2xx, or the body is malformed. The message says which. `--json` emits `{"status": "ok" | "unreachable" | "malformed", "url": ..., ...}`.
- **Left to the builder:** human output layout (one line, plain words, no color dependence); the HTTP client already used by `src/dopemux` and how tests mock it.

### W4 - Service port drift tests

- **Writes:** new `tests/arch/test_service_port_drift.py`; `src/dopemux/config/manager.py`; `scripts/dopemux_dashboard.py` only if W4's evidence supports a fix (see below).
- **Gaps to cover.** These are not checked by anything today, per a read-only sweep of `origin/main`:
  1. Registry versus catalog for services present in both.
  2. Registry versus compose for services *not* marked `enabled_in_smoke`. The existing alignment test covers only smoke-enabled services (`tests/arch/test_registry_compose_alignment.py:46-49`).
  3. Hard-coded `host:port` literals in scripts versus the registry: `.claude/statusline.sh`, `scripts/dopemux_dashboard.py`, `mcp_server_health_report.sh`, `scripts/mcp_health_check.sh`, and the `config/manager.py` default.
- **Known differences today, and what to do with each:**

| Where | Difference | Verified by | Action |
|---|---|---|---|
| `config/manager.py:200,621` | ADHD engine default `3008`; registry `3025` | supervisor | Fix to `3025`. No reader in `src/`. |
| `scripts/dopemux_dashboard.py:66-72` | ADHD engine on `8095` (container port); host port is `3025` | supervisor | Fix if the script runs on the host; exception with reason if it runs in a container. Builder decides from how it is launched. |
| `scripts/dopemux_dashboard.py:74` | ConPort on `8005`, in neither registry nor compose | sweep (not spot-checked) | Exception with follow-up unless the correct port is unambiguous. |
| `.claude/statusline.sh:224-230` | Probes `localhost:3009` as task-orchestrator; `3009` is `gptr-mcp` | supervisor | Exception plus follow-up. The statusline is out of scope (non-goals). |
| `mcp_server_health_report.sh:168` | Probes pal at `/mcp`; the catalog says pal's health URL is `/health` | sweep (not spot-checked) | Builder verifies, then fixes or adds an exception. |
| `services/registry.yaml:152-156` vs catalog `:616-620` | task-orchestrator `8000` vs `7890` | supervisor | Exception: two processes share the name (S2). |
| registry `dopecon-bridge-alt` vs compose | `3000` vs `3016` | sweep (not spot-checked) | Builder verifies, then fixes or adds an exception. |

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
| W3 | Unit tests for ok, unreachable, non-2xx, malformed body, both key sets, `--json` and `--url`. A manual run against a live engine is `NOT_RUN` unless the operator runs one. |
| W4 | Drift test passes on the branch; mutation check fails as expected; stale-exception check works. |
| W5 | Frontmatter guard, docs hygiene, markdownlint (`markdownlint -c .markdownlint.jsonc`), relative-link check. |
| All | `make lint` on touched Python, `make type-check` where `src/` changes, `validate_change_contract.py` lane report. |

Results are reported as PASS, FAIL or NOT_RUN. NOT_RUN is never folded into PASS.

## 9. Follow-ups this wave creates (not done here)

- P2 break-writer endpoint and `dopemux adhd break|focus|ack`, after #1472 merges.
- Register the engine's MCP server in the catalog and `.mcp.json`.
- Triage `services/adhd_engine/tests/` and wire it into CI.
- Fix `.claude/statusline.sh`'s orchestrator probe.
- Retire `services/adhd_engine/cli/adhd.py`.
- Resolve the task-orchestrator name collision (S2).
- Proof-only closure mode for clean merges of `main` (operator decision).
