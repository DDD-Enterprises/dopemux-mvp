# Dopemux Development Platform

**Project**: Python-based ADHD-optimized development platform
**Architecture**: Python CLI (`src/dopemux/`) + services under `services/<name>/` + MCP fleet (task-orchestrator, ConPort, dope-memory, dope-context)
**Mode**: PLAN/ACT-aware with modular authority boundaries
**Canonical repo rules**: `AGENTS.md` (not auto-loaded by Claude Code; read it for packet, governance and MCP work)

<!-- CONTROL_TOWER_ENTRY_BEGIN -->
## Control Tower Supervision

For supervised engineering packets, follow [Control Tower Packet Workflow](../AGENTS.md#control-tower-packet-workflow).
Read the installed kit contracts and project configuration through that entry point.
Read `.claude/PROJECT_INSTRUCTIONS.md` and `.claude/PRIMER.md` first; this file adds project context.
<!-- CONTROL_TOWER_ENTRY_END -->

## 🎯 Governance Principles

**Doctrine**: truth over fluency, inspect before editing, minimal correct change, deterministic systems first, fail closed when evidence is missing. This module elaborates the same Truth Order / proof-and-finality regime that [AGENTS.md](../AGENTS.md) mandates for Codex — keep both files in sync.

**Default workflow**: `inspect → analyze → trace → plan → challenge → implement minimally → validate → precommit → summarize truthfully`.

**Mandatory hierarchy**:

```text
OPERATOR
 -> CONTROL TOWER SUPERVISOR
 -> SUPERVISOR MACROPACKET
 -> TEAM LEAD
 -> MULTIPLE CHILD WORKSTREAMS
 -> AGGREGATE RETURN
```

Every non-trivial design, implementation, investigation, repair, qualification,
finality, or repo-changing execution request starts with one supervisor-issued
MacroPacket containing at least two genuine workstreams; never invent ceremonial
work. Child Task Packets remain scoped execution law. Authority, risk lane, write
allowlist, rollback, route, proof, and audit obligations are non-transferable.

The team lead coordinates legal children with one mutating implementer per
workstream. Parallel mutation requires proven-disjoint physical and semantic
writes, canonical writers, rollback, custody, and current workflow legality;
otherwise serialize explicitly. The team lead cannot widen or transfer authority,
lower risk, waive proof or audit, override Task Orchestrator, create operator
authority, merge, activate, self-certify acceptance, or independently audit work
it supervised. Continue unaffected legal children unless a global stop applies;
return at actual authority/risk/custody/writer/rollback/audit/activation conflicts,
no legal route, FAIL/NEEDS_SUPERVISOR, or an operator gate.

Before every MacroPacket or child Task Packet, emit TP_ROUTE with runner, exact
model, effort, and why. Exact runtime runner/model/effort is ExecutionBinding,
never DCP RouteDecision. DCP owns policy/classification/context/route eligibility;
Task Orchestrator owns workflow legality; Universal Router ranks eligible routes;
Audit Broker owns auditor certification/dispatch; Dopetask executes separately
authorized effects. No layer may widen upstream authority.

Use shell/local for deterministic facts. Settle CI and reviews before substantive
freeze and one final independent L2/L3 audit; no intermediate model audits. Later
semantic changes invalidate that audit. Proof-only successors do not automatically
require re-audit; reuse valid subject-bound evidence and reharvest affected facts.
Return one aggregate preserving child states and subjects, with authority NONE;
aggregation cannot mint PASS/READY/DONE. Autonomous next-MacroPacket dispatch
remains separately gated. Never merge, mark ready, close, force-push, rewrite
history, alter credentials or permissions, activate, publish, migrate, mutate
production, or accept security residual risk without required explicit operator authority.

**Non-negotiables**:
- **Authority order**: latest user instruction → [AGENTS.md](../AGENTS.md) / Task Packet → runtime code → schemas → tests → config → docs → assumptions. Runtime outranks docs. Mark unresolved authority as `UNKNOWN`.
- **PAL workflows and audit budgets**: governed by [AGENTS.md §5](../AGENTS.md). Use deterministic validation between slices; do not add intermediate model audits or restate chains here.
- **Confidence states**: `exploring / low / medium / high / certain`. `certain` requires direct evidence; final confidence for repo-changing work must be `VERIFIED` per [AGENTS.md §9](../AGENTS.md).
- **Validation buckets**: report **PASS / FAIL / NOT_RUN** — never collapse `NOT_RUN` into `PASS`.
- **Contract-sensitive surfaces** (schemas, migrations, event payloads, MCP manifests, hooks, proof bundles) require canonical-writer inspection before editing.
- **Security**: least privilege, fail-closed, never expose secrets, strict tool isolation in MCP/agent flows.

**Required final response shape**: Change Summary · Authority Used · Analysis Performed · Validation Performed (PASS/FAIL/NOT_RUN) · Remaining Uncertainty · Files Touched · Git State · Rollback Plan · Requested Next Step. For repo-changing work, also produce the proof bundle from [AGENTS.md §9](../AGENTS.md).

**Cost-first delegation**: follow [AGENTS.md §5](../AGENTS.md): cheapest adequate qualified model, lowest sufficient supported effort, explicit bounded ownership/validation/stop conditions. Pin cheaper children; avoid inheriting expensive supervisors. Preserve user/packet restrictions and no-fallback gates; record escalation reasons and unknown actual identity/availability. YAML is advisory; Codex review never formal embedded audit.

**Full doctrine**: [.claude/modules/shared/governance-principles.md](modules/shared/governance-principles.md).

## ⚙️ Commands & Environment

Python 3.12 via mise; repo venv at `.venv` (hooks prefer it). The Makefile is the canonical runner (uv, frozen lockfile).

```bash
make test              # uv run --frozen --extra test pytest tests
make test-fast         # unit only, --maxfail=1, no coverage
make test-integration  # syncs --extra services first
make lint              # flake8 — bare tool names; activate .venv first
make format            # black + isort
make type-check        # mypy src/
```

- `pytest.ini` overrides `[tool.pytest.ini_options]` in pyproject.toml (pytest warns and ignores the latter) — edit `pytest.ini`; markers are strict.
- CLI: `cli.py` (~6.5k lines) registers the `commands/*.py` groups and still hosts 27 legacy inline commands (26 `@cli.command` + 1 `@click.command`) — put new commands in `src/dopemux/commands/`.
- Personas in `.claude/personas/` and `.claude/agents/*.md` are SHA-256-pinned by `proof/CCAR-002/SOURCE_MANIFEST.json`; editing one makes `scripts/commandcode_router/build_normalized_catalog.py` exit 1 and fails `tests/commandcode_router/test_normalized_catalog.py`. Precedent (#1388, #1389): re-pin only the changed entries' `sha256` in a separate `proof(ccar-002): re-pin …` commit in the same PR, then run the builder's `--check`.

## 🧠 Core ADHD Principles

- **Context Preservation**: Manual `dopemux save` and `/save` support context capture; Stop hooks can perform best-effort saves when the ADHD Engine is running. A background 30-second save loop is planned/configured behavior, not observed Claude runtime support.
- **Gentle Guidance**: Encouraging, supportive language with clear next steps
- **Progressive Disclosure**: Essential info first, details on request
- **Decision Reduction**: Maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Use operator-managed 25-minute checkpoints with visual progress; automatic timer enforcement is not observed runtime support.

## Task & memory routing (real tools)

- Workflow items: task-orchestrator via `/dx:next`, `/dx:start`, `/dx:complete`, `/dx:context` (see `.claude/commands/dx/` for the rest: `block`, `blocked`, `cancel`, `depends`, `note`, `notes`, `preview`, `reopen`, `resume`, `search`, `tree`).
- Decisions/progress: ConPort live tools `log_decision`, `get_decisions`, `log_progress`, `get_progress`, `get_context`, `update_context`, `search_content`, `save_custom_data` (surface captured in `mcp_tool_surfaces.json`).
- Chronicle: dope-memory `memory_recap` / `memory_search`. Code/docs retrieval: dope-context `search_code` / `docs_search`. Symbols and navigation: Serena.
- `~/.claude/MCP_*.md` are NOT auto-loaded; live tool names are in `mcp_tool_surfaces.json`.
- Session context capture: `/save` or `dopemux save`.

## 🎯 Mode-Aware Operation

**PLAN Mode**: Architecture, sprint planning, story breakdown
- Load PM plane modules + decision modules
- Focus on strategic thinking and synthesis
- Log decisions with rationale in ConPort

**ACT Mode**: Implementation, debugging, testing
- Load cognitive plane + execution modules
- Focus on concrete changes and linking artifacts
- Track progress and create deliverables

**Mode Detection**: Automatic based on activity type and user context

## 🚀 Integration Points

## 🪝 Lifecycle Hooks

The project's `.claude/settings.json` registers 11 lifecycle hooks (`SessionStart`, `SubagentStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `Stop`, `SubagentStop`, `PreCompact`, `SessionEnd`), all dispatched through one entry point: `.claude/hooks/run_native_hooks.sh`, which runs `src/dopemux/claude/native_hooks.py` with the repo `.venv` interpreter (falling back to `python3`). A bare `python3` can resolve to an interpreter without the repo's dependencies (e.g. no `pydantic`), making every hook fail. Individual hook scripts live under `.claude/hooks/` (e.g., `check_energy.sh`, `log_progress.sh`, `save_context.sh`, `track_file_edit.sh`, `prompt_analyzer.py`, `session_lifecycle.py`).

**Orchestrator-coordination hooks** (ported from upstream `claude-plugins/task-orchestrator`, TP-CS-101 / Path B — see [docs/03-reference/orchestrator-integration/plugin-hooks-port.md](../docs/03-reference/orchestrator-integration/plugin-hooks-port.md)): available as `.claude/hooks/orchestrator_session_start.py` (SessionStart context inject), `orchestrator_post_edit_nudge.py` (PostToolUse edit nudge), `orchestrator_subagent_protocol.py` (SubagentStart agent-owned-phase protocol for implementation subagents), and `orchestrator_enforcement.py` (PreToolUse actor-attribution enforcement [dormant until `actor_authentication.enabled`], skill-invocation enforcement, and EnterPlanMode/ExitPlanMode guidance). These route through `native_hooks.py` when invoked and fail open (no-op) when their helpers or config are absent.

**DCP/MCP hooks**: four hooks that wire the DCP read-only facade and MCP server health into the normal edit workflow — all fail-open, all with per-session cooldown caches under `.claude/`:
- **H1** `dcp_surface_guard.py` — PreToolUse hard-deny for DCP-RED-MERGE-SEAM-0001 paths; one-time advisory for contract surfaces (schemas, route_manifest, mcp_catalog, .mcp.json).
- **H2** `dcp_denylist_nudge.py` — PostToolUse scan of facade adapter edits for denied-route tokens loaded at runtime from `route_manifest.py` (no drift); advisory names token + line.
- **H3** `mcp_health_probe.py` — SessionStart 15-min-cached MCP server health snapshot; detects leaked task-orchestrator containers (SQLite-contention risk) and unreachable http/sse servers.
- **H4** `proof_tracking_guard.py` — PostToolUse advisory when a TRACK-tier proof artifact (`PROOF.json`, `SUMMARY.md`, etc.) is gitignored or untracked; prompts `git add -f`.

**Observed runtime support**: Settings dispatch all lifecycle events through `run_native_hooks.sh` → `native_hooks.py`; hook scripts provide best-effort context save on Stop, energy warnings before complex tools, and progress/edit event signals.

**Planned/specification behavior**: focus-session timers, periodic save loops, automatic break prompts, and forced hyperfocus pauses are not proven wired in the observed Claude runtime.

Hooks run outside the model's turn. If you want to change hook behavior, edit the dispatcher or `.claude/hooks/` scripts; routine settings tweaks should go through the `update-config` skill rather than hand-editing `settings.json`. Hook output reaches the model as `<user-prompt-submit-hook>` blocks — treat as user input.

## 🧩 Plugin Skills (auto-use)

Invoke these without being asked when the trigger fires. Repo doctrine overrides any skill step that conflicts with it. Full matrix and overrides: [.claude/modules/shared/plugin-integration.md](modules/shared/plugin-integration.md).

- Bug / failing test → `superpowers:systematic-debugging` · feature or fix → `superpowers:test-driven-development` · before any done/commit/PR claim → `superpowers:verification-before-completion` · multi-step spec → `superpowers:writing-plans`
- Finishing a branch → `superpowers:finishing-a-development-branch`, **PR route only** (never local-merge to `main`). Worktrees go in `<repo>/.worktrees/`.
- Second opinion / stuck → `codex:rescue`, `/codex:review`. **Codex is advisory, never the §9.1 auditor.** New UI → `frontend-design:frontend-design`.
- GHA failure → `superdevflow:gha` · session handoff → `superdevflow:handoff` (plus `/save`) · CLAUDE.md upkeep → `claude-md-management:revise-claude-md` (manual).
- After editing Python → `LSP` tool (pyright-lsp) for hover/diagnostics. Serena stays the navigation and symbol-edit authority. Server install: `uv tool install 'pyright[nodejs]'`.
- Parallel/subagent skills stay inside AGENTS.md §5 budgets. Enablement is pinned in `.claude/settings.json` `enabledPlugins`. `claude-mem`, `caveman`, `ck`, `hookify`, and `feature-dev` are uninstalled; `crewmarshal` and the other off-scope synced plugins are disabled.

## 📚 Detailed Information Locations

When you need comprehensive details, refer to:

**Governance Principles**: `.claude/modules/shared/governance-principles.md` (Truth Order, PAL workflow rules, canonical writers, contract-sensitive surfaces, validation policy, required response structure)
**SuperClaude Workflows**: `.claude/modules/shared/superclaude-workflows.md` (integration patterns, command selection, ADHD sessions)
**Task Management**: `.claude/modules/superclaude-integration.md`, `.claude/modules/custom-commands.md`
**Cognitive Plane**: `.claude/modules/cognitive-plane/` (serena-lsp.md, conport-memory.md)
**ADHD Engine**: `.claude/modules/shared/adhd-patterns.md` (sessions, energy tracking, break management; separates observed support from planned automation)
**Shared Systems**: `.claude/modules/shared/` (sprint.md, event-patterns.md, superclaude-workflows.md)
**Filesystem Organization**: `docs/03-reference/filesystem-guide.md` (directory structure, file placement rules)
**Plugins**: `.claude/modules/shared/plugin-integration.md` (installed plugins, auto-use triggers, doctrine overrides, do-not-enable list)
**Harness features** (Plan mode, advisor, /loop, ToolSearch, Skill): `~/.claude/MODES_AND_TOOLS.md`

## Repo gotchas

- dope-context source is `services/dope-context/src/` (not `src/`); service code lives under `services/<name>/`.
- `gh pr view --json` has no `reviewThreads` or `merged` field; use `gh api graphql`, or `--json state,mergedAt`. Do not `sleep` in Bash to poll CI (the harness blocks it); use Monitor or `/loop`.
- Secret scan tool is gitleaks (installed). `detect-secrets` and `semgrep` CLIs are not installed.
- PR Steward "final readiness" and CodeQL fail until the embedded-audit proof is pinned to the PR head (AGENTS.md §9.1): expected, not a regression.

## 🔌 MCP Transport and Setup Rules (see AGENTS.md §12)

**Do not change transport types without reading server source.** The correct types are:

| Server | `type` | Protocol |
|---|---|---|
| `conport` | `sse` | SSE — `GET /sse` |
| `dope-memory`, `task-orchestrator` | `http` | Streamable HTTP — `POST /mcp` |
| `pal`, `serena`, `dope-context` | `http` | Streamable HTTP — `POST /mcp` |

A `406 Not Acceptable: Client must accept text/event-stream` on `GET /mcp` is
**correct Streamable HTTP behaviour** — not evidence the server is SSE. Fix: POST with JSON-RPC.

**Setting up MCP in a new repo**:
```bash
cd ~/code/target-repo && dopemux mcp init
source .envrc.dopemux-mcp && dopemux mcp doctor
```

**Debug sequence**: source envrc → `dopemux mcp doctor` → curl probe → tail docker logs
→ `./mcp_server_health_report.sh`

**Sharing classes today**: `postgres-age`, `redis-primary`, `qdrant`, `dope-context`, `litellm`,
`gpt-researcher`, `exa`, `desktop-commander`, bridges are host singletons (one process, shared).
`redis-events` is OBSERVED **host-singleton today and noncompliant** for multi-project use (global container,
no stream isolation; its events get promoted into canonical work_log) — the REQUIRED target is project-scoped
(design §10.4, gate P-21, not yet implemented). `conport`, `dope-memory`, `serena`
are still **worktree-scoped** (one container per worktree) pending identity gates — expect N worktrees to
cost 3N containers until those land; ConPort's ruled end-state is **project-scoped**, never host-singleton
(§10.3). Never start fleet services outside `dopemux mcp` (no raw `docker compose up` / `docker run`). Full
sharing-class table + command surface (`init`/`start`/`stop`/`doctor` implemented;
`reconcile`/`adopt`/`migrate`/`switch-project` PLANNED — `switch-project` transitional only): AGENTS.md §12.6
and `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md` (ACCEPTED with supervisor rulings 2026-07-28).

**Key docs**:
- [`docs/02-how-to/mcp-setup-other-repos.md`](../docs/02-how-to/mcp-setup-other-repos.md) — user guide for other projects
- [`docs/02-how-to/mcp-transport-and-port-bugs.md`](../docs/02-how-to/mcp-transport-and-port-bugs.md) — bug record + correct analysis
- `AGENTS.md §12` — canonical MCP rules for all agents

### M0 supervised contract convergence

For supervised execution, `schemas/governed_execution/manifest.v1.json` identifies
GEC v2 as the sole current artifact contract. CT v1 schemas are historical,
read-only compatibility; they cannot create current bindings or packages.
ExecutionBinding and WriterCustody constrain and record evidence, never grant
execution authority. Local CT state is technical/noncanonical. PR Steward retains
readiness classification; automatic next-action dispatch and M1-M7 are absent.
