# Embedded Audit Report — TP-DMX-EMBEDDED-AUDIT-PROMPT-TRUST-001

## Verdict

`PASS_WITH_RISKS` (local implementer-adjacent review). Independent CI
`embedded-audit` workflow remains authoritative for PR Steward READY.

## Inspected paths

- `.github/workflows/embedded-audit.yml`
- `scripts/audit/pal_clink_runner.py`
- `scripts/audit/run_embedded_audit.py`
- `tools/auditor_router/pal_clink.py`
- `tools/auditor_router/models.py`
- `schemas/proof/embedded_audit.schema.json`
- `tests/audit/fixtures/prompt_trust/**`
- `tests/audit/test_run_embedded_audit.py`
- `docs/ops/embedded-audit.md`

## Evidence

1. Candidate content appears only inside untrusted delimiters; trusted trailer follows END marker.
2. Scanner detects adversarial fixture categories; proof stores hashes only.
3. Empty-rationale / missing evidence_refs PASS → NEEDS_SUPERVISOR.
4. FAIL and SKIPPED paths unchanged.
5. Tools/MCP contract still requires `--tools ""` and `--strict-mcp-config`.
6. Candidate code never checked out as working tree in workflow.
7. Full listed pytest suite green; schema validates.

## Instruction-like content

Adversarial fixtures intentionally contain injection-like strings. Scanner
detection is expected and treated as evidence. Benign documentation may also
match patterns; false positives do not auto-fail.

## Remaining risks

- Semantic fabrication of evidence fields by the auditor model
- Pattern-evading injection language
- Local proof is not a substitute for independent CI audit at exact head

## Validation

See `review_bundle/VALIDATION.txt`.
