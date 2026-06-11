# DX Overhaul — Phase 1 Research Synthesis

**Date**: 2026-06-11 · **Method**: 7 parallel read-only explorations (architecture, MCP fleet, commands/skills, hooks, git/CI/PR/supervisor, cross-tool instruction surface, ADHD/CLI/memory, worktree/orchestrator loop) at branch `dcp/chatgpt-mcp-ro-0006-…` (≈ main).
**Labels**: OBSERVED (read in files) / INFERRED / ASPIRATIONAL (documented, not wired).

---

## 1. The holistic picture

Dopemux today is **a strong governance spine wearing several generations of unfinished UX**.

**What actually works (the spine):**
- **Governance**: AGENTS.md Truth Order → Task Packets → proof bundles with `embedded_audit` → CI validators (`audit-validator` is a required PR gate). PAL chains defined per AGENTS.md §5.
- **Authority split (canonical writers)**: task-orchestrator = workflow transitions; ConPort = decisions/progress/knowledge graph; dope-memory = session chronicle; Leantime = passive PM metadata; dopecon-bridge = transport only (explicitly not authoritative).
- **Claude Code hook spine**: all 11 lifecycle events route through one dispatcher (`src/dopemux/claude/native_hooks.py`). The real, load-bearing behaviors: workflow stop-gate (fail-closed), workflow/orchestrator context injection at SessionStart/prompt/compact, orchestrator context caching, edit-count evidence nudges, plan-mode guidance.
- **CI**: `ci-complete.yml` with 7 blocking jobs + preflight + repo-identity; docs hygiene via pre-commit in CI; proof schema validation.
- **Orchestrator loop**: v3.8.0, work trees, claim/advance/complete with proof-bundle gate; multi-project data dirs already exist (adOps, dnh_crm, …).

**What's bloat or dead:**
- **~122 slash commands; only ~15–20 deliver value.** 57 `tm:*` (TaskMaster — deprecated), 7 OpenMemory/Mem0 commands (dead MCP), ~13 aspirational one-liner orphans (`/doc:*`, `/rfc:*`, `/web:*`, `/trigger:run`, `/security-review`…). Keep-list seed: `/dx:*` (orchestrator-backed), `/save`, `/switch`, `/plan`, `/zen`, `/implement`, `/debug`, `/research:*`, `/bootstrap`.
- **6 dead hook scripts** in `.claude/hooks/` (check_energy.sh, log_progress.sh, save_context.sh, track_file_edit.sh, prompt_analyzer.py, session_lifecycle.py) — none called by the dispatcher; they read env vars Claude Code never sets and POST to services that aren't listening.
- **Dead config**: ADHD profile fields (`energy_tracking_enabled`, `break_reminders_enabled`, …) parsed but consumed by nothing. `dopemux.toml` is a 14-line tmux stub.
- **Ghost MCP entries**: mas-sequential-thinking (no container), stale exa README port, serena dual code path (wrapper vs Docker).

