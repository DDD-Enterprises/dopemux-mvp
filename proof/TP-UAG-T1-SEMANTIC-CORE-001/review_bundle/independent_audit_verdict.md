# Independent embedded audit — branch feat/uag-t1-semantic-core-001 at HEAD 06d515dfd (PR #1309 UAG hardening)

Auditor: Claude Code CLI (Tier-1 route #2, Sonnet model)
Invocation: `claude --print --model sonnet` against full branch base c2c74d896..HEAD 06d515dfd
Date: 2026-09-03T23:10Z

## Verdict: PASS

## Note on coverage vs brief
test_hardening.py has 31 tests covering F-1..F-8; the full tests/unit/uag/ suite has 72 tests. All 72 pass at HEAD 06d515dfd in a clean isolated detached worktree (`python -m pytest -q tests/unit/uag` -> `72 passed`). Closures more thoroughly tested than the brief described, not less.

## Findings (numbered, severity, status)

1. **[INFO]** `test_valid_floats_accepted` (~line 44) has a logically-vacuous second assertion (`"0.0" not in result or "0" in result` always true). Cosmetic only; the preceding `"1.5" in result` assertion still validates normal-float serialization survives allow_nan=False. **ACCEPTED_RISK**
2. **[INFO]** Test count exceeds brief description (31 in test_hardening, 72 total). More coverage, not less. **ACCEPTED_RISK**

## Closure verification (per-item, exact line refs)

- **F-1** CLOSED — receipt.py:42-43 `execution_authority is not ExecutionAuthority.NONE` -> ValueError. Identity check rejects raw string "NONE" (value-equal but not identity-equal to str,Enum member). Verified by test_raw_string_rejected (passed).
- **F-2** CLOSED — primitives.py:39-45 allow_nan=False; NaN/Inf raise ValueError before sha256_text. Deterministic: key-order-independent dict digests match.
- **F-3** CLOSED — ledger.py:62-65 for_kind() rejects non-CorrelationKind (strings, None, ints, other enums like EvidenceStatus.OBSERVED).
- **F-4** CLOSED — identity.py:73-74 UnknownItem.evidence_status isinstance(EvidenceStatus).
- **F-7** CLOSED — ledger.py:43-44 LedgerEntry.evidence_status isinstance(EvidenceStatus).
- **F-8** CLOSED — identity.py:44-47 IdentityStage.evidence_status + confidence both isinstance-validated.

## Scope / security / determinism
- No secrets/tokens: grep for API keys, secrets, passwords, PEM headers, AWS keys, Bearer tokens returned nothing.
- No scope creep: changes confined to src/dopemux/uag/*, tests/unit/uag/*, proof/TP-UAG-T1-SEMANTIC-CORE-001/*.
- No I/O on import: __init__.py imports only sibling dopemux.uag.*; primitives.py imports only stdlib (hashlib, json, re, dataclasses, typing).
- Deterministic canonical digesting preserved.
