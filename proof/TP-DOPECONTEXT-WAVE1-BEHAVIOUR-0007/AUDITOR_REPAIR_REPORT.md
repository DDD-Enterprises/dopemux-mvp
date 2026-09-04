# AUDITOR REPAIR REPORT — TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007 / PR #1318, round 2

- **Auditor:** AGY CLI v1.1.26, model `gemini-3.1-pro-high`
- **Audited head:** `fecb5f3a35ec9b28cf849c2f8e29a5fcdb09f19a`
- **Round-1 head:** `1f6af050aca60a21c10c280756f22358fc3596ec` (PASS, zero findings)
- **Mode:** repository mounted read-only via `--add-dir`
- **Verdict: PASS — 0 findings. `round_1_still_holds: true`.**

## What triggered round 2

Four Copilot review threads, all making the same point: bare `index_profile.py:<line>` citations
should carry a repo-root path in documents used for operator approval and later implementation.

Copilot's stated premise — that the repository has multiple `index_profile.py` candidates — is
**false**, and the audit confirms it (check D4: exactly one, at
`services/dope-context/src/index_profile.py`). The recommendation was adopted anyway on its other
ground: these are governance documents whose findings *are* file:line claims, and every other
citation in them already carried the full path, so the bare ones were an internal inconsistency.

Repair commit `fecb5f3a3` expands all **ten** bare citations across the three documents, not only
the four flagged, and re-wraps the affected lines.

## Why a second round was required at all

The local-attestation lane (`scripts/audit/local_audit_acceptance.py`) binds an attestation to an
audited `head_sha` that must be an ancestor of the PR head with a **proof-directory-only** delta.
A content commit on top of the round-1 audited head voids that bond by design. Re-attesting
without re-auditing would have produced a signature over an unaudited head, so round 2 is a
requirement of the mechanism, not a courtesy.

## Checks

| Check | Result | Established |
|---|---|---|
| **D1** Diff is presentation-only | **VERIFIED** | No assertion, verdict, scope ruling, line number or count modified — only the path prefix and line wrapping |
| **D2** Expanded paths are *correct* | **VERIFIED** | `CODE_CHUNKER_VERSION` at :35, `DOCS_CHUNKER_VERSION` at :36, `VectorProfile.fingerprint_payload()` spanning :77-89 — each confirmed against the file. A citation made more precise while being wrong would be worse than the ambiguous original; this was checked explicitly |
| **D3** No bare citations missed | **VERIFIED** | All 10 updated; none remain in the three documents |
| **D4** Exactly one `index_profile.py` | **VERIFIED** | Repository-wide search; Copilot's premise refuted |
| **D5** Round-1 hard requirements still hold | **VERIFIED** | `src/dopemux/dcp/red_lane_rules.py` and all of `services/dope-context/` strictly unmodified by this PR |

## Findings

**None**, at any severity, in either round.

## Disposition of the review threads

All four Copilot threads were replied to with the correction to their premise and the scope of the
fix applied, then resolved. No thread was resolved without a substantive reply.

## Round-1 result, carried forward

Round 1 verified nine substantive claims (C1–C9) covering the two-Wave-1 finding and its 6-of-12
file count, `chunker_version`'s membership in `fingerprint_payload()`, the already-done set
E3/E11/E21, the still-open set including the A4 truncation residual, the E17 docs-versus-code
asymmetry, Amendment A5's regex and `PROPOSED` status, scope discipline, three-way document
consistency, and the A5b directory-exhaustion disclosure. Finding R-6 was returned NOT_VERIFIABLE
and is recorded as such, not collapsed into the PASS. Full record in `AUDITOR_REPORT.md`.
