# Memory Trinity Supervisor Audit

**Packet**: TP-DMX-MEMORY-TRINITY-001  
**Series**: DMX-MEMORY-TRINITY  
**Date**: 2026-06-19  
**Auditor**: Codex (read-only local audit)  
**Repo**: DDD-Enterprises/dopemux-mvp  
**Branch**: `fix/mcp-server-build-failures`  
**HEAD**: `a1690402b86f9304efb4da5068c03118239c1b4e`  
**PR**: https://github.com/DDD-Enterprises/dopemux-mvp/pull/939 (not merged to `main`)

## Verdict: PARTIAL

Slice 001 deliverables **PASS on this branch** (ADR law, routing card, command drift fix, validator). Full operator readiness is **not PASS**: per-worktree MCP doctor fails (port drift), skills are not installed under `.claude/skills/` or `.github/skills/`, and DCP facade dope-context transport remains BLOCKED. Against `origin/main` alone, required artifacts are **FAIL** (not merged).

## Summary

- Four Memory Trinity ADRs are **accepted**; `AGENTS.md` §6 and `memory-trinity-routing.md` align with ADR object classes.
- **dope-context** runtime healthy on `127.0.0.1:3010`; MCP `initialize` returns HTTP 200 with required `Accept` header; singleton present in `~/.claude.json`.
- `scripts/validate_memory_command_refs.py` exits **0** — no forbidden OpenMemory/Mem0/memory_bank command drift in active bodies.
- `dopemux mcp doctor` exits **1**: worktree `.envrc.dopemux-mcp` expects `:3039`/`:3054` but running containers bind `:3005`/`:3020`.
- Skills inventory **partial**: 20 templates pass frontmatter; `tm:*` count is 0; `.claude/skills/` and `.github/skills/` are absent (sync path documented, not executed).
- `origin/main` lacks `memory-trinity-routing.md` and `validate_memory_command_refs.py` — supervisor GitHub-only preflight against `main` correctly **FAILs** until PR #939 merges.

## Scope note (branch vs main)

| Scope | Verdict | Rationale |
|-------|---------|-----------|
| Local branch `fix/mcp-server-build-failures` | **PARTIAL** | Slice 001 source deliverables present; runtime doctor + skills install gaps remain |
| `origin/main` (GitHub preflight only) | **FAIL** | Required routing module and validator absent on `main` |

## Checklist results (A–F)

| ID | Section | Result | Evidence |
|----|---------|--------|----------|
| A1 | Four ADRs `status: accepted` + body Accepted | **PASS** | `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md:11,25`; child ADRs conport/dope-memory/dope-context lines 11,25–26 |
| A2 | `AGENTS.md` §6 cites Memory Trinity | **PASS** | `AGENTS.md:78–86` |
| A3 | `memory-trinity-routing.md` exists, matches ADR classes | **PASS** (branch) / **FAIL** (`main`) | `.claude/modules/shared/memory-trinity-routing.md:7–37`; `git show origin/main:...` fatal |
| A4 | `authority-matrix.md` lists Trinity planes, not Leantime as task authority | **PASS** | `.claude/modules/coordination/authority-matrix.md:14–16`; Leantime removed `:206` |
| B1 | `mcp-dope-context` healthy on `127.0.0.1:3010` | **PASS** | `docker ps`: `mcp-dope-context Up 2 hours (healthy) 127.0.0.1:3010->3010/tcp` |
| B2 | MCP `initialize` with `Accept: application/json, text/event-stream` | **PASS** | curl HTTP 200; SSE `serverInfo.name=dope-context` |
| B3 | `dope-context` in `~/.claude.json` singleton | **PASS** | `~/.claude.json` → `http://localhost:3010/mcp` |
| B4 | Per-worktree `.mcp.json` has conport, dope-memory, task-orchestrator | **PASS** | `.mcp.json:3–33` |
| B5 | `dopemux mcp doctor` per-server PASS/FAIL | **FAIL** | exit 1: conport `:3039`, dope-memory `:3054` not listening; containers on `:3005`/`:3020` |
| C1 | `validate_memory_command_refs.py` exit 0 | **PASS** (branch) / **FAIL** (`main`) | exit 0; script absent on `origin/main` |
| C2 | `/decision`, `/caveat`, `/followup`, `/scratch` → ConPort | **PASS** | `.claude/commands/decision.md:3`; `caveat.md:3`; `followup.md:3`; `scratch.md:3` |
| C3 | `/ctx:search-here`, `/ctx:index-search` → dope-context + frontmatter | **PASS** | `.claude/commands/ctx/search-here.md:4–9`; `ctx/index-search.md:6–10` |
| C4 | `/get-decisions`, `/search-decisions` unchanged (ConPort) | **PASS** | `get-decisions.md:2`; `search-decisions.md:2` |
| D1 | `templates/skills/**/SKILL.md` frontmatter | **PASS** | `scripts/validate_skill_frontmatter.py` exit 0 (20 skills) |
| D2 | `.github/skills/` or `.claude/skills/` populated OR sync documented | **PARTIAL** | OR-gate: `sync_repo_skills.py:61-76` + `docs_index.yaml:175` document path; dirs **ABSENT** (sync not run); dry-run proves `.claude/skills` targets — operator readiness still FAIL |
| D3 | `docs/docs_index.yaml` skills vs template count | **PASS** | Source `docs/docs_index.yaml:175-196`; verify script `catalog_count=20 template_count=20 missing=[]` |
| D4 | `tm:*` command count = 0 (post-remediation) | **PASS** | `find`/`rg` count 0; deleted in commit `2bab19203` (slices 002–004); TP-001 invariant scoped to packet 001 only |
| D5 | `templates/plugin/l0_membership.json` fleet deps | **PASS** | file exists; deps documented (minor staleness: `plan-tasks.md` still references task-master-ai) |
| E1 | `TRINITY_BOUNDARY_MARKER` in dope-context search_all | **PASS** | `services/dope-context/src/mcp/server.py:96,2094,2209` |
| E2 | `memory_writers.py` ConPort canonical + dope-memory mirror | **PASS** | `src/dopemux/orchestrator/memory_writers.py:70–232` |
| E3 | DCP facade dope-context BLOCKED vs bridged | **PASS** (documented BLOCKED) | `services/dcp-readonly-facade/src/dcp_facade/dope_context.py:1–50` fail-closed stub |
| F1 | Residual risks enumerated | **PASS** | See below |

