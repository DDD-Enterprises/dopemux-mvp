# Repository Guidelines

This guide orients contributors. Produce small, correct patches that build green on first run.

## Project Structure & Module Organization
- `src/chatx/` — CLI, extractors, storage, embeddings, utilities (typed Python).
- `tests/` — `unit/` and `integration/`; fixtures live under `tests/**`.
- `docs/` — MkDocs portal (architecture, specs, how‑tos, plans). Start at `docs/index.md`. See also `docs/implementation.md` and `docs/architecture.md`.
- `schemas/` — JSON Schemas used by extract/transform.
- `.claude/commands/` — internal command/workflow guides (kept in place; referenced from docs).

## Workflow (Slice‑Based)
Follow CLAUDE.md: Bootstrap → Research → Story → Plan → Implement → Debug → Ship.
- Implement: write tests first, minimal edits, run gates locally.
- Ship: `git add -A && git commit -m "type(scope): summary" && gh pr create ...` then `gh pr checks` and `gh pr merge --squash`.
- Tool priority: prefer project tools/automation and semantic helpers; avoid ad‑hoc shell when structured tools exist.

## Build, Test, and Development Commands
- Setup: `pip install -e ".[dev]"` (Python 3.11+)
- Lint/types/tests (required gates): `ruff check .` · `mypy src/chatx` · `pytest --cov=src/chatx --cov-fail-under=90`
- Docs: `mkdocs serve` (local) · `mkdocs build`
- Data flow (example): `chatx imessage pull ...` → `chatx transform ...` → `chatx redact ...` → `chatx index ...`

## Artifacts & Reports
- `out/manifest.json` and `out/run_report.json` — inputs, versions, elapsed, counts.
- `out/redaction_report.json` — privacy coverage/validation stats.
- `out/missing_attachments.json` — iCloud eviction/completeness checks.

## Coding Style & Naming
- Python 4‑space indent; type hints for new/changed code.
- Names: `snake_case` (func/vars), `PascalCase` (classes), `kebab-case` (docs files).
- Encoding: UTF‑8 only. Pre‑commit blocks non‑UTF‑8; never stage binaries.

## Testing Guidelines
- Framework: `pytest`; files `tests/**/test_*.py` mirroring module paths.
- Coverage: ≥90% for new/changed code; add focused unit tests first; optional `-m perf` where available.

## Commit & Pull Request
- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
- PRs must include: clear description, rationale, tests passing, and docs/nav updates if applicable. Link issues (`Fixes #123`).

## Automation & Commands
- Internal command docs live under `.claude/commands/`; see the index at `docs/reference/commands/index.md` for quick navigation.

## Security & Configuration
- Local‑first privacy: attachments never leave device; redact before any optional cloud use.
- Don’t commit secrets (`.env`, keys). On macOS grant Full Disk Access for iMessage paths.
- Vector DB artifacts under `context_portal/` are ignored by `.gitignore`.

## MCP Integration & Setup
- Config lives in `.claude/` and user overrides in `~/.claude.json` (may include secrets; do not commit). See `.claude/mcp.config.json`.
- Start/check/stop helpers: `bash scripts/mcp/start.sh` · `bash scripts/mcp/check.sh` · `bash scripts/mcp/stop.sh`.
- Env vars: set `OPENAI_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, and `OPENMEMORY_API_KEY` (see `.env.example`).
- Servers: fast‑markdown (Docker `devdocs-mcp`), OpenMemory (`npx openmemory`), Zen (`uvx … zen-mcp-server`).
- Advanced: `python scripts/mcp/mcpctl.py list|start-all|start <name>|check|stop[-all]` merges project and user configs. Optional per‑server health in config:
  - `"health": { "type": "http", "url": "http://127.0.0.1:8000/health", "expect": "ok" }`
  - or `{"type": "tcp", "host": "127.0.0.1", "port": 8000}`
  - or `{"type": "cmd", "cmd": ["docker", "ps"], "expect": "devdocs-mcp"}`
