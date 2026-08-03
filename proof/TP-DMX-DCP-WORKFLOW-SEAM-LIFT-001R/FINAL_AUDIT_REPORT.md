# Final Independent Audit Report — PR #1193

**Packet**: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
**Repository**: DDD-Enterprises/dopemux-mvp
**PR**: #1193 (draft)
**Base**: `ff08e573b4259ac7456dae1a9985968603e9111d`
**Audited content head**: `34cc73c3edcde27ea362cf2046995ada9db97999`
**Audit mode**: READ_ONLY, tool-free static-bundle audit
**Verdict**: `PASS_WITH_RISKS`

## Route

The originally authorized route (`opencode` + `openrouter/deepseek/deepseek-v4-pro`,
agent `ccar-audit-readonly`) failed twice — once as a degenerate premature
stop with no real tool use, once producing a fully fabricated, internally
consistent but entirely fictional audit transcript for a nonexistent task
packet and repository. Neither attempt is valid audit evidence for PR #1193.
Full detail in `AUDIT_ROUTE_INCIDENT.md`. That failure was reported to the
supervisor and a distinct alternate route was explicitly authorized in
response — not substituted unilaterally.

The authorized alternate route: `opencode` + `openrouter/moonshotai/kimi-k3`
(exact, non-aliased selector, confirmed present via `opencode models`),
agent `ccar-audit-notools` (zero tools: read/glob/grep/edit/write/bash/
webfetch/websearch/task/todowrite/lsp/skill all denied). The model received
no file-access capability at all — every piece of evidence it could use was
pasted directly into a single message, assembled deterministically outside
the repository from the exact audited head, with a SHA-256 manifest over
every input file. This removes the fictional-tool-session escape hatch that
both DeepSeek attempts exploited.

The model's output began with the required self-reported header:

```
AUDIT_TARGET_HEAD=34cc73c3edcde27ea362cf2046995ada9db97999
BUNDLE_MANIFEST_SHA256=1b8cb98b90e74e12fd2e9b17c01a94a0f05fda65697b61b369baa4b5a6a2ec90
INPUT_FILE_COUNT=15
EXTERNAL_TOOLS_USED=false
EXTERNAL_FILES_REFERENCED=false
```

Both the reported head and the reported manifest hash were independently
cross-checked against the actual bundle and match exactly. Unlike the
disqualified DeepSeek attempt, no finding in the output references any
file, path, packet ID, or repository that is not actually present in the
bundle.

## Summary of verification

All nine required verification points from the audit instruction were
addressed:

1. **Exact-path scope** — VERIFIED by direct regex trace. Confirmed the
   carve-out exempts exactly `embedded-audit.yml` and `pr-steward.yml` at
   the top level, and that `.bak` near-misses, nested copies, case
   variants, and normalized traversal forms all remain blocked.
2. **`TEXT_RULES` still active** — VERIFIED. Confirmed `FORBIDDEN_PATHS`
   and `TEXT_RULES` are applied in two independent loops in
   `red_lane_scanner.py`, and that the new dedicated test proves a
   `MERGE_SEAM_VIOLATION` still fires on carved-out file content.
3. **Fallback sync** — VERIFIED. `_FALLBACK_COMPILED` never contained a
   workflows pattern; no live/fallback divergence introduced.
4. **ADR-224 accuracy** — VERIFIED against the actual diff and code.
5. **Repaired `001R` packet** — VERIFIED field-by-field against the
   canonical Task Packet JSON Schema, including confirming the old (no-`R`)
   draft's disqualifying schema violations and the exclusion of its
   unrelated historical scope.
6. **Baseline-failure proof** — reasoning judged sound (this PR adds zero
   files matching any `FORBIDDEN_PATHS` pattern, so the pre-existing
   `test_16_no_forbidden_files_modified` anchor comparison should indeed be
   identical), but the actual pytest execution could not be independently
   re-run from a static bundle — marked UNVERIFIED rather than assumed PASS.
7. **No workflow/automation/signer changes** — VERIFIED; diff touches
   exactly 10 files, none under `.github/workflows/`; insertion arithmetic
   cross-checked against the stated diffstat.
8. **Test sufficiency** — judged adequate for the claimed positive/hostile
   cases, with a noted minor gap (see F4).
9. **README scope-drift** — VERIFIED as pre-existing, already flagged
   out-of-scope by ADR-224, and not worsened by this PR.

## Findings

Four findings were raised, all LOW/INFORMATIONAL/MINOR severity, and all
explicitly scoped as pre-existing characteristics of the guard that this PR
does not introduce or worsen:

- **F1** (LOW) — `_repo_relative()` in `dcp_surface_guard.py` does not
  resolve `..` segments or handle absolute paths outside the project root,
  which is a pre-existing lexical-evasion weakness in the guard generally
  (not specific to the workflow carve-out).
- **F2** (LOW) — `red_lane_scanner.py`'s path-check loop matches
  `FORBIDDEN_PATHS` against unnormalized path strings, another pre-existing
  general weakness.
- **F3** (INFORMATIONAL) — a theoretical trailing-newline edge case in the
  regex `$` anchor, judged not a realistic bypass.
- **F4** (MINOR) — missing dedicated regression tests for case-variant,
  traversal, separator, and whitespace path forms (verified instead by
  direct reasoning, and reasoned to be fail-safe in every case).

Full detail in `FINAL_AUDIT_VERDICT.json`. See `FINAL_AUDIT_RAW_OUTPUT.txt`
for the complete, unedited model output.

## Mutation statement

No mutation was performed by the audit. The auditing agent had zero tools
available and worked entirely from pasted content; this is enforced by the
`ccar-audit-notools` agent's permission profile (all tool categories
explicitly denied), not merely by instruction.

## Route evidence

See `FINAL_AUDIT_ROUTE_PROVENANCE.json` for the full ledger. Several fields
(provider, generation_id, fallback_used, zdr_confirmed) are `UNKNOWN` — the
model was explicitly instructed not to access credentials to determine
these, and did not claim to. Per the supervisor's stated verdict ceiling,
this caps the verdict at `PASS_WITH_RISKS` rather than `PASS`.