## Commands run (exit codes)

| Command | Exit | Notes |
|---------|------|-------|
| `git rev-parse --show-toplevel` | 0 | `/Users/hue/code/dopemux-mvp` |
| `git remote -v` | 0 | `origin` → `DDD-Enterprises/dopemux-mvp.git` |
| `git branch --show-current` | 0 | `fix/mcp-server-build-failures` |
| `git rev-parse HEAD` | 0 | `a1690402b` |
| `git status --porcelain=v1` | 0 | untracked `audit_inputs/open_pr_merge_train_2026_06_19/` only |
| `python3 scripts/validate_memory_command_refs.py` | 0 | OK: no forbidden memory refs |
| `python3 scripts/validate_skill_frontmatter.py` | 0 | 20 skills pass |
| `docker ps --filter name=dope-context` | 0 | healthy |
| MCP `initialize` curl `127.0.0.1:3010/mcp` | 0 | HTTP 200 |
| `PYTHONPATH=src python -m dopemux.cli mcp doctor` (unsourced env) | 1 | 4 issues (ports + task-orchestrator env) |
| `source .envrc.dopemux-mcp && ... mcp doctor` | 1 | 2 issues (conport :3039, dope-memory :3054) |
| `git show origin/main:.claude/modules/shared/memory-trinity-routing.md` | 128 | path not in `main` |
| `git show origin/main:scripts/validate_memory_command_refs.py` | 128 | path not in `main` |

## UNKNOWNs

- Live end-to-end `search_all` ConPort decision projection (not exercised this audit).
- Whether `dopemux mcp init` regeneration would fix worktree port drift vs container bindings.
- PAL proof artifacts under `proof/TP-DMX-MEMORY-TRINITY-001/pal/` — present but not re-validated this run.

## NOT_RUN

- Full `sync_repo_skills.py --target claude` install (dry-run path only observed).
- DCP facade live JSON-RPC bridge probe (transport documented BLOCKED; no bridge to test).
- ConPort/dope-memory MCP initialize on worktree ports `:3039`/`:3054` (ports not bound).

## Residual risks (top 5)

1. **Worktree port drift** — `.envrc.dopemux-mcp` `:3039`/`:3054` vs containers on `:3005`/`:3020` breaks per-worktree MCP (`mcp doctor` FAIL).
2. **DCP facade transport gap** — REST-only facade cannot proxy dope-context MCP JSON-RPC (`dope_context.py` fail-closed).
3. **`search_all` projection misread** — operators may treat derived decision snippets as canonical despite `TRINITY_BOUNDARY_MARKER`.
4. **Skills not installed** — templates exist but `.claude/skills/` empty; operator may not discover workflow skills.
5. **`main` not merged** — supervisor GitHub preflight against `main` will FAIL until PR #939 lands.

## Recommended next slices (ordered, max 5)

1. Merge PR #939 or rebase; rerun this audit against `main` post-merge.
2. Regenerate worktree MCP env (`dopemux mcp init`) and confirm `mcp doctor` PASS for conport + dope-memory + task-orchestrator.
3. Run `scripts/skills/sync_repo_skills.py --target claude` (and optionally `github`) to populate operator skill paths.
4. **TP-DMX-MEMORY-TRINITY-005** — docs dedup (`docs/skills/` → canonical reference path).
5. Separate child packet — DCP facade dope-context MCP JSON-RPC bridge.

## Git state after artifact write

See `git status --porcelain` and `git diff --stat` in auditor final response (proof artifacts only modified).