**What's fragmented (the cross-tool problem):**
- Only **Claude Code** has rich support (hooks + skills + agents + MCP). Copilot: 3 overlapping instruction files, MCP fork config, referenced agents (`.github/agents/dopemux-*.agent.md`) **don't exist**. Codex: AGENTS.md only. Gemini: 36-line GEMINI.md referencing possibly-aspirational CLI commands. opencode: PAL-only. Grok/AGY: nothing.
- Governance doctrine duplicated in 4+ places with drift (PAL chains differ between AGENTS.md §5 and pal-opencode-guide.md; Copilot files don't cite AGENTS.md at all).
- `config/ai/model-routing.policy.yaml` is consistency-tested in CI but **no tool reads it at runtime**.

---

## 2. Inventory summary tables

### Slash commands (full audit in transcript; counts OBSERVED)

| Family | Count | Verdict |
|---|---|---|
| `/tm:*` (TaskMaster) | 57 | DELETE — deprecated by decisions #132–134 |
| OpenMemory/Mem0 (`/caveat /decision /followup /mem*`) | 7 | DELETE — dead MCP |
| Aspirational orphans (`/doc:* /rfc:* /web:* /trigger:run /security-review /adr:new /safe`) | ~13 | DELETE or implement deliberately |
| `/dx:*` (orchestrator) | 17 | KEEP — core; but `/dx:load`, `/dx:prd-parse` specified and missing; full 18-command surface partially dropped from main (palette clobber), lives on `task-orchestrator-claude-surface` |
| Research (`/research*`) | 4 | KEEP, consolidate to quick/deep |
| Dev loop (`/implement /debug /tdd-loop /ship /retrospect /plan /zen*`) | 7 | KEEP |
| Session (`/save /switch /bootstrap /scratch /get-decisions /search-decisions`) | 6 | KEEP |
| Misc (`/pattern /runbook:update /story /diff-proposal /dangerous`) | 5 | case-by-case |

**Post-cleanup target: ~35–40 commands** (audit's estimate), in 4 families.

### MCP fleet (key rows)

| Server | Transport | Worktree-aware | Key issue |
|---|---|---|---|
| conport | SSE :3005 (+REST :3004) | yes (env) | port split 3004/3005 drift in pm/reads.py; global config hardcodes 3005 |
| task-orchestrator | stdio docker (singleton kill-and-replace) | yes (sha256 of project root) | **second session kills first**; HTTP mode exists in jar (POC-verified) but not cut over |
| dope-memory | declared `http …/mcp` | yes | `/mcp` endpoint absent **on this branch** — fix is PR #857 (open); stdio adapter knows only 3 of 10 tools |
| dope-context | HTTP :3010 | partial | `search_all` has Redis side effects (facade denies it); not truly per-worktree |
| pal | SSE :3003 | n/a | healthy; the workhorse for validation |
| serena | SSE :3006 / local wrapper | yes | two divergent code paths |
| dcp-readonly-facade | stdio/HTTP | registry-bound | code+tests done; deployment ASPIRATIONAL (tunnel = TP-0007) |

Wiring: global `~/.claude.json` (8 servers) + per-worktree `.mcp.json` (3 servers). `dopemux mcp init` port-allocation is cataloged but implementation unconfirmed. Proxy configs for Copilot are a stale fork.

### Hooks

- **Live** (via native_hooks.py): stop-gate (fail-closed in workflows), context injection, orchestrator cache, edit nudge, plan guidance, dormant actor-attribution enforcement (config key absent).
- **Dead**: the 6 legacy scripts above; Redis activity events likely no-op (no Redis URL in env).
- **Cross-tool**: hooks are Claude Code-exclusive. Everyone else only hits the git/pre-commit/CI layer. `.githooks/` activation (`core.hooksPath`) not wired by any setup script — UNKNOWN whether developers actually have local pre-commit enforcement.

### Git → CI → PR pipeline

- Blocking: ci-summary aggregate (7 jobs), preflight, repo-identity, docs pre-commit, containers/scout (path-scoped). **Branch-protection registration of ci-summary is UNKNOWN** (acknowledged in workflow comment).
- Advisory: embedded-audit (PAL clink), pr-steward intake (`MERGE_READINESS.json`), gemini review (quota-noisy), claude security, CodeQL.
- **Manual today**: resolving review threads, fixing CI, assembling evidence for the supervisor, supervisor verdict (no ingestion path — `supervisor_accepted` field exists but unplumbed), the merge click (`allow_governed_automerge: false`), post-merge ledger updates.
- Hard invariants: DCP-RED-MERGE-SEAM-0001; LIVE_WRITE_READY undefined/blocking.

### ADHD / CLI / memory reality

- T1 honesty + T4 pipeline remediation **shipped** (fail-honest `status --attention`, confidence bands, hyperfocus latch in core/engine.py) — but all validated against mocked Redis; live event pipeline never exercised end-to-end.
- Dashboard: builds; cognitive state falls back transparently; team panel is hardcoded fiction.
- Four memory layers (ConPort, dope-memory, Serena state, Claude auto-memory) with no dedup/routing between ConPort and dope-memory.

### Worktree / multi-project

- Worktree CLI + wrappers resolve workspace correctly (common-dir hash). Orchestrator DB shared per-repo across worktrees — by design — but also accumulates **cross-project contamination** (dNh CRM root inside dopemux workspace).
- Load plans are JSON design artifacts loaded by **manual MCP calls** — no loader script.
- `dopemux init` scaffolds projects but does NOT provision MCP stack for foreign repos; adOps runs off global config.

---

## 3. Top pain points ranked for redesign leverage

1. **Session bootstrap is convention, not mechanism** — fresh session in a worktree starts cold unless caches happen to be warm; `/dx:load` doesn't exist; `/sc:load` is doctrine-only.
2. **Command bloat destroys discoverability** — 122 commands, >50% dead; the magic 15 are buried.
3. **task-orchestrator stdio singleton** — second session kills first; HTTP cutover already POC-verified but not applied.
4. **Supervisor loop is fully manual** — evidence assembly, verdict, and post-verdict bookkeeping have no automation; `supervisor_accepted` is unplumbed.
5. **Cross-tool parity is doctrine-by-copy-paste** — 4+ drifting copies of governance; Copilot agents referenced but missing; routing policy unread at runtime.
6. **MCP transport fragility** — dope-memory /mcp gap (PR #857 pending), conport port split, serena dual path, ghost entries.
7. **Dead surface area misleads agents and humans** — dead hooks/commands/config actively waste model context and trust.
8. **Load-plan → orchestrator loading is manual** — every series load is hand-driven MCP calls.
9. **Local enforcement gap** — `.githooks` activation unknown; devs may discover failures only in CI (this session's PR #854 fix-waves are the live example).
10. **ADHD layer half-real** — honest now, but the live signal pipeline (hooks → Redis → engine) is unverified; profile config decorative.

## 4. Redesign levers (preview for Phase 2/3 — not yet approved)

- **One bootstrap mechanism**: SessionStart hook does the full orient (orchestrator + ConPort + chronicle + git state) with graceful degradation; `/dx:load`–equivalent becomes automatic.
- **Command consolidation**: ~6 verb-level entry commands (work, save, plan, research, review, ship) wrapping the orchestrated machinery; family commands kept as power-user surface.
- **HTTP-singleton MCP topology** per workspace (orchestrator cutover; dope-memory PR #857; conport port unification) → multi-session safe.
- **Single-source doctrine**: one canonical governance file compiled/synced into per-tool surfaces (CLAUDE.md, copilot-instructions, GEMINI.md, opencode) by a sync script + CI drift gate — same pattern as existing `sync_repo_skills.py`.
- **Automate the PR loop up to (not including) merge**: evidence-package assembler, supervisor verdict ingestion via DCP-facade-adjacent artifact, auto-fix lanes for the recurring CI failure classes — preserving DCP-RED-MERGE-SEAM-0001 and human merge.
- **Load-plan loader**: script that replays `load_plan-*.json` into the orchestrator idempotently.
- **Delete sweep**: tm:*, mem/OpenMemory commands, dead hooks, ghost MCP entries, decorative config.
