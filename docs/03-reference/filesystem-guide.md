---
id: FILESYSTEM-GUIDE
title: Filesystem Guide
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-06'
prelude: Where things live and where new things should go. Canonical filesystem layout and placement rules for the dopemux-mvp repository.
---
# Filesystem Guide

## Top-level layout

| Directory | Contents |
|---|---|
| `src/` | Python package source (`src/dopemux/...`). Type-hinted, PEP 8 with Black formatting. |
| `tests/` | All pytest tests. Never co-locate tests next to source. |
| `scripts/` | Operator/utility scripts (Bash, Python). Never put one-off scripts in repo root. |
| `services/` | Service implementations and MCP wrappers (`services/serena/`, `services/dope-context/`, `scripts/mcp-wrappers/`). |
| `docs/` | All documentation (Diataxis structure, see below). |
| `.claude/` | Claude Code configuration: `settings.json`, `settings.local.json`, `CLAUDE.md`, `modules/`, `statusline.sh`, nested `worktrees/`. |
| `claudedocs/` | Claude-authored analyses, summaries, reports. Never commit ad-hoc Claude output to other locations. |
| `out/` | Generated artifacts (build outputs, audit bundles). Treated as ephemeral. |
| `docker/` | Container build assets (`docker/mcp-servers/`, etc.). |
| `task-packets/` | `TP-*.json` task specs consumed by automation. |
| `compose.yml`, `compose/` | Docker Compose stack root. |
| `installers/` | Installer scripts and assets. |
| `instructions/` | Operator-facing instruction files. |

Repo root holds only canonical top-level files (`AGENTS.md`, `ARCHITECTURE.md`, `INSTALL.md`, `LICENSE`, `README*`, `pyproject.toml`, etc.). Avoid adding new files to the root.

## Documentation (Diataxis)

The `docs/` tree follows the [Diataxis](https://diataxis.fr/) framework with numeric prefixes:

| Path | Purpose |
|---|---|
| `docs/01-tutorials/` | Learning-oriented guides for first-time users. |
| `docs/02-how-to/` | Task-oriented recipes ("how do I X?"). |
| `docs/03-reference/` | Information-oriented references (specs, catalogs, APIs). This file lives here. |
| `docs/04-explanation/` | Understanding-oriented background and design rationale. |
| `docs/05-audit-reports/` | Audit outputs and remediation plans. |
| `docs/06-research/` | Research notes, deep-dives, exploratory writeups. |
| `docs/90-adr/` | Architecture Decision Records. **Descriptive filenames, not numbered** (e.g., `adr-conport-as-decision-progress-and-context-authority.md`). Index: `docs/90-adr/adr-index.md`. |
| `docs/91-rfc/` | RFCs (use `docs/templates/rfc-template.md`). |
| `docs/92-runbooks/` | Operational runbooks. |
| `docs/_assets/`, `docs/templates/` | Shared assets and document templates. |

Index surfaces: `docs/00-MASTER-INDEX.md`, `docs/INDEX.md`, `docs/docs_index.yaml`, plus per-section `overview.md` files. See `docs/03-reference/documentation-catalog.md` for the canonical list of active index surfaces and policy files.

## Placement rules

- **Tests** → `tests/` only. Pytest discovers from there. Never `*_test.py` next to source.
- **Scripts** → `scripts/` (operator/utility) or `tools/`/`bin/` if the project gains those. Never one-off `.sh`/`.py` in repo root.
- **Claude analyses, summaries, reports** → `claudedocs/`.
- **ADRs** → `docs/90-adr/` with descriptive filenames; update `adr-index.md`.
- **RFCs** → `docs/91-rfc/`; start from `docs/templates/rfc-template.md`.
- **How-tos** → `docs/02-how-to/<feature-area>/` with frontmatter (`id`, `title`, `type: how-to`, `owner`, `date`).
- **Reference docs** (this file's class) → `docs/03-reference/<area>/` with frontmatter (`type: reference`).
- **Generated artifacts** → `out/` (ephemeral, gitignored where appropriate).
- **Backups (`*.bak`)** → avoid committing; if unavoidable, place in `archive/` or annotate.
- **Secrets** → never commit. `.env`, `credentials.json`, etc. stay out of git. Use the configured key sources.

## Worktree convention

- **In-tree experiments**: `.claude/worktrees/<name>/` (e.g., `.claude/worktrees/optimistic-williams-98f54b/`). Each may carry its own `.claude/settings.json`; keep it in sync with the root project's `settings.json` shape.
- **External/codex worktrees**: `/Users/hue/code/dopemux-mvp-wt-<name>/`, `/Users/hue/code/dopemux-worktrees/<name>/`, or `~/.codex/worktrees/<id>/<name>/`. Treat these as ephemeral parallel branches; abandoned ones should be `git worktree remove`'d periodically.
- Workspace detection (`git rev-parse --show-toplevel`) lets workspace-aware MCPs (ConPort, Serena) isolate state per worktree. Wrappers live in `scripts/mcp-wrappers/`.
- Per-worktree ConPort tagging: tag entries with `worktree:$(basename $(git rev-parse --show-toplevel))` for traceability across parallel work.

## Authority anchors (for placement decisions)

- **Tasks, decisions, patterns, progress** → ConPort (PostgreSQL AGE on port 5455). On-disk `docs/90-adr/` ADRs are the human-readable counterpart for architectural decisions; ConPort is the queryable graph.
- **Code intelligence, navigation, complexity** → Serena LSP (port 3006).
- **Semantic search of code & docs** → Dope-Context.
- **ADHD workflows, sessions, energy tracking** → Python ADHD Engine via `/dx:` SuperClaude commands; data lives in ConPort.
- **Documentation source of truth** → this `docs/` tree. Per-feature hubs cross-reference here; never duplicate canonical content into `claudedocs/` or root README files.

## Cross-references

- `.claude/CLAUDE.md` (project) — authority routing and high-level structure.
- `.claude/modules/_index.md` — active vs deprecated modules.
- `docs/03-reference/documentation-catalog.md` — canonical list of active index surfaces and policy files.
- `~/.claude/RULES.md` — global file-organization and workspace-hygiene rules.
