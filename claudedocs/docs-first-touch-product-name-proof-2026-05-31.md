# docs first-touch product-name proof - 2026-05-31

## Scope

- Task Packet: `task-packets/generated/TP-DOCS-FIRST-TOUCH-PRODUCT-NAME-001.json`
- Branch: `fix/docs-first-touch-product-name`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-docs-first-touch`
- Base branch: `main`
- Target: replace stale active Start Here onboarding content with the actual Dopemux first-touch flow.

## Observed State

- `docs/01-tutorials/start-here.md`, `start-here-2.md`, and `start-here-3.md` were byte-identical stale audit-branch guides.
- The stale Start Here files referenced `code-audit`, audit success summaries, and non-existent first-touch files such as `README-AUDIT-COMPLETE.md`.
- `docs/01-tutorials/quickstart.md`, root `QUICK_START.md`, and `README.md` already documented Dopemux install/start boundaries.
- The prescribed `chatx` grep still finds `ChatX` only in `docs/archive/...` historical material, not in active first-touch onboarding docs.

## Change

- Replaced the active Start Here variants with a Dopemux onboarding path:
  - clone repo
  - run `./install.sh`
  - run `dopemux start`
  - open Claude Code from the checkout and inspect `/mcp`
- Preserved explicit runtime authority language and directed compose-backed smoke checks to `QUICK_START.md`.
- Added a Task Packet and index row for replayability.

## Validation

PASS:

- `python -m json.tool task-packets/generated/TP-DOCS-FIRST-TOUCH-PRODUCT-NAME-001.json >/dev/null`
- `python -m jsonschema -i task-packets/generated/TP-DOCS-FIRST-TOUCH-PRODUCT-NAME-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `grep -rn "chatx\\|chat-x\\|ChatX" README.md INSTALL.md docs/01-tutorials 2>/dev/null; test $? -eq 1`
  - Result: no active first-touch matches.
- `rg -n "code-audit|README-AUDIT|ULTIMATE-AUDIT|production-ready|START HERE - Complete Audit" docs/01-tutorials/start-here.md docs/01-tutorials/start-here-2.md docs/01-tutorials/start-here-3.md; test $? -eq 1`
  - Result: no stale audit-branch matches.
- `python scripts/docs_validator.py docs/01-tutorials/start-here.md docs/01-tutorials/start-here-2.md docs/01-tutorials/start-here-3.md`
- `python scripts/docs_frontmatter_guard.py docs/01-tutorials/start-here.md docs/01-tutorials/start-here-2.md docs/01-tutorials/start-here-3.md`
  - Result: all docs have valid frontmatter.
- PAL codereview with `gpt-5-codex`
  - Result: no issues found.
- `pre-commit run --files docs/01-tutorials/start-here.md docs/01-tutorials/start-here-2.md docs/01-tutorials/start-here-3.md task-packets/INDEX.md task-packets/generated/TP-DOCS-FIRST-TOUCH-PRODUCT-NAME-001.json claudedocs/docs-first-touch-product-name-proof-2026-05-31.md`
  - Result: passed.

WARN:

- `grep -rn "chatx\\|chat-x\\|ChatX" docs/ README.md INSTALL.md 2>/dev/null | head -20` still reports archive/history-only matches under `docs/archive/...`.
- This slice did not validate a live `./install.sh` or `dopemux start` runtime session.

NOT_RUN:

- Full docs lint suite.
- Full repository test suite.
- Live installer/startup run.

## Residual Risk

- The repo has duplicated `start-here` variants with the same frontmatter `id`; this slice refreshed all three because they were identical active tutorial files, but did not resolve duplicate-doc architecture.
- Archive/historical `ChatX` references remain because they are not active onboarding surfaces and were not read deeply enough to rewrite safely.
