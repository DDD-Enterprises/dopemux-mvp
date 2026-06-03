# Dopemux Beta-Readiness — Implementer Assignments (Opus pass, Gemini-rebalanced)

HEAD `755bf3846` · 2026-05-29. All 56 backlog items in task-orchestrator root `b5960763` are tagged `impl-<implementer>`. Dispatch prompts: `05-DISPATCH-PROMPTS.md`.

## Distribution (after Gemini rebalance)
| implementer | # | tag |
|-------------|---|-----|
| Claude Sonnet | 15 | `impl-sonnet` |
| Gemini + PAL | 15 | `impl-gemini-pal` |
| Claude Opus | 8 | `impl-opus` |
| Claude Haiku | 7 | `impl-haiku` |
| Codex 5.3-codex | 4 | `impl-codex-53` |
| Codex 5.4-mini | 3 | `impl-codex-54mini` |
| Codex 5.5 | 2 | `impl-codex-55` |
| Agy (Antigravity) | 2 | `impl-agy` |

## Criteria
- **Opus** — security exposure, data-safety, architecture, net-new design, multi-instance correctness
- **Sonnet** — CI/test-iteration work + standard fixes needing a local run-fix loop
- **Haiku** — trivial mechanical (one-liners, restores, deletions, doc truncation)
- **Codex** — well-specified code (5.3-codex) / small edits (5.4-mini) / heavy net-new builds (5.5)
- **Agy** — large autonomous multi-file refactor / bulk
- **Gemini+PAL** — well-specified install/compose/config/docs/dead-code that ship as async PRs (NOT tight local test loops)

## By implementer

### `impl-opus` (8)
INSTALL-06 (uninstall data-loss) · WF-02 (orchestrator split-brain) · SEC-01 (LiteLLM key+bind) · SEC-02 (unauth on 0.0.0.0) · MCP-03 (per-instance Redis) · UI-02 (canonical HUD) · WRAP-00 (wrapping spec) · WRAP-04 (vanilla compat)

### `impl-sonnet` (15)
SURF-01 · UI-01 (restores+build verify) · CLI-05 · TEST-01 (CI gate) · TEST-02 · SEC-04 · SEC-05 · HOOK-02 (vanilla-CC safety) · UI-03 · TEST-03 (re-enable suite, needs test loop) · TEST-04 · TEST-05 · HOOK-01/03 · REMOVE-BUNDLE (confirming diffs) · WRAP-01

### `impl-gemini-pal` (15)
INSTALL-01 · INSTALL-03 · INSTALL-04 · INSTALL-05 · INSTALL-09 · SEC-03 (pw→env) · MCP-02 (compose health) · CLI-02 (narrow except) · CLI-04 (remove Dummy fallbacks) · SVC-03/05/06 · DOCS-02 (CLI reference) · DOCS-03 (install-doc merge) · DOCS-06 (troubleshooting) · MCP-04 (posture doc) · SVC-04 (single-instance doc)

### `impl-haiku` (7)
WF-01 · INSTALL-02 (the CRIT 2-liner) · MCP-01 · DOCS-01 · DOCS-04 · DOCS-05 · WF-03

### `impl-codex-53` (4)
CLI-01 (decisions subcommands) · CLI-03 (stub pattern) · TEST-06 (un-quarantine) · CLI-07/08

### `impl-codex-54mini` (3)
INSTALL-07 (pull retry) · SVC-01 (resource limits) · TEST-07/08

### `impl-codex-55` (2)
WRAP-02 (Codex live wrapping) · WRAP-03 (Copilot live wrapping)

### `impl-agy` (2)
CLI-06 (cli.py monolith split) · DOCS-DEDUP (760-file cleanup)

## Notes
- Tags are **who**, not **when** — orchestrator wave deps (`w0→w1→w2→w3`, `WRAP-00→builds`) still sequence execution.
- `TEST-04` final required-status toggle is an operator action (Sonnet drives `gh api`, you flip the switch).
- `impl-agy` + `impl-codex-55` items are the largest — owners-with-review, not fire-and-forget.
