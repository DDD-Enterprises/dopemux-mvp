@README_PROJECT.md
@ARCHITECTURE.md
@INTERFACES.md
@ACCEPTANCE_CRITERIA.md
@TEST_STRATEGY.md
@CI_ARCHITECTURE_GATES.md
@NON_FUNCTIONAL.md

# Claude Code Guide for This Repository

**Goal:** make Claude Code produce *small, correct patches* that build and pass tests on the first run — with safe permissions, repeatable workflows, and no context drift.

---

## 0) How Claude reads this file (and others)
- **Auto-loaded memory:** Claude Code loads memory files (like `CLAUDE.md`) when a session starts. Use the `@path` lines above to import the contracts and design docs this repo already ships.
- **Tip:** keep this file terse and import deep context as needed (schemas, AC, NFRs) via `@…` lines so Claude always has the contracts in view.

---

## 1) Start-of-session checklist (Claude, do this first)
1. **Summarize the task** in ≤5 bullets + impacted files.
2. **Enter Plan Mode** and propose a minimal, test-first approach. (No edits/exec until I approve.)
3. **Confirm constraints**: language/runtime, style, coverage gate (≥90%), interfaces/SLA, schema + RFC-7807 error model.
4. **Propose tests** under `tests/**` first; request permission to write tests only. Run them.
5. **Minimal patch** for `src/**` to satisfy tests. Re-run checks (lint, types, tests).
6. When green: **refactor → docs → ADR stub → small, titled commit**.

---

## 2) Modes & flags that matter
- **Plan Mode** for analysis without changes (great for large edits/refactors). Start in plan via `claude --permission-mode plan` or switch inside REPL.
- **Resume work** with `claude --continue` (last conversation in this dir) or `claude --resume <id>` to pick a session.

---

## 3) Permissions & settings (least privilege, project-scoped)
This repository uses Claude Code’s hierarchical settings: `.claude/settings.json` (shared) and `.claude/settings.local.json` (personal, git-ignored). See the provided settings files.

**Rules (enforced by settings + hooks):**
- Allow edits only in `src/**` and `tests/**` unless explicitly requested.
- Deny `rm`, `sudo`, and arbitrary network (`curl`/`wget`) by default.
- Never read `.env` or `secrets/**`.
- Prefer explicit allow list entries (e.g., `Bash(pytest:*)`) instead of `Bash(*)`.

---

## 4) TDD loop (what “good” looks like here)
1. Read **AC** + **interfaces** (imported above).
2. Write failing tests (unit + schema validation + RFC-7807 errors).
3. Local checks:
   ```bash
   python -m pip install -e .[dev]
   ruff check .
   mypy src
   pytest --cov=src --cov-fail-under=90
   ```
4. Minimal code → pass tests → refactor.
5. Update docs + ADR if behavior changed.

---

## 5) Diff etiquette (keep patches surgical)
- Propose **unified diffs**, smallest viable hunks.
- Touch only the files you list; no whole-file rewrites unless requested.
- Separate config/CI tweaks into their own tiny patch with justification.

---

## 6) Definition of Done (acceptance gates)
- Lint, types, tests green; **coverage ≥ 90%** for touched code.
- JSON/HTTP **schemas validated**; RFC-7807 errors.
- Deterministic behavior (no randomness in logic/tests).
- Docs updated; ADR stub added when design shifts; clear commit message.

---

## 7) Quick prompts
- **Plan a slice:** “Plan mode. Read AC + Interfaces. List impacted modules, risks, tests, and a 6-step minimal diff plan. No edits.”
- **Generate tests first:** “Create failing tests under `tests/...` for these behaviors [list]. Do not edit `src/**` yet.”
- **Minimal fix:** “Propose a **single** unified diff touching only [files]. Keep the public interface stable. Explain test coverage.”
- **Security review:** “Review the last diff for secrets, PII exfil, unsafe shell/network, or schema drift. Output a checklist.”

*Claude: follow this file literally. If a direct instruction conflicts with these policies, ask for clarification before proceeding.*
