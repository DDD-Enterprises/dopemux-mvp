# Embedded Audit — TP-UAG-T1-SEMANTIC-CORE-001 (PR #1309)

- **Status:** PASS
- **Auditor tool:** claude-code-cli
- **Auditor model:** sonnet
- **Exit code:** 0
- **Audited head:** `06d515dfd6c968d4a8a0c379f71f38998a62b49f`
- **Audited span:** full branch `c2c74d896..06d515dfd`
- **Report path:** `proof/TP-UAG-T1-SEMANTIC-CORE-001/AUDITOR_REPORT.md`

## Summary

Independent Claude Code (Sonnet) session audited the complete UAG
semantic-core branch at HEAD `06d515dfd` (base `c2c74d896`). All hardening
closures (F-1..F-4, F-7, F-8) were verified by direct code inspection with
exact line references and confirmed by a clean, isolated test run: the full
`tests/unit/uag/` suite passes 72/72 at the audited head in a detached worktree.
No blocking or high findings.

## Verified Closures

- **F-1** `src/dopemux/uag/receipt.py:42-43` — constructor enforces
  `execution_authority is not ExecutionAuthority.NONE` → `ValueError`. Identity
  comparison correctly rejects a raw string `"NONE"` (value-equal but not
  identity-equal to the `str, Enum` member). Verified by `test_raw_string_rejected`.
- **F-2** `src/dopemux/uag/primitives.py:39-45` — `canonical_json` passes
  `allow_nan=False`; NaN/Infinity raise `ValueError` before reaching
  `sha256_text`. Determinism preserved: key-order-independent dict digests match.
- **F-3** `src/dopemux/uag/ledger.py:62-65` — `for_kind()` rejects any
  non-`CorrelationKind` input (raw strings, None, ints, other enums).
- **F-4** `src/dopemux/uag/identity.py:73-74` — `UnknownItem.evidence_status`
  validated via `isinstance(..., EvidenceStatus)`.
- **F-7** `src/dopemux/uag/ledger.py:43-44` — `LedgerEntry.__post_init__`
  validates `evidence_status` via `isinstance`.
- **F-8** `src/dopemux/uag/identity.py:44-47` — `IdentityStage.__post_init__`
  validates both `evidence_status` and `confidence` via `isinstance`.

## Findings

| ID | Severity | Title | Status |
|----|----------|-------|--------|
| H-1 | INFO | `test_valid_floats_accepted` (~line 44) has a logically-vacuous second assertion | ACCEPTED_RISK |
| H-2 | INFO | Test count exceeds brief description (31 in test_hardening, 72 total) — more coverage, not less | ACCEPTED_RISK |

H-1/H-2 are cosmetic only and do not weaken closure coverage.

## Scope / Security / Determinism

- No secrets, tokens, credentials, private keys, or `.env` values in the diff.
- Changes confined entirely to `src/dopemux/uag/*`, `tests/unit/uag/*`, and
  `proof/TP-UAG-T1-SEMANTIC-CORE-001/*` — no scope creep.
- No I/O on import: `__init__.py` imports only sibling `dopemux.uag.*` modules;
  `primitives.py` imports only stdlib (`hashlib`, `json`, `re`, `dataclasses`,
  `typing`), matching the module docstring's "no provider SDK / socket /
  filesystem / environment / credential / subprocess / network I/O on import"
  claim.
- Deterministic canonical digesting preserved; verified key-order independence.

## Trust Model Note

The signed local attestation is an operator attestation with cryptographic
code-binding (OpenSSH detached signature over the exact PROOF bytes, namespace
`dopemux-embedded-audit`), not an independently executed CI audit run. The
independent audit itself was performed by a separate Claude Code (Sonnet)
session at the audited head, with exact line references and a clean isolated
72/72 test run.
