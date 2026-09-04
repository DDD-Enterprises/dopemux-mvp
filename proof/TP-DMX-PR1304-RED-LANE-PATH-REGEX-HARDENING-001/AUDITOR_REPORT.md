# AUDITOR_REPORT — TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001

## Subject

PR #1322: `fix(dcp): harden red-lane FORBIDDEN_PATHS anchoring against
control characters`. Touches only the DCP-RED-MERGE-SEAM-0001 red-lane
guard: `src/dopemux/dcp/red_lane_rules.py` (FORBIDDEN_PATHS anchoring:
`$` → `\Z`, `.*` patterns gain `re.DOTALL`), `.claude/hooks/dcp_surface_guard.py`
(new unconditional control-character fail-closed check), and
`tests/test_dcp_surface_guard.py` (7 new regression tests, including a
direct `FORBIDDEN_PATHS.search()` assertion added in response to a Copilot
finding — see round 2 below). No product code.

- Base: `8910fd64c38e438b1cfbf9a77c6217511d8c7374` (origin/main after #1318)
- Head: `892b856d33574fa2b76a9d21f96c7edc4b032d99`

## Auditor

`agy` (Google Antigravity CLI), model `gemini-3.1-pro-high`. Connectivity
verified live immediately before each run.

## Round 1 (head `7d963fae3`)

**PASS** — 7/7 checks confirmed. Independently reproduced the claimed
regex vulnerability with a live Python repro and confirmed the fix closes
it. Full findings in `review_bundle/AGY_AUDIT_R1_RAW.json`.

## Round 1 follow-up: Copilot finding

Automated review on PR #1322 correctly found that the round-1 regression
tests only exercised the new control-character short-circuit in
`surface_guard_block` (which returns before ever evaluating
`FORBIDDEN_PATHS`), so they never actually proved the `\Z` + `re.DOTALL`
anchoring fix on its own. Fixed by adding `_matches_forbidden_pattern()`,
which imports `FORBIDDEN_PATHS` directly and asserts `pattern.search()` on
the newline-bearing strings, bypassing the guard entirely, plus a sanity
check that ordinary exempt paths still don't match. The round-1 commits
were then squashed with this fix into one clean content commit (`892b856d3`)
before re-auditing, since the original proof-only commits had landed
between two content commits.

## Round 2 (head `892b856d3`, current)

**PASS** — 7/7 findings confirmed, 0 remaining risks.

| ID | Severity | Title | Status |
|---|---|---|---|
| F-001 | INFO | Diff scope confined to the 3 stated files; no product code, no secrets | RESOLVED |
| F-002 | HIGH | Independently reproduced the regex anchor vulnerability (blanket-pattern bypass + exemption falsification) with a live Python repro, and independently confirmed `\Z`+`DOTALL` closes both | RESOLVED |
| F-003 | HIGH | Control-character guard runs unconditionally, first, before any normalization — cannot be bypassed | RESOLVED |
| F-004 | LOW | Adversarial check for a Unicode-line-separator (` `/` `) bypass gap: none found — those characters never triggered the regex-level hazard in the first place | RESOLVED |
| F-005 | CRITICAL | Matched-path set for ordinary (control-character-free) paths is unchanged — verified against existing dope-context carve-outs | RESOLVED |
| F-006 | MEDIUM | Confirmed the Copilot addendum fix (`_matches_forbidden_pattern`) genuinely proves the regex-level fix independent of the control-character short-circuit | RESOLVED |
| F-007 | HIGH | Full test suite independently re-run on the `892b856` head: 76/76 passed | RESOLVED |

Full auditor output: `review_bundle/AGY_AUDIT_RAW.json` (round 2),
`review_bundle/AGY_AUDIT_R1_RAW.json` (round 1).

## Additional validation (performed by the operator session, not re-run by the auditor)

- `tests/dcp/` full red-lane suite: 185 passed, 1 deselected (matches CI's own deselect)
- Required-CI-scope unit lane (`tests/unit tests/test_voice_core.py tests/test_brand_voice.py`): 1878 passed, 2 pre-existing quarantines, 0 new failures
- `scripts/brand_lint.py`: 0 errors, 0 warnings
