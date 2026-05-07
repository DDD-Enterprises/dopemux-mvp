---
id: FILESYSTEM-GUIDE
title: Filesystem Guide
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-06'
last_review: '2026-05-07'
next_review: '2026-08-05'
prelude: Where things live and where new things should go. Canonical filesystem layout and placement rules for the dopemux-mvp repository.
---
# Filesystem Guide

## Top-level layout

| Directory | Contents |
|---|---|
| `src/` | Python package source (`src/dopemux/...`). Type-hinted, PEP 8 with Black formatting. |
| `tests/` | Python pytest tests. UI and service toolchains may keep their own tests under their package directories when their test runner owns discovery. |
| `scripts/` | Operator/utility scripts (Bash, Python). Never put one-off scripts in repo root. |
| `services/` | Service implementations and MCP wrappers (`services/serena/`, `services/dope-context/`, `scripts/mcp-wrappers/`). |
| `docs/` | All documentation (Diataxis structure, see below). |
| `.claude/` | Claude Code configuration: tracked `settings.json`, `claude.md`, `modules/`, `statusline.sh`, and optional ignored local overrides such as `settings.local.json`. |
| `claudedocs/` | Reserved destination for Claude-authored analyses, summaries, and reports. Create it when committing durable Claude output there; do not use arbitrary root paths. |
| `out/` | Generated artifacts (build outputs, audit bundles). Usually ephemeral; committed artifacts must be intentional evidence outputs for the active work scope. |
| `docker/` | Container build assets (`docker/mcp-servers/`, etc.). |
| `task-packets/` | `TP-*.json` task specs consumed by automation. |
| `compose.yml`, `compose/` | Docker Compose stack root. |
| `installers/` | Installer scripts and assets. |
| `instructions/` | Operator-facing instruction files. |

Repo root holds only canonical top-level files (`AGENTS.md`, `ARCHITECTURE.md`, `INSTALL.md`, `LICENSE`, `README*`, `pyproject.toml`, `mcp_catalog.yaml`, `pal_validation.json`, etc.). Avoid adding new files to the root.

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
| `docs/90-adr/` | Architecture Decision Records. Use the existing `adr-###-...` naming when a sequence number is assigned; descriptive `adr-...` filenames are also present for named authority records. Index: `docs/90-adr/adr-index.md`. |
| `docs/91-rfc/` | RFCs (use `docs/templates/rfc-template.md`). |
| `docs/92-runbooks/` | Operational runbooks. |
| `docs/_assets/`, `docs/templates/` | Shared assets and document templates. |

Index surfaces: `docs/00-MASTER-INDEX.md`, `docs/INDEX.md`, `docs/docs_index.yaml`, plus per-section `overview.md` files. See `docs/03-reference/documentation-catalog.md` for the canonical list of active index surfaces and policy files.

## Placement rules

- **Python tests** → `tests/`. Pytest discovers from there. Never put Python `*_test.py` next to source.
- **UI/service-local tests** → the package-owned test location when the local runner requires it, such as `ui-dashboard/src/components/__tests__/`.
- **Scripts** → `scripts/` (operator/utility) or the existing `tools/` directory when the code is reusable tooling. Never one-off `.sh`/`.py` in repo root.
- **Claude analyses, summaries, reports** → `claudedocs/`; create the directory when the work requires a committed Claude-authored output.
- **ADRs** → `docs/90-adr/` with descriptive filenames; update `adr-index.md`.
- **RFCs** → `docs/91-rfc/`; start from `docs/templates/rfc-template.md`.
- **How-tos** → `docs/02-how-to/<feature-area>/` with frontmatter (`id`, `title`, `type: how-to`, `owner`, `date`).
- **Reference docs** (this file's class) → `docs/03-reference/<area>/` with frontmatter (`type: reference`); cross-cutting reference docs may live directly under `docs/03-reference/`.
- **Generated artifacts** → `out/` (ephemeral, gitignored where appropriate). Commit generated audit or review evidence there only when the PR explicitly owns that evidence.
- **Backups (`*.bak`)** → avoid committing; if unavoidable, place in `archive/` or annotate.
- **Secrets** → never commit. `.env`, `credentials.json`, etc. stay out of git. Use the configured key sources.

## Worktree convention

- **In-tree experiments**: `.claude/worktrees/<name>/` (e.g., `.claude/worktrees/optimistic-williams-98f54b/`). Each may carry its own `.claude/settings.json`; keep it in sync with the root project's `settings.json` shape.
- **External/codex worktrees**: `<workspace-parent>/dopemux-mvp-wt-<name>`, `<workspace-parent>/dopemux-worktrees/<name>`, or `~/.codex/worktrees/<id>/<name>/`. Treat these as ephemeral parallel branches; abandoned ones should be `git worktree remove`'d periodically.
- Workspace detection (`git rev-parse --show-toplevel`) lets workspace-aware MCPs (ConPort, Serena) isolate state per worktree. Wrappers live in `scripts/mcp-wrappers/`.
- Per-worktree ConPort tagging: tag entries with `worktree:$(basename $(git rev-parse --show-toplevel))` for traceability across parallel work.

## Authority anchors (for placement decisions)

- **Tasks, decisions, patterns, progress** → ConPort (PostgreSQL AGE on port 5455). On-disk `docs/90-adr/` ADRs are the human-readable counterpart for architectural decisions; ConPort is the queryable graph.
- **Code intelligence, navigation, complexity** → Serena LSP (port 3006).
- **Semantic search of code & docs** → Dope-Context.
- **ADHD workflows, sessions, energy tracking** → Python ADHD Engine via `/dx:` SuperClaude commands; data lives in ConPort.
- **Documentation source of truth** → this `docs/` tree. Per-feature hubs cross-reference here; never duplicate canonical content into `claudedocs/` or root README files.

## Cross-references

- `.claude/claude.md` (project) — authority routing and high-level structure.
- `.claude/modules/_index.md` — active vs deprecated modules.
- `docs/03-reference/documentation-catalog.md` — canonical list of active index surfaces and policy files.
- `~/.claude/RULES.md` — global file-organization and workspace-hygiene rules.
