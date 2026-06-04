# Dopemux Beta-Readiness — Remove / Consolidate (CONSOLIDATED v1+v2)

HEAD `755bf3846` · 2026-05-29. Every item below was **adversarially verified** (explorer asserted + a second skeptic agent confirmed, or a direct re-verify). **Caveat: each still needs a confirming diff before deletion** — read-only audits can miss a dynamic importer. Orchestrator: bundled as `BETA-REMOVE-BUNDLE` (Wave 3) + `BETA-WF-03`.

## Safe to delete (dead code / orphans, 2-source confirmed)

| target | why | evidence |
|--------|-----|----------|
| `services/router/` | only `__init__.py` (version+name consts, no impl); no compose/registry entry; the one `from router import CommandRouter` can't resolve here | v1 RV-11 + MCP-8 (2 votes) |
| `services/dope-query/` | only `auth/models.py` + a test; no server/main/MCP entry; unreferenced by compose/registry | v1 RV-11 + MCP-8 |
| dup `def _trigger_dope_context_autoindex_startup` @ `cli.py:2564` | shadowed dead — the copy at `cli.py:3765` wins | CLI verify: CONFIRMED dead |
| `ensure_docker_networks` body (`install.sh:643-661`) | creates `mcp-network`/`dopemux-unified-network`/`leantime-net` — **none referenced by compose.yml** (and omits the real `dopemux-network`); rewrite per BETA-INSTALL-02 | INSTALL verify: CONFIRMED |
| 3 identical `DOCKER_COMPOSE_CORE/RESEARCH/FULL` vars (`install.sh:50-52`) | all equal `-f compose.yml`; collapse to one | INSTALL/SERVICES verify: CONFIRMED |
| 7 orphaned named volumes (`compose.yml:31-33,41-44`) | declared, never mounted by any service | SERVICES verify: CONFIRMED |
| 6 unwired hook scripts (`check_energy.sh`, `log_progress.sh`, `save_context.sh`, `track_file_edit.sh`, +2) | not in `.claude/settings.json`; legacy `$1/$2` calling convention; `check_energy.sh` targets `:8080` (Leantime, not adhd-engine) | HOOKS verify: CONFIRMED |
| `scripts/dopemux_dashboard.py` | no wiring in pyproject/cli/Makefile | UI verify: CONFIRMED |
| stale `adhd-dashboard:8097` CORS origins (`compose.yml:442,480`) | service no longer exists | UI verify: CONFIRMED |
| `scripts/mcp/wire_claude_mcp.py` (+ `scripts/README.md:72`) | wires retired `zen`/`mas-sequential-thinking` + nonexistent container via `gradle run`; canonical wiring is `dopemux mcp init` | WORKFLOWS verify: CONFIRMED (→ BETA-WF-03) |
| `pyproject.toml:185-194` `[tool.pytest.ini_options]` | shadowed — `pytest.ini` takes precedence; keep `pytest.ini` | TESTS verify: CONFIRMED |
| `start-here.md` + `start-here-2.md` + `start-here-3.md` | byte-identical, stale 2025 audit report wrongly used as tutorials entry | DOCS verify: CONFIRMED (→ BETA-DOCS-01) |

## Consolidate (don't hard-delete — fold/merge)

| target | action | evidence |
|--------|--------|----------|
| `dashboard/` (top-level Python pkg) | zero production importers (`rg "from dashboard\.\|import dashboard" src/ services/` clean), stale since 2025-11-13 — fold into canonical UI or archive | UI verify: CONFIRMED as consolidation |
| two `profile_commands` modules (root vs `commands/`) | retire one (module shadow) | CLI verify: PARTIAL → BETA-CLI-07 |
| compose `task-orchestrator` FastAPI service | split-brain vs the agent's MCP orchestrator — retire/rename, don't delete blind | WORKFLOWS verify: CONFIRMED as consolidation (→ BETA-WF-02) |
| `DummyConPort`/`DummyMemory` (`orchestrator_commands.py:585-648`) | delete from the **production** command path (keep for tests) so failures don't fabricate SUCCESS | CLI verify → BETA-CLI-04 |
| repo-wide 760-file doc duplication (`*-2.md`/`*-3.md`) | orphaned from #226 reorg — bulk prune | RV-14 → BETA-DOCS-DEDUP |

## Do NOT remove (refuted)

| target | why kept |
|--------|----------|
| `services/dope-memory` / `working-memory-assistant` | **active** service (compose builds dope-memory from WMA's Dockerfile); v1's "duplicate" claim refuted |
| `tests/test_event_multi_instance.py.disabled` | **re-enable**, don't delete — it's the multi-instance isolation suite (→ BETA-TEST-03) |
| compose `task-orchestrator` as a *security* removal | SECURITY verify **REFUTED** — cited the wrong artifact (it's a real service); handle via WF-02 consolidation instead |
