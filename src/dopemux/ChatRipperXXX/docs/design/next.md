Title: NEXT
Status: Draft | Owner: You | Last Updated: 2025-09-02 PT

## Open Questions

* iMessage iCloud completeness automation: What OS-supported or acceptable method will we implement to **force download** all evicted attachments at scale? (Manual = OK short-term).
* Voice note transcription: Choose local engine (e.g., Whisper variants), language coverage, quality/latency targets, and evaluation set.
* iPhone USB path: Which acquisition tool/UX do we standardize for backups (and required prompts/permissions)?
* Output layout & retention: Set workspace layout for `out/attachments/**`, hashing strategy, and default retention policy.
* Detector thresholds: What SHOULD the default detector thresholds be for each coarse label family (conservative vs balanced)? Capture as config + unit tests.
* Episode hysteresis: SHOULD episode start/stop rules vary by platform (iMessage vs Instagram vs WhatsApp)? Define per-source defaults.
* Default chunking: Resolved in ADR-0002 — default is `turns:40, stride:10` for dense chats; daily windows for sparse periods.
* Local model default & quantization: PROPOSE `gemma2:9b` (IT) at 4-bit; CONFIRM as the project default and pin build hashes.
* NUANCE_LEVEL default: CONFIRM `balanced` as the default for cloud prompting.

## Next Actions

* Harden attributedBody/message_summary_info decoding (full parser + edge cases); add targeted fixtures.
* Finalize attachment copy policy (hashing, layout, retention); document backup vs local paths; edge cases in completeness report.
* Wire schema validation & quarantine; perf smoke; CI gates per TEST_STRATEGY.md.
* Draft ADRs for transcription engine choice (Whisper vs alternatives) and iCloud/USB acquisition UX.

## Changes Since Last Update

* 2025-09-02: Implemented initial iMessage extractor with reaction folding, reply resolution, and attachment metadata; added unit and integration tests.
* 2025-09-02: Wired CLI flags `--copy-binaries`, `--transcribe-audio local|off`, and `--report-missing`; added missing attachments report generation and validation; implemented local transcription path (mock/Whisper) and surfaced run stats.
* 2025-09-02: Added MobileSync backup path support: stage sms.db via Manifest.db, resolve/copy attachments by fileID, and enable transcription from backup without copy.
* 2025-09-02: Implemented best‑effort decoding for attributedBody and message_summary_info (plist parse + UTF‑8 fallback).
* 2025-09-03: Extractor hardening (X3–X6):
  - X3 — Row validation + quarantine wired; CLI exits non‑zero on zero valid rows.
  - X5 — Introduced RFC‑7807 error model and `--error-format json|text` (machine‑readable errors).
  - X6 — Attributed body normalization to clean text; raw preserved (base64) under `source_meta.raw.attributed_body`.
* 2025-08-16: **CLOUD_ENRICHMENT.md** expanded with `provenance`, `shield`, and confidence calibration details; added field-visibility matrix.
* 2025-08-16: **INTERFACES.md** updated to mirror enrichment fields, error codes, and visibility rules; enriched CLI contracts clarified.
* 2025-08-16: **ACCEPTANCE_CRITERIA.md** extended with Gherkin for chunking, relationship labels, idempotency, and minimal-context checks.
* 2025-08-15: Architecture, ADRs, and NFRs aligned on local-first operation, Policy Shield, schema-locked outputs, and temporal analytics foundation.
