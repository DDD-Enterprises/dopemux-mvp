# CCAR-002 Command Log

## Original C1 implementation
- Builder v1.0.0 catalog generation and 21 focused tests (historical).

## CCAR-002R R1 · Portability repair (2026-08-02/03)
- `python3 scripts/commandcode_router/build_normalized_catalog.py --repo-root <wt>` → exit 0
- `python3 scripts/commandcode_router/build_normalized_catalog.py --check --repo-root <wt>` → exit 0
- `python3 -m pytest tests/commandcode_router/test_normalized_catalog.py -v` → 24 passed
- Dual-worktree byte-identical catalog test: PASS (fixed generated_at)
- `meta.source_manifest` = `proof/CCAR-002/SOURCE_MANIFEST.json` (repo-relative)
- Repo-root resolution: git toplevel / markers / optional `--repo-root` (validated)
- Source agent/persona bytes: UNCHANGED vs pre-R1 baseline
- Independent audit: still pending R2 (AGY against exact R1)

## CCAR-002R-A2 R3 · Evidence + test correctness repair (2026-08-03)
- `python scripts/commandcode_router/build_normalized_catalog.py --check --repo-root <wt>` → exit 0
- `python -m pytest tests/commandcode_router/test_normalized_catalog.py -v` → 26 passed (24 prior + 2 new `TestScanModelIds`)
- Removed absolute `worktree` path from `proof/CCAR-002/SOURCE_MANIFEST.json` (unused by any code path)
- Replaced literal `$(date -u +%Y-%m-%dT%H:%M:%SZ)` in `NORMALIZATION_REPORT.md` with concrete regeneration timestamp
- `test_generation_idempotent` reordered: `--check` against committed catalog runs before any regeneration
- `_scan_model_ids` regex group changed to non-capturing; matching switched to `finditer(...).group(0)`
- Source agent/persona bytes: UNCHANGED vs pre-R1 baseline

## CCAR-002R-A2 R3 follow-up · Evidence timestamp re-sync (2026-08-03)
- Root cause: `test_generation_idempotent` (fixed above) legitimately regenerates the
  catalog as part of its own idempotency check, rewriting `generated_at` to a fresh
  wall-clock value on disk. The `NORMALIZATION_REPORT.md` `**Generated**` line was
  written from an earlier manual regeneration, then the full test suite was run for
  verification *after* that, silently advancing the on-disk `generated_at` past what
  the report recorded. The mismatch was not caught before the prior commit was pushed;
  an independent OpenRouter DeepSeek V4 Pro audit (below) surfaced it and it was
  confirmed by direct inspection of the committed catalog.
- Fix: ran the full mutating test suite FIRST, captured the resulting final
  `generated_at` from disk, then wrote that exact value into the report. No mutating
  regeneration run after this point — only non-writing `--check` from here on.
- `python -m pytest tests/commandcode_router/test_normalized_catalog.py -q` → 26 passed
- `python scripts/commandcode_router/build_normalized_catalog.py --check --repo-root <wt>` → exit 0
- Independent audit: OpenCode + OpenRouter `moonshotai/kimi-k3` (preferred) failed twice
  with malformed/incomplete output (reasoned correctly but never emitted a tool call or
  verdict); fallback OpenCode + OpenRouter `deepseek/deepseek-v4-pro` completed with
  `VERDICT: PASS` against the pre-fix head, but its rationale dismissing the timestamp
  mismatch as "not a contradiction" was itself wrong per the root-cause above — treated
  as a partial finding, not a clean PASS. Fresh audit required against the corrected head.
