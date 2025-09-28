# Agent Workflows (Claude Code + MCP)
_Last updated: 2025-09-02 UTC_

## Tools
- Claude Code (CLI) and **Claude Context** (MCP) for semantic code search
- **GitHub** MCP to create issues/PRs and read CI logs
- **Repo Prompt** (MCP) for XML-based edits
- `gh` (GitHub CLI) and **aicommits** for Conventional Commits

## Loop
1. **Explore** (no writes): read specific files and latest ADRs.
2. **Plan** (`/project:plan-think` or “think hard”): small, testable steps.
3. **Create issue** (GitHub MCP or `gh issue create`) using templates.
4. **TDD**: `/project:tdd-start` (failing test) → `/project:tdd-implement` (make green + refactor).
5. **Docs/ADR** updates.
6. **Commit**: aicommits drafts a Conventional Commit.
7. **PR**: `/project:pr-open` or `gh pr create`; CI runs tests/lint/types and docs-updated gate.
8. **Merge**; docs auto-deploy to Pages.

## Chat Sessions (XML apply)
- **Web/chat outputs:** return a **Repo Prompt XML edits document** and apply via Repo Prompt’s **Apply** tab or its MCP tool.
- **Claude Code sessions (terminal):** the agent may **edit files directly** or **emit a unified diff** (we’ll apply with `git apply`). After apply: run `pytest -q`, `ruff`, `mypy`; update `/docs` & ADRs; Conventional Commit; PR.
