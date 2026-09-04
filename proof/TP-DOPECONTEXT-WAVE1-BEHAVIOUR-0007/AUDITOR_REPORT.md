# AUDITOR REPORT — TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007 / PR #1318

- **Auditor:** AGY CLI v1.1.26, model `gemini-3.1-pro-high` (Gemini 3.1 Pro High)
- **Route:** `docs/ops/embedded-audit.md` route #1 (Tier-1 independent)
- **Audited head:** `1f6af050aca60a21c10c280756f22358fc3596ec`
- **Base:** `f7f0ed626`
- **Mode:** repository mounted read-only via `--add-dir`, so the auditor recomputed every
  claim against the files rather than against a diff embedded in the prompt
- **Round:** 1
- **Verdict: PASS — 0 blocking findings, 0 non-blocking findings**

## Why this audit exists

The CI check `independent embedded audit` fails on this PR for the standing structural reason,
not for anything in the change: the runner's static auditor route preflights to
`NEEDS_SUPERVISOR` and the PAL clink step exits 127 with *"Trusted Claude provider credential is
unavailable"* (run `33878654636`, 24 s, no provider call made). `PR Steward / final readiness`
inherits that failure. This bundle is the real exact-subject audit, imported through the local
signed-attestation lane that `scripts/audit/local_audit_acceptance.py` implements.

## Subject

Documentation only. Four files:

| File | Change |
|---|---|
| `claudedocs/dope-context-wave-reconciliation-2026-09-04.md` | new — reconciliation record |
| `task-packets/dope-context/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007.md` | new — task packet |
| `docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md` | append-only — Amendment A5 (`PROPOSED`) |
| `claudedocs/dope-context-retrieval-redesign-2026-09-03.md` | Revision 3 section + frontmatter `status:` |

No file under `services/dope-context/` and no file under `src/dopemux/dcp/` is touched.

## Claims audited and results

Nine substantive claims plus one deliberately-unverifiable one. All nine verified.

| Claim | Result | What the auditor established |
|---|---|---|
| **C1** Two Wave 1 definitions in the redesign doc, later supersedes earlier, differing in 6 of 12 owner files | **VERIFIED** | Both locations present, supersession statement present, and the 6-of-12 count confirmed independently |
| **C2** `chunker_version` ∈ `VectorProfile.fingerprint_payload()`, feeding `fingerprint_profiles()` → collection identity | **VERIFIED** | Confirmed in `services/dope-context/src/index_profile.py`. This is the load-bearing premise of the record's manifest-boundary ruling; had it been false the ruling would collapse |
| **C3** E3, E11, E21 already closed | **VERIFIED** | E3 via `RerankQueryTooLargeError` + `server.py` surfacing `rerank_degraded`; E11 via the bounded `_evict_expired` cache; E21 via `total_requests` incremented before the ratio, in both embedders |
| **C4** E1, E16, E10, E2/E4, C1, C6, C13 and the A4 `EmbeddingRequest.truncation` residual all still open | **VERIFIED** | Each confirmed at the cited file, including that the flags in `token_budget.py` are declared and never assigned `True` |
| **C5** E17 is asymmetric — docs payloads carry `token_count`, code payloads do not | **VERIFIED** | `docs_pipeline.py` writes it; `indexing_pipeline.py` omits it |
| **C6** Amendment A5's quoted regex matches the live rule; `red_lane_rules.py` unmodified; status `PROPOSED`; five lookaheads correctly anchored | **VERIFIED** | All four sub-checks. The auditor confirmed the additions are anchored "without widening" |
| **C7** Scope discipline — no code touched | **VERIFIED** | Exactly four markdown files in the diff |
| **C8** Record, packet and A5 agree with one another | **VERIFIED** | The five files added to the regex exactly match the five pending entries in the packet's Allowed Files |
| **C9** No overclaiming | **VERIFIED** | The A5b directory-exhaustion disclosure matches reality: `src/embeddings/` is 3-of-3 exempt under A2+A4+A5b and `src/rerank/` 1-of-1 |
| **R-6** Guard absent from the `pr-92` checkout | **NOT_VERIFIABLE** | Correctly refused: that checkout is outside the mounted directory. The auditor did confirm the narrower in-scope half — this worktree *does* contain `.claude/hooks/dcp_surface_guard.py` and `src/dopemux/dcp/red_lane_rules.py` |

`R-6` being returned as NOT_VERIFIABLE rather than PASS is the correct behaviour and is recorded
as such; it is not collapsed into the PASS verdict.

## Findings

**None.** No BLOCKER, HIGH, MEDIUM, LOW or INFO finding was raised.

## Remaining risks

The auditor returned an empty `remaining_risks` list. The following are carried from the subject
documents themselves rather than raised by the audit, and are disclosed here for completeness:

* `independent embedded audit` and `PR Steward / final readiness` are red in CI for the standing
  provider-credential reason. This bundle is the substitute authority for merge, via the
  documented local-attestation lane — not a claim that the CI route ran.
* ADR-226 Amendment A5 is `PROPOSED`. Nothing in this PR opens the red lane; the regex lands only
  on operator approval, as A2, A3 and A4 each did.
* The whole-repo benchmark remains `NOT_RUN` and `TP-DOPECONTEXT-VECTOR-SPACE-0004` remains
  `DECISION_REQUIRED`. This PR does not change either.
* R-6's out-of-worktree half rests on this session's own probe of the `pr-92` checkout and was
  not independently reproduced by the auditor.

## Local verification accompanying this audit

Run in the PR branch worktree, reported as PASS/FAIL/NOT_RUN:

| Check | Result |
|---|---|
| `services/dope-context` suite (`mise exec -- python -m pytest tests -q`) | **PASS** — 124 passed, 1 skipped |
| `tests/test_dcp_surface_guard.py` + `tests/dcp/test_dcp_0005_red_lane_scanner.py` | **PASS** — 69 passed |
| Proposed A5 regex against 14 exempt/blocked/traversal cases | **PASS** — all 14 as specified |
| CI `Unit Tests`, `Security Review`, `Docs`, `identity-check`, `Analyze`×4, `preflight`, `Clobber Guard` | **PASS** |
| CI `independent embedded audit` / `PR Steward` | **FAIL** — structural, see above |
| AGY audit round 2 | **NOT_RUN** — round 1 returned PASS with zero findings; no repair to re-audit |
