# Extractor Readiness — iMessage and Instagram

Status: Draft | Owner: You | Last Updated: 2025-09-02

This note assesses whether extractors are ready to hand off to transform → redact → index and lists the exact gaps to close first.

## MUSTs (handoff blockers)

1) Timestamp hardening (Apple epoch variants)
- Status: Partial
- iMessage: robust converter present (`_convert_apple_timestamp`) and used throughout extractors; ISO-8601 UTC ensured in CLI path. Add a single helper to centralize conversion and property tests.
- Action: PR-X1

2) Deterministic folding for reactions + replies
- Status: Present
- Reactions folded; replies resolved to stable `reply_to_msg_id`. Add order-shuffle tests to prove idempotency.
- Action: PR-X2

3) Attachment completeness + non-fatal reporting
- Status: Present
- Attachment metadata emitted; no uploads. Missing attachment report generated as `out/missing_attachments.json`; audit command added.
- Action: Keep

4) Schema validity + quarantine path
- Status: Present
- Row validation via Pydantic; quarantine file `out/quarantine/messages_bad.jsonl` written by JSON writer; CLI continues when valid rows exist.
- Action: Keep

5) Reproducibility & run manifest
- Status: Partial
- Run report + metrics implemented. Manifest (input hashes) added in this pass.
- Action: PR-X4 (completed here)

6) Machine-readable CLI error model
- Status: Missing
- Text errors/hints exist; standard JSON error codes not yet implemented.
- Action: PR-X5

7) Coverage + perf smoke
- Status: Partial
- Coverage ≥60% repo-wide; extractor paths >90% in many modules; perf smoke not automated. Add a simple perf marker and keep ≥90% for new code.
- Action: Add perf smoke later; enforce ≥90% for new modules.

8) Observability presence
- Status: Present
- `out/run_report.json` + `out/metrics.jsonl` emitted; schemas exist.
- Action: Keep

## Strong SHOULDs (soon)

- Attributed body normalization
  - Status: Placeholder texts used; full normalization not implemented. Action: PR-X6.
- Conversation index export
  - Status: Missing. Action: small follow-up PR (metadata-only file).
- Identity pseudo-IDs
  - Status: `source_meta.sender_pid` present; `sender_id` remains original for compatibility. Decide flip timing.
- Backup mode UX polish
  - Status: Implemented (preflights, secure prompt, hints, redaction).
- I/O safety & streaming
  - Status: Copy uses streaming hashing; add `--max-workers` later if we parallelize.

## Next

1. Land PR-X1…X5 (and X6 optional) as small, test-first changes.
2. Re-run extractor on fixtures and small sample; verify schema pass, quarantine presence, manifest+run_report present, perf smoke meets target.
3. Hand off to transform → redact → index per ADRs.

