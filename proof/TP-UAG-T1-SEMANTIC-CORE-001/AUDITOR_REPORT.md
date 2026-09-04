# Embedded Audit — TP-UAG-T1-SEMANTIC-CORE-001 (PR #1309)

- **Status:** PASS_WITH_RISKS
- **Auditor tool:** claude-code-cli
- **Auditor model:** sonnet
- **Exit code:** 0
- **Audited head:** `06d515dfd6c968d4a8a0c379f71f38998a62b49f`
- **Audited span:** full branch `c2c74d896..06d515dfd`
- **Report path:** `proof/TP-UAG-T1-SEMANTIC-CORE-001/AUDITOR_REPORT.md`

## Summary

Independent Claude Code (Sonnet) session audited the complete UAG
semantic-core branch at HEAD `06d515dfd` (base `c2c74d896`). Static analysis of
the branch (tools/MCP-disabled) confirmed the hardening closures (F-1..F-4,
F-7, F-8) are correctly implemented with the argued guards, and found two
non-blocking LOW findings (AUD-01, AUD-02) described below. Deterministic
suites (72 unit / 187 contract / ruff / diff-check / change-contract) were run
by the implementer, not the auditor.

## Verified Closures

- **F-1** `src/dopemux/uag/receipt.py` — constructor enforces
  `execution_authority is ExecutionAuthority.NONE` (identity comparison, rejects
  raw `"NONE"` string and any other authority).
- **F-2** `src/dopemux/uag/primitives.py` — `canonical_json` passes
  `allow_nan=False`, so NaN/Infinity raise `ValueError` before digesting.
- **F-3** `src/dopemux/uag/ledger.py` — `for_kind()` rejects non-`CorrelationKind`.
- **F-4** `src/dopemux/uag/identity.py` — `UnknownItem.evidence_status` validated
  as `EvidenceStatus`.
- **F-7** `src/dopemux/uag/ledger.py` — `LedgerEntry.__post_init__` validates
  `evidence_status` as `EvidenceStatus`.
- **F-8** `src/dopemux/uag/identity.py` — `IdentityStage.__post_init__` validates
  both `evidence_status` and `confidence`.

## Findings

| ID | Severity | Title | Status |
|----|----------|-------|--------|
| AUD-01 | LOW | `is_sha256` accepts a single trailing newline via `$` regex anchor | OPEN |
| AUD-02 | LOW | `test_valid_floats_accepted` has a tautological assertion | OPEN |

### AUD-01 — is_sha256 trailing-newline gap (LOW, OPEN)

`primitives.py` `_SHA256_RE = re.compile(r'^[a-f0-9]{64}$')` used with
`.match()` admits a single trailing newline (Python `$` matches before a
trailing newline). This weakens the exact-digest-binding invariant that
`DigestRef` and `Receipt` rely on. Untested in either direction as of this head.

### AUD-02 — tautological test assertion (LOW, OPEN)

`tests/unit/uag/test_hardening.py::TestCanonicalJsonRejectsNonStandardFloats::test_valid_floats_accepted`
asserts `("0.0" not in result or "0" in result)`, which is satisfied regardless
of actual float-serialization behavior and does not meaningfully verify the
intended `-0.0` handling.

## Remaining Risks

- Independent audit ran tools/MCP-disabled (static analysis only); no in-audit
  test execution or live git/gh cross-check. Deterministic suites were run by
  the implementer, not the auditor.
- `is_sha256` trailing-newline gap (AUD-01) is unpatched and untested as of this
  head.
- Enum-value fidelity to ratified C0-R2 `common_defs.schema.json` could not be
  byte-verified (schema file not present in this checkout).
- No execution/approval surface verified via name-based denylist plus manual
  review only; reasonable for a pure-data module but not a formal proof.
- `PublicCore.canonical()` does not dedupe `public_values` keys on ties;
  `AttemptRecord.model_transport_receipt_ref` and `DigestRef.media_type` remain
  free-form (cosmetic).

## Scope / Security / Determinism

- No secrets, tokens, credentials, private keys, or `.env` values; no
  instruction-like content detected in the diff.
- Changes confined to `src/dopemux/uag/*`, `tests/unit/uag/*`, and
  `proof/TP-UAG-T1-SEMANTIC-CORE-001/*` — no scope creep.
- No provider SDK / socket / subprocess / env / credential access in the import
  surface (AST allowlist + subprocess no-filesystem-side-effect test pass).
- Deterministic canonical digesting preserved.

## Trust Model Note

The signed local attestation is an operator attestation with cryptographic
code-binding (OpenSSH detached signature over the exact PROOF bytes, namespace
`dopemux-embedded-audit`), not an independently executed CI audit run. The
independent audit itself was performed by a separate Claude Code (Sonnet)
session at the audited head with static analysis; deterministic suites were run
by the implementer.
