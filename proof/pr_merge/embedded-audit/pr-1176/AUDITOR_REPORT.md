# CCAR-002R-A2 Independent Audit Report (R4 — canonical, supersedes R1/A1)

**PR**: 1176
**Audit Head (R4 / exact-head, "R3" in the Supervisor decision's numbering)**: `c8181389864bfc099bc24f7d689716057c3c8573`
**PR base**: `899082ae74155b2412a2ce862376438c1d33d13e`
**Auditor tool**: claude-code-cli
**Auditor model (proof enum)**: opus
**CLI version**: 2.1.220 (Claude Code)
**Orchestrating session ID**: 696c53ec-1cb2-49d8-a0ab-0fbe7560cbbf (see review_bundle/A2_INVOCATION_AND_SESSION.md for full invocation and session detail; the audited `claude -p --model opus` subprocess has no separately captured session id of its own)
**Exit code**: 0
**Verdict**: PASS_WITH_RISKS
**Blocking findings**: False

## Supersession note

This report and its bound `PROOF.json` supersede the prior R1/A1 report (Claude Sonnet, bound to
head `41bc62071ce4e152a3b2040e408eda0c830fb215`), which is preserved unmodified as historical record
under `review_bundle/R1_*` and referenced in `PROOF.json.history`. That prior audit's own finding
F-013 ("r2_not_yet_executed") and the current round's finding A2-F-006 both describe exactly the gap
this R4 report closes: the canonical proof is now bound to the exact current PR head, not a stale
intermediate one.

## Independence

- Implementation (CCAR-002R-A2 repair commits cd0d6a469c/b096551dfa/fd7afbe295/c818138): Claude Sonnet, single session
- Audit (this report): Claude Opus 5 (claude-code-cli), separate process and separate session
- Classification: `LIMITED_SAME_FAMILY_DIFFERENT_MODEL_SESSION` — different model tier, different
  session, did not author any of the audited work (REVIEW-001 satisfied), but same model family
  (Claude), not the cross-vendor OpenCode/OpenRouter route originally named in
  `task-packets/CCAR-002R-A2.md:115`. The named route was superseded by Supervisor decision after the
  direct Gemini CLI route was found unavailable (`IneligibleTierError`; see
  `review_bundle/A2_GEMINI_FAILURE.txt`) and the two prior OpenCode/OpenRouter passes were classified
  as advisory-only challenge history, not canonical evidence for this head.

## Ground truth re-derived by the auditor (not trusted from prior commit messages or in-repo claims)

- `git log -1 --format=%H` → `c8181389864bfc099bc24f7d689716057c3c8573` — matches the audited head.
- `git diff --stat 899082ae..HEAD` → 29 files, 4686 insertions, 0 deletions; `--name-status` shows
  all 29 entries as `A` (pure addition).
- `41bc6207..HEAD` → 5 commits, 23 files, all within the A2 allowlist (builder, tests, generated
  catalog, `proof/CCAR-002/**`, `proof/pr_merge/embedded-audit/pr-1176/**`, `task-packets/CCAR-002*`).

## Summary

All four CCAR-002R-A2 repair items were independently verified present and correct in the working
tree at the exact audited head, not merely claimed in commit messages: the absolute `worktree` key is
gone from `SOURCE_MANIFEST.json`; `NORMALIZATION_REPORT.md`'s `**Generated**` timestamp is a real
value (`2026-08-03T07:37:00Z`) matching the committed catalog's `meta.generated_at` byte-for-byte;
`test_generation_idempotent` now runs `--check` against the committed catalog before any
regeneration; and `_scan_model_ids()` uses a non-capturing group plus `finditer(...).group(0)`,
verified to return full matched tokens (not truncated fragments) across 7 manual probes. The full
test suite (`tests/commandcode_router/test_normalized_catalog.py`) passed 26/26 with the working tree
left byte-identical (catalog sha256 unchanged, `git status --short` clean). No stale "Claude Sonnet"
wording survives outside correct historical statements about the R1 round. No scope creep: the
41bc6207→HEAD range is 5 commits / 23 files, all inside the A2 allowlist. No hooks, MCP config,
skills, DCP surfaces, or CommandCode routing activation appear anywhere in the base→HEAD diff — the
catalog remains inert config/proof data. Nine base agents and 43 personas are present; all
authority-prohibition booleans (`may_change_tools`/`may_select_model`/`may_grant_write_authority`)
are `False` for all 43 records, and `route_eligible` is `False` throughout. No BLOCKING findings.

## Findings

### A2-F-001 [MEDIUM] test_generation_idempotent still writes the committed catalog — accepted_risk
The test regenerates `config/commandcode/normalized_agent_persona_catalog.yaml` in place and restores
it via a `finally` block. Verified clean on a normal run (catalog sha256 identical before/after, `git
status --short` clean afterward), but a SIGKILL, pytest timeout, or `-n auto` run could still leave
committed evidence dirty. The builder already exposes `--stdout`; the regeneration leg could avoid
touching the committed file entirely.

### A2-F-002 [LOW] --check cannot detect generated_at drift — open
`main()` calls `normalize_generated_at()` on both the committed and freshly-built YAML before
comparing in `--check` mode, so `--check` is structurally blind to `generated_at` mismatches — the
exact defect class A2 was repairing. Timestamp/catalog sync for this head was confirmed here by
direct byte comparison instead of by trusting `--check`'s exit code.

### A2-F-003 [LOW] Audit-route attribution inconsistent between proof files — open
`proof/CCAR-002/PROOF.json` records "round 2 vs fd7afbe295 (kimi-k3): FAIL", but
`proof/CCAR-002/COMMAND_LOG.md` correctly states kimi-k3 emitted no verdict at all and
deepseek-v4-pro was the fallback whose PASS was overridden to FAIL by direct operator inspection. The
FAIL was an operator determination, not kimi-k3's own verdict.

### A2-F-004 [LOW] Stale generator version string in NORMALIZATION_REPORT.md — open
The "Generator" section still reads `build_normalized_catalog.py v1.0.0`, contradicting the catalog's
`meta.generator_version: 1.0.1` and the R1 notes section of the same file.

### A2-F-005 [INFO] Manifest count label overcounts reference-only personas — accepted_risk
`SOURCE_MANIFEST.json` reports `reference_only_src_personas: 11` because it includes
`src/dopemux/personas/__init__.py`, while `NORMALIZATION_REPORT.md`'s "10 fallback copies" counts
only `.md` personas. Both counts are individually defensible; only the category label is imprecise.

### A2-F-006 [INFO] Canonical PR proof was stale by design prior to this commit — resolved
Prior to this R4 commit, `proof/pr_merge/embedded-audit/pr-1176/PROOF.json` was bound to
`head_sha=41bc62071ce4e152a3b2040e408eda0c830fb215` with a signature covering only that R1-bound
content. This R4 commit regenerates and re-signs `PROOF.json` against the exact final head, resolving
the finding.

### A2-F-007 [INFO] Committed instruction-like content in the R1 review bundle — accepted_risk
`review_bundle/AUDIT_INSTRUCTION.md` (R1 round) is a legitimate committed auditor prompt but contains
directive phrasing ("Only PASS or non-blocking PASS_WITH_RISKS authorizes R2.") and a pre-filled JSON
answer template with several booleans defaulted to `true`. Benign by design, not obeyed here, flagged
as a soft anchoring hazard for future auditors skimming rather than deriving each field
independently. Retained unmodified as historical record rather than edited after the fact.

### A2-F-008 [INFO] No dedicated CI/pre-commit drift gate for the catalog — open
No `.github/workflows/**` or `.pre-commit-config.yaml` entry references the catalog or its builder
specifically. Drift protection depends entirely on the pytest suite being collected via
`testpaths = ["tests"]`, which it is, but there is no dedicated gate.

### A2-F-009 [INFO] REVIEW-001 satisfied but named audit route not used — resolved
`task-packets/CCAR-002R-A2.md:115` names OpenCode + OpenRouter as the R3/R4 independent-audit route.
This audit was run by Claude Opus 5 in a separate process and session from the Claude Sonnet session
that authored the A2 repair; REVIEW-001's self-audit prohibition is satisfied, but the named route
was not used. Recorded honestly per Supervisor decision; independence classified
`LIMITED_SAME_FAMILY_DIFFERENT_MODEL_SESSION`, not full cross-vendor independence.

## Remaining risks

See `PROOF.json.embedded_audit.remaining_risks` for the canonical list (mirrors the findings above).

## Verdict

**PASS_WITH_RISKS** — R4 (this proof-only commit) authorized. Merge is **not** authorized by this
audit; PR Steward, trusted embedded-audit CI, and current security-release approval on the exact
final head are still required per the Supervisor decision's stop conditions.
