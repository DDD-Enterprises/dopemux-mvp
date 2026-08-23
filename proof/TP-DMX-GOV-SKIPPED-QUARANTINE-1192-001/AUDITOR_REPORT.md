# Embedded Audit Report

- Packet: `TP-DMX-GOV-SKIPPED-QUARANTINE-1192-001` PR 1257
- Audited content head: `f844ac7dd5c7dba26270ad4fea68a498264eee91`
- Implementer: Grok 4.6
- Auditor: agy gemini-3.1-pro-high / display Gemini 3.1 Pro (High) / session `b686b845-6bfc-4d56-99df-1c0ab41a7119`
- Verdict: **PASS_WITH_RISKS**

## Findings
- **missing_test_merge_base LOW OPEN** — Missing unit tests for merge-base logic. The new logic in evaluate() that attempts to use 'git merge-base' to bind quarantine content_head when origin/main has moved lacks explicit unit tests. The implementation correctly handles errors by falling back to range_base, but a test is recommended to prevent future regressions.
- **jsonschema_fail_closed_verified INFO RESOLVED** — jsonschema validation and fail-closed logic verified. The fix correctly imports and uses jsonschema to validate embedded_audit objects claiming SKIPPED status. It successfully fails closed (returning False) when the library is missing, the schema file is absent, or the JSON object is schema-invalid. Validated via test_malformed_skipped_does_not_activate_quarantine and test_quarantine_not_detected_when_jsonschema_missing.
- **quarantine_vs_audited_modes_verified INFO RESOLVED** — Quarantine vs Audited modes correctly handled. The boundary between SKIPPED quarantine and audited modes is properly maintained and tested. Quarantine mode explicitly forbids signatures and ignores missing audited_heads, while ensuring content and proof heads bind correctly. No new secrets were introduced, and the scope of changes is cleanly bounded to governance validation scripts and tests.

## Remaining risks
- Lack of explicit test coverage for the merge-base content_head binding could allow future changes to break the moved-main fallback logic silently.

## Summary
Audit completed for PR #1257 at content head f844ac7dd5c7dba26270ad4fea68a498264eee91. The fixes correctly implement jsonschema validation for SKIPPED proofs (failing closed appropriately) and correctly use git merge-base to bind quarantine content_head to prevent inflated proof-only deltas when origin/main moves. Tests cover all the malformed and missing jsonschema paths. No secret leaks or scope creep detected. A minor risk exists due to the missing unit test for the git merge-base fallback logic.
