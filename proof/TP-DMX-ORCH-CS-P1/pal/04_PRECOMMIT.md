# 04 — Precommit · TP-DMX-ORCH-CS-P1

## Validation runs (all on branch `claude/dmx-orch-cs-p1`, base `origin/main` 59b309f27)

| check | command | exit | bucket |
|---|---|---|---|
| validator (happy) | `python3 scripts/validate_dx_surface.py` | 0 | PASS |
| validator (bite) | inject `advance_item` into `tree.md`, re-run | 1 | PASS (caught) |
| validator (post-revert) | re-run after revert | 0 | PASS |
| pytest | `python3 -m pytest tests/orchestrator/test_dx_surface_manifest.py -q` | 0 | PASS (7 passed) |
| manifest JSON | `python3 -m json.tool .taskorchestrator/surface_manifest.json` | 0 | PASS |
| packet JSON | `python3 -m json.tool task-packets/TP-DMX-ORCH-CS-P1.json` | 0 | PASS |
| packet schema | `python3 -m jsonschema -i task-packets/TP-DMX-ORCH-CS-P1.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | 0 | PASS |
| compileall | `python3 -m compileall -q scripts/... tests/...` | 0 | PASS |
| pre-commit | `pre-commit run --files <changed>` | 0 | PASS (frontmatter auto-normalized on first run; clean on re-run) |
| git diff --check | `git diff --check` | 0 | PASS |

## NOT_RUN
- Full repo test suite — out of scope for an additive docs+validator packet; residual risk low
  (no runtime/source code changed; only new files added).
- CI wiring of the validator — deferred to a follow-up packet (stated in invariants/out-of-scope).

## Diff scope
Additive only — 5 new files + this proof bundle. No existing command, config, or ADR modified.
Confirmed via `git status --short` (only `??` entries for the new paths; pre-existing untracked
`dcp_tp_0001…` and `src/proof/` left untouched and excluded from the commit allowlist).

## Schema-gap note
`execution.agent` enum is `[gemini, codex, vibe, shell]` — no `claude`. Used `shell` (literally
true: executed via shell tooling in an interactive session). Flagged for a possible future
spec enum addition.

## Verdict
VERIFIED on the targeted path. Ready to commit + open PR. Review transition held pending
human signoff (item is supervised-only).
