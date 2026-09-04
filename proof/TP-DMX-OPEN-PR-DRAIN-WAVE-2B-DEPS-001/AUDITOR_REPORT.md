# AUDITOR_REPORT — TP-DMX-OPEN-PR-DRAIN-WAVE-2B-DEPS-001

## Subject

Integration branch `integration/deps-2026-09`, part of
`TP-DMX-OPEN-PR-DRAIN-MERGE-001` Wave 2B (§15): a batch of PATCH/MINOR
dependency updates. #1295 (a Dependabot "python-minor-patch" group bump)
was **pulled out** of this batch after a real regression was found: merging
it silently upgraded FastAPI from 0.135.2 to 0.141.1 as an *unpinned*
side-effect of `uv lock` re-resolution — `pyproject.toml`'s own constraint
(`fastapi>=0.115.12`) never changed. FastAPI 0.141.1 introduces a new
internal `_IncludedRouter` lazy-router-wrapping class that broke
`tests/unit/pm/test_pm_route_contracts.py::test_task_orchestrator_runtime_includes_project_workflow_router`,
confirmed passing on unmodified `origin/main` via a separate baseline
worktree and failing only with #1295 merged. #1295 is reclassified for
individual handling; this packet covers only #1298 (pip 26.1.2→26.2) and
#1299 (postcss-selector-parser 6.1.2→6.1.4), rebuilt from current main.

- Base: `3e61f0d0a8931b1cb50bff83d29e70794aef930d`
- Frozen integration head: `6de2f30309db11ea79713382932a4320776ff1d1`

## Auditor

`agy` (Google Antigravity CLI), model `gemini-3.1-pro-high`.

## Verdict

**PASS** — 6/6 findings VERIFIED, 0 remaining risks.

## Findings

| ID | Severity | Title | Status |
|---|---|---|---|
| F01 | INFO | Diff scope confined to `uv.lock` + `package-lock.json` only | VERIFIED |
| F02 | INFO | `uv.lock`'s only version change is pip 26.1.2→26.2 | VERIFIED |
| F03 | INFO | `package-lock.json`'s only version change is postcss-selector-parser 6.1.2→6.1.4 | VERIFIED |
| F04 | INFO | FastAPI remains pinned at 0.135.2 (regression confirmed excluded) | VERIFIED |
| F05 | INFO | `tests/unit/pm/test_pm_route_contracts.py` independently re-run: 3/3 passed | VERIFIED |
| F06 | INFO | No secrets/credentials; diff is routine version/hash/URL metadata only | VERIFIED |

Full auditor output: `review_bundle/auditor_raw_output.txt`.

## Additional validation (performed by the operator session, not re-run by the auditor)

- `uv lock --check`: resolves cleanly, 276 packages
- `npm install --package-lock-only` in repo root: no drift
- Full required-CI-scope test suite: `tests/unit tests/test_voice_core.py
  tests/test_brand_voice.py` — 1878 passed, 2 skipped (pre-existing
  quarantines), 0 new failures (1 pre-existing worktree-topology-dependent
  failure deselected and confirmed identical on unmodified `origin/main`)
- WMA MCP endpoint gate: 6/6 passed
- DCP red-lane gate: 185 passed, 1 deselected (matches CI's own deselect)
- Brand lint gate: 0 errors, 0 warnings
