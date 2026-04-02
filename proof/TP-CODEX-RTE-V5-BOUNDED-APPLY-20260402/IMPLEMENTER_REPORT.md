# TP-CODEX-RTE-V5-BOUNDED-APPLY-20260402

## Scope

- branch under test: `codex/rte-v5-prelive-stack-pr-20260402`
- code commit under test: `500db9015` `feat(repo-truth-extractor): add bounded hygiene apply controls`
- repo root under mutation: `/Users/hue/code/dopemux-mvp`
- bounded target:
  - bucket: `stale_resume_state`
  - limit: `20`

## Procedure

1. Previewed bounded apply with JSON output:
   - `python services/repo-truth-extractor/extraction_hygiene.py --repo-root /Users/hue/code/dopemux-mvp apply --dry-run --bucket stale_resume_state --limit 20 --json`
2. Captured scan before:
   - `python services/repo-truth-extractor/extraction_hygiene.py --repo-root /Users/hue/code/dopemux-mvp scan --json`
3. Executed bounded apply with explicit live-apply flag:
   - `python services/repo-truth-extractor/extraction_hygiene.py --repo-root /Users/hue/code/dopemux-mvp apply --apply --bucket stale_resume_state --limit 20 --json`
4. Captured scan after:
   - `python services/repo-truth-extractor/extraction_hygiene.py --repo-root /Users/hue/code/dopemux-mvp scan --json`
5. Validated:
   - preview planned count stayed within limit
   - blocked promptset skips were nonzero in preview
   - no cross-bucket leakage in preview actions
   - stale resume delta matched applied count
   - blocked promptset count stayed unchanged
   - noise bucket counts stayed unchanged
   - preview target set matched actual applied set
   - each source path disappeared and each destination path existed

## Preview Truth

- `planned_actions=20`
- `summary.eligible_actions=4563`
- `summary.skipped_blocked_promptset=3687`
- `summary.skipped_top_level_zip=1`
- `summary.skipped_ambiguous=0`
- `summary.skipped_non_matching_policy=381`

Interpretation:
- the bucket filter narrowed the candidate universe from the broader mixed apply preview to only stale resume sidecars
- the limit was honored at preview time
- blocked promptset safeguards were active and observable

## Apply Result

- `applied_actions=20`
- archive manifest:
  - `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/quarantine/20260402T211158Z/ARCHIVE_MANIFEST.json`

## Before / After

- before `stale_resume_state=7368`
- after `stale_resume_state=7348`
- delta `=20`
- applied count `=20`

- before `blocked_promptset=4`
- after `blocked_promptset=4`

- before `noise_paths=2873`
- after `noise_paths=2873`

- before `warnings=4`
- after `warnings=4`

## Safety Verdict

This bounded apply passed the required TP10 checks.

- Selective:
  - only `stale_resume_state` actions were planned and applied
- Bounded:
  - preview and apply both stayed at `20`
- Safe:
  - blocked promptset stayed unchanged at `4`
  - no noise-bucket drift occurred
  - preview target set matched the applied path set exactly
- Observable:
  - before/after stale resume delta matched the applied count exactly

## Important Note

The user packet's step-3 command omitted `--apply`. This repo's CLI still requires explicit `--apply` for live mutation, and that safety invariant was preserved. The live bounded apply therefore used the explicit apply flag rather than silently changing CLI defaults.

## Residual Risk

- This proves the bounded path for one bucket and one limit, not full unbounded cleanup.
- A larger or cross-bucket apply still needs its own packet and proof.
